"""Server-side Google Routes calls. The browser key is never used here."""

import json
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.security import CurrentUser

router = APIRouter(prefix="/api/maps", tags=["Maps"])

TravelMode = Literal["DRIVE", "WALK", "BICYCLE", "TRANSIT", "TWO_WHEELER"]


class LatLng(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class RouteRequest(BaseModel):
    origin: LatLng
    destination: LatLng
    travel_mode: TravelMode = "DRIVE"


@router.post("/route")
def compute_route(body: RouteRequest, user: CurrentUser):
    key = settings.GOOGLE_MAPS_SERVER_KEY.strip()
    if not key:
        raise HTTPException(
            status_code=503,
            detail=(
                "Google Routes is not configured. Set GOOGLE_MAPS_SERVER_KEY on the server. "
                "No distance or duration was estimated."
            ),
        )
    payload = {
        "origin": {"location": {"latLng": body.origin.model_dump()}},
        "destination": {"location": {"latLng": body.destination.model_dump()}},
        "travelMode": body.travel_mode,
    }
    request = Request(
        "https://routes.googleapis.com/directions/v2:computeRoutes",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode())
    except HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Google Routes rejected the request. Check that the Routes API is enabled for the server key.",
        ) from exc
    except URLError as exc:
        raise HTTPException(status_code=502, detail=f"Google Routes request failed: {exc.reason}") from exc
    routes = data.get("routes") or []
    if not routes:
        return {"routes": [], "note": "Google Routes returned no route for these points."}
    first = routes[0]
    return {
        "requested_by": user.id,
        "travel_mode": body.travel_mode,
        "distance_meters": first.get("distanceMeters"),
        "duration": first.get("duration"),
        "encoded_polyline": (first.get("polyline") or {}).get("encodedPolyline"),
        "source": "google_routes_api",
    }

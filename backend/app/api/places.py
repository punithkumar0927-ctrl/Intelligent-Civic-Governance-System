"""Saved map places. Each row belongs to the signed-in user."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.database import get_db
from app.models.saved_place import SavedPlace

router = APIRouter(prefix="/api/places", tags=["Places"])


class PlaceIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: Optional[str] = Field(None, max_length=400)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    category: str = Field("saved", max_length=40)
    google_place_id: Optional[str] = Field(None, max_length=160)
    source: str = Field("user", max_length=40)


class PlaceOut(PlaceIn):
    id: int

    class Config:
        from_attributes = True


@router.get("", response_model=list[PlaceOut])
def list_places(user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    rows = (
        db.query(SavedPlace)
        .filter(SavedPlace.user_id == user.id)
        .order_by(SavedPlace.id.desc())
        .limit(200)
        .all()
    )
    return rows


@router.post("", response_model=PlaceOut, status_code=201)
def create_place(body: PlaceIn, user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    row = SavedPlace(user_id=user.id, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{place_id}", status_code=204)
def delete_place(place_id: int, user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    row = db.query(SavedPlace).filter(SavedPlace.id == place_id, SavedPlace.user_id == user.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Saved place not found")
    db.delete(row)
    db.commit()

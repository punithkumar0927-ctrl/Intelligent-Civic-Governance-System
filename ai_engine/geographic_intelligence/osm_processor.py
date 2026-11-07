'''ai_engine/geographic_intelligence/osm_processor.py
OpenStreetMap data: reverse geocoding, road names, POI nearby.'''
import requests
from typing import Optional
from dataclasses import dataclass

NOMINATM_URL = "https://nominatim.openstreetmap.org"
USER_AGENT   = "NEXUS-AI/1.0 (research; contact@example.com)"

@dataclass
class GeocodeResult:
    display_name: str
    road: Optional[str] = None
    suburb: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    ward: Optional[str] = None
    postcode: Optional[str] = None
    osm_type: Optional[str] = None

def reverse_geocode(lat: float, lon: float) -> Optional[GeocodeResult]:
    try:
        r = requests.get(f'{NOMINATM_URL}/reverse',
            params={'lat': lat, 'lon': lon, 'format': 'jsonv2', 'addressdetails': 1},
            headers={'User-Agent': USER_AGENT}, timeout=8)
        if r.status_code != 200:
            return None
        d = r.json().get('address', {})
        return GeocodeResult(
            display_name=r.json().get('display_name', ''),
            road=d.get('road'), suburb=d.get('suburb') or d.get('neighbourhood'),
            city=d.get('city') or d.get('town') or d.get('village'),
            state=d.get('state'), ward=d.get('city_district') or d.get('ward'),
            postcode=d.get('postcode'), osm_type=r.json().get('type'),
        )
    except Exception as e:
        print(f'[osm_processor] reverse_geocode error: {e}')
        return None

HIGH_RISK_AMENITIES = {'school', 'hospital', 'clinic', 'college', 'kindergarten', 'bus_station'}

def nearest_amenity(lat: float, lon: float, radius_m: int = 500) -> list[dict]:
    try:
        # Use Overpass API
        query = f'[out:json][timeout:10];(node["amenity"~"school|hospital|clinic|college"](around:{radius_m},{lat},{lon}););out body;'
        r = requests.post('https://overpass-api.de/api/interpreter',
            data={'data': query}, headers={'User-Agent': USER_AGENT}, timeout=12)
        if r.status_code != 200:
            return []
        return [{'name': el.get('tags', {}).get('name', 'Unknown'),
                 'type': el.get('tags', {}).get('amenity', 'unknown'),
                 'lat': el.get('lat'), 'lon': el.get('lon')}
                for el in r.json().get('elements', [])[:10]]
    except Exception as e:
        print(f'[osm_processor] nearest_amenity error: {e}')
        return []

def is_high_risk_location(lat: float, lon: float) -> tuple[bool, list[dict]]:
    amenities = nearest_amenity(lat, lon, radius_m=400)
    risky = [a for a in amenities if a['type'] in HIGH_RISK_AMENITIES]
    return len(risky) > 0, risky

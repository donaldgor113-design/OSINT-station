from fastapi import APIRouter
from pydantic import BaseModel

from ...media.geocode import forward_geocode, reverse_geocode

router = APIRouter(prefix="/api", tags=["geocode"])


class GeocodeRequest(BaseModel):
    query: str


@router.post("/geocode")
async def geocode(body: GeocodeRequest):
    """Resolve an address/coords to a point on the map (Nominatim, real)."""
    q = body.query.strip()
    coords = None

    # If it's already coordinates ("lat, lng"), parse directly.
    parts = q.replace(",", " ").split()
    if len(parts) == 2:
        try:
            lat, lng = float(parts[0]), float(parts[1])
            coords = {"lat": lat, "lng": lng}
        except ValueError:
            coords = None

    if coords is None:
        coords = await forward_geocode(q)

    if not coords:
        return {"results": []}

    place = await reverse_geocode(coords["lat"], coords["lng"])
    return {
        "results": [
            {
                "lat": coords["lat"],
                "lng": coords["lng"],
                "address": place.get("address") or q,
                "city": place.get("city", ""),
                "country": place.get("country", ""),
            }
        ]
    }

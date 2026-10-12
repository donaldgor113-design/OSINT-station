from datetime import datetime, timezone

import httpx

from ..core.normalization import compute_entity_id
from ..schemas.universal_entity import (
    GeoProperty,
    Metadata,
    Properties,
    Source,
    UniversalEntityCreate,
)
from .base import Adapter


class GoogleMapsGeocodeAdapter(Adapter):
    """Geocode addresses / place names into `location` entities."""

    source_name = "google_maps"
    access_type = "api"
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"

    def __init__(self, api_key: str = "", mock: bool = True):
        self.api_key = api_key
        self.mock = mock

    async def search(self, query: str) -> list[dict]:
        if self.api_key and not self.mock:
            return await self._search_api(query)
        if self.mock:
            return self._mock_results(query)
        return []

    async def _search_api(self, query: str) -> list[dict]:
        params = {"address": query, "key": self.api_key}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
        return data.get("results", [])

    @staticmethod
    def _mock_results(query: str) -> list[dict]:
        return [
            {
                "formatted_address": f"{query}, Київ, Україна, 01001",
                "geometry": {"location": {"lat": 50.4501, "lng": 30.5234}},
                "address_components": [
                    {"long_name": "Київ", "types": ["locality", "political"]},
                    {"long_name": "Україна", "types": ["country", "political"]},
                ],
            },
            {
                "formatted_address": f"{query}, Львів, Україна, 79000",
                "geometry": {"location": {"lat": 49.8397, "lng": 24.0297}},
                "address_components": [
                    {"long_name": "Львів", "types": ["locality", "political"]},
                    {"long_name": "Україна", "types": ["country", "political"]},
                ],
            },
        ]

    def normalize_response(self, raw: dict) -> UniversalEntityCreate:
        geometry = raw.get("geometry") or {}
        location = geometry.get("location") or {}
        lat = location.get("lat")
        lng = location.get("lng")

        city, country = "", ""
        for comp in raw.get("address_components") or []:
            types = comp.get("types") or []
            if "locality" in types and not city:
                city = comp.get("long_name", "")
            elif "country" in types and not country:
                country = comp.get("long_name", "")

        coords = [0.0, 0.0]
        if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
            coords = [float(lng), float(lat)]
            # Locations dedupe on rounded coordinates (spec §4).
            key = [f"{round(float(lat), 4)}", f"{round(float(lng), 4)}"]
        else:
            key = [str(raw.get("formatted_address") or "unknown")]

        address = str(raw.get("formatted_address") or "")
        now = datetime.now(timezone.utc).isoformat()

        properties = Properties(
            geo=GeoProperty(coordinates=coords, city=city, country=country, address=address),
            metadata=Metadata(
                sources=[Source(name=self.source_name, confidence=0.85, last_verified=now)],
                completeness=0.4,
                risk_level="low",
            ),
        )

        return UniversalEntityCreate(
            entity_type="location",
            entity_id=compute_entity_id("location", key),
            entity_name=address or f"{lat},{lng}",
            properties=properties,
            raw_data={self.source_name: raw},
        )

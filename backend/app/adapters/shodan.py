import json
from datetime import datetime, timezone

import httpx

from ..core.normalization import compute_entity_id
from ..schemas.universal_entity import (
    DigitalFootprint,
    GeoProperty,
    Metadata,
    Properties,
    Source,
    TemporalProperty,
    UniversalEntityCreate,
)
from .base import Adapter


class ShodanAdapter(Adapter):
    """Search the internet-facing host index via the Shodan API."""

    source_name = "shodan"
    access_type = "api"
    base_url = "https://api.shodan.io"

    def __init__(self, api_key: str = "", mock: bool = False):
        self.api_key = api_key
        self.mock = mock

    async def search(self, query: str) -> list[dict]:
        if self.api_key:
            return await self._search_api(query)
        if self.mock:
            return self._mock_matches(query)
        return []

    async def _search_api(self, query: str) -> list[dict]:
        params = {"key": self.api_key, "query": query}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            response = await client.get("/shodan/host/search", params=params)
            response.raise_for_status()
            data = response.json()
        return data.get("matches", [])

    @staticmethod
    def _mock_matches(query: str) -> list[dict]:
        """Deterministic sample data so the UI works without an API key."""
        return [
            {
                "ip_str": "185.199.108.153",
                "port": 443,
                "org": "GitHub, Inc.",
                "location": {
                    "city": "Frankfurt am Main",
                    "country_name": "Germany",
                    "latitude": 50.1109,
                    "longitude": 8.6821,
                },
                "product": "nginx",
                "data": "HTTP/1.1 200 OK",
            },
            {
                "ip_str": "8.8.8.8",
                "port": 53,
                "org": "Google LLC",
                "location": {
                    "city": "Mountain View",
                    "country_name": "United States",
                    "latitude": 37.4056,
                    "longitude": -122.0775,
                },
                "product": "dns",
                "data": "DNS resolver",
            },
            {
                "ip_str": "1.1.1.1",
                "port": 443,
                "org": "Cloudflare, Inc.",
                "location": {
                    "city": "Sydney",
                    "country_name": "Australia",
                    "latitude": -33.8678,
                    "longitude": 151.2073,
                },
                "product": "cloudflare",
                "data": "HTTP/1.1 200 OK",
            },
        ]

    def normalize_response(self, raw: dict) -> UniversalEntityCreate:
        ip = str(raw.get("ip_str", "")).strip()
        location = raw.get("location") or {}
        lat = location.get("latitude")
        lng = location.get("longitude")

        coordinates = [0.0, 0.0]
        if isinstance(lng, (int, float)) and isinstance(lat, (int, float)):
            coordinates = [float(lng), float(lat)]

        now = datetime.now(timezone.utc).isoformat()

        properties = Properties(
            geo=GeoProperty(
                coordinates=coordinates,
                city=str(location.get("city") or ""),
                country=str(location.get("country_name") or ""),
                address="",
            ),
            temporal=TemporalProperty(observed_at=now),
            digital_footprint=DigitalFootprint(ip_addresses=[ip] if ip else []),
            metadata=Metadata(
                sources=[Source(name=self.source_name, confidence=0.9, last_verified=now)],
                completeness=0.5,
                risk_level="low",
            ),
        )

        if ip:
            entity_id = compute_entity_id("ip", [ip])
            entity_name = ip
        else:
            # Defensive fallback: still produce a stable id from the raw payload.
            canonical = json.dumps(raw, sort_keys=True, default=str)
            entity_id = compute_entity_id("ip", [canonical])
            entity_name = str(raw.get("org") or "unknown")

        return UniversalEntityCreate(
            entity_type="ip",
            entity_id=entity_id,
            entity_name=entity_name,
            properties=properties,
            raw_data={self.source_name: raw},
        )

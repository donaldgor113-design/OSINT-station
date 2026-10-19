import os
import time

import httpx

from .base import BaseTier, TierResult


class Tier4Specialized(BaseTier):
    """Спеціалізовані API (Shodan, Serper) — останній рубіж, опційний."""

    name = "tier4_special"

    def __init__(self, db, ai=None, cache=None):
        self.db = db
        self.shodan_key = os.getenv("SHODAN_API_KEY")
        self.serper_key = os.getenv("SERPER_API_KEY")
        self.timeout = httpx.Timeout(20.0, connect=5.0)

    def is_available(self):
        if not (self.shodan_key or self.serper_key):
            return False, "no specialized API keys (SHODAN_API_KEY / SERPER_API_KEY)"
        return True, None

    async def search(self, query: str, query_type: str, workspace_id: int) -> TierResult:
        started = time.monotonic()
        entities: list[dict] = []
        sources: list[str] = []

        if query_type == "ip" and self.shodan_key:
            ip_entity = await self._shodan_lookup(query)
            if ip_entity:
                entities.append(ip_entity)
                sources.append("shodan")

        if query_type in ("text", "domain") and self.serper_key:
            serper_hits = await self._serper_search(query)
            entities.extend(self._hits_to_docs(serper_hits, "serper"))
            sources.append("serper")

        return TierResult(
            tier_name=self.name,
            entities=entities,
            raw_sources=sources,
            confidence=0.9 if entities else 0.0,
            duration_ms=int((time.monotonic() - started) * 1000),
        )

    async def _shodan_lookup(self, ip: str) -> dict | None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"https://api.shodan.io/shodan/host/{ip}",
                    params={"key": self.shodan_key},
                )
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError:
            return None

        return {
            "entity_type": "ip",
            "entity_id": f"ip:{ip}",
            "entity_name": ip,
            "properties": {
                "digital_footprint": {
                    "ip_addresses": [ip],
                    "open_ports": data.get("ports", []),
                    "hostnames": data.get("hostnames", []),
                    "vulns": list(data.get("vulns", {}).keys()),
                    "org": data.get("org", ""),
                    "country": data.get("country_name", ""),
                },
                "metadata": {
                    "sources": [{"name": "shodan", "confidence": 0.9}],
                },
            },
            "relations": [],
            "raw_data": {"shodan": data},
        }

    async def _serper_search(self, query: str) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": self.serper_key,
                        "Content-Type": "application/json",
                    },
                    json={"q": query, "num": 10},
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError:
            return []
        return data.get("organic", [])

    def _hits_to_docs(self, hits: list[dict], source: str) -> list[dict]:
        return [
            {
                "entity_type": "document",
                "entity_id": f"url:{h['link']}",
                "entity_name": h.get("title", h["link"]),
                "properties": {
                    "document": {
                        "url": h["link"],
                        "title": h.get("title", ""),
                        "snippet": h.get("snippet", ""),
                    },
                    "metadata": {
                        "sources": [{"name": source, "confidence": 0.75}],
                    },
                },
                "relations": [],
                "raw_data": {source: h},
            }
            for h in hits
        ]

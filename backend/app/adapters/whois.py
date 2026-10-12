from datetime import datetime, timezone

import httpx

from ..core.normalization import compute_entity_id
from ..schemas.universal_entity import (
    Metadata,
    Properties,
    Source,
    UniversalEntityCreate,
)
from .base import Adapter


class WhoisAdapter(Adapter):
    """Domain lookup via the RDAP protocol (free, no key) with mock fallback.

    Spec §roadmap Phase 4 — "WHOIS/корпоративні реєстри".
    """

    source_name = "whois"
    access_type = "api"
    base_url = "https://rdap.org/domain/{domain}"

    def __init__(self, mock: bool = True):
        self.mock = mock

    async def search(self, query: str) -> list[dict]:
        domain = self._normalize_domain(query)
        if not domain:
            return []
        if not self.mock:
            real = await self._search_rdap(domain)
            if real:
                return [real]
        return [self._mock_record(domain)]

    @staticmethod
    def _normalize_domain(query: str) -> str:
        domain = query.strip().lower()
        for prefix in ("http://", "https://", "www."):
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
        return domain.split("/")[0].strip()

    async def _search_rdap(self, domain: str) -> dict | None:
        url = self.base_url.format(domain=domain)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception:
            return None

    @staticmethod
    def _mock_record(domain: str) -> dict:
        return {
            "mock": True,
            "ldhName": domain.upper(),
            "handle": domain.upper(),
            "status": [],
            "entities": [],
            "events": [],
        }

    def normalize_response(self, raw: dict) -> UniversalEntityCreate:
        domain = str(raw.get("ldhName") or raw.get("handle") or "").lower()
        is_mock = bool(raw.get("mock"))

        registrar = ""
        for entity in raw.get("entities") or []:
            if "registrar" in (entity.get("roles") or []):
                registrar = self._vcard_name(entity)
                break

        expires = ""
        for event in raw.get("events") or []:
            if event.get("eventAction") == "expiration":
                expires = str(event.get("eventDate") or "")

        now = datetime.now(timezone.utc).isoformat()

        properties = Properties(
            metadata=Metadata(
                sources=[
                    Source(
                        name=self.source_name,
                        confidence=0.5 if is_mock else 0.95,
                        last_verified=now,
                    )
                ],
                completeness=0.1 if is_mock else 0.6,
                risk_level="low",
            ),
            domain={
                "registrar": registrar,
                "expires": expires,
                "status": raw.get("status") or [],
                "note": "RDAP недоступний для цього домену (mock)" if is_mock else "",
            },
        )

        return UniversalEntityCreate(
            entity_type="domain",
            entity_id=compute_entity_id("domain", [domain]) if domain else None,
            entity_name=domain or "unknown",
            properties=properties,
            raw_data={self.source_name: raw},
        )

    @staticmethod
    def _vcard_name(entity: dict) -> str:
        vcard = entity.get("vcardArray")
        if not vcard:
            return ""
        try:
            for item in vcard[1]:
                if item[0] == "fn":
                    return str(item[3])
        except (IndexError, TypeError):
            pass
        return ""

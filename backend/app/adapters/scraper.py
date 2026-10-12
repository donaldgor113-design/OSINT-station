import re
from datetime import datetime, timezone

from ..core.normalization import compute_entity_id
from ..schemas.universal_entity import (
    Metadata,
    Properties,
    Source,
    UniversalEntityCreate,
)
from .base import Adapter


class CompanyScraperAdapter(Adapter):
    """Scrape a company's public homepage (spec §6 mechanism #2: web scraping).

    Fetching is done via httpx; parsing is a lightweight regex pass so it works
    with zero extra dependencies. Falls back to mock on network/parse failure.
    """

    source_name = "company_scraper"
    access_type = "scraper"

    def __init__(self, mock: bool = True):
        self.mock = mock

    async def search(self, query: str) -> list[dict]:
        domain = self._guess_domain(query)
        if not domain:
            return []
        if not self.mock:
            html = await self._fetch(domain)
            if html:
                return [self._extract(domain, html)]
            return []
        return [self._mock_record(domain)]

    async def _fetch(self, domain: str) -> str | None:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(
                    f"https://{domain}/",
                    headers={"User-Agent": "osint-workspace-poc/0.1"},
                )
                response.raise_for_status()
                return response.text
        except Exception:
            return None

    @staticmethod
    def _extract(domain: str, html: str) -> dict:
        title = ""
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if match:
            title = re.sub(r"\s+", " ", match.group(1)).strip()
        return {"domain": domain, "title": title}

    @staticmethod
    def _guess_domain(query: str) -> str:
        q = query.strip().lower()
        for prefix in ("https://", "http://", "www."):
            if q.startswith(prefix):
                q = q[len(prefix):]
        q = q.split("/")[0].strip()
        if "." not in q:
            q = f"{q}.com"
        return q

    @staticmethod
    def _mock_record(domain: str) -> dict:
        return {"domain": domain, "title": f"{domain.split('.')[0].title()} — публічна сторінка"}

    def normalize_response(self, raw: dict) -> UniversalEntityCreate:
        domain = str(raw.get("domain") or "")
        title = str(raw.get("title") or "")
        now = datetime.now(timezone.utc).isoformat()

        properties = Properties(
            metadata=Metadata(
                sources=[Source(name=self.source_name, confidence=0.6, last_verified=now)],
                completeness=0.3,
                risk_level="low",
            ),
        )

        return UniversalEntityCreate(
            entity_type="company",
            entity_id=compute_entity_id("company", [domain]) if domain else None,
            entity_name=title or domain or "unknown",
            properties=properties,
            raw_data={self.source_name: raw},
        )

from datetime import datetime, timezone

from ..core.normalization import compute_entity_id
from ..schemas.universal_entity import (
    Metadata,
    Properties,
    Source,
    UniversalEntityCreate,
)
from .base import Adapter


class SocialBrowserAdapter(Adapter):
    """Browser automation (spec §6 mechanism #3): render a JS-heavy page.

    Uses Playwright (Chromium) when installed to render a page and extract its
    title + visible text. Falls back to mock when Playwright is unavailable or
    the navigation fails. This is the mechanism that AI agents (phase 5) will
    reuse for automated collection.
    """

    source_name = "social_browser"
    access_type = "browser"

    def __init__(self, mock: bool = True):
        self.mock = mock

    async def search(self, query: str) -> list[dict]:
        if not self.mock:
            result = await self._scrape_dynamic(query)
            return result or []
        return self._mock_matches(query)

    async def _scrape_dynamic(self, query: str) -> list[dict] | None:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return None

        url = self._guess_url(query)
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=25000)
                title = (await page.title()).strip()
                try:
                    text = (await page.inner_text("body")).strip()
                except Exception:
                    text = ""
                await browser.close()
            return [{"query": query, "url": url, "title": title, "content": text[:500]}]
        except Exception:
            return None

    @staticmethod
    def _guess_url(query: str) -> str:
        q = query.strip()
        if q.lower().startswith(("http://", "https://")):
            return q
        if "." not in q:
            return f"https://{q}.com"
        return f"https://{q}"

    @staticmethod
    def _mock_matches(query: str) -> list[dict]:
        return [
            {
                "query": query,
                "url": f"https://{query}",
                "title": f"{query} (mock-результат)",
                "content": "Дані недоступні — увімкніть BROWSER_MOCK=false для реального рендерингу.",
            }
        ]

    def normalize_response(self, raw: dict) -> UniversalEntityCreate:
        title = str(raw.get("title") or "")
        url = str(raw.get("url") or "")
        content = str(raw.get("content") or "")
        now = datetime.now(timezone.utc).isoformat()

        properties = Properties(
            metadata=Metadata(
                sources=[Source(name=self.source_name, confidence=0.5, last_verified=now)],
                completeness=0.4,
                risk_level="low",
            ),
        )

        return UniversalEntityCreate(
            entity_type="document",
            entity_id=compute_entity_id("document", [url]) if url else None,
            entity_name=title or url or "unknown",
            properties=properties,
            raw_data={self.source_name: raw},
        )

import os

import httpx
from bs4 import BeautifulSoup

from .base import BaseTier, TierResult

JINA_READER = "https://r.jina.ai/{url}"


class Tier3Scraping(BaseTier):
    """Збагачення вже знайдених URL: Jina Reader → Playwright Stealth.

    Не шукає нові URL і тому не входить у загальний каскад — Orchestrator
    викликає `enrich_urls()` точково, коли інші рівні не дали достатньої
    впевненості.
    """

    name = "tier3_scrape"

    def __init__(self, db, ai=None, cache=None):
        self.db = db
        self.jina_key = os.getenv("JINA_API_KEY")
        self.timeout = httpx.Timeout(20.0, connect=5.0)

    def is_available(self):
        return True, None

    async def search(self, query: str, query_type: str, workspace_id: int) -> TierResult:
        return TierResult(
            tier_name=self.name,
            skipped=True,
            skip_reason="Tier3 is enrichment-only (викликається точково)",
        )

    async def enrich_urls(self, urls: list[str]) -> list[dict]:
        """Збагатити конкретні URL повним контентом."""
        enriched = []
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for url in urls[:5]:
                text = await self._jina_read(client, url)
                if not text:
                    text = await self._playwright_read(url)

                if text:
                    enriched.append(
                        {
                            "entity_type": "document",
                            "entity_id": f"url:{url}",
                            "entity_name": self._extract_title(text) or url,
                            "properties": {
                                "document": {
                                    "url": url,
                                    "full_text": text[:50_000],
                                    "text_length": len(text),
                                },
                                "metadata": {
                                    "sources": [{"name": "scraper", "confidence": 0.7}],
                                },
                            },
                            "relations": [],
                            "raw_data": {"scraper": {"url": url}},
                        }
                    )
        return enriched

    async def _jina_read(self, client: httpx.AsyncClient, url: str) -> str:
        headers = {"Accept": "text/plain"}
        if self.jina_key:
            headers["Authorization"] = f"Bearer {self.jina_key}"
        try:
            resp = await client.get(JINA_READER.format(url=url), headers=headers)
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPError:
            return ""

    async def _playwright_read(self, url: str) -> str:
        try:
            from playwright.async_api import async_playwright
            from playwright_stealth import Stealth
        except ImportError:
            return ""

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()
            await Stealth().apply_stealth_async(page)

            try:
                await page.goto(url, wait_until="networkidle", timeout=30_000)
                html = await page.content()
            except Exception:  # noqa: BLE001
                html = ""
            finally:
                await browser.close()

        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)

    @staticmethod
    def _extract_title(text: str) -> str:
        for line in text.splitlines():
            line = line.strip()
            if line and len(line) < 200:
                return line
        return ""

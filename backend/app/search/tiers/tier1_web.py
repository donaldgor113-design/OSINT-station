import os
import re
import time
import urllib.parse

import httpx

from ...adapters.web_search import search_web
from .base import BaseTier, TierResult

JINA_SEARCH = "https://s.jina.ai/{query}"
JINA_READER = "https://r.jina.ai/{url}"


class Tier1WebSearch(BaseTier):
    """Загальний веб-пошук.

    Основний безкоштовний канал — наявний `search_web` (Bing → DuckDuckGo →
    Playwright), який не потребує ключа. Jina і Brave підключаються опційно,
    якщо задано відповідні ключі.
    """

    name = "tier1_web"

    def __init__(self, db, ai=None, cache=None):
        self.db = db
        self.brave_key = os.getenv("BRAVE_SEARCH_API_KEY")
        self.jina_key = os.getenv("JINA_API_KEY")
        self.timeout = httpx.Timeout(15.0, connect=5.0)

    def is_available(self):
        return True, None  # Bing/DDG доступні без ключа

    async def search(self, query: str, query_type: str, workspace_id: int) -> TierResult:
        started = time.monotonic()
        entities: list[dict] = []
        sources: list[str] = []

        # 1. Основний канал — шар веб-пошуку проєкту (Bing → DDG → Playwright).
        try:
            web_results = await search_web(query, limit=10)
        except Exception:  # noqa: BLE001
            web_results = []
        if web_results:
            entities.extend(self._docs_to_entities(web_results, "web_search", 0.6))
            sources.append("web_search")

        # 2. Jina (опційно, якщо задано JINA_API_KEY — без ключа s.jina.ai
        #    віддає 401).
        if self.jina_key:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                jina_results = await self._jina_search(client, query)
                if jina_results:
                    entities.extend(self._docs_to_entities(jina_results, "jina_search", 0.6))
                    sources.append("jina_search")

        confidence = min(0.7, 0.15 * len(entities)) if entities else 0.0

        return TierResult(
            tier_name=self.name,
            entities=entities,
            raw_sources=sources,
            confidence=confidence,
            duration_ms=int((time.monotonic() - started) * 1000),
        )

    # --- Jina ---

    async def _jina_search(self, client: httpx.AsyncClient, query: str) -> list[dict]:
        """s.jina.ai повертає Markdown. Потрібен JINA_API_KEY."""
        encoded = urllib.parse.quote(query, safe="")
        url = JINA_SEARCH.format(query=encoded)
        headers = {"Accept": "text/plain"}
        if self.jina_key:
            headers["Authorization"] = f"Bearer {self.jina_key}"
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPError:
            return []

        pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        results = []
        for match in pattern.finditer(resp.text):
            title, href = match.group(1), match.group(2)
            if href.startswith("http"):
                results.append({"title": title, "url": href, "snippet": ""})
        return results[:10]

    async def _jina_read(self, client: httpx.AsyncClient, url: str) -> str:
        """Читає будь-який URL → чистий Markdown. Використовується в Tier3."""
        headers = {"Accept": "text/plain"}
        if self.jina_key:
            headers["Authorization"] = f"Bearer {self.jina_key}"
        try:
            resp = await client.get(JINA_READER.format(url=url), headers=headers)
            resp.raise_for_status()
            return resp.text[:20_000]
        except httpx.HTTPError:
            return ""

    # --- helpers ---

    @staticmethod
    def _docs_to_entities(results: list[dict], source_name: str, confidence: float) -> list[dict]:
        return [
            {
                "entity_type": "document",
                "entity_id": f"url:{r['url']}",
                "entity_name": r.get("title") or r["url"],
                "properties": {
                    "document": {
                        "url": r["url"],
                        "title": r.get("title", ""),
                        "snippet": r.get("snippet", ""),
                    },
                    "metadata": {
                        "sources": [{"name": source_name, "confidence": confidence}],
                    },
                },
                "relations": [],
                "raw_data": {source_name: r},
            }
            for r in results
            if r.get("url")
        ]

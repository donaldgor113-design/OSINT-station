import os
import re
import time
import urllib.parse

import httpx

from .base import BaseTier, TierResult

try:
    from dorksmith import generate, search_url, validate_query  # type: ignore

    _DORKSMITH_AVAILABLE = True
except ImportError:  # опційна залежність — рівень просто пропускається
    generate = None  # type: ignore
    search_url = None  # type: ignore
    validate_query = None  # type: ignore
    _DORKSMITH_AVAILABLE = False


class Tier2Dorking(BaseTier):
    """Автоматизований доркінг (dorksmith) для domain / компаній / осіб."""

    name = "tier2_dorks"

    INTENT_MAP = {
        "company-profile": "company-profile",
        "person-profile": "person-organization",
        "public-documents": "public-documents",
        "media-discovery": "media-discovery",
        "general-discovery": "general-discovery",
        "exposed-config-files": "exposed-config-files",
    }

    def __init__(self, db, ai=None, cache=None):
        self.db = db
        self.jina_key = os.getenv("JINA_API_KEY")
        self.timeout = httpx.Timeout(15.0, connect=5.0)

    def is_available(self):
        if not _DORKSMITH_AVAILABLE:
            return False, "dorksmith not installed"
        return True, None

    async def search(self, query: str, query_type: str, workspace_id: int) -> TierResult:
        started = time.monotonic()
        intent = self._pick_intent(query_type)
        if not intent:
            return TierResult(
                tier_name=self.name,
                skipped=True,
                skip_reason=f"no dork intent for type={query_type}",
            )

        input_type, options = self._build_dorksmith_input(query, query_type)
        if not input_type:
            return TierResult(
                tier_name=self.name,
                skipped=True,
                skip_reason="dorksmith input not recognized",
            )

        try:
            result = generate(
                input=query,
                input_type=input_type,
                intent=intent,
                options=options,
            )
        except Exception as exc:  # noqa: BLE001
            return TierResult(tier_name=self.name, error=f"dorksmith: {exc}")

        entities: list[dict] = []
        executed_queries: list[str] = []

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for variant in result.variants[:3]:
                validation = validate_query(variant.query)
                if validation.warnings:
                    continue

                url = search_url(variant.query)
                executed_queries.append(variant.query)

                hits = await self._execute_dork(client, url, variant.query)
                entities.extend(self._hits_to_entities(hits, variant.label, variant.query))

        confidence = min(0.6, 0.1 * len(entities)) if entities else 0.0

        return TierResult(
            tier_name=self.name,
            entities=entities,
            raw_sources=[f"dork:{q}" for q in executed_queries],
            confidence=confidence,
            duration_ms=int((time.monotonic() - started) * 1000),
        )

    def _pick_intent(self, query_type: str) -> str | None:
        if query_type == "domain":
            return "public-documents"
        if query_type == "company_edrpou":
            return "company-profile"
        if query_type == "person_ipn":
            return "person-organization"
        if query_type == "handle":
            return "person-organization"
        if query_type == "text":
            return "general-discovery"
        return None

    def _build_dorksmith_input(self, query: str, query_type: str):
        if query_type == "domain":
            return "domain", {"fileTypes": ["pdf", "docx", "xlsx"], "maxVariants": 5}
        if query_type == "company_edrpou":
            return "keyword", {
                "organization": query,
                "fileTypes": ["pdf", "docx"],
                "maxVariants": 5,
            }
        if query_type == "person_ipn":
            # Дорк по самому номеру ІПН безглуздий — Orchestrator підставляє
            # сюди ПІБ, знайдене в Tier0 (resolved_query).
            return "keyword", {"maxVariants": 5}
        if query_type == "handle":
            return "handle", {"maxVariants": 5}
        if query_type == "text":
            return "keyword", {"maxVariants": 5}
        return None, {}

    async def _execute_dork(
        self, client: httpx.AsyncClient, search_url_str: str, dork_query: str
    ) -> list[dict]:
        """Виконує дork.

        Спочатку — Jina (якщо задано JINA_API_KEY). Інакше — наявний шар
        веб-пошуку проєкту (Bing розуміє оператори site:/filetype:).
        """
        if self.jina_key:
            hits = await self._jina_dork(client, dork_query)
            if hits:
                return hits

        from ...adapters.web_search import search_web

        try:
            results = await search_web(dork_query, limit=10)
        except Exception:  # noqa: BLE001
            return []
        return [
            {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("snippet", "")}
            for r in results
            if r.get("url")
        ]

    async def _jina_dork(self, client: httpx.AsyncClient, dork_query: str) -> list[dict]:
        parsed = urllib.parse.urlparse(dork_query)
        pure_query = urllib.parse.parse_qs(parsed.query).get("q", [dork_query])[0]

        encoded = urllib.parse.quote(pure_query, safe="")
        try:
            resp = await client.get(
                f"https://s.jina.ai/{encoded}",
                headers={"Accept": "text/plain", "Authorization": f"Bearer {self.jina_key}"},
            )
            resp.raise_for_status()
        except httpx.HTTPError:
            return []

        pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        return [
            {"title": m.group(1), "url": m.group(2), "snippet": ""}
            for m in pattern.finditer(resp.text)
            if m.group(2).startswith("http")
        ][:10]

    def _hits_to_entities(self, hits: list[dict], label: str, dork: str) -> list[dict]:
        return [
            {
                "entity_type": "document",
                "entity_id": f"url:{h['url']}",
                "entity_name": h.get("title") or h["url"],
                "properties": {
                    "document": {
                        "url": h["url"],
                        "title": h.get("title", ""),
                        "snippet": h.get("snippet", ""),
                        "dork_label": label,
                        "dork_query": dork,
                    },
                    "metadata": {
                        "sources": [{"name": "dorksmith", "confidence": 0.55}],
                    },
                },
                "relations": [],
                "raw_data": {"dorksmith": {"label": label, "dork": dork, "hit": h}},
            }
            for h in hits
        ]

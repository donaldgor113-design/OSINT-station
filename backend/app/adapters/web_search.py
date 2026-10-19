import asyncio
import base64
import re
import time
import urllib.parse
from datetime import datetime, timezone

import httpx

from ..config import get_settings
from ..core.normalization import compute_entity_id
from ..schemas.universal_entity import (
    Metadata,
    Properties,
    Source,
    UniversalEntityCreate,
)
from .base import Adapter

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

# Simple in-memory cache + throttle to avoid triggering engine rate limits.
_cache: dict[str, list[dict]] = {}
_last_request = 0.0
_MIN_INTERVAL = 1.0


def _strip(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _clean_url(href: str) -> str:
    href = href.replace("&amp;", "&")
    # Bing redirect: .../ck/a?...&u=a1<base64url>
    if "bing.com/ck" in href:
        match = re.search(r"[?&]u=([^&]+)", href)
        if match:
            val = match.group(1)
            if val.startswith("a1"):
                val = val[2:]
            elif val.startswith("a"):
                val = val[1:]
            val = urllib.parse.unquote(val)
            try:
                padded = val + "=" * (-len(val) % 4)
                decoded = base64.b64decode(padded).decode("utf-8")
                if decoded.startswith("http"):
                    return decoded
            except Exception:
                pass
    # DuckDuckGo redirect
    match = re.search(r"uddg=([^&]+)", href)
    if match:
        return urllib.parse.unquote(match.group(1))
    if href.startswith("//"):
        return "https:" + href
    return href


async def _throttle() -> None:
    global _last_request
    now = time.monotonic()
    wait = _last_request + _MIN_INTERVAL - now
    if wait > 0:
        await asyncio.sleep(wait)
    _last_request = time.monotonic()


async def _get(url: str, params: dict) -> str | None:
    await _throttle()
    try:
        async with httpx.AsyncClient(
            timeout=10.0, follow_redirects=True, headers=_HEADERS
        ) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.text
    except Exception:
        return None


def parse_ddg(html: str) -> list[dict]:
    titles = re.findall(
        r'class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL
    )
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
    results = []
    for i, (href, title_html) in enumerate(titles):
        url = _clean_url(href)
        if not url.startswith("http"):
            continue
        results.append(
            {
                "title": _strip(title_html),
                "url": url,
                "snippet": _strip(snippets[i]) if i < len(snippets) else "",
            }
        )
    return results


def parse_ddg_lite(html: str) -> list[dict]:
    links = re.findall(
        r'<a[^>]*class="result-link"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL
    )
    snippets = re.findall(
        r'<td[^>]*class="result-snippet"[^>]*>(.*?)</td>', html, re.DOTALL
    )
    results = []
    for i, (href, title_html) in enumerate(links):
        url = _clean_url(href)
        if not url.startswith("http"):
            continue
        results.append(
            {
                "title": _strip(title_html),
                "url": url,
                "snippet": _strip(snippets[i]) if i < len(snippets) else "",
            }
        )
    return results


def parse_bing(html: str) -> list[dict]:
    results = []
    for block in re.findall(r'<li class="b_algo".*?</li>', html, re.DOTALL):
        title_m = re.search(
            r'<h2[^>]*>\s*<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL
        )
        if not title_m:
            title_m = re.search(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
        snippet_m = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
        if not title_m:
            continue
        url = _clean_url(title_m.group(1))
        if not url.startswith("http"):
            continue
        results.append(
            {
                "title": _strip(title_m.group(2)),
                "url": url,
                "snippet": _strip(snippet_m.group(1)) if snippet_m else "",
            }
        )
    return results


_ENGINES = [
    ("https://www.bing.com/search", parse_bing),
    ("https://html.duckduckgo.com/html/", parse_ddg),
    ("https://lite.duckduckgo.com/lite/", parse_ddg_lite),
]


async def search_google_cse(query: str, limit: int) -> list[dict]:
    """Google Custom Search JSON API (free tier: 100 queries/day)."""
    settings = get_settings()
    if not (settings.google_cse_api_key and settings.google_cse_id):
        return []
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": settings.google_cse_api_key,
                    "cx": settings.google_cse_id,
                    "q": query,
                },
            )
            response.raise_for_status()
            data = response.json()
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("link", ""),
                "snippet": r.get("snippet", ""),
            }
            for r in data.get("items", [])
        ][:limit]
    except Exception:
        return []


async def search_brave(query: str, limit: int) -> list[dict]:
    """Brave Search API (paid tier) when a key is set."""
    key = get_settings().brave_search_api_key
    if not key:
        return []
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": min(limit, 20)},
                headers={"X-Subscription-Token": key, "Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("description", ""),
            }
            for r in data.get("web", {}).get("results", [])
        ]
    except Exception:
        return []


async def search_playwright(query: str, limit: int) -> list[dict]:
    """Real-browser search via Playwright (harder to block) as a last resort."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return []

    url = f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote(query)}"
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            html = await page.content()
            await browser.close()
        return parse_ddg_lite(html)[:limit]
    except Exception:
        return []


async def search_web(query: str, limit: int = 30) -> list[dict]:
    """Layered web search: Brave API -> HTTP engines -> Playwright browser."""
    key = f"{query}:{limit}"
    if key in _cache:
        return _cache[key]

    results = await search_google_cse(query, limit)
    if results:
        _cache[key] = results
        return results

    results = await search_brave(query, limit)
    if results:
        _cache[key] = results
        return results

    for url, parser in _ENGINES:
        html = await _get(url, {"q": query})
        if not html:
            continue
        results = parser(html)[:limit]
        if results:
            _cache[key] = results
            return results

    results = await search_playwright(query, limit)
    _cache[key] = results
    return results


def parse_bing_images(html: str) -> list[str]:
    urls = []
    for m in re.findall(r'murl&quot;:&quot;(.*?)&quot;', html):
        url = m.replace("\\u002f", "/").replace("\\u0026", "&").replace("\\/", "/")
        if url.startswith("http"):
            urls.append(url)
    return urls


async def search_images(query: str, limit: int = 5) -> list[str]:
    """Fetch image URLs from Bing image search (small thumbnails for cards)."""
    html = await _get("https://www.bing.com/images/search", {"q": query})
    if not html:
        return []
    return parse_bing_images(html)[:limit]


class WebSearchAdapter(Adapter):
    """Search the web and return real results from a search engine."""

    source_name = "web_search"
    access_type = "scraper"

    def __init__(self, mock: bool = False):
        self.mock = mock

    async def search(self, query: str) -> list[dict]:
        if self.mock:
            return []
        return await search_web(query, limit=8)

    def normalize_response(self, raw: dict) -> UniversalEntityCreate:
        url = str(raw.get("url") or "")
        title = str(raw.get("title") or "")
        snippet = str(raw.get("snippet") or "")
        now = datetime.now(timezone.utc).isoformat()

        properties = Properties(
            metadata=Metadata(
                sources=[Source(name=self.source_name, confidence=0.5, last_verified=now)],
                completeness=0.3,
                risk_level="low",
            ),
            document={"url": url, "snippet": snippet},
        )

        return UniversalEntityCreate(
            entity_type="document",
            entity_id=compute_entity_id("document", [url]) if url else None,
            entity_name=title or url or "unknown",
            properties=properties,
            raw_data={self.source_name: raw},
        )

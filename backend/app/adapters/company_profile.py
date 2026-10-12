import asyncio
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from ..config import get_settings
from ..core.normalization import compute_entity_id
from ..media.geocode import forward_geocode
from ..schemas.universal_entity import (
    GeoProperty,
    Metadata,
    Properties,
    Source,
    UniversalEntityCreate,
)
from .base import Adapter
from .web_search import search_images, search_web

_SOCIAL_DOMAINS = {
    "facebook.com": "Facebook",
    "instagram.com": "Instagram",
    "linkedin.com": "LinkedIn",
    "twitter.com": "Twitter/X",
    "x.com": "Twitter/X",
    "t.me": "Telegram",
    "telegram.me": "Telegram",
    "youtube.com": "YouTube",
    "tiktok.com": "TikTok",
}
_REGISTRY_DOMAINS = (
    "youcontrol.com.ua",
    "opendatabot.com",
    "vkursi.pro",
    "clarity-project.info",
    "ring.org.ua",
    "yousearch.io",
)
_SEARCH_ENGINE_DOMAINS = (
    "bing.com",
    "duckduckgo.com",
    "google.com",
    "google.com.ua",
    "yahoo.com",
    "search.brave.com",
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def _strip_tags(html: str) -> str:
    text = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


class CompanyProfileAdapter(Adapter):
    """Company profile: web search (by name) or direct registry lookup (by ЄДРПОУ).

    For a name — search the web, classify results, open top pages and parse legal
    fields. For an 8-digit ЄДРПОУ — query registry aggregators directly.
    """

    source_name = "company_profile"
    access_type = "scraper"

    def __init__(self, mock: bool = False):
        self.mock = mock

    async def search(self, query: str) -> list[dict]:
        if self.mock:
            return []
        q = query.strip()

        edrpou = self._extract_edrpou(q)

        record: dict | None = None
        if edrpou:
            legal = await self._lookup_by_edrpou(edrpou)
            if legal.get("address") or legal.get("name"):
                record = {
                    "name": legal.get("name") or edrpou,
                    "wikipedia": None,
                    "website": None,
                    "socials": [],
                    "mentions": [],
                    "legal": legal,
                    "all_results": [],
                }
            else:
                # Fallback: search the web with context and extract from snippets.
                results = await search_web(f"ЄДРПОУ {edrpou}", limit=30)
                if results:
                    record = await self._profile_from_search(edrpou, results)
                    record["legal"].setdefault("edrpou", edrpou)
        else:
            results = await search_web(q, limit=30)
            if results:
                record = await self._profile_from_search(q, results)

        if not record:
            return []

        # Geocode the address so it can be shown on a map and in the geo tab.
        legal = record.get("legal") or {}
        if legal.get("address"):
            coords = await forward_geocode(legal["address"])
            if coords:
                record["geo"] = {
                    "coordinates": [coords["lng"], coords["lat"]],
                    "address": legal["address"],
                }

        record["images"] = await search_images(record.get("name") or q, limit=5)
        if edrpou:
            record["opendatabot_url"] = f"https://opendatabot.ua/c/{edrpou}"

        return [record]

    # ---------- helpers ----------

    @staticmethod
    def _is_edrpou(q: str) -> bool:
        return q.isdigit() and len(q) == 8

    @staticmethod
    def _extract_edrpou(q: str) -> str | None:
        """Find an 8-digit ЄДРПОУ code anywhere in the query text."""
        match = re.search(r"\b(\d{8})\b", q)
        return match.group(1) if match else None

    @staticmethod
    def _domain_of(url: str) -> str:
        try:
            domain = urlparse(url).netloc.lower()
            return domain[4:] if domain.startswith("www.") else domain
        except Exception:
            return ""

    @staticmethod
    def _is_wiki(domain: str) -> bool:
        return "wikipedia.org" in domain

    @staticmethod
    def _social_name(domain: str) -> str | None:
        for key, name in _SOCIAL_DOMAINS.items():
            if domain.endswith(key):
                return name
        return None

    @staticmethod
    def _is_registry(domain: str) -> bool:
        return any(r in domain for r in _REGISTRY_DOMAINS)

    @staticmethod
    def _is_search_engine(domain: str) -> bool:
        return any(d in domain for d in _SEARCH_ENGINE_DOMAINS)

    # ---------- aggregation (by name) ----------

    def _aggregate(self, query: str, results: list[dict]) -> dict:
        socials: list[dict] = []
        wikipedia: str | None = None
        website: str | None = None
        mentions: list[dict] = []
        titles: list[str] = []

        for r in results:
            url = r.get("url", "")
            domain = self._domain_of(url)
            if not domain or self._is_search_engine(domain):
                continue
            title = r.get("title", "")
            if not title:
                continue

            titles.append(f"{title} {r.get('snippet', '')}")
            social = self._social_name(domain)
            if self._is_wiki(domain):
                if wikipedia is None:
                    wikipedia = url
            elif social:
                socials.append({"network": social, "url": url})
            elif self._is_registry(domain):
                mentions.append({"title": title, "url": url})
            else:
                if website is None:
                    website = url
                mentions.append({"title": title, "url": url})

        return {
            "name": query,
            "wikipedia": wikipedia,
            "website": website,
            "socials": socials,
            "mentions": mentions[:7],
            "legal": self._extract_fields(" ".join(titles)),
        }

    @staticmethod
    def _extract_fields(text: str) -> dict:
        """Extract all legal fields from free text (snippets, titles, page text)."""
        result: dict = {}

        m = re.search(
            r"(?:ЄДРПОУ|код ЄДРПОУ|EDRPOU)[^0-9]{0,15}(\d{8})|\b(\d{8})\b", text, re.I
        )
        if m:
            result["edrpou"] = m.group(1) or m.group(2)

        m = re.search(
            r"(?:ТОВ|ТОВАРИСТВО З ОБМЕЖЕНОЮ ВІДПОВІДАЛЬНІСТЮ|ПАТ|ПрАТ|АТ|ПП|ФОП)\s*[«\"]([^»\"]+)[»\"]",
            text,
            re.I,
        )
        if m:
            result["name"] = m.group(1).strip()

        m = re.search(
            r"(?:організаційно-правова форма|організаційна форма|правова форма)"
            r"[^А-Яа-я]{0,10}([А-ЯІЇЄҐ][А-ЯІЇЄҐA-Za-z ()\-]{2,60})",
            text,
        )
        if m:
            result["legal_form"] = m.group(1).strip()

        m = re.search(
            r"(?:юридична адреса|адреса|місцезнаходження)[^А-Яа-я]{0,20}"
            r"([А-Яа-я0-9].*?)(?=\s*(?:Керівник|Директор|Стан|Статус|Дата|ЄДРПОУ|КВЕД|Основний|Контакт|Телефон|Статутний|$))",
            text,
            re.I,
        )
        if m:
            result["address"] = m.group(1).strip()

        m = re.search(
            r"(?:керівник|директор)[^А-Яа-я]{0,20}"
            r"([А-ЯІЇЄҐ][а-яіїєґ'’-]+\s+[А-ЯІЇЄҐ][а-яіїєґ'’-]+(?:\s+[А-ЯІЇЄҐ][а-яіїєґ'’-]+)?)",
            text,
        )
        if m:
            result["director"] = m.group(1).strip()

        m = re.search(
            r"(зареєстрована|припинена|в стані припинення|перебуває в стані припинення|ліквідована)",
            text,
            re.I,
        )
        if m:
            result["status"] = m.group(1)

        m = re.search(
            r"(?:дата реєстрації|дата державної реєстрації)[^0-9]{0,20}(\d{2}\.\d{2}\.\d{4})",
            text,
            re.I,
        )
        if m:
            result["registered_at"] = m.group(1)

        m = re.search(
            r"(?:основний вид діяльності|КВЕД)[^0-9]{0,20}(\d{2}\.\d{2}[^,;]{0,60})",
            text,
            re.I,
        )
        if m:
            result["activities"] = [m.group(1).strip()]

        m = re.search(
            r"(?:статутний капітал|розмір статутного капіталу)[^0-9]{0,20}([\d\s,\.]+(?:грн|₴|UAH)?)",
            text,
            re.I,
        )
        if m:
            result["capital"] = m.group(1).strip()

        m = re.search(
            r"(?:телефон|тел\.|контактний номер)[^0-9]{0,15}(\+?[\d][\d\s()\-]{8,17})",
            text,
            re.I,
        )
        if m:
            result["phone"] = m.group(1).strip()

        m = re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", text)
        if m:
            result["email"] = m.group(0)

        m = re.search(
            r"(?:контактна особа|контактна персона)[^А-Яа-я]{0,20}"
            r"([А-ЯІЇЄҐ][а-яіїєґ'’-]+\s+[А-ЯІЇЄҐ][а-яіїєґ'’-]+(?:\s+[А-ЯІЇЄҐ][а-яіїєґ'’-]+)?)",
            text,
            re.I,
        )
        if m:
            result["contact_person"] = m.group(1).strip()

        return result

    async def _profile_from_search(self, name: str, results: list[dict]) -> dict:
        """Aggregate search results + extract from pages into one record."""
        record = self._aggregate(name, results)
        page_legal = await self._extract_from_pages(results)
        legal = dict(record.get("legal") or {})
        for key, value in page_legal.items():
            if value and not legal.get(key):
                legal[key] = value
        if legal.get("name"):
            record["name"] = legal["name"]
        record["legal"] = legal
        record["all_results"] = results
        return record

    # ---------- page fetching / parsing ----------

    async def _fetch_page(self, url: str) -> str | None:
        try:
            async with httpx.AsyncClient(
                timeout=20.0, follow_redirects=True, headers=_HEADERS
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text
                if len(html) > 1000:
                    return html
        except Exception:
            pass
        return await self._fetch_page_playwright(url)

    async def _fetch_page_playwright(self, url: str) -> str | None:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                html = await page.content()
                await browser.close()
            return html
        except Exception:
            return None

    def _parse_legal_page(self, html: str) -> dict:
        result = self._extract_fields(_strip_tags(html))

        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.DOTALL)
        if m:
            name = _strip_tags(m.group(1))
            name = re.split(r"\s*[—|·–]\s*", name)[0].strip()
            if name:
                result["name"] = name
        return result

    async def _lookup_opendatabot(self, edrpou: str) -> dict:
        """OpenDataBot API (paid). Stub: returns {} unless a key is configured."""
        key = get_settings().opendatabot_api_key
        if not key:
            return {}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(
                    f"https://opendatabot.ua/api/v1/company/{edrpou}",
                    params={"apikey": key},
                )
                response.raise_for_status()
                data = response.json()
            # Map API fields (best-effort; refine once a real key is available).
            return {
                "edrpou": data.get("edrpou", edrpou),
                "name": data.get("name", ""),
                "address": data.get("address", ""),
                "director": data.get("director", ""),
                "status": data.get("status", ""),
            }
        except Exception:
            return {}

    async def _lookup_by_edrpou(self, edrpou: str) -> dict:
        legal = await self._lookup_opendatabot(edrpou)
        if legal.get("address") or legal.get("name"):
            legal.setdefault("edrpou", edrpou)
            return legal

        urls = [
            f"https://clarity-project.info/edr/{edrpou}",
            f"https://opendatabot.ua/c/{edrpou}",
            f"https://ring.org.ua/edr/uk/company/{edrpou}",
            f"https://youcontrol.com.ua/catalog/card-details/?id={edrpou}",
        ]
        legal = {"edrpou": edrpou}
        for url in urls:
            html = await self._fetch_page(url)
            if not html:
                continue
            parsed = self._parse_legal_page(html)
            for key, value in parsed.items():
                if value and not legal.get(key):
                    legal[key] = value
            if legal.get("address") and legal.get("name"):
                break
        return legal

    async def _extract_from_pages(self, results: list[dict]) -> dict:
        candidates = sorted(
            results,
            key=lambda r: not self._is_registry(self._domain_of(r.get("url", ""))),
        )[:5]

        pages = await asyncio.gather(
            *(self._fetch_page(r.get("url", "")) for r in candidates),
            return_exceptions=True,
        )

        legal: dict = {}
        for r, html in zip(candidates, pages):
            if not isinstance(html, str) or not html:
                continue
            parsed = self._parse_legal_page(html)
            for key, value in parsed.items():
                if value and not legal.get(key):
                    legal[key] = value
        return legal

    # ---------- normalize ----------

    def normalize_response(self, raw: dict) -> UniversalEntityCreate:
        name = str(raw.get("name") or "")
        legal = raw.get("legal") or {}
        geo = raw.get("geo")
        now = datetime.now(timezone.utc).isoformat()

        geo_prop = None
        if geo:
            geo_prop = GeoProperty(
                coordinates=geo.get("coordinates", [0.0, 0.0]),
                address=geo.get("address", ""),
            )

        properties = Properties(
            geo=geo_prop,
            metadata=Metadata(
                sources=[Source(name=self.source_name, confidence=0.6, last_verified=now)],
                completeness=0.6,
                risk_level="low",
            ),
            company={
                "edrpou": legal.get("edrpou", ""),
                "legal_form": legal.get("legal_form", ""),
                "address": legal.get("address", ""),
                "director": legal.get("director", ""),
                "contact_person": legal.get("contact_person", ""),
                "phone": legal.get("phone", ""),
                "email": legal.get("email", ""),
                "founders": legal.get("founders", ""),
                "registered_at": legal.get("registered_at", ""),
                "status": legal.get("status", ""),
                "activities": legal.get("activities", []),
                "capital": legal.get("capital", ""),
                "tax_status": legal.get("tax_status", ""),
                "contacts": legal.get("contacts", ""),
                "wikipedia": raw.get("wikipedia"),
                "website": raw.get("website"),
                "opendatabot_url": raw.get("opendatabot_url"),
                "images": raw.get("images", []),
                "socials": raw.get("socials", []),
                "mentions": raw.get("mentions", []),
            },
        )

        return UniversalEntityCreate(
            entity_type="company",
            entity_id=compute_entity_id("company", [name]) if name else None,
            entity_name=name or "unknown",
            properties=properties,
            raw_data={self.source_name: raw},
        )

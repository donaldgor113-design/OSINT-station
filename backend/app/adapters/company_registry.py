import hashlib
from datetime import datetime, timezone

from ..core.normalization import compute_entity_id
from ..schemas.universal_entity import (
    Metadata,
    Properties,
    Source,
    UniversalEntityCreate,
)
from .base import Adapter


class CompanyRegistryAdapter(Adapter):
    """Look up a Ukrainian company by name or ЄДРПОУ (spec Phase 4 — реєстри).

    Returns structured data split into legal info / online presence / mentions.
    Mock for now; real source is the state registry ЄДР (usr.minjust.gov.ua)
    or the OpenDataBot API (requires a key).
    """

    source_name = "company_registry"
    access_type = "api"

    _DIRECTORS = [
        "Коваленко Олексій В.",
        "Шевченко Ірина П.",
        "Бондаренко Максим С.",
        "Петренко Андрій Ю.",
    ]
    _CITIES = ["Київ", "Львів", "Одеса", "Дніпро", "Харків"]
    _STREETS = ["вул. Хрещатик", "просп. Свободи", "вул. Дерибасівська", "вул. Сумська"]
    _ACTIVITIES = [
        "62.01 Комп'ютерне програмування",
        "47.91 Роздрібна торгівля через Інтернет",
        "73.11 Рекламні агенції",
        "70.22 Консультування з питань керування",
    ]

    def __init__(self, mock: bool = True):
        self.mock = mock

    async def search(self, query: str) -> list[dict]:
        q = query.strip()
        if self._is_edrpou(q):
            return [self._record(edrpou=q, name=self._name_for(q))]
        return [self._record(edrpou=self._edrpou_for(q), name=q.title())]

    @staticmethod
    def _is_edrpou(q: str) -> bool:
        return q.isdigit() and len(q) == 8

    @staticmethod
    def _seed(s: str) -> int:
        return int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16)

    @staticmethod
    def _edrpou_for(name: str) -> str:
        return str(10000000 + CompanyRegistryAdapter._seed(name.lower()) % 89999999)

    @staticmethod
    def _name_for(edrpou: str) -> str:
        return f"ТОВ «Компанія {edrpou[-4:]}»"

    def _record(self, edrpou: str, name: str) -> dict:
        seed = self._seed(edrpou)
        city = self._CITIES[seed % len(self._CITIES)]
        street = self._STREETS[(seed // 7) % len(self._STREETS)]
        director = self._DIRECTORS[seed % len(self._DIRECTORS)]
        year = 2005 + seed % 20
        slug = name.lower().replace("«", "").replace("»", "").replace(" ", "-").replace("'", "")
        domain = slug or f"company-{edrpou}"

        return {
            "name": name,
            "edrpou": edrpou,
            "address": f"Україна, м. {city}, {street}, буд. {seed % 100 + 1}",
            "director": director,
            "status": "зареєстрована",
            "registered_at": f"{year}-{seed % 12 + 1:02d}-{seed % 28 + 1:02d}",
            "activities": [
                self._ACTIVITIES[seed % len(self._ACTIVITIES)],
                self._ACTIVITIES[(seed // 3) % len(self._ACTIVITIES)],
            ],
            "website": f"https://{domain}.ua",
            "socials": [
                {"network": "Facebook", "url": f"https://facebook.com/{domain}"},
                {"network": "Instagram", "url": f"https://instagram.com/{domain}"},
                {"network": "LinkedIn", "url": f"https://linkedin.com/company/{domain}"},
            ],
            "mentions": [
                {"title": f"{name} у новинах", "url": f"https://example.com/news/{domain}"},
                {"title": f"Профіль на порталі відгуків", "url": f"https://example.com/reviews/{domain}"},
            ],
        }

    def normalize_response(self, raw: dict) -> UniversalEntityCreate:
        edrpou = str(raw.get("edrpou") or "")
        name = str(raw.get("name") or "")
        now = datetime.now(timezone.utc).isoformat()

        properties = Properties(
            metadata=Metadata(
                sources=[Source(name=self.source_name, confidence=0.8, last_verified=now)],
                completeness=0.7,
                risk_level="low",
            ),
            company={
                "edrpou": edrpou,
                "address": raw.get("address", ""),
                "director": raw.get("director", ""),
                "status": raw.get("status", ""),
                "registered_at": raw.get("registered_at", ""),
                "activities": raw.get("activities", []),
                "website": raw.get("website", ""),
                "socials": raw.get("socials", []),
                "mentions": raw.get("mentions", []),
            },
        )

        key = edrpou if edrpou else name
        return UniversalEntityCreate(
            entity_type="company",
            entity_id=compute_entity_id("company", [key]) if key else None,
            entity_name=name or "unknown",
            properties=properties,
            raw_data={self.source_name: raw},
        )

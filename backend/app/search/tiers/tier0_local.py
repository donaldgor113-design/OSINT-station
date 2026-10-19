import time

from ...adapters.registry_search import RegistrySearchAdapter
from ...search.mapping import entity_create_to_dict
from .base import BaseTier, TierResult


class Tier0Local(BaseTier):
    """Локальна БД реєстрів (ЄДР) + кеш.

    Використовує наявний `RegistrySearchAdapter`, щоб не дублювати логіку
    і зберегти той самий `entity_id` (дедуплікація з наявними даними).
    """

    name = "tier0_local"

    def __init__(self, db, ai=None, cache=None):
        self.db = db
        self.cache = cache
        self._adapter = RegistrySearchAdapter(db)

    def is_available(self):
        return True, None  # завжди доступний

    async def search(self, query: str, query_type: str, workspace_id: int) -> TierResult:
        started = time.monotonic()

        cache_key = f"tier0:{query_type}:{query.lower()}"
        if self.cache is not None:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return TierResult(**cached)

        raw_items = await self._adapter.search(query)

        entities = []
        resolved_query = None
        for raw in raw_items:
            entity = self._adapter.normalize_response(raw)
            if not entity.entity_id:
                continue
            entities.append(entity_create_to_dict(entity))
            if entity.entity_name:
                resolved_query = entity.entity_name

        result = TierResult(
            tier_name=self.name,
            entities=entities,
            raw_sources=["local_registry"],
            resolved_query=resolved_query,
        )

        if self.cache is not None:
            await self.cache.set(cache_key, result.__dict__)

        result.duration_ms = int((time.monotonic() - started) * 1000)
        return result

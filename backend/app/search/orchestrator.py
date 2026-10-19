import asyncio
import logging
import time

from .confidence import compute_confidence
from .detector import detect_intent, detect_query_type
from .entity_extractor import extract_entities_from_documents
from .tiers import (
    Tier0Local,
    Tier1WebSearch,
    Tier2Dorking,
    Tier3Scraping,
    Tier4Specialized,
)
from .tiers.base import TierResult

logger = logging.getLogger(__name__)

# Tier3 навмисно відсутній у загальному списку — він enrichment-only
# і викликається явним кроком нижче, а не через уніфікований .search()
TIERS = [Tier0Local, Tier1WebSearch, Tier2Dorking, Tier4Specialized]

# Тіри, після яких має сенс пробувати AI-екстракцію (ті, що повертають
# сирі document-сутності, а не вже структуровані дані)
EXTRACTABLE_TIERS = {"tier1_web", "tier2_dorks"}


class SearchOrchestrator:
    """Каскадний пошук: Tier0 → Tier1 → Tier2 → Tier4 (+ Tier3 enrichment).

    Зупиняється, щойно накопичений набір сутностей досягає порогу
    впевненості (повнота структурованих полів, а не кількість лінків).
    """

    def __init__(self, db_session, ai_provider=None, cache=None):
        self.db = db_session
        self.ai = ai_provider
        self.cache = cache  # спільний кеш-сервіс, живе довше за один запит
        self._tier_instances = {
            tier_cls: tier_cls(self.db, self.ai, self.cache) for tier_cls in TIERS
        }
        self._tier3 = Tier3Scraping(self.db, self.ai)

    async def search(
        self,
        query: str,
        workspace_id: int,
        *,
        min_confidence: float = 0.6,
        force_tier: str | None = None,
    ) -> dict:
        query_type = detect_query_type(query)
        intent = detect_intent(query, query_type)

        logger.info(
            "Search start: query=%r type=%s intent=%s workspace=%s",
            query, query_type, intent, workspace_id,
        )

        collected: list[TierResult] = []
        final_entities: list[dict] = []
        resolved_query: str | None = None

        for tier_cls in TIERS:
            tier = self._tier_instances[tier_cls]

            if force_tier and tier.name != force_tier:
                continue

            available, reason = tier.is_available()
            if not available:
                collected.append(TierResult(tier_name=tier.name, skipped=True, skip_reason=reason))
                logger.info("Tier %s skipped: %s", tier.name, reason)
                continue

            started = time.monotonic()
            try:
                result = await asyncio.wait_for(
                    tier.search(resolved_query or query, query_type, workspace_id),
                    timeout=20.0,
                )
            except asyncio.TimeoutError:
                logger.warning("Tier %s timed out", tier.name)
                result = TierResult(tier_name=tier.name, error="timeout")
            except Exception as exc:  # noqa: BLE001
                logger.exception("Tier %s failed: %s", tier.name, exc)
                result = TierResult(tier_name=tier.name, error=str(exc))
            result.duration_ms = int((time.monotonic() - started) * 1000)
            collected.append(result)
            logger.info("Tier %s done: %d entities", tier.name, len(result.entities))

            if result.resolved_query:
                resolved_query = result.resolved_query

            final_entities = self._merge_entities(final_entities, result.entities)

            # AI-екстракція одразу поверх свіжих документів цього тіра
            if tier.name in EXTRACTABLE_TIERS and self.ai is not None:
                try:
                    extracted = await asyncio.wait_for(
                        extract_entities_from_documents(
                            self.ai, result.entities, query, query_type,
                        ),
                        timeout=30.0,
                    )
                except asyncio.TimeoutError:
                    extracted = []
                final_entities = self._soft_merge_by_name(final_entities, extracted)

            overall_confidence = compute_confidence(final_entities, intent)
            if not force_tier and overall_confidence >= min_confidence and final_entities:
                logger.info(
                    "Sufficient after %s (conf=%.2f) — stopping", tier.name, overall_confidence
                )
                break

            if force_tier and tier.name == force_tier:
                break
        else:
            # Жоден TIERS-тір не дав достатньої впевненості — пробуємо
            # enrichment: беремо топ-N ще не збагачених document-URL
            # і витягуємо повний текст, потім ще раз AI-екстракція.
            if not force_tier and self._tier3.is_available()[0]:
                top_urls = self._pick_urls_to_enrich(final_entities)
                if top_urls:
                    started = time.monotonic()
                    try:
                        enriched_docs = await asyncio.wait_for(
                            self._tier3.enrich_urls(top_urls), timeout=20.0,
                        )
                    except asyncio.TimeoutError:
                        enriched_docs = []
                    tier3_result = TierResult(
                        tier_name=self._tier3.name,
                        entities=enriched_docs,
                        duration_ms=int((time.monotonic() - started) * 1000),
                    )
                    collected.append(tier3_result)
                    final_entities = self._merge_entities(final_entities, enriched_docs)

                    if self.ai is not None:
                        try:
                            extracted = await asyncio.wait_for(
                                extract_entities_from_documents(
                                    self.ai, enriched_docs, query, query_type,
                                ),
                                timeout=30.0,
                            )
                        except asyncio.TimeoutError:
                            extracted = []
                        final_entities = self._soft_merge_by_name(final_entities, extracted)

        return {
            "query": query,
            "query_type": query_type,
            "intent": intent,
            "entities": final_entities,
            "confidence": compute_confidence(final_entities, intent),
            "tiers": [
                {
                    "name": r.tier_name,
                    "entities_count": len(r.entities),
                    "confidence": r.confidence,
                    "duration_ms": r.duration_ms,
                    "skipped": r.skipped,
                    "skip_reason": r.skip_reason,
                    "error": r.error,
                }
                for r in collected
            ],
            "stopped_at": collected[-1].tier_name if collected else None,
        }

    @staticmethod
    def _pick_urls_to_enrich(entities: list[dict], limit: int = 5) -> list[str]:
        urls = [
            e["properties"]["document"]["url"]
            for e in entities
            if e.get("entity_type") == "document"
            and e.get("properties", {}).get("document", {}).get("url")
        ]
        return urls[:limit]

    @staticmethod
    def _merge_entities(existing: list[dict], new: list[dict]) -> list[dict]:
        """Дедуплікація за entity_id. Нові дані зливаються в існуючі."""
        by_id = {e["entity_id"]: e for e in existing}
        for e in new:
            eid = e["entity_id"]
            by_id[eid] = _deep_merge(by_id[eid], e) if eid in by_id else e
        return list(by_id.values())

    @staticmethod
    def _soft_merge_by_name(existing: list[dict], new: list[dict]) -> list[dict]:
        """
        Для AI-екстрагованих сутностей: entity_id ненадійний (немає ЄДРПОУ/ІПН),
        тому зливаємо за збігом (entity_type, normalized entity_name).
        """

        def key(e: dict) -> tuple:
            return (e["entity_type"], e["entity_name"].strip().lower())

        by_key = {key(e): e for e in existing}
        for e in new:
            k = key(e)
            by_key[k] = _deep_merge(by_key[k], e) if k in by_key else e
        return list(by_key.values())


def _deep_merge(a: dict, b: dict) -> dict:
    """
    Зливає дві версії однієї сутності: properties — рекурсивно (b доповнює a,
    непорожні значення b мають пріоритет), sources і relations — обʼєднуються
    без дублікатів.
    """
    merged = dict(a)

    merged["properties"] = _deep_merge_dict(
        a.get("properties", {}), b.get("properties", {})
    )

    existing_sources = {
        s["name"]: s for s in a.get("properties", {}).get("metadata", {}).get("sources", [])
    }
    for s in b.get("properties", {}).get("metadata", {}).get("sources", []):
        existing_sources[s["name"]] = s
    merged.setdefault("properties", {}).setdefault("metadata", {})["sources"] = list(
        existing_sources.values()
    )

    existing_relations = {(r["target_id"], r["type"]) for r in a.get("relations", [])}
    merged_relations = list(a.get("relations", []))
    for r in b.get("relations", []):
        if (r.get("target_id"), r.get("type")) not in existing_relations:
            merged_relations.append(r)
    merged["relations"] = merged_relations

    merged["raw_data"] = {**a.get("raw_data", {}), **b.get("raw_data", {})}
    return merged


def _deep_merge_dict(a: dict, b: dict) -> dict:
    result = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge_dict(result[k], v)
        elif v:  # непорожнє значення з b перекриває a
            result[k] = v
    return result

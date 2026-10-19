import httpx
import pytest

from app.search.cache import SearchCache
from app.search.confidence import compute_confidence
from app.search.detector import detect_intent, detect_query_type
from app.search.mapping import dict_to_entity_create
from app.search.orchestrator import SearchOrchestrator, _deep_merge
from app.search.tiers import (
    Tier0Local,
    Tier1WebSearch,
    Tier2Dorking,
    Tier4Specialized,
)
from app.search.tiers import tier0_local, tier1_web
from app.search.tiers.base import TierResult


def _full_company() -> dict:
    return {
        "entity_type": "company",
        "entity_id": "edrpou:12345678",
        "entity_name": "ТОВ Ромашка",
        "properties": {
            "company": {
                "edrpou": "12345678",
                "name": "ТОВ Ромашка",
                "address": "Київ",
                "status": "active",
                "director": "Іванов",
                "owner": "Петров",
            },
            "metadata": {"sources": [{"name": "local_registry", "confidence": 0.95}]},
        },
        "relations": [],
        "raw_data": {},
    }


# --- detector -------------------------------------------------------------


def test_detect_query_type():
    assert detect_query_type("8.8.8.8") == "ip"
    assert detect_query_type("12345678") == "company_edrpou"
    assert detect_query_type("1234567890") == "person_ipn"
    assert detect_query_type("example.com") == "domain"
    assert detect_query_type("ТОВ Ромашка") == "text"
    assert detect_query_type("@user") == "handle"
    assert detect_query_type("50.45, 30.52") == "location"


def test_detect_intent():
    assert detect_intent("ТОВ Ромашка", "text") == "company-profile"
    assert detect_intent("example.com", "domain") == "domain-recon"
    assert detect_intent("12345678", "company_edrpou") == "company-profile"


# --- confidence -----------------------------------------------------------


def test_confidence_many_documents_without_structure_is_low():
    entities = [
        {
            "entity_type": "document",
            "entity_id": f"url:{i}",
            "entity_name": "doc",
            "properties": {"document": {"url": f"https://e/{i}"}},
        }
        for i in range(10)
    ]
    # Документи без структури не досягають порогу зупинки (0.6):
    # їхній внесок обмежений стелею 0.3 (min(0.3, n * 0.1)).
    assert compute_confidence(entities, "company-profile") <= 0.3
    assert compute_confidence(entities, "company-profile") < 0.6


def test_confidence_full_company_is_high():
    assert compute_confidence([_full_company()], "company-profile") >= 0.6


def test_confidence_general_discovery_uses_best_structured():
    entities = [_full_company()]
    assert compute_confidence(entities, "general-discovery") >= 0.6


# --- _deep_merge ----------------------------------------------------------


def test_deep_merge_merges_sources_and_relations():
    a = {
        "entity_id": "x",
        "properties": {"metadata": {"sources": [{"name": "a", "confidence": 0.5}]}},
        "relations": [],
        "raw_data": {"a": {}},
    }
    b = {
        "entity_id": "x",
        "properties": {"metadata": {"sources": [{"name": "b", "confidence": 0.7}]}},
        "relations": [{"target_id": "y", "type": "owns"}],
        "raw_data": {"b": {}},
    }
    merged = _deep_merge(a, b)
    assert {s["name"] for s in merged["properties"]["metadata"]["sources"]} == {"a", "b"}
    assert merged["relations"] == [{"target_id": "y", "type": "owns"}]
    assert merged["raw_data"] == {"a": {}, "b": {}}


# --- orchestrator ---------------------------------------------------------


@pytest.mark.asyncio
async def test_orchestrator_stops_early(monkeypatch):
    calls = []

    async def fake_t0(self, query, query_type, workspace_id):
        calls.append("tier0")
        return TierResult(
            tier_name="tier0_local",
            entities=[_full_company()],
            raw_sources=["local_registry"],
        )

    async def fake_t1(self, query, query_type, workspace_id):
        calls.append("tier1")
        return TierResult(tier_name="tier1_web", entities=[])

    monkeypatch.setattr(tier0_local.Tier0Local, "search", fake_t0)
    monkeypatch.setattr(tier1_web.Tier1WebSearch, "search", fake_t1)

    orchestrator = SearchOrchestrator(db_session=None, ai_provider=None)
    result = await orchestrator.search("12345678", workspace_id=1)

    assert "tier1" not in calls
    assert result["stopped_at"] == "tier0_local"
    assert result["confidence"] >= 0.6


@pytest.mark.asyncio
async def test_orchestrator_calls_tier3_enrichment(monkeypatch):
    enriched_urls = []

    async def fake_t1(self, query, query_type, workspace_id):
        return TierResult(
            tier_name="tier1_web",
            entities=[{
                "entity_type": "document",
                "entity_id": "url:https://example.com",
                "entity_name": "Example",
                "properties": {"document": {"url": "https://example.com"}},
            }],
        )

    async def fake_empty(self, query, query_type, workspace_id):
        return TierResult(tier_name=self.name, entities=[])

    monkeypatch.setattr(tier1_web.Tier1WebSearch, "search", fake_t1)
    for cls in (Tier0Local, Tier2Dorking, Tier4Specialized):
        monkeypatch.setattr(cls, "search", fake_empty)

    orchestrator = SearchOrchestrator(db_session=None, ai_provider=None)

    async def fake_enrich(urls):
        enriched_urls.extend(urls)
        return []

    monkeypatch.setattr(orchestrator._tier3, "enrich_urls", fake_enrich)

    await orchestrator.search("example.com", workspace_id=1)

    assert enriched_urls == ["https://example.com"]


# --- tier availability ----------------------------------------------------


def test_tier4_skipped_without_keys(monkeypatch):
    monkeypatch.delenv("SHODAN_API_KEY", raising=False)
    monkeypatch.delenv("SERPER_API_KEY", raising=False)

    tier = Tier4Specialized(db=None)
    available, reason = tier.is_available()
    assert available is False
    assert "no specialized API keys" in reason


# --- cache ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_cache_roundtrip():
    cache = SearchCache(redis_url=None, ttl_seconds=60)
    assert await cache.get("k") is None
    await cache.set("k", {"a": 1})
    assert await cache.get("k") == {"a": 1}


# --- mapping --------------------------------------------------------------


def test_dict_to_entity_create_converts_target_name_relations():
    data = {
        "entity_type": "company",
        "entity_id": "x",
        "entity_name": "ТОВ Ромашка",
        "properties": {"company": {"edrpou": "12345678"}},
        "relations": [{"target_name": "Іванов", "type": "director_of", "confidence": 0.8}],
        "raw_data": {},
    }
    entity = dict_to_entity_create(data)
    assert entity.relations[0].target_id == "ref:іванов"
    assert entity.relations[0].type == "director_of"


# --- URL encoding (respx, опційно) ---------------------------------------


def test_tier1_encodes_cyrillic_query():
    respx = pytest.importorskip("respx")
    from app.search.tiers.tier1_web import Tier1WebSearch

    with respx.mock(assert_all_called=False) as mock:
        mock.get(url__regex=r"https://s\.jina\.ai/.*").mock(
            return_value=httpx.Response(200, text="")
        )
        import asyncio

        async def run():
            tier = Tier1WebSearch(db=None)
            async with httpx.AsyncClient() as client:
                await tier._jina_search(client, "ТОВ Ромашка")

        asyncio.run(run())

        assert mock.calls, "Jina request was not made"
        url = str(mock.calls[0].request.url)
        assert "ТОВ" not in url
        assert "%D0%A2%D0%9E%D0%92" in url

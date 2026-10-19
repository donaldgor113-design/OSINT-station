import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ...ai.providers import get as get_ai_provider
from ...config import get_settings
from ...database import get_db
from ...schemas.universal_entity import CascadeSearchResponse, SearchRequest, TierInfo
from ...search.mapping import dict_to_entity_create
from ...search.orchestrator import SearchOrchestrator
from ...services import entity_to_read, upsert_entity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])


def _resolve_ai_provider(db):
    """AI-провайдер для каскаду — тільки якщо він реально налаштований.

    Якщо ключів немає і `AI_PROVIDER` не вказує на конкретного провайдера —
    повертаємо None, щоб каскад не гаяв час на недоступну AI-екстракцію.
    """
    settings = get_settings()
    if settings.anthropic_api_key and not settings.anthropic_mock:
        return get_ai_provider("claude", db)
    if settings.openai_api_key:
        return get_ai_provider("openai", db)
    if settings.ai_provider == "ollama":
        return get_ai_provider("ollama", db)
    return None


@router.post("/search", response_model=CascadeSearchResponse)
async def search(body: SearchRequest, request: Request, db: Session = Depends(get_db)):
    """Каскадний пошук (Tier0 → Tier4).

    Зберігає знайдені сутності в БД і повертає їх разом зі зведенням
    по рівнях. Поле `results` залишено для сумісності зі старим форматом.
    """
    cache = getattr(request.app.state, "search_cache", None)

    orchestrator = SearchOrchestrator(
        db_session=db,
        ai_provider=_resolve_ai_provider(db),
        cache=cache,
    )

    result = await orchestrator.search(
        query=body.query,
        workspace_id=body.workspace_id,
        force_tier=body.force_tier,
        min_confidence=body.min_confidence,
    )

    results = []
    for data in result["entities"]:
        entity = dict_to_entity_create(data)
        stored = upsert_entity(db, entity, body.workspace_id)
        results.append(entity_to_read(stored))

    return CascadeSearchResponse(
        query=result["query"],
        source="cascade",
        query_type=result["query_type"],
        intent=result["intent"],
        confidence=result["confidence"],
        results=results,
        tiers=[TierInfo(**t) for t in result["tiers"]],
        stopped_at=result["stopped_at"],
    )

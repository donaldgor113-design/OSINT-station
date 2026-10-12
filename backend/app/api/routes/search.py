import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...adapters.factory import build_adapter
from ...adapters.registry_search import RegistrySearchAdapter
from ...database import get_db
from ...schemas.universal_entity import SearchRequest, SearchResponse
from ...services import entity_to_read, upsert_entity

router = APIRouter(prefix="/api", tags=["search"])


def detect_source(query: str) -> str:
    """Pick the right web adapter for a query (fallback path)."""
    q = query.strip()
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", q):
        return "shodan"
    if q.isdigit() and len(q) in (8, 10):
        return "company_profile"
    if re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)+", q, re.IGNORECASE):
        return "whois"
    return "company_profile"


@router.post("/search", response_model=SearchResponse)
async def search(body: SearchRequest, db: Session = Depends(get_db)):
    # 1. Try the local registry DB first (imported ЄДР data).
    registry = RegistrySearchAdapter(db)
    registry_raw = await registry.search(body.query)
    if registry_raw:
        results = []
        for raw in registry_raw:
            entity = registry.normalize_response(raw)
            if not entity.entity_id:
                continue
            stored = upsert_entity(db, entity, body.workspace_id)
            results.append(entity_to_read(stored))
        if results:
            return SearchResponse(query=body.query, source="registry", results=results)

    # 2. Fall back to web adapters.
    source = body.source if body.source != "auto" else detect_source(body.query)
    adapter = build_adapter(source)
    if adapter is None:
        raise HTTPException(status_code=404, detail=f"Unknown source: {source}")

    try:
        raw_items = await adapter.search(body.query)
    except Exception:
        raw_items = []

    results = []
    for raw in raw_items:
        entity = adapter.normalize_response(raw)
        if not entity.entity_id:
            continue
        stored = upsert_entity(db, entity, body.workspace_id)
        results.append(entity_to_read(stored))

    return SearchResponse(query=body.query, source=source, results=results)

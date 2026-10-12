from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...ai import detect_anomalies, get_provider
from ...database import get_db
from ...models.universal_entity import UniversalEntity
from ...schemas.universal_entity import AnalyzeRequest, AnalyzeResponse
from ...services import compact_entity

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(body: AnalyzeRequest, db: Session = Depends(get_db)):
    query = db.query(UniversalEntity).filter(
        UniversalEntity.workspace_id == body.workspace_id
    )
    if body.entity_ids:
        query = query.filter(UniversalEntity.entity_id.in_(body.entity_ids))
    entities = query.all()

    compact = [compact_entity(e) for e in entities]

    provider = get_provider(body.provider, db)
    summary = await provider.summarize(compact)
    cross_check = await provider.cross_check(compact)
    anomalies = detect_anomalies(compact)

    return AnalyzeResponse(summary=summary, cross_check=cross_check, anomalies=anomalies)

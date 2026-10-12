from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.universal_entity import UniversalEntity
from ...schemas.universal_entity import UniversalEntityRead
from ...services import entity_to_read

router = APIRouter(prefix="/api/entities", tags=["entities"])


@router.get("", response_model=list[UniversalEntityRead])
def list_entities(workspace_id: int, db: Session = Depends(get_db)):
    entities = (
        db.query(UniversalEntity)
        .filter(UniversalEntity.workspace_id == workspace_id)
        .order_by(UniversalEntity.id.desc())
        .all()
    )
    return [entity_to_read(e) for e in entities]


@router.get("/{entity_id}", response_model=UniversalEntityRead)
def get_entity(entity_id: str, workspace_id: int, db: Session = Depends(get_db)):
    entity = (
        db.query(UniversalEntity)
        .filter(
            UniversalEntity.workspace_id == workspace_id,
            UniversalEntity.entity_id == entity_id,
        )
        .first()
    )
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity_to_read(entity)

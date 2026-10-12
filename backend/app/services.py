from sqlalchemy.orm import Session

from .core.normalization import merge_entity
from .models.universal_entity import UniversalEntity
from .schemas.universal_entity import (
    Properties,
    Relation,
    UniversalEntityCreate,
    UniversalEntityRead,
)


def entity_to_orm(create: UniversalEntityCreate, workspace_id: int) -> UniversalEntity:
    return UniversalEntity(
        workspace_id=workspace_id,
        entity_type=create.entity_type,
        entity_id=create.entity_id,
        entity_name=create.entity_name,
        properties=create.properties.model_dump(exclude_none=True) if create.properties else {},
        relations=[r.model_dump() for r in create.relations],
        raw_data=create.raw_data,
    )


def entity_to_read(entity: UniversalEntity) -> UniversalEntityRead:
    return UniversalEntityRead(
        id=entity.id,
        entity_type=entity.entity_type,
        entity_id=entity.entity_id,
        entity_name=entity.entity_name,
        properties=Properties.model_validate(entity.properties) if entity.properties else None,
        relations=[Relation.model_validate(r) for r in (entity.relations or [])],
        raw_data=entity.raw_data or {},
    )


def upsert_entity(
    db: Session, create: UniversalEntityCreate, workspace_id: int
) -> UniversalEntity:
    if not create.entity_id:
        raise ValueError("entity_id is required to upsert")

    existing = (
        db.query(UniversalEntity)
        .filter(
            UniversalEntity.workspace_id == workspace_id,
            UniversalEntity.entity_id == create.entity_id,
        )
        .first()
    )
    if existing:
        merge_entity(existing, create)
        stored = existing
    else:
        stored = entity_to_orm(create, workspace_id)
        db.add(stored)

    db.commit()
    db.refresh(stored)
    return stored


def compact_entity(entity: UniversalEntity) -> dict:
    """Reduce an entity to a small dict suitable for an AI prompt.

    Drops the raw payload so we never send source blobs to a model.
    """
    props = entity.properties or {}
    geo = props.get("geo") or {}
    meta = props.get("metadata") or {}
    temporal = props.get("temporal") or {}
    return {
        "id": entity.entity_id,
        "type": entity.entity_type,
        "name": entity.entity_name,
        "city": geo.get("city", ""),
        "country": geo.get("country", ""),
        "coordinates": geo.get("coordinates", []),
        "observed_at": temporal.get("observed_at") or temporal.get("created"),
        "sources": [s.get("name") for s in meta.get("sources", [])],
    }

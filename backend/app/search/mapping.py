import re

from ..core.normalization import compute_entity_id
from ..schemas.universal_entity import UniversalEntityCreate


def entity_create_to_dict(entity: UniversalEntityCreate) -> dict:
    """UniversalEntityCreate (Pydantic) -> словник каскаду."""
    return {
        "entity_type": entity.entity_type,
        "entity_id": entity.entity_id,
        "entity_name": entity.entity_name,
        "properties": (
            entity.properties.model_dump(exclude_none=True) if entity.properties else {}
        ),
        "relations": [r.model_dump() for r in entity.relations],
        "raw_data": entity.raw_data or {},
    }


def dict_to_entity_create(data: dict) -> UniversalEntityCreate:
    """Словник каскаду -> UniversalEntityCreate.

    Обробляє два формати relations: повний (`target_id`) і скорочений
    (`target_name` з AI-екстракції). Для `target_name` синтезується
    стабільний `target_id`, щоб не порушувати схему Relation.
    """
    relations = []
    for rel in data.get("relations", []) or []:
        target_id = rel.get("target_id")
        if not target_id:
            name = (rel.get("target_name") or "").strip().lower()
            target_id = "ref:" + re.sub(r"\s+", " ", name)
        relations.append(
            {
                "target_id": target_id,
                "type": rel.get("type", "related"),
                "confidence": rel.get("confidence", 0.0),
            }
        )

    entity_id = data.get("entity_id")
    if not entity_id:
        entity_id = compute_entity_id(
            data.get("entity_type", "document"),
            [data.get("entity_name", "")],
        )

    properties = data.get("properties")
    return UniversalEntityCreate(
        entity_type=data.get("entity_type", "document"),
        entity_id=entity_id,
        entity_name=data.get("entity_name", ""),
        properties=properties or None,
        relations=relations,
        raw_data=data.get("raw_data", {}) or {},
    )

import hashlib
from datetime import datetime, timezone

from ..models.universal_entity import UniversalEntity
from ..schemas.universal_entity import UniversalEntityCreate


def compute_entity_id(entity_type: str, key_fields: list[str]) -> str:
    """Deterministic hash of normalized key fields (spec §4).

    Two sources describing the same object produce the same id, so records
    merge instead of duplicating.
    """
    parts = [entity_type] + [str(f).strip().lower() for f in key_fields if str(f).strip()]
    normalized = "|".join(parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def merge_entity(existing: UniversalEntity, incoming: UniversalEntityCreate) -> None:
    """Merge an incoming normalized entity into an existing stored entity.

    Preserves the original raw response per source (for audit) and deduplicates
    the sources list so cross-source confidence stays honest.
    """
    # raw_data: keep every source's original payload untouched.
    merged_raw = dict(existing.raw_data or {})
    incoming_source = list(incoming.raw_data.keys())[0] if incoming.raw_data else "unknown"
    merged_raw[incoming_source] = incoming.raw_data.get(incoming_source, {})

    # sources: append new sources, dedupe by name, keep highest confidence.
    inc_props = incoming.properties
    inc_meta = inc_props.metadata if inc_props else None
    inc_sources = [s.model_dump() for s in (inc_meta.sources or [])] if inc_meta else []

    cur_props = dict(existing.properties or {})
    cur_meta = dict(cur_props.get("metadata") or {})
    cur_sources = list(cur_meta.get("sources") or [])

    by_name: dict[str, dict] = {}
    for s in cur_sources:
        by_name[s.get("name")] = s
    for s in inc_sources:
        name = s.get("name")
        if name not in by_name:
            by_name[name] = s
        else:
            by_name[name]["confidence"] = max(
                by_name[name].get("confidence", 0.0), s.get("confidence", 0.0)
            )

    new_meta = dict(cur_meta)
    new_meta["sources"] = list(by_name.values())
    new_meta["completeness"] = max(
        cur_meta.get("completeness", 0.0), (inc_meta.completeness if inc_meta else 0.0)
    )

    new_props = dict(cur_props)
    new_props["metadata"] = new_meta
    new_props["temporal"] = {
        **(cur_props.get("temporal") or {}),
        "updated": _now_iso(),
    }

    # Merge the incoming entity-specific fields (company/geo/domain/document/...)
    # so re-searching the same entity with fresher data actually updates it.
    if inc_props:
        inc_dict = inc_props.model_dump(exclude_none=True)
        for key, value in inc_dict.items():
            if key in ("metadata", "temporal"):
                continue
            if key == "company" and isinstance(value, dict) and isinstance(new_props.get("company"), dict):
                merged_company = dict(new_props["company"])
                for k, v in value.items():
                    if v or k not in merged_company:
                        merged_company[k] = v
                new_props["company"] = merged_company
            else:
                new_props[key] = value

    incoming_relations = [r.model_dump() for r in incoming.relations]

    existing.properties = new_props
    existing.raw_data = merged_raw
    existing.relations = existing.relations or incoming_relations

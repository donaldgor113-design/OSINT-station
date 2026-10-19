from typing import Any

# Ключові поля для кожного типу сутності. Порожній список (document) —
# означає "сам факт існування не підвищує впевненість", обробляється окремо.
KEY_FIELDS: dict[str, list[str]] = {
    "company": ["edrpou", "name", "address", "status", "director", "owner"],
    "person": ["full_name", "dob", "address", "phone"],
    "financial_account": ["account_number", "owner", "balance"],
    "ip": ["ip", "org", "open_ports", "country"],
    "domain": ["domain", "registrar", "created"],
    "location": ["coordinates", "address"],
}

# document не має "повноти" — кожен додає фіксовану, невелику вагу,
# щоб сама по собі купа посилань ніколи не досягла порогу зупинки
DOCUMENT_WEIGHT = 0.1

# Який entity_type вважається "головним" для кожного наміру пошуку —
# саме його повноту і перевіряє каскад перед зупинкою
PRIMARY_TYPE_BY_INTENT = {
    "company-profile": "company",
    "person-profile": "person",
    "person-organization": "person",
    "ip-recon": "ip",
    "domain-recon": "domain",
    "geo-context": "location",
    "contact-discovery": "person",
    "social-profile": "person",
    "public-documents": None,   # немає єдиної "головної" сутності
    "media-discovery": None,
    "general-discovery": None,
}


def _entity_completeness(entity: dict[str, Any]) -> float:
    """Частка заповнених ключових полів для однієї сутності (0.0-1.0)."""
    etype = entity.get("entity_type")
    fields = KEY_FIELDS.get(etype)
    if not fields:
        return 0.0

    props = entity.get("properties", {}).get(etype, {})
    # fallback: деякі адаптери кладуть поля прямо в properties без вкладеного ключа
    if not props:
        props = entity.get("properties", {})

    filled = sum(1 for f in fields if props.get(f))
    return filled / len(fields)


def compute_confidence(entities: list[dict[str, Any]], intent: str) -> float:
    """
    Головна зупиняюча метрика каскаду.
    Якщо в намірі немає чіткого "головного" типу (general-discovery тощо) —
    рахуємо м'яко: найповніша сутність будь-якого типу, що має KEY_FIELDS.
    """
    primary = PRIMARY_TYPE_BY_INTENT.get(intent)

    candidates = entities if primary is None else [
        e for e in entities if e.get("entity_type") == primary
    ]
    structured = [e for e in candidates if e.get("entity_type") in KEY_FIELDS]

    best_structured = max((_entity_completeness(e) for e in structured), default=0.0)

    doc_count = sum(1 for e in entities if e.get("entity_type") == "document")
    doc_bonus = min(0.3, doc_count * DOCUMENT_WEIGHT)  # документи — лише бонус, стеля 0.3

    # Структуровані дані завжди важать більше: документи ніколи не
    # дотягують самі по собі до порогу зупинки (0.6 за замовчуванням)
    return min(1.0, best_structured + (doc_bonus if best_structured == 0 else doc_bonus * 0.3))

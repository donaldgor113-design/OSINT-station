"""Import ЄДР data (legal entities + ФОП) into the local registry DB.

The data.gov.ua dataset "Єдиний державний реєстр юридичних осіб, фізичних
осіб-підприємців та громадських формувань" is provided as JSON/XML resources.
Field names may vary between exports, so the importer maps common aliases.

Usage:
    python -m scripts.import_registry path/to/file.json
"""

from sqlalchemy.orm import Session

from ..models.registry import IndividualEntrepreneur, LegalEntity

# Common data.gov.ua field aliases -> our schema fields.
_LEGAL_MAP = {
    "edrpou": ("edrpou", "code", "код", "kod"),
    "name": ("name", "назва", "full_name", "повна_назва"),
    "short_name": ("short_name", "скорочена_назва"),
    "legal_form": ("legal_form", "организационно_правовая_форма", "опф"),
    "status": ("status", "stan", "стан", "статус"),
    "registered_at": ("registration_date", "registered_at", "дата_реєстрації"),
    "address": ("address", "адреса", "location"),
    "director": ("boss", "director", "керівник", "kerivnyk"),
    "founders": ("founders", "засновники", "zasnovnyky"),
    "kved": ("kveds", "kved", "квед"),
    "capital": ("capital", "статутний_капітал", "statutnyi_kapital"),
    "phone": ("phone", "телефон"),
    "email": ("email", "емайл"),
    "beneficiaries": ("beneficiaries", "бенефіціари", "kintsovi_benefitsiary"),
}

_FOP_MAP = {
    "rnokpp": ("rnokpp", "ipn", "іпн", "ipn_code", "code"),
    "name": ("name", "піб", "fio", "full_name"),
    "status": ("status", "stan", "стан"),
    "registered_at": ("registration_date", "registered_at", "дата_реєстрації"),
    "address": ("address", "адреса"),
    "kved": ("kveds", "kved", "квед"),
    "contacts": ("contacts", "контакти"),
}


def _pick(record: dict, aliases: tuple[str, ...]):
    for a in aliases:
        if a in record and record[a] not in (None, ""):
            return record[a]
    return None


def _to_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return ""
    return str(value).strip()


def _to_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [v.strip() for v in value.split(";") if v.strip()]
    return [str(value)]


def map_legal_record(record: dict) -> dict:
    return {
        "edrpou": _to_str(_pick(record, _LEGAL_MAP["edrpou"])),
        "name": _to_str(_pick(record, _LEGAL_MAP["name"])),
        "short_name": _to_str(_pick(record, _LEGAL_MAP["short_name"])),
        "legal_form": _to_str(_pick(record, _LEGAL_MAP["legal_form"])),
        "status": _to_str(_pick(record, _LEGAL_MAP["status"])),
        "registered_at": _to_str(_pick(record, _LEGAL_MAP["registered_at"])),
        "address": _to_str(_pick(record, _LEGAL_MAP["address"])),
        "director": _to_str(_pick(record, _LEGAL_MAP["director"])),
        "founders": _to_list(_pick(record, _LEGAL_MAP["founders"])),
        "kved": _to_list(_pick(record, _LEGAL_MAP["kved"])),
        "capital": _to_str(_pick(record, _LEGAL_MAP["capital"])),
        "phone": _to_str(_pick(record, _LEGAL_MAP["phone"])),
        "email": _to_str(_pick(record, _LEGAL_MAP["email"])),
        "beneficiaries": _to_list(_pick(record, _LEGAL_MAP["beneficiaries"])),
        "raw": record,
    }


def map_fop_record(record: dict) -> dict:
    return {
        "rnokpp": _to_str(_pick(record, _FOP_MAP["rnokpp"])),
        "name": _to_str(_pick(record, _FOP_MAP["name"])),
        "status": _to_str(_pick(record, _FOP_MAP["status"])),
        "registered_at": _to_str(_pick(record, _FOP_MAP["registered_at"])),
        "address": _to_str(_pick(record, _FOP_MAP["address"])),
        "kved": _to_list(_pick(record, _FOP_MAP["kved"])),
        "contacts": _pick(record, _FOP_MAP["contacts"]) or {},
        "raw": record,
    }


def import_legal_entities(db: Session, records: list[dict]) -> int:
    count = 0
    for rec in records:
        mapped = map_legal_record(rec)
        if not mapped["edrpou"]:
            continue
        exists = db.query(LegalEntity).filter(LegalEntity.edrpou == mapped["edrpou"]).first()
        if exists:
            continue
        db.add(LegalEntity(**mapped))
        count += 1
    db.commit()
    return count


def import_individual_entrepreneurs(db: Session, records: list[dict]) -> int:
    count = 0
    for rec in records:
        mapped = map_fop_record(rec)
        if not mapped["rnokpp"]:
            continue
        exists = (
            db.query(IndividualEntrepreneur)
            .filter(IndividualEntrepreneur.rnokpp == mapped["rnokpp"])
            .first()
        )
        if exists:
            continue
        db.add(IndividualEntrepreneur(**mapped))
        count += 1
    db.commit()
    return count

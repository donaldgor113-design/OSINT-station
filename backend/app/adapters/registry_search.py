from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..core.normalization import compute_entity_id
from ..models.registry import IndividualEntrepreneur, LegalEntity
from ..schemas.universal_entity import (
    Metadata,
    Properties,
    Source,
    UniversalEntityCreate,
)
from .base import Adapter


class RegistrySearchAdapter(Adapter):
    """Search the local ЄДР DB (imported from data.gov.ua) instead of the web."""

    source_name = "registry"
    access_type = "api"

    def __init__(self, db: Session):
        self.db = db

    async def search(self, query: str) -> list[dict]:
        q = query.strip()

        if q.isdigit() and len(q) == 8:
            e = self.db.query(LegalEntity).filter(LegalEntity.edrpou == q).first()
            return [self._legal_raw(e)] if e else []

        if q.isdigit() and len(q) == 10:
            e = (
                self.db.query(IndividualEntrepreneur)
                .filter(IndividualEntrepreneur.rnokpp == q)
                .first()
            )
            return [self._fop_raw(e)] if e else []

        entities = (
            self.db.query(LegalEntity)
            .filter(LegalEntity.name.ilike(f"%{q}%"))
            .limit(5)
            .all()
        )
        return [self._legal_raw(e) for e in entities]

    @staticmethod
    def _legal_raw(e) -> dict:
        return {
            "kind": "legal",
            "edrpou": e.edrpou,
            "name": e.name or e.short_name,
            "short_name": e.short_name,
            "legal_form": e.legal_form,
            "status": e.status,
            "registered_at": e.registered_at,
            "address": e.address,
            "director": e.director,
            "founders": e.founders or [],
            "activities": e.kved or [],
            "capital": e.capital,
            "phone": e.phone,
            "email": e.email,
            "beneficiaries": e.beneficiaries or [],
        }

    @staticmethod
    def _fop_raw(e) -> dict:
        contacts = e.contacts or {}
        return {
            "kind": "fop",
            "rnokpp": e.rnokpp,
            "name": e.name,
            "status": e.status,
            "registered_at": e.registered_at,
            "address": e.address,
            "activities": e.kved or [],
            "phone": contacts.get("phone", ""),
            "email": contacts.get("email", ""),
        }

    def normalize_response(self, raw: dict) -> UniversalEntityCreate:
        name = raw.get("name") or raw.get("edrpou") or raw.get("rnokpp") or "unknown"
        edrpou = raw.get("edrpou") or raw.get("rnokpp") or ""
        now = datetime.now(timezone.utc).isoformat()

        properties = Properties(
            metadata=Metadata(
                sources=[Source(name="registry", confidence=0.95, last_verified=now)],
                completeness=0.9,
                risk_level="low",
            ),
            company={
                "edrpou": edrpou,
                "legal_form": raw.get("legal_form", ""),
                "address": raw.get("address", ""),
                "director": raw.get("director", ""),
                "phone": raw.get("phone", ""),
                "email": raw.get("email", ""),
                "founders": ", ".join(raw.get("founders", [])),
                "beneficiaries": ", ".join(raw.get("beneficiaries", [])),
                "registered_at": raw.get("registered_at", ""),
                "status": raw.get("status", ""),
                "activities": raw.get("activities", []),
                "capital": raw.get("capital", ""),
            },
        )

        key = edrpou if edrpou else name
        return UniversalEntityCreate(
            entity_type="company",
            entity_id=compute_entity_id("company", [key]) if key else None,
            entity_name=name,
            properties=properties,
            raw_data={self.source_name: raw},
        )

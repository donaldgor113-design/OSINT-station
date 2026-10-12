from sqlalchemy import JSON, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base

_JSON = JSON().with_variant(JSONB(), "postgresql")


class LegalEntity(Base):
    """Юридична особа (ЄДР) — імпортована з data.gov.ua."""

    __tablename__ = "legal_entities"
    __table_args__ = (
        Index("ix_legal_edrpou", "edrpou"),
        Index("ix_legal_name", "name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    edrpou: Mapped[str] = mapped_column(String(16), unique=True)
    name: Mapped[str] = mapped_column(String(500), default="")
    short_name: Mapped[str] = mapped_column(String(300), default="")
    legal_form: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(100), default="")
    registered_at: Mapped[str] = mapped_column(String(32), default="")
    address: Mapped[str] = mapped_column(String(500), default="")
    director: Mapped[str] = mapped_column(String(300), default="")
    founders: Mapped[list] = mapped_column(_JSON, default=list)
    kved: Mapped[list] = mapped_column(_JSON, default=list)
    capital: Mapped[str] = mapped_column(String(100), default="")
    phone: Mapped[str] = mapped_column(String(100), default="")
    email: Mapped[str] = mapped_column(String(200), default="")
    beneficiaries: Mapped[list] = mapped_column(_JSON, default=list)
    raw: Mapped[dict] = mapped_column(_JSON, default=dict)


class IndividualEntrepreneur(Base):
    """ФОП (фізична особа-підприємець, РНОКПП) — імпортована з data.gov.ua."""

    __tablename__ = "individual_entrepreneurs"
    __table_args__ = (
        Index("ix_fop_rnokpp", "rnokpp"),
        Index("ix_fop_name", "name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rnokpp: Mapped[str] = mapped_column(String(16), unique=True)
    name: Mapped[str] = mapped_column(String(300), default="")
    status: Mapped[str] = mapped_column(String(100), default="")
    registered_at: Mapped[str] = mapped_column(String(32), default="")
    address: Mapped[str] = mapped_column(String(500), default="")
    kved: Mapped[list] = mapped_column(_JSON, default=list)
    contacts: Mapped[dict] = mapped_column(_JSON, default=dict)
    raw: Mapped[dict] = mapped_column(_JSON, default=dict)

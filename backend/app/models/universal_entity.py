from sqlalchemy import JSON, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base

# JSON on SQLite (tests) / JSONB on PostgreSQL (production).
_JSON = JSON().with_variant(JSONB(), "postgresql")


class UniversalEntity(Base):
    """Unified data model — every source normalizes into this shape (spec §4).

    Entities are scoped to a workspace; `entity_id` is unique *within* a
    workspace (spec: "хеш, унікальний у межах воркспейсу").
    """

    __tablename__ = "universal_entities"
    __table_args__ = (
        UniqueConstraint("workspace_id", "entity_id", name="uq_workspace_entity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspaces.id"), index=True
    )
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    entity_name: Mapped[str] = mapped_column(String(255), index=True)

    # Structured, typed fields live inside the flexible JSON blobs so that new
    # source-specific fields can be added without schema migrations.
    properties: Mapped[dict] = mapped_column(_JSON, default=dict)
    relations: Mapped[list] = mapped_column(_JSON, default=list)
    raw_data: Mapped[dict] = mapped_column(_JSON, default=dict)

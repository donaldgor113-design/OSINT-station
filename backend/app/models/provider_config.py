from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class ProviderConfig(Base):
    """A user-defined AI provider (any OpenAI-compatible API, Ollama, Claude).

    Stored so users are not limited to the built-in model list.
    NOTE: api_key is stored in plaintext for the PoC — production must encrypt
    (spec §9: Vault / Secrets Manager).
    """

    __tablename__ = "ai_providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    # "openai" (OpenAI-compatible) | "ollama" | "claude"
    kind: Mapped[str] = mapped_column(String(20), default="openai")
    base_url: Mapped[str] = mapped_column(String(500), default="")
    api_key: Mapped[str] = mapped_column(String(500), default="")
    model: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

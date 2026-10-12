from datetime import datetime, timezone

from ..core.normalization import compute_entity_id
from ..schemas.universal_entity import (
    DigitalFootprint,
    Metadata,
    Properties,
    Source,
    UniversalEntityCreate,
)
from .base import Adapter


class TelegramAdapter(Adapter):
    """Look up Telegram channels / users.

    Telegram's Bot API has no public "search everything" endpoint, so this is
    mock-only for now (spec Phase 4); a bot-token based resolver can be added
    later without changing the interface.
    """

    source_name = "telegram"
    access_type = "api"

    def __init__(self, bot_token: str = "", mock: bool = True):
        self.bot_token = bot_token
        self.mock = mock

    async def search(self, query: str) -> list[dict]:
        if self.mock or not self.bot_token:
            return self._mock_matches(query)
        return []  # real Telegram resolution not implemented yet

    @staticmethod
    def _mock_matches(query: str) -> list[dict]:
        return [
            {
                "kind": "channel",
                "username": f"{query}_news",
                "title": f"{query} News",
                "subscribers": 15400,
            },
            {
                "kind": "person",
                "username": f"{query}_admin",
                "full_name": f"{query} Admin",
                "phone": "+380000000000",
            },
        ]

    def normalize_response(self, raw: dict) -> UniversalEntityCreate:
        kind = str(raw.get("kind") or "channel")
        username = str(raw.get("username") or "")

        if kind == "person":
            entity_type = "person"
            entity_name = str(raw.get("full_name") or username or "unknown")
            footprint = DigitalFootprint(
                social_accounts=[f"t.me/{username}"] if username else [],
                phones=[str(raw["phone"])] if raw.get("phone") else [],
            )
        else:
            entity_type = "channel"
            entity_name = str(raw.get("title") or username or "unknown")
            footprint = DigitalFootprint(
                social_accounts=[f"t.me/{username}"] if username else [],
            )

        now = datetime.now(timezone.utc).isoformat()

        properties = Properties(
            digital_footprint=footprint,
            metadata=Metadata(
                sources=[Source(name=self.source_name, confidence=0.7, last_verified=now)],
                completeness=0.3,
                risk_level="low",
            ),
        )

        key = [username] if username else [entity_name]
        return UniversalEntityCreate(
            entity_type=entity_type,
            entity_id=compute_entity_id(entity_type, key),
            entity_name=entity_name,
            properties=properties,
            raw_data={self.source_name: raw},
        )

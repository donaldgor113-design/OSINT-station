from abc import ABC, abstractmethod

from ..schemas.universal_entity import UniversalEntityCreate


class Adapter(ABC):
    """Common interface for every external service integration (spec §6).

    Each concrete adapter implements the three pieces:
      - `search()`            fetch raw records from the source
      - `normalize_response()` map one raw record to a UniversalEntity
      - `source_name`/`access_type`  metadata so the UI can surface reliability
    """

    source_name: str = "base"
    # "api" | "scraper" | "browser"
    access_type: str = "api"

    @abstractmethod
    async def search(self, query: str) -> list[dict]:
        """Return raw records from the external service."""

    @abstractmethod
    def normalize_response(self, raw: dict) -> UniversalEntityCreate:
        """Map a single raw record into the unified entity schema."""

from abc import ABC, abstractmethod


class AIProviderAdapter(ABC):
    """Common interface for AI models (spec §7).

    Swappable so a user can change model/provider without touching app logic.
    """

    name: str = "base"

    @abstractmethod
    async def summarize(self, entities: list[dict]) -> str:
        """Condense a set of entities into a short fact summary."""

    @abstractmethod
    async def cross_check(self, entities: list[dict]) -> str:
        """Compare entities across sources and flag inconsistencies."""

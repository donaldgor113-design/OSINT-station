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

    async def complete(self, prompt: str) -> str:
        """Generic raw completion for free-form prompts (extraction, etc.)."""
        raise NotImplementedError

    async def is_available(self) -> tuple[bool, str | None]:
        """(True, None) якщо провайдер налаштований/доступний, інакше (False, причина)."""
        return True, None

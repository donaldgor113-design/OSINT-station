from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TierResult:
    """Результат роботи одного рівня каскаду."""

    tier_name: str
    entities: list[dict[str, Any]] = field(default_factory=list)
    raw_sources: list[str] = field(default_factory=list)
    confidence: float = 0.0          # 0.0–1.0, наскільки повний результат рівня
    error: str | None = None
    duration_ms: int = 0
    skipped: bool = False            # True, якщо рівень непридатний (немає ключа тощо)
    skip_reason: str | None = None
    # Якщо рівень перетворив запит (напр. ЄДРПОУ/ІПН → ПІБ), наступні рівні
    # мають шукати за цим значенням, а не за сирим рядком.
    resolved_query: str | None = None

    def is_sufficient(self, threshold: float = 0.6) -> bool:
        """Чи достатньо даних, щоб зупинити каскад."""
        return self.confidence >= threshold and len(self.entities) > 0


class BaseTier(ABC):
    """Базовий рівень каскаду. Кожен рівень незалежний."""

    name: str = "base"

    @abstractmethod
    async def search(self, query: str, query_type: str, workspace_id: int) -> TierResult:
        """
        Виконати пошук на цьому рівні.

        query       — оригінальний рядок від користувача
        query_type  — результат detector.detect_query_type()
        workspace_id — для ізоляції даних
        """
        ...

    def is_available(self) -> tuple[bool, str | None]:
        """
        Чи готовий рівень працювати (наявність ключів, залежностей тощо).
        Повертає (True, None) або (False, "причина").
        """
        return True, None

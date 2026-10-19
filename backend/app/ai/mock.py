from collections import Counter

from .base import AIProviderAdapter


class MockAIProvider(AIProviderAdapter):
    """Deterministic, offline AI stand-in used when no provider key is set."""

    name = "mock"

    async def summarize(self, entities: list[dict]) -> str:
        if not entities:
            return "Немає даних для аналізу."

        type_counts = Counter(e.get("type", "unknown") for e in entities)
        source_counts = Counter(s for e in entities for s in (e.get("sources") or []))
        countries = {e.get("country") for e in entities if e.get("country")}

        parts = [
            f"Зібрано сутностей: {len(entities)}.",
            "Розбивка за типом: " + ", ".join(f"{t} — {c}" for t, c in type_counts.items()) + ".",
            "Джерела: " + ", ".join(f"{s} — {c}" for s, c in source_counts.items()) + ".",
        ]
        if countries:
            parts.append("Країни: " + ", ".join(sorted(countries)) + ".")
        parts.append("(mock-аналіз — підключіть Claude для повноцінного зведення)")

        return " ".join(parts)

    async def cross_check(self, entities: list[dict]) -> str:
        if not entities:
            return "Немає даних для кросс-перевірки."

        # Entities with more than one independent source are better corroborated.
        corroborated = [e for e in entities if len(e.get("sources") or []) > 1]
        single = [e for e in entities if len(e.get("sources") or []) <= 1]

        lines = [
            f"Підтверджено кількома джерелами: {len(corroborated)} з {len(entities)}.",
            "Сутності з одним джерелом: " + ", ".join(e.get("name", "") for e in single) + ".",
        ]
        if corroborated:
            lines.append(
                "Перехресно підтверджені: "
                + ", ".join(e.get("name", "") for e in corroborated)
                + "."
            )
        lines.append("(mock-аналіз)")

        return " ".join(lines)

    async def complete(self, prompt: str) -> str:
        # Mock не вміє витягувати структуру — повертаємо валідній порожній JSON.
        return "[]"

    async def is_available(self) -> tuple[bool, str | None]:
        return True, None

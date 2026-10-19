import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """
Ти аналізуєш результати пошуку для OSINT-розслідування.
Запит користувача: {query}
Тип запиту: {query_type}

Нижче — знайдені документи (назва, URL, текст). Витягни з них структуровані
сутності, якщо такі дані дійсно присутні в тексті. НЕ вигадуй дані, яких
немає в тексті.

Документи:
{documents}

Поверни JSON-масив сутностей у форматі:
[
  {{
    "entity_type": "company" | "person" | "financial_account" | "location",
    "entity_name": "...",
    "properties": {{ ... поля відповідно до типу ... }},
    "relations": [{{"target_name": "...", "type": "director_of" | "owner_of" | ...}}],
    "source_url": "з якого документа взято",
    "extraction_confidence": 0.0-1.0
  }}
]
Якщо структурованих даних немає — поверни порожній масив [].
"""


async def extract_entities_from_documents(
    ai_provider,
    documents: list[dict[str, Any]],
    query: str,
    query_type: str,
    *,
    max_documents: int = 8,
) -> list[dict[str, Any]]:
    """
    Витягує структуровані сутності (company/person/financial_account/location)
    з уже знайдених document-сутностей.

    Якщо ai_provider недоступний (немає ключа) — повертає [] без помилки,
    каскад просто працює з тим, що вже є.
    """
    if ai_provider is None:
        return []

    available, _ = await ai_provider.is_available()
    if not available:
        return []

    docs_for_prompt = documents[:max_documents]
    if not docs_for_prompt:
        return []

    documents_text = "\n\n".join(
        f"[{i}] {d.get('entity_name', '')}\n"
        f"URL: {d.get('properties', {}).get('document', {}).get('url', '')}\n"
        f"Текст: {_document_text(d)[:3000]}"
        for i, d in enumerate(docs_for_prompt)
    )

    prompt = EXTRACTION_PROMPT.format(
        query=query, query_type=query_type, documents=documents_text
    )

    try:
        raw = await ai_provider.complete(prompt)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Entity extraction failed: %s", exc)
        return []

    extracted = _extract_json_array(raw)
    if extracted is None:
        logger.warning("Entity extraction: no JSON array in response: %r", (raw or "")[:300])
        return []

    return [_to_universal_entity(e) for e in extracted if _is_valid(e)]


def _extract_json_array(raw: str | None) -> list | None:
    """Дістає JSON-масив з відповіді моделі.

    Моделі часто обгортають JSON у markdown-блок (```json ... ```) або
    додають текст навколо — тому шукаємо підрядок від першого '[' до
    останнього ']' і парсимо лише його.
    """
    if not raw:
        return None

    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()

    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        return None

    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, list) else None


def _document_text(doc: dict[str, Any]) -> str:
    d = doc.get("properties", {}).get("document", {})
    return d.get("full_text") or d.get("snippet") or d.get("abstract") or ""


def _is_valid(e: dict[str, Any]) -> bool:
    return bool(e.get("entity_type") and e.get("entity_name"))


def _to_universal_entity(e: dict[str, Any]) -> dict[str, Any]:
    etype = e["entity_type"]
    name = e["entity_name"]
    return {
        "entity_type": etype,
        "entity_id": f"ai_extracted:{etype}:{name.lower()}",
        "entity_name": name,
        "properties": {
            etype: e.get("properties", {}),
            "metadata": {
                "sources": [{
                    "name": "ai_extraction",
                    "confidence": e.get("extraction_confidence", 0.5),
                }],
            },
        },
        "relations": e.get("relations", []),
        "raw_data": {"ai_extraction": {"source_url": e.get("source_url")}},
    }

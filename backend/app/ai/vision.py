import base64

import httpx

from ..config import get_settings


def describe_from_metadata(info: dict) -> str:
    """Deterministic image description from metadata (no vision model)."""
    parts: list[str] = []

    gps = info.get("gps")
    if gps:
        parts.append(f"Зображення має геотег: {gps['lat']}, {gps['lng']}.")
    if info.get("device"):
        parts.append(f"Пристрій: {info['device']}.")
    if info.get("datetime"):
        parts.append(f"Дата зйомки: {info['datetime']}.")
    parts.append(f"Роздільна здатність: {info.get('width')}×{info.get('height')}.")

    if not gps:
        parts.append("GPS у метаданих відсутній — геолокацію потрібно визначити візуально.")

    parts.append("(Візуальний опис орієнтирів недоступний без мультимодальної моделі.)")
    return " ".join(parts)


async def _ollama_vision(prompt: str, data: bytes, mime: str) -> str | None:
    """Call an Ollama multimodal model. Returns None if unavailable."""
    settings = get_settings()
    if not settings.ollama_vision_model:
        return None
    b64 = base64.b64encode(data).decode("ascii")
    payload = {
        "model": settings.ollama_vision_model,
        "prompt": prompt,
        "images": [b64],
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate", json=payload
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
    except Exception:
        return None


async def describe_image(data: bytes, info: dict, mime: str) -> str:
    """Vision-based description when a model is available, else metadata-based."""
    prompt = (
        "Опиши коротко, що зображено на фото: місцевість, помітні об'єкти, "
        "орієнтири, можливу країну/місто. Відповідай українською."
    )
    text = await _ollama_vision(prompt, data, mime)
    if text:
        return text
    return describe_from_metadata(info)


async def verify_location(data: bytes, country: str, mime: str) -> dict:
    """Cross-check EXIF GPS country against the visual content (spec §7).

    Returns {"status": "ok" | "mismatch" | "unchecked", "detail": str}.
    """
    if not country:
        return {"status": "unchecked", "detail": "Немає країни в метаданих для звірки"}

    prompt = (
        f"Чи могло це фото бути зроблено в країні '{country}'? "
        "Відповідай лише одним словом: 'так' або 'ні'."
    )
    text = await _ollama_vision(prompt, data, mime)
    if text is None:
        return {
            "status": "unchecked",
            "detail": "Немає vision-моделі — візуальну перевірку виконати неможливо",
        }

    low = text.strip().lower()
    if low.startswith("так") or "так" in low[:8]:
        return {
            "status": "ok",
            "detail": f"Vision-модель підтверджує сумісність зображення із '{country}'",
        }
    if low.startswith("ні") or "ні" in low[:8]:
        return {
            "status": "mismatch",
            "detail": (
                f"⚠️ Vision-модель вказує, що фото НЕ схоже на '{country}' — "
                "можлива розбіжність метаданих (GPS не збігається з вмістом)"
            ),
        }
    return {"status": "unchecked", "detail": f"Невизначена відповідь моделі: {text}"}

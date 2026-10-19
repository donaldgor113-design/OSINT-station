import json

import httpx

from .base import AIProviderAdapter


class OllamaProvider(AIProviderAdapter):
    """Local LLM via the Ollama HTTP API (free, runs on the user's machine).

    Uses the /api/generate endpoint. When `model` is empty, the first model
    returned by /api/tags is auto-selected.
    """

    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434", model: str = ""):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def summarize(self, entities: list[dict]) -> str:
        return await self._complete(
            "Підсумуй ці сутності кількома реченнями українською.", entities
        )

    async def cross_check(self, entities: list[dict]) -> str:
        return await self._complete(
            "Порівняй сутності між джерелами та вкажи можливі суперечності українською.",
            entities,
        )

    async def _resolve_model(self) -> str:
        if self.model:
            return self.model
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                models = response.json().get("models", [])
                if models:
                    return models[0].get("name", "llama3.2")
        except Exception:
            pass
        return "llama3.2"

    async def _complete(self, instruction: str, entities: list[dict]) -> str:
        prompt = instruction + "\n\n" + json.dumps(entities, ensure_ascii=False, indent=2)
        try:
            model = await self._resolve_model()
            payload = {"model": model, "prompt": prompt, "stream": False}
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                return response.json().get("response", "").strip()
        except Exception as exc:  # noqa: BLE001
            return f"(Ollama недоступний: {exc})"

    async def complete(self, prompt: str) -> str:
        try:
            model = await self._resolve_model()
            payload = {"model": model, "prompt": prompt, "stream": False}
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                return response.json().get("response", "").strip()
        except Exception as exc:  # noqa: BLE001
            return f"(Ollama недоступний: {exc})"

    async def is_available(self) -> tuple[bool, str | None]:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
            return True, None
        except Exception as exc:  # noqa: BLE001
            return False, f"ollama unreachable: {exc}"

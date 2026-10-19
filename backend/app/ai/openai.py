import json

import httpx

from .base import AIProviderAdapter


class OpenAIProvider(AIProviderAdapter):
    """OpenAI or any OpenAI-compatible API (Groq, OpenRouter, LM Studio, vLLM…).

    The base_url defaults to OpenAI; point it elsewhere to use a compatible
    endpoint that speaks the /chat/completions protocol.
    """

    name = "openai"

    def __init__(
        self,
        api_key: str = "",
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def summarize(self, entities: list[dict]) -> str:
        return await self._complete("Підсумуй ці сутності кількома реченнями українською.", entities)

    async def cross_check(self, entities: list[dict]) -> str:
        return await self._complete(
            "Порівняй сутності між джерелами та вкажи можливі суперечності українською.",
            entities,
        )

    async def _complete(self, instruction: str, entities: list[dict]) -> str:
        prompt = instruction + "\n\n" + json.dumps(entities, ensure_ascii=False, indent=2)
        url = f"{self.base_url}/chat/completions"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024,
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # noqa: BLE001
            return f"({self.name} недоступний: {exc})"

    async def complete(self, prompt: str) -> str:
        return await self._complete(prompt)

    async def is_available(self) -> tuple[bool, str | None]:
        if not self.api_key:
            return False, "no api key"
        return True, None

import json

import httpx

from .base import AIProviderAdapter


class ClaudeProvider(AIProviderAdapter):
    """Anthropic Claude via the Messages API."""

    name = "claude"
    base_url = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-latest"):
        self.api_key = api_key
        self.model = model

    async def summarize(self, entities: list[dict]) -> str:
        prompt = self._prompt("Підсумуй ці сутності кількома реченнями.", entities)
        return await self._complete(prompt)

    async def cross_check(self, entities: list[dict]) -> str:
        prompt = self._prompt(
            "Порівняй сутності між джерелами та вкажи можливі суперечності.",
            entities,
        )
        return await self._complete(prompt)

    @staticmethod
    def _prompt(instruction: str, entities: list[dict]) -> str:
        return instruction + "\n\n" + json.dumps(entities, ensure_ascii=False, indent=2)

    async def _complete(self, prompt: str) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        return data["content"][0]["text"]

    async def complete(self, prompt: str) -> str:
        return await self._complete(prompt)

    async def is_available(self) -> tuple[bool, str | None]:
        if not self.api_key:
            return False, "no api key"
        return True, None

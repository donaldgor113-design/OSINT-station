import json
import time
from typing import Any


class SearchCache:
    """Кеш результатів пошуку.

    За замовчуванням — in-memory (dict з TTL), тому працює без жодного
    зовнішнього сервісу. Якщо передано `redis_url` і встановлено пакет
    `redis` — використовує Redis із тим самим TTL. Якщо Redis недоступний,
    тихо повертаємося на in-memory, щоб кеш ніколи не ламав пошук.
    """

    def __init__(self, redis_url: str | None = None, ttl_seconds: int = 3600):
        self._ttl = ttl_seconds
        self._mem: dict[str, tuple[float, Any]] = {}
        self._redis = None
        self._redis_failed = False

        if redis_url:
            try:
                import redis.asyncio as redis  # type: ignore

                self._redis = redis.from_url(redis_url)
            except ImportError:
                self._redis = None

    async def get(self, key: str) -> Any | None:
        now = time.monotonic()

        if self._redis is not None and not self._redis_failed:
            try:
                raw = await self._redis.get(key)
                return json.loads(raw) if raw else None
            except Exception:  # noqa: BLE001 — Redis недоступний, працюємо in-memory
                self._redis_failed = True

        entry = self._mem.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if now >= expires_at:
            self._mem.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: Any) -> None:
        now = time.monotonic()
        self._mem[key] = (now + self._ttl, value)

        if self._redis is not None and not self._redis_failed:
            try:
                await self._redis.set(key, json.dumps(value), ex=self._ttl)
            except Exception:  # noqa: BLE001
                self._redis_failed = True

    async def close(self) -> None:
        if self._redis is not None:
            try:
                await self._redis.aclose()
            except Exception:  # noqa: BLE001
                pass

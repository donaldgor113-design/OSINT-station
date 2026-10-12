from ..config import get_settings
from ..models.provider_config import ProviderConfig
from .base import AIProviderAdapter
from .claude import ClaudeProvider
from .mock import MockAIProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider

RESERVED_NAMES = {"mock", "ollama", "claude", "openai"}


def builtin_providers() -> list[dict]:
    settings = get_settings()
    return [
        {"name": "mock", "label": "Без AI (детермінований аналіз)", "local": False, "configured": True},
        {"name": "ollama", "label": "Ollama (локальні моделі)", "local": True, "configured": True},
        {
            "name": "claude",
            "label": "Claude (Anthropic)",
            "local": False,
            "configured": bool(settings.anthropic_api_key) and not settings.anthropic_mock,
        },
        {
            "name": "openai",
            "label": "GPT (OpenAI)",
            "local": False,
            "configured": bool(settings.openai_api_key),
        },
    ]


def available(db) -> list[dict]:
    """Built-in + user-defined providers."""
    result = builtin_providers()
    for cfg in db.query(ProviderConfig).order_by(ProviderConfig.id).all():
        result.append(
            {
                "name": cfg.name,
                "label": cfg.name,
                "local": cfg.kind == "ollama",
                "configured": True,
                "custom": True,
                "id": cfg.id,
                "kind": cfg.kind,
            }
        )
    return result


def _build_custom(cfg: ProviderConfig) -> AIProviderAdapter:
    settings = get_settings()
    if cfg.kind == "ollama":
        return OllamaProvider(cfg.base_url or settings.ollama_base_url, cfg.model)
    if cfg.kind == "claude":
        return ClaudeProvider(cfg.api_key, cfg.model or "claude-3-5-sonnet-latest")
    return OpenAIProvider(
        cfg.api_key, cfg.model or "gpt-4o-mini", cfg.base_url or "https://api.openai.com/v1"
    )


def get(name: str | None, db=None) -> AIProviderAdapter:
    """Instantiate a provider by name (built-in or custom), or auto via settings."""
    settings = get_settings()

    if name == "mock":
        return MockAIProvider()
    if name == "ollama":
        return OllamaProvider(settings.ollama_base_url, settings.ollama_model)
    if name == "claude":
        return ClaudeProvider(settings.anthropic_api_key)
    if name == "openai":
        return OpenAIProvider(settings.openai_api_key, settings.openai_model)

    if name and db is not None:
        cfg = db.query(ProviderConfig).filter(ProviderConfig.name == name).first()
        if cfg:
            return _build_custom(cfg)

    # auto
    if settings.anthropic_api_key and not settings.anthropic_mock:
        return ClaudeProvider(settings.anthropic_api_key)
    if settings.openai_api_key:
        return OpenAIProvider(settings.openai_api_key, settings.openai_model)
    return OllamaProvider(settings.ollama_base_url, settings.ollama_model)

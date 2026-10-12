from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, overridable via environment variables or .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./osint.db"
    shodan_api_key: str = ""
    shodan_mock: bool = True
    google_maps_api_key: str = ""
    google_maps_mock: bool = True
    whois_mock: bool = False
    telegram_bot_token: str = ""
    telegram_mock: bool = True
    scraper_mock: bool = False
    browser_mock: bool = False
    web_search_mock: bool = False
    brave_search_api_key: str = ""
    google_cse_api_key: str = ""
    google_cse_id: str = ""
    opendatabot_api_key: str = ""
    anthropic_api_key: str = ""
    anthropic_mock: bool = True
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    # "auto" | "ollama" | "claude" | "openai" | "mock"
    ai_provider: str = "auto"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = ""
    ollama_vision_model: str = ""

    # Parsed as a JSON list or comma-separated string.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if raw.startswith("["):
            import json

            return json.loads(raw)
        return [o.strip() for o in raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

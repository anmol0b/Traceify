from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = ""
    rapidapi_key: str = ""
    supabase_url: str = ""
    supabase_key: str = ""

    groq_model_fast: str = "openai/gpt-oss-20b"
    groq_model_smart: str = "openai/gpt-oss-120b"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    cache_ttl_hours: int = 24
    tweet_pages: int = 5
    allowed_origins: str = "http://localhost:3000"

    chat_rate_limit: int = 20  # requests per window per IP
    fetch_rate_limit: int = 10
    rate_limit_window_seconds: int = 300

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def db_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

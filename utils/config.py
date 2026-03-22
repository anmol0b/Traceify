from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    app_name: str = "Traceify"
    groq_api_key: str = os.getenv("GROQ_API_KEY", "").strip()
    rapidapi_key: str = os.getenv("RAPIDAPI_KEY", "").strip()
    supabase_url: str = os.getenv("SUPABASE_URL", "").strip()
    supabase_key: str = os.getenv("SUPABASE_KEY", "").strip()
    linkedin_username: str = os.getenv("LINKEDIN_USERNAME", "").strip()
    linkedin_password: str = os.getenv("LINKEDIN_PASSWORD", "").strip()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

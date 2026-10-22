from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = ""
    rapidapi_key: str = ""
    database_url: str = ""  # Postgres with pgvector, e.g. a Neon pooled connection string

    # The smart model writes every chat answer; the fast one does internal jobs (query rewriting, ingest analysis).
    groq_model_fast: str = "openai/gpt-oss-20b"
    groq_model_smart: str = "openai/gpt-oss-120b"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    llm_temperature: float = 0.3
    # gpt-oss reasons before answering and those tokens count toward this limit, so leave headroom.
    llm_max_completion_tokens: int = 4096
    llm_timeout_seconds: float = 30
    # Characters of tweet text in each chat prompt (0 = every tweet). ~10k chars is ~2.5k tokens, which keeps a
    # prompt well inside Groq's free-tier limit of 8k tokens/minute for gpt-oss-120b. On a paid tier, set 0.
    context_max_tweet_chars: int = 10_000
    retrieval_limit: int = 8
    # Cosine floor. With bge-small-en-v1.5 on tweets, real matches score ~0.45-0.8 and unrelated ones ~0.35-0.55
    # (see `python -m evals.run --retrieval-only`), so this only drops clear misses. Every tweet is in the prompt
    # anyway; retrieval just points the model at the likeliest ones.
    retrieval_min_similarity: float = 0.5
    # BGE models accept "Represent this sentence for searching relevant passages: " on queries. On our eval set it
    # didn't improve ranking for bge-small-en-v1.5 (MRR 0.897 vs 0.898, recall@8 0.79 vs 0.64), so it's off.
    embedding_query_prefix: str = ""
    analyze_on_ingest: bool = True  # LLM summary, topic labels and suggested questions when a profile is fetched

    cache_ttl_hours: int = 24
    tweet_pages: int = 5
    allowed_origins: str = "http://localhost:3000"

    chat_rate_limit: int = 20  # requests per window per IP
    fetch_rate_limit: int = 10
    rate_limit_window_seconds: int = 300

    @property
    def cors_origins(self) -> list[str]:
        # Browsers send Origin without a trailing slash, so "https://site.com/" would never match.
        return [o.strip().rstrip("/") for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def db_enabled(self) -> bool:
        return bool(self.database_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

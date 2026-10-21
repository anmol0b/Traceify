"""Groq client factory and small helpers shared by chat and ingest analysis."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

from ..config import Settings, get_settings

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _client(api_key: str, timeout: float) -> Any:
    from groq import Groq

    return Groq(api_key=api_key, timeout=timeout, max_retries=1)


def get_llm_client(settings: Settings | None = None) -> Any | None:
    """A shared Groq client, or None when no API key is configured."""
    settings = settings or get_settings()
    if not settings.groq_api_key:
        return None
    return _client(settings.groq_api_key, settings.llm_timeout_seconds)


def complete_text(client: Any, *, model: str, messages: list[dict[str, str]], **params: Any) -> str:
    response = client.chat.completions.create(model=model, messages=messages, include_reasoning=False, **params)
    return (response.choices[0].message.content or "").strip()


def complete_json(client: Any, *, model: str, messages: list[dict[str, str]], **params: Any) -> dict[str, Any]:
    """Ask for a JSON object and parse it. Raises ValueError if the model returns something else."""
    text = complete_text(client, model=model, messages=messages, response_format={"type": "json_object"}, **params)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model returned invalid JSON: {text[:200]!r}") from exc
    if not isinstance(data, dict):
        raise ValueError("Model returned JSON that is not an object")
    return data

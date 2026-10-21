"""Structured LLM traces: one JSON log line per event, easy to grep or ship to a log pipeline."""

from __future__ import annotations

import json
import logging
from typing import Any

log = logging.getLogger("traceify.trace")


def trace(event: str, **fields: Any) -> None:
    payload = {"event": event, **{k: v for k, v in fields.items() if v is not None}}
    log.info(json.dumps(payload, ensure_ascii=False, default=str))

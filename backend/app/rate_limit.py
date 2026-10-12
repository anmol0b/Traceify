"""Tiny in-memory sliding-window rate limiter (per process) to protect the public demo's API quotas."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request

from .errors import RateLimited


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, bucket: str, key: str, limit: int, window_seconds: int) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[(bucket, key)]
            while hits and now - hits[0] > window_seconds:
                hits.popleft()
            if len(hits) >= limit:
                retry = int(window_seconds - (now - hits[0])) + 1
                raise RateLimited(f"Too many requests. Try again in {retry}s.")
            hits.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

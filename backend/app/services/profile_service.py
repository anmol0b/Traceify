"""Orchestrates profile fetching: normalize → cache → fetch → embed → analyze → persist (profile before tweets)."""

from __future__ import annotations

import logging
from collections import OrderedDict
from collections.abc import Callable
from functools import lru_cache
from threading import Lock
from typing import Any

from ..config import Settings, get_settings
from ..schemas import PROFILE_SCHEMA_VERSION, Profile
from .analysis import analyze_profile
from .embeddings import Embedder, get_embedder
from .llm import get_llm_client
from .profiles import build_profile_summary, normalize_x_input
from .repo import Repo, get_repo
from .retrieval import Retriever
from .x_client import XClient, attach_tweets

log = logging.getLogger(__name__)


class ProfileService:
    def __init__(
        self,
        repo: Repo,
        x_client: XClient,
        tweet_pages: int = 5,
        memory_size: int = 200,
        embedder_factory: Callable[[], Embedder] | None = None,
        llm_client: Any | None = None,
        settings: Settings | None = None,
    ):
        self.repo = repo
        self.x = x_client
        self.tweet_pages = tweet_pages
        self.settings = settings or get_settings()
        self.llm = llm_client
        self._embedder_factory = embedder_factory
        # Without an embedder there's no semantic search; chat still sees every tweet.
        self.retriever = (
            Retriever(
                repo,
                embedder_factory,
                limit=self.settings.retrieval_limit,
                min_similarity=self.settings.retrieval_min_similarity,
                cache_size=memory_size,
            )
            if embedder_factory
            else None
        )
        # Fallback store so chat still works when no database is configured.
        self._memory: OrderedDict[str, Profile] = OrderedDict()
        self._memory_size = memory_size
        self._lock = Lock()

    def get_cached(self, raw_handle: str) -> Profile | None:
        handle = normalize_x_input(raw_handle)
        return self.repo.get_cached_profile(handle) or self._memory_get(handle)

    def get(self, raw_handle: str) -> tuple[Profile, bool]:
        """Return (profile, from_cache). Raises TraceifyError subclasses on failure."""
        cached = self.get_cached(raw_handle)
        if cached:
            return cached, True
        return self.fetch(normalize_x_input(raw_handle)), False

    def refresh(self, raw_handle: str) -> Profile:
        handle = normalize_x_input(raw_handle)
        self.repo.delete_profile(handle)
        with self._lock:
            self._memory.pop(handle.lower(), None)
        if self.retriever:
            self.retriever.forget(handle)
        return self.fetch(handle)

    def fetch(self, handle: str) -> Profile:
        profile, rest_id = self.x.fetch_profile(handle)
        tweets = []
        if rest_id:
            tweets = self.x.fetch_tweets(rest_id, profile.handle, pages=self.tweet_pages)
            if not tweets:
                profile.warnings.append("No recent original tweets could be loaded for this account.")
        attach_tweets(profile, tweets)
        profile.summary = build_profile_summary(profile)
        profile.schema_version = PROFILE_SCHEMA_VERSION

        # Embed once and reuse the vectors for topic clustering, the database and in-memory search.
        vectors = self._embed([t.text for t in profile.tweets])
        if self.settings.analyze_on_ingest:
            analyze_profile(profile, vectors, self.llm, self.settings)

        # Order matters: tweets.handle references profiles.handle.
        self.repo.save_profile(profile)
        self.repo.save_tweets(profile.handle, profile.tweets, vectors)
        if self.retriever and vectors:
            self.retriever.remember(profile, vectors)
        self._memory_put(profile)
        return profile

    def _embed(self, texts: list[str]) -> list[list[float]] | None:
        if not texts or not self._embedder_factory:
            return None
        try:
            return self._embedder_factory().embed(texts)
        except Exception:
            log.exception("Embedding tweets failed; semantic search and topics are unavailable")
            return None

    def _memory_get(self, handle: str) -> Profile | None:
        with self._lock:
            profile = self._memory.get(handle.lower())
            if profile:
                self._memory.move_to_end(handle.lower())
            return profile

    def _memory_put(self, profile: Profile) -> None:
        with self._lock:
            self._memory[profile.handle.lower()] = profile
            self._memory.move_to_end(profile.handle.lower())
            while len(self._memory) > self._memory_size:
                self._memory.popitem(last=False)


@lru_cache(maxsize=1)
def get_profile_service() -> ProfileService:
    settings = get_settings()
    return ProfileService(
        get_repo(),
        XClient(settings.rapidapi_key),
        tweet_pages=settings.tweet_pages,
        embedder_factory=get_embedder,
        llm_client=get_llm_client(settings),
        settings=settings,
    )

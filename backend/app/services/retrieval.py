"""Semantic search over one profile's tweets: in-memory vectors first, pgvector when they aren't loaded."""

from __future__ import annotations

import logging
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock

import numpy as np

from ..schemas import Profile
from .embeddings import Embedder, get_embedder
from .repo import Repo

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Hit:
    tweet_id: str
    similarity: float


def normalize_rows(vectors: list[list[float]] | np.ndarray) -> np.ndarray:
    matrix = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.where(norms == 0, 1, norms)


class Retriever:
    def __init__(
        self,
        repo: Repo,
        embedder_factory: Callable[[], Embedder] = get_embedder,
        limit: int = 8,
        min_similarity: float = 0.6,
        cache_size: int = 200,
    ):
        self.repo = repo
        self._embedder_factory = embedder_factory
        self.limit = limit
        self.min_similarity = min_similarity
        self._vectors: OrderedDict[str, tuple[tuple[str, ...], np.ndarray]] = OrderedDict()
        self._cache_size = cache_size
        self._lock = Lock()

    def remember(self, profile: Profile, vectors: list[list[float]]) -> None:
        """Keep a profile's tweet vectors in memory so chat doesn't have to re-embed or query the database."""
        if len(vectors) != len(profile.tweets) or not vectors:
            return
        ids = tuple(t.id for t in profile.tweets)
        with self._lock:
            self._vectors[profile.handle.lower()] = (ids, normalize_rows(vectors))
            self._vectors.move_to_end(profile.handle.lower())
            while len(self._vectors) > self._cache_size:
                self._vectors.popitem(last=False)

    def forget(self, handle: str) -> None:
        with self._lock:
            self._vectors.pop(handle.lower(), None)

    def search(self, profile: Profile, query: str) -> list[Hit]:
        """Tweets from the profile's current tweet set that are similar enough to the query, best first."""
        if not profile.tweets or not query.strip():
            return []
        try:
            query_vector = self._embedder_factory().embed_query(query)
            hits = self._search_memory(profile, query_vector)
            if hits is None and self.repo.enabled:
                rows = self.repo.search_tweets(
                    profile.handle, query_vector, [t.id for t in profile.tweets], limit=self.limit
                )
                hits = [Hit(str(r["id"]), float(r["similarity"])) for r in rows]
            if hits is None:
                hits = self._search_memory(profile, query_vector, build=True) or []
        except Exception:
            log.exception("Semantic search failed for @%s", profile.handle)
            return []
        return [h for h in hits if h.similarity >= self.min_similarity][: self.limit]

    def _search_memory(self, profile: Profile, query_vector: list[float], build: bool = False) -> list[Hit] | None:
        ids = tuple(t.id for t in profile.tweets)
        with self._lock:
            cached = self._vectors.get(profile.handle.lower())
        if cached is None or cached[0] != ids:
            if not build:
                return None
            self.remember(profile, self._embedder_factory().embed([t.text for t in profile.tweets]))
            with self._lock:
                cached = self._vectors.get(profile.handle.lower())
            if cached is None:
                return None
        _, matrix = cached
        scores = matrix @ normalize_rows([query_vector])[0]
        order = np.argsort(-scores)[: self.limit]
        return [Hit(ids[i], float(scores[i])) for i in order]

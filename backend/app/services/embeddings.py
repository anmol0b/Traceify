from __future__ import annotations

import logging
from functools import lru_cache
from typing import Protocol

from ..config import get_settings

log = logging.getLogger(__name__)


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, query: str) -> list[float]: ...


class FastEmbedder:
    """Thin wrapper over fastembed (ONNX runtime, no torch) so the API fits in ~512MB of RAM."""

    def __init__(self, model_name: str, query_prefix: str = ""):
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=model_name)
        self._query_prefix = query_prefix  # some models expect an instruction on queries only

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._model.embed(texts)]

    def embed_query(self, query: str) -> list[float]:
        return self.embed([self._query_prefix + query])[0]


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    settings = get_settings()
    log.info("Loading embedding model %s", settings.embedding_model)
    return FastEmbedder(settings.embedding_model, settings.embedding_query_prefix)

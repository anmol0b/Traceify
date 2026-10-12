from __future__ import annotations

import logging
from functools import lru_cache
from typing import Protocol

from ..config import get_settings

log = logging.getLogger(__name__)


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class FastEmbedder:
    """Thin wrapper over fastembed (ONNX runtime, no torch) so the API fits in ~512MB of RAM."""

    def __init__(self, model_name: str):
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._model.embed(texts)]


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    model_name = get_settings().embedding_model
    log.info("Loading embedding model %s", model_name)
    return FastEmbedder(model_name)

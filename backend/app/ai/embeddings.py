"""Embedding providers.

Three modes, selected by `EMBEDDING_PROVIDER`:

- ``openrouter``  : NVIDIA Nemotron or any OpenRouter embedding model
- ``openai``      : OpenAI ``text-embedding-3-small`` (or any OpenAI model)
- ``deterministic``: offline, hash-based feature vectors (no API key). Used
                     for development, demos, and tests so the full matching
                     pipeline runs without external dependencies.
"""

from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod

from app.config import settings


class BaseEmbedder(ABC):
    dim: int

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one fixed-dimension float vector per input text."""


class DeterministicEmbedder(BaseEmbedder):
    """Feature-hashing embedder. Deterministic and dependency-free."""

    def __init__(self, dim: int = 1536) -> None:
        self.dim = dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            idx = int(digest, 16) % self.dim
            sign = 1.0 if int(digest[0], 16) % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]


class OpenAICompatEmbedder(BaseEmbedder):
    """OpenAI-compatible embeddings client (works with OpenAI or OpenRouter)."""

    def __init__(
        self,
        api_key: str,
        base_url: str | None,
        model: str,
        dim: int,
    ) -> None:
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.dim = dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
            encoding_format="float",
        )
        return [item.embedding for item in response.data]


_embedder: BaseEmbedder | None = None


def get_embedder() -> BaseEmbedder:
    """Return a singleton embedder based on settings.EMBEDDING_PROVIDER."""
    global _embedder
    if _embedder is not None:
        return _embedder

    dim = settings.embedding_dimensions
    provider = settings.embedding_provider.lower()

    if provider in {"openai", "openrouter"} and settings.embedding_api_key:
        _embedder = OpenAICompatEmbedder(
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_base_url or None,
            model=settings.embedding_model,
            dim=dim,
        )
    else:
        _embedder = DeterministicEmbedder(dim=dim)
    return _embedder

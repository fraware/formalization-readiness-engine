"""Embedding-based declaration search (Phase 4b interface)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from fre_core.schemas import DeclarationIndex, MathlibDeclaration


@dataclass(frozen=True)
class EmbeddingSearchHit:
    declaration: MathlibDeclaration
    score: float


class EmbeddingIndex(Protocol):
    index_id: str

    def search(self, *, query: str, top_k: int = 10) -> list[EmbeddingSearchHit]:
        ...


class StubEmbeddingIndex:
    def __init__(self, *, index: DeclarationIndex) -> None:
        self._index = index
        self.index_id = f"{index.index_id}_embedding_stub"

    def search(self, *, query: str, top_k: int = 10) -> list[EmbeddingSearchHit]:
        if not query.strip() or top_k <= 0:
            return []
        return []

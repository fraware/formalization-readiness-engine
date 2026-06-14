"""Embedding-based declaration search (fixture-backed v0).

Precomputed declaration vectors live in sidecar JSON files under
``fixtures/mathlib_declarations/*_embeddings.json``. Query vectors are built
at search time with the same deterministic hashed n-gram model so CI needs no
external APIs or heavyweight model downloads.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

from fre_core.schemas import DeclarationIndex, MathlibDeclaration

EMBEDDING_MODEL_ID = "hashed_char_ngram_v0"
EMBEDDING_DIMENSIONS = 128
_SCORE_EMBEDDING_MAX = 350

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


class DeclarationEmbeddingEntry(BaseModel):
    declaration_id: str
    vector: list[float]


class DeclarationEmbeddingSidecar(BaseModel):
    schema_version: str = "0.1"
    index_id: str
    model_id: str
    dimensions: int
    declarations: list[DeclarationEmbeddingEntry] = Field(default_factory=list)


@dataclass(frozen=True)
class EmbeddingSearchHit:
    declaration: MathlibDeclaration
    score: float


class EmbeddingIndex(Protocol):
    index_id: str

    def search(self, *, query: str, top_k: int = 10) -> list[EmbeddingSearchHit]:
        ...


def default_embedding_path(*, index_path: Path) -> Path:
    """Return the embedding sidecar path for a declaration index fixture."""
    return index_path.with_name(f"{index_path.stem}_embeddings.json")


def declaration_embed_text(declaration: MathlibDeclaration) -> str:
    """Build the canonical text used for declaration embedding."""
    parts = [
        declaration.full_name,
        declaration.namespace,
        declaration.module,
        declaration.kind,
        declaration.type_signature or "",
        declaration.docstring or "",
    ]
    return " ".join(part.strip() for part in parts if part and part.strip())


def _normalize_embed_text(text: str) -> str:
    return " ".join(_TOKEN_PATTERN.findall(text.casefold()))


def _hash_bucket(token: str, dimensions: int) -> int:
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return int(digest, 16) % dimensions


def embed_text(*, text: str, dimensions: int = EMBEDDING_DIMENSIONS) -> list[float]:
    """Embed text with a deterministic hashed character n-gram model."""
    normalized = _normalize_embed_text(text)
    if not normalized:
        return [0.0] * dimensions

    vector = [0.0] * dimensions
    for token in normalized.split():
        vector[_hash_bucket(f"tok:{token}", dimensions)] += 1.0

    compact = normalized.replace(" ", "")
    for index in range(max(0, len(compact) - 2)):
        trigram = compact[index : index + 3]
        vector[_hash_bucket(f"tri:{trigram}", dimensions)] += 0.5

    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 0.0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Vector dimensions must match for cosine similarity.")
    return sum(a * b for a, b in zip(left, right, strict=True))


def build_declaration_embedding_sidecar(*, index: DeclarationIndex) -> DeclarationEmbeddingSidecar:
    """Build a sidecar payload for all declarations in an index."""
    entries = [
        DeclarationEmbeddingEntry(
            declaration_id=declaration.declaration_id,
            vector=embed_text(text=declaration_embed_text(declaration)),
        )
        for declaration in index.declarations
    ]
    return DeclarationEmbeddingSidecar(
        index_id=index.index_id,
        model_id=EMBEDDING_MODEL_ID,
        dimensions=EMBEDDING_DIMENSIONS,
        declarations=entries,
    )


def load_declaration_embedding_sidecar(path: Path) -> DeclarationEmbeddingSidecar:
    return DeclarationEmbeddingSidecar.model_validate_json(path.read_text(encoding="utf-8"))


def write_declaration_embedding_sidecar(*, sidecar: DeclarationEmbeddingSidecar, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sidecar.model_dump_json(indent=2) + "\n", encoding="utf-8")


class FixtureEmbeddingIndex:
    """Search precomputed fixture vectors with cosine similarity."""

    def __init__(
        self,
        *,
        index: DeclarationIndex,
        sidecar: DeclarationEmbeddingSidecar,
    ) -> None:
        if sidecar.index_id != index.index_id:
            raise ValueError(
                f"Embedding sidecar index_id {sidecar.index_id!r} "
                f"does not match declaration index {index.index_id!r}."
            )
        if sidecar.model_id != EMBEDDING_MODEL_ID:
            raise ValueError(
                f"Unsupported embedding model {sidecar.model_id!r}; "
                f"expected {EMBEDDING_MODEL_ID!r}."
            )
        if sidecar.dimensions != EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"Embedding dimensions {sidecar.dimensions} do not match "
                f"runtime model ({EMBEDDING_DIMENSIONS})."
            )

        by_id = {declaration.declaration_id: declaration for declaration in index.declarations}
        self._vectors: list[tuple[MathlibDeclaration, list[float]]] = []
        for entry in sidecar.declarations:
            declaration = by_id.get(entry.declaration_id)
            if declaration is None:
                continue
            if len(entry.vector) != sidecar.dimensions:
                raise ValueError(
                    f"Vector for {entry.declaration_id!r} has length {len(entry.vector)}, "
                    f"expected {sidecar.dimensions}."
                )
            self._vectors.append((declaration, entry.vector))

        self.index_id = f"{index.index_id}_embeddings"
        self._dimensions = sidecar.dimensions

    @classmethod
    def from_sidecar(cls, *, index: DeclarationIndex, path: Path) -> FixtureEmbeddingIndex:
        return cls(index=index, sidecar=load_declaration_embedding_sidecar(path))

    def search(self, *, query: str, top_k: int = 10) -> list[EmbeddingSearchHit]:
        if not query.strip() or top_k <= 0 or not self._vectors:
            return []

        query_vector = embed_text(text=query, dimensions=self._dimensions)
        hits: list[EmbeddingSearchHit] = []
        for declaration, vector in self._vectors:
            score = cosine_similarity(query_vector, vector)
            if score <= 0.0:
                continue
            hits.append(EmbeddingSearchHit(declaration=declaration, score=score))

        hits.sort(
            key=lambda hit: (
                -hit.score,
                hit.declaration.full_name,
                hit.declaration.declaration_id,
            )
        )
        return hits[:top_k]


class StubEmbeddingIndex:
    def __init__(self, *, index: DeclarationIndex) -> None:
        self._index = index
        self.index_id = f"{index.index_id}_embedding_stub"

    def search(self, *, query: str, top_k: int = 10) -> list[EmbeddingSearchHit]:
        if not query.strip() or top_k <= 0:
            return []
        return []


def load_embedding_index(*, index: DeclarationIndex, index_path: Path) -> EmbeddingIndex:
    """Load fixture embeddings when a sidecar exists; otherwise return a stub index."""
    embedding_path = default_embedding_path(index_path=index_path)
    if embedding_path.is_file():
        return FixtureEmbeddingIndex.from_sidecar(index=index, path=embedding_path)
    return StubEmbeddingIndex(index=index)

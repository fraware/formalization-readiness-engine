from pathlib import Path

import pytest

from fre_core.embedding_index import (
    EMBEDDING_MODEL_ID,
    FixtureEmbeddingIndex,
    StubEmbeddingIndex,
    cosine_similarity,
    default_embedding_path,
    embed_text,
    load_embedding_index,
)
from fre_core.mathlib_index import load_index

ROOT = Path(__file__).resolve().parents[1]
FINITE_TREE_INDEX = ROOT / "fixtures" / "mathlib_declarations" / "finite_tree_v0.json"
FINITE_TREE_EMBEDDINGS = default_embedding_path(index_path=FINITE_TREE_INDEX)


@pytest.fixture
def index():
    return load_index(FINITE_TREE_INDEX)


def test_stub_returns_empty(index):
    assert StubEmbeddingIndex(index=index).search(query="tree", top_k=3) == []


def test_embed_text_is_deterministic():
    first = embed_text(text="finite tree edge count")
    second = embed_text(text="finite tree edge count")
    assert first == second
    assert len(first) == 128


def test_cosine_similarity_unit_vector():
    vector = embed_text(text="tree")
    assert pytest.approx(cosine_similarity(vector, vector)) == 1.0


def test_default_embedding_path():
    assert default_embedding_path(index_path=FINITE_TREE_INDEX).name == "finite_tree_v0_embeddings.json"


def test_fixture_index_returns_hits(index):
    sidecar_index = FixtureEmbeddingIndex.from_sidecar(
        index=index,
        path=FINITE_TREE_EMBEDDINGS,
    )
    hits = sidecar_index.search(query="finite tree edge count", top_k=5)
    assert hits
    hit_names = {hit.declaration.full_name for hit in hits}
    assert "SimpleGraph.IsTree.card_edgeFinset" in hit_names
    assert all(hit.score > 0.0 for hit in hits)


def test_fixture_index_ranking_is_deterministic(index):
    sidecar_index = FixtureEmbeddingIndex.from_sidecar(
        index=index,
        path=FINITE_TREE_EMBEDDINGS,
    )
    query = "tree leaf vertex finite graph"
    first = sidecar_index.search(query=query, top_k=5)
    second = sidecar_index.search(query=query, top_k=5)
    assert [hit.declaration.declaration_id for hit in first] == [
        hit.declaration.declaration_id for hit in second
    ]


def test_load_embedding_index_uses_sidecar(index):
    loaded = load_embedding_index(index=index, index_path=FINITE_TREE_INDEX)
    assert loaded.index_id.endswith("_embeddings")
    hits = loaded.search(query="SimpleGraph IsTree", top_k=3)
    assert hits
    assert hits[0].score > 0.0


def test_sidecar_model_id(index):
    sidecar_index = FixtureEmbeddingIndex.from_sidecar(
        index=index,
        path=FINITE_TREE_EMBEDDINGS,
    )
    assert EMBEDDING_MODEL_ID == "hashed_char_ngram_v0"
    assert sidecar_index.index_id == "mathlib_finite_tree_v0_embeddings"

from pathlib import Path
import pytest
from fre_core.embedding_index import StubEmbeddingIndex
from fre_core.mathlib_index import load_index

@pytest.fixture
def index():
    return load_index(Path(__file__).resolve().parents[1] / "fixtures/mathlib_declarations/finite_tree_v0.json")

def test_stub(index):
    assert StubEmbeddingIndex(index=index).search(query="tree", top_k=3) == []

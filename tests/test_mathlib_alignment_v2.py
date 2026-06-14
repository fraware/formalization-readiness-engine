from pathlib import Path
from fre_core.embedding_index import load_embedding_index
from fre_core.mathlib_alignment import align_readiness_report, suggest_import_modules_from_alignment
from fre_core.mathlib_index import load_index, trimmed_index_path
from fre_core.validation import load_readiness_report

ROOT = Path(__file__).resolve().parents[1]
FINITE_TREE_INDEX = ROOT / "fixtures/mathlib_declarations/finite_tree_v0.json"

def test_trimmed_fixture():
    index = load_index(trimmed_index_path(repo_root=ROOT))
    names = {d.full_name for d in index.declarations}
    assert "SimpleGraph.IsTree.card_edgeFinset" in names
    assert "CategoryTheory.Limits.PreservesPullback" in names

def test_suggest_imports():
    report = load_readiness_report(ROOT / "examples/finite_tree/readiness_report.json")
    index = load_index(FINITE_TREE_INDEX)
    alignment = align_readiness_report(report=report, index=index, confirmed_full_names=frozenset({"SimpleGraph.IsTree.card_edgeFinset"}))
    assert suggest_import_modules_from_alignment(alignment) == ["Mathlib.Combinatorics.SimpleGraph.Acyclic"]

def test_alignment_includes_embedding_hits():
    report = load_readiness_report(ROOT / "examples/finite_tree/readiness_report.json")
    index = load_index(FINITE_TREE_INDEX)
    embedding_index = load_embedding_index(index=index, index_path=FINITE_TREE_INDEX)
    alignment = align_readiness_report(
        report=report,
        index=index,
        embedding_index=embedding_index,
    )
    embedding_sources = [candidate.query_source for candidate in alignment.candidates if "embedding:" in candidate.query_source]
    assert embedding_sources
    embedding_reasons = {
        reason
        for candidate in alignment.candidates
        for reason in candidate.match_reasons
        if reason.startswith("embedding:")
    }
    assert embedding_reasons


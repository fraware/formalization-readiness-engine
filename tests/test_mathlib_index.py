from pathlib import Path

import pytest

from fre_core.mathlib_index import (
    build_search_query_from_report,
    build_search_query_from_unit,
    enrich_readiness_candidates,
    enrich_readiness_report_from_unit,
    load_index,
    search,
)
from fre_core.schemas import ReadinessDimension, ReadinessReport, TheoremProofUnit
from fre_core.validation import load_readiness_report, load_unit

ROOT = Path(__file__).resolve().parents[1]
FINITE_TREE_INDEX = ROOT / "fixtures" / "mathlib_declarations" / "finite_tree_v0.json"
EXAMPLE_DIR = ROOT / "examples" / "finite_tree"


@pytest.fixture
def finite_tree_index():
    return load_index(FINITE_TREE_INDEX)


def test_load_index_validates_fixture(finite_tree_index) -> None:
    assert finite_tree_index.index_id == "mathlib_finite_tree_v0"
    assert len(finite_tree_index.declarations) >= 10


def test_finite_tree_unit_query_ranks_card_edgeFinset_first(finite_tree_index) -> None:
    unit = load_unit(EXAMPLE_DIR / "unit.json")
    query = build_search_query_from_unit(unit)
    hits = search(index=finite_tree_index, query=query, top_k=5)

    assert hits
    assert hits[0].declaration.full_name == "SimpleGraph.IsTree.card_edgeFinset"
    assert all(hit.declaration.full_name for hit in hits)


def test_finite_tree_report_query_is_deterministic(finite_tree_index) -> None:
    report = load_readiness_report(EXAMPLE_DIR / "readiness_report.json")
    query = build_search_query_from_report(report)

    first = search(index=finite_tree_index, query=query, top_k=5)
    second = search(index=finite_tree_index, query=query, top_k=5)

    assert [hit.declaration.full_name for hit in first] == [hit.declaration.full_name for hit in second]
    assert first[0].declaration.full_name == "SimpleGraph.IsTree.card_edgeFinset"


def test_enrich_readiness_candidates_uses_index_names(finite_tree_index) -> None:
    report = ReadinessReport(
        unit_id="finite_tree_edge_count",
        statement_readiness=ReadinessDimension(status="clear", recovered=["finite tree"], unresolved=[]),
        context_readiness=ReadinessDimension(status="partial", recovered=["graph", "tree"], unresolved=[]),
        notation_readiness=ReadinessDimension(status="partial", recovered=["|E|"], unresolved=[]),
        dependency_readiness=ReadinessDimension(
            status="partial",
            recovered=["edge count", "cardinality"],
            unresolved=[],
        ),
        existing_theorem_candidates=["ModelGuessed.TheoremName"],
        constructive_path=["leaf deletion"],
        blockers=["definition alignment for finite tree"],
        recommended_next_action="Confirm existing theorem alignment.",
    )

    enriched = enrich_readiness_candidates(report=report, index=finite_tree_index, top_k=3)

    assert enriched.existing_theorem_candidates[0] == "SimpleGraph.IsTree.card_edgeFinset"
    assert all(name in {d.full_name for d in finite_tree_index.declarations} for name in enriched.existing_theorem_candidates)


def test_enrich_from_unit_replaces_model_guess(finite_tree_index) -> None:
    unit = load_unit(EXAMPLE_DIR / "unit.json")
    report = ReadinessReport(
        unit_id=unit.unit_id,
        statement_readiness=ReadinessDimension(status="clear", recovered=["statement"], unresolved=[]),
        context_readiness=ReadinessDimension(status="partial", recovered=["tree"], unresolved=[]),
        notation_readiness=ReadinessDimension(status="partial", recovered=["|V|"], unresolved=[]),
        dependency_readiness=ReadinessDimension(status="partial", recovered=["induction"], unresolved=[]),
        existing_theorem_candidates=["ModelGuessed.TheoremName"],
        constructive_path=["leaf deletion"],
        blockers=["deletion notation"],
        recommended_next_action="Confirm existing theorem alignment.",
    )

    enriched = enrich_readiness_report_from_unit(
        report=report,
        unit=unit,
        index=finite_tree_index,
        top_k=3,
    )

    assert enriched.existing_theorem_candidates[0] == "SimpleGraph.IsTree.card_edgeFinset"


def test_search_returns_empty_for_blank_query(finite_tree_index) -> None:
    assert search(index=finite_tree_index, query="   ", top_k=5) == []


def test_build_search_query_from_unit_includes_statement() -> None:
    unit = TheoremProofUnit(
        unit_id="finite_tree_edge_count",
        source_id="source",
        statement="Let G be a finite tree.",
        proof="Use induction.",
        domain="graph_theory",
    )

    query = build_search_query_from_unit(unit)

    assert "finite tree" in query
    assert "graph_theory" not in query
    assert "graph theory" in query

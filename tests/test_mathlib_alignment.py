from pathlib import Path

import pytest

from fre_core.mathlib_alignment import (
    align_readiness_report,
    collect_alignment_queries,
    enrich_readiness_candidates_from_alignment,
)
from fre_core.mathlib_index import enrich_readiness_candidates, load_index
from fre_core.schemas import ReadinessDimension, ReadinessReport
from fre_core.validation import load_readiness_report, load_unit

ROOT = Path(__file__).resolve().parents[1]
FINITE_TREE_INDEX = ROOT / "fixtures" / "mathlib_declarations" / "finite_tree_v0.json"
CATEGORY_THEORY_INDEX = ROOT / "fixtures" / "mathlib_declarations" / "category_theory_v0.json"
FINITE_TREE_DIR = ROOT / "examples" / "finite_tree"
CATEGORY_THEORY_DIR = ROOT / "examples" / "category_theory_pullback"


@pytest.fixture
def finite_tree_index():
    return load_index(FINITE_TREE_INDEX)


@pytest.fixture
def category_theory_index():
    return load_index(CATEGORY_THEORY_INDEX)


def test_align_finite_tree_report_ranks_card_edgeFinset_first(finite_tree_index) -> None:
    report = load_readiness_report(FINITE_TREE_DIR / "readiness_report.json")
    unit = load_unit(FINITE_TREE_DIR / "unit.json")

    first = align_readiness_report(report=report, index=finite_tree_index, unit=unit)
    second = align_readiness_report(report=report, index=finite_tree_index, unit=unit)

    assert first.unit_id == report.unit_id
    assert first.index_id == finite_tree_index.index_id
    assert first.candidates
    assert first.candidates[0].full_name == "SimpleGraph.IsTree.card_edgeFinset"
    assert first.candidates[0].alignment_status == "candidate"
    assert first.confirmed == []
    assert [candidate.full_name for candidate in first.candidates] == [
        candidate.full_name for candidate in second.candidates
    ]


def test_align_category_theory_report_is_deterministic(category_theory_index) -> None:
    report = load_readiness_report(CATEGORY_THEORY_DIR / "readiness_report.json")
    unit = load_unit(CATEGORY_THEORY_DIR / "unit.json")

    alignment = align_readiness_report(report=report, index=category_theory_index, unit=unit)

    top_names = {candidate.full_name for candidate in alignment.candidates[:5]}
    assert "CategoryTheory.Limits.PreservesPullback" in top_names
    assert all(candidate.alignment_status == "candidate" for candidate in alignment.candidates)


def test_confirmed_alignment_requires_explicit_reviewer_flag(finite_tree_index) -> None:
    report = load_readiness_report(FINITE_TREE_DIR / "readiness_report.json")

    alignment = align_readiness_report(
        report=report,
        index=finite_tree_index,
        confirmed_full_names=frozenset({"SimpleGraph.IsTree.card_edgeFinset"}),
    )

    assert len(alignment.confirmed) == 1
    assert alignment.confirmed[0].alignment_status == "confirmed"
    assert alignment.confirmed[0].match_reasons == ["reviewer_confirmed"]
    assert alignment.candidates[0].alignment_status == "candidate"


def test_collect_alignment_queries_includes_candidates_and_statement_tokens() -> None:
    report = ReadinessReport(
        unit_id="finite_tree_edge_count",
        statement_readiness=ReadinessDimension(status="clear", recovered=["finite tree"], unresolved=[]),
        context_readiness=ReadinessDimension(status="partial", recovered=["graph"], unresolved=[]),
        notation_readiness=ReadinessDimension(status="partial", recovered=["|E|"], unresolved=[]),
        dependency_readiness=ReadinessDimension(status="partial", recovered=["cardinality"], unresolved=[]),
        existing_theorem_candidates=["SimpleGraph.IsTree.card_edgeFinset"],
        constructive_path=["leaf deletion"],
        blockers=["definition alignment for finite tree"],
        recommended_next_action="Confirm existing theorem alignment.",
    )
    unit = load_unit(FINITE_TREE_DIR / "unit.json")

    queries = collect_alignment_queries(report=report, unit=unit)
    sources = {query.source for query in queries}

    assert "existing_theorem_candidate" in sources
    assert "statement_recovered" in sources
    assert "unit_statement_token" in sources


def test_enrich_from_alignment_preserves_legacy_enrichment_behavior(finite_tree_index) -> None:
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

    legacy = enrich_readiness_candidates(report=report, index=finite_tree_index, top_k=3)
    alignment = align_readiness_report(report=report, index=finite_tree_index, top_k_total=3)
    enriched = enrich_readiness_candidates_from_alignment(report=report, alignment=alignment, top_k=3)

    assert legacy.existing_theorem_candidates[0] == "SimpleGraph.IsTree.card_edgeFinset"
    assert enriched.existing_theorem_candidates[0] == "SimpleGraph.IsTree.card_edgeFinset"


def test_alignment_candidate_includes_match_reasons(finite_tree_index) -> None:
    report = load_readiness_report(FINITE_TREE_DIR / "readiness_report.json")

    alignment = align_readiness_report(report=report, index=finite_tree_index, top_k_total=3)

    assert alignment.candidates[0].match_reasons
    assert alignment.candidates[0].score > 0

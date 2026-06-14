from pathlib import Path

import pytest

from fre_core.schemas import AtlasRecord, LeanTaskPackage, ProofGraph, ReadinessReport, TheoremProofUnit
from fre_core.validation import (
    ArtifactValidationError,
    load_atlas_record,
    load_leantask_package,
    load_proofgraph,
    load_readiness_report,
    load_unit,
    validate_proofgraph,
)

ROOT = Path(__file__).resolve().parents[1]
FINITE_TREE_DIR = ROOT / "examples" / "finite_tree"
CATEGORY_THEORY_DIR = ROOT / "examples" / "category_theory_pullback"


def test_finite_tree_unit_validates() -> None:
    unit = load_unit(FINITE_TREE_DIR / "unit.json")
    assert isinstance(unit, TheoremProofUnit)


def test_finite_tree_readiness_report_validates() -> None:
    report = load_readiness_report(FINITE_TREE_DIR / "readiness_report.json")
    assert isinstance(report, ReadinessReport)


def test_finite_tree_proofgraph_validates() -> None:
    graph = load_proofgraph(FINITE_TREE_DIR / "proofgraph.json")
    assert isinstance(graph, ProofGraph)


def test_finite_tree_atlas_record_validates() -> None:
    record = load_atlas_record(FINITE_TREE_DIR / "atlas_record.json")
    assert isinstance(record, AtlasRecord)


def test_finite_tree_leantask_validates() -> None:
    task = load_leantask_package(FINITE_TREE_DIR / "leantask.json")
    assert isinstance(task, LeanTaskPackage)


def test_category_theory_unit_validates() -> None:
    unit = load_unit(CATEGORY_THEORY_DIR / "unit.json")
    assert isinstance(unit, TheoremProofUnit)
    assert unit.domain == "category_theory"
    assert unit.unit_id == "category_theory_pullback_equivalence"


def test_category_theory_readiness_report_validates() -> None:
    report = load_readiness_report(CATEGORY_THEORY_DIR / "readiness_report.json")
    assert isinstance(report, ReadinessReport)
    assert report.unit_id == "category_theory_pullback_equivalence"
    assert report.existing_theorem_candidates
    assert report.constructive_path


def test_category_theory_proofgraph_validates() -> None:
    graph = load_proofgraph(CATEGORY_THEORY_DIR / "proofgraph.json")
    assert isinstance(graph, ProofGraph)
    assert graph.unit_id == "category_theory_pullback_equivalence"


def test_category_theory_atlas_record_validates() -> None:
    record = load_atlas_record(CATEGORY_THEORY_DIR / "atlas_record.json")
    assert isinstance(record, AtlasRecord)
    assert record.unit_id == "category_theory_pullback_equivalence"


def test_category_theory_leantask_validates() -> None:
    task = load_leantask_package(CATEGORY_THEORY_DIR / "leantask.json")
    assert isinstance(task, LeanTaskPackage)
    assert task.unit_id == "category_theory_pullback_equivalence"


def test_category_theory_leantask_l1_validates() -> None:
    task = load_leantask_package(CATEGORY_THEORY_DIR / "leantask_L1.json")
    assert isinstance(task, LeanTaskPackage)
    assert task.level.value == "L1"
    assert task.formal_target


def test_validate_example_dir_category_theory() -> None:
    from fre_core.cli import validate_example_dir

    validate_example_dir(CATEGORY_THEORY_DIR)


def test_proofgraph_rejects_missing_edge_endpoint() -> None:
    graph = ProofGraph(
        unit_id="bad_graph",
        nodes=[{"node_id": "N1", "node_type": "statement", "text": "A theorem."}],
        edges=[{"source": "N1", "target": "N_missing", "edge_type": "uses"}],
    )

    with pytest.raises(ArtifactValidationError) as excinfo:
        validate_proofgraph(graph)

    assert "missing_edge_target" in str(excinfo.value)

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
EXAMPLE_DIR = ROOT / "examples" / "finite_tree"


def test_finite_tree_unit_validates() -> None:
    unit = load_unit(EXAMPLE_DIR / "unit.json")
    assert isinstance(unit, TheoremProofUnit)


def test_finite_tree_readiness_report_validates() -> None:
    report = load_readiness_report(EXAMPLE_DIR / "readiness_report.json")
    assert isinstance(report, ReadinessReport)


def test_finite_tree_proofgraph_validates() -> None:
    graph = load_proofgraph(EXAMPLE_DIR / "proofgraph.json")
    assert isinstance(graph, ProofGraph)


def test_finite_tree_atlas_record_validates() -> None:
    record = load_atlas_record(EXAMPLE_DIR / "atlas_record.json")
    assert isinstance(record, AtlasRecord)


def test_finite_tree_leantask_validates() -> None:
    task = load_leantask_package(EXAMPLE_DIR / "leantask.json")
    assert isinstance(task, LeanTaskPackage)


def test_proofgraph_rejects_missing_edge_endpoint() -> None:
    graph = ProofGraph(
        unit_id="bad_graph",
        nodes=[{"node_id": "N1", "node_type": "statement", "text": "A theorem."}],
        edges=[{"source": "N1", "target": "N_missing", "edge_type": "uses"}],
    )

    with pytest.raises(ArtifactValidationError) as excinfo:
        validate_proofgraph(graph)

    assert "missing_edge_target" in str(excinfo.value)

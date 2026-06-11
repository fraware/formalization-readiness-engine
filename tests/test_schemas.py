from pathlib import Path

from fre_core.schemas import AtlasRecord, LeanTaskPackage, ProofGraph, ReadinessReport, TheoremProofUnit

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / "examples" / "finite_tree"


def test_finite_tree_unit_validates() -> None:
    TheoremProofUnit.model_validate_json((EXAMPLE_DIR / "unit.json").read_text())


def test_finite_tree_readiness_report_validates() -> None:
    ReadinessReport.model_validate_json((EXAMPLE_DIR / "readiness_report.json").read_text())


def test_finite_tree_proofgraph_validates() -> None:
    ProofGraph.model_validate_json((EXAMPLE_DIR / "proofgraph.json").read_text())


def test_finite_tree_atlas_record_validates() -> None:
    AtlasRecord.model_validate_json((EXAMPLE_DIR / "atlas_record.json").read_text())


def test_finite_tree_leantask_validates() -> None:
    LeanTaskPackage.model_validate_json((EXAMPLE_DIR / "leantask.json").read_text())

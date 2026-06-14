"""Round-trip schema migration tests for committed artifact fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from fre_core.schemas import ReviewStatus
from fre_core.validation import (
    ArtifactValidationError,
    load_atlas_record,
    load_leantask_package,
    load_proofgraph,
    load_readiness_report,
    load_unit,
    validation_mode_for_review_status,
)

ROOT = Path(__file__).resolve().parents[1]

COMMITTED_READINESS_REPORTS = sorted(
    path
    for path in (
        list((ROOT / "examples").rglob("readiness_report.json"))
        + list((ROOT / "benchmarks" / "readinessbench").rglob("readiness_report.json"))
        + list((ROOT / "tests" / "fixtures" / "readinessbench_predictions").rglob("readiness_report.json"))
        + list((ROOT / "tests" / "fixtures" / "baseline_predictions").rglob("readiness_report.json"))
    )
    if path.is_file()
)
COMMITTED_PROOFGRAPHS = sorted(
    path
    for path in (
        list((ROOT / "examples").rglob("proofgraph.json"))
        + list((ROOT / "tests" / "fixtures" / "baseline_predictions").rglob("proofgraph.json"))
    )
    if path.is_file()
)
COMMITTED_ATLAS_RECORDS = sorted(
    path
    for path in (
        list((ROOT / "examples").rglob("atlas_record.json"))
        + list((ROOT / "benchmarks" / "readinessbench" / "gold").rglob("atlas_record.json"))
    )
    if path.is_file()
)
COMMITTED_UNITS = sorted(
    path
    for path in (
        list((ROOT / "examples").rglob("unit.json"))
        + list((ROOT / "benchmarks" / "readinessbench").rglob("unit.json"))
        + list((ROOT / "corpus" / "units").glob("*.json"))
    )
    if path.is_file()
)
COMMITTED_LEANTASKS = sorted((ROOT / "examples").rglob("leantask*.json"))


@pytest.mark.parametrize("path", COMMITTED_READINESS_REPORTS, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_committed_readiness_reports_round_trip(path: Path) -> None:
    report = load_readiness_report(path)
    if report.review_status in {
        ReviewStatus.EXPERT_REVIEWED,
        ReviewStatus.HUMAN_REVIEWED,
        ReviewStatus.MACHINE_VALIDATED,
    }:
        assert validation_mode_for_review_status(report.review_status) == "strict"
    report.model_dump_json()


@pytest.mark.parametrize("path", COMMITTED_PROOFGRAPHS, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_committed_proofgraphs_round_trip(path: Path) -> None:
    graph = load_proofgraph(path)
    graph.model_dump_json()


@pytest.mark.parametrize("path", COMMITTED_ATLAS_RECORDS, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_committed_atlas_records_round_trip(path: Path) -> None:
    record = load_atlas_record(path)
    record.model_dump_json()


@pytest.mark.parametrize("path", COMMITTED_UNITS, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_committed_units_round_trip(path: Path) -> None:
    unit = load_unit(path)
    unit.model_dump_json()


@pytest.mark.parametrize("path", COMMITTED_LEANTASKS, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_committed_leantasks_round_trip(path: Path) -> None:
    task = load_leantask_package(path)
    task.model_dump_json()


def test_source_span_end_must_not_be_before_start() -> None:
    from pydantic import ValidationError

    from fre_core.schemas import SourceSpan

    SourceSpan(start=0, end=5)
    with pytest.raises(ValidationError):
        SourceSpan(start=10, end=5)


def test_gold_readiness_reports_use_strict_validation() -> None:
    gold_reports = sorted((ROOT / "benchmarks" / "readinessbench" / "gold").rglob("readiness_report.json"))
    for path in gold_reports:
        report = load_readiness_report(path)
        assert validation_mode_for_review_status(report.review_status) == "strict"


def test_live_demo_candidate_artifacts_validate_permissively() -> None:
    live_root = ROOT / "artifacts" / "generated" / "demo_run" / "live"
    if not live_root.is_dir():
        pytest.skip("Live demo artifacts are not present in this checkout.")

    for example_dir in sorted(path for path in live_root.iterdir() if path.is_dir()):
        report_path = example_dir / "readiness_report.model.json"
        graph_path = example_dir / "proofgraph.model.json"
        atlas_path = example_dir / "atlas_record.model.json"
        if report_path.is_file():
            load_readiness_report(report_path, mode="permissive")
        if graph_path.is_file():
            load_proofgraph(graph_path, mode="permissive")
        if atlas_path.is_file():
            load_atlas_record(atlas_path, mode="permissive")
            with pytest.raises(ArtifactValidationError):
                load_atlas_record(atlas_path, mode="strict")

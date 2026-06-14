from pathlib import Path

import pytest

from fre_core.benchmark import (
    BenchmarkValidationError,
    default_benchmark_root,
    default_manifest_path,
    load_manifest,
    resolve_benchmark_path,
    run_readinessbench,
    validate_benchmark_item,
    validate_manifest,
)
from fre_core.evaluation import score_readiness_report
from fre_core.schemas import BenchmarkItem, BenchmarkTier, ReviewStatus
from fre_core.validation import load_readiness_report

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = default_benchmark_root(repo_root=ROOT)
MANIFEST_PATH = default_manifest_path(repo_root=ROOT)
PREDICTIONS_DIR = ROOT / "tests" / "fixtures" / "readinessbench_predictions"


def test_default_manifest_loads_and_validates() -> None:
    manifest = load_manifest(MANIFEST_PATH)
    gold_reports = validate_manifest(manifest=manifest, benchmark_root=BENCHMARK_ROOT)

    assert manifest.benchmark_id == "readinessbench"
    assert len(manifest.items) == 3
    assert len(gold_reports) == 1
    assert gold_reports[0].review_status == ReviewStatus.EXPERT_REVIEWED


def test_gold_item_rejects_candidate_review_status(tmp_path: Path) -> None:
    benchmark_root = tmp_path / "bench"
    item_dir = benchmark_root / "gold" / "bad_item"
    item_dir.mkdir(parents=True)

    unit_path = item_dir / "unit.json"
    report_path = item_dir / "readiness_report.json"
    unit_path.write_text(
        (
            '{"schema_version":"0.1","unit_id":"u1","source_id":"s1","statement":"s",'
            '"proof":null,"local_context":null,"domain":"d","statement_span":null,'
            '"proof_span":null,"review_status":"candidate"}'
        ),
        encoding="utf-8",
    )
    report_path.write_text(
        (
            '{"schema_version":"0.1","unit_id":"u1","statement_readiness":{"status":"clear"},'
            '"context_readiness":{"status":"clear"},"notation_readiness":{"status":"clear"},'
            '"dependency_readiness":{"status":"clear"},"existing_theorem_candidates":[],'
            '"constructive_path":["step"],"blockers":[],"recommended_next_action":"next",'
            '"review_status":"candidate"}'
        ),
        encoding="utf-8",
    )

    item = BenchmarkItem(
        item_id="bad_gold",
        unit_id="u1",
        tier=BenchmarkTier.GOLD,
        unit_path="gold/bad_item/unit.json",
        readiness_report_path="gold/bad_item/readiness_report.json",
    )

    with pytest.raises(BenchmarkValidationError, match="review_status='candidate'"):
        validate_benchmark_item(item=item, benchmark_root=benchmark_root)


def test_manifest_rejects_generated_artifact_paths(tmp_path: Path) -> None:
    with pytest.raises(BenchmarkValidationError, match="generated artifacts"):
        resolve_benchmark_path(
            benchmark_root=tmp_path,
            relative_path="gold/../../artifacts/generated/finite_tree/readiness_report.json",
            context="test path",
        )


def test_run_readinessbench_produces_deterministic_macro_f1() -> None:
    gold = load_readiness_report(
        BENCHMARK_ROOT / "gold" / "finite_tree_edge_count" / "readiness_report.json"
    )
    predicted = load_readiness_report(
        PREDICTIONS_DIR / "finite_tree_edge_count" / "readiness_report.json"
    )
    expected_macro_f1 = round(score_readiness_report(predicted=predicted, gold=gold).macro_f1, 6)

    report = run_readinessbench(
        manifest_path=MANIFEST_PATH,
        predictions_dir=PREDICTIONS_DIR,
        benchmark_root=BENCHMARK_ROOT,
    )

    assert report.scored_item_count == 1
    assert report.gold_item_count == 1
    assert report.macro_f1_mean == expected_macro_f1
    assert report.items[0].macro_f1 == expected_macro_f1
    assert report.items[0].unit_id == "finite_tree_edge_count"


def test_run_readinessbench_is_repeatable() -> None:
    first = run_readinessbench(
        manifest_path=MANIFEST_PATH,
        predictions_dir=PREDICTIONS_DIR,
        benchmark_root=BENCHMARK_ROOT,
    )
    second = run_readinessbench(
        manifest_path=MANIFEST_PATH,
        predictions_dir=PREDICTIONS_DIR,
        benchmark_root=BENCHMARK_ROOT,
    )

    assert first.model_dump() == second.model_dump()


BASELINE_PREDICTIONS_DIR = ROOT / "tests" / "fixtures" / "baseline_predictions"


def test_run_benchmark_evaluation_scores_full_macro_f1() -> None:
    from fre_core.benchmark import run_benchmark_evaluation

    report = run_benchmark_evaluation(
        manifest_path=MANIFEST_PATH,
        predictions_dir=BASELINE_PREDICTIONS_DIR,
        benchmark_root=BENCHMARK_ROOT,
        repo_root=ROOT,
    )

    assert report.scored_item_count == 1
    assert report.full_macro_f1_mean is not None
    assert report.items[0].full_macro_f1 is not None


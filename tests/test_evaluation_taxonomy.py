from pathlib import Path

from fre_core.evaluation_taxonomy import ErrorCategory, aggregate_error_summaries, categorize_baseline_run
from fre_core.validation import load_readiness_report

ROOT = Path(__file__).resolve().parents[1]


def test_categorize_baseline_run_detects_notation_and_blocker_errors(tmp_path: Path) -> None:
    gold_dir = ROOT / "examples" / "finite_tree"
    predicted_dir = tmp_path / "finite_tree_edge_count"
    predicted_dir.mkdir(parents=True)

    gold_report = load_readiness_report(gold_dir / "readiness_report.json")
    predicted = gold_report.model_copy(
        update={
            "blockers": ["different blocker"],
            "notation_readiness": gold_report.notation_readiness.model_copy(
                update={"unresolved": ["extra notation gap"]}
            ),
        }
    )
    predicted_dir.joinpath("readiness_report.json").write_text(
        predicted.model_dump_json(indent=2),
        encoding="utf-8",
    )
    for name in ("proofgraph.json", "atlas_record.json", "leantask.json"):
        (predicted_dir / name).write_text((gold_dir / name).read_text(encoding="utf-8"), encoding="utf-8")

    summary = categorize_baseline_run(
        predicted_dir=predicted_dir,
        gold_dir=gold_dir,
        unit_id="finite_tree_edge_count",
    )

    assert ErrorCategory.NOTATION in summary.categories
    assert ErrorCategory.BLOCKERS in summary.categories


def test_aggregate_error_summaries_counts_categories() -> None:
    gold_dir = ROOT / "examples" / "finite_tree"
    perfect = categorize_baseline_run(
        predicted_dir=gold_dir,
        gold_dir=gold_dir,
        unit_id="finite_tree_edge_count",
    )

    payload = aggregate_error_summaries(summaries=[perfect])

    assert payload["unit_count"] == 1
    assert payload["total_errors"] == 0
    assert payload["categories"]["notation"]["count"] == 0

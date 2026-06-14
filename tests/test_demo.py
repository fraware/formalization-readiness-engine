from pathlib import Path

import pytest

from fre_core.demo_runner import (
    EXAMPLE_CONFIG,
    default_demo_output_root,
    default_predictions_dir,
    main,
    resolve_example_keys,
    run_demo,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def skip_lean_in_demo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_SKIP_LEAN", "1")


def test_resolve_example_keys_accepts_aliases() -> None:
    assert resolve_example_keys("all") == ("finite_tree", "category_theory_pullback")
    assert resolve_example_keys("finite_tree") == ("finite_tree",)
    assert resolve_example_keys("category-theory-pullback") == ("category_theory_pullback",)


def test_offline_demo_runs_both_examples() -> None:
    result = run_demo(offline=True, example="all", repo_root_path=ROOT)

    assert len(result.example_results) == 2
    assert result.macro_f1_mean is not None

    for example_result in result.example_results:
        assert example_result.validation_ok
        assert example_result.top_alignment
        assert example_result.lean_check_status == "skipped"

        output_dir = example_result.output_dir
        assert (output_dir / "alignment.json").is_file()
        assert (output_dir / "readiness_report.enriched.json").is_file()

        lean_name = EXAMPLE_CONFIG[example_result.example_key]["lean_output"]
        assert (output_dir / lean_name).is_file()
        assert "theorem" in (output_dir / lean_name).read_text(encoding="utf-8")


def test_offline_demo_finite_tree_only() -> None:
    result = run_demo(offline=True, example="finite_tree", repo_root_path=ROOT)

    assert len(result.example_results) == 1
    assert result.example_results[0].unit_id == "finite_tree_edge_count"
    assert result.example_results[0].top_alignment == "SimpleGraph.IsTree.card_edgeFinset"


def test_main_returns_zero_for_offline_demo() -> None:
    assert main(offline=True, example="all") == 0


def test_default_paths_under_repo_root() -> None:
    assert default_predictions_dir(root=ROOT).is_dir()
    output_root = default_demo_output_root(root=ROOT, offline=True)
    assert output_root.as_posix().endswith("artifacts/generated/demo_run/offline")

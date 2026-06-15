from pathlib import Path

from fre_core.evaluation import score_readiness_report
from fre_core.evaluation_v03 import (
    default_equivalence_dir,
    score_readiness_report_v03,
    score_theorem_candidates_declaration_id,
    _load_equivalence_groups,
)
from fre_core.mathlib_index import load_index
from fre_core.validation import load_readiness_report

ROOT = Path(__file__).resolve().parents[1]
CATEGORY_THEORY_INDEX = ROOT / "fixtures" / "mathlib_declarations" / "category_theory_v0.json"
LIVE_PREDICTION = (
    ROOT / "artifacts" / "generated" / "demo_run" / "live" / "category_theory_pullback" / "readiness_report.model.json"
)
GOLD_REPORT = (
    ROOT
    / "benchmarks"
    / "readinessbench"
    / "gold"
    / "category_theory_pullback_equivalence"
    / "readiness_report.json"
)


def test_category_theory_lexical_f1_zero_semantic_declaration_match() -> None:
    if not LIVE_PREDICTION.is_file():
        import pytest

        pytest.skip("live prediction artifact missing")

    predicted = load_readiness_report(LIVE_PREDICTION, mode="permissive")
    gold = load_readiness_report(GOLD_REPORT)
    index = load_index(CATEGORY_THEORY_INDEX)

    lexical = score_readiness_report(predicted=predicted, gold=gold)
    assert lexical.existing_theorem_candidates.f1 == 0.0

    equivalence_groups = _load_equivalence_groups(
        unit_id=gold.unit_id,
        equivalence_dir=default_equivalence_dir(repo_root=ROOT),
    )
    semantic = score_theorem_candidates_declaration_id(
        predicted=predicted.existing_theorem_candidates,
        gold=gold.existing_theorem_candidates,
        index=index,
        equivalence_groups=equivalence_groups,
    )
    assert semantic.f1 > 0.0


def test_score_readiness_report_v03_uses_equivalence_fixture() -> None:
    if not LIVE_PREDICTION.is_file():
        import pytest

        pytest.skip("live prediction artifact missing")

    predicted = load_readiness_report(LIVE_PREDICTION, mode="permissive")
    gold = load_readiness_report(GOLD_REPORT)
    index = load_index(CATEGORY_THEORY_INDEX)

    scores = score_readiness_report_v03(
        predicted=predicted,
        gold=gold,
        index=index,
        equivalence_dir=default_equivalence_dir(repo_root=ROOT),
    )
    assert scores.theorem_candidates_declaration_f1 > 0.0
    assert scores.lexical_macro_f1 == score_readiness_report(predicted=predicted, gold=gold).macro_f1

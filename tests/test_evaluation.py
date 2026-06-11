import pytest

from fre_core.evaluation import score_label_set, score_readiness_report
from fre_core.schemas import ReadinessDimension, ReadinessReport


def dimension() -> ReadinessDimension:
    return ReadinessDimension(status="clear", recovered=[], unresolved=[])


def report(*, unit_id: str, candidates: list[str], path: list[str], blockers: list[str]) -> ReadinessReport:
    return ReadinessReport(
        unit_id=unit_id,
        statement_readiness=dimension(),
        context_readiness=dimension(),
        notation_readiness=dimension(),
        dependency_readiness=dimension(),
        existing_theorem_candidates=candidates,
        constructive_path=path,
        blockers=blockers,
        recommended_next_action="Next action.",
    )


def test_score_label_set_computes_precision_recall_f1() -> None:
    score = score_label_set(predicted=["A", "B"], gold=["a", "C"])

    assert score.true_positives == 1
    assert score.predicted_count == 2
    assert score.gold_count == 2
    assert score.precision == 0.5
    assert score.recall == 0.5
    assert score.f1 == 0.5


def test_score_label_set_handles_empty_sets() -> None:
    score = score_label_set(predicted=[], gold=[])

    assert score.precision == 1.0
    assert score.recall == 1.0
    assert score.f1 == 1.0


def test_score_readiness_report() -> None:
    predicted = report(
        unit_id="u1",
        candidates=["SimpleGraph.IsTree.card_edgeFinset"],
        path=["leaf deletion"],
        blockers=["notation mismatch"],
    )
    gold = report(
        unit_id="u1",
        candidates=["simplegraph.istree.card_edgefinset"],
        path=["leaf deletion", "count update"],
        blockers=["notation mismatch"],
    )

    scores = score_readiness_report(predicted=predicted, gold=gold)

    assert scores.existing_theorem_candidates.f1 == 1.0
    assert round(scores.constructive_path.f1, 3) == 0.667
    assert scores.blockers.f1 == 1.0
    assert round(scores.macro_f1, 3) == 0.889


def test_score_readiness_report_rejects_unit_mismatch() -> None:
    predicted = report(unit_id="u1", candidates=[], path=["path"], blockers=[])
    gold = report(unit_id="u2", candidates=[], path=["path"], blockers=[])

    with pytest.raises(ValueError):
        score_readiness_report(predicted=predicted, gold=gold)

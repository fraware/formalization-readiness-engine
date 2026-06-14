"""Deterministic evaluation utilities for ReadinessBench."""

from __future__ import annotations

from dataclasses import dataclass

from fre_core.schemas import ReadinessDimension, ReadinessReport


@dataclass(frozen=True)
class PrecisionRecallF1:
    """Set-overlap precision, recall, and F1."""

    precision: float
    recall: float
    f1: float
    true_positives: int
    predicted_count: int
    gold_count: int


def _normalize_label(value: str) -> str:
    """Normalize labels for deterministic set comparison."""
    return " ".join(value.casefold().strip().split())


def score_label_set(*, predicted: list[str], gold: list[str]) -> PrecisionRecallF1:
    """Score a predicted label list against a gold label list."""
    predicted_set = {_normalize_label(item) for item in predicted if item.strip()}
    gold_set = {_normalize_label(item) for item in gold if item.strip()}
    true_positives = len(predicted_set & gold_set)

    precision = true_positives / len(predicted_set) if predicted_set else 1.0 if not gold_set else 0.0
    recall = true_positives / len(gold_set) if gold_set else 1.0 if not predicted_set else 0.0
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)

    return PrecisionRecallF1(
        precision=precision,
        recall=recall,
        f1=f1,
        true_positives=true_positives,
        predicted_count=len(predicted_set),
        gold_count=len(gold_set),
    )


@dataclass(frozen=True)
class ReadinessDimensionScores:
    """Deterministic scores for one readiness dimension field group."""

    recovered: PrecisionRecallF1
    unresolved: PrecisionRecallF1

    @property
    def f1(self) -> float:
        return (self.recovered.f1 + self.unresolved.f1) / 2


def score_readiness_dimension(
    *, predicted: ReadinessDimension, gold: ReadinessDimension
) -> ReadinessDimensionScores:
    """Score one predicted readiness dimension against gold."""
    return ReadinessDimensionScores(
        recovered=score_label_set(predicted=predicted.recovered, gold=gold.recovered),
        unresolved=score_label_set(predicted=predicted.unresolved, gold=gold.unresolved),
    )


@dataclass(frozen=True)
class ReadinessReportScores:
    """Deterministic scores for major readiness-report fields."""

    existing_theorem_candidates: PrecisionRecallF1
    constructive_path: PrecisionRecallF1
    blockers: PrecisionRecallF1
    notation_readiness: ReadinessDimensionScores

    @property
    def macro_f1(self) -> float:
        return (
            self.existing_theorem_candidates.f1
            + self.constructive_path.f1
            + self.blockers.f1
            + self.notation_readiness.f1
        ) / 4


def score_readiness_report(*, predicted: ReadinessReport, gold: ReadinessReport) -> ReadinessReportScores:
    """Score one predicted readiness report against one reviewed report."""
    if predicted.unit_id != gold.unit_id:
        raise ValueError(f"Unit mismatch: predicted={predicted.unit_id!r}, gold={gold.unit_id!r}")

    return ReadinessReportScores(
        existing_theorem_candidates=score_label_set(
            predicted=predicted.existing_theorem_candidates,
            gold=gold.existing_theorem_candidates,
        ),
        constructive_path=score_label_set(
            predicted=predicted.constructive_path,
            gold=gold.constructive_path,
        ),
        blockers=score_label_set(predicted=predicted.blockers, gold=gold.blockers),
        notation_readiness=score_readiness_dimension(
            predicted=predicted.notation_readiness,
            gold=gold.notation_readiness,
        ),
    )

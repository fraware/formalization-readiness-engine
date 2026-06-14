"""Deterministic LeanTask package evaluation."""

from __future__ import annotations

from fre_core.evaluation import PrecisionRecallF1, score_label_set
from fre_core.schemas import LeanTaskPackage


def _normalize(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(value.casefold().strip().split())


def score_leantask_package(*, predicted: LeanTaskPackage, gold: LeanTaskPackage) -> PrecisionRecallF1:
    if predicted.unit_id != gold.unit_id:
        raise ValueError(f"Unit mismatch: predicted={predicted.unit_id!r}, gold={gold.unit_id!r}")
    exact_fields = [
        _normalize(predicted.level.value) == _normalize(gold.level.value),
        _normalize(predicted.informal_statement) == _normalize(gold.informal_statement),
        _normalize(predicted.formal_target) == _normalize(gold.formal_target),
        _normalize(predicted.proof_path) == _normalize(gold.proof_path),
        _normalize(predicted.fallback_path) == _normalize(gold.fallback_path),
        _normalize(predicted.next_action) == _normalize(gold.next_action),
        _normalize(predicted.leantask_id) == _normalize(gold.leantask_id),
    ]
    import_score = score_label_set(predicted=predicted.imports, gold=gold.imports)
    hypothesis_score = score_label_set(predicted=predicted.hypotheses, gold=gold.hypotheses)
    components = exact_fields + [import_score.f1, hypothesis_score.f1]
    f1 = sum(components) / len(components)
    return PrecisionRecallF1(
        precision=f1,
        recall=f1,
        f1=f1,
        true_positives=int(round(f1 * len(components))),
        predicted_count=len(components),
        gold_count=len(components),
    )

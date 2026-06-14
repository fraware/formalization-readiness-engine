"""Deterministic Atlas record evaluation."""

from __future__ import annotations

from fre_core.evaluation import PrecisionRecallF1
from fre_core.schemas import AtlasRecord

_ATLAS_FIELDS = (
    "blocker_type",
    "evidence",
    "recommended_action",
)


def _normalize(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).casefold().strip().split())


def score_atlas_record(*, predicted: AtlasRecord, gold: AtlasRecord) -> PrecisionRecallF1:
    if predicted.unit_id != gold.unit_id:
        raise ValueError(f"Unit mismatch: predicted={predicted.unit_id!r}, gold={gold.unit_id!r}")
    matches = sum(
        _normalize(getattr(predicted, field)) == _normalize(getattr(gold, field))
        for field in _ATLAS_FIELDS
    )
    total = len(_ATLAS_FIELDS)
    f1 = matches / total
    return PrecisionRecallF1(
        precision=f1,
        recall=f1,
        f1=f1,
        true_positives=matches,
        predicted_count=total,
        gold_count=total,
    )

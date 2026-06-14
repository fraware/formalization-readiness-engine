"""ReadinessBench manifest loading, tier validation, and evaluation runner."""

from __future__ import annotations

from pathlib import Path

from fre_core.evaluation import score_readiness_report
from fre_core.evaluation_atlas import score_atlas_record
from fre_core.evaluation_leantask import score_leantask_package
from fre_core.evaluation_proofgraph import score_proofgraph
from fre_core.schemas import (
    BenchmarkEvaluationReport,
    BenchmarkItem,
    BenchmarkItemScore,
    BenchmarkManifest,
    BenchmarkTier,
    ReadinessDimension,
    ReadinessReport,
    ReviewStatus,
    TheoremProofUnit,
)
from fre_core.validation import load_atlas_record, load_leantask_package, load_proofgraph, load_readiness_report, load_unit

TIER_ALLOWED_REVIEW_STATUSES: dict[BenchmarkTier, frozenset[ReviewStatus]] = {
    BenchmarkTier.BRONZE: frozenset({ReviewStatus.CANDIDATE, ReviewStatus.MACHINE_VALIDATED}),
    BenchmarkTier.SILVER: frozenset({ReviewStatus.HUMAN_REVIEWED}),
    BenchmarkTier.GOLD: frozenset({ReviewStatus.HUMAN_REVIEWED, ReviewStatus.EXPERT_REVIEWED}),
}

GENERATED_ARTIFACT_SEGMENT = "artifacts/generated"
PREDICTION_REPORT_FILENAME = "readiness_report.json"
PREDICTION_PROOFGRAPH_FILENAME = "proofgraph.json"
PREDICTION_ATLAS_FILENAME = "atlas_record.json"
PREDICTION_LEANTASK_FILENAME = "leantask.json"


class BenchmarkValidationError(ValueError):
    """Raised when a benchmark manifest or item violates tier invariants."""


def _repo_root_from_module() -> Path:
    return Path(__file__).resolve().parents[4]


def default_benchmark_root(*, repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root_from_module()
    return root / "benchmarks" / "readinessbench"


def default_manifest_path(*, repo_root: Path | None = None) -> Path:
    return default_benchmark_root(repo_root=repo_root) / "manifest.json"


def load_manifest(path: Path) -> BenchmarkManifest:
    return BenchmarkManifest.model_validate_json(path.read_text(encoding="utf-8"))


def _normalize_relative_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _reject_generated_artifact_path(*, path: Path, context: str) -> None:
    parts = {part.casefold() for part in path.parts}
    if "artifacts" in parts and "generated" in parts:
        raise BenchmarkValidationError(
            f"{context} must not reference generated artifacts: {path.as_posix()}"
        )
    if GENERATED_ARTIFACT_SEGMENT.casefold() in path.as_posix().casefold():
        raise BenchmarkValidationError(
            f"{context} must not reference generated artifacts: {path.as_posix()}"
        )


def resolve_benchmark_path(*, benchmark_root: Path, relative_path: str, context: str) -> Path:
    normalized = _normalize_relative_path(relative_path)
    if not normalized:
        raise BenchmarkValidationError(f"{context} must not be empty.")
    if GENERATED_ARTIFACT_SEGMENT.casefold() in normalized.casefold():
        raise BenchmarkValidationError(
            f"{context} must not reference generated artifacts: {relative_path}"
        )
    candidate = (benchmark_root / normalized).resolve()
    root = benchmark_root.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise BenchmarkValidationError(
            f"{context} must stay under the benchmark root: {relative_path}"
        ) from exc
    _reject_generated_artifact_path(path=candidate, context=context)
    return candidate


def validate_review_status_for_tier(*, tier: BenchmarkTier, review_status: ReviewStatus, context: str) -> None:
    allowed = TIER_ALLOWED_REVIEW_STATUSES[tier]
    if review_status not in allowed:
        allowed_values = ", ".join(sorted(status.value for status in allowed))
        raise BenchmarkValidationError(
            f"{context} has review_status={review_status.value!r}, "
            f"but tier {tier.value} allows only: {allowed_values}."
        )


def validate_benchmark_item(*, item: BenchmarkItem, benchmark_root: Path) -> ReadinessReport:
    unit_path = resolve_benchmark_path(
        benchmark_root=benchmark_root,
        relative_path=item.unit_path,
        context=f"item {item.item_id!r} unit_path",
    )
    report_path = resolve_benchmark_path(
        benchmark_root=benchmark_root,
        relative_path=item.readiness_report_path,
        context=f"item {item.item_id!r} readiness_report_path",
    )
    if not unit_path.exists():
        raise BenchmarkValidationError(f"Missing unit artifact for item {item.item_id!r}: {unit_path.as_posix()}")
    if not report_path.exists():
        raise BenchmarkValidationError(
            f"Missing readiness report for item {item.item_id!r}: {report_path.as_posix()}"
        )
    unit = load_unit(unit_path)
    report = load_readiness_report(report_path)
    if unit.unit_id != item.unit_id:
        raise BenchmarkValidationError(
            f"item {item.item_id!r} unit_id={item.unit_id!r} does not match unit artifact {unit.unit_id!r}."
        )
    if report.unit_id != item.unit_id:
        raise BenchmarkValidationError(
            f"item {item.item_id!r} unit_id={item.unit_id!r} does not match report artifact {report.unit_id!r}."
        )
    validate_review_status_for_tier(
        tier=item.tier, review_status=report.review_status, context=f"item {item.item_id!r} readiness report"
    )
    validate_review_status_for_tier(
        tier=item.tier, review_status=unit.review_status, context=f"item {item.item_id!r} unit"
    )
    expected_tier_prefix = f"{item.tier.value}/"
    for label, relative in (("unit_path", item.unit_path), ("readiness_report_path", item.readiness_report_path)):
        normalized = _normalize_relative_path(relative)
        if not normalized.startswith(expected_tier_prefix):
            raise BenchmarkValidationError(
                f"item {item.item_id!r} tier={item.tier.value} but {label}={relative!r} "
                f"is not under {expected_tier_prefix!r}."
            )
    return report


def validate_manifest(*, manifest: BenchmarkManifest, benchmark_root: Path) -> list[ReadinessReport]:
    if not manifest.items:
        raise BenchmarkValidationError("Benchmark manifest must contain at least one item.")
    seen_item_ids: set[str] = set()
    gold_reports: list[ReadinessReport] = []
    for item in manifest.items:
        if item.item_id in seen_item_ids:
            raise BenchmarkValidationError(f"Duplicate benchmark item_id: {item.item_id!r}")
        seen_item_ids.add(item.item_id)
        report = validate_benchmark_item(item=item, benchmark_root=benchmark_root)
        if item.tier == BenchmarkTier.GOLD:
            gold_reports.append(report)
    if not gold_reports:
        raise BenchmarkValidationError("Benchmark manifest must contain at least one gold item.")
    return gold_reports


def create_bronze_readiness_placeholder(unit: TheoremProofUnit) -> ReadinessReport:
    pending = ReadinessDimension(
        status="pending",
        recovered=[],
        unresolved=["awaiting extraction pass"],
        notes="Bronze placeholder generated from corpus ingestion.",
    )
    return ReadinessReport(
        unit_id=unit.unit_id,
        statement_readiness=pending,
        context_readiness=pending,
        notation_readiness=pending,
        dependency_readiness=pending,
        existing_theorem_candidates=[],
        constructive_path=["awaiting machine extraction pass"],
        blockers=["awaiting machine extraction pass"],
        recommended_next_action="Run extract-report to populate bronze readiness fields.",
        review_status=ReviewStatus.CANDIDATE,
    )


def promote_benchmark_item(
    *, unit: TheoremProofUnit, manifest: BenchmarkManifest, benchmark_root: Path, overwrite: bool = False
) -> BenchmarkItem:
    item_id = f"{unit.unit_id}_bronze"
    existing = {item.item_id: item for item in manifest.items}
    if item_id in existing and not overwrite:
        raise BenchmarkValidationError(f"Benchmark item already exists for unit_id={unit.unit_id!r}: {item_id!r}")
    item_dir = benchmark_root / "bronze" / unit.unit_id
    item_dir.mkdir(parents=True, exist_ok=True)
    unit_path = item_dir / "unit.json"
    report_path = item_dir / "readiness_report.json"
    _reject_generated_artifact_path(path=unit_path.resolve(), context="Bronze unit path")
    _reject_generated_artifact_path(path=report_path.resolve(), context="Bronze report path")
    bronze_unit = unit.model_copy(update={"review_status": ReviewStatus.CANDIDATE})
    report = create_bronze_readiness_placeholder(bronze_unit)
    unit_path.write_text(bronze_unit.model_dump_json(indent=2) + "\n", encoding="utf-8")
    report_path.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    item = BenchmarkItem(
        item_id=item_id,
        unit_id=unit.unit_id,
        tier=BenchmarkTier.BRONZE,
        unit_path=f"bronze/{unit.unit_id}/unit.json",
        readiness_report_path=f"bronze/{unit.unit_id}/readiness_report.json",
    )
    validate_benchmark_item(item=item, benchmark_root=benchmark_root)
    if item_id in existing:
        manifest.items = [entry if entry.item_id != item_id else item for entry in manifest.items]
    else:
        manifest.items.append(item)
    return item


def promote_units_to_bronze(
    *, units: list[TheoremProofUnit], manifest_path: Path, benchmark_root: Path | None = None, overwrite: bool = False
) -> list[BenchmarkItem]:
    root = benchmark_root or manifest_path.parent
    manifest = load_manifest(manifest_path)
    promoted = [
        promote_benchmark_item(unit=unit, manifest=manifest, benchmark_root=root, overwrite=overwrite)
        for unit in sorted(units, key=lambda unit: unit.unit_id)
    ]
    manifest_path.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    validate_manifest(manifest=manifest, benchmark_root=root)
    return promoted


def resolve_prediction_report_path(*, predictions_dir: Path, unit_id: str) -> Path:
    nested = predictions_dir / unit_id / PREDICTION_REPORT_FILENAME
    if nested.exists():
        return nested
    flat = predictions_dir / f"{unit_id}.json"
    if flat.exists():
        return flat
    raise BenchmarkValidationError(
        f"Missing prediction for unit_id={unit_id!r}. Expected {nested.as_posix()} or {flat.as_posix()}."
    )


def _round_metric(value: float) -> float:
    return round(value, 6)


def run_readinessbench(
    *, manifest_path: Path, predictions_dir: Path, benchmark_root: Path | None = None
) -> BenchmarkEvaluationReport:
    root = benchmark_root or manifest_path.parent
    manifest = load_manifest(manifest_path)
    validate_manifest(manifest=manifest, benchmark_root=root)
    item_scores: list[BenchmarkItemScore] = []
    for item in sorted(manifest.items, key=lambda entry: entry.item_id):
        if item.tier != BenchmarkTier.GOLD:
            continue
        gold_path = resolve_benchmark_path(
            benchmark_root=root,
            relative_path=item.readiness_report_path,
            context=f"gold item {item.item_id!r} readiness_report_path",
        )
        gold = load_readiness_report(gold_path)
        if gold.review_status not in TIER_ALLOWED_REVIEW_STATUSES[BenchmarkTier.GOLD]:
            raise BenchmarkValidationError(
                f"Refusing to treat non-reviewed report as gold for item {item.item_id!r}."
            )
        prediction_path = resolve_prediction_report_path(predictions_dir=predictions_dir, unit_id=item.unit_id)
        _reject_generated_artifact_path(path=prediction_path.resolve(), context="Prediction report")
        predicted = load_readiness_report(prediction_path)
        scores = score_readiness_report(predicted=predicted, gold=gold)
        item_scores.append(
            BenchmarkItemScore(
                item_id=item.item_id,
                unit_id=item.unit_id,
                macro_f1=_round_metric(scores.macro_f1),
                existing_theorem_candidates_f1=_round_metric(scores.existing_theorem_candidates.f1),
                constructive_path_f1=_round_metric(scores.constructive_path.f1),
                blockers_f1=_round_metric(scores.blockers.f1),
                notation_readiness_f1=_round_metric(scores.notation_readiness.f1),
            )
        )
    gold_item_count = sum(1 for item in manifest.items if item.tier == BenchmarkTier.GOLD)
    macro_f1_mean = _round_metric(sum(score.macro_f1 for score in item_scores) / len(item_scores))
    return BenchmarkEvaluationReport(
        benchmark_id=manifest.benchmark_id,
        gold_item_count=gold_item_count,
        scored_item_count=len(item_scores),
        items=item_scores,
        macro_f1_mean=macro_f1_mean,
    )


def resolve_prediction_artifact_path(*, predictions_dir: Path, unit_id: str, filename: str) -> Path:
    nested = predictions_dir / unit_id / filename
    if nested.exists():
        return nested
    stem = Path(filename).stem
    flat = predictions_dir / f"{unit_id}_{stem}.json"
    if flat.exists():
        return flat
    raise BenchmarkValidationError(
        f"Missing prediction artifact for unit_id={unit_id!r}. "
        f"Expected {nested.as_posix()} or {flat.as_posix()}."
    )


def _gold_example_dirs_by_unit_id(*, repo_root: Path) -> dict[str, Path]:
    manifest_path = repo_root / "benchmarks" / "baselines" / "manifest.json"
    if not manifest_path.is_file():
        return {}
    from fre_core.baseline_runner import load_baseline_manifest

    manifest = load_baseline_manifest(manifest_path)
    return {entry.unit_id: (repo_root / entry.example_dir).resolve() for entry in manifest.units}


def _item_full_macro_f1(
    *, readiness_macro_f1: float, proofgraph_macro_f1: float, atlas_f1: float, leantask_f1: float
) -> float:
    return (readiness_macro_f1 + proofgraph_macro_f1 + atlas_f1 + leantask_f1) / 4


def run_benchmark_evaluation(
    *,
    manifest_path: Path,
    predictions_dir: Path,
    benchmark_root: Path | None = None,
    repo_root: Path | None = None,
) -> BenchmarkEvaluationReport:
    root = benchmark_root or manifest_path.parent
    repo = repo_root or _repo_root_from_module()
    manifest = load_manifest(manifest_path)
    validate_manifest(manifest=manifest, benchmark_root=root)
    gold_dirs = _gold_example_dirs_by_unit_id(repo_root=repo)
    item_scores: list[BenchmarkItemScore] = []
    for item in sorted(manifest.items, key=lambda entry: entry.item_id):
        if item.tier != BenchmarkTier.GOLD:
            continue
        gold_dir = gold_dirs.get(item.unit_id)
        if gold_dir is None:
            raise BenchmarkValidationError(f"No reference gold directory found for unit_id={item.unit_id!r}.")
        gold_report = load_readiness_report(
            resolve_benchmark_path(
                benchmark_root=root,
                relative_path=item.readiness_report_path,
                context=f"gold item {item.item_id!r} readiness_report_path",
            )
        )
        predicted_report = load_readiness_report(
            resolve_prediction_report_path(predictions_dir=predictions_dir, unit_id=item.unit_id)
        )
        readiness_scores = score_readiness_report(predicted=predicted_report, gold=gold_report)
        graph_scores = score_proofgraph(
            predicted=load_proofgraph(
                resolve_prediction_artifact_path(
                    predictions_dir=predictions_dir, unit_id=item.unit_id, filename=PREDICTION_PROOFGRAPH_FILENAME
                )
            ),
            gold=load_proofgraph(gold_dir / PREDICTION_PROOFGRAPH_FILENAME),
        )
        atlas_score = score_atlas_record(
            predicted=load_atlas_record(
                resolve_prediction_artifact_path(
                    predictions_dir=predictions_dir, unit_id=item.unit_id, filename=PREDICTION_ATLAS_FILENAME
                )
            ),
            gold=load_atlas_record(gold_dir / PREDICTION_ATLAS_FILENAME),
        )
        leantask_score = score_leantask_package(
            predicted=load_leantask_package(
                resolve_prediction_artifact_path(
                    predictions_dir=predictions_dir, unit_id=item.unit_id, filename=PREDICTION_LEANTASK_FILENAME
                )
            ),
            gold=load_leantask_package(gold_dir / PREDICTION_LEANTASK_FILENAME),
        )
        full_macro_f1 = _round_metric(
            _item_full_macro_f1(
                readiness_macro_f1=readiness_scores.macro_f1,
                proofgraph_macro_f1=graph_scores.macro_f1,
                atlas_f1=atlas_score.f1,
                leantask_f1=leantask_score.f1,
            )
        )
        item_scores.append(
            BenchmarkItemScore(
                item_id=item.item_id,
                unit_id=item.unit_id,
                macro_f1=_round_metric(readiness_scores.macro_f1),
                existing_theorem_candidates_f1=_round_metric(readiness_scores.existing_theorem_candidates.f1),
                constructive_path_f1=_round_metric(readiness_scores.constructive_path.f1),
                blockers_f1=_round_metric(readiness_scores.blockers.f1),
                notation_readiness_f1=_round_metric(readiness_scores.notation_readiness.f1),
                proofgraph_f1=_round_metric(graph_scores.macro_f1),
                atlas_f1=_round_metric(atlas_score.f1),
                leantask_f1=_round_metric(leantask_score.f1),
                full_macro_f1=full_macro_f1,
            )
        )
    gold_item_count = sum(1 for item in manifest.items if item.tier == BenchmarkTier.GOLD)
    macro_f1_mean = _round_metric(sum(score.macro_f1 for score in item_scores) / len(item_scores))
    full_macro_f1_mean = _round_metric(
        sum(score.full_macro_f1 or 0.0 for score in item_scores) / len(item_scores)
    )
    return BenchmarkEvaluationReport(
        benchmark_id=manifest.benchmark_id,
        gold_item_count=gold_item_count,
        scored_item_count=len(item_scores),
        items=item_scores,
        macro_f1_mean=macro_f1_mean,
        full_macro_f1_mean=full_macro_f1_mean,
    )

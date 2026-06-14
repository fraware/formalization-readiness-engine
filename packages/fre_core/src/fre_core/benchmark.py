"""ReadinessBench manifest loading, tier validation, and evaluation runner."""

from __future__ import annotations

import json
from pathlib import Path

from fre_core.baseline_runner import default_baseline_manifest_path, load_baseline_manifest
from fre_core.corpus import load_corpus_catalog, resolve_source_path
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
    ReviewOrigin,
    ReviewStatus,
    TheoremProofUnit,
)
from fre_core.review_workflow import load_changelog_entries
from fre_core.validation import (
    load_atlas_record,
    load_leantask_package,
    load_proofgraph,
    load_readiness_report,
    load_unit,
)

TIER_ALLOWED_REVIEW_STATUSES: dict[BenchmarkTier, frozenset[ReviewStatus]] = {
    BenchmarkTier.BRONZE: frozenset({ReviewStatus.CANDIDATE, ReviewStatus.MACHINE_VALIDATED}),
    BenchmarkTier.SILVER: frozenset({ReviewStatus.HUMAN_REVIEWED}),
    BenchmarkTier.GOLD: frozenset({ReviewStatus.HUMAN_REVIEWED, ReviewStatus.EXPERT_REVIEWED}),
}

GENERATED_ARTIFACT_SEGMENT = "artifacts/generated"
REVIEW_SUBMISSION_TEMPLATE_PATH = "docs/review/templates/readiness_report_review.json"
GOLD_CHANGELOG_RELATIVE = "gold/changelog.jsonl"
PREDICTION_REPORT_FILENAME = "readiness_report.json"
PREDICTION_REPORT_MODEL_FILENAME = "readiness_report.model.json"
PREDICTION_PROOFGRAPH_FILENAME = "proofgraph.json"
PREDICTION_PROOFGRAPH_MODEL_FILENAME = "proofgraph.model.json"
PREDICTION_ATLAS_FILENAME = "atlas_record.json"
PREDICTION_ATLAS_MODEL_FILENAME = "atlas_record.model.json"
PREDICTION_LEANTASK_FILENAME = "leantask.json"
PREDICTION_LEANTASK_MODEL_FILENAME = "leantask.model.json"
PREDICTION_SUBDIR_SKIP = frozenset({".predictions", "public_exports"})


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


def _repo_root_from_benchmark(benchmark_root: Path) -> Path:
    return benchmark_root.parent.parent


def _resolve_unit_source_text(*, unit: TheoremProofUnit, repo_root: Path) -> str | None:
    catalog_path = repo_root / "corpus" / "catalog.json"
    if not catalog_path.is_file():
        return None
    catalog = load_corpus_catalog(catalog_path)
    source = catalog.by_source_id().get(unit.source_id)
    if source is None:
        return None
    source_path = resolve_source_path(source=source, repo_root=repo_root)
    if not source_path.is_file():
        return None
    return source_path.read_text(encoding="utf-8")


def _load_gold_changelog_entries(*, benchmark_root: Path) -> list:
    changelog_path = benchmark_root / GOLD_CHANGELOG_RELATIVE
    if not changelog_path.is_file():
        return []
    return load_changelog_entries(changelog_path)


def _changelog_entries_for_item(*, item_id: str, entries: list) -> list:
    return [entry for entry in entries if entry.item_id == item_id]


def _is_template_review_submission_path(path: str) -> bool:
    normalized = path.replace("\\", "/").strip()
    return normalized == REVIEW_SUBMISSION_TEMPLATE_PATH


def validate_gold_review_origin(
    *,
    item: BenchmarkItem,
    report: ReadinessReport,
    benchmark_root: Path,
    repo_root: Path,
) -> None:
    if item.tier != BenchmarkTier.GOLD:
        return

    review_origin = report.review_origin or item.review_origin
    if review_origin is None:
        raise BenchmarkValidationError(
            f"item {item.item_id!r} gold readiness report must declare review_origin."
        )

    changelog_entries = _load_gold_changelog_entries(benchmark_root=benchmark_root)
    item_entries = _changelog_entries_for_item(item_id=item.item_id, entries=changelog_entries)
    if not item_entries:
        raise BenchmarkValidationError(
            f"item {item.item_id!r} gold tier requires a matching entry in {GOLD_CHANGELOG_RELATIVE}."
        )

    if review_origin == ReviewOrigin.EXTERNAL_EXPERT:
        submission_paths = [
            entry.review_submission_path
            for entry in item_entries
            if entry.review_submission_path
        ]
        if not submission_paths:
            raise BenchmarkValidationError(
                f"item {item.item_id!r} with review_origin='external_expert' "
                f"requires review_submission_path in {GOLD_CHANGELOG_RELATIVE}."
            )
        valid_paths = [
            path
            for path in submission_paths
            if not _is_template_review_submission_path(path)
            and (repo_root / path).is_file()
        ]
        if not valid_paths:
            raise BenchmarkValidationError(
                f"item {item.item_id!r} with review_origin='external_expert' "
                f"requires a persisted review submission on disk (not the template placeholder)."
            )


def validate_benchmark_item(
    *,
    item: BenchmarkItem,
    benchmark_root: Path,
    repo_root: Path | None = None,
) -> ReadinessReport:
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
    resolved_repo_root = repo_root or _repo_root_from_benchmark(benchmark_root)
    unit_payload = unit_path.read_text(encoding="utf-8")
    unit_model = TheoremProofUnit.model_validate_json(unit_payload)
    source_text = _resolve_unit_source_text(unit=unit_model, repo_root=resolved_repo_root)
    unit = load_unit(unit_path, source_text=source_text)
    validation_mode = "public_export" if item.tier in {BenchmarkTier.GOLD, BenchmarkTier.SILVER} else None
    report = load_readiness_report(report_path, mode=validation_mode)
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
    validate_gold_review_origin(
        item=item,
        report=report,
        benchmark_root=benchmark_root,
        repo_root=resolved_repo_root,
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


def _read_json_unit_id(path: Path) -> str | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    unit_id = payload.get("unit_id")
    return unit_id if isinstance(unit_id, str) and unit_id else None


def _prediction_subdirs(predictions_dir: Path) -> list[Path]:
    if not predictions_dir.is_dir():
        return []
    return sorted(
        subdir
        for subdir in predictions_dir.iterdir()
        if subdir.is_dir() and subdir.name not in PREDICTION_SUBDIR_SKIP and not subdir.name.startswith(".")
    )


def _iter_prediction_report_candidates(*, predictions_dir: Path, unit_id: str) -> list[Path]:
    candidates: list[Path] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            candidates.append(path)

    add(predictions_dir / unit_id / PREDICTION_REPORT_FILENAME)
    add(predictions_dir / f"{unit_id}.json")
    for subdir in _prediction_subdirs(predictions_dir):
        add(subdir / PREDICTION_REPORT_FILENAME)
        add(subdir / PREDICTION_REPORT_MODEL_FILENAME)
    return candidates


def _artifact_filename_variants(filename: str) -> tuple[str, ...]:
    stem = Path(filename).stem
    if filename.endswith(".model.json"):
        return (filename,)
    return (filename, f"{stem}.model.json")


def _iter_prediction_artifact_candidates(
    *, predictions_dir: Path, unit_id: str, filename: str
) -> list[Path]:
    candidates: list[Path] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            candidates.append(path)

    for variant in _artifact_filename_variants(filename):
        add(predictions_dir / unit_id / variant)
    flat_stem = Path(filename).stem.replace(".model", "")
    add(predictions_dir / f"{unit_id}_{flat_stem}.json")
    for subdir in _prediction_subdirs(predictions_dir):
        for variant in _artifact_filename_variants(filename):
            add(subdir / variant)
    return candidates


def resolve_prediction_report_path(*, predictions_dir: Path, unit_id: str) -> Path:
    path = find_prediction_report_path(predictions_dir=predictions_dir, unit_id=unit_id)
    if path is not None:
        return path
    searched = [
        candidate.as_posix()
        for candidate in _iter_prediction_report_candidates(predictions_dir=predictions_dir, unit_id=unit_id)
    ]
    raise BenchmarkValidationError(
        f"Missing prediction for unit_id={unit_id!r}. Searched: {', '.join(searched)}."
    )


def find_prediction_report_path(*, predictions_dir: Path, unit_id: str) -> Path | None:
    for path in _iter_prediction_report_candidates(predictions_dir=predictions_dir, unit_id=unit_id):
        if not path.is_file():
            continue
        if path.parent.name == unit_id and path.name == PREDICTION_REPORT_FILENAME:
            return path
        if path.name == f"{unit_id}.json":
            return path
        if _read_json_unit_id(path) == unit_id:
            return path
    return None


def resolve_prediction_artifact_path(
    *, predictions_dir: Path, unit_id: str, filename: str
) -> Path | None:
    """Resolve an optional predicted artifact path for one unit."""
    for path in _iter_prediction_artifact_candidates(
        predictions_dir=predictions_dir,
        unit_id=unit_id,
        filename=filename,
    ):
        if not path.is_file():
            continue
        if path.parent.name == unit_id and path.name == filename:
            return path
        if path.name == f"{unit_id}_{Path(filename).stem}.json":
            return path
        if _read_json_unit_id(path) == unit_id:
            return path
    return None


def _gold_example_dir_for_unit(*, unit_id: str, repo_root: Path) -> Path | None:
    manifest_path = default_baseline_manifest_path(repo_root=repo_root)
    if not manifest_path.exists():
        return None
    manifest = load_baseline_manifest(manifest_path)
    for entry in manifest.units:
        if entry.unit_id == unit_id:
            candidate = (repo_root / entry.example_dir).resolve()
            if candidate.is_dir():
                return candidate
    return None


def _gold_benchmark_dir_for_unit(*, unit_id: str, benchmark_root: Path) -> Path | None:
    candidate = benchmark_root / "gold" / unit_id
    if candidate.is_dir():
        return candidate
    return None


def _score_optional_artifacts(
    *,
    unit_id: str,
    predictions_dir: Path,
    repo_root: Path,
    benchmark_root: Path | None = None,
) -> dict[str, float | None]:
    scores: dict[str, float | None] = {
        "proofgraph_f1": None,
        "atlas_f1": None,
        "leantask_f1": None,
    }
    bench_root = benchmark_root or default_benchmark_root(repo_root=repo_root)
    example_dir = _gold_example_dir_for_unit(unit_id=unit_id, repo_root=repo_root)
    benchmark_gold_dir = _gold_benchmark_dir_for_unit(unit_id=unit_id, benchmark_root=bench_root)

    def _resolve_gold_artifact(filename: str) -> Path | None:
        if benchmark_gold_dir is not None:
            candidate = benchmark_gold_dir / filename
            if candidate.is_file():
                return candidate
        if example_dir is not None:
            candidate = example_dir / filename
            if candidate.is_file():
                return candidate
        return None

    predicted_graph = resolve_prediction_artifact_path(
        predictions_dir=predictions_dir,
        unit_id=unit_id,
        filename=PREDICTION_PROOFGRAPH_FILENAME,
    )
    gold_graph = _resolve_gold_artifact(PREDICTION_PROOFGRAPH_FILENAME)
    if predicted_graph is not None and gold_graph is not None:
        graph_scores = score_proofgraph(
            predicted=load_proofgraph(predicted_graph),
            gold=load_proofgraph(gold_graph),
        )
        scores["proofgraph_f1"] = _round_metric(graph_scores.macro_f1)

    predicted_atlas = resolve_prediction_artifact_path(
        predictions_dir=predictions_dir,
        unit_id=unit_id,
        filename=PREDICTION_ATLAS_FILENAME,
    )
    gold_atlas = _resolve_gold_artifact(PREDICTION_ATLAS_FILENAME)
    if predicted_atlas is not None and gold_atlas is not None:
        atlas_scores = score_atlas_record(
            predicted=load_atlas_record(predicted_atlas),
            gold=load_atlas_record(gold_atlas),
        )
        scores["atlas_f1"] = _round_metric(atlas_scores.f1)

    predicted_leantask = resolve_prediction_artifact_path(
        predictions_dir=predictions_dir,
        unit_id=unit_id,
        filename=PREDICTION_LEANTASK_FILENAME,
    )
    gold_leantask = _resolve_gold_artifact(PREDICTION_LEANTASK_FILENAME)
    if predicted_leantask is not None and gold_leantask is not None:
        leantask_scores = score_leantask_package(
            predicted=load_leantask_package(predicted_leantask),
            gold=load_leantask_package(gold_leantask),
        )
        scores["leantask_f1"] = _round_metric(leantask_scores.f1)

    return scores


def _full_macro_f1(
    *,
    readiness_macro_f1: float,
    proofgraph_f1: float | None,
    atlas_f1: float | None,
    leantask_f1: float | None,
) -> float | None:
    components = [readiness_macro_f1, proofgraph_f1, atlas_f1, leantask_f1]
    present = [value for value in components if value is not None]
    if len(present) <= 1:
        return None
    return _round_metric(sum(present) / len(present))


def _round_metric(value: float) -> float:
    return round(value, 6)


def run_readinessbench(
    *,
    manifest_path: Path,
    predictions_dir: Path,
    benchmark_root: Path | None = None,
    repo_root: Path | None = None,
) -> BenchmarkEvaluationReport:
    root = benchmark_root or manifest_path.parent
    resolved_repo_root = repo_root or _repo_root_from_module()
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
        prediction_path = find_prediction_report_path(predictions_dir=predictions_dir, unit_id=item.unit_id)
        if prediction_path is None:
            continue
        predicted = load_readiness_report(prediction_path)
        scores = score_readiness_report(predicted=predicted, gold=gold)
        optional_scores = _score_optional_artifacts(
            unit_id=item.unit_id,
            predictions_dir=predictions_dir,
            repo_root=resolved_repo_root,
            benchmark_root=root,
        )
        readiness_macro_f1 = _round_metric(scores.macro_f1)
        full_macro_f1 = _full_macro_f1(
            readiness_macro_f1=readiness_macro_f1,
            proofgraph_f1=optional_scores["proofgraph_f1"],
            atlas_f1=optional_scores["atlas_f1"],
            leantask_f1=optional_scores["leantask_f1"],
        )
        try:
            prediction_report_path = prediction_path.resolve().relative_to(resolved_repo_root.resolve()).as_posix()
        except ValueError:
            prediction_report_path = prediction_path.resolve().as_posix()
        item_scores.append(
            BenchmarkItemScore(
                item_id=item.item_id,
                unit_id=item.unit_id,
                prediction_report_path=prediction_report_path,
                macro_f1=readiness_macro_f1,
                existing_theorem_candidates_f1=_round_metric(scores.existing_theorem_candidates.f1),
                constructive_path_f1=_round_metric(scores.constructive_path.f1),
                blockers_f1=_round_metric(scores.blockers.f1),
                notation_readiness_f1=_round_metric(scores.notation_readiness.f1),
                proofgraph_f1=optional_scores["proofgraph_f1"],
                atlas_f1=optional_scores["atlas_f1"],
                leantask_f1=optional_scores["leantask_f1"],
                full_macro_f1=full_macro_f1,
            )
        )
    gold_item_count = sum(1 for item in manifest.items if item.tier == BenchmarkTier.GOLD)
    if not item_scores:
        raise BenchmarkValidationError(
            f"No predictions found under {predictions_dir.as_posix()} for any of "
            f"{gold_item_count} gold ReadinessBench items."
        )
    macro_f1_mean = _round_metric(sum(score.macro_f1 for score in item_scores) / len(item_scores))
    full_values = [score.full_macro_f1 for score in item_scores if score.full_macro_f1 is not None]
    full_macro_f1_mean = (
        _round_metric(sum(full_values) / len(full_values)) if full_values else None
    )

    return BenchmarkEvaluationReport(
        benchmark_id=manifest.benchmark_id,
        gold_item_count=gold_item_count,
        scored_item_count=len(item_scores),
        items=item_scores,
        macro_f1_mean=macro_f1_mean,
        full_macro_f1_mean=full_macro_f1_mean,
    )


def run_benchmark_evaluation(
    *,
    manifest_path: Path,
    predictions_dir: Path,
    benchmark_root: Path | None = None,
    repo_root: Path | None = None,
) -> BenchmarkEvaluationReport:
    """Score all artifact types where gold references exist."""
    return run_readinessbench(
        manifest_path=manifest_path,
        predictions_dir=predictions_dir,
        benchmark_root=benchmark_root,
        repo_root=repo_root,
    )

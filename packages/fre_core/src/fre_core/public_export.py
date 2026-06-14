"""Public JSONL export for ReadinessBench and the Formalization Gap Atlas."""

from __future__ import annotations

import json
from pathlib import Path

from fre_core.benchmark import (
    default_manifest_path,
    load_manifest,
    resolve_benchmark_path,
)
from fre_core.corpus import CorpusCatalog, load_corpus_catalog, make_shareable_units
from fre_core.schemas import (
    PublicAtlasExportRecord,
    PublicBenchmarkExportRecord,
    PublicExportManifest,
    TheoremProofUnit,
)
from fre_core.validation import load_atlas_record, load_readiness_report, load_unit


class PublicExportError(ValueError):
    """Raised when a public export violates release or schema constraints."""


class LicensingLeakError(PublicExportError):
    """Raised when restricted source text appears in a public export."""


def _repo_root_from_module() -> Path:
    return Path(__file__).resolve().parents[4]


def default_public_exports_dir(*, repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root_from_module()
    return root / "public_exports"


def _write_jsonl(*, records: list[object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record.model_dump(mode="json"), sort_keys=True) for record in records]
    output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _shareable_unit(
    *,
    unit: TheoremProofUnit,
    catalog: CorpusCatalog | None,
) -> TheoremProofUnit:
    if catalog is None:
        return unit
    shared = make_shareable_units(units=[unit], catalog=catalog, include_text=False)
    if not shared:
        raise PublicExportError(
            f"Unit {unit.unit_id!r} with source_id={unit.source_id!r} is not shareable under catalog release modes."
        )
    return shared[0]


def export_public_benchmark(
    *,
    output_path: Path | None = None,
    manifest_path: Path | None = None,
    benchmark_root: Path | None = None,
    catalog_path: Path | None = None,
    repo_root: Path | None = None,
) -> PublicExportManifest:
    """Export ReadinessBench gold, silver, and bronze items as public JSONL."""
    root = repo_root or _repo_root_from_module()
    manifest_file = manifest_path or default_manifest_path(repo_root=root)
    bench_root = benchmark_root or manifest_file.parent
    target = output_path or (default_public_exports_dir(repo_root=root) / "readinessbench.jsonl")

    manifest = load_manifest(manifest_file)
    catalog = load_corpus_catalog(catalog_path) if catalog_path is not None else None

    records: list[PublicBenchmarkExportRecord] = []
    for item in sorted(manifest.items, key=lambda entry: (entry.tier.value, entry.item_id)):
        unit_path = resolve_benchmark_path(
            benchmark_root=bench_root,
            relative_path=item.unit_path,
            context=f"export item {item.item_id!r} unit_path",
        )
        report_path = resolve_benchmark_path(
            benchmark_root=bench_root,
            relative_path=item.readiness_report_path,
            context=f"export item {item.item_id!r} readiness_report_path",
        )
        unit = _shareable_unit(unit=load_unit(unit_path), catalog=catalog)
        export_mode = "public_export" if item.tier.value in {"gold", "silver"} else "permissive"
        report = load_readiness_report(report_path, mode=export_mode)
        review_origin = report.review_origin
        records.append(
            PublicBenchmarkExportRecord(
                item_id=item.item_id,
                unit_id=item.unit_id,
                tier=item.tier.value,
                unit=unit,
                readiness_report=report,
                review_origin=review_origin,
            )
        )

    _write_jsonl(records=records, output_path=target)
    return PublicExportManifest(
        export_id="readinessbench_public_v0",
        export_type="readinessbench",
        record_count=len(records),
        output_path=target.as_posix(),
        description="Public ReadinessBench export with corpus release-mode filtering on unit text.",
    )


def _example_dirs(*, repo_root: Path) -> list[Path]:
    examples_root = repo_root / "examples"
    names = ("finite_tree", "category_theory_pullback")
    return [examples_root / name for name in names if (examples_root / name).is_dir()]


def export_public_atlas(
    *,
    output_path: Path | None = None,
    manifest_path: Path | None = None,
    benchmark_root: Path | None = None,
    catalog_path: Path | None = None,
    repo_root: Path | None = None,
    example_dirs: list[Path] | None = None,
) -> PublicExportManifest:
    """Export curated Atlas records from examples and reviewed benchmark items."""
    root = repo_root or _repo_root_from_module()
    target = output_path or (default_public_exports_dir(repo_root=root) / "atlas.jsonl")
    catalog = load_corpus_catalog(catalog_path) if catalog_path is not None else None

    records: list[PublicAtlasExportRecord] = []
    seen_unit_ids: set[str] = set()

    for example_dir in example_dirs or _example_dirs(repo_root=root):
        atlas_path = example_dir / "atlas_record.json"
        unit_path = example_dir / "unit.json"
        if not atlas_path.exists():
            continue
        atlas = load_atlas_record(atlas_path)
        unit = load_unit(unit_path) if unit_path.exists() else None
        shareable = _shareable_unit(unit=unit, catalog=catalog) if unit is not None else None
        if atlas.unit_id in seen_unit_ids:
            continue
        seen_unit_ids.add(atlas.unit_id)
        records.append(
            PublicAtlasExportRecord(
                unit_id=atlas.unit_id,
                source_id=shareable.source_id if shareable is not None else None,
                domain=shareable.domain if shareable is not None else None,
                atlas_record=atlas,
                unit=shareable,
            )
        )

    manifest_file = manifest_path or default_manifest_path(repo_root=root)
    if manifest_file.exists():
        bench_root = benchmark_root or manifest_file.parent
        manifest = load_manifest(manifest_file)
        for item in sorted(manifest.items, key=lambda entry: entry.item_id):
            if item.tier.value != "gold":
                continue
            unit_path = resolve_benchmark_path(
                benchmark_root=bench_root,
                relative_path=item.unit_path,
                context=f"atlas export item {item.item_id!r} unit_path",
            )
            atlas_candidate = bench_root / item.tier.value / item.unit_id / "atlas_record.json"
            if not atlas_candidate.exists():
                continue
            atlas = load_atlas_record(atlas_candidate)
            if atlas.unit_id in seen_unit_ids:
                continue
            seen_unit_ids.add(atlas.unit_id)
            unit = _shareable_unit(unit=load_unit(unit_path), catalog=catalog)
            records.append(
                PublicAtlasExportRecord(
                    unit_id=atlas.unit_id,
                    source_id=unit.source_id,
                    domain=unit.domain,
                    atlas_record=atlas,
                    unit=unit,
                )
            )

    records.sort(key=lambda record: record.unit_id)
    _write_jsonl(records=records, output_path=target)
    return PublicExportManifest(
        export_id="atlas_public_v0",
        export_type="atlas",
        record_count=len(records),
        output_path=target.as_posix(),
        description="Curated Formalization Gap Atlas export from examples and reviewed benchmark items.",
    )


def _restricted_source_ids(catalog: CorpusCatalog) -> set[str]:
    return {source.source_id for source in catalog.sources if source.release_mode == "metadata_only"}


def _collect_text_fields(payload: object) -> list[str]:
    texts: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in {"statement", "proof"} and isinstance(value, str) and value.strip():
                texts.append(value)
            texts.extend(_collect_text_fields(value))
    elif isinstance(payload, list):
        for item in payload:
            texts.extend(_collect_text_fields(item))
    return texts


def assert_no_licensing_leak(
    *,
    jsonl_path: Path,
    catalog: CorpusCatalog,
    restricted_units: list[TheoremProofUnit] | None = None,
) -> None:
    """Fail when metadata-only source text appears in a public export."""
    restricted_ids = _restricted_source_ids(catalog)
    if not restricted_ids:
        return

    forbidden_fragments: list[str] = []
    if restricted_units is not None:
        for unit in restricted_units:
            if unit.source_id not in restricted_ids:
                continue
            if unit.statement.strip():
                forbidden_fragments.append(unit.statement.strip())
            if unit.proof and unit.proof.strip():
                forbidden_fragments.append(unit.proof.strip())

    for line_number, line in enumerate(jsonl_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)

        source_id = payload.get("source_id")
        unit_payload = payload.get("unit")
        if isinstance(unit_payload, dict):
            source_id = unit_payload.get("source_id", source_id)

        if source_id in restricted_ids:
            for text in _collect_text_fields(payload):
                raise LicensingLeakError(
                    f"Licensing leak at line {line_number}: metadata-only source {source_id!r} "
                    f"contains restricted text: {text[:80]!r}..."
                )

        for fragment in forbidden_fragments:
            if fragment and fragment in line:
                raise LicensingLeakError(
                    f"Licensing leak at line {line_number}: found restricted fragment from "
                    f"metadata-only source: {fragment[:80]!r}..."
                )


def write_export_manifest(*, manifest: PublicExportManifest, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return output_path

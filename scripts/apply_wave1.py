#!/usr/bin/env python3
"""One-shot Wave 1 corpus patcher. Run from repo root on engineering/wave1-corpus."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "fre_core" / "src"))


def write(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print("wrote", rel)


def patch_schemas(text: str) -> str:
    old = """class SourceDocument(BaseModel):
    source_id: str
    source_type: str
    license_status: str
    release_mode: str
    domain: str
    path: str


class SourceSpan(BaseModel):"""
    new = """class SourceDocument(BaseModel):
    source_id: str
    source_type: str
    license_status: str
    release_mode: str
    domain: str
    path: str
    curator: str | None = None
    permission_reference: str | None = None


class RepairedUnitSpan(BaseModel):
    statement: str
    proof: str | None = None
    statement_span: SourceSpan
    proof_span: SourceSpan | None = None


class SegmentationRepairResult(BaseModel):
    units: list[RepairedUnitSpan] = Field(default_factory=list)


class SourceSpan(BaseModel):"""
    if old not in text:
        raise RuntimeError("schemas.py anchor missing")
    return text.replace(old, new)


def patch_benchmark(text: str) -> str:
    text = text.replace(
        "    ReadinessReport,\n    ReviewStatus,\n)",
        "    ReadinessDimension,\n    ReadinessReport,\n    ReviewStatus,\n    TheoremProofUnit,\n)",
    )
    anchor = "    return gold_reports\n\n\ndef resolve_prediction_report_path"
    insert = '''    return gold_reports


def create_bronze_readiness_placeholder(unit: TheoremProofUnit) -> ReadinessReport:
    pending = ReadinessDimension(
        status="pending", recovered=[], unresolved=["awaiting extraction pass"],
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


def promote_benchmark_item(*, unit: TheoremProofUnit, manifest: BenchmarkManifest, benchmark_root: Path, overwrite: bool = False) -> BenchmarkItem:
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
    unit_path.write_text(bronze_unit.model_dump_json(indent=2) + "\\n", encoding="utf-8")
    report_path.write_text(report.model_dump_json(indent=2) + "\\n", encoding="utf-8")
    item = BenchmarkItem(
        item_id=item_id, unit_id=unit.unit_id, tier=BenchmarkTier.BRONZE,
        unit_path=f"bronze/{unit.unit_id}/unit.json",
        readiness_report_path=f"bronze/{unit.unit_id}/readiness_report.json",
    )
    validate_benchmark_item(item=item, benchmark_root=benchmark_root)
    if item_id in existing:
        manifest.items = [entry if entry.item_id != item_id else item for entry in manifest.items]
    else:
        manifest.items.append(item)
    return item


def promote_units_to_bronze(*, units: list[TheoremProofUnit], manifest_path: Path, benchmark_root: Path | None = None, overwrite: bool = False) -> list[BenchmarkItem]:
    root = benchmark_root or manifest_path.parent
    manifest = load_manifest(manifest_path)
    promoted = [promote_benchmark_item(unit=unit, manifest=manifest, benchmark_root=root, overwrite=overwrite) for unit in sorted(units, key=lambda u: u.unit_id)]
    manifest_path.write_text(manifest.model_dump_json(indent=2) + "\\n", encoding="utf-8")
    validate_manifest(manifest=manifest, benchmark_root=root)
    return promoted


def resolve_prediction_report_path'''
    if anchor not in text:
        raise RuntimeError("benchmark.py anchor missing")
    return text.replace(anchor, insert)


def patch_cli(text: str) -> str:
    text = text.replace(
        "    load_units_from_dir,\n    write_units,\n)",
        "    load_units_from_dir,\n    validate_corpus_catalog,\n    write_units,\n)",
    )
    text = text.replace(
        "    load_manifest,\n    run_readinessbench,\n    validate_manifest,\n)",
        "    load_manifest,\n    promote_benchmark_item,\n    promote_units_to_bronze,\n    run_readinessbench,\n    validate_manifest,\n)",
    )
    old = '@app.command("ingest-catalog")'
    new = '''@app.command("validate-corpus-catalog")
def validate_corpus_catalog_cmd(
    catalog_path: Path = typer.Argument(..., help="Path to corpus catalog JSON"),
    repo_root: Path = typer.Option(Path("."), help="Repository root for source paths"),
) -> None:
    catalog = load_corpus_catalog(catalog_path)
    validate_corpus_catalog(catalog=catalog, repo_root=repo_root)
    release_modes = sorted({source.release_mode for source in catalog.sources})
    print(f"[green]valid corpus catalog[/green] {len(catalog.sources)} sources (release_modes: {', '.join(release_modes)})")


@app.command("ingest-catalog")'''
    if old not in text:
        raise RuntimeError("cli ingest anchor missing")
    text = text.replace(old, new)
    text = text.replace(
        "    repo_root: Path = typer.Option(Path(\".\"), help=\"Repository root for source paths\"),\n) -> None:\n    \"\"\"Ingest catalog sources into theorem/proof unit JSON files.\"\"\"\n    catalog = load_corpus_catalog(catalog_path)\n    units = ingest_catalog(catalog=catalog, repo_root=repo_root)",
        "    repo_root: Path = typer.Option(Path(\".\"), help=\"Repository root for source paths\"),\n    repair: bool = typer.Option(False, help=\"Repair segmentation with a structured model when parsing fails.\"),\n) -> None:\n    \"\"\"Ingest catalog sources into theorem/proof unit JSON files.\"\"\"\n    catalog = load_corpus_catalog(catalog_path)\n    model_client = OpenAIResponsesProvider() if repair else None\n    units = ingest_catalog(catalog=catalog, repo_root=repo_root, repair=repair, model_client=model_client)",
    )
    old2 = '@app.command("validate-readinessbench")'
    new2 = '''@app.command("promote-benchmark-item")
def promote_benchmark_item_cmd(
    unit_path: Path = typer.Argument(..., help="Path to an ingested unit JSON file"),
    manifest_path: Path = typer.Option(default_manifest_path(), help="ReadinessBench manifest path."),
    benchmark_root: Path | None = typer.Option(None, help="Benchmark root (defaults to manifest parent)."),
    overwrite: bool = typer.Option(False, help="Replace an existing bronze item for the same unit."),
) -> None:
    root = benchmark_root or manifest_path.parent
    unit = load_unit(unit_path)
    manifest = load_manifest(manifest_path)
    item = promote_benchmark_item(unit=unit, manifest=manifest, benchmark_root=root, overwrite=overwrite)
    manifest_path.write_text(manifest.model_dump_json(indent=2) + "\\n", encoding="utf-8")
    print(f"[green]promoted bronze item[/green] {item.item_id} -> {item.unit_path}")


@app.command("promote-benchmark-units")
def promote_benchmark_units_cmd(
    units_dir: Path = typer.Argument(..., help="Directory containing ingested unit JSON files"),
    manifest_path: Path = typer.Option(default_manifest_path(), help="ReadinessBench manifest path."),
    benchmark_root: Path | None = typer.Option(None, help="Benchmark root (defaults to manifest parent)."),
    overwrite: bool = typer.Option(False, help="Replace existing bronze items for the same units."),
) -> None:
    root = benchmark_root or manifest_path.parent
    units = load_units_from_dir(units_dir)
    promoted = promote_units_to_bronze(units=units, manifest_path=manifest_path, benchmark_root=root, overwrite=overwrite)
    print(f"[green]promoted bronze items[/green] {len(promoted)}")


@app.command("validate-readinessbench")'''
    if old2 not in text:
        raise RuntimeError("cli validate anchor missing")
    return text.replace(old2, new2)


def main() -> int:
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    if branch != "engineering/wave1-corpus":
        print("ERROR: must be on engineering/wave1-corpus, got", branch)
        return 1

    base = "51406ce"
    for rel in [
        "packages/fre_core/src/fre_core/schemas.py",
        "packages/fre_core/src/fre_core/benchmark.py",
        "packages/fre_core/src/fre_core/cli.py",
    ]:
        content = subprocess.check_output(["git", "show", f"{base}:{rel}"], cwd=ROOT, text=True)
        if rel.endswith("schemas.py"):
            content = patch_schemas(content)
        elif rel.endswith("benchmark.py"):
            content = patch_benchmark(content)
        elif rel.endswith("cli.py"):
            content = patch_cli(content)
        write(rel, content)

    for rel in [
        "packages/fre_core/src/fre_core/corpus.py",
        "packages/fre_core/src/fre_core/latex_ingestion.py",
        "packages/fre_core/src/fre_core/segmentation_repair.py",
    ]:
        write(rel, (ROOT / rel).read_text(encoding="utf-8"))

    env = {**dict(**subprocess.os.environ), "PYTHONPATH": f"packages/fre_core/src{subprocess.os.pathsep}."}
    for cmd in [
        [sys.executable, "-m", "fre_core.cli", "validate-corpus-catalog", "corpus/catalog.json", "--repo-root", "."],
        [sys.executable, "-m", "fre_core.cli", "ingest-catalog", "corpus/catalog.json", "corpus/units/", "--repo-root", "."],
        [sys.executable, "-m", "fre_core.cli", "promote-benchmark-units", "corpus/units/"],
        [sys.executable, "-m", "pytest", "-q", "tests/test_corpus_governance.py", "tests/test_corpus_ingestion.py", "tests/test_latex_ingestion.py", "tests/test_segmentation_repair.py", "tests/test_benchmark.py"],
    ]:
        print("RUN", " ".join(cmd))
        r = subprocess.run(cmd, cwd=ROOT, env=env)
        if r.returncode:
            return r.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

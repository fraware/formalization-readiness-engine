"""Command-line entry points for the Formalization Readiness Engine."""

from __future__ import annotations

from pathlib import Path

import json

import typer
from rich import print

from fre_core.corpus import (
    export_shareable_units,
    ingest_catalog,
    load_corpus_catalog,
    load_units_from_dir,
    validate_corpus_catalog,
    validate_corpus_unit_spans,
    write_units,
)
from fre_core.extract_atlas import extract_atlas_record
from fre_core.extract_leantask import extract_leantask_package
from fre_core.extract_proofgraph import extract_proofgraph
from fre_core.evaluation_taxonomy import aggregate_error_summaries, categorize_baseline_run
from fre_core.extraction import extract_readiness_report
from fre_core.latex_ingestion import ingest_latex_file
from fre_core.lean_runner import check_lean_file
from fre_core.leantask_renderer import write_leantask
from fre_core.mathlib_alignment import (
    align_readiness_report,
    enrich_readiness_candidates_from_alignment,
)
from fre_core.mathlib_index import (
    build_search_query_from_report,
    build_search_query_from_unit,
    default_index_path,
    enrich_readiness_candidates,
    load_index,
    search,
)
from fre_core.atlas_generator import generate_atlas_cluster_report, write_atlas_cluster_report
from fre_core.release_manifest import (
    build_release_manifest,
    verify_release_manifest,
    write_release_manifest,
)
from fre_core.public_export import (
    assert_no_licensing_leak,
    default_public_exports_dir,
    export_public_atlas,
    export_public_benchmark,
    write_export_manifest,
)
from fre_core.baseline_runner import BaselineCondition, resolve_baseline_conditions, run_baselines
from fre_core.benchmark import (
    default_manifest_path,
    load_manifest,
    promote_benchmark_item,
    promote_units_to_bronze,
    run_benchmark_evaluation,
    run_readinessbench,
    validate_manifest,
)
from fre_core.openai_responses_provider import OpenAIResponsesProvider
from fre_core.schema_exports import export_json_schemas
from fre_core.schemas import LeanTaskLevel
from fre_core.review_workflow import (
    load_changelog_entries,
    load_review_submission,
    validate_changelog_entries,
    validate_review_submission,
)
from fre_core.validation import (
    load_atlas_record,
    load_leantask_package,
    load_proofgraph,
    load_readiness_report,
    load_unit,
)

app = typer.Typer(help="Formalization Readiness Engine CLI")


@app.command()
def validate_unit(path: Path) -> None:
    """Validate a theorem/proof unit JSON file."""
    unit = load_unit(path)
    print(f"[green]valid unit[/green] {unit.unit_id}")


@app.command()
def validate_report(path: Path) -> None:
    """Validate a readiness report JSON file."""
    report = load_readiness_report(path)
    print(f"[green]valid readiness report[/green] {report.unit_id}")


@app.command()
def validate_proofgraph(path: Path) -> None:
    """Validate a proof graph JSON file."""
    graph = load_proofgraph(path)
    print(f"[green]valid proof graph[/green] {graph.unit_id}")


@app.command()
def validate_atlas(path: Path) -> None:
    """Validate an Atlas record JSON file."""
    record = load_atlas_record(path)
    print(f"[green]valid Atlas record[/green] {record.unit_id}")


@app.command()
def validate_leantask(path: Path) -> None:
    """Validate a LeanTask package JSON file."""
    task = load_leantask_package(path)
    print(f"[green]valid LeanTask package[/green] {task.leantask_id}")


@app.command()
def validate_example_dir(path: Path) -> None:
    """Validate the standard files in an example artifact directory."""
    unit = load_unit(path / "unit.json")
    report = load_readiness_report(path / "readiness_report.json")
    graph = load_proofgraph(path / "proofgraph.json")
    record = load_atlas_record(path / "atlas_record.json")
    task = load_leantask_package(path / "leantask.json")

    unit_ids = {unit.unit_id, report.unit_id, graph.unit_id, record.unit_id, task.unit_id}
    if len(unit_ids) != 1:
        raise typer.BadParameter(f"Example directory has inconsistent unit ids: {sorted(unit_ids)}")

    print(f"[green]valid example directory[/green] {unit.unit_id}")


@app.command()
def export_schemas(output_dir: Path = Path("schemas")) -> None:
    """Export public artifact contracts as JSON Schema files."""
    written = export_json_schemas(output_dir)
    for path in written:
        print(f"[green]wrote schema[/green] {path}")


@app.command()
def ingest_latex(
    path: Path,
    output_dir: Path,
    source_id: str,
    domain: str,
    local_context: str | None = None,
) -> None:
    """Parse a LaTeX file into theorem/proof unit JSON files."""
    units = ingest_latex_file(
        path=path,
        source_id=source_id,
        domain=domain,
        local_context=local_context,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    for unit in units:
        target = output_dir / f"{unit.unit_id}.json"
        target.write_text(unit.model_dump_json(indent=2), encoding="utf-8")
        print(f"[green]wrote unit[/green] {target}")
    print(f"[green]parsed units[/green] {len(units)}")


@app.command("validate-corpus-catalog")
def validate_corpus_catalog_cmd(
    catalog_path: Path = typer.Argument(..., help="Path to corpus catalog JSON"),
    repo_root: Path = typer.Option(Path("."), help="Repository root for source paths"),
    check_spans: bool = typer.Option(
        True,
        "--check-spans/--no-check-spans",
        help="Validate corpus unit source spans against catalog sources.",
    ),
) -> None:
    catalog = load_corpus_catalog(catalog_path)
    validate_corpus_catalog(catalog=catalog, repo_root=repo_root)
    if check_spans:
        validate_corpus_unit_spans(catalog=catalog, repo_root=repo_root)
    release_modes = sorted({source.release_mode for source in catalog.sources})
    span_note = " with span checks" if check_spans else ""
    print(
        f"[green]valid corpus catalog[/green] {len(catalog.sources)} sources "
        f"(release_modes: {', '.join(release_modes)}){span_note}"
    )


@app.command("ingest-catalog")
def ingest_catalog_cmd(
    catalog_path: Path = typer.Argument(..., help="Path to corpus catalog JSON"),
    output_dir: Path = typer.Argument(..., help="Directory for unit JSON output"),
    repo_root: Path = typer.Option(Path("."), help="Repository root for source paths"),
    repair: bool = typer.Option(False, help="Repair segmentation with a structured model when parsing fails."),
) -> None:
    """Ingest catalog sources into theorem/proof unit JSON files."""
    catalog = load_corpus_catalog(catalog_path)
    model_client = OpenAIResponsesProvider() if repair else None
    units = ingest_catalog(catalog=catalog, repo_root=repo_root, repair=repair, model_client=model_client)
    written = write_units(units, output_dir)
    for path in written:
        print(f"[green]wrote unit[/green] {path}")
    print(f"[green]ingested units[/green] {len(units)} from {len(catalog.sources)} sources")


@app.command("export-shareable-units")
def export_shareable_units_cmd(
    units_dir: Path = typer.Argument(..., help="Directory containing unit JSON files"),
    catalog_path: Path = typer.Argument(..., help="Path to corpus catalog JSON"),
    output_dir: Path = typer.Argument(..., help="Directory for shareable unit JSON output"),
    include_text: bool = typer.Option(False, help="Include only full-text-allowed sources"),
) -> None:
    """Export units with text retained or stripped according to catalog release modes."""
    catalog = load_corpus_catalog(catalog_path)
    units = load_units_from_dir(units_dir)
    shared = export_shareable_units(units=units, catalog=catalog, include_text=include_text)
    written = write_units(shared, output_dir)
    for path in written:
        print(f"[green]wrote shareable unit[/green] {path}")
    print(f"[green]exported shareable units[/green] {len(shared)}")


@app.command()
def render_leantask(task_path: Path, output_path: Path) -> None:
    """Render a LeanTask package JSON file into a Lean source skeleton."""
    task = load_leantask_package(task_path)
    written = write_leantask(task, output_path)
    print(f"[green]wrote Lean file[/green] {written}")


@app.command()
def check_lean(path: Path, project_dir: Path = Path("lean"), timeout_seconds: int = 60) -> None:
    """Check one Lean file through the configured Lake project."""
    resolved_path = path.resolve()
    result = check_lean_file(path=resolved_path, cwd=project_dir.resolve(), timeout_seconds=timeout_seconds)
    if result.passed:
        print(f"[green]Lean check passed[/green] {path}")
        return
    print(f"[red]Lean check failed[/red] {path}")
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    raise typer.Exit(code=result.returncode or 1)


@app.command()
def extract_report(
    unit_path: Path,
    output_path: Path,
    model: str | None = None,
    enrich_candidates: bool = typer.Option(
        False,
        help="Replace theorem candidates with mathlib index lookup results.",
    ),
    index_path: Path | None = typer.Option(
        None,
        help="Declaration index JSON path (defaults to finite-tree fixture).",
    ),
    candidate_top_k: int = typer.Option(5, help="Maximum index candidates when enriching."),
) -> None:
    """Extract a readiness report from a theorem/proof unit using the model provider."""
    unit = load_unit(unit_path)
    provider = OpenAIResponsesProvider(model=model)
    index = load_index(index_path or default_index_path()) if enrich_candidates else None
    report = extract_readiness_report(
        unit=unit,
        model_client=provider,
        enrich_candidates=enrich_candidates,
        index=index,
        candidate_top_k=candidate_top_k,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    print(f"[green]wrote readiness report[/green] {output_path}")


@app.command("extract-proofgraph")
def extract_proofgraph_cmd(
    unit_path: Path,
    output_path: Path,
    model: str | None = None,
) -> None:
    """Extract a proof graph from a theorem/proof unit using the model provider."""
    unit = load_unit(unit_path)
    provider = OpenAIResponsesProvider(model=model)
    graph = extract_proofgraph(unit=unit, model_client=provider)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(graph.model_dump_json(indent=2), encoding="utf-8")
    print(f"[green]wrote proof graph[/green] {output_path}")


@app.command("extract-atlas")
def extract_atlas_cmd(
    unit_path: Path,
    output_path: Path,
    model: str | None = None,
) -> None:
    """Extract an Atlas record from a theorem/proof unit using the model provider."""
    unit = load_unit(unit_path)
    provider = OpenAIResponsesProvider(model=model)
    record = extract_atlas_record(unit=unit, model_client=provider)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
    print(f"[green]wrote Atlas record[/green] {output_path}")


@app.command("generate-leantask")
def generate_leantask_cmd(
    unit_path: Path,
    report_path: Path,
    output_path: Path,
    level: LeanTaskLevel = typer.Option(LeanTaskLevel.L0, help="LeanTask level to generate."),
    model: str | None = None,
    enrich_imports: bool = typer.Option(
        False,
        help="Append mathlib module imports from declaration index lookup.",
    ),
    index_path: Path | None = typer.Option(
        None,
        help="Declaration index JSON path (defaults to finite-tree fixture).",
    ),
    import_top_k: int = typer.Option(5, help="Maximum index modules when enriching imports."),
) -> None:
    """Generate a LeanTask package from a unit and readiness report using the model provider."""
    unit = load_unit(unit_path)
    report = load_readiness_report(report_path)
    provider = OpenAIResponsesProvider(model=model)
    index = load_index(index_path or default_index_path()) if enrich_imports else None
    package = extract_leantask_package(
        unit=unit,
        report=report,
        model_client=provider,
        level=level,
        enrich_imports=enrich_imports,
        index=index,
        import_top_k=import_top_k,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(package.model_dump_json(indent=2), encoding="utf-8")
    print(f"[green]wrote LeanTask package[/green] {output_path}")


@app.command("lookup-declarations")
def lookup_declarations_cmd(
    query: str | None = typer.Option(None, help="Lexical search query."),
    unit_path: Path | None = typer.Option(None, help="Build query from a theorem/proof unit."),
    report_path: Path | None = typer.Option(None, help="Build query from a readiness report."),
    index_path: Path = typer.Option(
        default_index_path(),
        help="Declaration index JSON path.",
    ),
    top_k: int = typer.Option(10, help="Maximum ranked results to print."),
) -> None:
    """Search the mathlib declaration index and print ranked candidates."""
    if sum(value is not None for value in (query, unit_path, report_path)) != 1:
        raise typer.BadParameter("Provide exactly one of --query, --unit-path, or --report-path.")

    if unit_path is not None:
        unit = load_unit(unit_path)
        lookup_query = build_search_query_from_unit(unit)
    elif report_path is not None:
        report = load_readiness_report(report_path)
        lookup_query = build_search_query_from_report(report)
    else:
        lookup_query = query or ""

    index = load_index(index_path)
    hits = search(index=index, query=lookup_query, top_k=top_k)
    print(f"[bold]query[/bold] {lookup_query}")
    for rank, hit in enumerate(hits, start=1):
        print(
            f"{rank}. {hit.declaration.full_name} "
            f"(score={hit.score}, kind={hit.declaration.kind}, module={hit.declaration.module})"
        )


@app.command("align-declarations")
def align_declarations_cmd(
    query: str | None = typer.Option(None, help="Lexical search query."),
    unit_path: Path | None = typer.Option(None, help="Build queries from a theorem/proof unit."),
    report_path: Path | None = typer.Option(None, help="Build queries from a readiness report."),
    index_path: Path = typer.Option(
        default_index_path(),
        help="Declaration index JSON path.",
    ),
    confirmed_name: list[str] = typer.Option(
        [],
        help="Reviewer-confirmed declaration full names (never auto-promoted).",
    ),
    top_k: int = typer.Option(15, help="Maximum ranked alignment candidates to print."),
) -> None:
    """Search the mathlib index across lexical, namespace, module, and kind dimensions."""
    if sum(value is not None for value in (query, unit_path, report_path)) != 1:
        raise typer.BadParameter("Provide exactly one of --query, --unit-path, or --report-path.")

    index = load_index(index_path)
    if report_path is not None:
        report = load_readiness_report(report_path)
        unit = None
        if unit_path is not None:
            unit = load_unit(unit_path)
        alignment = align_readiness_report(
            report=report,
            index=index,
            unit=unit,
            confirmed_full_names=frozenset(confirmed_name),
            top_k_total=top_k,
        )
        print(f"[bold]unit[/bold] {alignment.unit_id}")
        print(f"[bold]index[/bold] {alignment.index_id}")
        for rank, candidate in enumerate(alignment.candidates, start=1):
            print(
                f"{rank}. {candidate.full_name} "
                f"(score={candidate.score}, status={candidate.alignment_status}, "
                f"source={candidate.query_source})"
            )
        if alignment.confirmed:
            print("[bold]confirmed[/bold]")
            for candidate in alignment.confirmed:
                print(f"- {candidate.full_name}")
        return

    if unit_path is not None:
        unit = load_unit(unit_path)
        lookup_query = build_search_query_from_unit(unit)
    else:
        lookup_query = query or ""

    hits = search(index=index, query=lookup_query, top_k=top_k)
    print(f"[bold]query[/bold] {lookup_query}")
    for rank, hit in enumerate(hits, start=1):
        print(
            f"{rank}. {hit.declaration.full_name} "
            f"(score={hit.score}, kind={hit.declaration.kind}, module={hit.declaration.module})"
        )


@app.command("align-readiness-report")
def align_readiness_report_cmd(
    report_path: Path,
    output_path: Path,
    unit_path: Path | None = typer.Option(None, help="Optional source unit for statement tokens."),
    index_path: Path = typer.Option(
        default_index_path(),
        help="Declaration index JSON path.",
    ),
    confirmed_name: list[str] = typer.Option(
        [],
        help="Reviewer-confirmed declaration full names (never auto-promoted).",
    ),
    top_k: int = typer.Option(15, help="Maximum ranked alignment candidates to write."),
    enrich_report: bool = typer.Option(
        False,
        help="Also write an enriched readiness report with candidate theorem names.",
    ),
    enriched_output_path: Path | None = typer.Option(
        None,
        help="Path for enriched readiness report when --enrich-report is set.",
    ),
) -> None:
    """Align a readiness report against the mathlib index and write an AlignmentResult artifact."""
    report = load_readiness_report(report_path)
    unit = load_unit(unit_path) if unit_path is not None else None
    index = load_index(index_path)
    alignment = align_readiness_report(
        report=report,
        index=index,
        unit=unit,
        confirmed_full_names=frozenset(confirmed_name),
        top_k_total=top_k,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(alignment.model_dump_json(indent=2), encoding="utf-8")
    print(f"[green]wrote alignment result[/green] {output_path}")
    if alignment.confirmed:
        print(f"[green]confirmed alignments[/green] {len(alignment.confirmed)}")
    print(f"[green]candidate alignments[/green] {len(alignment.candidates)}")

    if enrich_report:
        enriched = enrich_readiness_candidates_from_alignment(
            report=report,
            alignment=alignment,
            top_k=top_k,
        )
        target = enriched_output_path or output_path.with_name("readiness_report.enriched.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(enriched.model_dump_json(indent=2), encoding="utf-8")
        print(f"[green]wrote enriched readiness report[/green] {target}")


@app.command("enrich-report-candidates")
def enrich_report_candidates_cmd(
    report_path: Path,
    output_path: Path,
    index_path: Path = typer.Option(
        default_index_path(),
        help="Declaration index JSON path.",
    ),
    query: str | None = typer.Option(None, help="Optional override query for lookup."),
    top_k: int = typer.Option(5, help="Maximum candidates to write into the report."),
) -> None:
    """Replace readiness-report theorem candidates with index lookup results."""
    report = load_readiness_report(report_path)
    index = load_index(index_path)
    enriched = enrich_readiness_candidates(
        report=report,
        index=index,
        query=query,
        top_k=top_k,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(enriched.model_dump_json(indent=2), encoding="utf-8")
    print(f"[green]wrote enriched readiness report[/green] {output_path}")


@app.command("promote-benchmark-item")
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
    manifest_path.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
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


@app.command("validate-readinessbench")
def validate_readinessbench_cmd(
    manifest_path: Path = typer.Option(
        default_manifest_path(),
        help="Path to ReadinessBench manifest JSON.",
    ),
    benchmark_root: Path | None = typer.Option(
        None,
        help="Benchmark root directory (defaults to manifest parent).",
    ),
) -> None:
    """Validate ReadinessBench manifest tier invariants and artifact paths."""
    root = benchmark_root or manifest_path.parent
    manifest = load_manifest(manifest_path)
    gold_reports = validate_manifest(manifest=manifest, benchmark_root=root)
    print(
        f"[green]valid ReadinessBench manifest[/green] {manifest.benchmark_id} "
        f"({len(manifest.items)} items, {len(gold_reports)} gold)"
    )


@app.command("run-readinessbench")
def run_readinessbench_cmd(
    predictions_dir: Path = typer.Argument(..., help="Directory of predicted readiness reports."),
    manifest_path: Path = typer.Option(
        default_manifest_path(),
        help="Path to ReadinessBench manifest JSON.",
    ),
    output_path: Path | None = typer.Option(
        None,
        help="Optional path for the evaluation report JSON.",
    ),
    benchmark_root: Path | None = typer.Option(
        None,
        help="Benchmark root directory (defaults to manifest parent).",
    ),
) -> None:
    """Score predicted readiness reports against ReadinessBench gold items."""
    root = benchmark_root or manifest_path.parent
    report = run_readinessbench(
        manifest_path=manifest_path,
        predictions_dir=predictions_dir,
        benchmark_root=root,
    )
    payload = report.model_dump_json(indent=2)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
        print(f"[green]wrote evaluation report[/green] {output_path}")
    print(payload)
    print(f"[green]macro_f1_mean[/green] {report.macro_f1_mean}")



@app.command("run-benchmark-evaluation")
def run_benchmark_evaluation_cmd(
    predictions_dir: Path = typer.Argument(..., help="Directory of predicted artifacts."),
    manifest_path: Path = typer.Option(
        default_manifest_path(),
        help="Path to ReadinessBench manifest JSON.",
    ),
    output_path: Path | None = typer.Option(
        None,
        help="Optional path for the evaluation report JSON.",
    ),
    benchmark_root: Path | None = typer.Option(
        None,
        help="Benchmark root directory (defaults to manifest parent).",
    ),
    repo_root: Path = typer.Option(Path("."), help="Repository root for gold example lookup."),
) -> None:
    """Score predicted artifacts against ReadinessBench gold and reference examples."""
    root = benchmark_root or manifest_path.parent
    report = run_benchmark_evaluation(
        manifest_path=manifest_path,
        predictions_dir=predictions_dir,
        benchmark_root=root,
        repo_root=repo_root.resolve(),
    )
    payload = report.model_dump_json(indent=2)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
        print(f"[green]wrote evaluation report[/green] {output_path}")
    print(payload)
    print(f"[green]full_macro_f1_mean[/green] {report.full_macro_f1_mean}")


@app.command("run-baselines")
def run_baselines_cmd(
    output_dir: Path = typer.Option(
        Path("artifacts/generated/baselines"),
        help="Output directory for baseline run artifacts.",
    ),
    catalog_path: Path = typer.Option(
        Path("benchmarks/baselines/manifest.json"),
        help="Baseline manifest JSON path.",
    ),
    conditions: str = typer.Option(
        "all",
        help="Comma-separated conditions: direct, with_alignment, no_alignment, or all.",
    ),
    run_id: str = typer.Option("local_run", help="Run identifier for manifest output."),
    model: str | None = typer.Option(None, help="Optional model override."),
    repo_root: Path = typer.Option(Path("."), help="Repository root."),
) -> None:
    """Run baseline artifact generation for reference examples."""
    repo = repo_root.resolve()
    selected = resolve_baseline_conditions(conditions=conditions)
    provider = OpenAIResponsesProvider(model=model)
    run_output = output_dir / run_id
    result = run_baselines(
        output_dir=run_output,
        model_client=provider,
        repo_root=repo,
        manifest_path=(repo / catalog_path).resolve(),
        run_id=run_id,
        conditions=selected,
        model_name=provider.model,
    )
    print(
        f"[green]baseline run complete[/green] units={result.unit_count} "
        f"conditions={result.condition_count} -> {result.output_dir}"
    )


@app.command("categorize-baseline-errors")
def categorize_baseline_errors_cmd(
    predicted_root: Path = typer.Argument(..., help="Root directory of predicted baseline runs."),
    repo_root: Path = typer.Option(Path("."), help="Repository root."),
    output_path: Path | None = typer.Option(
        None,
        help="Optional JSON output path for aggregated summary.",
    ),
) -> None:
    """Categorize baseline prediction errors against reference gold examples."""
    repo = repo_root.resolve()
    manifest_path = repo / "benchmarks" / "baselines" / "manifest.json"
    from fre_core.baseline_runner import load_baseline_units

    units = load_baseline_units(repo_root=repo, manifest_path=manifest_path)
    summaries = []
    for unit in units:
        predicted_dir = predicted_root / unit.unit_id
        if not predicted_dir.is_dir():
            predicted_dir = predicted_root / BaselineCondition.DIRECT.value / unit.unit_id
        summaries.append(
            categorize_baseline_run(
                predicted_dir=predicted_dir,
                gold_dir=unit.example_dir,
                unit_id=unit.unit_id,
            )
        )
    payload = aggregate_error_summaries(summaries=summaries)
    encoded = json.dumps(payload, indent=2)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(encoded + "\n", encoding="utf-8")
        print(f"[green]wrote error summary[/green] {output_path}")
    print(encoded)


@app.command("validate-review-submission")
def validate_review_submission_cmd(path: Path) -> None:
    """Validate a structured readiness-report review submission JSON file."""
    submission = load_review_submission(path)
    validate_review_submission(submission)
    print(
        f"[green]valid review submission[/green] {submission.unit_id} "
        f"reviewer={submission.reviewer_id}"
    )


@app.command("validate-gold-changelog")
def validate_gold_changelog_cmd(
    path: Path = typer.Option(
        Path("benchmarks/readinessbench/gold/changelog.jsonl"),
        help="Path to gold artifact changelog JSONL.",
    ),
) -> None:
    """Validate ReadinessBench gold artifact changelog entries."""
    entries = load_changelog_entries(path)
    validate_changelog_entries(entries)
    print(f"[green]valid gold changelog[/green] {len(entries)} entries")


@app.command("export-public-benchmark")
def export_public_benchmark_cmd(
    output_path: Path = typer.Option(
        default_public_exports_dir() / "readinessbench.jsonl",
        help="Output JSONL path.",
    ),
    manifest_path: Path = typer.Option(
        default_manifest_path(),
        help="ReadinessBench manifest JSON path.",
    ),
    catalog_path: Path | None = typer.Option(
        None,
        help="Optional corpus catalog for release-mode text stripping.",
    ),
    manifest_output: Path | None = typer.Option(
        None,
        help="Optional path for the export manifest JSON.",
    ),
) -> None:
    """Export ReadinessBench tiers as public JSONL with release-mode filtering."""
    manifest = export_public_benchmark(
        output_path=output_path,
        manifest_path=manifest_path,
        catalog_path=catalog_path,
    )
    target = manifest_output or output_path.with_suffix(".manifest.json")
    write_export_manifest(manifest=manifest, output_path=target)
    print(f"[green]exported benchmark[/green] {manifest.record_count} records -> {output_path}")
    print(f"[green]wrote manifest[/green] {target}")


@app.command("export-public-atlas")
def export_public_atlas_cmd(
    output_path: Path = typer.Option(
        default_public_exports_dir() / "atlas.jsonl",
        help="Output JSONL path.",
    ),
    catalog_path: Path | None = typer.Option(
        None,
        help="Optional corpus catalog for release-mode text stripping.",
    ),
    manifest_output: Path | None = typer.Option(
        None,
        help="Optional path for the export manifest JSON.",
    ),
) -> None:
    """Export curated Atlas records from examples and reviewed benchmark items."""
    manifest = export_public_atlas(
        output_path=output_path,
        catalog_path=catalog_path,
    )
    target = manifest_output or output_path.with_suffix(".manifest.json")
    write_export_manifest(manifest=manifest, output_path=target)
    print(f"[green]exported atlas[/green] {manifest.record_count} records -> {output_path}")
    print(f"[green]wrote manifest[/green] {target}")


@app.command("check-licensing-leak")
def check_licensing_leak_cmd(
    jsonl_path: Path,
    catalog_path: Path,
) -> None:
    """Fail when metadata-only source text appears in a public export."""
    from fre_core.corpus import load_corpus_catalog, load_units_from_dir

    catalog = load_corpus_catalog(catalog_path)
    units_dir = catalog_path.parent / "ingested"
    restricted_units = load_units_from_dir(units_dir) if units_dir.is_dir() else None
    assert_no_licensing_leak(
        jsonl_path=jsonl_path,
        catalog=catalog,
        restricted_units=restricted_units,
    )
    print(f"[green]no licensing leak detected[/green] {jsonl_path}")



@app.command("generate-atlas-clusters")
def generate_atlas_clusters_cmd(
    manifest_path: Path = typer.Option(
        default_manifest_path(),
        help="ReadinessBench manifest path.",
    ),
    output_path: Path = typer.Option(
        Path("public_exports/atlas_clusters.json"),
        help="Output path for the cluster report JSON.",
    ),
) -> None:
    """Cluster gold benchmark blockers into a deterministic Atlas report."""
    report = generate_atlas_cluster_report(manifest_path=manifest_path)
    write_atlas_cluster_report(report=report, output_path=output_path)
    print(f"[green]wrote atlas cluster report[/green] {report.cluster_count} clusters -> {output_path}")


@app.command("build-release-manifest")
def build_release_manifest_cmd(
    release_version: str = typer.Option("v0.2.0", help="Release version label."),
    output_path: Path = typer.Option(
        Path("releases/v0.2.0/manifest.json"),
        help="Output path for the release manifest JSON.",
    ),
    artifact_path: list[Path] = typer.Option(
        [],
        help="Artifact file paths to checksum (repeatable). Defaults to public exports.",
    ),
    git_commit: str | None = typer.Option(None, help="Optional git commit override."),
    repo_root: Path = typer.Option(
        Path("."),
        help="Repository root for repo-relative artifact paths in the manifest.",
    ),
) -> None:
    """Build a versioned release manifest with artifact checksums."""
    root = repo_root.resolve()
    artifacts = artifact_path
    if not artifacts:
        exports_dir = default_public_exports_dir(repo_root=root)
        artifacts = [
            exports_dir / "readinessbench.jsonl",
            exports_dir / "atlas.jsonl",
            exports_dir / "atlas_clusters.json",
        ]
    manifest = build_release_manifest(
        release_version=release_version,
        artifact_paths=artifacts,
        git_commit=git_commit,
        repo_root=root,
    )
    write_release_manifest(manifest=manifest, output_path=output_path)
    print(f"[green]wrote release manifest[/green] {output_path} ({len(manifest.artifacts)} artifacts)")


@app.command("verify-release-manifest")
def verify_release_manifest_cmd(
    manifest_path: Path = typer.Option(
        Path("releases/v0.2.0/manifest.json"),
        help="Path to the release manifest JSON.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        help="Repository root used to resolve artifact paths.",
    ),
) -> None:
    """Verify committed release artifacts match the release manifest checksums."""
    verify_release_manifest(manifest_path=manifest_path, repo_root=repo_root.resolve())
    print(f"[green]release manifest verified[/green] {manifest_path}")

@app.command()
def demo(
    offline: bool = typer.Option(
        True,
        "--offline/--live",
        help="Offline mode uses committed gold artifacts (CI-safe). Live mode runs OpenAI extraction.",
    ),
    example: str = typer.Option(
        "all",
        "--example",
        help="Reference example to run: finite_tree, category_theory_pullback, or all.",
    ),
) -> None:
    """Run the end-to-end artifact pipeline on reference examples."""
    from fre_core.demo_runner import main as run_demo_main

    exit_code = run_demo_main(offline=offline, example=example)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


if __name__ == "__main__":
    app()

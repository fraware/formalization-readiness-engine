"""Command-line entry points for the Formalization Readiness Engine."""

from __future__ import annotations

from pathlib import Path

import typer
from rich import print

from fre_core.corpus import (
    export_shareable_units,
    ingest_catalog,
    load_corpus_catalog,
    load_units_from_dir,
    write_units,
)
from fre_core.extract_atlas import extract_atlas_record
from fre_core.extract_proofgraph import extract_proofgraph
from fre_core.extraction import extract_readiness_report
from fre_core.latex_ingestion import ingest_latex_file
from fre_core.lean_runner import check_lean_file
from fre_core.leantask_renderer import write_leantask
from fre_core.mathlib_index import (
    build_search_query_from_report,
    build_search_query_from_unit,
    default_index_path,
    enrich_readiness_candidates,
    load_index,
    search,
)
from fre_core.openai_responses_provider import OpenAIResponsesProvider
from fre_core.schema_exports import export_json_schemas
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


@app.command("ingest-catalog")
def ingest_catalog_cmd(
    catalog_path: Path = typer.Argument(..., help="Path to corpus catalog JSON"),
    output_dir: Path = typer.Argument(..., help="Directory for unit JSON output"),
    repo_root: Path = typer.Option(Path("."), help="Repository root for source paths"),
) -> None:
    """Ingest catalog sources into theorem/proof unit JSON files."""
    catalog = load_corpus_catalog(catalog_path)
    units = ingest_catalog(catalog=catalog, repo_root=repo_root)
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
    result = check_lean_file(path=path, cwd=project_dir, timeout_seconds=timeout_seconds)
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


@app.command()
def demo() -> None:
    """Describe the first target demo."""
    print(
        "finite-tree source -> theorem/proof unit -> readiness report -> "
        "proof graph -> Atlas record -> LeanTask package -> Lean check"
    )


if __name__ == "__main__":
    app()

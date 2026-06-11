"""Command-line entry points for the Formalization Readiness Engine."""

from __future__ import annotations

from pathlib import Path

import typer
from rich import print

from fre_core.extraction import extract_readiness_report
from fre_core.latex_ingestion import ingest_latex_file
from fre_core.lean_runner import check_lean_file
from fre_core.leantask_renderer import write_leantask
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
def extract_report(unit_path: Path, output_path: Path, model: str | None = None) -> None:
    """Extract a readiness report from a theorem/proof unit using the model provider."""
    unit = load_unit(unit_path)
    provider = OpenAIResponsesProvider(model=model)
    report = extract_readiness_report(unit=unit, model_client=provider)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    print(f"[green]wrote readiness report[/green] {output_path}")


@app.command()
def demo() -> None:
    """Describe the first target demo."""
    print(
        "finite-tree source -> theorem/proof unit -> readiness report -> "
        "proof graph -> Atlas record -> LeanTask package -> Lean check"
    )


if __name__ == "__main__":
    app()

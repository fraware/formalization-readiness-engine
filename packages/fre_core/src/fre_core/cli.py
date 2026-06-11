"""Command-line entry points for the Formalization Readiness Engine."""

from __future__ import annotations

from pathlib import Path

import typer
from rich import print

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
def demo() -> None:
    """Describe the first target demo."""
    print(
        "finite-tree source -> theorem/proof unit -> readiness report -> "
        "proof graph -> Atlas record -> LeanTask package -> Lean check"
    )


if __name__ == "__main__":
    app()

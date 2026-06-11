"""Command-line entry points for the Formalization Readiness Engine."""

from __future__ import annotations

from pathlib import Path

import typer
from rich import print

from fre_core.schemas import ReadinessReport, TheoremProofUnit

app = typer.Typer(help="Formalization Readiness Engine CLI")


@app.command()
def validate_unit(path: Path) -> None:
    """Validate a theorem/proof unit JSON file."""
    payload = path.read_text(encoding="utf-8")
    unit = TheoremProofUnit.model_validate_json(payload)
    print(f"[green]valid unit[/green] {unit.unit_id}")


@app.command()
def validate_report(path: Path) -> None:
    """Validate a readiness report JSON file."""
    payload = path.read_text(encoding="utf-8")
    report = ReadinessReport.model_validate_json(payload)
    print(f"[green]valid readiness report[/green] {report.unit_id}")


@app.command()
def demo() -> None:
    """Describe the first target demo."""
    print(
        "finite-tree source -> theorem/proof unit -> readiness report -> "
        "proof graph -> Atlas record -> LeanTask package -> Lean check"
    )


if __name__ == "__main__":
    app()

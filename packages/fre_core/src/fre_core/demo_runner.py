"""End-to-end demo orchestration for the Formalization Readiness Engine."""

from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from rich.console import Console
from rich.table import Table

from fre_core.benchmark import (
    default_benchmark_root,
    default_manifest_path,
    load_manifest,
    run_readinessbench,
    validate_manifest,
)
from fre_core.extract_atlas import extract_atlas_record
from fre_core.extract_leantask import extract_leantask_package
from fre_core.extract_proofgraph import extract_proofgraph
from fre_core.extraction import extract_readiness_report
from fre_core.lean_runner import check_lean_file
from fre_core.leantask_renderer import write_leantask
from fre_core.mathlib_alignment import (
    align_readiness_report,
    enrich_readiness_candidates_from_alignment,
)
from fre_core.embedding_index import load_embedding_index
from fre_core.mathlib_index import load_index
from fre_core.openai_responses_provider import OpenAIResponsesProvider
from fre_core.public_export import export_public_atlas, export_public_benchmark
from fre_core.schemas import AlignmentResult, LeanTaskLevel
from fre_core.validation import (
    load_atlas_record,
    load_leantask_package,
    load_proofgraph,
    load_readiness_report,
    load_unit,
)

ExampleKey = Literal["finite_tree", "category_theory_pullback"]

EXAMPLE_KEYS: tuple[ExampleKey, ...] = ("finite_tree", "category_theory_pullback")

EXAMPLE_CONFIG: dict[ExampleKey, dict[str, str]] = {
    "finite_tree": {
        "dir": "examples/finite_tree",
        "unit_id": "finite_tree_edge_count",
        "index_fixture": "fixtures/mathlib_declarations/finite_tree_v0.json",
        "lean_output": "FiniteTree.lean",
    },
    "category_theory_pullback": {
        "dir": "examples/category_theory_pullback",
        "unit_id": "category_theory_pullback_equivalence",
        "index_fixture": "fixtures/mathlib_declarations/category_theory_v0.json",
        "lean_output": "CategoryTheoryPullback.lean",
    },
}

ALL_EXAMPLES = "all"


class DemoError(RuntimeError):
    """Raised when the demo pipeline cannot continue."""


@dataclass(frozen=True)
class ExampleDemoResult:
    """Outcome summary for one reference example."""

    example_key: ExampleKey
    unit_id: str
    validation_ok: bool
    top_alignment: str | None
    lean_check_status: str
    output_dir: Path


@dataclass
class DemoRunResult:
    """Aggregate outcome for a full demo invocation."""

    offline: bool
    example_results: list[ExampleDemoResult] = field(default_factory=list)
    macro_f1_mean: float | None = None
    export_benchmark_path: Path | None = None
    export_atlas_path: Path | None = None
    export_dir: Path | None = None


def repo_root() -> Path:
    """Return the repository root directory."""
    return Path(__file__).resolve().parents[4]


def resolve_example_keys(example: str) -> tuple[ExampleKey, ...]:
    """Resolve CLI example selector to concrete example keys."""
    normalized = example.strip().casefold().replace("-", "_")
    if normalized == ALL_EXAMPLES:
        return EXAMPLE_KEYS
    if normalized in EXAMPLE_KEYS:
        return (normalized,)  # type: ignore[return-value]
    allowed = ", ".join([*EXAMPLE_KEYS, ALL_EXAMPLES])
    raise DemoError(f"Unknown example {example!r}. Expected one of: {allowed}.")


def default_predictions_dir(*, root: Path | None = None) -> Path:
    """Return the committed ReadinessBench prediction fixture directory."""
    base = root or repo_root()
    return base / "tests" / "fixtures" / "readinessbench_predictions"


def default_demo_output_root(*, root: Path | None = None, offline: bool = True) -> Path:
    """Return the demo artifact output root under artifacts/generated/demo_run/."""
    base = root or repo_root()
    mode = "offline" if offline else "live"
    return base / "artifacts" / "generated" / "demo_run" / mode


def _resolve_leantask_l1_path(example_dir: Path) -> Path:
    """Return the L1 LeanTask package path for an example directory."""
    l1_path = example_dir / "leantask_L1.json"
    if l1_path.is_file():
        return l1_path

    fallback = example_dir / "leantask.json"
    if not fallback.is_file():
        raise DemoError(f"Missing LeanTask package in {example_dir.as_posix()}.")

    package = load_leantask_package(fallback)
    if package.level == LeanTaskLevel.L1:
        return fallback

    raise DemoError(
        f"Missing leantask_L1.json in {example_dir.as_posix()} "
        f"and {fallback.name} is level {package.level.value}."
    )


def _should_skip_lean() -> bool:
    return os.environ.get("DEMO_SKIP_LEAN", "").strip().casefold() in {"1", "true", "yes", "on"}


def _lean_available() -> bool:
    return shutil.which("lake") is not None


def _log_stage(console: Console, stage: str, detail: str) -> None:
    console.print(f"[bold cyan]->[/bold cyan] [bold]{stage}[/bold]  {detail}")


def _log_ok(console: Console, message: str) -> None:
    console.print(f"  [green]ok[/green] {message}")


def _log_skip(console: Console, message: str) -> None:
    console.print(f"  [yellow]skip[/yellow] {message}")


def _validate_example_dir(*, example_dir: Path, console: Console) -> str:
    _log_stage(console, "validate-example-dir", example_dir.as_posix())
    unit = load_unit(example_dir / "unit.json")
    report = load_readiness_report(example_dir / "readiness_report.json")
    graph = load_proofgraph(example_dir / "proofgraph.json")
    record = load_atlas_record(example_dir / "atlas_record.json")
    task = load_leantask_package(example_dir / "leantask.json")

    unit_ids = {unit.unit_id, report.unit_id, graph.unit_id, record.unit_id, task.unit_id}
    if len(unit_ids) != 1:
        raise DemoError(f"Inconsistent unit ids in {example_dir.as_posix()}: {sorted(unit_ids)}")

    _log_ok(console, f"valid example directory ({unit.unit_id})")
    return unit.unit_id


def _run_live_extraction(
    *,
    example_dir: Path,
    output_dir: Path,
    console: Console,
) -> None:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise DemoError("Live demo requires OPENAI_API_KEY.")

    unit = load_unit(example_dir / "unit.json")
    provider = OpenAIResponsesProvider()

    report_path = output_dir / "readiness_report.model.json"
    _log_stage(console, "extract-report", report_path.as_posix())
    report = extract_readiness_report(unit=unit, model_client=provider)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    _log_ok(console, f"wrote readiness report ({report.unit_id})")

    graph_path = output_dir / "proofgraph.model.json"
    _log_stage(console, "extract-proofgraph", graph_path.as_posix())
    graph = extract_proofgraph(unit=unit, model_client=provider)
    graph_path.write_text(graph.model_dump_json(indent=2), encoding="utf-8")
    _log_ok(console, f"wrote proof graph ({graph.unit_id})")

    atlas_path = output_dir / "atlas_record.model.json"
    _log_stage(console, "extract-atlas", atlas_path.as_posix())
    record = extract_atlas_record(unit=unit, model_client=provider)
    atlas_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
    _log_ok(console, f"wrote Atlas record ({record.unit_id})")

    leantask_path = output_dir / "leantask.model.json"
    _log_stage(console, "generate-leantask", leantask_path.as_posix())
    package = extract_leantask_package(
        unit=unit,
        report=report,
        model_client=provider,
        level=LeanTaskLevel.L0,
    )
    leantask_path.write_text(package.model_dump_json(indent=2), encoding="utf-8")
    _log_ok(console, f"wrote LeanTask package ({package.leantask_id})")


def _align_and_enrich(
    *,
    example_dir: Path,
    index_path: Path,
    output_dir: Path,
    console: Console,
) -> AlignmentResult:
    report = load_readiness_report(example_dir / "readiness_report.json")
    unit = load_unit(example_dir / "unit.json")
    index = load_index(index_path)
    embedding_index = load_embedding_index(index=index, index_path=index_path)

    alignment_path = output_dir / "alignment.json"
    _log_stage(console, "align-readiness-report", alignment_path.as_posix())
    alignment = align_readiness_report(
        report=report,
        index=index,
        unit=unit,
        embedding_index=embedding_index,
    )
    alignment_path.parent.mkdir(parents=True, exist_ok=True)
    alignment_path.write_text(alignment.model_dump_json(indent=2), encoding="utf-8")
    top = alignment.candidates[0].full_name if alignment.candidates else None
    candidate_count = len(alignment.candidates)
    top_detail = f", top={top}" if top else ""
    _log_ok(console, f"wrote alignment ({candidate_count} candidates{top_detail})")

    enriched_path = output_dir / "readiness_report.enriched.json"
    _log_stage(console, "enrich-report-candidates", enriched_path.as_posix())
    enriched = enrich_readiness_candidates_from_alignment(report=report, alignment=alignment)
    enriched_path.write_text(enriched.model_dump_json(indent=2), encoding="utf-8")
    _log_ok(console, "wrote enriched readiness report")

    return alignment


def _render_l1(
    *,
    example_dir: Path,
    lean_output_name: str,
    output_dir: Path,
    console: Console,
) -> Path:
    task_path = _resolve_leantask_l1_path(example_dir)
    lean_path = output_dir / lean_output_name
    _log_stage(console, "render-leantask", f"{task_path.name} -> {lean_path.as_posix()}")
    task = load_leantask_package(task_path)
    written = write_leantask(task, lean_path)
    _log_ok(console, f"wrote Lean skeleton ({task.leantask_id})")
    return written


def _check_lean(
    *,
    lean_path: Path,
    project_dir: Path,
    console: Console,
) -> str:
    if _should_skip_lean():
        _log_skip(console, "Lean check skipped (DEMO_SKIP_LEAN=1)")
        return "skipped"

    if not _lean_available():
        _log_skip(console, "Lean check skipped (lake not found on PATH)")
        return "skipped"

    _log_stage(console, "check-lean", lean_path.as_posix())
    result = check_lean_file(path=lean_path, cwd=project_dir)
    if result.passed:
        _log_ok(console, "Lean check passed")
        return "passed"

    detail = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
    raise DemoError(f"Lean check failed for {lean_path.as_posix()}: {detail}")


def _run_readinessbench_global(
    *,
    root: Path,
    predictions_dir: Path,
    console: Console,
) -> float | None:
    manifest_path = default_manifest_path(repo_root=root)
    benchmark_root = default_benchmark_root(repo_root=root)

    _log_stage(console, "validate-readinessbench", manifest_path.as_posix())
    manifest = load_manifest(manifest_path)
    validate_manifest(manifest=manifest, benchmark_root=benchmark_root)
    _log_ok(console, f"valid manifest ({len(manifest.items)} items)")

    _log_stage(console, "run-readinessbench", predictions_dir.as_posix())
    if not predictions_dir.is_dir():
        _log_skip(console, f"predictions directory missing: {predictions_dir.as_posix()}")
        return None

    report = run_readinessbench(
        manifest_path=manifest_path,
        predictions_dir=predictions_dir,
        benchmark_root=benchmark_root,
    )
    _log_ok(console, f"macro_f1_mean={report.macro_f1_mean} ({report.scored_item_count} gold items scored)")
    return report.macro_f1_mean


def _export_public_artifacts(
    *,
    export_dir: Path,
    console: Console,
) -> tuple[Path, Path]:
    benchmark_path = export_dir / "readinessbench.jsonl"
    atlas_path = export_dir / "atlas.jsonl"

    _log_stage(console, "export-public-benchmark", benchmark_path.as_posix())
    export_public_benchmark(output_path=benchmark_path)
    _log_ok(console, f"exported benchmark -> {benchmark_path.as_posix()}")

    _log_stage(console, "export-public-atlas", atlas_path.as_posix())
    export_public_atlas(output_path=atlas_path)
    _log_ok(console, f"exported atlas -> {atlas_path.as_posix()}")

    return benchmark_path, atlas_path


def _print_summary(console: Console, result: DemoRunResult) -> None:
    table = Table(title="Demo summary", show_header=True, header_style="bold")
    table.add_column("example")
    table.add_column("unit_id")
    table.add_column("validation")
    table.add_column("top alignment")
    table.add_column("lean check")
    table.add_column("output dir")

    for example_result in result.example_results:
        table.add_row(
            example_result.example_key,
            example_result.unit_id,
            "ok" if example_result.validation_ok else "failed",
            example_result.top_alignment or "-",
            example_result.lean_check_status,
            example_result.output_dir.as_posix(),
        )

    console.print()
    console.print(table)

    if result.macro_f1_mean is not None:
        console.print(f"[bold]ReadinessBench macro_f1_mean:[/bold] {result.macro_f1_mean}")
    if result.export_benchmark_path is not None:
        console.print(f"[bold]Public benchmark export:[/bold] {result.export_benchmark_path.as_posix()}")
    if result.export_atlas_path is not None:
        console.print(f"[bold]Public atlas export:[/bold] {result.export_atlas_path.as_posix()}")


def run_example_demo(
    *,
    example_key: ExampleKey,
    root: Path,
    offline: bool,
    output_root: Path,
    console: Console,
) -> ExampleDemoResult:
    """Run the artifact pipeline for one reference example."""
    config = EXAMPLE_CONFIG[example_key]
    example_dir = root / config["dir"]
    example_output = output_root / example_key
    example_output.mkdir(parents=True, exist_ok=True)

    console.print()
    console.print(f"[bold magenta]Example:[/bold magenta] {example_key} ({config['unit_id']})")

    if not offline:
        _run_live_extraction(example_dir=example_dir, output_dir=example_output, console=console)

    unit_id = _validate_example_dir(example_dir=example_dir, console=console)

    index_path = root / config["index_fixture"]
    alignment = _align_and_enrich(
        example_dir=example_dir,
        index_path=index_path,
        output_dir=example_output,
        console=console,
    )
    top_alignment = alignment.candidates[0].full_name if alignment.candidates else None

    lean_path = _render_l1(
        example_dir=example_dir,
        lean_output_name=config["lean_output"],
        output_dir=example_output,
        console=console,
    )
    lean_status = _check_lean(
        lean_path=lean_path,
        project_dir=root / "lean",
        console=console,
    )

    return ExampleDemoResult(
        example_key=example_key,
        unit_id=unit_id,
        validation_ok=True,
        top_alignment=top_alignment,
        lean_check_status=lean_status,
        output_dir=example_output,
    )


def run_demo(
    *,
    offline: bool = True,
    example: str = ALL_EXAMPLES,
    repo_root_path: Path | None = None,
    predictions_dir: Path | None = None,
    console: Console | None = None,
) -> DemoRunResult:
    """Run the end-to-end demo pipeline and return structured results."""
    root = repo_root_path or repo_root()
    console = console or Console()
    example_keys = resolve_example_keys(example)
    output_root = default_demo_output_root(root=root, offline=offline)
    if predictions_dir is not None:
        predictions = predictions_dir
    elif offline:
        predictions = default_predictions_dir(root=root)
    else:
        predictions = output_root

    mode_label = "offline" if offline else "live"
    console.print(f"[bold]Formalization Readiness Engine demo[/bold] ({mode_label})")
    console.print(f"Repository root: {root.as_posix()}")
    console.print(f"Demo outputs: {output_root.as_posix()}")

    result = DemoRunResult(offline=offline)

    for example_key in example_keys:
        example_result = run_example_demo(
            example_key=example_key,
            root=root,
            offline=offline,
            output_root=output_root,
            console=console,
        )
        result.example_results.append(example_result)

    result.macro_f1_mean = _run_readinessbench_global(
        root=root,
        predictions_dir=predictions,
        console=console,
    )

    if offline:
        export_temp = tempfile.TemporaryDirectory(prefix="fre_demo_export_")
        export_dir = Path(export_temp.name)
        try:
            benchmark_path, atlas_path = _export_public_artifacts(
                export_dir=export_dir,
                console=console,
            )
            result.export_dir = export_dir
            result.export_benchmark_path = benchmark_path
            result.export_atlas_path = atlas_path
            _print_summary(console, result)
        finally:
            export_temp.cleanup()
    else:
        export_dir = output_root / "public_exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        benchmark_path, atlas_path = _export_public_artifacts(
            export_dir=export_dir,
            console=console,
        )
        result.export_dir = export_dir
        result.export_benchmark_path = benchmark_path
        result.export_atlas_path = atlas_path
        _print_summary(console, result)

    console.print()
    console.print("[green]Demo completed successfully.[/green]")
    return result


def main(*, offline: bool = True, example: str = ALL_EXAMPLES) -> int:
    """CLI entry point for the demo runner."""
    try:
        run_demo(offline=offline, example=example)
    except DemoError as exc:
        Console().print(f"[red]Demo failed:[/red] {exc}")
        return 1
    except Exception as exc:
        Console().print(f"[red]Demo failed unexpectedly:[/red] {exc}")
        return 1
    return 0

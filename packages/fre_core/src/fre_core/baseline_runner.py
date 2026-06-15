"""Baseline extraction harness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from fre_core.extract_atlas import extract_atlas_record
from fre_core.extract_leantask import extract_leantask_package
from fre_core.extract_proofgraph import extract_proofgraph
from fre_core.extraction import extract_readiness_report
from fre_core.mathlib_alignment import align_readiness_report, enrich_readiness_candidates_from_alignment
from fre_core.embedding_index import load_embedding_index
from fre_core.mathlib_index import default_index_path, load_index
from fre_core.model_client import StructuredModelClient
from fre_core.validation import load_unit


class BaselineCondition(str, Enum):
    DIRECT = "direct"
    WITH_ALIGNMENT = "with_alignment"
    NO_ALIGNMENT = "no_alignment"


ALL_BASELINE_CONDITIONS = (
    BaselineCondition.DIRECT,
    BaselineCondition.WITH_ALIGNMENT,
    BaselineCondition.NO_ALIGNMENT,
)


class BaselineManifestUnit(BaseModel):
    unit_id: str
    example_dir: str


class BaselineManifest(BaseModel):
    schema_version: str = "0.1"
    baseline_id: str
    units: list[BaselineManifestUnit] = Field(default_factory=list)


@dataclass(frozen=True)
class BaselineUnit:
    unit_id: str
    example_dir: Path


@dataclass(frozen=True)
class BaselineRunResult:
    output_dir: Path
    unit_count: int
    condition_count: int


def _repo_root_from_module() -> Path:
    return Path(__file__).resolve().parents[4]


def default_baseline_manifest_path(*, repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root_from_module()
    return root / "benchmarks" / "baselines" / "manifest.json"


def resolve_baseline_conditions(*, conditions: str) -> tuple[BaselineCondition, ...]:
    normalized = conditions.strip().casefold().replace("-", "_")
    if normalized in {"all", "*"}:
        return ALL_BASELINE_CONDITIONS
    selected = tuple(BaselineCondition(token.strip()) for token in normalized.split(",") if token.strip())
    if not selected:
        raise ValueError("At least one baseline condition must be selected.")
    return selected


def load_baseline_manifest(path: Path) -> BaselineManifest:
    return BaselineManifest.model_validate_json(path.read_text(encoding="utf-8"))


def load_baseline_units(*, repo_root: Path, manifest_path: Path) -> list[BaselineUnit]:
    manifest = load_baseline_manifest(manifest_path)
    return [
        BaselineUnit(unit_id=entry.unit_id, example_dir=(repo_root / entry.example_dir).resolve())
        for entry in manifest.units
    ]


def _write_json(path: Path, payload: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload.model_dump_json(indent=2) + "\n", encoding="utf-8")


def run_baselines(
    *,
    output_dir: Path,
    model_client: StructuredModelClient,
    repo_root: Path,
    manifest_path: Path,
    run_id: str,
    conditions: tuple[BaselineCondition, ...],
    model_name: str,
) -> BaselineRunResult:
    units = load_baseline_units(repo_root=repo_root, manifest_path=manifest_path)
    index_path = default_index_path(repo_root=repo_root)
    index = load_index(index_path)
    embedding_index = load_embedding_index(index=index, index_path=index_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    for condition in conditions:
        for unit_entry in units:
            unit = load_unit(unit_entry.example_dir / "unit.json")
            unit_output = output_dir / condition.value / unit.unit_id
            unit_output.mkdir(parents=True, exist_ok=True)

            if condition == BaselineCondition.NO_ALIGNMENT:
                report = extract_readiness_report(
                    unit=unit,
                    model_client=model_client,
                    enrich_candidates=False,
                )
            elif condition == BaselineCondition.WITH_ALIGNMENT:
                report = extract_readiness_report(
                    unit=unit,
                    model_client=model_client,
                    enrich_candidates=True,
                    index=index,
                    use_index_suggestions=True,
                )
                alignment = align_readiness_report(
                    report=report,
                    index=index,
                    unit=unit,
                    embedding_index=embedding_index,
                )
                _write_json(unit_output / "alignment.json", alignment)
                report = enrich_readiness_candidates_from_alignment(
                    report=report,
                    alignment=alignment,
                )
            else:
                report = extract_readiness_report(unit=unit, model_client=model_client)

            _write_json(unit_output / "readiness_report.json", report)
            _write_json(unit_output / "proofgraph.json", extract_proofgraph(unit=unit, model_client=model_client))
            _write_json(unit_output / "atlas_record.json", extract_atlas_record(unit=unit, model_client=model_client))
            _write_json(
                unit_output / "leantask.json",
                extract_leantask_package(unit=unit, report=report, model_client=model_client),
            )

    manifest_payload: dict[str, Any] = {
        "run_id": run_id,
        "model_name": model_name,
        "conditions": [condition.value for condition in conditions],
        "units": [unit.unit_id for unit in units],
    }
    (output_dir / "run_manifest.json").write_text(json.dumps(manifest_payload, indent=2) + "\n", encoding="utf-8")
    return BaselineRunResult(output_dir=output_dir, unit_count=len(units), condition_count=len(conditions))

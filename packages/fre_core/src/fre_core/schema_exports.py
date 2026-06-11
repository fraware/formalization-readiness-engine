"""JSON Schema export utilities for public artifact contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeAlias

from pydantic import BaseModel

from fre_core.schemas import (
    AtlasRecord,
    BenchmarkEvaluationReport,
    BenchmarkManifest,
    DeclarationIndex,
    GoldArtifactChangelogEntry,
    LeanTaskPackage,
    ProofGraph,
    ReadinessReport,
    ReadinessReportReviewSubmission,
    SourceDocument,
    TheoremProofUnit,
)

SchemaModel: TypeAlias = type[BaseModel]

SCHEMA_MODELS: dict[str, SchemaModel] = {
    "source_document": SourceDocument,
    "theorem_proof_unit": TheoremProofUnit,
    "readiness_report": ReadinessReport,
    "proofgraph": ProofGraph,
    "atlas_record": AtlasRecord,
    "leantask_package": LeanTaskPackage,
    "declaration_index": DeclarationIndex,
    "benchmark_manifest": BenchmarkManifest,
    "benchmark_evaluation_report": BenchmarkEvaluationReport,
    "readiness_report_review_submission": ReadinessReportReviewSubmission,
    "gold_artifact_changelog_entry": GoldArtifactChangelogEntry,
}


def export_json_schemas(output_dir: Path) -> list[Path]:
    """Export all public artifact schemas as JSON Schema files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for name, model in SCHEMA_MODELS.items():
        path = output_dir / f"{name}.schema.json"
        schema = model.model_json_schema()
        path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)

    return written

"""Artifact-level validators for the Formalization Readiness Engine."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fre_core.schemas import AtlasRecord, LeanTaskPackage, ProofGraph, ReadinessReport, TheoremProofUnit

PROOFGRAPH_EDGE_TYPES: frozenset[str] = frozenset({
    "uses", "uses_assumption", "uses_definition", "depends_on", "blocked_by",
    "aligns_with_library_candidate", "aligns_with_library_theorem", "requires_lemma",
    "proof_strategy_step", "invokes_universal_property", "transports", "specializes",
})


@dataclass(frozen=True)
class ValidationIssue:
    """A human-readable validation issue."""

    code: str
    message: str


class ArtifactValidationError(ValueError):
    """Raised when an artifact fails semantic validation."""

    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        super().__init__(details)


def validate_proofgraph(graph: ProofGraph) -> None:
    """Validate graph-level invariants that Pydantic alone cannot check."""
    issues: list[ValidationIssue] = []
    node_ids = [node.node_id for node in graph.nodes]
    node_id_set = set(node_ids)

    if len(node_ids) != len(node_id_set):
        issues.append(ValidationIssue("duplicate_node_id", "ProofGraph node identifiers must be unique."))

    for edge in graph.edges:
        if edge.edge_type not in PROOFGRAPH_EDGE_TYPES:
            issues.append(ValidationIssue("invalid_edge_type", f"Edge type {edge.edge_type!r} is not allowed."))
        if edge.source not in node_id_set:
            issues.append(
                ValidationIssue(
                    "missing_edge_source",
                    f"Edge source {edge.source!r} does not match any node identifier.",
                )
            )
        if edge.target not in node_id_set:
            issues.append(
                ValidationIssue(
                    "missing_edge_target",
                    f"Edge target {edge.target!r} does not match any node identifier.",
                )
            )

    if issues:
        raise ArtifactValidationError(issues)


def validate_readiness_report(report: ReadinessReport) -> None:
    """Validate readiness-report semantic invariants."""
    issues: list[ValidationIssue] = []

    if not report.recommended_next_action.strip():
        issues.append(ValidationIssue("missing_next_action", "ReadinessReport needs a next action."))

    if not report.existing_theorem_candidates and not report.constructive_path:
        issues.append(
            ValidationIssue(
                "missing_formalization_path",
                "ReadinessReport should contain an existing-theorem candidate or constructive path.",
            )
        )

    if issues:
        raise ArtifactValidationError(issues)


def validate_atlas_record(record: AtlasRecord) -> None:
    """Validate Atlas-record semantic invariants."""
    issues: list[ValidationIssue] = []

    if not record.evidence.strip():
        issues.append(ValidationIssue("missing_evidence", "AtlasRecord needs source-grounded evidence."))
    if not record.recommended_action.strip():
        issues.append(ValidationIssue("missing_recommended_action", "AtlasRecord needs an action."))

    if issues:
        raise ArtifactValidationError(issues)


def validate_leantask_package(task: LeanTaskPackage) -> None:
    """Validate LeanTask semantic invariants."""
    issues: list[ValidationIssue] = []

    if not task.next_action.strip():
        issues.append(ValidationIssue("missing_next_action", "LeanTaskPackage needs a next action."))
    if task.level.value in {"L1", "L2"} and not task.formal_target:
        issues.append(
            ValidationIssue("missing_formal_target", "L1/L2 LeanTaskPackage needs a formal target.")
        )

    if issues:
        raise ArtifactValidationError(issues)


def load_unit(path: Path) -> TheoremProofUnit:
    return TheoremProofUnit.model_validate_json(path.read_text(encoding="utf-8"))


def load_readiness_report(path: Path) -> ReadinessReport:
    report = ReadinessReport.model_validate_json(path.read_text(encoding="utf-8"))
    validate_readiness_report(report)
    return report


def load_proofgraph(path: Path) -> ProofGraph:
    graph = ProofGraph.model_validate_json(path.read_text(encoding="utf-8"))
    validate_proofgraph(graph)
    return graph


def load_atlas_record(path: Path) -> AtlasRecord:
    record = AtlasRecord.model_validate_json(path.read_text(encoding="utf-8"))
    validate_atlas_record(record)
    return record


def load_leantask_package(path: Path) -> LeanTaskPackage:
    task = LeanTaskPackage.model_validate_json(path.read_text(encoding="utf-8"))
    validate_leantask_package(task)
    return task

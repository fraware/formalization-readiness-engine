"""Artifact-level validators for the Formalization Readiness Engine."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fre_core.schemas import (
    AtlasBlockerType,
    AtlasRecord,
    LeanTaskPackage,
    ProofGraph,
    ProofGraphNodeType,
    ReadinessDimensionStatus,
    ReadinessReport,
    ReviewStatus,
    TheoremProofUnit,
)

ValidationMode = Literal["strict", "permissive", "public_export"]
ValidationProfile = Literal["candidate", "reviewed", "public_export"]

PROOFGRAPH_EDGE_TYPES: frozenset[str] = frozenset({
    "uses", "uses_assumption", "uses_definition", "depends_on", "blocked_by",
    "aligns_with_library_candidate", "aligns_with_library_theorem", "requires_lemma",
    "proof_strategy_step", "invokes_universal_property", "transports", "specializes",
})

STRICT_REVIEW_STATUSES: frozenset[ReviewStatus] = frozenset({
    ReviewStatus.EXPERT_REVIEWED,
    ReviewStatus.HUMAN_REVIEWED,
    ReviewStatus.MACHINE_VALIDATED,
})

KNOWN_PROOFGRAPH_NODE_TYPES_STRICT: frozenset[str] = frozenset(
    member.value for member in ProofGraphNodeType
    if member
    in {
        ProofGraphNodeType.THEOREM_STATEMENT,
        ProofGraphNodeType.ASSUMPTION,
        ProofGraphNodeType.LIBRARY_CANDIDATE,
        ProofGraphNodeType.PROOF_STRATEGY,
        ProofGraphNodeType.PROOF_STEP,
        ProofGraphNodeType.BLOCKER,
    }
)

KNOWN_PROOFGRAPH_NODE_TYPES_PERMISSIVE: frozenset[str] = frozenset(
    member.value for member in ProofGraphNodeType
)

KNOWN_ATLAS_BLOCKER_TYPES_STRICT: frozenset[str] = frozenset(
    member.value
    for member in AtlasBlockerType
    if member != AtlasBlockerType.OTHER
)

KNOWN_READINESS_DIMENSION_STATUSES: frozenset[str] = frozenset(
    member.value for member in ReadinessDimensionStatus
)


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


def validation_mode_for_review_status(review_status: ReviewStatus) -> ValidationMode:
    """Return strict validation for reviewed artifacts and permissive for candidates."""
    if review_status in STRICT_REVIEW_STATUSES:
        return "strict"
    return "permissive"


def validation_mode_for_profile(profile: ValidationProfile) -> ValidationMode:
    """Map a named validation profile to a validation mode.

    Profiles:
    - ``candidate``: permissive checks for model output and bronze artifacts.
    - ``reviewed``: strict enum enforcement for human- or expert-reviewed artifacts.
    - ``public_export``: strict checks used before ReadinessBench export and gold/silver validation.
    """
    if profile == "candidate":
        return "permissive"
    if profile == "reviewed":
        return "strict"
    return "public_export"


def _is_strict_mode(mode: ValidationMode) -> bool:
    return mode in {"strict", "public_export"}


def _validate_readiness_dimension_statuses(
    report: ReadinessReport,
    *,
    mode: ValidationMode,
    issues: list[ValidationIssue],
) -> None:
    for field_name in (
        "statement_readiness",
        "context_readiness",
        "notation_readiness",
        "dependency_readiness",
    ):
        dimension = getattr(report, field_name)
        if dimension.status not in KNOWN_READINESS_DIMENSION_STATUSES:
            issues.append(
                ValidationIssue(
                    "invalid_dimension_status",
                    f"{field_name}.status {dimension.status!r} is not a known readiness status.",
                )
            )
        elif _is_strict_mode(mode) and dimension.status == ReadinessDimensionStatus.PENDING.value:
            issues.append(
                ValidationIssue(
                    "pending_dimension_status",
                    f"{field_name}.status must not be pending for reviewed or exported artifacts.",
                )
            )


def validate_proofgraph(graph: ProofGraph, *, mode: ValidationMode | None = None) -> None:
    """Validate graph-level invariants that Pydantic alone cannot check."""
    issues: list[ValidationIssue] = []
    resolved_mode = mode or validation_mode_for_review_status(graph.review_status)
    node_ids = [node.node_id for node in graph.nodes]
    node_id_set = set(node_ids)
    allowed_node_types = (
        KNOWN_PROOFGRAPH_NODE_TYPES_STRICT
        if _is_strict_mode(resolved_mode)
        else KNOWN_PROOFGRAPH_NODE_TYPES_PERMISSIVE
    )

    if len(node_ids) != len(node_id_set):
        issues.append(ValidationIssue("duplicate_node_id", "ProofGraph node identifiers must be unique."))

    for node in graph.nodes:
        if _is_strict_mode(resolved_mode) and node.node_type not in allowed_node_types:
            issues.append(
                ValidationIssue(
                    "invalid_node_type",
                    f"Node {node.node_id!r} has unsupported node_type {node.node_type!r}.",
                )
            )

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


def validate_readiness_report(report: ReadinessReport, *, mode: ValidationMode | None = None) -> None:
    """Validate readiness-report semantic invariants."""
    issues: list[ValidationIssue] = []
    resolved_mode = mode or validation_mode_for_review_status(report.review_status)

    if not report.recommended_next_action.strip():
        issues.append(ValidationIssue("missing_next_action", "ReadinessReport needs a next action."))

    if not report.existing_theorem_candidates and not report.constructive_path:
        issues.append(
            ValidationIssue(
                "missing_formalization_path",
                "ReadinessReport should contain an existing-theorem candidate or constructive path.",
            )
        )

    _validate_readiness_dimension_statuses(report, mode=resolved_mode, issues=issues)

    if issues:
        raise ArtifactValidationError(issues)


def validate_atlas_record(record: AtlasRecord, *, mode: ValidationMode | None = None) -> None:
    """Validate Atlas-record semantic invariants."""
    issues: list[ValidationIssue] = []
    resolved_mode = mode or validation_mode_for_review_status(record.review_status)

    if not record.evidence.strip():
        issues.append(ValidationIssue("missing_evidence", "AtlasRecord needs source-grounded evidence."))
    if not record.recommended_action.strip():
        issues.append(ValidationIssue("missing_recommended_action", "AtlasRecord needs an action."))

    if _is_strict_mode(resolved_mode):
        if record.blocker_type not in KNOWN_ATLAS_BLOCKER_TYPES_STRICT:
            issues.append(
                ValidationIssue(
                    "invalid_blocker_type",
                    f"Atlas blocker_type {record.blocker_type!r} is not in the controlled vocabulary.",
                )
            )
    elif record.blocker_type == AtlasBlockerType.OTHER.value and not (record.evidence or "").strip():
        issues.append(
            ValidationIssue(
                "missing_other_blocker_evidence",
                "Atlas blocker_type 'other' requires source-grounded evidence.",
            )
        )

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
    if task.level.value == "L2":
        if not task.alignment_declarations:
            issues.append(
                ValidationIssue(
                    "missing_alignment_declarations",
                    "L2 LeanTaskPackage needs at least one alignment declaration.",
                )
            )
        if not task.sub_lemmas:
            issues.append(
                ValidationIssue(
                    "missing_sub_lemmas",
                    "L2 LeanTaskPackage needs at least one sub-lemma for decomposition.",
                )
            )
        sub_lemma_ids = [sub_lemma.lemma_id for sub_lemma in task.sub_lemmas]
        if len(sub_lemma_ids) != len(set(sub_lemma_ids)):
            issues.append(
                ValidationIssue("duplicate_sub_lemma_id", "L2 sub-lemma identifiers must be unique.")
            )
        for sub_lemma in task.sub_lemmas:
            if not sub_lemma.statement.strip():
                issues.append(
                    ValidationIssue(
                        "missing_sub_lemma_statement",
                        f"Sub-lemma {sub_lemma.lemma_id!r} needs a statement.",
                    )
                )

    if issues:
        raise ArtifactValidationError(issues)


def _validate_unit_spans(unit: TheoremProofUnit, *, source_text: str | None = None) -> None:
    issues: list[ValidationIssue] = []
    if source_text is None:
        return
    for field_name, span in (
        ("statement_span", unit.statement_span),
        ("proof_span", unit.proof_span),
    ):
        if span is None:
            continue
        if span.end > len(source_text):
            issues.append(
                ValidationIssue(
                    "span_out_of_range",
                    f"{field_name} end {span.end} exceeds source text length {len(source_text)}.",
                )
            )
    if issues:
        raise ArtifactValidationError(issues)


def load_unit(path: Path, *, source_text: str | None = None) -> TheoremProofUnit:
    unit = TheoremProofUnit.model_validate_json(path.read_text(encoding="utf-8"))
    _validate_unit_spans(unit, source_text=source_text)
    return unit


def load_readiness_report(path: Path, *, mode: ValidationMode | None = None) -> ReadinessReport:
    report = ReadinessReport.model_validate_json(path.read_text(encoding="utf-8"))
    validate_readiness_report(report, mode=mode)
    return report


def load_proofgraph(path: Path, *, mode: ValidationMode | None = None) -> ProofGraph:
    graph = ProofGraph.model_validate_json(path.read_text(encoding="utf-8"))
    validate_proofgraph(graph, mode=mode)
    return graph


def load_atlas_record(path: Path, *, mode: ValidationMode | None = None) -> AtlasRecord:
    record = AtlasRecord.model_validate_json(path.read_text(encoding="utf-8"))
    validate_atlas_record(record, mode=mode)
    return record


def load_leantask_package(path: Path) -> LeanTaskPackage:
    task = LeanTaskPackage.model_validate_json(path.read_text(encoding="utf-8"))
    validate_leantask_package(task)
    return task

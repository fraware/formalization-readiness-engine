"""Versioned artifact schemas for the Formalization Readiness Engine."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ReviewStatus(str, Enum):
    CANDIDATE = "candidate"
    MACHINE_VALIDATED = "machine_validated"
    HUMAN_REVIEWED = "human_reviewed"
    EXPERT_REVIEWED = "expert_reviewed"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class LeanTaskLevel(str, Enum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"


class SourceDocument(BaseModel):
    source_id: str
    source_type: str
    license_status: str
    release_mode: str
    domain: str
    path: str


class SourceSpan(BaseModel):
    start: int = Field(ge=0)
    end: int = Field(ge=0)


class TheoremProofUnit(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    unit_id: str
    source_id: str
    statement: str
    proof: str | None = None
    local_context: str | None = None
    domain: str
    statement_span: SourceSpan | None = None
    proof_span: SourceSpan | None = None
    review_status: ReviewStatus = ReviewStatus.CANDIDATE


class ReadinessDimension(BaseModel):
    status: str
    recovered: list[str] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)
    notes: str | None = None


class ReadinessReport(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    unit_id: str
    statement_readiness: ReadinessDimension
    context_readiness: ReadinessDimension
    notation_readiness: ReadinessDimension
    dependency_readiness: ReadinessDimension
    existing_theorem_candidates: list[str] = Field(default_factory=list)
    constructive_path: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    recommended_next_action: str
    review_status: ReviewStatus = ReviewStatus.CANDIDATE


class ProofGraphNode(BaseModel):
    node_id: str
    node_type: str
    text: str
    source_span: SourceSpan | None = None


class ProofGraphEdge(BaseModel):
    source: str
    target: str
    edge_type: str


class ProofGraph(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    unit_id: str
    nodes: list[ProofGraphNode]
    edges: list[ProofGraphEdge]
    review_status: ReviewStatus = ReviewStatus.CANDIDATE


class AtlasRecord(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    unit_id: str
    blocker_type: str
    mathematical_pattern: str
    evidence: str
    candidate_formal_object: str | None = None
    likely_library_location: str | None = None
    severity: Literal["low", "medium", "high"]
    status: str
    recommended_action: str
    review_status: ReviewStatus = ReviewStatus.CANDIDATE


class LeanTaskPackage(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    leantask_id: str
    unit_id: str
    level: LeanTaskLevel
    informal_statement: str
    imports: list[str] = Field(default_factory=list)
    formal_target: str | None = None
    hypotheses: list[str] = Field(default_factory=list)
    proof_path: str | None = None
    fallback_path: str | None = None
    next_action: str
    review_status: ReviewStatus = ReviewStatus.CANDIDATE


class MathlibDeclaration(BaseModel):
    """One Lean/mathlib declaration entry in a reproducible lookup index."""

    declaration_id: str
    full_name: str
    namespace: str
    module: str
    kind: Literal["theorem", "def", "instance", "abbrev", "structure", "class", "inductive"]
    type_signature: str | None = None
    docstring: str | None = None


class DeclarationIndex(BaseModel):
    """Versioned index of mathlib declarations for lexical candidate lookup."""

    schema_version: Literal["0.1"] = "0.1"
    index_id: str
    description: str | None = None
    declarations: list[MathlibDeclaration] = Field(default_factory=list)


class BenchmarkTier(str, Enum):
    """ReadinessBench data tier."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


class BenchmarkItem(BaseModel):
    """One benchmark item with explicit tier and artifact paths."""

    item_id: str
    unit_id: str
    tier: BenchmarkTier
    unit_path: str
    readiness_report_path: str


class BenchmarkManifest(BaseModel):
    """Manifest listing ReadinessBench items and their tier placement."""

    schema_version: Literal["0.1"] = "0.1"
    benchmark_id: str
    items: list[BenchmarkItem] = Field(default_factory=list)


class BenchmarkItemScore(BaseModel):
    """Deterministic scores for one gold benchmark item."""

    item_id: str
    unit_id: str
    macro_f1: float
    existing_theorem_candidates_f1: float
    constructive_path_f1: float
    blockers_f1: float


class BenchmarkEvaluationReport(BaseModel):
    """Aggregate ReadinessBench evaluation output."""

    schema_version: Literal["0.1"] = "0.1"
    benchmark_id: str
    gold_item_count: int
    scored_item_count: int
    items: list[BenchmarkItemScore] = Field(default_factory=list)
    macro_f1_mean: float


class ReadinessDimensionReview(BaseModel):
    """Reviewer assessment of one ReadinessReport dimension field group."""

    status_accurate: bool
    recovered_accurate: bool
    unresolved_accurate: bool
    notes: str | None = None


class UsefulnessRubricScores(BaseModel):
    """External-usefulness rubric scores (1 = poor, 5 = excellent)."""

    source_fidelity: int = Field(ge=1, le=5)
    actionability: int = Field(ge=1, le=5)
    library_alignment: int = Field(ge=1, le=5)
    blocker_specificity: int = Field(ge=1, le=5)
    path_clarity: int = Field(ge=1, le=5)


class ReadinessReportDimensionReviews(BaseModel):
    """Per-dimension review flags aligned with ReadinessReport schema fields."""

    statement_readiness: ReadinessDimensionReview
    context_readiness: ReadinessDimensionReview
    notation_readiness: ReadinessDimensionReview
    dependency_readiness: ReadinessDimensionReview


class ReadinessReportReviewSubmission(BaseModel):
    """Structured external review output for one theorem/proof unit."""

    schema_version: Literal["0.1"] = "0.1"
    unit_id: str
    item_id: str | None = None
    reviewer_id: str
    review_date: str
    tier_promotion: Literal["silver", "gold"] | None = None
    review_status: ReviewStatus
    rubric_scores: UsefulnessRubricScores
    dimension_reviews: ReadinessReportDimensionReviews
    list_fields_accurate: bool
    recommended_next_action_accurate: bool
    corrected_report_path: str | None = None
    corrected_report: ReadinessReport | None = None
    notes: str | None = None


class GoldArtifactChangelogEntry(BaseModel):
    """Auditable record of a change to a ReadinessBench gold artifact."""

    date: str
    item_id: str
    reviewer_id: str
    summary: str
    fields_changed: list[str] = Field(default_factory=list)
    review_submission_path: str | None = None


class AlignmentCandidate(BaseModel):
    """One mathlib declaration match proposed or confirmed for a readiness report."""

    declaration_id: str
    full_name: str
    namespace: str
    module: str
    kind: str
    score: int
    match_reasons: list[str] = Field(default_factory=list)
    query_source: str
    alignment_status: Literal["candidate", "confirmed"] = "candidate"


class AlignmentResult(BaseModel):
    """Alignment output separating reviewer-confirmed matches from proposed candidates."""

    schema_version: Literal["0.1"] = "0.1"
    unit_id: str
    index_id: str
    candidates: list[AlignmentCandidate] = Field(default_factory=list)
    confirmed: list[AlignmentCandidate] = Field(default_factory=list)


class PublicBenchmarkExportRecord(BaseModel):
    """One ReadinessBench item in a public JSONL export."""

    schema_version: Literal["0.1"] = "0.1"
    record_type: Literal["benchmark_item"] = "benchmark_item"
    item_id: str
    unit_id: str
    tier: str
    unit: TheoremProofUnit
    readiness_report: ReadinessReport


class PublicAtlasExportRecord(BaseModel):
    """One Atlas record in a public JSONL export."""

    schema_version: Literal["0.1"] = "0.1"
    record_type: Literal["atlas"] = "atlas"
    unit_id: str
    source_id: str | None = None
    domain: str | None = None
    atlas_record: AtlasRecord
    unit: TheoremProofUnit | None = None


class PublicExportManifest(BaseModel):
    """Manifest describing a public JSONL export."""

    schema_version: Literal["0.1"] = "0.1"
    export_id: str
    export_type: Literal["readinessbench", "atlas"]
    record_count: int
    output_path: str
    description: str | None = None

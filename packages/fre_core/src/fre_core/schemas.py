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

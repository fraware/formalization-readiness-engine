"""Semantic-aware ReadinessBench evaluation (v0.3 metrics layer).

Complements lexical v0.2 overlap scoring with declaration-ID resolution,
controlled-vocabulary blocker alignment, and normalized ProofGraph typing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from fre_core.artifact_normalization import normalize_atlas_blocker_type, normalize_proofgraph
from fre_core.evaluation import PrecisionRecallF1, score_label_set, score_readiness_report
from fre_core.evaluation_atlas import score_atlas_record
from fre_core.evaluation_proofgraph import score_proofgraph
from fre_core.mathlib_index import default_index_path, load_index, lookup_declaration
from fre_core.schemas import (
    AtlasRecord,
    DeclarationIndex,
    ProofGraph,
    ReadinessReport,
)


def _repo_root_from_module() -> Path:
    return Path(__file__).resolve().parents[4]


def default_equivalence_dir(*, repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root_from_module()
    return root / "benchmarks" / "readinessbench" / "equivalence"


def default_index_path_for_unit(*, unit_id: str, repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root_from_module()
    if "category_theory" in unit_id:
        return root / "fixtures" / "mathlib_declarations" / "category_theory_v0.json"
    if "finite_tree" in unit_id:
        return root / "fixtures" / "mathlib_declarations" / "finite_tree_v0.json"
    return default_index_path(repo_root=root)


def _normalize_declaration_candidate(value: str) -> str:
    stripped = value.strip()
    if stripped.casefold().startswith("mathlib:"):
        return stripped.split(":", 1)[1].strip()
    return stripped


def _normalize_identity_key(value: str) -> str:
    return _normalize_declaration_candidate(value).casefold()


def _candidate_identity(*, candidate: str, index: DeclarationIndex | None) -> str:
    normalized = _normalize_declaration_candidate(candidate)
    if index is not None:
        declaration = lookup_declaration(index=index, candidate=normalized)
        if declaration is not None:
            return _normalize_identity_key(declaration.full_name)
    return _normalize_identity_key(normalized)


def _load_equivalence_groups(
    *,
    unit_id: str,
    equivalence_dir: Path,
) -> list[frozenset[str]]:
    path = equivalence_dir / f"{unit_id}.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    groups: list[frozenset[str]] = []
    for group in payload.get("theorem_candidate_groups", []):
        if not isinstance(group, list):
            continue
        identities = {
            _normalize_identity_key(str(entry))
            for entry in group
            if str(entry).strip()
        }
        if identities:
            groups.append(frozenset(identities))
    return groups


def _canonical_group_key(identity: str, groups: list[frozenset[str]]) -> str:
    normalized = _normalize_identity_key(identity)
    for group in groups:
        if normalized in group:
            return min(group)
    return normalized


def score_theorem_candidates_declaration_id(
    *,
    predicted: list[str],
    gold: list[str],
    index: DeclarationIndex | None,
    equivalence_groups: list[frozenset[str]] | None = None,
) -> PrecisionRecallF1:
    """Score theorem candidates by declaration identity with optional alias groups."""
    groups = equivalence_groups or []

    def to_keys(candidates: list[str]) -> set[str]:
        keys: set[str] = set()
        for candidate in candidates:
            identity = _candidate_identity(candidate=candidate, index=index)
            keys.add(_canonical_group_key(identity, groups))
        return keys

    predicted_set = to_keys(predicted)
    gold_set = to_keys(gold)
    true_positives = len(predicted_set & gold_set)
    precision = true_positives / len(predicted_set) if predicted_set else 1.0 if not gold_set else 0.0
    recall = true_positives / len(gold_set) if gold_set else 1.0 if not predicted_set else 0.0
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return PrecisionRecallF1(
        precision=precision,
        recall=recall,
        f1=f1,
        true_positives=true_positives,
        predicted_count=len(predicted_set),
        gold_count=len(gold_set),
    )


def score_blockers_ontology(*, predicted: list[str], gold: list[str]) -> PrecisionRecallF1:
    """Map readiness blockers to Atlas blocker ontology labels before scoring."""
    predicted_types = [
        normalize_atlas_blocker_type(blocker)[0]
        for blocker in predicted
        if blocker.strip()
    ]
    gold_types = [
        normalize_atlas_blocker_type(blocker)[0]
        for blocker in gold
        if blocker.strip()
    ]
    return score_label_set(predicted=predicted_types, gold=gold_types)


def score_proofgraph_normalized_types(*, predicted: ProofGraph, gold: ProofGraph) -> PrecisionRecallF1:
    """Score ProofGraph node types after public-export normalization."""
    predicted_graph = normalize_proofgraph(predicted)
    gold_graph = normalize_proofgraph(gold)
    return score_label_set(
        predicted=[node.node_type for node in predicted_graph.nodes],
        gold=[node.node_type for node in gold_graph.nodes],
    )


def score_atlas_blocker_type_normalized(*, predicted: AtlasRecord, gold: AtlasRecord) -> PrecisionRecallF1:
    """Score atlas blocker_type after controlled-vocabulary normalization."""
    from fre_core.artifact_normalization import normalize_atlas_record

    predicted_type = normalize_atlas_record(predicted).blocker_type
    gold_type = normalize_atlas_record(gold).blocker_type
    match = predicted_type.casefold() == gold_type.casefold()
    f1 = 1.0 if match else 0.0
    return PrecisionRecallF1(
        precision=f1,
        recall=f1,
        f1=f1,
        true_positives=int(match),
        predicted_count=1,
        gold_count=1,
    )


@dataclass(frozen=True)
class V03ReadinessScores:
    """v0.3 semantic scores for one readiness report pair."""

    theorem_candidates_declaration_f1: float
    blockers_ontology_f1: float
    lexical_macro_f1: float

    @property
    def macro_f1(self) -> float:
        return (
            self.theorem_candidates_declaration_f1
            + self.blockers_ontology_f1
            + self.lexical_macro_f1
        ) / 3


def score_readiness_report_v03(
    *,
    predicted: ReadinessReport,
    gold: ReadinessReport,
    index: DeclarationIndex | None = None,
    equivalence_dir: Path | None = None,
) -> V03ReadinessScores:
    """Compute v0.3 semantic metrics for one predicted vs gold readiness report."""
    if predicted.unit_id != gold.unit_id:
        raise ValueError(f"Unit mismatch: predicted={predicted.unit_id!r}, gold={gold.unit_id!r}")

    equivalence_path = equivalence_dir or default_equivalence_dir()
    equivalence_groups = _load_equivalence_groups(unit_id=gold.unit_id, equivalence_dir=equivalence_path)
    lexical = score_readiness_report(predicted=predicted, gold=gold)
    theorem_scores = score_theorem_candidates_declaration_id(
        predicted=predicted.existing_theorem_candidates,
        gold=gold.existing_theorem_candidates,
        index=index,
        equivalence_groups=equivalence_groups,
    )
    blocker_scores = score_blockers_ontology(predicted=predicted.blockers, gold=gold.blockers)
    return V03ReadinessScores(
        theorem_candidates_declaration_f1=theorem_scores.f1,
        blockers_ontology_f1=blocker_scores.f1,
        lexical_macro_f1=lexical.macro_f1,
    )


def score_v03_metrics(
    *,
    predicted_report: ReadinessReport,
    gold_report: ReadinessReport,
    predicted_proofgraph: ProofGraph | None = None,
    gold_proofgraph: ProofGraph | None = None,
    predicted_atlas: AtlasRecord | None = None,
    gold_atlas: AtlasRecord | None = None,
    repo_root: Path | None = None,
) -> dict[str, float]:
    """Aggregate v0.3 metrics for one benchmark item."""
    root = repo_root or _repo_root_from_module()
    index_path = default_index_path_for_unit(unit_id=gold_report.unit_id, repo_root=root)
    index = load_index(index_path) if index_path.is_file() else None

    readiness = score_readiness_report_v03(
        predicted=predicted_report,
        gold=gold_report,
        index=index,
    )
    metrics: dict[str, float] = {
        "theorem_candidates_declaration_f1": round(readiness.theorem_candidates_declaration_f1, 6),
        "blockers_ontology_f1": round(readiness.blockers_ontology_f1, 6),
        "readiness_lexical_macro_f1": round(readiness.lexical_macro_f1, 6),
        "readiness_v03_macro_f1": round(readiness.macro_f1, 6),
    }

    if predicted_proofgraph is not None and gold_proofgraph is not None:
        graph_type_scores = score_proofgraph_normalized_types(
            predicted=predicted_proofgraph,
            gold=gold_proofgraph,
        )
        graph_scores = score_proofgraph(predicted=predicted_proofgraph, gold=gold_proofgraph)
        metrics["proofgraph_node_type_f1"] = round(graph_type_scores.f1, 6)
        metrics["proofgraph_lexical_macro_f1"] = round(graph_scores.macro_f1, 6)

    if predicted_atlas is not None and gold_atlas is not None:
        atlas_type_scores = score_atlas_blocker_type_normalized(predicted=predicted_atlas, gold=gold_atlas)
        atlas_scores = score_atlas_record(predicted=predicted_atlas, gold=gold_atlas)
        metrics["atlas_blocker_type_f1"] = round(atlas_type_scores.f1, 6)
        metrics["atlas_lexical_f1"] = round(atlas_scores.f1, 6)

    v03_values = [
        metrics["theorem_candidates_declaration_f1"],
        metrics["blockers_ontology_f1"],
    ]
    if "proofgraph_node_type_f1" in metrics:
        v03_values.append(metrics["proofgraph_node_type_f1"])
    if "atlas_blocker_type_f1" in metrics:
        v03_values.append(metrics["atlas_blocker_type_f1"])
    metrics["v03_macro_f1"] = round(sum(v03_values) / len(v03_values), 6)
    return metrics

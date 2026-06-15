"""Normalize model-extracted ProofGraph and Atlas artifacts to public-export vocabulary."""

from __future__ import annotations

import re

from fre_core.schemas import AtlasBlockerType, AtlasRecord, ProofGraph, ProofGraphNode, ProofGraphNodeType
from fre_core.validation import KNOWN_ATLAS_BLOCKER_TYPES_STRICT, KNOWN_PROOFGRAPH_NODE_TYPES_STRICT

_STRICT_PROOFGRAPH_TYPES: frozenset[str] = KNOWN_PROOFGRAPH_NODE_TYPES_STRICT

_PROOFGRAPH_NODE_TYPE_SYNONYMS: dict[str, str] = {
    ProofGraphNodeType.THEOREM.value: ProofGraphNodeType.THEOREM_STATEMENT.value,
    ProofGraphNodeType.CONSTRUCTION_STEP.value: ProofGraphNodeType.PROOF_STEP.value,
    ProofGraphNodeType.APPLICATION_STEP.value: ProofGraphNodeType.PROOF_STEP.value,
    ProofGraphNodeType.DERIVED_FACT.value: ProofGraphNodeType.PROOF_STEP.value,
    ProofGraphNodeType.ANALYSIS.value: ProofGraphNodeType.PROOF_STEP.value,
    ProofGraphNodeType.CALCULATION.value: ProofGraphNodeType.PROOF_STEP.value,
    ProofGraphNodeType.BASE_CASE.value: ProofGraphNodeType.PROOF_STEP.value,
    ProofGraphNodeType.INDUCTIVE_STEP.value: ProofGraphNodeType.PROOF_STEP.value,
    ProofGraphNodeType.JUSTIFICATION.value: ProofGraphNodeType.PROOF_STEP.value,
    ProofGraphNodeType.LEMMA.value: ProofGraphNodeType.LIBRARY_CANDIDATE.value,
    ProofGraphNodeType.DEFINITION.value: ProofGraphNodeType.ASSUMPTION.value,
}

_ATLAS_BLOCKER_SYNONYMS: dict[str, str] = {
    "definition-gap": AtlasBlockerType.NOTATION_ALIGNMENT.value,
    "definition_gap": AtlasBlockerType.NOTATION_ALIGNMENT.value,
    "definition gap": AtlasBlockerType.NOTATION_ALIGNMENT.value,
    "notation": AtlasBlockerType.NOTATION_ALIGNMENT.value,
    "notation_gap": AtlasBlockerType.NOTATION_ALIGNMENT.value,
    "library": AtlasBlockerType.LIBRARY_ALIGNMENT.value,
    "library_gap": AtlasBlockerType.LIBRARY_ALIGNMENT.value,
    "library_alignment": AtlasBlockerType.LIBRARY_ALIGNMENT.value,
    "notation_alignment": AtlasBlockerType.NOTATION_ALIGNMENT.value,
}

_NOTATION_KEYWORDS = frozenset({
    "notation",
    "definition",
    "symbol",
    "transport",
    "equivalence",
    "isomorphism",
    "cone",
    "unique",
    "up_to",
})

_LIBRARY_KEYWORDS = frozenset({
    "library",
    "mathlib",
    "import",
    "module",
    "declaration",
    "theorem",
    "lemma",
})


def _normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def normalize_proofgraph_node_type(raw_type: str) -> tuple[str, str | None]:
    """Map a model node type to the public-export ProofGraph vocabulary."""
    stripped = raw_type.strip()
    if not stripped:
        return ProofGraphNodeType.BLOCKER.value, raw_type

    if stripped in _STRICT_PROOFGRAPH_TYPES:
        return stripped, None

    direct = _PROOFGRAPH_NODE_TYPE_SYNONYMS.get(stripped)
    if direct is not None:
        return direct, stripped

    normalized_key = _normalize_token(stripped)
    for synonym, canonical in _PROOFGRAPH_NODE_TYPE_SYNONYMS.items():
        if _normalize_token(synonym) == normalized_key:
            return canonical, stripped

    return ProofGraphNodeType.BLOCKER.value, stripped


def normalize_proofgraph(graph: ProofGraph) -> ProofGraph:
    """Normalize ProofGraph node types and preserve raw labels for audit."""
    normalized_nodes: list[ProofGraphNode] = []
    for node in graph.nodes:
        canonical_type, raw_type = normalize_proofgraph_node_type(node.node_type)
        update: dict[str, object] = {"node_type": canonical_type}
        if raw_type is not None and raw_type != canonical_type:
            update["raw_node_type"] = raw_type
        elif node.raw_node_type is not None:
            update["raw_node_type"] = node.raw_node_type
        normalized_nodes.append(node.model_copy(update=update))
    return graph.model_copy(update={"nodes": normalized_nodes})


def normalize_atlas_blocker_type(raw_type: str) -> tuple[str, str | None]:
    """Map a free-form atlas blocker label to the controlled vocabulary."""
    stripped = raw_type.strip()
    if not stripped:
        return AtlasBlockerType.OTHER.value, raw_type

    if stripped in KNOWN_ATLAS_BLOCKER_TYPES_STRICT:
        return stripped, None

    lowered = stripped.casefold()
    if lowered in _ATLAS_BLOCKER_SYNONYMS:
        canonical = _ATLAS_BLOCKER_SYNONYMS[lowered]
        return canonical, stripped if canonical != stripped else None

    normalized_key = _normalize_token(stripped)
    for synonym, canonical in _ATLAS_BLOCKER_SYNONYMS.items():
        if _normalize_token(synonym) == normalized_key:
            return canonical, stripped

    tokens = set(_normalize_token(stripped).split("_"))
    if tokens & _LIBRARY_KEYWORDS:
        return AtlasBlockerType.LIBRARY_ALIGNMENT.value, stripped
    if tokens & _NOTATION_KEYWORDS:
        return AtlasBlockerType.NOTATION_ALIGNMENT.value, stripped

    if any(keyword in lowered for keyword in ("mathlib", "library", "module", "import")):
        return AtlasBlockerType.LIBRARY_ALIGNMENT.value, stripped
    if any(keyword in lowered for keyword in ("notation", "definition", "symbol", "equivalence", "isomorphism")):
        return AtlasBlockerType.NOTATION_ALIGNMENT.value, stripped

    return AtlasBlockerType.NOTATION_ALIGNMENT.value, stripped


def normalize_atlas_record(record: AtlasRecord) -> AtlasRecord:
    """Normalize atlas blocker_type and preserve the model label when mapped."""
    canonical_type, raw_type = normalize_atlas_blocker_type(record.blocker_type)
    update: dict[str, object] = {"blocker_type": canonical_type}
    if raw_type is not None and raw_type != canonical_type:
        update["blocker_type_raw"] = raw_type
    elif record.blocker_type_raw is not None:
        update["blocker_type_raw"] = record.blocker_type_raw
    return record.model_copy(update=update)

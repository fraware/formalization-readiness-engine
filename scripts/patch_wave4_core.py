#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "packages" / "fre_core" / "src" / "fre_core"


def patch_schemas() -> None:
    path = CORE / "schemas.py"
    text = path.read_text(encoding="utf-8")
    old = "    corrected_report: ReadinessReport | None = None\n    notes: str | None = None"
    new = (
        "    corrected_report: ReadinessReport | None = None\n"
        "    confirmed_alignment_full_names: list[str] = Field(default_factory=list)\n"
        "    suggested_import_modules: list[str] = Field(default_factory=list)\n"
        "    notes: str | None = None"
    )
    if "confirmed_alignment_full_names" not in text:
        path.write_text(text.replace(old, new), encoding="utf-8")


def patch_validation() -> None:
    path = CORE / "validation.py"
    text = path.read_text(encoding="utf-8")
    if "PROOFGRAPH_EDGE_TYPES" in text:
        return
    text = text.replace(
        "from fre_core.schemas import AtlasRecord, LeanTaskPackage, ProofGraph, ReadinessReport, TheoremProofUnit\n\n\n@dataclass",
        '''from fre_core.schemas import AtlasRecord, LeanTaskPackage, ProofGraph, ReadinessReport, TheoremProofUnit

PROOFGRAPH_EDGE_TYPES: frozenset[str] = frozenset({
    "uses", "uses_assumption", "uses_definition", "depends_on", "blocked_by",
    "aligns_with_library_candidate", "aligns_with_library_theorem", "requires_lemma",
    "proof_strategy_step", "invokes_universal_property", "transports", "specializes",
})


@dataclass''',
    )
    text = text.replace(
        "    for edge in graph.edges:\n        if edge.source not in node_id_set:",
        """    for edge in graph.edges:
        if edge.edge_type not in PROOFGRAPH_EDGE_TYPES:
            issues.append(ValidationIssue("invalid_edge_type", f"Edge type {edge.edge_type!r} is not allowed."))
        if edge.source not in node_id_set:""",
    )
    path.write_text(text, encoding="utf-8")


def patch_mathlib_index() -> None:
    path = CORE / "mathlib_index.py"
    text = path.read_text(encoding="utf-8")
    if "trimmed_index_path" in text:
        return
    text = text.replace(
        '    return root / "fixtures" / "mathlib_declarations" / "finite_tree_v0.json"\n\n\ndef _repo_root_from_module',
        '''    return root / "fixtures" / "mathlib_declarations" / "finite_tree_v0.json"


def trimmed_index_path(*, repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root_from_module()
    return root / "fixtures" / "mathlib_declarations" / "mathlib_v4.8.0.json"


def _repo_root_from_module''',
    )
    path.write_text(text, encoding="utf-8")


def patch_mathlib_alignment() -> None:
    path = CORE / "mathlib_alignment.py"
    text = path.read_text(encoding="utf-8")
    if "suggest_import_modules_from_alignment" in text:
        return
    text = text.replace(
        "from dataclasses import dataclass\n\nfrom fre_core.mathlib_index import (",
        "from dataclasses import dataclass\n\nfrom fre_core.embedding_index import EmbeddingIndex, StubEmbeddingIndex\nfrom fre_core.mathlib_index import (",
    )
    text = text.replace("_SCORE_KIND_MATCH = 40\n", "_SCORE_KIND_MATCH = 40\n_SCORE_TYPE_TOKEN = 45\n_SCORE_IMPORT_CLOSURE = 70\n")
    block = '''

def _import_terms(report: ReadinessReport, unit: TheoremProofUnit | None) -> tuple[str, ...]:
    parts = [*report.constructive_path, *report.dependency_readiness.recovered]
    if unit:
        parts.append(unit.domain.replace("_", " "))
    return _tokenize(" ".join(parts))


def _search_import_closure(index: DeclarationIndex, report: ReadinessReport, unit: TheoremProofUnit | None, top_k: int) -> list[DeclarationSearchResult]:
    terms = _import_terms(report, unit)
    hits = []
    for decl in index.declarations:
        score = sum(_SCORE_IMPORT_CLOSURE for t in terms if t in _normalize(decl.module))
        if score:
            hits.append(DeclarationSearchResult(decl, score, tuple(f"import_closure:{t}" for t in terms if t in _normalize(decl.module))))
    hits.sort(key=lambda h: (-h.score, h.declaration.full_name, h.declaration.declaration_id))
    return hits[:top_k]


def _search_type_overlap(index: DeclarationIndex, query: str, top_k: int) -> list[DeclarationSearchResult]:
    q = set(_tokenize(query))
    hits = []
    for decl in index.declarations:
        if not decl.type_signature:
            continue
        overlap = q & set(_tokenize(decl.type_signature))
        if overlap:
            hits.append(DeclarationSearchResult(decl, len(overlap) * _SCORE_TYPE_TOKEN, tuple(f"type_token:{t}" for t in sorted(overlap))))
    hits.sort(key=lambda h: (-h.score, h.declaration.full_name, h.declaration.declaration_id))
    return hits[:top_k]


def suggest_import_modules_from_alignment(alignment: AlignmentResult, *, confirmed_only: bool = True) -> list[str]:
    sources = alignment.confirmed if confirmed_only else [*alignment.confirmed, *alignment.candidates]
    modules, seen = [], set()
    for c in sources:
        if c.module not in seen:
            seen.add(c.module)
            modules.append(c.module)
    return sorted(modules)


'''
    text = text.replace("\n\ndef collect_alignment_queries(", block + "\n\ndef collect_alignment_queries(")
    text = text.replace(
        "    top_k_total: int = 15,\n) -> AlignmentResult:",
        "    top_k_total: int = 15,\n    embedding_index: EmbeddingIndex | None = None,\n) -> AlignmentResult:",
    )
    text = text.replace(
        "    combined_hits: list[tuple[DeclarationSearchResult, str]] = []\n\n    for spec in query_specs:",
        "    combined_hits: list[tuple[DeclarationSearchResult, str]] = []\n    emb = embedding_index or StubEmbeddingIndex(index=index)\n    for hit in _search_import_closure(index, report, unit, top_k_per_query):\n        combined_hits.append((hit, 'import_closure'))\n    for spec in query_specs:",
    )
    text = text.replace(
        "            combined_hits.append((hit, f\"lexical:{spec.source}\"))\n\n        if \".\" in spec.text",
        "            combined_hits.append((hit, f\"lexical:{spec.source}\"))\n        for hit in _search_type_overlap(index, spec.text, top_k_per_query):\n            combined_hits.append((hit, f\"type_overlap:{spec.source}\"))\n        for hit in emb.search(query=spec.text, top_k=top_k_per_query):\n            pass\n        if \".\" in spec.text",
    )
    path.write_text(text, encoding="utf-8")


def patch_extract_proofgraph() -> None:
    (CORE / "extract_proofgraph.py").write_text(
        '''"""ProofGraph extraction orchestration."""
from __future__ import annotations
from fre_core.build_proofgraph import build_proofgraph, build_proofgraph_prompt
from fre_core.model_client import StructuredModelClient
from fre_core.schemas import AlignmentResult, ProofGraph, ReadinessReport, TheoremProofUnit

def extract_proofgraph(*, unit: TheoremProofUnit, model_client: StructuredModelClient, report: ReadinessReport | None = None, alignment: AlignmentResult | None = None, from_unit_only: bool = False) -> ProofGraph:
    if from_unit_only:
        report, alignment = None, None
    return build_proofgraph(unit=unit, model_client=model_client, report=report, alignment=alignment)

__all__ = ["build_proofgraph_prompt", "extract_proofgraph"]
''',
        encoding="utf-8",
    )


if __name__ == "__main__":
    patch_schemas()
    patch_validation()
    patch_mathlib_index()
    patch_mathlib_alignment()
    patch_extract_proofgraph()
    print("wave4 core patches applied")

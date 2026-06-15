"""mathlib declaration index: reproducible lexical lookup for alignment candidates.

The index is a versioned artifact that can later be populated from a real mathlib
export. Search results are candidate alignments only; confirmed alignment requires
human review (Silver/Gold).

Lexical ranking algorithm
-------------------------
Given a query string ``Q`` and declaration ``D``, the score is the sum of:

1. **Exact full name** (+1000): ``Q`` equals ``D.full_name`` case-insensitively.
2. **Full-name substring** (+500): normalized ``Q`` appears in ``D.full_name``.
3. **Namespace exact** (+200): ``Q`` equals ``D.namespace`` case-insensitively.
4. **Module path match** (+100): normalized ``Q`` appears in ``D.module``.
5. **Per-term full name** (+50 each): each alphanumeric token from ``Q`` with length
   at least 3 found in ``D.full_name``.
6. **Per-term namespace** (+20 each): each qualifying token found in ``D.namespace``.
7. **Per-term module** (+10 each): each qualifying token found in ``D.module``.
8. **Theorem kind** (+25): ``D.kind`` is ``theorem`` (alignment candidates are usually theorems).

Single-character tokens are ignored to avoid spurious matches on names such as ``deleteVert``.

Results are sorted by ``(-score, full_name, declaration_id)`` for deterministic ranking.
Declarations with score zero are excluded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from fre_core.schemas import DeclarationIndex, MathlibDeclaration, ReadinessReport, TheoremProofUnit

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

_SCORE_EXACT_FULL_NAME = 1000
_SCORE_FULL_NAME_SUBSTRING = 500
_SCORE_NAMESPACE_EXACT = 200
_SCORE_MODULE_SUBSTRING = 100
_SCORE_TERM_FULL_NAME = 50
_SCORE_TERM_NAMESPACE = 20
_SCORE_TERM_MODULE = 10
_SCORE_THEOREM_KIND = 25
_MIN_TERM_LENGTH = 3


@dataclass(frozen=True)
class DeclarationSearchResult:
    """One ranked declaration lookup hit."""

    declaration: MathlibDeclaration
    score: int
    matched_fields: tuple[str, ...]


def default_index_path(*, repo_root: Path | None = None) -> Path:
    """Return the committed finite-tree mathlib index fixture path."""
    root = repo_root or _repo_root_from_module()
    return root / "fixtures" / "mathlib_declarations" / "finite_tree_v0.json"


def trimmed_index_path(*, repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root_from_module()
    return root / "fixtures" / "mathlib_declarations" / "mathlib_v4.8.0.json"


def _repo_root_from_module() -> Path:
    return Path(__file__).resolve().parents[4]


def load_index(path: Path) -> DeclarationIndex:
    """Load a declaration index from JSON."""
    return DeclarationIndex.model_validate_json(path.read_text(encoding="utf-8"))


def _normalize(text: str) -> str:
    return text.casefold()


def _tokenize(query: str) -> tuple[str, ...]:
    return tuple(token for token in _TOKEN_PATTERN.findall(_normalize(query)) if len(token) >= _MIN_TERM_LENGTH)


def _score_declaration(*, query: str, declaration: MathlibDeclaration) -> tuple[int, tuple[str, ...]]:
    normalized_query = _normalize(query)
    full_name = _normalize(declaration.full_name)
    namespace = _normalize(declaration.namespace)
    module = _normalize(declaration.module)
    terms = _tokenize(query)

    score = 0
    matched: list[str] = []

    if normalized_query == full_name:
        score += _SCORE_EXACT_FULL_NAME
        matched.append("full_name_exact")
    elif normalized_query and normalized_query in full_name:
        score += _SCORE_FULL_NAME_SUBSTRING
        matched.append("full_name_substring")

    if normalized_query == namespace:
        score += _SCORE_NAMESPACE_EXACT
        matched.append("namespace_exact")
    elif normalized_query and normalized_query in namespace:
        matched.append("namespace_substring")

    if normalized_query and normalized_query in module:
        score += _SCORE_MODULE_SUBSTRING
        matched.append("module_substring")

    for term in terms:
        if term in full_name:
            score += _SCORE_TERM_FULL_NAME
            matched.append(f"term:{term}:full_name")
        if term in namespace:
            score += _SCORE_TERM_NAMESPACE
            matched.append(f"term:{term}:namespace")
        if term in module:
            score += _SCORE_TERM_MODULE
            matched.append(f"term:{term}:module")

    if declaration.kind == "theorem":
        score += _SCORE_THEOREM_KIND
        matched.append("kind:theorem")

    return score, tuple(matched)


def search(*, index: DeclarationIndex, query: str, top_k: int = 10) -> list[DeclarationSearchResult]:
    """Lexically search the index and return deterministically ranked hits."""
    if not query.strip():
        return []

    hits: list[DeclarationSearchResult] = []
    for declaration in index.declarations:
        score, matched_fields = _score_declaration(query=query, declaration=declaration)
        if score <= 0:
            continue
        hits.append(
            DeclarationSearchResult(
                declaration=declaration,
                score=score,
                matched_fields=matched_fields,
            )
        )

    hits.sort(
        key=lambda hit: (
            -hit.score,
            hit.declaration.full_name,
            hit.declaration.declaration_id,
        )
    )
    return hits[:top_k]


def build_search_query_from_unit(unit: TheoremProofUnit) -> str:
    """Build a lexical lookup query from a theorem/proof unit."""
    parts = [unit.statement, unit.local_context or "", unit.domain.replace("_", " ")]
    return " ".join(part for part in parts if part)


def build_search_query_from_report(report: ReadinessReport) -> str:
    """Build a lexical lookup query from readiness-report recovered fields."""
    parts = [
        *report.statement_readiness.recovered,
        *report.context_readiness.recovered,
        *report.dependency_readiness.recovered,
        *report.blockers,
    ]
    return " ".join(parts)


def enrich_readiness_candidates(
    *,
    report: ReadinessReport,
    index: DeclarationIndex,
    query: str | None = None,
    top_k: int = 5,
) -> ReadinessReport:
    """Replace free-text theorem candidates with index-backed lookup results."""
    lookup_query = query or build_search_query_from_report(report)
    hits = search(index=index, query=lookup_query, top_k=top_k)
    candidates = [hit.declaration.full_name for hit in hits]
    return report.model_copy(update={"existing_theorem_candidates": candidates})


def enrich_readiness_report_from_unit(
    *,
    report: ReadinessReport,
    unit: TheoremProofUnit,
    index: DeclarationIndex,
    top_k: int = 5,
) -> ReadinessReport:
    """Enrich candidates using a query derived from the source unit."""
    query = build_search_query_from_unit(unit)
    return enrich_readiness_candidates(report=report, index=index, query=query, top_k=top_k)


def suggest_declarations_for_unit(
    *,
    unit: TheoremProofUnit,
    index: DeclarationIndex,
    top_k: int = 5,
) -> list[str]:
    """Return ranked mathlib declaration full names for prompt augmentation."""
    query = build_search_query_from_unit(unit)
    hits = search(index=index, query=query, top_k=top_k)
    return [hit.declaration.full_name for hit in hits]


def lookup_declaration(
    *,
    index: DeclarationIndex,
    candidate: str,
) -> MathlibDeclaration | None:
    """Resolve a candidate string to a declaration in the index, if present."""
    normalized = candidate.strip()
    if normalized.casefold().startswith("mathlib:"):
        normalized = normalized.split(":", 1)[1].strip()
    if not normalized:
        return None
    normalized_key = normalized.casefold()
    for declaration in index.declarations:
        if declaration.full_name.casefold() == normalized_key:
            return declaration
        if declaration.declaration_id.casefold() == normalized_key:
            return declaration
        decl_suffix = declaration.declaration_id.split(":", 1)[-1]
        if decl_suffix.casefold() == normalized_key:
            return declaration
    return None

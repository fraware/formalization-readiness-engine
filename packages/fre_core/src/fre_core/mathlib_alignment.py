"""mathlib Alignment Service: multi-dimensional candidate search with explicit confirmation.

Candidate alignments are proposed from readiness-report fields and optional unit text.
Confirmed alignments require an explicit reviewer flag and are never auto-promoted from
retrieval scores. Silver and Gold records should promote alignments only through review.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from fre_core.embedding_index import (
    EMBEDDING_MODEL_ID,
    EmbeddingIndex,
    EmbeddingSearchHit,
    StubEmbeddingIndex,
    _SCORE_EMBEDDING_MAX,
)
from fre_core.mathlib_index import (
    DeclarationSearchResult,
    build_search_query_from_report,
    build_search_query_from_unit,
    search,
)
from typing import Literal

from fre_core.schemas import (
    AlignmentCandidate,
    AlignmentResult,
    DeclarationIndex,
    MathlibDeclaration,
    ReadinessReport,
    TheoremProofUnit,
)

AlignmentStatus = Literal["candidate", "confirmed"]

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_MIN_TERM_LENGTH = 3

_SCORE_NAMESPACE_EXACT = 300
_SCORE_NAMESPACE_TOKEN = 80
_SCORE_MODULE_EXACT = 250
_SCORE_MODULE_TOKEN = 60
_SCORE_KIND_MATCH = 40
_SCORE_TYPE_TOKEN = 45
_SCORE_IMPORT_CLOSURE = 70


@dataclass(frozen=True)
class _QuerySpec:
    text: str
    source: str


def _normalize(text: str) -> str:
    return text.casefold()


def _tokenize(text: str) -> tuple[str, ...]:
    return tuple(token for token in _TOKEN_PATTERN.findall(_normalize(text)) if len(token) >= _MIN_TERM_LENGTH)


def _embedding_hit_to_search_result(hit: EmbeddingSearchHit) -> DeclarationSearchResult:
    """Map cosine similarity to the lexical score band (max ~350, below exact-name hits)."""
    score = max(1, int(round(hit.score * _SCORE_EMBEDDING_MAX)))
    return DeclarationSearchResult(
        declaration=hit.declaration,
        score=score,
        matched_fields=(f"embedding:{EMBEDDING_MODEL_ID}", f"embedding_similarity:{hit.score:.4f}"),
    )


def _candidate_from_hit(*, hit: DeclarationSearchResult, query_source: str) -> AlignmentCandidate:
    declaration = hit.declaration
    return AlignmentCandidate(
        declaration_id=declaration.declaration_id,
        full_name=declaration.full_name,
        namespace=declaration.namespace,
        module=declaration.module,
        kind=declaration.kind,
        score=hit.score,
        match_reasons=list(hit.matched_fields),
        query_source=query_source,
        alignment_status="candidate",
    )


def _candidate_from_declaration(
    *,
    declaration: MathlibDeclaration,
    score: int,
    match_reasons: list[str],
    query_source: str,
    alignment_status: AlignmentStatus = "candidate",
) -> AlignmentCandidate:
    return AlignmentCandidate(
        declaration_id=declaration.declaration_id,
        full_name=declaration.full_name,
        namespace=declaration.namespace,
        module=declaration.module,
        kind=declaration.kind,
        score=score,
        match_reasons=match_reasons,
        query_source=query_source,
        alignment_status=alignment_status,
    )


def _search_namespace(*, index: DeclarationIndex, query: str) -> list[DeclarationSearchResult]:
    normalized_query = _normalize(query)
    if not normalized_query:
        return []

    hits: list[DeclarationSearchResult] = []
    terms = _tokenize(query)

    for declaration in index.declarations:
        namespace = _normalize(declaration.namespace)
        score = 0
        matched: list[str] = []

        if normalized_query == namespace:
            score += _SCORE_NAMESPACE_EXACT
            matched.append("namespace_exact")
        else:
            for term in terms:
                if term in namespace:
                    score += _SCORE_NAMESPACE_TOKEN
                    matched.append(f"namespace_term:{term}")

        if score <= 0:
            continue

        hits.append(
            DeclarationSearchResult(
                declaration=declaration,
                score=score,
                matched_fields=tuple(matched),
            )
        )

    hits.sort(key=lambda hit: (-hit.score, hit.declaration.full_name, hit.declaration.declaration_id))
    return hits


def _search_module(*, index: DeclarationIndex, query: str) -> list[DeclarationSearchResult]:
    normalized_query = _normalize(query)
    if not normalized_query:
        return []

    hits: list[DeclarationSearchResult] = []
    terms = _tokenize(query)

    for declaration in index.declarations:
        module = _normalize(declaration.module)
        score = 0
        matched: list[str] = []

        if normalized_query == module:
            score += _SCORE_MODULE_EXACT
            matched.append("module_exact")
        elif normalized_query in module:
            score += _SCORE_MODULE_EXACT // 2
            matched.append("module_substring")
        else:
            for term in terms:
                if term in module:
                    score += _SCORE_MODULE_TOKEN
                    matched.append(f"module_term:{term}")

        if score <= 0:
            continue

        hits.append(
            DeclarationSearchResult(
                declaration=declaration,
                score=score,
                matched_fields=tuple(matched),
            )
        )

    hits.sort(key=lambda hit: (-hit.score, hit.declaration.full_name, hit.declaration.declaration_id))
    return hits


def _search_by_kind(
    *,
    index: DeclarationIndex,
    query: str,
    kind: str,
) -> list[DeclarationSearchResult]:
    lexical_hits = search(index=index, query=query, top_k=len(index.declarations))
    hits: list[DeclarationSearchResult] = []

    for hit in lexical_hits:
        if hit.declaration.kind != kind:
            continue
        boosted_score = hit.score + _SCORE_KIND_MATCH
        matched = (*hit.matched_fields, f"kind:{kind}")
        hits.append(
            DeclarationSearchResult(
                declaration=hit.declaration,
                score=boosted_score,
                matched_fields=matched,
            )
        )

    hits.sort(key=lambda hit: (-hit.score, hit.declaration.full_name, hit.declaration.declaration_id))
    return hits


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




def collect_alignment_queries(
    *,
    report: ReadinessReport,
    unit: TheoremProofUnit | None = None,
) -> list[_QuerySpec]:
    """Collect deterministic query strings from report candidates and statement tokens."""
    queries: list[_QuerySpec] = []
    seen: set[tuple[str, str]] = set()

    def add(text: str, source: str) -> None:
        cleaned = text.strip()
        if not cleaned:
            return
        key = (_normalize(cleaned), source)
        if key in seen:
            return
        seen.add(key)
        queries.append(_QuerySpec(text=cleaned, source=source))

    for candidate in report.existing_theorem_candidates:
        add(candidate, "existing_theorem_candidate")

    for recovered in report.statement_readiness.recovered:
        add(recovered, "statement_recovered")

    if unit is not None:
        for token in _tokenize(unit.statement):
            add(token, "unit_statement_token")

    aggregate_report_query = build_search_query_from_report(report)
    if aggregate_report_query.strip():
        add(aggregate_report_query, "report_aggregate")

    if unit is not None:
        aggregate_unit_query = build_search_query_from_unit(unit)
        if aggregate_unit_query.strip():
            add(aggregate_unit_query, "unit_aggregate")

    return queries


def _merge_hits(
    *,
    hits: list[tuple[DeclarationSearchResult, str]],
    top_k_total: int,
) -> list[AlignmentCandidate]:
    merged: dict[str, AlignmentCandidate] = {}

    for hit, query_source in hits:
        declaration_id = hit.declaration.declaration_id
        candidate = _candidate_from_hit(hit=hit, query_source=query_source)
        existing = merged.get(declaration_id)
        if existing is None or candidate.score > existing.score:
            merged[declaration_id] = candidate
        elif existing.score == candidate.score:
            combined_reasons = sorted(set(existing.match_reasons) | set(candidate.match_reasons))
            merged[declaration_id] = existing.model_copy(
                update={
                    "match_reasons": combined_reasons,
                    "query_source": f"{existing.query_source}+{query_source}",
                }
            )

    ranked = sorted(
        merged.values(),
        key=lambda candidate: (
            -candidate.score,
            candidate.full_name,
            candidate.declaration_id,
        ),
    )
    return ranked[:top_k_total]


def align_readiness_report(
    *,
    report: ReadinessReport,
    index: DeclarationIndex,
    unit: TheoremProofUnit | None = None,
    confirmed_full_names: frozenset[str] | None = None,
    top_k_per_query: int = 5,
    top_k_total: int = 15,
    embedding_index: EmbeddingIndex | None = None,
) -> AlignmentResult:
    """Propose alignment candidates from report fields; confirmed alignments need explicit flags."""
    query_specs = collect_alignment_queries(report=report, unit=unit)
    combined_hits: list[tuple[DeclarationSearchResult, str]] = []
    emb = embedding_index or StubEmbeddingIndex(index=index)
    for hit in _search_import_closure(index, report, unit, top_k_per_query):
        combined_hits.append((hit, 'import_closure'))
    for spec in query_specs:
        for hit in search(index=index, query=spec.text, top_k=top_k_per_query):
            combined_hits.append((hit, f"lexical:{spec.source}"))
        for hit in _search_type_overlap(index, spec.text, top_k_per_query):
            combined_hits.append((hit, f"type_overlap:{spec.source}"))
        for emb_hit in emb.search(query=spec.text, top_k=top_k_per_query):
            combined_hits.append((_embedding_hit_to_search_result(emb_hit), f"embedding:{spec.source}"))
        if "." in spec.text or spec.text[:1].isupper():
            for hit in _search_namespace(index=index, query=spec.text)[:top_k_per_query]:
                combined_hits.append((hit, f"namespace:{spec.source}"))

            for hit in _search_module(index=index, query=spec.text)[:top_k_per_query]:
                combined_hits.append((hit, f"module:{spec.source}"))

        for hit in _search_by_kind(index=index, query=spec.text, kind="theorem")[:top_k_per_query]:
            combined_hits.append((hit, f"kind_theorem:{spec.source}"))

    candidates = _merge_hits(hits=combined_hits, top_k_total=top_k_total)

    confirmed: list[AlignmentCandidate] = []
    if confirmed_full_names:
        by_full_name = {declaration.full_name: declaration for declaration in index.declarations}
        for full_name in sorted(confirmed_full_names):
            declaration = by_full_name.get(full_name)
            if declaration is None:
                continue
            confirmed.append(
                _candidate_from_declaration(
                    declaration=declaration,
                    score=0,
                    match_reasons=["reviewer_confirmed"],
                    query_source="reviewer_confirmed",
                    alignment_status="confirmed",
                )
            )

    return AlignmentResult(
        unit_id=report.unit_id,
        index_id=index.index_id,
        candidates=candidates,
        confirmed=confirmed,
    )


def enrich_readiness_candidates_from_alignment(
    *,
    report: ReadinessReport,
    alignment: AlignmentResult,
    top_k: int = 5,
) -> ReadinessReport:
    """Replace theorem candidates with ranked alignment candidate names."""
    candidate_names = [candidate.full_name for candidate in alignment.candidates[:top_k]]
    if not candidate_names:
        return report
    return report.model_copy(update={"existing_theorem_candidates": candidate_names})

"""Deterministic LaTeX ingestion for theorem/proof units."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from fre_core.model_client import StructuredModelClient
from fre_core.schemas import SourceSpan, TheoremProofUnit

THEOREM_ENVIRONMENTS = ("theorem", "lemma", "proposition", "corollary", "definition", "remark")


@dataclass(frozen=True)
class LatexTheoremBlock:
    env: str
    title: str | None
    statement: str
    proof: str | None
    statement_span: SourceSpan
    proof_span: SourceSpan | None


def build_theorem_pattern(environments: tuple[str, ...] = THEOREM_ENVIRONMENTS) -> re.Pattern[str]:
    env_group = "|".join(re.escape(env) for env in environments)
    return re.compile(rf"\\begin\{{(?P<env>{env_group})\}}(?:\[(?P<title>[^\]]*)\])?(?P<body>.*?)\\end\{{(?P=env)\}}", flags=re.DOTALL)


PROOF_PATTERN = re.compile(r"\\begin\{proof\}(?P<body>.*?)\\end\{proof\}", flags=re.DOTALL)


def _clean_latex_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _find_following_proof(source: str, theorem_end: int) -> tuple[str | None, SourceSpan | None]:
    suffix = source[theorem_end:]
    skipped = len(suffix) - len(suffix.lstrip())
    proof_match = PROOF_PATTERN.match(suffix, pos=skipped)
    if proof_match is None:
        return None, None
    return _clean_latex_text(proof_match.group("body")), SourceSpan(start=theorem_end + proof_match.start("body"), end=theorem_end + proof_match.end("body"))


def parse_latex_theorem_blocks(source: str, *, environments: tuple[str, ...] = THEOREM_ENVIRONMENTS) -> list[LatexTheoremBlock]:
    blocks: list[LatexTheoremBlock] = []
    for match in build_theorem_pattern(environments).finditer(source):
        proof, proof_span = _find_following_proof(source, match.end())
        blocks.append(LatexTheoremBlock(env=match.group("env"), title=match.group("title"), statement=_clean_latex_text(match.group("body")), proof=proof, statement_span=SourceSpan(start=match.start("body"), end=match.end("body")), proof_span=proof_span))
    return blocks


def theorem_blocks_to_units(*, blocks: list[LatexTheoremBlock], source_id: str, domain: str, local_context: str | None = None) -> list[TheoremProofUnit]:
    units: list[TheoremProofUnit] = []
    for index, block in enumerate(blocks, start=1):
        title_slug = re.sub(r"[^a-zA-Z0-9]+", "_", (block.title or block.env).lower()).strip("_")
        units.append(TheoremProofUnit(unit_id=f"{source_id}_{index:04d}_{title_slug}", source_id=source_id, statement=block.statement, proof=block.proof, local_context=local_context, domain=domain, statement_span=block.statement_span, proof_span=block.proof_span))
    return units


def ingest_latex_source(*, source: str, source_id: str, domain: str, local_context: str | None = None, environments: tuple[str, ...] = THEOREM_ENVIRONMENTS, repair: bool = False, model_client: StructuredModelClient | None = None) -> list[TheoremProofUnit]:
    blocks = parse_latex_theorem_blocks(source, environments=environments)
    if blocks:
        return theorem_blocks_to_units(blocks=blocks, source_id=source_id, domain=domain, local_context=local_context)
    if repair:
        if model_client is None:
            raise ValueError("model_client is required when repair=True.")
        from fre_core.segmentation_repair import repair_latex_segmentation
        return repair_latex_segmentation(source=source, source_id=source_id, domain=domain, model_client=model_client, local_context=local_context)
    return []


def ingest_latex_file(*, path: Path, source_id: str, domain: str, local_context: str | None = None, environments: tuple[str, ...] = THEOREM_ENVIRONMENTS, repair: bool = False, model_client: StructuredModelClient | None = None) -> list[TheoremProofUnit]:
    return ingest_latex_source(source=path.read_text(encoding="utf-8"), source_id=source_id, domain=domain, local_context=local_context, environments=environments, repair=repair, model_client=model_client)

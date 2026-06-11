"""Deterministic LaTeX ingestion for theorem/proof units."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from fre_core.schemas import SourceSpan, TheoremProofUnit

THEOREM_ENVIRONMENTS = ("theorem", "lemma", "proposition", "corollary")
THEOREM_PATTERN = re.compile(
    r"\\begin\{(?P<env>theorem|lemma|proposition|corollary)\}(?:\[(?P<title>[^\]]*)\])?"
    r"(?P<body>.*?)"
    r"\\end\{(?P=env)\}",
    flags=re.DOTALL,
)
PROOF_PATTERN = re.compile(
    r"\\begin\{proof\}(?P<body>.*?)\\end\{proof\}",
    flags=re.DOTALL,
)


@dataclass(frozen=True)
class LatexTheoremBlock:
    """A theorem-like LaTeX block and its optional following proof."""

    env: str
    title: str | None
    statement: str
    proof: str | None
    statement_span: SourceSpan
    proof_span: SourceSpan | None


def _clean_latex_text(text: str) -> str:
    """Normalize whitespace while preserving mathematical text."""
    return re.sub(r"\s+", " ", text).strip()


def _find_following_proof(source: str, theorem_end: int) -> tuple[str | None, SourceSpan | None]:
    """Return the first proof immediately following a theorem block, if present."""
    suffix = source[theorem_end:]
    skipped = len(suffix) - len(suffix.lstrip())
    proof_match = PROOF_PATTERN.match(suffix, pos=skipped)
    if proof_match is None:
        return None, None

    proof_start = theorem_end + proof_match.start("body")
    proof_end = theorem_end + proof_match.end("body")
    return _clean_latex_text(proof_match.group("body")), SourceSpan(start=proof_start, end=proof_end)


def parse_latex_theorem_blocks(source: str) -> list[LatexTheoremBlock]:
    """Parse theorem-like environments and immediately following proof blocks."""
    blocks: list[LatexTheoremBlock] = []

    for match in THEOREM_PATTERN.finditer(source):
        proof, proof_span = _find_following_proof(source, match.end())
        blocks.append(
            LatexTheoremBlock(
                env=match.group("env"),
                title=match.group("title"),
                statement=_clean_latex_text(match.group("body")),
                proof=proof,
                statement_span=SourceSpan(start=match.start("body"), end=match.end("body")),
                proof_span=proof_span,
            )
        )

    return blocks


def theorem_blocks_to_units(
    *,
    blocks: list[LatexTheoremBlock],
    source_id: str,
    domain: str,
    local_context: str | None = None,
) -> list[TheoremProofUnit]:
    """Convert parsed LaTeX theorem blocks into theorem/proof units."""
    units: list[TheoremProofUnit] = []

    for index, block in enumerate(blocks, start=1):
        title_slug = re.sub(r"[^a-zA-Z0-9]+", "_", (block.title or block.env).lower()).strip("_")
        unit_id = f"{source_id}_{index:04d}_{title_slug}"
        units.append(
            TheoremProofUnit(
                unit_id=unit_id,
                source_id=source_id,
                statement=block.statement,
                proof=block.proof,
                local_context=local_context,
                domain=domain,
                statement_span=block.statement_span,
                proof_span=block.proof_span,
            )
        )

    return units


def ingest_latex_file(
    *,
    path: Path,
    source_id: str,
    domain: str,
    local_context: str | None = None,
) -> list[TheoremProofUnit]:
    """Read a LaTeX file and return parsed theorem/proof units."""
    source = path.read_text(encoding="utf-8")
    blocks = parse_latex_theorem_blocks(source)
    return theorem_blocks_to_units(
        blocks=blocks,
        source_id=source_id,
        domain=domain,
        local_context=local_context,
    )

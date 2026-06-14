"""Model-assisted LaTeX segmentation repair when deterministic parsing fails."""

from __future__ import annotations

from fre_core.latex_ingestion import LatexTheoremBlock, theorem_blocks_to_units
from fre_core.model_client import StructuredModelClient
from fre_core.schemas import SegmentationRepairResult, TheoremProofUnit


class SegmentationRepairError(RuntimeError):
    pass


def repair_latex_segmentation(*, source: str, source_id: str, domain: str, model_client: StructuredModelClient, local_context: str | None = None) -> list[TheoremProofUnit]:
    result = model_client.extract_json(prompt=f"Segment LaTeX into units with spans:\n{source}", schema=SegmentationRepairResult)
    if not result.units:
        raise SegmentationRepairError(f"No units repaired for {source_id!r}")
    for unit in result.units:
        if source[unit.statement_span.start : unit.statement_span.end].strip() != unit.statement.strip():
            raise SegmentationRepairError("Repaired statement span does not match statement text.")
    blocks = [LatexTheoremBlock(env="theorem", title=None, statement=u.statement, proof=u.proof, statement_span=u.statement_span, proof_span=u.proof_span) for u in result.units]
    return theorem_blocks_to_units(blocks=blocks, source_id=source_id, domain=domain, local_context=local_context)

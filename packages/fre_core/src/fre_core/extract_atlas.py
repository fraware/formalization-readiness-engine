"""Atlas record extraction orchestration.

This module converts a theorem/proof unit into a Formalization Gap Atlas record using
an injected structured model client. It does not import provider SDKs directly.
"""

from __future__ import annotations

from fre_core.artifact_normalization import normalize_atlas_record
from fre_core.model_client import StructuredModelClient
from fre_core.schemas import AtlasRecord, TheoremProofUnit
from fre_core.validation import validate_atlas_record


ATLAS_EXTRACTION_INSTRUCTIONS = """
You are extracting a source-grounded Formalization Gap Atlas record.

Follow these rules:
1. Identify the most important formalization blocker for this unit.
2. Quote or paraphrase source-grounded evidence from the statement or proof.
3. Describe the mathematical pattern and a candidate formal object when applicable.
4. The recommended action must be specific enough for a formalizer to act on.
5. Keep severity proportional to how much the blocker impedes formalization.
""".strip()


def build_atlas_prompt(unit: TheoremProofUnit) -> str:
    """Build the prompt for Atlas-record extraction from one theorem/proof unit."""
    proof = unit.proof or "No proof body was provided."
    context = unit.local_context or "No local context was provided."

    return f"""
{ATLAS_EXTRACTION_INSTRUCTIONS}

Unit identifier: {unit.unit_id}
Domain: {unit.domain}

Local context:
{context}

Theorem statement:
{unit.statement}

Proof body:
{proof}
""".strip()


def extract_atlas_record(
    *,
    unit: TheoremProofUnit,
    model_client: StructuredModelClient,
) -> AtlasRecord:
    """Extract an Atlas record for one theorem/proof unit."""
    prompt = build_atlas_prompt(unit)
    record = model_client.extract_json(prompt=prompt, schema=AtlasRecord)
    if record.unit_id != unit.unit_id:
        record = record.model_copy(update={"unit_id": unit.unit_id})
    record = normalize_atlas_record(record)
    validate_atlas_record(record)
    validate_atlas_record(record, mode="public_export")
    return record

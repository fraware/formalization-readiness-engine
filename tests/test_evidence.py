"""Optional guards for committed documentation evidence."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "evidence" / "live_extraction_v0.2"
LIVE_EXTRACTION_SUMMARY = EVIDENCE_DIR / "summary.json"


def test_live_extraction_summary_exists_and_parses() -> None:
    assert LIVE_EXTRACTION_SUMMARY.is_file(), (
        "docs/evidence/live_extraction_v0.2/summary.json is missing; "
        "run make record-live-extraction after make demo-live"
    )
    payload = json.loads(LIVE_EXTRACTION_SUMMARY.read_text(encoding="utf-8"))
    assert payload.get("schema_version") == "0.1"
    examples = payload.get("examples")
    assert isinstance(examples, list) and len(examples) >= 2

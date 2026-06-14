import pytest
from fre_core.latex_ingestion import ingest_latex_source
from fre_core.schemas import RepairedUnitSpan, SegmentationRepairResult, SourceSpan
from fre_core.segmentation_repair import SegmentationRepairError, repair_latex_segmentation

class FakeRepairClient:
    def __init__(self, result: SegmentationRepairResult) -> None:
        self._result = result
    def extract_json(self, *, prompt: str, schema: type[SegmentationRepairResult]) -> SegmentationRepairResult:
        return self._result

UNPARSEABLE = "Some prose. A repaired theorem statement. A repaired proof."

def test_ingest_without_repair_returns_empty() -> None:
    assert ingest_latex_source(source=UNPARSEABLE, source_id="x", domain="graph_theory") == []

def test_repair_preserves_spans() -> None:
    statement = "A repaired theorem statement."
    proof = "A repaired proof."
    client = FakeRepairClient(SegmentationRepairResult(units=[RepairedUnitSpan(statement=statement, proof=proof, statement_span=SourceSpan(start=UNPARSEABLE.index(statement), end=UNPARSEABLE.index(statement)+len(statement)), proof_span=SourceSpan(start=UNPARSEABLE.index(proof), end=UNPARSEABLE.index(proof)+len(proof)))]))
    units = repair_latex_segmentation(source=UNPARSEABLE, source_id="x", domain="graph_theory", model_client=client)
    assert len(units) == 1 and units[0].statement_span is not None

def test_repair_rejects_mismatched_spans() -> None:
    client = FakeRepairClient(SegmentationRepairResult(units=[RepairedUnitSpan(statement="Wrong", proof=None, statement_span=SourceSpan(start=0, end=4), proof_span=None)]))
    with pytest.raises(SegmentationRepairError):
        repair_latex_segmentation(source=UNPARSEABLE, source_id="x", domain="graph_theory", model_client=client)

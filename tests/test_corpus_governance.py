from pathlib import Path

import pytest

from fre_core.corpus import (
    CorpusCatalog,
    CorpusValidationError,
    load_corpus_catalog,
    validate_corpus_catalog,
    validate_corpus_unit_spans,
)
from fre_core.schemas import SourceDocument, SourceSpan, TheoremProofUnit
from fre_core.validation import load_unit

REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_CATALOG = REPO_ROOT / "corpus" / "catalog.json"


def test_validate_main_catalog_passes() -> None:
    catalog = load_corpus_catalog(MAIN_CATALOG)
    validate_corpus_catalog(catalog=catalog, repo_root=REPO_ROOT)
    validate_corpus_unit_spans(catalog=catalog, repo_root=REPO_ROOT)


def test_main_catalog_has_five_sources() -> None:
    catalog = load_corpus_catalog(MAIN_CATALOG)
    assert len(catalog.sources) == 5
    assert {s.release_mode for s in catalog.sources} == {"full_text_allowed", "metadata_only"}


def test_validate_catalog_rejects_duplicate_source_id() -> None:
    catalog = CorpusCatalog(sources=[
        SourceDocument(source_id="dup", source_type="author_permitted_notes", license_status="permission_granted", release_mode="full_text_allowed", domain="graph_theory", path="corpus/sources/finite_tree.tex"),
        SourceDocument(source_id="dup", source_type="author_permitted_notes", license_status="permission_granted", release_mode="metadata_only", domain="graph_theory", path="corpus/sources/metadata_only_graph_sketch.tex"),
    ])
    with pytest.raises(CorpusValidationError, match="Duplicate source_id"):
        validate_corpus_catalog(catalog=catalog, repo_root=REPO_ROOT)


def test_validate_corpus_unit_spans_rejects_out_of_range(tmp_path: Path) -> None:
    catalog = load_corpus_catalog(MAIN_CATALOG)
    source = next(source for source in catalog.sources if source.release_mode == "full_text_allowed")
    source_path = REPO_ROOT / source.path
    source_text = source_path.read_text(encoding="utf-8")

    units_dir = tmp_path / "units"
    units_dir.mkdir()
    unit = TheoremProofUnit(
        unit_id="bad_span_unit",
        source_id=source.source_id,
        statement="Example statement.",
        proof=None,
        domain=source.domain,
        statement_span=SourceSpan(start=0, end=len(source_text) + 10),
        proof_span=None,
    )
    unit_path = units_dir / f"{unit.unit_id}.json"
    unit_path.write_text(unit.model_dump_json(indent=2), encoding="utf-8")

    with pytest.raises(CorpusValidationError, match="span_out_of_range"):
        validate_corpus_unit_spans(catalog=catalog, repo_root=REPO_ROOT, units_dir=units_dir)


def test_gold_seed_units_with_null_spans_skip_span_validation() -> None:
    catalog = load_corpus_catalog(MAIN_CATALOG)
    gold_units_dir = REPO_ROOT / "benchmarks" / "readinessbench" / "gold"
    for unit_path in sorted(gold_units_dir.glob("*/unit.json")):
        unit = TheoremProofUnit.model_validate_json(unit_path.read_text(encoding="utf-8"))
        assert unit.statement_span is None and unit.proof_span is None
        load_unit(unit_path, source_text=None)
    validate_corpus_unit_spans(catalog=catalog, repo_root=REPO_ROOT)

import pytest

from fre_core.corpus import CorpusCatalog, CorpusValidationError, make_shareable_units, validate_unit_sources
from fre_core.schemas import SourceDocument, TheoremProofUnit


def source(source_id: str, release_mode: str) -> SourceDocument:
    return SourceDocument(
        source_id=source_id,
        source_type="author_permitted_notes",
        license_status="tracked",
        release_mode=release_mode,
        domain="graph_theory",
        path=f"raw/{source_id}.tex",
    )


def unit(source_id: str) -> TheoremProofUnit:
    return TheoremProofUnit(
        unit_id=f"{source_id}_unit",
        source_id=source_id,
        statement="A theorem statement.",
        proof="A proof body.",
        domain="graph_theory",
    )


def test_validate_unit_sources_accepts_known_sources() -> None:
    catalog = CorpusCatalog(sources=[source("s1", "full_text_allowed")])

    validate_unit_sources(units=[unit("s1")], catalog=catalog)


def test_validate_unit_sources_rejects_unknown_sources() -> None:
    catalog = CorpusCatalog(sources=[source("s1", "full_text_allowed")])

    with pytest.raises(CorpusValidationError):
        validate_unit_sources(units=[unit("missing")], catalog=catalog)


def test_make_shareable_units_keeps_text_when_allowed() -> None:
    catalog = CorpusCatalog(sources=[source("s1", "full_text_allowed")])

    shared = make_shareable_units(units=[unit("s1")], catalog=catalog, include_text=True)

    assert shared[0].statement == "A theorem statement."
    assert shared[0].proof == "A proof body."


def test_make_shareable_units_removes_text_for_metadata_only_sources() -> None:
    catalog = CorpusCatalog(sources=[source("s1", "metadata_only")])

    shared = make_shareable_units(units=[unit("s1")], catalog=catalog, include_text=False)

    assert shared[0].statement == ""
    assert shared[0].proof is None


def test_make_shareable_units_drops_metadata_only_sources_when_text_requested() -> None:
    catalog = CorpusCatalog(sources=[source("s1", "metadata_only")])

    shared = make_shareable_units(units=[unit("s1")], catalog=catalog, include_text=True)

    assert shared == []

"""Tests for corpus catalog ingestion and shareable export."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from fre_core.corpus import (
    CorpusValidationError,
    export_shareable_units,
    ingest_catalog,
    load_corpus_catalog,
    validate_unit_sources,
)
from fre_core.latex_ingestion import ingest_latex_file

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures" / "corpus"
TWO_SOURCE_CATALOG = FIXTURES / "catalog_two_sources.json"
MAIN_CATALOG = REPO_ROOT / "corpus" / "catalog.json"
FINITE_TREE_TEX = REPO_ROOT / "corpus" / "sources" / "finite_tree.tex"
CATEGORY_THEORY_TEX = REPO_ROOT / "corpus" / "sources" / "category_theory_pullback.tex"


def test_load_main_catalog_has_reference_sources() -> None:
    catalog = load_corpus_catalog(MAIN_CATALOG)

    assert len(catalog.sources) == 2
    source_ids = {source.source_id for source in catalog.sources}
    assert source_ids == {"finite_tree_notes_001", "category_theory_pullback_notes_001"}
    assert all(source.release_mode == "full_text_allowed" for source in catalog.sources)


def test_ingest_catalog_assigns_known_source_ids() -> None:
    catalog = load_corpus_catalog(TWO_SOURCE_CATALOG)

    units = ingest_catalog(catalog=catalog, repo_root=REPO_ROOT)

    assert len(units) == 2
    source_ids = {unit.source_id for unit in units}
    assert source_ids == {"full_text_source", "metadata_only_source"}


def test_ingest_catalog_rejects_missing_source_file() -> None:
    catalog = load_corpus_catalog(TWO_SOURCE_CATALOG)

    with pytest.raises(CorpusValidationError, match="Missing source file"):
        ingest_catalog(catalog=catalog, repo_root=REPO_ROOT / "missing")


def test_ingest_main_catalog_reference_sources() -> None:
    catalog = load_corpus_catalog(MAIN_CATALOG)

    units = ingest_catalog(catalog=catalog, repo_root=REPO_ROOT)

    assert len(units) == 2
    by_source = {unit.source_id: unit for unit in units}

    finite_tree = by_source["finite_tree_notes_001"]
    assert "finite tree" in finite_tree.statement.lower()
    assert finite_tree.proof is not None

    category_theory = by_source["category_theory_pullback_notes_001"]
    assert "equivalence" in category_theory.statement.lower()
    assert "pullback" in category_theory.statement.lower()
    assert category_theory.proof is not None


def test_source_spans_preserved_through_catalog_ingest() -> None:
    catalog = load_corpus_catalog(MAIN_CATALOG)
    source_text = FINITE_TREE_TEX.read_text(encoding="utf-8")

    units = ingest_catalog(catalog=catalog, repo_root=REPO_ROOT)
    unit = units[0]

    assert unit.statement_span is not None
    assert unit.proof_span is not None
    assert unit.statement == source_text[unit.statement_span.start : unit.statement_span.end].strip()
    assert unit.proof == source_text[unit.proof_span.start : unit.proof_span.end].strip()


def test_source_spans_preserved_after_shareable_export() -> None:
    catalog = load_corpus_catalog(TWO_SOURCE_CATALOG)
    units = ingest_catalog(catalog=catalog, repo_root=REPO_ROOT)

    exported = export_shareable_units(units=units, catalog=catalog, include_text=False)
    by_source = {unit.source_id: unit for unit in exported}

    full_text_unit = by_source["full_text_source"]
    metadata_unit = by_source["metadata_only_source"]

    assert full_text_unit.statement
    assert full_text_unit.proof
    assert full_text_unit.statement_span is not None
    assert full_text_unit.proof_span is not None

    assert metadata_unit.statement == ""
    assert metadata_unit.proof is None
    assert metadata_unit.statement_span is not None


def test_export_shareable_units_full_text_fixture() -> None:
    catalog = load_corpus_catalog(TWO_SOURCE_CATALOG)
    units = ingest_catalog(catalog=catalog, repo_root=REPO_ROOT)
    full_text_units = [unit for unit in units if unit.source_id == "full_text_source"]

    shared = export_shareable_units(
        units=full_text_units,
        catalog=catalog,
        include_text=True,
    )

    assert len(shared) == 1
    assert shared[0].statement
    assert shared[0].proof


def test_export_shareable_units_metadata_only_fixture() -> None:
    catalog = load_corpus_catalog(TWO_SOURCE_CATALOG)
    units = ingest_catalog(catalog=catalog, repo_root=REPO_ROOT)
    metadata_units = [unit for unit in units if unit.source_id == "metadata_only_source"]

    shared = export_shareable_units(
        units=metadata_units,
        catalog=catalog,
        include_text=False,
    )

    assert len(shared) == 1
    assert shared[0].statement == ""
    assert shared[0].proof is None
    assert shared[0].unit_id == metadata_units[0].unit_id


def test_validate_unit_sources_rejects_ingested_units_with_unknown_catalog() -> None:
    catalog = load_corpus_catalog(TWO_SOURCE_CATALOG)
    units = ingest_latex_file(
        path=FINITE_TREE_TEX,
        source_id="unknown_source",
        domain="graph_theory",
    )

    with pytest.raises(CorpusValidationError):
        validate_unit_sources(units=units, catalog=catalog)


def test_ingest_catalog_cli_runs_on_main_catalog(tmp_path: Path) -> None:
    output_dir = tmp_path / "units"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "fre_core.cli",
            "ingest-catalog",
            str(MAIN_CATALOG),
            str(output_dir),
            "--repo-root",
            str(REPO_ROOT),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    written = list(output_dir.glob("*.json"))
    assert len(written) == 2
    assert "ingested units" in result.stdout


def test_source_spans_preserved_for_category_theory_catalog_ingest() -> None:
    catalog = load_corpus_catalog(MAIN_CATALOG)
    source_text = CATEGORY_THEORY_TEX.read_text(encoding="utf-8")

    units = ingest_catalog(catalog=catalog, repo_root=REPO_ROOT)
    unit = next(unit for unit in units if unit.source_id == "category_theory_pullback_notes_001")

    assert unit.statement_span is not None
    assert unit.proof_span is not None
    assert unit.statement == source_text[unit.statement_span.start : unit.statement_span.end].strip()
    assert unit.proof == source_text[unit.proof_span.start : unit.proof_span.end].strip()

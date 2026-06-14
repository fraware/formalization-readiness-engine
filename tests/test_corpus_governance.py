from pathlib import Path
import pytest
from fre_core.corpus import CorpusCatalog, CorpusValidationError, load_corpus_catalog, validate_corpus_catalog
from fre_core.schemas import SourceDocument

REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_CATALOG = REPO_ROOT / "corpus" / "catalog.json"

def test_validate_main_catalog_passes() -> None:
    validate_corpus_catalog(catalog=load_corpus_catalog(MAIN_CATALOG), repo_root=REPO_ROOT)

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

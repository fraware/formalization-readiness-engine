"""Corpus catalog utilities."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from fre_core.latex_ingestion import ingest_latex_file
from fre_core.schemas import SourceDocument, TheoremProofUnit


class CorpusCatalog(BaseModel):
    """A versioned catalog of source documents used by the engine."""

    schema_version: str = "0.1"
    sources: list[SourceDocument] = Field(default_factory=list)

    def by_source_id(self) -> dict[str, SourceDocument]:
        return {source.source_id: source for source in self.sources}


class CorpusValidationError(ValueError):
    """Raised when corpus metadata is missing or inconsistent."""


def load_corpus_catalog(path: Path) -> CorpusCatalog:
    """Load a corpus catalog from JSON."""
    return CorpusCatalog.model_validate_json(path.read_text(encoding="utf-8"))


def resolve_source_path(*, source: SourceDocument, repo_root: Path) -> Path:
    """Resolve a catalog source path relative to the repository root."""
    return repo_root / source.path


def ingest_catalog(
    *,
    catalog: CorpusCatalog,
    repo_root: Path,
) -> list[TheoremProofUnit]:
    """Ingest every catalog source and validate unit source identifiers."""
    units: list[TheoremProofUnit] = []

    for source in catalog.sources:
        source_path = resolve_source_path(source=source, repo_root=repo_root)
        if not source_path.is_file():
            raise CorpusValidationError(
                f"Missing source file for {source.source_id}: {source_path}"
            )
        if source_path.suffix.lower() != ".tex":
            raise CorpusValidationError(
                f"Unsupported source format for {source.source_id}: {source_path}"
            )
        units.extend(
            ingest_latex_file(
                path=source_path,
                source_id=source.source_id,
                domain=source.domain,
            )
        )

    validate_unit_sources(units=units, catalog=catalog)
    return units


def load_units_from_dir(units_dir: Path) -> list[TheoremProofUnit]:
    """Load theorem/proof unit JSON files from a directory."""
    units: list[TheoremProofUnit] = []
    for path in sorted(units_dir.glob("*.json")):
        units.append(TheoremProofUnit.model_validate_json(path.read_text(encoding="utf-8")))
    return units


def write_units(units: list[TheoremProofUnit], output_dir: Path) -> list[Path]:
    """Write theorem/proof units as JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for unit in units:
        target = output_dir / f"{unit.unit_id}.json"
        target.write_text(unit.model_dump_json(indent=2), encoding="utf-8")
        written.append(target)
    return written


def export_shareable_units(
    *,
    units: list[TheoremProofUnit],
    catalog: CorpusCatalog,
    include_text: bool = False,
) -> list[TheoremProofUnit]:
    """Validate and filter units for sharing according to catalog release modes."""
    validate_unit_sources(units=units, catalog=catalog)
    return make_shareable_units(units=units, catalog=catalog, include_text=include_text)


def validate_unit_sources(*, units: list[TheoremProofUnit], catalog: CorpusCatalog) -> None:
    """Ensure every theorem/proof unit refers to a known source document."""
    sources = catalog.by_source_id()
    missing = sorted({unit.source_id for unit in units if unit.source_id not in sources})
    if missing:
        raise CorpusValidationError(f"Unknown source identifiers: {missing}")


def full_text_allowed(source: SourceDocument) -> bool:
    """Return whether source text may be copied into shared artifacts."""
    return source.release_mode == "full_text_allowed"


def derived_record_allowed(source: SourceDocument) -> bool:
    """Return whether derived records may be shared for a source."""
    return source.release_mode in {"full_text_allowed", "metadata_only", "derived_annotations_only"}


def make_shareable_units(
    *,
    units: list[TheoremProofUnit],
    catalog: CorpusCatalog,
    include_text: bool = False,
) -> list[TheoremProofUnit]:
    """Prepare units for sharing according to catalog release modes."""
    sources = catalog.by_source_id()
    shared: list[TheoremProofUnit] = []

    for unit in units:
        source = sources.get(unit.source_id)
        if source is None:
            raise CorpusValidationError(f"Unknown source identifier: {unit.source_id}")

        if include_text:
            if full_text_allowed(source):
                shared.append(unit)
            continue

        if derived_record_allowed(source):
            if full_text_allowed(source):
                shared.append(unit)
            else:
                shared.append(unit.model_copy(update={"statement": "", "proof": None}))

    return shared

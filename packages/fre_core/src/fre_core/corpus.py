"""Corpus catalog utilities."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from fre_core.latex_ingestion import ingest_latex_file
from fre_core.model_client import StructuredModelClient
from fre_core.schemas import SourceDocument, TheoremProofUnit
from fre_core.validation import ArtifactValidationError, load_unit

VALID_RELEASE_MODES = frozenset({"full_text_allowed", "metadata_only", "derived_annotations_only"})


class CorpusCatalog(BaseModel):
    schema_version: str = "0.1"
    sources: list[SourceDocument] = Field(default_factory=list)

    def by_source_id(self) -> dict[str, SourceDocument]:
        return {source.source_id: source for source in self.sources}


class CorpusValidationError(ValueError):
    """Raised when corpus metadata is missing or inconsistent."""


def load_corpus_catalog(path: Path) -> CorpusCatalog:
    return CorpusCatalog.model_validate_json(path.read_text(encoding="utf-8"))


def resolve_source_path(*, source: SourceDocument, repo_root: Path) -> Path:
    return repo_root / source.path


def validate_corpus_catalog(*, catalog: CorpusCatalog, repo_root: Path) -> None:
    if not catalog.sources:
        raise CorpusValidationError("Corpus catalog must contain at least one source.")
    seen: set[str] = set()
    release_modes: set[str] = set()
    for source in catalog.sources:
        if source.source_id in seen:
            raise CorpusValidationError(f"Duplicate source_id: {source.source_id!r}")
        seen.add(source.source_id)
        if source.release_mode not in VALID_RELEASE_MODES:
            raise CorpusValidationError(f"Invalid release_mode for {source.source_id!r}: {source.release_mode!r}")
        release_modes.add(source.release_mode)
        path = resolve_source_path(source=source, repo_root=repo_root)
        if not path.is_file():
            raise CorpusValidationError(f"Missing source file for {source.source_id}: {path.as_posix()}")
    if "full_text_allowed" not in release_modes:
        raise CorpusValidationError("Corpus catalog must include at least one full_text_allowed source.")
    if "metadata_only" not in release_modes:
        raise CorpusValidationError("Corpus catalog must include at least one metadata_only source for leak-test coverage.")


def validate_corpus_unit_spans(
    *,
    catalog: CorpusCatalog,
    repo_root: Path,
    units_dir: Path | None = None,
) -> None:
    """Validate that corpus unit source spans fall within resolved source files."""
    resolved_units_dir = units_dir or (repo_root / "corpus" / "units")
    if not resolved_units_dir.is_dir():
        raise CorpusValidationError(f"Missing corpus units directory: {resolved_units_dir.as_posix()}")

    sources = catalog.by_source_id()
    issues: list[str] = []
    for unit_path in sorted(resolved_units_dir.glob("*.json")):
        unit = TheoremProofUnit.model_validate_json(unit_path.read_text(encoding="utf-8"))
        if unit.statement_span is None and unit.proof_span is None:
            continue
        source = sources.get(unit.source_id)
        if source is None:
            issues.append(f"{unit_path.name}: unknown source_id {unit.source_id!r}")
            continue
        source_path = resolve_source_path(source=source, repo_root=repo_root)
        if not source_path.is_file():
            issues.append(f"{unit_path.name}: missing source file {source_path.as_posix()}")
            continue
        try:
            load_unit(unit_path, source_text=source_path.read_text(encoding="utf-8"))
        except ArtifactValidationError as exc:
            issues.append(f"{unit_path.name}: {exc}")

    if issues:
        raise CorpusValidationError("Corpus unit span validation failed:\n" + "\n".join(issues))


def ingest_catalog(*, catalog: CorpusCatalog, repo_root: Path, repair: bool = False, model_client: StructuredModelClient | None = None) -> list[TheoremProofUnit]:
    validate_corpus_catalog(catalog=catalog, repo_root=repo_root)
    units: list[TheoremProofUnit] = []
    for source in catalog.sources:
        units.extend(ingest_latex_file(path=resolve_source_path(source=source, repo_root=repo_root), source_id=source.source_id, domain=source.domain, repair=repair, model_client=model_client))
    validate_unit_sources(units=units, catalog=catalog)
    return units


def load_units_from_dir(units_dir: Path) -> list[TheoremProofUnit]:
    return [TheoremProofUnit.model_validate_json(p.read_text(encoding="utf-8")) for p in sorted(units_dir.glob("*.json"))]


def write_units(units: list[TheoremProofUnit], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for unit in units:
        target = output_dir / f"{unit.unit_id}.json"
        target.write_text(unit.model_dump_json(indent=2), encoding="utf-8")
        written.append(target)
    return written


def export_shareable_units(*, units: list[TheoremProofUnit], catalog: CorpusCatalog, include_text: bool = False) -> list[TheoremProofUnit]:
    validate_unit_sources(units=units, catalog=catalog)
    return make_shareable_units(units=units, catalog=catalog, include_text=include_text)


def validate_unit_sources(*, units: list[TheoremProofUnit], catalog: CorpusCatalog) -> None:
    sources = catalog.by_source_id()
    missing = sorted({unit.source_id for unit in units if unit.source_id not in sources})
    if missing:
        raise CorpusValidationError(f"Unknown source identifiers: {missing}")


def full_text_allowed(source: SourceDocument) -> bool:
    return source.release_mode == "full_text_allowed"


def derived_record_allowed(source: SourceDocument) -> bool:
    return source.release_mode in {"full_text_allowed", "metadata_only", "derived_annotations_only"}


def make_shareable_units(*, units: list[TheoremProofUnit], catalog: CorpusCatalog, include_text: bool = False) -> list[TheoremProofUnit]:
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
            shared.append(unit if full_text_allowed(source) else unit.model_copy(update={"statement": "", "proof": None}))
    return shared

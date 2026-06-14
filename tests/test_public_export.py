import json
from pathlib import Path

import pytest

from fre_core.corpus import ingest_catalog, load_corpus_catalog, write_units
from fre_core.public_export import (
    LicensingLeakError,
    assert_no_licensing_leak,
    export_public_atlas,
    export_public_benchmark,
)
from fre_core.schemas import TheoremProofUnit

ROOT = Path(__file__).resolve().parents[1]
SHAREABLE_CATALOG = ROOT / "examples" / "corpus_shareable" / "catalog.json"
FIXTURE_CATALOG = ROOT / "tests" / "fixtures" / "corpus" / "catalog_two_sources.json"
MANIFEST = ROOT / "benchmarks" / "readinessbench" / "manifest.json"


def test_export_public_benchmark_writes_all_tiers(tmp_path: Path) -> None:
    output_path = tmp_path / "readinessbench.jsonl"
    manifest = export_public_benchmark(
        output_path=output_path,
        manifest_path=MANIFEST,
        benchmark_root=MANIFEST.parent,
    )

    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert manifest.record_count == 13
    assert len(lines) == 13

    tiers = {json.loads(line)["tier"] for line in lines}
    assert tiers == {"bronze", "gold", "silver"}
    gold_count = sum(1 for line in lines if json.loads(line)["tier"] == "gold")
    assert gold_count == 11


def test_export_public_atlas_includes_examples(tmp_path: Path) -> None:
    output_path = tmp_path / "atlas.jsonl"
    manifest = export_public_atlas(output_path=output_path, repo_root=ROOT)

    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert manifest.record_count >= 2
    unit_ids = {json.loads(line)["unit_id"] for line in lines}
    assert "finite_tree_edge_count" in unit_ids


def test_metadata_only_sources_are_stripped_in_benchmark_export(tmp_path: Path) -> None:
    ingested_dir = tmp_path / "ingested"
    units = ingest_catalog(catalog=load_corpus_catalog(SHAREABLE_CATALOG), repo_root=ROOT)
    write_units(units, ingested_dir)

    restricted = next(
        unit for unit in units if unit.source_id == "shareable_metadata_only_001"
    )
    assert restricted.statement.strip()

    custom_manifest = {
        "schema_version": "0.1",
        "benchmark_id": "licensing_test",
        "items": [
            {
                "item_id": "metadata_only_item",
                "unit_id": restricted.unit_id,
                "tier": "bronze",
                "unit_path": "bronze/unit.json",
                "readiness_report_path": "bronze/readiness_report.json",
            }
        ],
    }
    bench_root = tmp_path / "bench"
    bronze_dir = bench_root / "bronze"
    bronze_dir.mkdir(parents=True)
    (bronze_dir / "unit.json").write_text(
        TheoremProofUnit.model_validate(restricted).model_dump_json(indent=2),
        encoding="utf-8",
    )
    (bronze_dir / "readiness_report.json").write_text(
        (ROOT / "benchmarks" / "readinessbench" / "bronze" / "finite_tree_edge_count" / "readiness_report.json").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    manifest_path = bench_root / "manifest.json"
    manifest_path.write_text(json.dumps(custom_manifest, indent=2), encoding="utf-8")

    output_path = tmp_path / "readinessbench.jsonl"
    export_public_benchmark(
        output_path=output_path,
        manifest_path=manifest_path,
        benchmark_root=bench_root,
        catalog_path=SHAREABLE_CATALOG,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8").splitlines()[0])
    exported_unit = payload["unit"]
    assert exported_unit["statement"] == ""
    assert exported_unit["proof"] is None

    assert_no_licensing_leak(
        jsonl_path=output_path,
        catalog=load_corpus_catalog(SHAREABLE_CATALOG),
        restricted_units=units,
    )


def test_licensing_leak_test_fails_when_text_present(tmp_path: Path) -> None:
    catalog = load_corpus_catalog(FIXTURE_CATALOG)
    leaked_unit = TheoremProofUnit(
        unit_id="metadata_only_source_unit",
        source_id="metadata_only_source",
        statement="Secret restricted statement text.",
        proof="Secret proof body.",
        domain="graph_theory",
    )
    record = {
        "schema_version": "0.1",
        "record_type": "benchmark_item",
        "item_id": "leak",
        "unit_id": leaked_unit.unit_id,
        "tier": "bronze",
        "unit": leaked_unit.model_dump(mode="json"),
        "readiness_report": {
            "schema_version": "0.1",
            "unit_id": leaked_unit.unit_id,
            "statement_readiness": {"status": "clear", "recovered": [], "unresolved": []},
            "context_readiness": {"status": "partial", "recovered": [], "unresolved": []},
            "notation_readiness": {"status": "partial", "recovered": [], "unresolved": []},
            "dependency_readiness": {"status": "partial", "recovered": [], "unresolved": []},
            "existing_theorem_candidates": ["Example.Theorem"],
            "constructive_path": ["step"],
            "blockers": ["blocker"],
            "recommended_next_action": "Review.",
        },
    }
    jsonl_path = tmp_path / "leak.jsonl"
    jsonl_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(LicensingLeakError):
        assert_no_licensing_leak(
            jsonl_path=jsonl_path,
            catalog=catalog,
            restricted_units=[leaked_unit],
        )

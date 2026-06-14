"""Tests for deterministic Atlas blocker clustering."""

from pathlib import Path

from fre_core.atlas_generator import (
    blocker_cluster_id,
    cluster_blocker_occurrences,
    collect_blocker_occurrences,
    generate_atlas_cluster_report,
    normalize_blocker_text,
)
from fre_core.benchmark import default_benchmark_root, default_manifest_path, validate_manifest
from fre_core.schemas import AtlasBlockerOccurrence

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = default_manifest_path(repo_root=ROOT)
BENCHMARK_ROOT = default_benchmark_root(repo_root=ROOT)


def test_normalize_blocker_text_is_stable() -> None:
    assert normalize_blocker_text("  Definition   Alignment ") == "definition alignment"
    assert blocker_cluster_id("definition alignment") == blocker_cluster_id("definition alignment")


def test_cluster_blocker_occurrences_is_deterministic() -> None:
    occurrences = [
        AtlasBlockerOccurrence(
            unit_id="u2",
            item_id="u2_gold",
            domain="algebra",
            blocker_text="Definition Alignment",
            normalized_text=normalize_blocker_text("Definition Alignment"),
        ),
        AtlasBlockerOccurrence(
            unit_id="u1",
            item_id="u1_gold",
            domain="algebra",
            blocker_text="definition alignment",
            normalized_text=normalize_blocker_text("definition alignment"),
        ),
        AtlasBlockerOccurrence(
            unit_id="u3",
            item_id="u3_gold",
            domain="topology",
            blocker_text="open cover transport",
            normalized_text=normalize_blocker_text("open cover transport"),
        ),
    ]

    first = cluster_blocker_occurrences(occurrences)
    second = cluster_blocker_occurrences(list(reversed(occurrences)))

    assert first.model_dump() == second.model_dump()
    assert first.cluster_count == 2
    assert first.clusters[0].occurrence_count == 2


def test_generate_atlas_cluster_report_from_manifest() -> None:
    validate_manifest(manifest=__import__("fre_core.benchmark", fromlist=["load_manifest"]).load_manifest(MANIFEST_PATH), benchmark_root=BENCHMARK_ROOT)
    report = generate_atlas_cluster_report(manifest_path=MANIFEST_PATH, benchmark_root=BENCHMARK_ROOT)
    assert report.cluster_count >= 1
    assert report.clusters == sorted(report.clusters, key=lambda cluster: cluster.normalized_text)
    occurrences = collect_blocker_occurrences(manifest_path=MANIFEST_PATH, benchmark_root=BENCHMARK_ROOT)
    assert len(occurrences) >= 20

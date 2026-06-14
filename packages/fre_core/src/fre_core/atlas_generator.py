"""Deterministic blocker clustering for the Formalization Gap Atlas."""

from __future__ import annotations

import hashlib
from pathlib import Path

from fre_core.benchmark import load_manifest, resolve_benchmark_path, validate_manifest
from fre_core.schemas import AtlasBlockerOccurrence, AtlasCluster, AtlasClusterReport
from fre_core.validation import load_readiness_report, load_unit


def normalize_blocker_text(text: str) -> str:
    """Normalize blocker text for stable clustering keys."""
    return " ".join(text.strip().lower().split())


def blocker_cluster_id(normalized_text: str) -> str:
    """Return a deterministic cluster identifier for normalized blocker text."""
    digest = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
    return digest[:16]


def collect_blocker_occurrences(
    *,
    manifest_path: Path,
    benchmark_root: Path | None = None,
) -> list[AtlasBlockerOccurrence]:
    """Collect readiness-report blockers from validated gold benchmark items."""
    root = benchmark_root or manifest_path.parent
    manifest = load_manifest(manifest_path)
    validate_manifest(manifest=manifest, benchmark_root=root)

    occurrences: list[AtlasBlockerOccurrence] = []
    for item in sorted(manifest.items, key=lambda entry: entry.item_id):
        if item.tier.value != "gold":
            continue
        report_path = resolve_benchmark_path(
            benchmark_root=root,
            relative_path=item.readiness_report_path,
            context=f"atlas cluster item {item.item_id!r} readiness_report_path",
        )
        report = load_readiness_report(report_path)
        unit_path = resolve_benchmark_path(
            benchmark_root=root,
            relative_path=item.unit_path,
            context=f"atlas cluster item {item.item_id!r} unit_path",
        )
        unit = load_unit(unit_path)
        for blocker in report.blockers:
            normalized = normalize_blocker_text(blocker)
            occurrences.append(
                AtlasBlockerOccurrence(
                    unit_id=item.unit_id,
                    item_id=item.item_id,
                    domain=unit.domain,
                    blocker_text=blocker,
                    normalized_text=normalized,
                )
            )

    return sorted(
        occurrences,
        key=lambda entry: (entry.normalized_text, entry.unit_id, entry.blocker_text),
    )


def cluster_blocker_occurrences(occurrences: list[AtlasBlockerOccurrence]) -> AtlasClusterReport:
    """Cluster blocker occurrences by normalized text with deterministic ordering."""
    grouped: dict[str, list[AtlasBlockerOccurrence]] = {}
    for occurrence in occurrences:
        grouped.setdefault(occurrence.normalized_text, []).append(occurrence)

    clusters: list[AtlasCluster] = []
    for normalized_text in sorted(grouped):
        members = sorted(
            grouped[normalized_text],
            key=lambda entry: (entry.unit_id, entry.blocker_text),
        )
        clusters.append(
            AtlasCluster(
                cluster_id=blocker_cluster_id(normalized_text),
                representative_text=members[0].blocker_text,
                normalized_text=normalized_text,
                occurrence_count=len(members),
                occurrences=members,
            )
        )

    return AtlasClusterReport(
        cluster_count=len(clusters),
        clusters=clusters,
    )


def generate_atlas_cluster_report(
    *,
    manifest_path: Path,
    benchmark_root: Path | None = None,
    source_label: str | None = None,
) -> AtlasClusterReport:
    """Build a cluster report from gold ReadinessBench blockers."""
    occurrences = collect_blocker_occurrences(
        manifest_path=manifest_path,
        benchmark_root=benchmark_root,
    )
    report = cluster_blocker_occurrences(occurrences)
    label = source_label or manifest_path.as_posix()
    return report.model_copy(update={"generated_from": label})


def write_atlas_cluster_report(*, report: AtlasClusterReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return output_path

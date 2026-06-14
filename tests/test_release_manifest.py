"""Tests for versioned release manifest generation."""

from pathlib import Path

from fre_core.release_manifest import build_release_manifest, collect_artifact_checksums


def test_collect_artifact_checksums_is_stable(tmp_path: Path) -> None:
    first = tmp_path / "a.jsonl"
    second = tmp_path / "b.jsonl"
    first.write_text('{"a": 1}\n', encoding="utf-8")
    second.write_text('{"b": 2}\n', encoding="utf-8")

    checksums = collect_artifact_checksums([second, first])

    assert [entry.path for entry in checksums] == [first.as_posix(), second.as_posix()]
    assert all(len(entry.sha256) == 64 for entry in checksums)
    assert checksums[0].byte_size == len(first.read_bytes())


def test_build_release_manifest_includes_schema_versions(tmp_path: Path) -> None:
    artifact = tmp_path / "readinessbench.jsonl"
    artifact.write_text("{}\n", encoding="utf-8")

    manifest = build_release_manifest(
        release_version="v0.2.0",
        artifact_paths=[artifact],
        git_commit="abc123",
    )

    assert manifest.release_version == "v0.2.0"
    assert manifest.git_commit == "abc123"
    assert manifest.schema_versions["readiness_report"] == "0.1"
    assert len(manifest.artifacts) == 1

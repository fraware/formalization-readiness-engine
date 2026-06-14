"""Tests for versioned release manifest generation."""

import hashlib
from pathlib import Path

from fre_core.release_manifest import (
    build_release_manifest,
    collect_artifact_checksums,
    normalize_text_artifact_line_endings,
    verify_release_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
V020_MANIFEST = ROOT / "releases" / "v0.2.0" / "manifest.json"
V020_EXPORTS = ROOT / "releases" / "v0.2.0" / "exports"


def test_collect_artifact_checksums_uses_repo_relative_paths(tmp_path: Path) -> None:
    repo_root = tmp_path
    first = repo_root / "a.jsonl"
    second = repo_root / "b.jsonl"
    first.write_text('{"a": 1}\n', encoding="utf-8")
    second.write_text('{"b": 2}\n', encoding="utf-8")

    checksums = collect_artifact_checksums([second, first], repo_root=repo_root)

    assert [entry.path for entry in checksums] == ["a.jsonl", "b.jsonl"]
    assert all(len(entry.sha256) == 64 for entry in checksums)
    assert checksums[0].byte_size == len(normalize_text_artifact_line_endings(first))


def test_build_release_manifest_includes_schema_versions(tmp_path: Path) -> None:
    artifact = tmp_path / "readinessbench.jsonl"
    artifact.write_text("{}\n", encoding="utf-8")

    manifest = build_release_manifest(
        release_version="v0.2.0",
        artifact_paths=[artifact],
        git_commit="abc123",
        repo_root=tmp_path,
    )

    assert manifest.release_version == "v0.2.0"
    assert manifest.git_commit == "abc123"
    assert manifest.schema_versions["readiness_report"] == "0.1"
    assert len(manifest.artifacts) == 1
    assert manifest.artifacts[0].path == "readinessbench.jsonl"


def test_crlf_jsonl_checksum_matches_lf_normalized_bytes(tmp_path: Path) -> None:
    artifact = tmp_path / "readinessbench.jsonl"
    artifact.write_bytes(b'{"id": 1}\r\n{"id": 2}\r\n')

    checksums = collect_artifact_checksums([artifact], repo_root=tmp_path)

    expected_bytes = normalize_text_artifact_line_endings(artifact)
    assert checksums[0].byte_size == len(expected_bytes)
    assert checksums[0].sha256 == hashlib.sha256(expected_bytes).hexdigest()


def test_committed_v020_manifest_matches_exports() -> None:
    manifest = verify_release_manifest(manifest_path=V020_MANIFEST, repo_root=ROOT)
    assert manifest.release_version == "v0.2.0"
    assert manifest.git_commit is not None
    assert len(manifest.git_commit) == 40
    assert len(manifest.artifacts) == 3
    for artifact in manifest.artifacts:
        assert (ROOT / artifact.path).is_file()
        assert artifact.path.startswith("releases/v0.2.0/exports/")

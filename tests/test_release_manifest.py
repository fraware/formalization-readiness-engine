"""Tests for versioned release manifest generation."""

import hashlib
import json
import re
import subprocess
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
V020_README = ROOT / "releases" / "v0.2.0" / "README.md"
ROOT_README = ROOT / "README.md"
PUBLIC_RELEASE = ROOT / "docs" / "PUBLIC_RELEASE.md"
EXPECTED_RELEASE_COMMIT = "f411fd5f1a6b6e4a5624970a26d1c33614b17f0b"


def _extract_frozen_commit_sha(text: str) -> str | None:
    match = re.search(
        r"(?:release bundle cut|frozen at git commit|Frozen v0\.2\.0 snapshot at)"
        r"[^\n]*?"
        r"([0-9a-f]{40})",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1)
    match = re.search(r"\[`([0-9a-f]{7,40})`\]", text)
    return match.group(1) if match else None


def _manifest_git_commit() -> str:
    payload = json.loads(V020_MANIFEST.read_text(encoding="utf-8"))
    commit = payload.get("git_commit")
    assert isinstance(commit, str) and len(commit) == 40
    return commit


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


def test_v020_manifest_git_commit_matches_release_docs() -> None:
    manifest_commit = _manifest_git_commit()
    assert manifest_commit == EXPECTED_RELEASE_COMMIT

    release_readme_sha = _extract_frozen_commit_sha(V020_README.read_text(encoding="utf-8"))
    root_readme_sha = _extract_frozen_commit_sha(ROOT_README.read_text(encoding="utf-8"))
    public_release_sha = _extract_frozen_commit_sha(PUBLIC_RELEASE.read_text(encoding="utf-8"))

    assert release_readme_sha is not None
    assert root_readme_sha is not None
    assert public_release_sha is not None

    for doc_sha in (release_readme_sha, root_readme_sha, public_release_sha):
        assert manifest_commit.startswith(doc_sha) or doc_sha.startswith(manifest_commit[: len(doc_sha)])

    assert manifest_commit.startswith("f411fd5")
    assert "56e48e83" in V020_README.read_text(encoding="utf-8")
    assert "Lean verification" in ROOT_README.read_text(encoding="utf-8")

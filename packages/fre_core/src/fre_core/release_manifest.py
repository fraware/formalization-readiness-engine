"""Versioned release manifest generation with artifact checksums."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from fre_core.schemas import ReleaseArtifactChecksum, ReleaseManifest

PUBLIC_SCHEMA_VERSIONS: dict[str, str] = {
    "readiness_report": "0.1",
    "theorem_proof_unit": "0.1",
    "atlas_record": "0.1",
    "atlas_cluster_report": "0.1",
    "benchmark_manifest": "0.1",
    "public_export_manifest": "0.1",
}

_TEXT_ARTIFACT_SUFFIXES = frozenset({".json", ".jsonl"})


def normalize_text_artifact_line_endings(path: Path, data: bytes | None = None) -> bytes:
    """Normalize CRLF to LF for text release artifacts so checksums match across platforms."""
    raw = data if data is not None else path.read_bytes()
    if path.suffix.lower() not in _TEXT_ARTIFACT_SUFFIXES:
        return raw
    return raw.replace(b"\r\n", b"\n")


def _artifact_bytes(path: Path) -> bytes:
    return normalize_text_artifact_line_endings(path)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(_artifact_bytes(path))


def collect_artifact_checksums(
    artifact_paths: list[Path],
    *,
    repo_root: Path,
) -> list[ReleaseArtifactChecksum]:
    """Compute stable checksum metadata for release artifacts."""
    resolved_root = repo_root.resolve()
    checksums: list[ReleaseArtifactChecksum] = []
    for path in sorted(artifact_paths, key=lambda entry: entry.as_posix()):
        resolved = path.resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Release artifact not found: {resolved.as_posix()}")
        try:
            relative_path = resolved.relative_to(resolved_root).as_posix()
        except ValueError as exc:
            raise ValueError(
                f"Release artifact {resolved.as_posix()} is outside repo root {resolved_root.as_posix()}."
            ) from exc
        artifact_bytes = _artifact_bytes(resolved)
        checksums.append(
            ReleaseArtifactChecksum(
                path=relative_path,
                sha256=_sha256_bytes(artifact_bytes),
                byte_size=len(artifact_bytes),
            )
        )
    return checksums


def resolve_git_commit(*, repo_root: Path | None = None) -> str | None:
    root = repo_root or Path(__file__).resolve().parents[4]
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def build_release_manifest(
    *,
    release_version: str,
    artifact_paths: list[Path],
    git_commit: str | None = None,
    repo_root: Path | None = None,
    schema_versions: dict[str, str] | None = None,
) -> ReleaseManifest:
    """Build a versioned release manifest for exported public artifacts."""
    root = repo_root or Path(__file__).resolve().parents[4]
    commit = git_commit if git_commit is not None else resolve_git_commit(repo_root=root)
    return ReleaseManifest(
        release_version=release_version,
        git_commit=commit,
        schema_versions=schema_versions or dict(PUBLIC_SCHEMA_VERSIONS),
        artifacts=collect_artifact_checksums(artifact_paths, repo_root=root),
    )


def write_release_manifest(*, manifest: ReleaseManifest, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return output_path


def verify_release_manifest(*, manifest_path: Path, repo_root: Path) -> ReleaseManifest:
    """Verify every artifact listed in a release manifest exists with matching checksums."""
    manifest = ReleaseManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    resolved_root = repo_root.resolve()
    for artifact in manifest.artifacts:
        artifact_path = resolved_root / artifact.path
        if not artifact_path.is_file():
            raise FileNotFoundError(f"Release artifact missing: {artifact.path}")
        artifact_bytes = _artifact_bytes(artifact_path)
        actual_sha256 = _sha256_bytes(artifact_bytes)
        if actual_sha256 != artifact.sha256:
            raise ValueError(
                f"Checksum mismatch for {artifact.path}: "
                f"expected {artifact.sha256}, got {actual_sha256}."
            )
        actual_size = len(artifact_bytes)
        if actual_size != artifact.byte_size:
            raise ValueError(
                f"Byte size mismatch for {artifact.path}: "
                f"expected {artifact.byte_size}, got {actual_size}."
            )
    return manifest

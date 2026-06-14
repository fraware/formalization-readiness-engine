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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_artifact_checksums(artifact_paths: list[Path]) -> list[ReleaseArtifactChecksum]:
    """Compute stable checksum metadata for release artifacts."""
    checksums: list[ReleaseArtifactChecksum] = []
    for path in sorted(artifact_paths, key=lambda entry: entry.as_posix()):
        resolved = path.resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Release artifact not found: {resolved.as_posix()}")
        checksums.append(
            ReleaseArtifactChecksum(
                path=resolved.as_posix(),
                sha256=_sha256_file(resolved),
                byte_size=resolved.stat().st_size,
            )
        )
    return checksums


def resolve_git_commit(*, repo_root: Path | None = None) -> str | None:
    root = repo_root or Path(__file__).resolve().parents[3]
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
    root = repo_root or Path(__file__).resolve().parents[3]
    commit = git_commit if git_commit is not None else resolve_git_commit(repo_root=root)
    return ReleaseManifest(
        release_version=release_version,
        git_commit=commit,
        schema_versions=schema_versions or dict(PUBLIC_SCHEMA_VERSIONS),
        artifacts=collect_artifact_checksums(artifact_paths),
    )


def write_release_manifest(*, manifest: ReleaseManifest, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return output_path

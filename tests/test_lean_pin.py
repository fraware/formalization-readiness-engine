"""Smoke tests for pinned Lean project essentials (Wave 0 / Sprint 2)."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LEAN_DIR = REPO_ROOT / "lean"

PINNED_FILES = (
    LEAN_DIR / "lean-toolchain",
    LEAN_DIR / "lake-manifest.json",
    LEAN_DIR / "README.md",
    LEAN_DIR / "lakefile.lean",
    LEAN_DIR / "FRETasks" / "Generated" / "FiniteTree.lean",
)


@pytest.mark.parametrize("path", PINNED_FILES, ids=lambda p: p.relative_to(REPO_ROOT).as_posix())
def test_lean_pin_file_exists(path: Path) -> None:
    assert path.is_file(), f"missing pinned Lean artifact: {path.relative_to(REPO_ROOT)}"


def test_lean_toolchain_pins_v4_8_0() -> None:
    content = (LEAN_DIR / "lean-toolchain").read_text(encoding="utf-8").strip()
    assert content == "leanprover/lean4:v4.8.0"


def test_lakefile_pins_mathlib_v4_8_0() -> None:
    content = (LEAN_DIR / "lakefile.lean").read_text(encoding="utf-8")
    assert ' @ "v4.8.0"' in content

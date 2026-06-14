#!/usr/bin/env python3
"""Export, trim, and build CI fixtures for mathlib DeclarationIndex artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "fixtures" / "mathlib_declarations"
DEFAULT_CI_OUTPUT = FIXTURES_DIR / "mathlib_v4.8.0.json"
CI_SOURCES = ("finite_tree_v0.json", "category_theory_v0.json")


def _ensure_path() -> None:
    src = REPO_ROOT / "packages" / "fre_core" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def build_ci_fixture(output: Path = DEFAULT_CI_OUTPUT) -> None:
    _ensure_path()
    from fre_core.schemas import DeclarationIndex

    merged, seen = [], set()
    for name in CI_SOURCES:
        index = DeclarationIndex.model_validate_json((FIXTURES_DIR / name).read_text(encoding="utf-8"))
        for decl in index.declarations:
            if decl.declaration_id not in seen:
                seen.add(decl.declaration_id)
                merged.append(decl)
    out = DeclarationIndex(
        schema_version="0.1",
        index_id="mathlib_v4.8.0_trimmed",
        description="Trimmed mathlib index for CI (finite_tree_v0 + category_theory_v0).",
        declarations=merged,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(out.model_dump_json(indent=2), encoding="utf-8")
    print(f"wrote {len(merged)} declarations to {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("export")
    sub.add_parser("trim")
    ci = sub.add_parser("build-ci-fixture")
    ci.add_argument("--output", type=Path, default=DEFAULT_CI_OUTPUT)
    args = parser.parse_args()
    if args.command == "build-ci-fixture":
        build_ci_fixture(args.output)
    else:
        print(f"{args.command} is a stub; use build-ci-fixture for CI.")


if __name__ == "__main__":
    main()

"""Apply Wave 6 implementation steps on engineering/wave6-release."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> None:
    run([sys.executable, str(ROOT / "scripts/_patch_schemas.py")])
    run([sys.executable, str(ROOT / "scripts/_patch_cli.py")])

    benchmark_test = ROOT / "tests/test_benchmark.py"
    text = (ROOT / "tests/test_benchmark.py")
    if "test_default_manifest_loads_and_validates" not in text.read_text(encoding="utf-8"):
        import subprocess as sp

        content = sp.check_output(["git", "show", "HEAD:tests/test_benchmark.py"], cwd=ROOT, text=True)
        benchmark_test.write_text(content, encoding="utf-8")

    run([sys.executable, str(ROOT / "scripts/_update_benchmark_counts.py")])
    run([sys.executable, str(ROOT / "scripts/_fix_benchmark_test.py")])
    run([sys.executable, str(ROOT / "scripts/seed_wave6_gold.py")])

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    if "docs:" not in makefile:
        makefile = makefile.replace(
            ".PHONY: setup setup-models",
            ".PHONY: setup setup-models docs",
        )
        insert = "\ndocs:\n\t$(PYTHON) -m pip install -r requirements-docs.txt\n\t$(PYTHON) -m mkdocs build -f apps/docs-site/mkdocs.yml\n\n"
        makefile = makefile.replace("setup:\n", insert + "setup:\n")
        (ROOT / "Makefile").write_text(makefile, encoding="utf-8")

    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    if "  docs:" not in ci:
        ci = ci.rstrip() + (
            "\n\n  docs:\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - uses: actions/setup-python@v5\n"
            "        with:\n          python-version: '3.11'\n"
            "      - name: Build documentation\n        run: |\n"
            "          python -m pip install --upgrade pip\n"
            "          python -m pip install -r requirements-docs.txt\n"
            "          python -m mkdocs build -f apps/docs-site/mkdocs.yml\n"
        )
        (ROOT / ".github/workflows/ci.yml").write_text(ci + "\n", encoding="utf-8")

    print("Wave 6 apply complete")


if __name__ == "__main__":
    main()

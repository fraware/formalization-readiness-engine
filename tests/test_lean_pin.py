from pathlib import Path


def test_lean_pin_files_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    lean_dir = root / "lean"

    assert (lean_dir / "lean-toolchain").is_file()
    assert (lean_dir / "lake-manifest.json").is_file()
    assert (lean_dir / "README.md").is_file()
    assert "leanprover/lean4:v4.8.0" in (lean_dir / "lean-toolchain").read_text(encoding="utf-8")


def test_lean_workflow_is_manual_dispatch_only() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "lean.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch" in workflow
    assert "pull_request" not in workflow

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_JS = ROOT / "apps" / "review-ui" / "app.js"

UNSAFE_INNERHTML_PATTERNS = (
    re.compile(r"\.innerHTML\s*="),
    re.compile(r"\.innerHTML\s*=\s*[^;]*\$\{unit\."),
    re.compile(r"\.innerHTML\s*=\s*[^;]*\$\{c\."),
)


def test_review_ui_avoids_innerhtml_for_loaded_data() -> None:
    source = APP_JS.read_text(encoding="utf-8")
    for pattern in UNSAFE_INNERHTML_PATTERNS:
        assert pattern.search(source) is None, (
            f"app.js must not use unsafe innerHTML ({pattern.pattern})"
        )


def test_review_ui_defines_safe_dom_helpers() -> None:
    source = APP_JS.read_text(encoding="utf-8")
    for helper in ("setText", "appendDl", "appendPre"):
        assert helper in source, f"app.js should define safe DOM helper {helper}"

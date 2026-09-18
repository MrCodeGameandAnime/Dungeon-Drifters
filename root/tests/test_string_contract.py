import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "src" / "app"
TARGET_METHODS = {
    "isascii",
    "isdecimal",
    "isdigit",
    "isnumeric",
    "strip",
    "lower",
    "upper",
    "startswith",
    "endswith",
    "split",
    "join",
    "replace",
}
UNSUPPORTED_RUNTIME_METHODS = {"isascii", "isdecimal"}


def _string_method_audit():
    calls = []
    for path in sorted(APP_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module = ".".join(path.relative_to(ROOT / "src").with_suffix("").parts)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr in TARGET_METHODS:
                calls.append((module, node.lineno, node.func.attr))
    return tuple(calls)


def test_runtime_string_method_audit_discovers_post_myp9_contract():
    calls = _string_method_audit()
    assert calls
    assert not {
        method for _, _, method in calls if method in UNSUPPORTED_RUNTIME_METHODS
    }
    assert any(method == "strip" for _, _, method in calls)


def test_tooling_string_methods_are_excluded_from_runtime_audit():
    tooling = (ROOT / "tools" / "scaffold_content.py").read_text(encoding="utf-8")
    assert ".isdecimal()" in tooling
    assert all(path.is_relative_to(APP_ROOT) for path in APP_ROOT.rglob("*.py"))

import ast
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1] / "src" / "app"


def _production_trees():
    for path in sorted(APP_ROOT.rglob("*.py")):
        yield path, ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _direct_zip_calls(tree):
    return tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "zip"
    )


def _strict_zip_calls(tree):
    return tuple(
        node
        for node in _direct_zip_calls(tree)
        if any(keyword.arg == "strict" for keyword in node.keywords)
    )


def test_production_builtin_zip_calls_have_no_strict_keyword():
    offenders = tuple(
        f"{path}:{node.lineno}: {ast.unparse(node)}"
        for path, tree in _production_trees()
        for node in _strict_zip_calls(tree)
    )

    assert offenders == ()


def test_strict_zip_classifier_targets_only_direct_builtin_name_calls():
    tree = ast.parse(
        """
zip(a, b)
zip(a, b, strict=True)
zip(a, b, strict=False)
zip(a, b, strict=value)
other(a, strict=True)
obj.zip(a, strict=True)
"""
    )

    calls = _direct_zip_calls(tree)
    assert len(calls) == 4
    assert len(_strict_zip_calls(tree)) == 3
    assert ast.unparse(calls[0]) == "zip(a, b)"

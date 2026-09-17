import ast
from pathlib import Path

import pytest

from app.iteration import first_or_none


APP_ROOT = Path(__file__).resolve().parents[1] / "src" / "app"


def _production_trees():
    for path in sorted(APP_ROOT.rglob("*.py")):
        yield path, ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _direct_default_next_calls(tree):
    return tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "next"
        and len(node.args) >= 2
    )


@pytest.mark.parametrize(
    "values",
    (
        (),
        (None,),
        (0,),
        (False,),
        ("",),
        ("a",),
        ("a", "b"),
    ),
)
def test_first_or_none_matches_native_next_default(values):
    assert first_or_none(iter(values)) == next(iter(values), None)


def test_first_or_none_is_lazy():
    events = []

    def values():
        events.append("first")
        yield 0
        events.append("second")
        yield 1

    assert first_or_none(values()) == 0
    assert events == ["first"]


def test_first_or_none_propagates_non_stop_iteration_exceptions():
    def broken_values():
        raise RuntimeError("unexpected iteration failure")
        yield None

    with pytest.raises(RuntimeError, match="unexpected iteration failure"):
        first_or_none(broken_values())


def test_production_has_no_direct_two_argument_next_calls():
    offenders = tuple(
        f"{path}:{node.lineno}: {ast.unparse(node)}"
        for path, tree in _production_trees()
        for node in _direct_default_next_calls(tree)
    )

    assert offenders == ()


def test_next_classifier_targets_only_direct_builtin_name_calls():
    tree = ast.parse(
        """
next(iterator)
next(iterator, None)
next(iterator, 0)
next(iterator, sentinel)
obj.next(iterator, None)
something_else(iterator, None)
"""
    )

    direct_calls = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "next"
    )

    assert len(direct_calls) == 4
    assert len(_direct_default_next_calls(tree)) == 3
    assert ast.unparse(direct_calls[0]) == "next(iterator)"

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "src" / "app"
SRC_ROOT = ROOT / "src"


def _module_name(path):
    return ".".join(path.relative_to(SRC_ROOT).with_suffix("").parts)


def _starred_contexts(tree):
    parents = {
        id(child): node
        for node in ast.walk(tree)
        for child in ast.iter_child_nodes(node)
    }
    contexts = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Starred):
            continue

        ancestor = parents.get(id(node))
        ancestors = []
        while ancestor is not None:
            ancestors.append(ancestor)
            ancestor = parents.get(id(ancestor))

        if isinstance(node.ctx, ast.Store):
            if any(isinstance(parent, (ast.For, ast.comprehension)) for parent in ancestors):
                context = "comprehension_or_for_target"
            else:
                context = "assignment_target"
        elif isinstance(parents.get(id(node)), ast.Tuple):
            context = "tuple_display_load"
        elif isinstance(parents.get(id(node)), ast.List):
            context = "list_display_load"
        elif isinstance(parents.get(id(node)), ast.Set):
            context = "set_display_load"
        elif isinstance(parents.get(id(node)), ast.Call):
            context = "function_call_starred_argument"
        else:
            context = "other"

        contexts.append((node.lineno, context))

    return tuple(contexts)


def _production_starred_contexts():
    occurrences = []
    for path in sorted(APP_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for line, context in _starred_contexts(tree):
            occurrences.append((_module_name(path), line, context))
    return tuple(occurrences)


def test_classifier_distinguishes_starred_expression_contexts():
    tree = ast.parse(
        """
result = (*values, final)
items = [*values]
members = {*values}
call(*values)
head, *tail = values
for *pair, in rows:
    pass
"""
    )

    contexts = {context for _, context in _starred_contexts(tree)}
    assert contexts == {
        "tuple_display_load",
        "list_display_load",
        "set_display_load",
        "function_call_starred_argument",
        "assignment_target",
        "comprehension_or_for_target",
    }


def test_production_has_no_load_context_starred_tuple_displays():
    occurrences = _production_starred_contexts()

    assert not [
        occurrence
        for occurrence in occurrences
        if occurrence[2] == "tuple_display_load"
    ]


def test_production_starred_audit_excludes_tests_and_tools():
    assert all(module.startswith("app.") for module, _, _ in _production_starred_contexts())

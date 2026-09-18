import ast
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1] / "src" / "app"


def _production_trees():
    for path in sorted(APP_ROOT.rglob("*.py")):
        yield path, ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _itertools_imports(tree):
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(
                alias
                for alias in node.names
                if alias.name == "itertools" or alias.name.startswith("itertools.")
            )
        elif isinstance(node, ast.ImportFrom) and node.module == "itertools":
            imports.extend(node.names)
    return tuple(imports)


def test_production_does_not_import_itertools():
    offenders = tuple(
        f"{path}:{node.lineno}: {ast.unparse(node)}"
        for path, tree in _production_trees()
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        and any(
            alias.name == "itertools" or alias.name.startswith("itertools.")
            for alias in node.names
        )
        or isinstance(node, ast.ImportFrom)
        and node.module == "itertools"
    )

    assert offenders == ()


def test_itertools_import_classifier_targets_only_itertools():
    tree = ast.parse(
        """
import itertools
import itertools as tools
from itertools import groupby
from itertools import count, groupby
from something_else import groupby
import unrelated_module
"""
    )

    imports = [
        node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    targeted = [
        node
        for node in imports
        if isinstance(node, ast.Import)
        and any(
            alias.name == "itertools" or alias.name.startswith("itertools.")
            for alias in node.names
        )
        or isinstance(node, ast.ImportFrom)
        and node.module == "itertools"
    ]
    allowed = [node for node in imports if node not in targeted]

    assert len(_itertools_imports(tree)) == 5
    assert len(targeted) == 4
    assert len(allowed) == 2
    assert isinstance(allowed[0], ast.ImportFrom)
    assert allowed[0].module == "something_else"
    assert isinstance(allowed[1], ast.Import)
    assert allowed[1].names[0].name == "unrelated_module"

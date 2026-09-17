import ast
import keyword
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "src" / "app"
TOOLS_ROOT = ROOT / "tools"
SUPPORTED = {"iskeyword"}
UNSUPPORTED = {
    "kwlist",
    "softkwlist",
    "issoftkeyword",
    "__all__",
}


def _runtime_keyword_usage():
    usage = []
    for path in sorted(APP_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        aliases = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "keyword":
                        aliases.add(alias.asname or "keyword")
            elif isinstance(node, ast.ImportFrom) and node.module == "keyword":
                usage.append((path, node.lineno, "from keyword import"))

        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute):
                continue
            if not isinstance(node.value, ast.Name) or node.value.id not in aliases:
                continue
            usage.append((path, node.lineno, node.attr))
    return tuple(usage)


def test_native_cpython_uses_stdlib_keyword():
    assert Path(keyword.__file__).resolve().parent != (
        ROOT / "portability" / "micropython"
    ).resolve()
    assert keyword.iskeyword("class") is True


def test_production_keyword_dependency_is_dynamically_discovered_and_narrow():
    usage = _runtime_keyword_usage()
    assert usage
    assert {entry[2] for entry in usage} == SUPPORTED
    assert not {entry[2] for entry in usage} & UNSUPPORTED


def test_tooling_keyword_variables_are_outside_runtime_audit():
    tooling_source = (TOOLS_ROOT / "generate_content_catalog.py").read_text(
        encoding="utf-8"
    )
    assert "import keyword" in tooling_source
    assert all(path.is_relative_to(APP_ROOT) for path, _, _ in _runtime_keyword_usage())


def test_native_keyword_contract_matches_required_hard_and_soft_distinction():
    assert all(keyword.iskeyword(value) for value in keyword.kwlist)
    assert keyword.iskeyword("goblin") is False
    assert keyword.iskeyword("ember_shard") is False
    assert keyword.iskeyword("dungeon_entrance") is False
    for value in keyword.softkwlist:
        assert keyword.iskeyword(value) is False


def test_overlay_does_not_duplicate_content_validation_rules():
    source = (ROOT / "portability" / "micropython" / "keyword.py").read_text(
        encoding="utf-8"
    )
    assert "goblin" not in source
    assert "ember_shard" not in source
    assert "dungeon_entrance" not in source
    assert "import re" not in source

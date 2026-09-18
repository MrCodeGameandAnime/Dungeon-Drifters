import ast
import enum
from pathlib import Path

from app.combat.move import MoveKind, ResourceType
from app.player.character_run_state import RunItemId


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "src" / "app"


def _enum_declarations():
    declarations = []
    for path in sorted(APP_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not any(
                isinstance(base, ast.Name) and base.id == "StrEnum"
                for base in node.bases
            ):
                continue
            module = ".".join(path.relative_to(ROOT / "src").with_suffix("").parts)
            declarations.append((module, node))
    return tuple(declarations)


def test_native_cpython_uses_stdlib_enum():
    assert enum.StrEnum.__module__ == "enum"
    assert Path(enum.__file__).resolve().parent != (
        ROOT / "portability" / "micropython"
    ).resolve()


def test_production_enum_surface_is_discovered_and_uses_only_portable_shape():
    declarations = _enum_declarations()
    assert declarations

    for module, node in declarations:
        assert [ast.unparse(base) for base in node.bases] == ["StrEnum"], module
        members = []
        for statement in node.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                raise AssertionError(f"custom enum method: {module}.{node.name}")
            targets = []
            if isinstance(statement, ast.Assign):
                targets = [target for target in statement.targets if isinstance(target, ast.Name)]
                value = statement.value
            elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                targets = [statement.target]
                value = statement.value
            else:
                continue
            for target in targets:
                if not target.id.isupper() or target.id.startswith("_"):
                    continue
                assert isinstance(value, ast.Constant), f"non-literal member: {module}.{node.name}.{target.id}"
                assert isinstance(value.value, str), f"non-string member: {module}.{node.name}.{target.id}"
                members.append((target.id, value.value))

        assert members, f"enum has no members: {module}.{node.name}"
        assert len({name for name, _ in members}) == len(members)
        assert len({value for _, value in members}) == len(members)


def test_production_does_not_use_unsupported_enum_type_operations():
    enum_names = {node.name for _, node in _enum_declarations()}
    unsupported = []
    for path in sorted(APP_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
                if node.value.id in enum_names:
                    unsupported.append((path, node.lineno, "class subscription"))
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in {"len", "iter", "list", "tuple"}:
                    if any(isinstance(argument, ast.Name) and argument.id in enum_names for argument in node.args):
                        unsupported.append((path, node.lineno, "enum iteration/length"))
    assert unsupported == []


def test_native_enum_contract_matches_real_dd_usage():
    assert MoveKind("damage") is MoveKind.DAMAGE
    assert ResourceType("mana") is ResourceType.MANA
    assert RunItemId("ember_shard") is RunItemId.EMBER_SHARD
    assert MoveKind.DAMAGE.value == "damage"
    assert MoveKind.DAMAGE.name == "DAMAGE"
    assert MoveKind.DAMAGE == "damage"
    assert str(MoveKind.DAMAGE) == "damage"
    assert isinstance(MoveKind.DAMAGE, MoveKind)
    assert {RunItemId.EMBER_SHARD: "found"}["ember_shard"] == "found"

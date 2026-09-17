import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
APP_ROOT = SRC_ROOT / "app"

SUPPORTED_TYPING_NAMES = {
    "Protocol",
    "runtime_checkable",
    "TypeAlias",
    "Sequence",
    "Union",
}
PROTOCOL_MODULES = {
    "app.combat.combatant": ("Combatant", "EnemyCombatant"),
    "app.ui.battle_ui": ("BattleUI",),
    "app.ui.overworld_ui": ("OverworldUI",),
}
TYPE_ALIAS_NAMES = {
    "BattleInput",
    "OverworldInput",
    "SessionView",
    "SessionInput",
}


def _module_name(path):
    return ".".join(path.relative_to(SRC_ROOT).with_suffix("").parts)


def _name(node):
    return node.id if isinstance(node, ast.Name) else None


def _union_members(node):
    if not isinstance(node, ast.Subscript):
        return None
    if _name(node.value) != "Union":
        return None
    slice_node = node.slice
    if isinstance(slice_node, ast.Tuple):
        return tuple(_name(element) for element in slice_node.elts)
    return (_name(slice_node),)


def _typing_audit():
    imports = []
    protocol_declarations = {}
    aliases = {}
    pep604 = []
    protocol_checks = []
    predicate_checks = []
    alias_uses = []
    unsupported_names = []

    for path in sorted(APP_ROOT.rglob("*.py")):
        module = _module_name(path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parents = {
            id(child): node
            for node in ast.walk(tree)
            for child in ast.iter_child_nodes(node)
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "typing" or alias.name.startswith("typing."):
                        imports.append((module, node.lineno, alias.name))
            elif isinstance(node, ast.ImportFrom) and node.module == "typing":
                for alias in node.names:
                    imports.append((module, node.lineno, alias.name))
                    if alias.name not in SUPPORTED_TYPING_NAMES:
                        unsupported_names.append((module, node.lineno, alias.name))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                protocol_bases = {
                    _name(base) for base in node.bases if _name(base) is not None
                }
                if "Protocol" in protocol_bases:
                    members = {"data": set(), "callable": set()}
                    for statement in node.body:
                        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            members["callable"].add(statement.name)
                        elif isinstance(statement, ast.AnnAssign):
                            target = _name(statement.target)
                            if target:
                                members["data"].add(target)
                        elif isinstance(statement, ast.Assign):
                            for target in statement.targets:
                                target_name = _name(target)
                                if target_name:
                                    members["data"].add(target_name)
                    for statement in node.body:
                        if isinstance(statement, ast.FunctionDef):
                            for decorator in statement.decorator_list:
                                if _name(decorator) == "property":
                                    members["callable"].discard(statement.name)
                                    members["data"].add(statement.name)
                    protocol_declarations[(module, node.name)] = {
                        "bases": tuple(_name(base) for base in node.bases),
                        "data": frozenset(members["data"]),
                        "callable": frozenset(members["callable"]),
                    }

            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if _name(node.annotation) == "TypeAlias":
                    aliases[node.target.id] = {
                        "module": module,
                        "line": node.lineno,
                        "value": node.value,
                        "union_members": _union_members(node.value),
                    }

            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
                ancestor = parents.get(id(node))
                context = "runtime_expression"
                while ancestor is not None:
                    if isinstance(ancestor, ast.AnnAssign):
                        if any(
                            descendant is node
                            for descendant in ast.walk(ancestor.annotation)
                        ):
                            context = "annotation"
                        elif ancestor.value is not None and any(
                            descendant is node
                            for descendant in ast.walk(ancestor.value)
                        ):
                            context = (
                                "type_alias_runtime_assignment"
                                if _name(ancestor.annotation) == "TypeAlias"
                                else "runtime_expression"
                            )
                        break
                    ancestor = parents.get(id(ancestor))
                pep604.append((module, node.lineno, context))

            if isinstance(node, ast.Call):
                function = node.func
                if _name(function) in {"isinstance", "issubclass"} and len(node.args) >= 2:
                    type_operand = _name(node.args[1])
                    if type_operand in TYPE_ALIAS_NAMES:
                        alias_uses.append((module, node.lineno, type_operand, "type_check"))
                    if type_operand in {"Combatant", "EnemyCombatant", "BattleUI", "OverworldUI"}:
                        protocol_checks.append((module, node.lineno, type_operand))
                if _name(function) in {
                    "is_combatant",
                    "is_enemy_combatant",
                    "is_battle_ui",
                    "is_overworld_ui",
                }:
                    predicate_checks.append((module, node.lineno, _name(function)))

            if isinstance(node, ast.Attribute) and _name(node.value) == "typing":
                unsupported_names.append((module, node.lineno, node.attr))

            if isinstance(node, ast.Name) and node.id in TYPE_ALIAS_NAMES:
                parent = parents.get(id(node))
                if not (
                    isinstance(parent, ast.AnnAssign)
                    and isinstance(parent.target, ast.Name)
                    and parent.target.id == node.id
                ):
                    alias_uses.append((module, node.lineno, node.id, "reference"))

    return {
        "imports": tuple(imports),
        "protocols": protocol_declarations,
        "aliases": aliases,
        "pep604": tuple(sorted(set(pep604))),
        "protocol_checks": tuple(sorted(set(protocol_checks))),
        "predicate_checks": tuple(sorted(set(predicate_checks))),
        "alias_uses": tuple(sorted(set(alias_uses))),
        "unsupported_names": tuple(unsupported_names),
    }


def test_typing_surface_is_dynamically_discovered_and_supported():
    audit = _typing_audit()

    assert audit["imports"]
    assert not audit["unsupported_names"]
    assert set(audit["aliases"]) == TYPE_ALIAS_NAMES


def test_pep604_audit_distinguishes_annotation_unions_from_runtime_aliases():
    audit = _typing_audit()

    assert audit["pep604"]
    assert any(context == "annotation" for _, _, context in audit["pep604"])
    assert all(alias["union_members"] is not None for alias in audit["aliases"].values())
    assert not any(context == "type_check" for *_, context in audit["alias_uses"])


def test_current_protocol_runtime_checks_are_explicitly_audited():
    audit = _typing_audit()

    assert audit["protocol_checks"] == ()
    assert {
        ("app.combat.battle", "is_enemy_combatant"),
        ("app.combat.resolver", "is_combatant"),
        ("app.game.overworld_session", "is_overworld_ui"),
    } == {
        (module, predicate)
        for module, _, predicate in audit["predicate_checks"]
    }


def test_protocol_declarations_have_expected_public_surface():
    audit = _typing_audit()

    assert set(audit["protocols"]) == {
        (module, name)
        for module, names in PROTOCOL_MODULES.items()
        for name in names
    }
    assert audit["protocols"][("app.combat.combatant", "EnemyCombatant")]["bases"] == (
        "Combatant",
        "Protocol",
    )


def test_typing_audit_excludes_non_runtime_paths():
    assert all(path.is_relative_to(APP_ROOT) for path in APP_ROOT.rglob("*.py"))
    assert not any("tools" in module for module, *_ in _typing_audit()["imports"])


def test_predicate_requirement_groups_match_protocol_ast():
    from app.combat.combatant import (
        _COMBATANT_CALLABLE_MEMBERS,
        _COMBATANT_DATA_MEMBERS,
        _ENEMY_COMBATANT_CALLABLE_MEMBERS,
        _ENEMY_COMBATANT_DATA_MEMBERS,
    )
    from app.ui.battle_ui import _BATTLE_UI_CALLABLE_MEMBERS
    from app.ui.overworld_ui import _OVERWORLD_UI_CALLABLE_MEMBERS

    audit = _typing_audit()["protocols"]
    combatant = audit[("app.combat.combatant", "Combatant")]
    enemy = audit[("app.combat.combatant", "EnemyCombatant")]
    battle_ui = audit[("app.ui.battle_ui", "BattleUI")]
    overworld_ui = audit[("app.ui.overworld_ui", "OverworldUI")]

    assert set(_COMBATANT_DATA_MEMBERS) == set(combatant["data"])
    assert set(_COMBATANT_CALLABLE_MEMBERS) == set(combatant["callable"])
    assert set(_ENEMY_COMBATANT_DATA_MEMBERS) == set(combatant["data"] | enemy["data"])
    assert set(_ENEMY_COMBATANT_CALLABLE_MEMBERS) == set(
        combatant["callable"] | enemy["callable"]
    )
    assert set(_BATTLE_UI_CALLABLE_MEMBERS) == set(battle_ui["callable"])
    assert set(_OVERWORLD_UI_CALLABLE_MEMBERS) == set(overworld_ui["callable"])


def test_native_protocols_and_predicates_agree_for_valid_structural_values():
    from app.combat.combatant import Combatant, is_combatant
    from app.ui.battle_ui import BattleUI, is_battle_ui
    from app.ui.overworld_ui import OverworldUI, is_overworld_ui

    class CombatantDouble:
        display_name = "double"
        health = object()
        mana_resource = object()
        super_resource = object()
        generates_super = True
        can_defend = True
        combat_moves = ()

        def effective_stat(self, name):
            return 1

        def defend_reduction_percent(self, damage_type):
            return 0

        def is_alive(self):
            return True

    class UIDouble:
        def render(self, view):
            pass

        def read_input(self, view):
            pass

    assert isinstance(CombatantDouble(), Combatant)
    assert is_combatant(CombatantDouble())
    assert isinstance(UIDouble(), BattleUI)
    assert isinstance(UIDouble(), OverworldUI)
    assert is_battle_ui(UIDouble())
    assert is_overworld_ui(UIDouble())

    class MissingMethod:
        render = None
        read_input = None

    assert not is_battle_ui(MissingMethod())
    assert not is_overworld_ui(MissingMethod())

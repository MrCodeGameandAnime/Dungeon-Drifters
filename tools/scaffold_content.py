"""Create conventional authored-content packages without overwriting work."""

import argparse
import ast
import re
import sys
from pathlib import Path
from textwrap import dedent

from tools.generate_content_catalog import (
    OUTPUT_PATH,
    ROOT,
    _validate_content_module_id,
    render_discovered_catalog,
    write_catalog,
)


CONTENT_LAYOUTS = {
    "enemy": ("enemies", "enemy.py", "ENEMY"),
    "weapon": ("weapons", "weapon.py", "WEAPON"),
    "drifter": ("drifters", "drifter.py", "DRIFTER"),
    "encounter": ("encounters", "encounter.py", "ENCOUNTER"),
    "route": ("routes", "route.py", "ROUTE"),
}
TODO_MARKER = "TODO(FLAT-CONTENT)"


def _write_text(path, source):
    with path.open("w", encoding="utf-8", newline="\n") as output:
        output.write(source)


def _title(content_id):
    return content_id.replace("_", " ").title()


def _persistence_key(content_id):
    return "".join(part.title() for part in content_id.split("_"))


def _content_roots(root):
    base = root / "src" / "app" / "content"
    return {
        "enemy_root": base / "enemies",
        "weapon_root": base / "weapons",
        "drifter_root": base / "drifters",
        "encounter_root": base / "encounters",
        "route_root": base / "routes",
    }


def _literal_keywords(path, assignment_name):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == assignment_name
            for target in node.targets
        ):
            continue
        if not isinstance(node.value, ast.Call):
            return {}
        values = {}
        for item in node.value.keywords:
            try:
                values[item.arg] = ast.literal_eval(item.value)
            except (TypeError, ValueError):
                continue
        return values
    return {}


def _existing_values(root, content_type, field):
    directory, primary_name, symbol = CONTENT_LAYOUTS[content_type]
    paths = (root / "src" / "app" / "content" / directory).glob(
        f"*/{primary_name}"
    )
    return {
        values[field]
        for path in paths
        if field in (values := _literal_keywords(path, symbol))
    }


def _existing_route_node_ids(root):
    route_root = root / "src" / "app" / "content" / "routes"
    node_ids = set()
    for path in route_root.glob("*/route.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function = node.func
            if not isinstance(function, ast.Name) or function.id != "RouteNodeSpec":
                continue
            if node.args:
                try:
                    value = ast.literal_eval(node.args[0])
                except (TypeError, ValueError):
                    continue
            else:
                keyword = next(
                    (item for item in node.keywords if item.arg == "node_id"),
                    None,
                )
                if keyword is None:
                    continue
                try:
                    value = ast.literal_eval(keyword.value)
                except (TypeError, ValueError):
                    continue
            if isinstance(value, str):
                node_ids.add(value)
    return node_ids


def _next_drifter_choice(root):
    choices = _existing_values(root, "drifter", "choice")
    integers = {int(choice) for choice in choices if str(choice).isdecimal()}
    value = 1
    while value in integers:
        value += 1
    return str(value)


def _first_existing_id(root, content_type, field):
    values = sorted(_existing_values(root, content_type, field))
    if not values:
        raise ValueError(f"cannot scaffold without an existing {content_type}")
    return values[0]


def _enemy_template(content_id):
    return dedent(
        f'''\
        """Authored {_title(content_id)} enemy content."""

        from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType
        from app.content.enemy_spec import EnemySpec, StatBlockSpec
        from app.enemies.definition import EnemyBehavior, EnemyCapability, EnemyRank, EnemyRole


        ENEMY = EnemySpec(
            archetype_id="{content_id}",
            name="{_title(content_id)}",  # {TODO_MARKER}
            stats=StatBlockSpec(1, 1, 1, 1, 1, 1),  # {TODO_MARKER}
            hp=1,  # {TODO_MARKER}
            mana=0,  # {TODO_MARKER}
            exp_reward=0,  # {TODO_MARKER}
            gold_reward=0,  # {TODO_MARKER}
            rank=EnemyRank.COMMON,  # {TODO_MARKER}
            role=EnemyRole.MELEE_SKIRMISHER,  # {TODO_MARKER}
            behavior=EnemyBehavior.AGGRESSIVE,  # {TODO_MARKER}
            capabilities=frozenset({{EnemyCapability.BASIC_ATTACKS}}),  # {TODO_MARKER}
            moves=(Move(
                name="Placeholder Strike",  # {TODO_MARKER}
                kind=MoveKind.DAMAGE,
                resource_type=ResourceType.NONE,
                resource_cost=0,
                power=1,  # {TODO_MARKER}
                scales_with=(ScalingAttribute.STRENGTH,),
                accuracy=100,
                target=TargetType.ENEMY,
                damage_type=DamageType.PHYSICAL,
                mechanic="basic_attack",
                description="Replace this placeholder move.",  # {TODO_MARKER}
            ),),
        )


        __all__ = ["ENEMY"]
        '''
    )


def _weapon_template(content_id):
    return dedent(
        f'''\
        """Authored {_title(content_id)} weapon content."""

        from app.content.weapon_spec import WeaponSpec


        WEAPON = WeaponSpec(
            item_id="{content_id}",
            persistence_key="{_persistence_key(content_id)}",  # {TODO_MARKER}
            name="{_title(content_id)}",  # {TODO_MARKER}
            weapon_type="Placeholder Weapon",  # {TODO_MARKER}
            intended_wielder="Unassigned",  # {TODO_MARKER}
            stat_bonuses={{}},  # {TODO_MARKER}
            value=0,  # {TODO_MARKER}
            description="Replace this placeholder weapon description.",  # {TODO_MARKER}
        )


        __all__ = ["WEAPON"]
        '''
    )


def _drifter_template(content_id, *, choice, weapon_id):
    return dedent(
        f'''\
        """Authored {_title(content_id)} Drifter content."""

        from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType
        from app.content.drifter_spec import ClassMechanicSpec, DrifterSpec, DrifterStatSpec


        DRIFTER = DrifterSpec(
            drifter_id="{content_id}",
            choice="{choice}",
            archetype_name="{_title(content_id)}",  # {TODO_MARKER}
            stats=DrifterStatSpec(10, 10, 10, 10, 10, 10),  # {TODO_MARKER}
            combat_moves=(Move(
                name="Placeholder Strike",  # {TODO_MARKER}
                kind=MoveKind.DAMAGE,
                resource_type=ResourceType.NONE,
                resource_cost=0,
                power=1,  # {TODO_MARKER}
                scales_with=(ScalingAttribute.STRENGTH,),
                accuracy=100,
                target=TargetType.ENEMY,
                damage_type=DamageType.PHYSICAL,
                mechanic="basic_attack",
                description="Replace this placeholder move.",  # {TODO_MARKER}
            ),),
            class_mechanic=ClassMechanicSpec("Placeholder", "Replace this mechanic."),  # {TODO_MARKER}
            starting_weapon_id="{weapon_id}",
            short_name="{_title(content_id)}",  # {TODO_MARKER}
            display_name="{_title(content_id)}",  # {TODO_MARKER}
            ascii_art="[art pending]",  # {TODO_MARKER}
            origin_title="Origin pending",  # {TODO_MARKER}
            biography="Biography pending",  # {TODO_MARKER}
            dungeon_motive="Motive pending",  # {TODO_MARKER}
            combat_role="Role pending",  # {TODO_MARKER}
            combat_summary="Summary pending",  # {TODO_MARKER}
            strengths="Strengths pending",  # {TODO_MARKER}
            weaknesses="Weaknesses pending",  # {TODO_MARKER}
            weapon="Weapon pending",  # {TODO_MARKER}
            discipline="Discipline pending",  # {TODO_MARKER}
            quote="Quote pending",  # {TODO_MARKER}
            selection_summary="Selection summary pending",  # {TODO_MARKER}
        )


        __all__ = ["DRIFTER"]
        '''
    )


def _encounter_template(content_id, *, enemy_id):
    return dedent(
        f'''\
        """Authored {_title(content_id)} encounter content."""

        from app.content.encounter_spec import EncounterSpec


        ENCOUNTER = EncounterSpec(
            encounter_id="{content_id}",
            enemy_archetype_ids=("{enemy_id}",),  # {TODO_MARKER}
        )


        __all__ = ["ENCOUNTER"]
        '''
    )


def _route_template(content_id):
    return dedent(
        f'''\
        """Authored {_title(content_id)} route content."""

        from app.content.route_spec import RouteNodeKind, RouteNodeSpec, RouteSpec


        ROUTE = RouteSpec(
            route_id="{content_id}",
            nodes=(RouteNodeSpec(
                node_id="{content_id}_start",
                display_label="{_title(content_id)} Start",  # {TODO_MARKER}
                kind=RouteNodeKind.REST,  # {TODO_MARKER}
            ),),
        )


        __all__ = ["ROUTE"]
        '''
    )


def _test_template(content_type, content_id):
    symbol = CONTENT_LAYOUTS[content_type][2]
    lookup = {
        "enemy": f'get_enemy_spec("{content_id}")',
        "weapon": f'get_weapon_spec("{content_id}")',
        "drifter": f'get_drifter_spec("{content_id}")',
        "encounter": f'get_encounter_spec("{content_id}")',
        "route": f'get_route_spec("{content_id}")',
    }[content_type]
    factory = {
        "enemy": f'create_enemy_state("{content_id}")',
        "weapon": f'create_weapon("{content_id}")',
        "drifter": f'create_drifter("{content_id}")',
    }.get(content_type)
    imports = {
        "enemy": "create_enemy_state, get_enemy_spec",
        "weapon": "create_weapon, get_weapon_spec",
        "drifter": "create_drifter, get_drifter_spec",
        "encounter": "get_encounter_spec, get_enemy_spec",
        "route": "get_route_node_spec, get_route_spec, get_route_successor_id",
    }[content_type]
    assertions = [f"    assert {lookup} is {symbol}"]
    if factory:
        assertions.extend(
            [f"    first = {factory}", f"    second = {factory}", "    assert first is not second"]
        )
    elif content_type == "encounter":
        assertions.append("    assert all(get_enemy_spec(value) for value in ENCOUNTER.enemy_archetype_ids)")
    else:
        assertions.extend(
            [
                "    assert all(get_route_node_spec(node.node_id) is node for node in ROUTE.nodes)",
                "    assert get_route_successor_id(ROUTE.nodes[-1].node_id) is None",
            ]
        )
    body = "\n".join(f"    {line.strip()}" for line in assertions)
    return (
        f"from app.content.catalog import {imports}\n"
        "from app.content."
        f"{CONTENT_LAYOUTS[content_type][0]}.{content_id}."
        f"{CONTENT_LAYOUTS[content_type][1][:-3]} import {symbol}\n\n\n"
        f"def test_{content_id}_{content_type}_identity_and_construction():\n"
        f"{body}\n"
    )


def scaffold_content(content_type, content_id, *, root=ROOT):
    if content_type not in CONTENT_LAYOUTS:
        raise ValueError(f"unknown content type: {content_type}")
    _validate_content_module_id(content_id)
    root = Path(root)
    directory, primary_name, symbol = CONTENT_LAYOUTS[content_type]
    package = root / "src" / "app" / "content" / directory / content_id
    primary = package / primary_name
    package_init = package / "__init__.py"
    test_path = root / "tests" / f"test_content_{content_type}_{content_id}.py"
    output_path = root / "src" / "app" / "content" / "_generated_catalog.py"

    collisions = [path for path in (package, primary, package_init, test_path) if path.exists()]
    if content_id in _existing_values(root, content_type, {
        "enemy": "archetype_id",
        "weapon": "item_id",
        "drifter": "drifter_id",
        "encounter": "encounter_id",
        "route": "route_id",
    }[content_type]):
        collisions.append(Path(f"catalog:{content_type}:{content_id}"))
    if content_type == "weapon" and _persistence_key(content_id) in _existing_values(root, "weapon", "persistence_key"):
        collisions.append(Path(f"persistence-key:{_persistence_key(content_id)}"))
    if content_type == "route" and f"{content_id}_start" in _existing_route_node_ids(root):
        collisions.append(Path(f"route-node:{content_id}_start"))
    if collisions:
        raise FileExistsError(f"scaffold collision: {collisions[0]}")

    drifter_choice = None
    if content_type == "drifter":
        drifter_choice = _next_drifter_choice(root)
        if drifter_choice in _existing_values(root, "drifter", "choice"):
            raise FileExistsError(f"Drifter choice collision: {drifter_choice}")

    if content_type == "enemy":
        source = _enemy_template(content_id)
    elif content_type == "weapon":
        source = _weapon_template(content_id)
    elif content_type == "drifter":
        source = _drifter_template(
            content_id,
            choice=drifter_choice,
            weapon_id=_first_existing_id(root, "weapon", "item_id"),
        )
    elif content_type == "encounter":
        source = _encounter_template(
            content_id,
            enemy_id=_first_existing_id(root, "enemy", "archetype_id"),
        )
    else:
        source = _route_template(content_id)

    old_catalog = output_path.read_bytes() if output_path.exists() else None
    created = []
    try:
        package.mkdir()
        created.append(package)
        _write_text(
            package_init,
            f"from .{primary_name[:-3]} import {symbol}\n\n__all__ = [\"{symbol}\"]\n",
        )
        _write_text(primary, source)
        _write_text(test_path, _test_template(content_type, content_id))
        catalog = render_discovered_catalog(**_content_roots(root))
        write_catalog(catalog, output_path)
    except Exception:
        if old_catalog is None:
            output_path.unlink(missing_ok=True)
        else:
            output_path.write_bytes(old_catalog)
        if test_path.exists():
            test_path.unlink()
        if package.exists():
            for path in sorted(package.iterdir(), reverse=True):
                path.unlink()
            package.rmdir()
        raise
    return primary, test_path, output_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("content_type", choices=tuple(CONTENT_LAYOUTS))
    parser.add_argument("content_id")
    args = parser.parse_args(argv)
    try:
        primary, test_path, _ = scaffold_content(args.content_type, args.content_id)
    except (FileExistsError, TypeError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    print(f"created {primary.relative_to(ROOT)}")
    print(f"created {test_path.relative_to(ROOT)}")
    print(f"complete every {TODO_MARKER} marker, then run python -m tools.validate_content")


if __name__ == "__main__":
    main()

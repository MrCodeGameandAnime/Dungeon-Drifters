"""Read-only validation for authored Dungeon Drifters content."""

import argparse
import dataclasses
import importlib
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from tools.generate_content_catalog import (
    OUTPUT_PATH,
    ROOT,
    discover_drifter_ids,
    discover_encounter_ids,
    discover_enemy_ids,
    discover_route_ids,
    discover_weapon_ids,
    render_discovered_catalog,
)


SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.combat.resolver import authored_move_rejection_reason
from app.content.drifter_spec import DrifterSpec
from app.content.encounter_spec import EncounterSpec
from app.content.enemy_spec import EnemySpec
from app.content.route_spec import RouteNodeKind, RouteSpec
from app.content.weapon_spec import WeaponSpec
from app.enemies.state import EnemyState


TODO_MARKER = "TODO(FLAT-CONTENT)"
CONTENT_TYPES = {
    "enemy": ("enemies", "enemy", "ENEMY", EnemySpec, discover_enemy_ids),
    "weapon": ("weapons", "weapon", "WEAPON", WeaponSpec, discover_weapon_ids),
    "drifter": ("drifters", "drifter", "DRIFTER", DrifterSpec, discover_drifter_ids),
    "encounter": (
        "encounters",
        "encounter",
        "ENCOUNTER",
        EncounterSpec,
        discover_encounter_ids,
    ),
    "route": ("routes", "route", "ROUTE", RouteSpec, discover_route_ids),
}


def _relative(path):
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _error(errors, path, message):
    errors.append(f"{_relative(path)}: {message}")


def _discover_and_import(errors):
    records = {content_type: [] for content_type in CONTENT_TYPES}
    for content_type, (directory, module_name, symbol, spec_type, discover) in CONTENT_TYPES.items():
        root = ROOT / "src" / "app" / "content" / directory
        try:
            content_ids = discover(root)
        except (OSError, SyntaxError, TypeError, ValueError) as error:
            _error(errors, root, str(error))
            continue
        for content_id in content_ids:
            path = root / content_id / f"{module_name}.py"
            source = path.read_text(encoding="utf-8")
            if TODO_MARKER in source:
                _error(errors, path, f"unfinished {TODO_MARKER} marker")
            qualified = f"app.content.{directory}.{content_id}.{module_name}"
            try:
                module = importlib.import_module(qualified)
            except Exception as error:
                _error(errors, path, f"cannot import content: {error}")
                continue
            if getattr(module, "__all__", None) != [symbol]:
                _error(errors, path, f"__all__ must be exactly [\"{symbol}\"]")
            value = getattr(module, symbol, None)
            if type(value) is not spec_type:
                _error(errors, path, f"{symbol} must be exactly {spec_type.__name__}")
                continue
            if not dataclasses.is_dataclass(value) or not value.__dataclass_params__.frozen:
                _error(errors, path, f"{symbol} must be an immutable dataclass")
            records[content_type].append((content_id, value, path))
    return records


def _duplicates(records, attribute, label, errors):
    seen = {}
    for _, spec, path in records:
        value = getattr(spec, attribute)
        if value in seen:
            _error(errors, path, f"duplicate {label} {value!r}; first defined in {_relative(seen[value])}")
        else:
            seen[value] = path


def _validate_moves(records, errors):
    for _, spec, path in records["enemy"]:
        try:
            if spec.supported_tiers != (0,):
                _error(errors, path, "supported_tiers must remain exactly (0,)")
            definition = spec.create_definition()
            second_definition = spec.create_definition()
            first = EnemyState(definition)
            second = EnemyState(second_definition)
            if (
                definition is second_definition
                or first is second
                or first.health is second.health
                or first.mana_resource is second.mana_resource
                or first.super_resource is second.super_resource
                or first.permanent_stats is second.permanent_stats
            ):
                _error(errors, path, "enemy construction must return fresh runtime owners")
        except (KeyError, TypeError, ValueError) as error:
            _error(errors, path, f"enemy construction failed: {error}")
        for move in spec.moves:
            reason = authored_move_rejection_reason(move)
            if reason is not None:
                _error(errors, path, f"move {move.name!r} is rejected by CombatResolver: {reason}")
    for _, spec, path in records["drifter"]:
        for move in spec.combat_moves:
            reason = authored_move_rejection_reason(move)
            if reason is not None:
                _error(errors, path, f"move {move.name!r} is rejected by CombatResolver: {reason}")


def _validate_references_and_factories(records, errors):
    enemies = {spec.archetype_id: spec for _, spec, _ in records["enemy"]}
    weapons = {spec.item_id: spec for _, spec, _ in records["weapon"]}
    encounters = {spec.encounter_id: spec for _, spec, _ in records["encounter"]}
    node_paths = {}

    for _, spec, path in records["weapon"]:
        try:
            first = spec.create_weapon()
            second = spec.create_weapon()
            if first is second or first.stat_bonuses is second.stat_bonuses:
                _error(errors, path, "weapon construction must return fresh runtime objects")
            if first.item_id != spec.item_id or first.persistence_key != spec.persistence_key:
                _error(errors, path, "weapon runtime identity differs from authored identity")
        except (KeyError, TypeError, ValueError) as error:
            _error(errors, path, f"weapon construction failed: {error}")

    for _, spec, path in records["drifter"]:
        if spec.starting_weapon_id not in weapons:
            _error(errors, path, f"unknown starting weapon ID {spec.starting_weapon_id!r}")
        try:
            first = spec.create_character()
            second = spec.create_character()
            if first is second or first.health is second.health or first.mana_resource is second.mana_resource:
                _error(errors, path, "Drifter construction must return fresh runtime owners")
        except (KeyError, TypeError, ValueError) as error:
            _error(errors, path, f"Drifter construction failed: {error}")

    for _, spec, path in records["encounter"]:
        for enemy_id in spec.enemy_archetype_ids:
            if enemy_id not in enemies:
                _error(errors, path, f"unknown enemy archetype ID {enemy_id!r}")

    for _, route, path in records["route"]:
        for index, node in enumerate(route.nodes):
            if node.node_id in node_paths:
                _error(errors, path, f"duplicate global route node ID {node.node_id!r}; first defined in {_relative(node_paths[node.node_id])}")
            else:
                node_paths[node.node_id] = path
            if node.encounter_id is not None and node.encounter_id not in encounters:
                _error(errors, path, f"unknown encounter ID {node.encounter_id!r}")
            if node.kind in {RouteNodeKind.COMBAT, RouteNodeKind.BOSS} and node.encounter_id is None:
                _error(errors, path, f"combat node {node.node_id!r} requires an encounter")
            if index + 1 < len(route.nodes) and route.nodes[index + 1] is node:
                _error(errors, path, "route successors must derive from distinct ordered nodes")


def _validate_catalog(errors):
    try:
        expected = render_discovered_catalog()
        actual = OUTPUT_PATH.read_text(encoding="utf-8")
    except (OSError, SyntaxError, TypeError, ValueError) as error:
        _error(errors, OUTPUT_PATH, str(error))
        return
    if actual != expected:
        _error(errors, OUTPUT_PATH, "generated content catalog is stale; run python -m tools.generate_content_catalog")


def _validate_schema_round_trips(records, errors):
    try:
        from app.content.catalog import (
            create_enemy_state,
            create_weapon,
            get_route_node_spec,
            get_route_successor_id,
        )
        from app.game.game_state import GameState
        from app.game.save_state import build_save_document, reconstruct_game_state
        from app.player.player_state import PlayerState
    except (ImportError, KeyError, TypeError, ValueError) as error:
        _error(errors, ROOT / "src/app/game/save_state.py", f"cannot load schema-8 boundary: {error}")
        return

    for _, spec, path in records["enemy"]:
        first = create_enemy_state(spec.archetype_id)
        second = create_enemy_state(spec.archetype_id)
        if (
            first is second
            or first.health is second.health
            or first.mana_resource is second.mana_resource
            or first.super_resource is second.super_resource
            or first.permanent_stats is second.permanent_stats
        ):
            _error(errors, path, "catalog enemy construction reuses runtime state")
    for _, spec, path in records["weapon"]:
        if create_weapon(spec.item_id) is create_weapon(spec.item_id):
            _error(errors, path, "catalog weapon construction reuses runtime state")
    for _, route, path in records["route"]:
        for index, node in enumerate(route.nodes):
            expected = (
                route.nodes[index + 1].node_id
                if index + 1 < len(route.nodes)
                else None
            )
            if get_route_node_spec(node.node_id) is not node:
                _error(errors, path, f"catalog route-node identity drift for {node.node_id!r}")
            if get_route_successor_id(node.node_id) != expected:
                _error(errors, path, f"catalog successor drift for {node.node_id!r}")
    for _, spec, path in records["drifter"]:
        try:
            document = build_save_document(GameState(PlayerState(spec.create_character())))
            rebuilt = reconstruct_game_state(document)
            if build_save_document(rebuilt) != document:
                _error(errors, path, "schema-8 build/reconstruct/build payload drift")
        except (KeyError, TypeError, ValueError) as error:
            _error(errors, path, f"schema-8 reconstruction failed: {error}")


def validate_content():
    """Return deterministic validation errors without changing repository files."""
    errors = []
    _validate_catalog(errors)
    records = _discover_and_import(errors)
    _duplicates(records["enemy"], "archetype_id", "enemy ID", errors)
    _duplicates(records["weapon"], "item_id", "weapon ID", errors)
    _duplicates(records["weapon"], "persistence_key", "weapon persistence key", errors)
    _duplicates(records["drifter"], "drifter_id", "Drifter ID", errors)
    _duplicates(records["drifter"], "choice", "Drifter choice", errors)
    _duplicates(records["encounter"], "encounter_id", "encounter ID", errors)
    _duplicates(records["route"], "route_id", "route ID", errors)
    _validate_moves(records, errors)
    _validate_references_and_factories(records, errors)
    if not errors:
        _validate_schema_round_trips(records, errors)
    return tuple(sorted(set(errors))), records


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        errors, records = validate_content()
    except Exception as error:
        print(f"ERROR content validation failed: {error}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    plurals = {
        "enemy": "enemies",
        "weapon": "weapons",
        "drifter": "drifters",
        "encounter": "encounters",
        "route": "routes",
    }
    counts = ", ".join(
        f"{len(records[name])} {name if len(records[name]) == 1 else plurals[name]}"
        for name in ("enemy", "weapon", "drifter", "encounter", "route")
    )
    print(f"content valid: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

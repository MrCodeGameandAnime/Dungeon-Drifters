"""Immutable authored encounter data for the M10 surface route."""

from dataclasses import dataclass
from types import MappingProxyType

from app.enemies.factory import create_enemy_definition, create_enemy_state
from app.game.overworld_route import (
    RouteNodeKind,
    SURFACE_ROUTE_NODES,
)


def _validate_text(name, value):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must be nonempty")


def _validate_nonnegative_int(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must not be negative")


@dataclass(frozen=True)
class EncounterManifest:
    encounter_id: str
    enemy_archetype_ids: tuple[str, ...]
    exp_reward: int
    gold_reward: int
    boss: bool

    def __post_init__(self):
        _validate_text("encounter_id", self.encounter_id)
        if not isinstance(self.enemy_archetype_ids, tuple):
            raise TypeError("enemy_archetype_ids must be a tuple")
        if not self.enemy_archetype_ids:
            raise ValueError("enemy_archetype_ids must not be empty")
        for archetype_id in self.enemy_archetype_ids:
            _validate_text("enemy archetype ID", archetype_id)
        _validate_nonnegative_int("exp_reward", self.exp_reward)
        _validate_nonnegative_int("gold_reward", self.gold_reward)
        if not isinstance(self.boss, bool):
            raise TypeError("boss must be a boolean")


@dataclass(frozen=True)
class RouteManifestNode:
    node_id: str
    next_node_id: str | None
    encounter: EncounterManifest | None = None

    def __post_init__(self):
        _validate_text("node_id", self.node_id)
        if self.next_node_id is not None:
            _validate_text("next_node_id", self.next_node_id)
        if self.encounter is not None and not isinstance(
            self.encounter,
            EncounterManifest,
        ):
            raise TypeError("encounter must be an EncounterManifest or None")


def _encounter(node_id, enemies, *, boss=False):
    definitions = tuple(
        create_enemy_definition(archetype_id, tier=0)
        for archetype_id in enemies
    )
    return EncounterManifest(
        encounter_id=node_id,
        enemy_archetype_ids=enemies,
        exp_reward=sum(definition.exp_reward for definition in definitions),
        gold_reward=sum(definition.gold_reward for definition in definitions),
        boss=boss,
    )


_MANIFEST_DETAILS = {
    "surface_goblin_solo": (
        "surface_goblin_pair",
        _encounter("surface_goblin_solo", ("goblin",)),
    ),
    "surface_goblin_pair": (
        "surface_warrior_solo",
        _encounter("surface_goblin_pair", ("goblin", "goblin")),
    ),
    "surface_warrior_solo": (
        "surface_rest_after_warrior_solo",
        _encounter("surface_warrior_solo", ("goblin_warrior",)),
    ),
    "surface_rest_after_warrior_solo": (
        "surface_warrior_pair",
        None,
    ),
    "surface_warrior_pair": (
        "surface_shaman_solo",
        _encounter(
            "surface_warrior_pair",
            ("goblin_warrior", "goblin_warrior"),
        ),
    ),
    "surface_shaman_solo": (
        "surface_shaman_pair",
        _encounter("surface_shaman_solo", ("goblin_shaman",)),
    ),
    "surface_shaman_pair": (
        "surface_rest_after_shaman_pair",
        _encounter(
            "surface_shaman_pair",
            ("goblin_shaman", "goblin_shaman"),
        ),
    ),
    "surface_rest_after_shaman_pair": (
        "surface_elite_patrol",
        None,
    ),
    "surface_elite_patrol": (
        "surface_rest_before_goblin_lord",
        _encounter(
            "surface_elite_patrol",
            ("goblin_elite", "goblin"),
        ),
    ),
    "surface_rest_before_goblin_lord": (
        "surface_goblin_lord",
        None,
    ),
    "surface_goblin_lord": (
        "surface_dungeon_entrance",
        _encounter(
            "surface_goblin_lord",
            ("goblin_lord", "goblin", "goblin_warrior"),
            boss=True,
        ),
    ),
    "surface_dungeon_entrance": (None, None),
}


SURFACE_ROUTE_MANIFEST = tuple(
    RouteManifestNode(
        node_id=node.node_id,
        next_node_id=_MANIFEST_DETAILS[node.node_id][0],
        encounter=_MANIFEST_DETAILS[node.node_id][1],
    )
    for node in SURFACE_ROUTE_NODES
)

_ROUTE_MANIFEST_BY_NODE_ID = MappingProxyType(
    {node.node_id: node for node in SURFACE_ROUTE_MANIFEST}
)
_ENCOUNTER_MANIFEST_BY_ID = MappingProxyType(
    {
        node.encounter.encounter_id: node.encounter
        for node in SURFACE_ROUTE_MANIFEST
        if node.encounter is not None
    }
)


def route_manifest_node(node_id):
    if not isinstance(node_id, str):
        raise TypeError("node_id must be a string")
    try:
        return _ROUTE_MANIFEST_BY_NODE_ID[node_id]
    except KeyError as error:
        raise ValueError(f"unknown surface route node: {node_id!r}") from error


def encounter_manifest(encounter_id):
    if not isinstance(encounter_id, str):
        raise TypeError("encounter_id must be a string")
    try:
        return _ENCOUNTER_MANIFEST_BY_ID[encounter_id]
    except KeyError as error:
        raise ValueError(f"unknown surface encounter: {encounter_id!r}") from error


def inspectable_encounter_for_node(node_id):
    node = route_manifest_node(node_id)
    while node is not None:
        if node.encounter is not None:
            return node.encounter
        if node.next_node_id is None:
            return None
        node = route_manifest_node(node.next_node_id)
    return None


def create_route_encounter_enemies(
    node_id,
    *,
    enemy_factory=create_enemy_state,
):
    if not callable(enemy_factory):
        raise TypeError("enemy_factory must be callable")
    node = route_manifest_node(node_id)
    if node.encounter is None:
        raise ValueError(f"route node does not define an encounter: {node_id!r}")
    return tuple(
        enemy_factory(archetype_id, tier=0)
        for archetype_id in node.encounter.enemy_archetype_ids
    )


def _validate_surface_route_manifest():
    if set(_MANIFEST_DETAILS) != {node.node_id for node in SURFACE_ROUTE_NODES}:
        raise ValueError("surface route manifest must cover every route node exactly")
    if len(_ROUTE_MANIFEST_BY_NODE_ID) != len(SURFACE_ROUTE_NODES):
        raise ValueError("surface route manifest node IDs must be unique")
    if len(_ENCOUNTER_MANIFEST_BY_ID) != 8:
        raise ValueError("surface route manifest must contain eight unique encounters")

    for index, (shell, manifest) in enumerate(
        zip(SURFACE_ROUTE_NODES, SURFACE_ROUTE_MANIFEST, strict=True)
    ):
        if shell.node_id != manifest.node_id:
            raise ValueError("surface route manifest order must match the route shell")
        expected_next = (
            SURFACE_ROUTE_NODES[index + 1].node_id
            if index + 1 < len(SURFACE_ROUTE_NODES)
            else None
        )
        if manifest.next_node_id != expected_next:
            raise ValueError("route nodes must point to their immediate successor")

        requires_encounter = shell.kind in {
            RouteNodeKind.COMBAT,
            RouteNodeKind.BOSS,
        }
        if requires_encounter != (manifest.encounter is not None):
            raise ValueError("only combat and Boss nodes may define encounters")
        if manifest.encounter is not None:
            if manifest.encounter.encounter_id != shell.node_id:
                raise ValueError("encounter IDs must match their route node IDs")
            if manifest.encounter.boss != (shell.kind is RouteNodeKind.BOSS):
                raise ValueError("Boss flags must match the route node kind")


_validate_surface_route_manifest()


__all__ = [
    "EncounterManifest",
    "RouteManifestNode",
    "SURFACE_ROUTE_MANIFEST",
    "create_route_encounter_enemies",
    "encounter_manifest",
    "inspectable_encounter_for_node",
    "route_manifest_node",
]

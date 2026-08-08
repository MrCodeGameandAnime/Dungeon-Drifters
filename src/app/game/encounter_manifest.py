"""Immutable authored encounter data for the M10 surface route."""

from dataclasses import dataclass
from types import MappingProxyType

from app.content.catalog import (
    get_encounter_spec,
    get_encounter_rewards,
    get_inspectable_encounter_spec,
    get_route_spec,
    get_route_successor_id,
)
from app.content.route_spec import RouteNodeKind
from app.enemies.factory import create_enemy_state
from app.game.overworld_route import SURFACE_ROUTE_NODES


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


def _encounter(node):
    authored = get_encounter_spec(node.encounter_id)
    enemies = authored.enemy_archetype_ids
    exp_reward, gold_reward = get_encounter_rewards(authored.encounter_id)
    return EncounterManifest(
        encounter_id=authored.encounter_id,
        enemy_archetype_ids=enemies,
        exp_reward=exp_reward,
        gold_reward=gold_reward,
        boss=node.kind is RouteNodeKind.BOSS,
    )


_SURFACE_ROUTE_SPEC = get_route_spec("surface")
SURFACE_ROUTE_MANIFEST = tuple(
    RouteManifestNode(
        node_id=node.node_id,
        next_node_id=get_route_successor_id(node.node_id),
        encounter=_encounter(node) if node.encounter_id is not None else None,
    )
    for node in _SURFACE_ROUTE_SPEC.nodes
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
    encounter = get_inspectable_encounter_spec(node_id)
    if encounter is None:
        return None
    return encounter_manifest(encounter.encounter_id)


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

"""Test-only conveniences derived from the public content catalog."""

from app.content.catalog import (
    create_enemy_state,
    get_encounter_spec,
    get_route_node_spec,
    get_route_spec,
)
from app.content.route_spec import RouteNodeKind


SURFACE_ROUTE_NODES = get_route_spec("surface").nodes
SURFACE_ROUTE_NODE_IDS = tuple(node.node_id for node in SURFACE_ROUTE_NODES)
SURFACE_REST_NODE_IDS = tuple(
    node.node_id for node in SURFACE_ROUTE_NODES if node.kind is RouteNodeKind.REST
)
FIRST_SURFACE_NODE_ID = SURFACE_ROUTE_NODE_IDS[0]
SECOND_SURFACE_NODE_ID = SURFACE_ROUTE_NODE_IDS[1]
DUNGEON_ENTRANCE_NODE_ID = SURFACE_ROUTE_NODE_IDS[-1]


def create_route_encounter_enemies(node_id, *, enemy_factory=create_enemy_state):
    if not callable(enemy_factory):
        raise TypeError("enemy_factory must be callable")
    node = get_route_node_spec(node_id)
    if node.encounter_id is None:
        raise ValueError(f"route node does not define an encounter: {node_id!r}")
    encounter = get_encounter_spec(node.encounter_id)
    return tuple(
        enemy_factory(archetype_id, tier=0)
        for archetype_id in encounter.enemy_archetype_ids
    )


__all__ = [
    "DUNGEON_ENTRANCE_NODE_ID",
    "FIRST_SURFACE_NODE_ID",
    "SECOND_SURFACE_NODE_ID",
    "SURFACE_REST_NODE_IDS",
    "SURFACE_ROUTE_NODE_IDS",
    "SURFACE_ROUTE_NODES",
    "create_route_encounter_enemies",
]

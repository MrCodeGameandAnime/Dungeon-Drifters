"""Immutable authored route shell used by overworld state and presentation."""

from dataclasses import dataclass
from enum import StrEnum


class RouteNodeKind(StrEnum):
    COMBAT = "combat"
    REST = "rest"
    BOSS = "boss"
    DUNGEON_ENTRANCE = "dungeon_entrance"


@dataclass(frozen=True)
class RouteNodeShell:
    node_id: str
    display_label: str
    kind: RouteNodeKind

    def __post_init__(self):
        for field_name in ("node_id", "display_label"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a nonempty string")
        object.__setattr__(self, "kind", RouteNodeKind(self.kind))


SURFACE_ROUTE_NODES = (
    RouteNodeShell("surface_goblin_solo", "Goblin Ambush", RouteNodeKind.COMBAT),
    RouteNodeShell("surface_goblin_pair", "Goblin Pair", RouteNodeKind.COMBAT),
    RouteNodeShell("surface_warrior_solo", "Goblin Warrior", RouteNodeKind.COMBAT),
    RouteNodeShell(
        "surface_rest_after_warrior_solo",
        "Woodland Rest",
        RouteNodeKind.REST,
    ),
    RouteNodeShell("surface_warrior_pair", "Warrior Patrol", RouteNodeKind.COMBAT),
    RouteNodeShell("surface_shaman_solo", "Goblin Shaman", RouteNodeKind.COMBAT),
    RouteNodeShell("surface_shaman_pair", "Shaman Pair", RouteNodeKind.COMBAT),
    RouteNodeShell(
        "surface_rest_after_shaman_pair",
        "Ritual Clearing Rest",
        RouteNodeKind.REST,
    ),
    RouteNodeShell("surface_elite_patrol", "Elite Patrol", RouteNodeKind.COMBAT),
    RouteNodeShell(
        "surface_rest_before_goblin_lord",
        "Final Approach Rest",
        RouteNodeKind.REST,
    ),
    RouteNodeShell("surface_goblin_lord", "Goblin Lord", RouteNodeKind.BOSS),
    RouteNodeShell(
        "surface_dungeon_entrance",
        "Dungeon Entrance",
        RouteNodeKind.DUNGEON_ENTRANCE,
    ),
)

SURFACE_ROUTE_NODE_IDS = tuple(node.node_id for node in SURFACE_ROUTE_NODES)
SURFACE_REST_NODE_IDS = tuple(
    node.node_id for node in SURFACE_ROUTE_NODES if node.kind is RouteNodeKind.REST
)
FIRST_SURFACE_NODE_ID = SURFACE_ROUTE_NODE_IDS[0]
SECOND_SURFACE_NODE_ID = SURFACE_ROUTE_NODE_IDS[1]
DUNGEON_ENTRANCE_NODE_ID = SURFACE_ROUTE_NODE_IDS[-1]


def route_node(node_id):
    if not isinstance(node_id, str):
        raise TypeError("node_id must be a string")
    for node in SURFACE_ROUTE_NODES:
        if node.node_id == node_id:
            return node
    raise ValueError(f"unknown surface route node: {node_id!r}")

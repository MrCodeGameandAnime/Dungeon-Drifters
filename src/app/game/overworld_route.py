"""Immutable authored route shell used by overworld state and presentation."""

from dataclasses import dataclass
from types import MappingProxyType

from app.content.catalog import get_route_spec
from app.content.route_spec import RouteNodeKind


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


_SURFACE_ROUTE_SPEC = get_route_spec("surface")
SURFACE_ROUTE_NODES = tuple(
    RouteNodeShell(node.node_id, node.display_label, node.kind)
    for node in _SURFACE_ROUTE_SPEC.nodes
)

SURFACE_ROUTE_NODE_IDS = tuple(node.node_id for node in SURFACE_ROUTE_NODES)
SURFACE_REST_NODE_IDS = tuple(
    node.node_id for node in SURFACE_ROUTE_NODES if node.kind is RouteNodeKind.REST
)
FIRST_SURFACE_NODE_ID = SURFACE_ROUTE_NODE_IDS[0]
SECOND_SURFACE_NODE_ID = SURFACE_ROUTE_NODE_IDS[1]
DUNGEON_ENTRANCE_NODE_ID = SURFACE_ROUTE_NODE_IDS[-1]
_SURFACE_ROUTE_BY_NODE_ID = MappingProxyType(
    {node.node_id: node for node in SURFACE_ROUTE_NODES}
)


def route_node(node_id):
    if not isinstance(node_id, str):
        raise TypeError("node_id must be a string")
    try:
        return _SURFACE_ROUTE_BY_NODE_ID[node_id]
    except KeyError as error:
        raise ValueError(f"unknown surface route node: {node_id!r}") from error


__all__ = [
    "DUNGEON_ENTRANCE_NODE_ID",
    "FIRST_SURFACE_NODE_ID",
    "RouteNodeKind",
    "RouteNodeShell",
    "SECOND_SURFACE_NODE_ID",
    "SURFACE_REST_NODE_IDS",
    "SURFACE_ROUTE_NODE_IDS",
    "SURFACE_ROUTE_NODES",
    "route_node",
]

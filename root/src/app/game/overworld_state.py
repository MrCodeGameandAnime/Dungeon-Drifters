"""Persistent route-session state for one active game."""

from enum import StrEnum

from app.content.catalog import get_route_node_spec, get_route_spec
from app.content.route_spec import RouteNodeKind
from app.snapshot import to_plain_value


_DEFAULT_ROUTE_ID = "surface"
_SURFACE_ROUTE = get_route_spec(_DEFAULT_ROUTE_ID)
_SURFACE_ROUTE_NODE_IDS = tuple(node.node_id for node in _SURFACE_ROUTE.nodes)
_SURFACE_REST_NODE_IDS = tuple(
    node.node_id
    for node in _SURFACE_ROUTE.nodes
    if node.kind is RouteNodeKind.REST
)
_FIRST_SURFACE_NODE_ID = _SURFACE_ROUTE_NODE_IDS[0]
_DUNGEON_ENTRANCE_NODE_ID = _SURFACE_ROUTE_NODE_IDS[-1]


class ContextualRoutePhase(StrEnum):
    ENTER_ENCOUNTER = "enter_encounter"
    RETRY = "retry"
    NONE = "none"


class OverworldState:
    def __init__(self):
        self._active_route_id = _DEFAULT_ROUTE_ID
        self._current_route_node_id = _FIRST_SURFACE_NODE_ID
        self._surface_route_begun = False
        self._dungeon_entrance_reached = False
        self._route_complete = False
        self._resolved_rest_node_ids = set()
        self._current_contextual_route_phase = (
            ContextualRoutePhase.ENTER_ENCOUNTER
        )

    @property
    def current_route_node_id(self):
        return self._current_route_node_id

    @property
    def active_route_id(self):
        return self._active_route_id

    @property
    def surface_route_begun(self):
        return self._surface_route_begun

    @property
    def dungeon_entrance_reached(self):
        return self._dungeon_entrance_reached

    @property
    def route_complete(self):
        return self._route_complete

    @property
    def resolved_rest_node_ids(self):
        route = get_route_spec(self.active_route_id)
        return tuple(
            node.node_id
            for node in route.nodes
            if node.kind is RouteNodeKind.REST
            and node.node_id in self._resolved_rest_node_ids
        )

    @property
    def current_contextual_route_phase(self):
        return self._current_contextual_route_phase

    def begin_surface_route(self):
        self._surface_route_begun = True

    def begin_route(self, route_id):
        try:
            route = get_route_spec(route_id)
        except (TypeError, ValueError) as error:
            raise ValueError(f"unknown route: {route_id!r}") from error
        self._active_route_id = route.route_id
        self._current_route_node_id = route.nodes[0].node_id
        self._route_complete = False
        self._resolved_rest_node_ids = set()
        self._current_contextual_route_phase = (
            ContextualRoutePhase.ENTER_ENCOUNTER
        )

    def return_to_surface_entrance(self):
        if not self.dungeon_entrance_reached:
            raise ValueError("the Surface dungeon entrance has not been reached")
        self._active_route_id = _DEFAULT_ROUTE_ID
        self._current_route_node_id = _DUNGEON_ENTRANCE_NODE_ID
        self._resolved_rest_node_ids = set(_SURFACE_REST_NODE_IDS)
        self._route_complete = True
        self._current_contextual_route_phase = ContextualRoutePhase.NONE

    def set_contextual_route_phase(self, phase):
        self._current_contextual_route_phase = ContextualRoutePhase(phase)

    def advance_to(self, node_id, *, contextual_phase=ContextualRoutePhase.NONE):
        route = get_route_spec(self.active_route_id)
        route_node_ids = tuple(node.node_id for node in route.nodes)
        try:
            node = get_route_node_spec(node_id)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"unknown {self.active_route_id} route node: {node_id!r}"
            ) from error
        phase = ContextualRoutePhase(contextual_phase)
        if self.route_complete:
            raise ValueError("the active route is already complete")

        current_index = route_node_ids.index(
            self.current_route_node_id
        )
        next_index = current_index + 1
        if (
            next_index >= len(route_node_ids)
            or node.node_id != route_node_ids[next_index]
        ):
            raise ValueError(
                "route advancement must use the immediate authored successor"
            )

        self._current_route_node_id = node.node_id
        self._current_contextual_route_phase = phase
        if self.active_route_id == _DEFAULT_ROUTE_ID and node.node_id == _DUNGEON_ENTRANCE_NODE_ID:
            self._dungeon_entrance_reached = True
        if next_index == len(route_node_ids) - 1:
            self._route_complete = True

    def record_resolved_rest_node(self, node_id):
        try:
            node = get_route_node_spec(node_id)
        except (TypeError, ValueError) as error:
            raise ValueError(f"not an authored Rest node: {node_id!r}") from error
        route_node_ids = {
            route_node.node_id
            for route_node in get_route_spec(self.active_route_id).nodes
        }
        if node.node_id not in route_node_ids or node.kind is not RouteNodeKind.REST:
            raise ValueError(f"not an authored Rest node: {node_id!r}")
        self._resolved_rest_node_ids.add(node_id)

    @classmethod
    def from_snapshot(cls, snapshot):
        state = cls()
        state._active_route_id = snapshot.get("active_route_id", _DEFAULT_ROUTE_ID)
        state._current_route_node_id = snapshot["current_route_node_id"]
        state._surface_route_begun = snapshot["surface_route_begun"]
        state._dungeon_entrance_reached = snapshot["dungeon_entrance_reached"]
        state._route_complete = snapshot["route_complete"]
        state._resolved_rest_node_ids = set(
            snapshot["resolved_rest_node_ids"]
        )
        state._current_contextual_route_phase = ContextualRoutePhase(
            snapshot["current_contextual_route_phase"]
        )
        return state

    def snapshot(self):
        snapshot = {
            "active_route_id": self.active_route_id,
            "current_route_node_id": self.current_route_node_id,
            "surface_route_begun": self.surface_route_begun,
            "dungeon_entrance_reached": self.dungeon_entrance_reached,
            "route_complete": self.route_complete,
            "resolved_rest_node_ids": list(self.resolved_rest_node_ids),
            "current_contextual_route_phase": (
                self.current_contextual_route_phase.value
            ),
        }
        return to_plain_value(snapshot, "overworld")

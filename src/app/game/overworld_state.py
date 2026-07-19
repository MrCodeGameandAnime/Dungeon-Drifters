"""Persistent route-session state for one active game."""

from enum import StrEnum

from app.game.overworld_route import (
    DUNGEON_ENTRANCE_NODE_ID,
    FIRST_SURFACE_NODE_ID,
    SURFACE_REST_NODE_IDS,
    SURFACE_ROUTE_NODE_IDS,
    route_node,
)
from app.snapshot import to_plain_value


class ContextualRoutePhase(StrEnum):
    ENTER_ENCOUNTER = "enter_encounter"
    RETRY = "retry"
    NONE = "none"


class OverworldState:
    def __init__(self):
        self._current_route_node_id = FIRST_SURFACE_NODE_ID
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
        return tuple(
            node_id
            for node_id in SURFACE_REST_NODE_IDS
            if node_id in self._resolved_rest_node_ids
        )

    @property
    def current_contextual_route_phase(self):
        return self._current_contextual_route_phase

    def begin_surface_route(self):
        self._surface_route_begun = True

    def set_contextual_route_phase(self, phase):
        self._current_contextual_route_phase = ContextualRoutePhase(phase)

    def advance_to(self, node_id, *, contextual_phase=ContextualRoutePhase.NONE):
        node = route_node(node_id)
        phase = ContextualRoutePhase(contextual_phase)
        if self.route_complete:
            raise ValueError("the surface route is already complete")

        current_index = SURFACE_ROUTE_NODE_IDS.index(
            self.current_route_node_id
        )
        next_index = current_index + 1
        if (
            next_index >= len(SURFACE_ROUTE_NODE_IDS)
            or node.node_id != SURFACE_ROUTE_NODE_IDS[next_index]
        ):
            raise ValueError(
                "route advancement must use the immediate authored successor"
            )

        self._current_route_node_id = node.node_id
        self._current_contextual_route_phase = phase
        if node.node_id == DUNGEON_ENTRANCE_NODE_ID:
            self._dungeon_entrance_reached = True
            self._route_complete = True

    def record_resolved_rest_node(self, node_id):
        if node_id not in SURFACE_REST_NODE_IDS:
            raise ValueError(f"not an authored Rest node: {node_id!r}")
        self._resolved_rest_node_ids.add(node_id)

    def snapshot(self):
        return to_plain_value(
            {
                "current_route_node_id": self.current_route_node_id,
                "surface_route_begun": self.surface_route_begun,
                "dungeon_entrance_reached": self.dungeon_entrance_reached,
                "route_complete": self.route_complete,
                "resolved_rest_node_ids": list(self.resolved_rest_node_ids),
                "current_contextual_route_phase": (
                    self.current_contextual_route_phase.value
                ),
            },
            "overworld",
        )

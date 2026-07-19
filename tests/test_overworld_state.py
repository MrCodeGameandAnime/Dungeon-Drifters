import pytest

from app.game.overworld_route import (
    DUNGEON_ENTRANCE_NODE_ID,
    FIRST_SURFACE_NODE_ID,
    SECOND_SURFACE_NODE_ID,
    SURFACE_REST_NODE_IDS,
)
from app.game.overworld_state import ContextualRoutePhase, OverworldState


def test_new_overworld_state_starts_at_the_first_authored_node():
    state = OverworldState()

    assert state.current_route_node_id == FIRST_SURFACE_NODE_ID
    assert state.surface_route_begun is False
    assert state.dungeon_entrance_reached is False
    assert state.route_complete is False
    assert state.resolved_rest_node_ids == ()
    assert (
        state.current_contextual_route_phase
        is ContextualRoutePhase.ENTER_ENCOUNTER
    )


def test_route_phase_and_node_validation_are_typed_and_explicit():
    state = OverworldState()

    state.begin_surface_route()
    state.set_contextual_route_phase(ContextualRoutePhase.RETRY)
    state.advance_to(SECOND_SURFACE_NODE_ID)

    assert state.surface_route_begun is True
    assert state.current_route_node_id == SECOND_SURFACE_NODE_ID
    assert state.current_contextual_route_phase is ContextualRoutePhase.NONE

    with pytest.raises(ValueError, match="unknown surface route node"):
        state.advance_to("not_a_route_node")
    with pytest.raises(ValueError, match="not an authored Rest node"):
        state.record_resolved_rest_node(FIRST_SURFACE_NODE_ID)
    with pytest.raises(ValueError):
        state.set_contextual_route_phase("not_a_phase")


def test_resolved_rest_nodes_follow_authored_order_not_resolution_order():
    state = OverworldState()

    state.record_resolved_rest_node(SURFACE_REST_NODE_IDS[2])
    state.record_resolved_rest_node(SURFACE_REST_NODE_IDS[0])

    assert state.resolved_rest_node_ids == (
        SURFACE_REST_NODE_IDS[0],
        SURFACE_REST_NODE_IDS[2],
    )
    assert state.snapshot()["resolved_rest_node_ids"] == [
        SURFACE_REST_NODE_IDS[0],
        SURFACE_REST_NODE_IDS[2],
    ]


def test_overworld_snapshot_is_plain_deterministic_and_defensive():
    state = OverworldState()
    state.begin_surface_route()
    state.set_contextual_route_phase(ContextualRoutePhase.RETRY)
    state.record_resolved_rest_node(SURFACE_REST_NODE_IDS[1])

    first = state.snapshot()
    second = state.snapshot()

    assert first == second
    assert first == {
        "current_route_node_id": FIRST_SURFACE_NODE_ID,
        "surface_route_begun": True,
        "dungeon_entrance_reached": False,
        "route_complete": False,
        "resolved_rest_node_ids": [SURFACE_REST_NODE_IDS[1]],
        "current_contextual_route_phase": "retry",
    }
    assert isinstance(first["current_contextual_route_phase"], str)
    assert first["resolved_rest_node_ids"] is not second["resolved_rest_node_ids"]

    first["resolved_rest_node_ids"].append("changed")
    first["current_route_node_id"] = "changed"

    assert state.snapshot() == second


def test_reaching_dungeon_entrance_sets_route_completion_facts():
    state = OverworldState()

    state.advance_to(DUNGEON_ENTRANCE_NODE_ID)

    assert state.dungeon_entrance_reached is True
    assert state.route_complete is True
    assert state.current_contextual_route_phase is ContextualRoutePhase.NONE


def test_independent_overworld_states_share_no_mutable_state():
    first = OverworldState()
    second = OverworldState()

    first.begin_surface_route()
    first.record_resolved_rest_node(SURFACE_REST_NODE_IDS[0])

    assert second.surface_route_begun is False
    assert second.resolved_rest_node_ids == ()

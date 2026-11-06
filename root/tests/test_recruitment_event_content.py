from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from app.content import catalog
from app.content.recruitment_event_spec import RecruitmentEventSpec
from app.game.party_state import DungeonPhase
from app.game.recruitment import available_recruitment_event


def test_floor_one_recruitment_event_is_authored_in_the_content_catalog():
    assert hasattr(catalog, "RECRUITMENT_EVENT_SPECS")
    assert hasattr(catalog, "get_recruitment_event")

    event = catalog.get_recruitment_event("floor_one_d2_recruitment")
    assert event.route_id == "surface"
    assert event.route_node_id == "surface_dungeon_entrance"
    assert event.candidate_drifter_ids == (
        "branoc",
        "azhvielle",
        "zhaivra",
        "joruun",
    )
    assert event.cost == 65

    with pytest.raises(FrozenInstanceError):
        event.cost = 1


def test_floor_two_d3_recruitment_event_is_authored_at_midway_rest():
    event = catalog.get_recruitment_event("floor_two_d3_recruitment")

    assert event.route_id == "floor_two"
    assert event.route_node_id == "floor_two_midway_rest"
    assert event.candidate_drifter_ids == (
        "branoc",
        "azhvielle",
        "zhaivra",
        "joruun",
    )
    assert event.cost == 65


def test_unrelated_route_node_does_not_resolve_recruited_roster():
    class GameState:
        party_state = SimpleNamespace()
        story_state = SimpleNamespace(completed_events=())
        overworld_state = SimpleNamespace(
            active_route_id="surface",
            current_route_node_id="not_a_recruitment_node",
        )

        @property
        def recruited_members(self):
            raise AssertionError("unrelated node must not resolve the recruited roster")

    assert available_recruitment_event(GameState()) is None


def test_completed_tutorial_at_d1_node_does_not_resolve_recruited_roster():
    class GameState:
        party_state = SimpleNamespace(
            phase=DungeonPhase.HUB,
            tutorial_complete=True,
            companions=(),
        )
        story_state = SimpleNamespace(completed_events=())
        overworld_state = SimpleNamespace(
            active_route_id="surface",
            current_route_node_id="surface_dungeon_entrance",
        )

        @property
        def recruited_members(self):
            raise AssertionError("ineligible D1 event must not resolve the recruited roster")

    assert available_recruitment_event(GameState()) is None


@pytest.mark.parametrize(
    ("kwargs", "error_type"),
    (
        ({"candidate_drifter_ids": ()}, ValueError),
        ({"candidate_drifter_ids": ("branoc", "branoc")}, ValueError),
        ({"candidate_drifter_ids": ["branoc"]}, TypeError),
        ({"candidate_drifter_ids": ("not_authored",)}, None),
        ({"cost": -1}, ValueError),
        ({"cost": True}, TypeError),
    ),
)
def test_recruitment_event_rejects_malformed_candidates_and_cost(kwargs, error_type):
    values = {
        "event_id": "test_recruitment",
        "route_id": "surface",
        "route_node_id": "surface_dungeon_entrance",
        "candidate_drifter_ids": ("branoc",),
        "cost": 65,
    }
    values.update(kwargs)
    if error_type is None:
        event = RecruitmentEventSpec(**values)
        with pytest.raises(ValueError, match="unknown Drifter"):
            catalog._build_recruitment_event_catalog(
                ((event.event_id, event),)
            )
    else:
        with pytest.raises(error_type):
            RecruitmentEventSpec(**values)

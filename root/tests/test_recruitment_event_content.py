from dataclasses import FrozenInstanceError

import pytest

from app.content import catalog
from app.content.recruitment_event_spec import RecruitmentEventSpec


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

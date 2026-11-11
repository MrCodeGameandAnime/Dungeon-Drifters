"""Authored Floor II third-Drifter recruitment event."""

from app.content.recruitment_event_spec import RecruitmentEventSpec


RECRUITMENT_EVENT = RecruitmentEventSpec(
    event_id="floor_two_d3_recruitment",
    route_id="floor_two",
    route_node_id="floor_two_midway_rest",
    candidate_drifter_ids=("branoc", "azhvielle", "zhaivra", "joruun"),
    cost=65,
)


__all__ = ["RECRUITMENT_EVENT"]

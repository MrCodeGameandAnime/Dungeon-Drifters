"""Authored Floor I second-Drifter recruitment event."""

from app.content.recruitment_event_spec import RecruitmentEventSpec


RECRUITMENT_EVENT = RecruitmentEventSpec(
    event_id="floor_one_d2_recruitment",
    route_id="surface",
    route_node_id="surface_dungeon_entrance",
    candidate_drifter_ids=("branoc", "azhvielle", "zhaivra", "joruun"),
    cost=65,
)


__all__ = ["RECRUITMENT_EVENT"]

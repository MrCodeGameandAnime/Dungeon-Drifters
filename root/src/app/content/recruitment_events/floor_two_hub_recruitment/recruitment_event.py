"""Authored post-Floor-II Hub recruitment offer for the remaining Drifters."""

from app.content.recruitment_event_spec import RecruitmentEventSpec


RECRUITMENT_EVENT = RecruitmentEventSpec(
    event_id="floor_two_hub_recruitment",
    route_id="surface",
    route_node_id="surface_dungeon_entrance",
    candidate_drifter_ids=("branoc", "azhvielle", "zhaivra", "joruun"),
    cost=65,
)


__all__ = ["RECRUITMENT_EVENT"]

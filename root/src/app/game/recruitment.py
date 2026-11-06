"""Runtime eligibility for authored Drifter recruitment events."""

from app.content.catalog import RECRUITMENT_EVENT_SPECS
from app.game.party_state import DungeonPhase


def available_recruitment_event(game_state):
    party = game_state.party_state
    completed_events = set(game_state.story_state.completed_events)
    overworld = game_state.overworld_state
    for event in RECRUITMENT_EVENT_SPECS:
        if event.event_id in completed_events:
            continue
        if (
            event.route_id != overworld.active_route_id
            or event.route_node_id != overworld.current_route_node_id
        ):
            continue
        if event.event_id == "floor_one_d2_recruitment":
            eligible = (
                party.phase is DungeonPhase.HUB
                and not party.tutorial_complete
                and not party.companions
            )
        elif event.event_id == "floor_two_d3_recruitment":
            eligible = (
                party.phase is DungeonPhase.OUTING
                and party.floor_two_run_id is not None
                and party.tutorial_complete
                and overworld.current_route_node_id
                not in overworld.resolved_rest_node_ids
            )
        else:
            continue
        if not eligible:
            continue
        if (
            event.event_id == "floor_two_d3_recruitment"
            and len(game_state.recruited_members) >= 4
        ):
            return None
        return event
    return None


__all__ = ["available_recruitment_event"]

"""Runtime eligibility for authored Drifter recruitment events."""

from app.content.catalog import RECRUITMENT_EVENT_SPECS
from app.game.party_state import DungeonPhase


def available_recruitment_event(game_state):
    party = game_state.party_state
    if (
        party.phase is not DungeonPhase.HUB
        or party.tutorial_complete
        or party.companions
    ):
        return None
    completed_events = set(game_state.story_state.completed_events)
    overworld = game_state.overworld_state
    for event in RECRUITMENT_EVENT_SPECS:
        if (
            event.event_id not in completed_events
            and event.route_id == overworld.active_route_id
            and event.route_node_id == overworld.current_route_node_id
        ):
            return event
    return None


__all__ = ["available_recruitment_event"]

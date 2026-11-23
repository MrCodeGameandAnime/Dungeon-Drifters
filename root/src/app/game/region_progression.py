"""Authoritative eligibility for the finite M8 regional progression portal."""

from dataclasses import dataclass

from app.content.catalog import get_route_spec
from app.content.region_progression_spec import (
    M8_ASHEN_ARENA_REVEALED_EVENT_ID,
    M8_DROWNED_BRIEFING_EVENT_ID,
    destinations_for_region,
    get_destination_spec,
    get_region_spec,
)
from app.game.floor_two_boss_helper import (
    floor_two_replay_requires_available_helper,
)
from app.game.party_state import DungeonPhase
from app.game.story_state import KnowledgeStatus


@dataclass(frozen=True)
class RegionAvailability:
    region_id: str
    display_name: str
    unlocked: bool
    selectable: bool
    message: str | None = None


@dataclass(frozen=True)
class DestinationAvailability:
    destination_id: str
    display_name: str
    route_id: str
    visible: bool
    enabled: bool
    reason: str | None
    knowledge_status: KnowledgeStatus | None


def portal_regions(game_state):
    party = game_state.party_state
    regions = [get_region_spec("region_1")]
    if party.region_two_unlocked:
        regions.append(get_region_spec("region_2"))
    return tuple(
        RegionAvailability(
            region_id=region.region_id,
            display_name=region.display_name,
            unlocked=True,
            selectable=bool(region.destination_ids),
            message=(
                None
                if region.destination_ids
                else "No playable destinations are available yet."
            ),
        )
        for region in regions
    )


def destination_availability(game_state, destination_id):
    spec = get_destination_spec(destination_id)
    knowledge_status = None
    visible = spec.portal_visible
    if spec.knowledge_fact_id is not None:
        knowledge_status = game_state.story_state.knowledge_status(
            spec.knowledge_fact_id
        )
        visible = visible and knowledge_status is not KnowledgeStatus.UNKNOWN

    reason = _destination_block_reason(game_state, spec)
    return DestinationAvailability(
        destination_id=spec.destination_id,
        display_name=spec.display_name,
        route_id=spec.route_id,
        visible=visible,
        enabled=visible and reason is None,
        reason=reason if visible else None,
        knowledge_status=knowledge_status,
    )


def visible_destinations(game_state, region_id):
    region = get_region_spec(region_id)
    if region_id == "region_2" and not game_state.party_state.region_two_unlocked:
        return ()
    visible = []
    for spec in destinations_for_region(region.region_id):
        availability = destination_availability(game_state, spec.destination_id)
        if availability.visible:
            visible.append(availability)
    return tuple(visible)


def is_drowned_reliquary_briefing_available(game_state):
    party = game_state.party_state
    return (
        party.phase is DungeonPhase.HUB
        and party.floor_three_cleared
        and len(game_state.recruited_members) == 4
        and M8_DROWNED_BRIEFING_EVENT_ID
        not in game_state.story_state.completed_events
    )


def is_reunion_boss_eligible(game_state):
    return reunion_boss_unavailable_reason(game_state) is None


def reunion_boss_unavailable_reason(game_state):
    party = game_state.party_state
    if party.phase is not DungeonPhase.HUB:
        return "The reunion can only be started from the Hub."
    if (
        M8_ASHEN_ARENA_REVEALED_EVENT_ID
        not in game_state.story_state.completed_events
    ):
        return "Reveal the Ashen arena first."
    if not party.floor_four_cleared:
        return "Clear Floor IV before entering the reunion arena."
    if len(game_state.recruited_members) != 4:
        return "Recruit all four permanent Drifters first."
    if game_state.expedition_state.active_assignment is not None:
        return "End the current expedition assignment first."
    try:
        get_route_spec("floor_five_reunion")
    except ValueError:
        return "The reunion route is not available yet."
    return None


def confirm_destination_entry(game_state, destination_id):
    availability = destination_availability(game_state, destination_id)
    if not availability.enabled:
        return False
    spec = get_destination_spec(destination_id)
    if spec.knowledge_fact_id is None:
        return False
    return game_state.story_state.reveal_knowledge_fact(
        spec.knowledge_fact_id,
        KnowledgeStatus.CONFIRMED,
    )


def _destination_block_reason(game_state, spec):
    party = game_state.party_state
    if party.phase not in {DungeonPhase.HUB, DungeonPhase.PARTY_READY}:
        return "Destinations can only be entered from the Hub."
    if spec.requires_tutorial and not party.tutorial_complete:
        return "Complete the opening tutorial first."
    if spec.required_floor_clear is not None:
        clear_field = {
            "floor_one": "floor_one_cleared",
            "floor_two": "floor_two_cleared",
            "floor_three": "floor_three_cleared",
            "floor_four": "floor_four_cleared",
        }.get(spec.required_floor_clear)
        if clear_field is None:
            return "This destination is not available yet."
        if not getattr(party, clear_field):
            floor_label = {
                "floor_one": "I",
                "floor_two": "II",
                "floor_three": "III",
                "floor_four": "IV",
            }[spec.required_floor_clear]
            return f"Clear Floor {floor_label} first."
    if spec.requires_full_roster and len(game_state.recruited_members) != 4:
        return "Recruit all four permanent Drifters first."
    if spec.route_id == "floor_two" and party.floor_two_cleared and (
        floor_two_replay_requires_available_helper(party.active_drifter_ids)
    ):
        return "Choose a pair that leaves D3 or D4 available for the Floor II boss."
    if spec.route_id == "floor_three" and (
        game_state.expedition_state.active_assignment is not None
    ):
        return "End the current expedition assignment before starting Floor III."
    try:
        get_route_spec(spec.route_id)
    except ValueError:
        return "This route is not available yet."
    return None


__all__ = [
    "DestinationAvailability",
    "RegionAvailability",
    "confirm_destination_entry",
    "destination_availability",
    "is_drowned_reliquary_briefing_available",
    "is_reunion_boss_eligible",
    "portal_regions",
    "reunion_boss_unavailable_reason",
    "visible_destinations",
]

"""Eligibility rules for the finite M8 optional story scenes."""

from app.content.m8_story_scenes import M8_PAIR_SCENE_BY_PAIR
from app.game.party_state import DungeonPhase
from app.presentation.overworld_models import OverworldScreen


M8_AZH_ARCHIVE_MEMORY_ID = "m8_azh_archive_memory"
M8_RELIQUARY_ECHO_EVENT_ID = "m8_story_reliquary_echo"
M8_RELIQUARY_ECHO_SCENE_ID = "m8_reliquary_echo_scene"


def available_m8_story_scene_ids(game_state, screen):
    screen = OverworldScreen(screen)
    story = game_state.story_state
    completed = set(story.completed_events)
    party = game_state.party_state
    overworld = game_state.overworld_state

    if (
        screen is OverworldScreen.REST
        and party.phase is DungeonPhase.OUTING
        and overworld.active_route_id == "floor_four"
        and overworld.current_route_node_id == "floor_four_rest_midpoint"
        and "floor_four_rest_midpoint" not in overworld.resolved_rest_node_ids
    ):
        scenes = []
        active_pair = tuple(sorted(party.active_drifter_ids))
        pair_scene_id = M8_PAIR_SCENE_BY_PAIR.get(active_pair)
        if pair_scene_id is not None and pair_scene_id not in completed:
            scenes.append(pair_scene_id)
        if (
            "azhvielle" in party.active_drifter_ids
            and M8_AZH_ARCHIVE_MEMORY_ID not in completed
        ):
            scenes.append(M8_AZH_ARCHIVE_MEMORY_ID)
        return tuple(scenes)

    if (
        screen is OverworldScreen.HUB
        and party.phase is DungeonPhase.HUB
        and M8_RELIQUARY_ECHO_EVENT_ID in completed
        and M8_RELIQUARY_ECHO_SCENE_ID not in completed
    ):
        return (M8_RELIQUARY_ECHO_SCENE_ID,)

    return ()


__all__ = (
    "M8_AZH_ARCHIVE_MEMORY_ID",
    "M8_RELIQUARY_ECHO_EVENT_ID",
    "M8_RELIQUARY_ECHO_SCENE_ID",
    "available_m8_story_scene_ids",
)

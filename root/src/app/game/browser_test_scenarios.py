"""Domain-built starting states for the browser's hidden test shortcuts."""

from app.content.catalog import (
    get_drifter_spec,
    get_encounter_item_rewards,
    get_encounter_rewards,
    get_route_spec,
)
from app.game.new_game import create_new_game
from app.game.overworld_state import OverworldState
from app.player.player_state import PlayerState


def build_browser_test_scenario(code):
    if not isinstance(code, str):
        raise ValueError("invalid shortcut code")
    normalized = code.strip().upper()
    if normalized == "H01B":
        return _hub_start_game("branoc"), "branoc", None
    if normalized == "F01BA":
        game = _floor_one_clear_game()
        text = (
            "Floor 1 is cleared. Branoc and Azhvielle return fully restored "
            "to the Hub with all run rewards secured."
        )
        return game, "branoc", text
    raise ValueError("invalid shortcut code")


def _hub_start_game(drifter_id):
    game = create_new_game(drifter_id)
    route = get_route_spec("surface")
    for node in route.nodes:
        if node.encounter_id is not None:
            game.world_state.mark_encounter_defeated(node.encounter_id)
    game.player_state.add_gold(75)
    game._overworld_state = OverworldState.from_snapshot(
        {
            "active_route_id": route.route_id,
            "current_route_node_id": route.nodes[-1].node_id,
            "surface_route_begun": True,
            "dungeon_entrance_reached": True,
            "route_complete": True,
            "resolved_rest_node_ids": [
                node.node_id for node in route.nodes if node.kind.value == "rest"
            ],
            "current_contextual_route_phase": "none",
        }
    )
    if not game.party_state.arrive_at_hub(game.player_state):
        raise RuntimeError("could not construct the Hub shortcut state")
    return game


def _floor_one_clear_game():
    game = _hub_start_game("branoc")
    lead = game.player_state
    companion = PlayerState(get_drifter_spec("azhvielle").create_character())
    party = game.party_state
    members = (lead, companion)
    if not party.recruit_companion(lead, companion):
        raise RuntimeError("could not recruit the Floor 1 shortcut companion")
    if not party.begin_outing() or not party.begin_extraction(
        experience=0,
        gold=0,
    ):
        raise RuntimeError("could not complete the tutorial for the Floor 1 shortcut")
    if not party.complete_extraction(members):
        raise RuntimeError("could not secure the tutorial for the Floor 1 shortcut")
    if party.start_floor_one_run() != 100:
        raise RuntimeError("could not start Floor 1 for the shortcut")

    experience = 0
    gold = 0
    items = {}
    for node in get_route_spec("floor_one").nodes:
        if node.encounter_id is None:
            continue
        encounter_experience, encounter_gold = get_encounter_rewards(
            node.encounter_id
        )
        experience += encounter_experience
        gold += encounter_gold
        for item_id, quantity in get_encounter_item_rewards(node.encounter_id):
            items[item_id] = items.get(item_id, 0) + quantity

    party.add_floor_one_rewards(
        experience=experience,
        gold=gold,
        items=items,
    )
    if not party.complete_floor_one_boss(members):
        raise RuntimeError("could not complete Floor 1 for the shortcut")
    game.overworld_state.return_to_surface_entrance()
    return game

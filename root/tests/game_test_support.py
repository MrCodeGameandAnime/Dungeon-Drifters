"""Valid scenario setup for tests whose subject is not the setup transition."""

from app.content.catalog import get_drifter_spec, get_route_node_spec, get_route_spec
from app.content.route_spec import RouteNodeKind
from app.game.game_state import GameState
from app.game.overworld_state import ContextualRoutePhase
from app.player.player_state import PlayerState


def advance_surface_to(game, node_id):
    """Seed completed earlier nodes without awarding unrelated encounter rewards."""
    route = get_route_spec("surface")
    node_ids = tuple(node.node_id for node in route.nodes)
    target = node_ids.index(node_id)
    game.overworld_state.begin_surface_route()
    current = node_ids.index(game.overworld_state.current_route_node_id)
    if target < current:
        raise ValueError("scenario setup cannot move a route backwards")
    for node in route.nodes[:target]:
        if node.encounter_id is not None:
            game.world_state.mark_encounter_defeated(node.encounter_id)
        elif node.kind is RouteNodeKind.REST:
            game.overworld_state.record_resolved_rest_node(node.node_id)
    for node in route.nodes[current + 1:target + 1]:
        phase = (
            ContextualRoutePhase.ENTER_ENCOUNTER
            if node.encounter_id is not None
            else ContextualRoutePhase.NONE
        )
        game.overworld_state.advance_to(node.node_id, contextual_phase=phase)
    return game


def hub_game(*, lead_id="branoc", gold=75):
    game = GameState(PlayerState(get_drifter_spec(lead_id).create_character(), gold=gold))
    advance_surface_to(game, get_route_spec("surface").nodes[-1].node_id)
    assert game.party_state.arrive_at_hub(game.player_state)
    return game


def recruited_pair_game(*, lead_id="branoc", companion_id="azhvielle", gold=75):
    game = hub_game(lead_id=lead_id, gold=gold)
    companion = PlayerState(get_drifter_spec(companion_id).create_character())
    assert game.party_state.recruit_companion(game.player_state, companion)
    return game


def complete_tutorial(game):
    party = game.party_state
    assert party.begin_outing()
    assert party.begin_extraction(experience=0, gold=0)
    assert party.complete_extraction((game.player_state,) + party.companions)
    return game


def completed_hub_game(*, lead_id="branoc", companion_id="azhvielle", gold=75):
    return complete_tutorial(recruited_pair_game(
        lead_id=lead_id, companion_id=companion_id, gold=gold,
    ))


def three_member_hub_game(
    *, lead_id="branoc", companion_id="azhvielle", third_id="joruun"
):
    game = completed_hub_game(lead_id=lead_id, companion_id=companion_id)
    third = PlayerState(get_drifter_spec(third_id).create_character())
    assert game.party_state.recruit_companion(
        game.player_state,
        third,
        cost=0,
    )
    return game


def enter_floor_one_rest(game, rest_index=0):
    route = get_route_spec("floor_one")
    rest = tuple(node for node in route.nodes if node.kind is RouteNodeKind.REST)[rest_index]
    game.party_state.start_floor_one_run()
    game.overworld_state.begin_route(route.route_id)
    for node in route.nodes[1:]:
        previous = get_route_node_spec(game.overworld_state.current_route_node_id)
        if previous.kind is RouteNodeKind.REST:
            game.overworld_state.record_resolved_rest_node(previous.node_id)
        phase = (
            ContextualRoutePhase.ENTER_ENCOUNTER
            if node.encounter_id is not None
            else ContextualRoutePhase.NONE
        )
        game.overworld_state.advance_to(node.node_id, contextual_phase=phase)
        if node is rest:
            return game
    raise AssertionError("authored Rest was not reached")


def floor_one_rest_game(rest_index=0):
    return enter_floor_one_rest(completed_hub_game(), rest_index)

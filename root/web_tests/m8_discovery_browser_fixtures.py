"""Emit real-runtime browser saves at the authored M8 discovery Rests."""

import json
from pathlib import Path
import sys
from uuid import UUID


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from app.content.catalog import get_drifter_spec, get_route_spec
from app.content.route_spec import RouteNodeKind
from app.game.overworld_state import ContextualRoutePhase
from app.persistence.envelope import build_profile_envelope, serialize_profile_envelope
from app.persistence.save_document import build_save_document
from app.player.player_state import PlayerState
from game_test_support import completed_hub_game


_DISCOVERY_RUN_IDS = {
    "floor_four_rest_midpoint": "m8-discovery-floor-four-midpoint",
    "floor_four_rest_pre_boss": "m8-discovery-floor-four-pre-boss",
}
_PROFILE_ID = UUID("d4d4d4d4-0000-4000-8000-000000000001")
_CLIENT_SAVE_IDS = {
    "floor_four_rest_midpoint": UUID("d4d4d4d4-0000-4000-8000-000000000002"),
    "floor_four_rest_pre_boss": UUID("d4d4d4d4-0000-4000-8000-000000000003"),
}


def _game_at(node_id):
    game = completed_hub_game()
    recruited = {
        member.character.profile.drifter_id for member in game.recruited_members
    }
    for drifter_id in ("azhvielle", "branoc", "joruun", "zhaivra"):
        if drifter_id in recruited:
            continue
        member = PlayerState(get_drifter_spec(drifter_id).create_character())
        if not game.party_state.recruit_companion(
            game.player_state,
            member,
            cost=0,
        ):
            raise AssertionError(f"could not recruit {drifter_id} for M8 fixture")

    party = game.party_state
    party._floor_one_cleared = True
    party._floor_two_cleared = True
    party._floor_three_cleared = True
    party.start_floor_four_run(
        run_id_factory=lambda: _DISCOVERY_RUN_IDS[node_id]
    )
    game.overworld_state.begin_route("floor_four")
    route = get_route_spec("floor_four")
    for node in route.nodes[1:]:
        previous_node = next(
            candidate
            for candidate in route.nodes
            if candidate.node_id == game.overworld_state.current_route_node_id
        )
        if previous_node.kind is RouteNodeKind.REST:
            game.overworld_state.record_resolved_rest_node(previous_node.node_id)
        game.overworld_state.advance_to(
            node.node_id,
            contextual_phase=(
                ContextualRoutePhase.ENTER_ENCOUNTER
                if node.encounter_id is not None
                else ContextualRoutePhase.NONE
            ),
        )
        if node.node_id == node_id:
            break
    else:
        raise AssertionError(f"unknown authored discovery node: {node_id}")
    party._mark_encounter_progress()
    return game


def _profile(node_id):
    game = _game_at(node_id)
    envelope = build_profile_envelope(
        build_save_document(game),
        profile_id=_PROFILE_ID,
        client_save_id=_CLIENT_SAVE_IDS[node_id],
    )
    return {
        "profile_key": f"dungeon-drifters.profile.v1.{_PROFILE_ID}",
        "envelope": serialize_profile_envelope(envelope).decode("utf-8"),
    }


def main():
    print(json.dumps({
        "ancient_well": _profile("floor_four_rest_midpoint"),
        "forgotten_altar": _profile("floor_four_rest_pre_boss"),
    }))


if __name__ == "__main__":
    main()

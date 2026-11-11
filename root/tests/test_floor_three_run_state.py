import pytest

from app.content.catalog import get_drifter_spec, get_route_spec
from app.content.route_spec import RouteNodeKind
from app.game.run_events import RunEventService
from app.game.overworld_state import ContextualRoutePhase
from app.player.player_state import PlayerState
from app.persistence.save_document import build_save_document, reconstruct_game_state
from app.persistence.ports import SaveLoadResult
from app.persistence.save_port_contract import SaveLoadStatus
from tests.game_test_support import completed_hub_game, three_member_hub_game


def floor_two_ready_game(*, recruit_fourth=True):
    game = three_member_hub_game()
    if recruit_fourth:
        zhaivra = PlayerState(get_drifter_spec("zhaivra").create_character())
        assert game.party_state.recruit_companion(
            game.player_state,
            zhaivra,
            cost=0,
        )
    party = game.party_state
    assert party.start_floor_one_run() == 100
    assert party.complete_floor_one_boss(game.active_party_members)
    assert party.start_floor_two_run(run_id_factory=lambda: "floor-two-gate") == 100
    assert party.complete_floor_two_boss(game.active_party_members)
    return game


class MemorySavePort:
    def inspect(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def load(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def save(self, game_state):
        return SaveLoadResult(SaveLoadStatus.SAVED)


class NoDropRng:
    def randint(self, minimum, maximum):
        return minimum


def test_floor_three_requires_floor_two_clear_and_four_permanent_drifters():
    locked = completed_hub_game()
    assert locked.party_state.start_floor_one_run() == 100
    assert locked.party_state.complete_floor_one_boss(locked.active_party_members)
    with pytest.raises(ValueError, match="Floor 2 must be cleared"):
        locked.party_state.start_floor_three_run()

    three_members = floor_two_ready_game(recruit_fourth=False)
    with pytest.raises(ValueError, match="four permanent Drifters"):
        three_members.party_state.start_floor_three_run()


def test_floor_three_run_identity_and_rest_checkpoint_round_trip():
    game = floor_two_ready_game()
    party = game.party_state

    assert party.start_floor_three_run(
        run_id_factory=lambda: "floor-three-checkpoint"
    ) == 100
    game.overworld_state.begin_route("floor_three")
    route = get_route_spec("floor_three")
    midway_rest_index = next(
        index
        for index, node in enumerate(route.nodes)
        if node.kind is RouteNodeKind.REST
    )
    for node in route.nodes[1 : midway_rest_index + 1]:
        game.overworld_state.advance_to(
            node.node_id,
            contextual_phase=(
                ContextualRoutePhase.NONE
                if node.kind is RouteNodeKind.REST
                else ContextualRoutePhase.ENTER_ENCOUNTER
            ),
        )

    restored = reconstruct_game_state(build_save_document(game))

    assert restored.party_state.floor_three_run_id == "floor-three-checkpoint"
    assert restored.overworld_state.active_route_id == "floor_three"
    assert restored.overworld_state.current_route_node_id == "floor_three_midway_rest"
    assert restored.party_state.active_drifter_ids == party.active_drifter_ids
    assert len(restored.recruited_members) == 4


def test_floor_three_clear_splits_pre_boss_xp_to_pair_then_boss_xp_four_ways():
    game = floor_two_ready_game()
    party = game.party_state
    assert party.start_floor_three_run(
        run_id_factory=lambda: "floor-three-xp-split"
    ) == 100
    party.add_floor_three_rewards(experience=100, gold=0)
    reward_result = RunEventService(
        save_port=MemorySavePort(),
        rng=NoDropRng(),
    ).resolve_encounter_rewards(
        game,
        node_id="floor_three_battle_10",
        experience=101,
        gold=0,
        enemy_drop_tables=((),),
    )
    assert reward_result.status.value == "resolved"
    game = reward_result.game_state
    party = game.party_state
    members = game.recruited_members
    active_ids = party.active_drifter_ids
    pre_boss_awards = party.secured_xp_awards(
        game.active_party_members,
        100,
    )
    boss_awards = party.secured_xp_awards(members, 101)
    expected_by_id = dict(zip(active_ids, pre_boss_awards))
    for member, award in zip(members, boss_awards):
        drifter_id = member.character.profile.drifter_id
        expected_by_id[drifter_id] = expected_by_id.get(drifter_id, 0) + award

    assert party.complete_floor_three_boss(
        members,
        boss_experience=101,
    )

    assert {
        member.character.profile.drifter_id: member.exp_state.current
        for member in members
    } == expected_by_id

from app.content.catalog import get_drifter_spec
from app.game.expeditions import ExpeditionService
from app.game.floor_two_boss_helper import (
    available_floor_two_boss_helper_ids,
    create_floor_two_boss_helper,
)
from app.player.player_state import PlayerState
from tests.game_test_support import completed_hub_game


def _level_player(player, target_level):
    while player.level_state.current < target_level:
        player.gain_experience(player.level_state.next_threshold)


def test_temporary_helper_matches_level_and_spreads_growth_points_deterministically():
    spec = get_drifter_spec("zhaivra")
    target = PlayerState(get_drifter_spec("branoc").create_character())
    _level_player(target, 4)

    helper = create_floor_two_boss_helper(spec.drifter_id, target.level_state.current)

    assert helper.drifter_id == "zhaivra"
    assert helper.level_state.current == 4
    assert helper.exp_state.current == 0
    assert helper.growth_points == 0
    assert helper.character.permanent_stats.as_dict() == {
        "constitution": spec.stats.constitution + 2,
        "spirit": spec.stats.spirit + 2,
        "intelligence": spec.stats.intelligence + 2,
        "strength": spec.stats.strength + 1,
        "dexterity": spec.stats.dexterity + 1,
        "intuition": spec.stats.intuition + 1,
    }
    assert helper.signature_weapon_state.weapon_id == spec.starting_weapon_id
    assert all(value == 0 for value in helper.signature_weapon_state.slot_progress.values())


def test_temporary_helper_caps_stats_and_leaves_unallocatable_growth_points():
    spec = get_drifter_spec("joruun")

    helper = create_floor_two_boss_helper(spec.drifter_id, 250)

    stats = helper.character.permanent_stats
    assert max(stats.as_dict().values()) == stats.MAXIMUM
    assert all(stats.get_stat(name) <= stats.MAXIMUM for name in stats.STAT_NAMES)
    assert helper.growth_points > 0


def test_expedition_assigned_drifter_can_be_a_separate_floor_two_helper():
    game = completed_hub_game()
    for drifter_id in ("joruun", "zhaivra"):
        assert game.party_state.recruit_companion(
            game.player_state,
            PlayerState(get_drifter_spec(drifter_id).create_character()),
            cost=0,
        )
    assignment_id = "00000000-0000-4000-8000-000000000778"
    game.expedition_state.install_assignment(
        {
            "assignment_id": assignment_id,
            "outing_floor_id": "floor_two",
            "destination_floor_id": "floor_one",
            "category": "training",
            "expedition_drifter_ids": ["joruun", "zhaivra"],
            "started_at_utc": "2026-11-10T12:00:00Z",
            "last_observed_at_utc": "2026-11-10T12:00:00Z",
            "completed_at_utc": None,
        }
    )
    permanent_joruun = game.member_for_drifter_id("joruun")
    permanent_before = permanent_joruun.snapshot()
    assignment_before = game.expedition_state.active_assignment

    choices = available_floor_two_boss_helper_ids(
        game.party_state.active_drifter_ids
    )
    helper = create_floor_two_boss_helper(
        "joruun",
        game.active_party_members[0].level_state.current,
    )

    assert set(choices) == {"joruun", "zhaivra"}
    assert helper is not permanent_joruun
    assert helper.snapshot() == permanent_before
    assert permanent_joruun.snapshot() == permanent_before
    assert game.expedition_state.active_assignment == assignment_before
    assert ExpeditionService.expedition_pair_for_active_party(game) == (
        "joruun",
        "zhaivra",
    )

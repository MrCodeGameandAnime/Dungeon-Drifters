from app.content.catalog import get_drifter_spec
from app.game.floor_two_boss_helper import create_floor_two_boss_helper
from app.player.player_state import PlayerState


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

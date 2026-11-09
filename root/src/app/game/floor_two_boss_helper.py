"""Deterministic construction of the temporary Floor II boss helper."""

from app.content.catalog import get_drifter_spec
from app.player.player_state import PlayerState


_HELPER_IDS = frozenset({"zhaivra", "joruun"})


def available_floor_two_boss_helper_ids(active_drifter_ids):
    active_ids = set(active_drifter_ids)
    return tuple(
        drifter_id
        for drifter_id in ("zhaivra", "joruun")
        if drifter_id not in active_ids
    )


def create_floor_two_boss_helper(drifter_id, target_level):
    if drifter_id not in _HELPER_IDS:
        raise ValueError("Floor II boss helper must be D3 or D4")
    if isinstance(target_level, bool) or not isinstance(target_level, int):
        raise TypeError("target level must be an integer")
    spec = get_drifter_spec(drifter_id)
    helper = PlayerState(spec.create_character())
    if target_level < helper.level_state.current:
        raise ValueError("target level cannot be below the helper's starting level")

    while helper.level_state.current < target_level:
        helper.gain_experience(helper.level_state.next_threshold)

    stat_names = helper.character.permanent_stats.STAT_NAMES
    while helper.growth_points:
        spent_this_pass = False
        for stat_name in stat_names:
            if helper.growth_points == 0:
                break
            if (
                helper.character.permanent_stats.get_stat(stat_name)
                >= helper.character.permanent_stats.MAXIMUM
            ):
                continue
            helper.increase_permanent_stat(stat_name)
            spent_this_pass = True
        if not spent_this_pass:
            break
    return helper


__all__ = [
    "available_floor_two_boss_helper_ids",
    "create_floor_two_boss_helper",
]

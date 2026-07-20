import pytest

from app.player.character import Brawler, BlackMage
from app.player.player_state import PlayerState


def test_player_growth_starts_at_zero_and_level_gain_grants_points_and_resources():
    player = PlayerState(BlackMage())
    player.health.take_damage(7)
    player.mana_resource.spend(8)

    assert player.gain_experience(100) == 1
    assert player.level_state.current == 2
    assert player.exp_state.current == 0
    assert player.growth_points == 3
    assert player.health.maximum == 95
    assert player.health.current == 88
    assert player.mana_resource.maximum == 57
    assert player.mana_resource.current == 49


def test_multiple_level_gain_grants_three_points_per_level():
    player = PlayerState(Brawler())

    assert player.gain_experience(350) == 3
    assert player.level_state.current == 4
    assert player.exp_state.current == 31
    assert player.growth_points == 9
    assert player.health.maximum == 128
    assert player.mana_resource.maximum == 49


@pytest.mark.parametrize(
    "stat_name",
    ("constitution", "spirit", "intelligence", "strength", "dexterity", "intuition"),
)
def test_one_growth_point_increases_each_permanent_stat(stat_name):
    player = PlayerState(Brawler())
    player.gain_experience(100)
    before = player.character.permanent_stats.get_stat(stat_name)

    assert player.increase_permanent_stat(stat_name) == before + 1
    assert player.character.permanent_stats.get_stat(stat_name) == before + 1
    assert player.growth_points == 2


def test_constitution_and_spirit_growth_updates_resources_without_full_refill():
    player = PlayerState(Brawler())
    player.gain_experience(100)
    player.health.take_damage(10)
    player.mana_resource.spend(5)

    health_before = (player.health.current, player.health.maximum)
    mana_before = (player.mana_resource.current, player.mana_resource.maximum)

    player.increase_permanent_stat("constitution")
    assert player.health.maximum == health_before[1] + 4
    assert player.health.current == health_before[0] + 4

    player.increase_permanent_stat("spirit")
    assert player.mana_resource.maximum == mana_before[1] + 1
    assert player.mana_resource.current == mana_before[0] + 1


def test_non_resource_stat_growth_does_not_change_hp_or_mana():
    player = PlayerState(Brawler())
    player.gain_experience(100)
    before = (
        player.health.current,
        player.health.maximum,
        player.mana_resource.current,
        player.mana_resource.maximum,
    )

    player.increase_permanent_stat("strength")

    assert (
        player.health.current,
        player.health.maximum,
        player.mana_resource.current,
        player.mana_resource.maximum,
    ) == before


def test_growth_uses_permanent_stat_not_equipped_weapon_bonus():
    player = PlayerState(Brawler())
    player.gain_experience(100)

    assert player.effective_stat("strength") == 18
    assert player.increase_permanent_stat("strength") == 16
    assert player.character.permanent_stats.strength == 16
    assert player.effective_stat("strength") == 19


@pytest.mark.parametrize("stat_name", ("invalid", "", None))
def test_invalid_growth_name_changes_nothing(stat_name):
    player = PlayerState(Brawler())
    before = player.snapshot()

    with pytest.raises((TypeError, ValueError)):
        player.increase_permanent_stat(stat_name)

    assert player.snapshot() == before


def test_growth_without_points_and_at_stat_cap_changes_nothing():
    player = PlayerState(Brawler())
    before = player.snapshot()

    with pytest.raises(ValueError, match="no Growth Points"):
        player.increase_permanent_stat("strength")
    assert player.snapshot() == before

    player.gain_experience(100)
    player.character.strength = 100
    before = player.snapshot()
    with pytest.raises(ValueError, match="maximum"):
        player.increase_permanent_stat("strength")
    assert player.snapshot() == before


def test_growth_points_are_present_in_defensive_snapshot():
    player = PlayerState(Brawler())
    player.gain_experience(100)
    player.increase_permanent_stat("constitution")

    snapshot = player.snapshot()
    snapshot["progression"]["growth_points"] = 999

    assert player.growth_points == 2
    assert player.snapshot()["progression"]["growth_points"] == 2

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.player.character import (
    BlackMage,
    Brawler,
    Exp,
    Health,
    Level,
    Mana,
    Monk,
    RogueArcher,
)


PLAYABLE_CLASSES = [
    Brawler,
    BlackMage,
    RogueArcher,
    Monk,
]


def test_health_healing_clamps_to_maximum():
    health = Health(maximum=60, current=40)

    assert health.heal(50) == 60
    assert health.current == 60
    assert health.maximum == 60
    assert health.is_alive()


def test_health_damage_clamps_to_zero_and_defeated():
    health = Health(maximum=60)

    assert health.take_damage(999) == 0
    assert health.current == 0
    assert health.is_defeated()
    assert not health.is_alive()


def test_mana_restore_clamps_to_maximum():
    mana = Mana(maximum=20, current=5)

    assert mana.restore(99) == 20
    assert mana.current == 20
    assert mana.mana_pool() == {"current": 20, "maximum": 20}


def test_mana_spend_checks_affordability_and_never_goes_below_zero():
    mana = Mana(maximum=20, current=5)

    assert mana.can_afford(6) is False
    assert mana.spend(6) is False
    assert mana.current == 5
    assert mana.spend(5) is True
    assert mana.current == 0


def test_exact_exp_threshold_levels_up():
    level = Level()
    exp = Exp(level)

    assert exp.gain(100) == 1
    assert level.current == 2
    assert exp.current == 0
    assert level.next_threshold == 200


def test_excess_exp_carries_over_after_level_up():
    level = Level()
    exp = Exp(level)

    assert exp.gain(125) == 1
    assert level.current == 2
    assert exp.current == 25


def test_one_exp_gain_can_cause_multiple_level_ups():
    level = Level()
    exp = Exp(level)

    assert exp.gain(350) == 2
    assert level.current == 3
    assert exp.current == 50
    assert exp.exp_pool() == {
        "current": 50,
        "level": 3,
        "next_threshold": 300,
    }


def test_derived_stats_return_nonnegative_values():
    for class_type in PLAYABLE_CLASSES:
        player = class_type()

        assert player.stats.attack_power() >= 0
        assert player.stats.defense_rating() >= 0
        assert player.stats.health_bonus() >= 0
        assert player.stats.mana_bonus() >= 0
        assert player.stats.luck_rating() >= 0


def test_legacy_character_attributes_remain_available_and_authoritative():
    player = BlackMage()

    assert player.hp == player.health.current
    assert player.mana == player.mana_resource.current
    assert player.level == player.level_state.current
    assert player.exp == player.exp_state.current

    player.hp = 999
    player.mana = 999
    player.level = 3
    player.exp = 45

    assert player.hp == player.health.maximum
    assert player.mana == player.mana_resource.maximum
    assert player.level_state.current == 3
    assert player.exp_state.current == 45


def test_all_four_playable_classes_initialize_correctly():
    for class_type in PLAYABLE_CLASSES:
        player = class_type()

        assert player.name
        assert player.profile is None
        assert player.archetype_name == player.name
        assert player.display_name == player.name
        assert player.full_display_name == player.name
        assert player.hp == player.health.maximum
        assert player.mana == player.mana_resource.maximum
        assert player.level == 1
        assert player.exp == 0
        assert player.moves
        assert player.combat_moves
        assert player.class_mechanic


if __name__ == "__main__":
    test_health_healing_clamps_to_maximum()
    test_health_damage_clamps_to_zero_and_defeated()
    test_mana_restore_clamps_to_maximum()
    test_mana_spend_checks_affordability_and_never_goes_below_zero()
    test_exact_exp_threshold_levels_up()
    test_excess_exp_carries_over_after_level_up()
    test_one_exp_gain_can_cause_multiple_level_ups()
    test_derived_stats_return_nonnegative_values()
    test_legacy_character_attributes_remain_available_and_authoritative()
    test_all_four_playable_classes_initialize_correctly()
    print("Character state test passed.")

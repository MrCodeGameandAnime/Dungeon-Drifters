import pytest

from app.player.character import (
    BlackMage,
    Brawler,
    Character,
    Monk,
    RogueArcher,
)
from app.player.progression import Exp, Level
from app.player.resources import Health, Mana, Super
from app.player.stats import PermanentStats


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


def test_super_starts_empty_and_banks_until_spent():
    super_resource = Super()

    assert super_resource.current == 0
    assert super_resource.maximum == 100
    assert super_resource.gain(30) == 30
    assert super_resource.gain(80) == 100
    assert super_resource.current == 100
    assert super_resource.can_afford(100)
    assert super_resource.current == 100


def test_super_spend_resets_full_meter_without_refund_behavior():
    super_resource = Super(current=100)

    assert super_resource.spend(100)
    assert super_resource.current == 0
    assert not super_resource.spend(100)
    assert super_resource.current == 0


def test_super_failed_spend_and_reset_behavior():
    super_resource = Super(current=40)

    assert not super_resource.can_afford(100)
    assert not super_resource.spend(100)
    assert super_resource.current == 40
    assert super_resource.reset() == 0
    assert super_resource.current == 0


def test_super_rejects_invalid_current_values_and_amounts():
    for invalid_type in (True, False, 1.5, "1", None):
        with pytest.raises(TypeError):
            Super(current=invalid_type)
        with pytest.raises(TypeError):
            Super().gain(invalid_type)
        with pytest.raises(TypeError):
            Super().can_afford(invalid_type)
        with pytest.raises(TypeError):
            Super().spend(invalid_type)

    for invalid_range in (-1, 101):
        with pytest.raises(ValueError):
            Super(current=invalid_range)

    with pytest.raises(ValueError):
        Super().gain(-1)
    with pytest.raises(ValueError):
        Super().can_afford(-1)
    with pytest.raises(ValueError):
        Super().spend(-1)


def test_health_maximum_changes_validate_and_clamp_current():
    health = Health(maximum=60, current=40)

    assert health.increase_maximum(10) == 70
    assert health.current == 40
    assert health.increase_maximum(5, increase_current=True) == 75
    assert health.current == 45
    assert health.decrease_maximum(20) == 55
    assert health.current == 45
    assert health.set_maximum(30) == 30
    assert health.current == 30
    assert health.set_maximum(0) == 0
    assert health.current == 0


def test_mana_maximum_changes_validate_and_clamp_current():
    mana = Mana(maximum=20, current=12)

    assert mana.increase_maximum(5) == 25
    assert mana.current == 12
    assert mana.increase_maximum(3, increase_current=True) == 28
    assert mana.current == 15
    assert mana.decrease_maximum(8) == 20
    assert mana.current == 15
    assert mana.set_maximum(10) == 10
    assert mana.current == 10
    assert mana.set_maximum(0) == 0
    assert mana.current == 0


def test_resource_maximum_changes_reject_invalid_values():
    for resource in (Health(10), Mana(10)):
        for invalid_type in (True, False, 1.5, "1", None):
            with pytest.raises(TypeError):
                resource.set_maximum(invalid_type)
            with pytest.raises(TypeError):
                resource.increase_maximum(invalid_type)
            with pytest.raises(TypeError):
                resource.decrease_maximum(invalid_type)

        with pytest.raises(ValueError):
            resource.set_maximum(-1)
        with pytest.raises(ValueError):
            resource.increase_maximum(-1)
        with pytest.raises(ValueError):
            resource.decrease_maximum(-1)


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

        assert player.stats.constitution == player.constitution
        assert player.stats.spirit == player.spirit
        assert player.stats.intelligence == player.intelligence
        assert player.stats.strength == player.strength
        assert player.stats.dexterity == player.dexterity
        assert player.stats.intuition == player.intuition
        assert player.stats.attack_power() >= 0
        assert player.stats.defense_rating() >= 0
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


def test_all_four_playable_classes_have_approved_six_stat_totals():
    expected = {
        Brawler: {
            "constitution": 14,
            "spirit": 6,
            "intelligence": 5,
            "strength": 15,
            "dexterity": 10,
            "intuition": 10,
        },
        BlackMage: {
            "constitution": 7,
            "spirit": 13,
            "intelligence": 15,
            "strength": 5,
            "dexterity": 8,
            "intuition": 12,
        },
        RogueArcher: {
            "constitution": 8,
            "spirit": 7,
            "intelligence": 10,
            "strength": 6,
            "dexterity": 15,
            "intuition": 14,
        },
        Monk: {
            "constitution": 10,
            "spirit": 10,
            "intelligence": 13,
            "strength": 7,
            "dexterity": 12,
            "intuition": 8,
        },
    }

    for class_type, stats in expected.items():
        player = class_type()

        assert player.permanent_stats.as_dict() == stats
        assert player.stats.as_dict() == stats
        assert player.permanent_stats.total == 60
        assert not hasattr(player, "charisma")


def test_base_character_accepts_valid_progressed_stat_totals_above_sixty():
    character = Character(
        constitution=20,
        spirit=20,
        intelligence=20,
        strength=20,
        dexterity=20,
        intuition=20,
        hp=100,
        mana=50,
        name="Progressed Test Character",
        moves={1: "test strike"},
    )

    assert character.permanent_stats.total == 120
    assert character.strength == 20
    assert character.spirit == 20
    assert character.intuition == 20


def test_permanent_stats_validation_and_mutation():
    permanent_stats = PermanentStats(
        constitution=10,
        spirit=10,
        intelligence=10,
        strength=10,
        dexterity=10,
        intuition=10,
    )

    assert permanent_stats.set_stat("strength", 11) == 11
    assert permanent_stats.increase_stat("strength", 1) == 12
    assert permanent_stats.decrease_stat("strength", 2) == 10
    assert permanent_stats.increase_stat("strength", 0) == 10
    assert permanent_stats.decrease_stat("strength", 0) == 10
    assert permanent_stats.increase_stat("strength", 1) == 11
    assert permanent_stats.total == 61

    for invalid_type in (True, False, 1.5, "10", None):
        with pytest.raises(TypeError):
            permanent_stats.set_stat("strength", invalid_type)
        with pytest.raises(TypeError):
            permanent_stats.increase_stat("strength", invalid_type)
        with pytest.raises(TypeError):
            permanent_stats.decrease_stat("strength", invalid_type)

    with pytest.raises(ValueError):
        permanent_stats.set_stat("strength", 0)
    with pytest.raises(ValueError):
        permanent_stats.set_stat("strength", 101)
    with pytest.raises(ValueError):
        permanent_stats.increase_stat("strength", -1)
    with pytest.raises(ValueError):
        permanent_stats.decrease_stat("strength", -1)
    with pytest.raises(ValueError):
        permanent_stats.increase_stat("strength", 90)
    with pytest.raises(ValueError):
        permanent_stats.decrease_stat("strength", 11)
    with pytest.raises(ValueError):
        permanent_stats.get_stat("charisma")

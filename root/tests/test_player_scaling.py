import pytest

from app.player import scaling


STAT_SCALING_FUNCTIONS = (
    scaling.maximum_hp_from_constitution,
    scaling.maximum_mana_from_spirit,
    scaling.magical_output_bonus_bps_from_intelligence,
    scaling.physical_output_bonus_bps_from_strength,
    scaling.physical_negation_bps_from_strength,
    scaling.physical_output_bonus_bps_from_dexterity,
    scaling.accuracy_bonus_bps_from_dexterity,
    scaling.dodge_bonus_bps_from_dexterity,
    scaling.special_potency_bps_from_intuition,
    scaling.crit_bonus_bps_from_intuition,
    scaling.super_gain_bonus_bps_from_intuition,
    scaling.discovery_bonus_bps_from_intuition,
    scaling.secured_xp_bonus_bps_from_intuition,
)


def test_stat_scaling_rejects_invalid_stat_types_and_ranges():
    for function in STAT_SCALING_FUNCTIONS:
        for invalid_type in (True, False, 1.5, "10", None):
            with pytest.raises(TypeError):
                function(invalid_type)

        for invalid_range in (0, 101):
            with pytest.raises(ValueError):
                function(invalid_range)


def test_resource_scaling_rejects_invalid_level_types_and_ranges():
    for function in (
            scaling.maximum_hp_from_constitution,
            scaling.maximum_mana_from_spirit,
    ):
        for invalid_type in (True, False, 1.5, "2", None):
            with pytest.raises(TypeError):
                function(10, level=invalid_type)

        with pytest.raises(ValueError):
            function(10, level=0)


def test_constitution_maximum_hp_scaling_milestones():
    expected = {
        7: 91,
        8: 94,
        10: 100,
        20: 140,
        40: 280,
        60: 380,
        80: 440,
        100: 480,
    }

    for constitution, maximum_hp in expected.items():
        assert scaling.maximum_hp_from_constitution(constitution) == maximum_hp


def test_constitution_maximum_hp_level_growth():
    assert scaling.maximum_hp_from_constitution(10, level=1) == 100
    assert scaling.maximum_hp_from_constitution(10, level=2) == 104
    assert scaling.maximum_hp_from_constitution(10, level=5) == 116


def test_spirit_maximum_mana_scaling_milestones():
    expected = {
        6: 46,
        7: 47,
        10: 50,
        20: 70,
        40: 150,
        60: 210,
        80: 250,
        100: 270,
    }

    for spirit, maximum_mana in expected.items():
        assert scaling.maximum_mana_from_spirit(spirit) == maximum_mana


def test_spirit_maximum_mana_level_growth():
    assert scaling.maximum_mana_from_spirit(10, level=1) == 50
    assert scaling.maximum_mana_from_spirit(10, level=2) == 51
    assert scaling.maximum_mana_from_spirit(10, level=5) == 54


@pytest.mark.parametrize(
    ("function", "expected"),
    (
        (
            scaling.magical_output_bonus_bps_from_intelligence,
            {10: 0, 20: 2500, 40: 6500, 60: 9500, 80: 11000, 100: 12000},
        ),
        (
            scaling.physical_output_bonus_bps_from_strength,
            {10: 0, 20: 2500, 40: 6500, 60: 9500, 80: 11000, 100: 12000},
        ),
        (
            scaling.physical_negation_bps_from_strength,
            {10: 0, 20: 500, 40: 1500, 60: 2400, 80: 3000, 100: 3400},
        ),
        (
            scaling.physical_output_bonus_bps_from_dexterity,
            {10: 0, 20: 2500, 40: 6500, 60: 9500, 80: 11000, 100: 12000},
        ),
        (
            scaling.accuracy_bonus_bps_from_dexterity,
            {10: 0, 20: 400, 40: 1000, 60: 1500, 80: 1800, 100: 2000},
        ),
        (
            scaling.dodge_bonus_bps_from_dexterity,
            {10: 0, 20: 200, 40: 600, 60: 1000, 80: 1300, 100: 1500},
        ),
        (
            scaling.special_potency_bps_from_intuition,
            {10: 0, 20: 1000, 40: 2500, 60: 3500, 80: 4200, 100: 5000},
        ),
        (
            scaling.crit_bonus_bps_from_intuition,
            {10: 0, 20: 200, 40: 600, 60: 1000, 80: 1300, 100: 1500},
        ),
        (
            scaling.super_gain_bonus_bps_from_intuition,
            {10: 0, 20: 1000, 40: 2500, 60: 4000, 80: 5000, 100: 6000},
        ),
        (
            scaling.discovery_bonus_bps_from_intuition,
            {10: 0, 20: 1000, 40: 2500, 60: 4000, 80: 5500, 100: 7000},
        ),
        (
            scaling.secured_xp_bonus_bps_from_intuition,
            {10: 0, 20: 100, 40: 400, 60: 700, 80: 1000, 100: 1200},
        ),
    ),
)
def test_basis_point_scaling_functions_return_exact_milestones(function, expected):
    for stat, basis_points in expected.items():
        result = function(stat)

        assert result == basis_points
        assert isinstance(result, int)


def test_basis_point_scaling_interpolates_between_milestones():
    assert scaling.magical_output_bonus_bps_from_intelligence(15) == 1250
    assert scaling.magical_output_bonus_bps_from_intelligence(30) == 4500
    assert scaling.magical_output_bonus_bps_from_intelligence(70) == 10250
    assert scaling.physical_negation_bps_from_strength(30) == 1000
    assert scaling.accuracy_bonus_bps_from_dexterity(50) == 1250
    assert scaling.special_potency_bps_from_intuition(50) == 3000
    assert scaling.secured_xp_bonus_bps_from_intuition(90) == 1100


def test_basis_point_scaling_extrapolates_below_baseline_contract_values():
    assert scaling.magical_output_bonus_bps_from_intelligence(5) == -1250
    assert scaling.physical_negation_bps_from_strength(5) == -250
    assert scaling.accuracy_bonus_bps_from_dexterity(5) == -200
    assert scaling.dodge_bonus_bps_from_dexterity(5) == -100
    assert scaling.special_potency_bps_from_intuition(5) == -500
    assert scaling.crit_bonus_bps_from_intuition(5) == -100
    assert scaling.super_gain_bonus_bps_from_intuition(5) == -500
    assert scaling.discovery_bonus_bps_from_intuition(5) == -500
    assert scaling.secured_xp_bonus_bps_from_intuition(5) == -50

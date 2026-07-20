import pytest

from app.player.progression import (
    GROWTH_POINTS_PER_LEVEL,
    MAXIMUM_LEVEL,
    MINIMUM_LEVEL,
    Exp,
    Level,
    xp_required_for_next_level,
)


def test_progression_constants_and_nonlinear_thresholds_are_locked():
    assert MINIMUM_LEVEL == 1
    assert MAXIMUM_LEVEL == 250
    assert GROWTH_POINTS_PER_LEVEL == 3
    assert {
        level: xp_required_for_next_level(level)
        for level in (1, 10, 25, 50, 249, 250)
    } == {
        1: 100,
        10: 166,
        25: 1259,
        50: 5993,
        249: 395280,
        250: None,
    }


@pytest.mark.parametrize("value", (True, False, 0, -1, 251, 1.0, "1", None))
def test_level_rejects_invalid_values(value):
    with pytest.raises((TypeError, ValueError)):
        Level(value)
    with pytest.raises((TypeError, ValueError)):
        xp_required_for_next_level(value)


def test_level_current_and_increase_are_strict_and_capped():
    level = Level(249)

    with pytest.raises((TypeError, ValueError)):
        level.current = True
    with pytest.raises((TypeError, ValueError)):
        level.increase_level(True)

    assert level.increase_level(10) == MAXIMUM_LEVEL
    assert level.current == MAXIMUM_LEVEL
    assert level.next_threshold is None
    assert level.increase_level(1) == MAXIMUM_LEVEL


def test_exp_gain_rejects_invalid_values_without_mutation():
    level = Level()
    exp = Exp(level)

    for value in (True, False, -1, 1.5, "10", None):
        with pytest.raises((TypeError, ValueError)):
            exp.gain(value)

    assert level.current == 1
    assert exp.current == 0


def test_nonlinear_exp_carries_across_multiple_levels():
    level = Level()
    exp = Exp(level)

    assert exp.gain(350) == 3
    assert level.current == 4
    assert exp.current == 31
    assert exp.exp_pool() == {
        "current": 31,
        "level": 4,
        "next_threshold": 120,
    }


def test_reaching_level_cap_discards_excess_exp_and_future_gains():
    level = Level(249)
    exp = Exp(level)
    amount = xp_required_for_next_level(249) + 12345

    assert exp.gain(amount) == 1
    assert level.current == MAXIMUM_LEVEL
    assert exp.current == 0
    assert exp.exp_pool()["next_threshold"] is None

    assert exp.gain(999999999) == 0
    assert exp.current == 0

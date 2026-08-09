STAT_MINIMUM = 1
STAT_MAXIMUM = 100


_PRIMARY_OUTPUT_BPS_MILESTONES = {
    10: 0,
    20: 2500,
    40: 6500,
    60: 9500,
    80: 11000,
    100: 12000,
}

_STRENGTH_PHYSICAL_NEGATION_BPS_MILESTONES = {
    10: 0,
    20: 500,
    40: 1500,
    60: 2400,
    80: 3000,
    100: 3400,
}

_DEXTERITY_ACCURACY_BPS_MILESTONES = {
    10: 0,
    20: 400,
    40: 1000,
    60: 1500,
    80: 1800,
    100: 2000,
}

_DEXTERITY_DODGE_BPS_MILESTONES = {
    10: 0,
    20: 200,
    40: 600,
    60: 1000,
    80: 1300,
    100: 1500,
}

_INTUITION_SPECIAL_POTENCY_BPS_MILESTONES = {
    10: 0,
    20: 1000,
    40: 2500,
    60: 3500,
    80: 4200,
    100: 5000,
}

_INTUITION_CRIT_BPS_MILESTONES = {
    10: 0,
    20: 200,
    40: 600,
    60: 1000,
    80: 1300,
    100: 1500,
}

_INTUITION_SUPER_GAIN_BPS_MILESTONES = {
    10: 0,
    20: 1000,
    40: 2500,
    60: 4000,
    80: 5000,
    100: 6000,
}

_INTUITION_DISCOVERY_BPS_MILESTONES = {
    10: 0,
    20: 1000,
    40: 2500,
    60: 4000,
    80: 5500,
    100: 7000,
}

_INTUITION_SECURED_XP_BPS_MILESTONES = {
    10: 0,
    20: 100,
    40: 400,
    60: 700,
    80: 1000,
    100: 1200,
}


def maximum_hp_from_constitution(constitution: int, level: int = 1) -> int:
    constitution = _validate_stat(constitution, name="constitution")
    level = _validate_level(level)

    hp = 100
    if constitution < 10:
        hp -= (10 - constitution) * 3
    else:
        hp += _points_above_baseline(
            constitution,
            (
                (20, 4),
                (40, 7),
                (60, 5),
                (80, 3),
                (100, 2),
            ),
        )

    return hp + (level - 1) * 4


def maximum_mana_from_spirit(spirit: int, level: int = 1) -> int:
    spirit = _validate_stat(spirit, name="spirit")
    level = _validate_level(level)

    mana = 50
    if spirit < 10:
        mana -= 10 - spirit
    else:
        mana += _points_above_baseline(
            spirit,
            (
                (20, 2),
                (40, 4),
                (60, 3),
                (80, 2),
                (100, 1),
            ),
        )

    return mana + (level - 1)


def magical_output_bonus_bps_from_intelligence(intelligence: int) -> int:
    intelligence = _validate_stat(intelligence, name="intelligence")
    return _interpolated_bps(intelligence, _PRIMARY_OUTPUT_BPS_MILESTONES)


def physical_output_bonus_bps_from_strength(strength: int) -> int:
    strength = _validate_stat(strength, name="strength")
    return _interpolated_bps(strength, _PRIMARY_OUTPUT_BPS_MILESTONES)


def physical_negation_bps_from_strength(strength: int) -> int:
    strength = _validate_stat(strength, name="strength")
    return _interpolated_bps(strength, _STRENGTH_PHYSICAL_NEGATION_BPS_MILESTONES)


def physical_output_bonus_bps_from_dexterity(dexterity: int) -> int:
    dexterity = _validate_stat(dexterity, name="dexterity")
    return _interpolated_bps(dexterity, _PRIMARY_OUTPUT_BPS_MILESTONES)


def accuracy_bonus_bps_from_dexterity(dexterity: int) -> int:
    dexterity = _validate_stat(dexterity, name="dexterity")
    return _interpolated_bps(dexterity, _DEXTERITY_ACCURACY_BPS_MILESTONES)


def dodge_bonus_bps_from_dexterity(dexterity: int) -> int:
    dexterity = _validate_stat(dexterity, name="dexterity")
    return _interpolated_bps(dexterity, _DEXTERITY_DODGE_BPS_MILESTONES)


def special_potency_bps_from_intuition(intuition: int) -> int:
    intuition = _validate_stat(intuition, name="intuition")
    return _interpolated_bps(intuition, _INTUITION_SPECIAL_POTENCY_BPS_MILESTONES)


def crit_bonus_bps_from_intuition(intuition: int) -> int:
    intuition = _validate_stat(intuition, name="intuition")
    return _interpolated_bps(intuition, _INTUITION_CRIT_BPS_MILESTONES)


def super_gain_bonus_bps_from_intuition(intuition: int) -> int:
    intuition = _validate_stat(intuition, name="intuition")
    return _interpolated_bps(intuition, _INTUITION_SUPER_GAIN_BPS_MILESTONES)


def discovery_bonus_bps_from_intuition(intuition: int) -> int:
    intuition = _validate_stat(intuition, name="intuition")
    return _interpolated_bps(intuition, _INTUITION_DISCOVERY_BPS_MILESTONES)


def secured_xp_bonus_bps_from_intuition(intuition: int) -> int:
    intuition = _validate_stat(intuition, name="intuition")
    return _interpolated_bps(intuition, _INTUITION_SECURED_XP_BPS_MILESTONES)


def _validate_stat(value: int, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < STAT_MINIMUM or value > STAT_MAXIMUM:
        raise ValueError(
            f"{name} must be between {STAT_MINIMUM} and {STAT_MAXIMUM}"
        )

    return value


def _validate_level(level: int) -> int:
    if isinstance(level, bool) or not isinstance(level, int):
        raise TypeError("level must be an integer")
    if level < 1:
        raise ValueError("level must be at least 1")

    return level


def _points_above_baseline(stat: int, brackets: tuple[tuple[int, int], ...]) -> int:
    total = 0
    previous_limit = 10
    for limit, points_per_stat in brackets:
        if stat <= previous_limit:
            break

        points_in_bracket = min(stat, limit) - previous_limit
        total += points_in_bracket * points_per_stat
        previous_limit = limit

    return total


def _interpolated_bps(stat: int, milestones: dict[int, int]) -> int:
    ordered_stats = sorted(milestones)

    if stat in milestones:
        return milestones[stat]

    lower_stat = ordered_stats[0]
    upper_stat = ordered_stats[1]

    if stat > lower_stat:
        for candidate in ordered_stats:
            if candidate < stat:
                lower_stat = candidate
                continue

            upper_stat = candidate
            break

    lower_value = milestones[lower_stat]
    upper_value = milestones[upper_stat]
    span = upper_stat - lower_stat
    offset = stat - lower_stat

    return lower_value + (upper_value - lower_value) * offset // span

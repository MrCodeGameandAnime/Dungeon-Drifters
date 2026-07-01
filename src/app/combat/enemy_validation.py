"""Shared validation for enemy model values."""


def validate_enemy_tier(tier):
    if isinstance(tier, bool) or not isinstance(tier, int):
        raise TypeError("enemy tier must be an integer")
    if tier < 0:
        raise ValueError("enemy tier must be zero or greater")

    return tier

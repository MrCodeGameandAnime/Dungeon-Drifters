def apply_scaling(enemy_definition, tier):
    if isinstance(tier, bool) or not isinstance(tier, int):
        raise TypeError("enemy tier must be an integer")
    if tier != 0:
        raise ValueError("Goblin only supports tier 0")

    return enemy_definition


def apply_scaling(enemy_definition, tier):
    if tier != 0:
        raise ValueError(f"goblin does not support tier {tier}")

    return enemy_definition

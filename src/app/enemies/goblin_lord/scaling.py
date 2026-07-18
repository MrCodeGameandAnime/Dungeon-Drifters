def apply_scaling(enemy_definition, tier):
    if tier != 0:
        raise ValueError(f"{enemy_definition.archetype_id} does not support tier {tier}")
    return enemy_definition

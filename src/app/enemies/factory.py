from app.content.catalog import (
    create_enemy_definition as _create_enemy_definition,
    create_enemy_state as _create_enemy_state,
)


def create_enemy_definition(archetype_id, tier=0):
    return _create_enemy_definition(archetype_id, tier=tier)


def create_enemy_state(archetype_id, tier=0):
    return _create_enemy_state(archetype_id, tier=tier)

from app.enemies.registry import get_enemy_registration
from app.enemies.state import EnemyState
from app.enemies.validation import validate_enemy_tier


def create_enemy_definition(archetype_id, tier=0):
    registration = get_enemy_registration(archetype_id)
    tier = validate_enemy_tier(tier)

    definition = registration.definition_factory()
    return registration.scaling_policy(definition, tier)


def create_enemy_state(archetype_id, tier=0):
    tier = validate_enemy_tier(tier)
    definition = create_enemy_definition(archetype_id, tier=tier)
    return EnemyState(definition, tier=tier)

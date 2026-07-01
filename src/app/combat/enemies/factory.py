from dataclasses import dataclass

from app.combat.enemies.goblin.definition import Goblin
from app.combat.enemies.goblin.scaling import apply_scaling
from app.combat.enemy_state import EnemyState
from app.combat.enemy_validation import validate_enemy_tier


@dataclass(frozen=True)
class EnemyArchetypeRegistration:
    definition_factory: object
    scaling_policy: object


ENEMY_ARCHETYPES = {
    "goblin": EnemyArchetypeRegistration(
        definition_factory=Goblin,
        scaling_policy=apply_scaling,
    ),
}


def create_enemy_state(archetype_id, tier=0):
    if archetype_id not in ENEMY_ARCHETYPES:
        raise ValueError(f"unknown enemy archetype: {archetype_id}")

    tier = validate_enemy_tier(tier)
    registration = ENEMY_ARCHETYPES[archetype_id]

    definition = registration.definition_factory()
    scaled_definition = registration.scaling_policy(definition, tier)
    return EnemyState(scaled_definition, tier=tier)

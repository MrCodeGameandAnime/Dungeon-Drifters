from app.combat.enemies.goblin.definition import Goblin
from app.combat.enemies.goblin.scaling import apply_scaling
from app.combat.enemy_state import EnemyState


ENEMY_DEFINITIONS = {
    "goblin": Goblin,
}


def create_enemy_state(enemy_type, tier=0):
    if enemy_type not in ENEMY_DEFINITIONS:
        raise ValueError(f"unknown enemy type: {enemy_type}")

    definition = ENEMY_DEFINITIONS[enemy_type]()
    scaled_definition = apply_scaling(definition, tier)
    return EnemyState(scaled_definition)


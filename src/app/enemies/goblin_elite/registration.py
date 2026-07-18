from app.enemies.goblin_elite.definition import GoblinElite
from app.enemies.goblin_elite.scaling import apply_scaling
from app.enemies.registration import EnemyArchetypeRegistration


GOBLIN_ELITE_REGISTRATION = EnemyArchetypeRegistration(
    archetype_id="goblin_elite",
    definition_factory=GoblinElite,
    scaling_policy=apply_scaling,
)

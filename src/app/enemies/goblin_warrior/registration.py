from app.enemies.goblin_warrior.definition import GoblinWarrior
from app.enemies.goblin_warrior.scaling import apply_scaling
from app.enemies.registration import EnemyArchetypeRegistration


GOBLIN_WARRIOR_REGISTRATION = EnemyArchetypeRegistration(
    archetype_id="goblin_warrior",
    definition_factory=GoblinWarrior,
    scaling_policy=apply_scaling,
)

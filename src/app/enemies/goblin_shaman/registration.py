from app.enemies.goblin_shaman.definition import GoblinShaman
from app.enemies.goblin_shaman.scaling import apply_scaling
from app.enemies.registration import EnemyArchetypeRegistration


GOBLIN_SHAMAN_REGISTRATION = EnemyArchetypeRegistration(
    archetype_id="goblin_shaman",
    definition_factory=GoblinShaman,
    scaling_policy=apply_scaling,
)

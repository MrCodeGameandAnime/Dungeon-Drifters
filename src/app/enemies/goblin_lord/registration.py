from app.enemies.goblin_lord.definition import GoblinLord
from app.enemies.goblin_lord.scaling import apply_scaling
from app.enemies.registration import EnemyArchetypeRegistration


GOBLIN_LORD_REGISTRATION = EnemyArchetypeRegistration(
    archetype_id="goblin_lord",
    definition_factory=GoblinLord,
    scaling_policy=apply_scaling,
)

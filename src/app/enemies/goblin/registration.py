"""Goblin enemy registration."""

from app.enemies.goblin.definition import Goblin
from app.enemies.goblin.scaling import apply_scaling
from app.enemies.registration import EnemyArchetypeRegistration


GOBLIN_REGISTRATION = EnemyArchetypeRegistration(
    archetype_id="goblin",
    definition_factory=Goblin,
    scaling_policy=apply_scaling,
)

"""Built-in enemy archetype registry."""

from types import MappingProxyType

from app.enemies.goblin.registration import GOBLIN_REGISTRATION
from app.enemies.registration import EnemyArchetypeRegistration
from app.enemies.m10 import GoblinElite, GoblinLord, GoblinShaman, GoblinWarrior


def _identity_scaling(enemy_definition, tier):
    if tier != 0:
        raise ValueError(f"{enemy_definition.archetype_id} does not support tier {tier}")
    return enemy_definition


M10_REGISTRATIONS = (
    EnemyArchetypeRegistration("goblin_warrior", GoblinWarrior, _identity_scaling),
    EnemyArchetypeRegistration("goblin_shaman", GoblinShaman, _identity_scaling),
    EnemyArchetypeRegistration("goblin_elite", GoblinElite, _identity_scaling),
    EnemyArchetypeRegistration("goblin_lord", GoblinLord, _identity_scaling),
)


_BUILTIN_REGISTRATIONS = (
    GOBLIN_REGISTRATION,
    *M10_REGISTRATIONS,
)


def build_enemy_registry(registrations):
    seen = set()
    registry = {}
    for registration in registrations:
        if not isinstance(registration, EnemyArchetypeRegistration):
            raise TypeError("enemy registrations must be EnemyArchetypeRegistration values")
        if registration.archetype_id in seen:
            raise ValueError(f"duplicate enemy archetype registration: {registration.archetype_id}")
        seen.add(registration.archetype_id)
        registry[registration.archetype_id] = registration

    return registry


_ENEMY_REGISTRY = MappingProxyType(
    build_enemy_registry(_BUILTIN_REGISTRATIONS)
)


def get_enemy_registration(archetype_id):
    try:
        return _ENEMY_REGISTRY[archetype_id]
    except KeyError as error:
        raise ValueError(f"unknown enemy archetype: {archetype_id}") from error

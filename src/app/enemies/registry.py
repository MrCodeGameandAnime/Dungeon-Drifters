"""Built-in enemy archetype registry."""

from app.enemies.goblin.registration import GOBLIN_REGISTRATION
from app.enemies.registration import EnemyArchetypeRegistration


BUILT_IN_ENEMY_REGISTRATIONS = (
    GOBLIN_REGISTRATION,
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


ENEMY_REGISTRY = build_enemy_registry(BUILT_IN_ENEMY_REGISTRATIONS)


def get_enemy_registration(archetype_id):
    try:
        return ENEMY_REGISTRY[archetype_id]
    except KeyError as error:
        raise ValueError(f"unknown enemy archetype: {archetype_id}") from error

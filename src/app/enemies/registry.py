"""Built-in enemy archetype registry."""

from types import MappingProxyType

from app.enemies.goblin.registration import GOBLIN_REGISTRATION
from app.enemies.registration import EnemyArchetypeRegistration


_BUILTIN_REGISTRATIONS = (
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


_ENEMY_REGISTRY = MappingProxyType(
    build_enemy_registry(_BUILTIN_REGISTRATIONS)
)


def get_enemy_registration(archetype_id):
    try:
        return _ENEMY_REGISTRY[archetype_id]
    except KeyError as error:
        raise ValueError(f"unknown enemy archetype: {archetype_id}") from error

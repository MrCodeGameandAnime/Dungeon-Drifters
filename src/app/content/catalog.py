"""Deterministic runtime access to authored content."""

from types import MappingProxyType

from app.content._generated_catalog import GENERATED_ENEMY_SPECS
from app.content.enemy_spec import EnemySpec
from app.enemies.state import EnemyState
from app.enemies.validation import validate_enemy_tier


def _build_enemy_catalog(records):
    catalog = {}
    ordered_specs = []
    for directory_id, spec in records:
        if not isinstance(directory_id, str):
            raise TypeError("generated enemy directory IDs must be strings")
        if not isinstance(spec, EnemySpec):
            raise TypeError("generated enemy records must contain EnemySpec values")
        if directory_id != spec.archetype_id:
            raise ValueError(
                "enemy directory ID does not match authored archetype ID: "
                f"{directory_id} != {spec.archetype_id}"
            )
        if spec.archetype_id in catalog:
            raise ValueError(f"duplicate enemy archetype: {spec.archetype_id}")
        catalog[spec.archetype_id] = spec
        ordered_specs.append(spec)
    return tuple(ordered_specs), MappingProxyType(catalog)


ENEMY_SPECS, _ENEMY_CATALOG = _build_enemy_catalog(GENERATED_ENEMY_SPECS)


def get_enemy_spec(archetype_id):
    try:
        return _ENEMY_CATALOG[archetype_id]
    except (KeyError, TypeError) as error:
        raise ValueError(f"unknown enemy archetype: {archetype_id}") from error


def create_enemy_definition(archetype_id, tier=0):
    spec = get_enemy_spec(archetype_id)
    return spec.create_definition(tier=tier)


def create_enemy_state(archetype_id, tier=0):
    tier = validate_enemy_tier(tier)
    return EnemyState(create_enemy_definition(archetype_id, tier=tier), tier=tier)


__all__ = [
    "ENEMY_SPECS",
    "create_enemy_definition",
    "create_enemy_state",
    "get_enemy_spec",
]

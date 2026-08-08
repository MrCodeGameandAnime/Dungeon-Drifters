"""Deterministic runtime access to authored content."""

from types import MappingProxyType

from app.content._generated_catalog import (
    GENERATED_DRIFTER_SPECS,
    GENERATED_ENEMY_SPECS,
    GENERATED_WEAPON_SPECS,
)
from app.content.drifter_spec import DrifterSpec
from app.content.enemy_spec import EnemySpec
from app.content.weapon_spec import WeaponSpec
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


def _build_weapon_catalog(records):
    by_item_id = {}
    by_persistence_key = {}
    ordered_specs = []
    for directory_id, spec in records:
        if not isinstance(directory_id, str):
            raise TypeError("generated weapon directory IDs must be strings")
        if not isinstance(spec, WeaponSpec):
            raise TypeError("generated weapon records must contain WeaponSpec values")
        if directory_id != spec.item_id:
            raise ValueError(
                "weapon directory ID does not match authored item ID: "
                f"{directory_id} != {spec.item_id}"
            )
        if spec.item_id in by_item_id:
            raise ValueError(f"duplicate weapon item ID: {spec.item_id}")
        if spec.persistence_key in by_persistence_key:
            raise ValueError(
                f"duplicate weapon persistence key: {spec.persistence_key}"
            )
        by_item_id[spec.item_id] = spec
        by_persistence_key[spec.persistence_key] = spec
        ordered_specs.append(spec)
    return (
        tuple(ordered_specs),
        MappingProxyType(by_item_id),
        MappingProxyType(by_persistence_key),
    )


WEAPON_SPECS, _WEAPON_CATALOG, _WEAPON_PERSISTENCE_CATALOG = (
    _build_weapon_catalog(GENERATED_WEAPON_SPECS)
)


def _build_drifter_catalog(records):
    by_id = {}
    by_choice = {}
    for directory_id, spec in records:
        if not isinstance(directory_id, str):
            raise TypeError("generated Drifter directory IDs must be strings")
        if not isinstance(spec, DrifterSpec):
            raise TypeError("generated Drifter records must contain DrifterSpec values")
        if directory_id != spec.drifter_id:
            raise ValueError(
                "Drifter directory ID does not match authored Drifter ID: "
                f"{directory_id} != {spec.drifter_id}"
            )
        if spec.drifter_id in by_id:
            raise ValueError(f"duplicate Drifter ID: {spec.drifter_id}")
        if spec.choice in by_choice:
            raise ValueError(f"duplicate Drifter choice: {spec.choice}")
        by_id[spec.drifter_id] = spec
        by_choice[spec.choice] = spec
    ordered = tuple(sorted(by_id.values(), key=lambda spec: int(spec.choice)))
    return ordered, MappingProxyType(by_id), MappingProxyType(by_choice)


DRIFTER_SPECS, _DRIFTER_CATALOG, _DRIFTER_CHOICE_CATALOG = (
    _build_drifter_catalog(GENERATED_DRIFTER_SPECS)
)


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


def get_weapon_spec(item_id):
    try:
        return _WEAPON_CATALOG[item_id]
    except (KeyError, TypeError) as error:
        raise ValueError(f"unknown weapon item ID: {item_id}") from error


def get_weapon_spec_by_persistence_key(persistence_key):
    try:
        return _WEAPON_PERSISTENCE_CATALOG[persistence_key]
    except (KeyError, TypeError) as error:
        raise ValueError(
            f"unknown weapon persistence key: {persistence_key}"
        ) from error


def create_weapon(item_id):
    return get_weapon_spec(item_id).create_weapon()


def create_weapon_from_persistence_key(persistence_key):
    return get_weapon_spec_by_persistence_key(persistence_key).create_weapon()


def get_drifter_spec(drifter_id):
    try:
        return _DRIFTER_CATALOG[drifter_id]
    except (KeyError, TypeError) as error:
        raise ValueError(f"unknown Drifter ID: {drifter_id}") from error


def get_drifter_spec_by_choice(choice):
    try:
        return _DRIFTER_CHOICE_CATALOG[choice]
    except (KeyError, TypeError):
        return None


def create_drifter(drifter_id):
    return get_drifter_spec(drifter_id).create_unselected_character()


__all__ = [
    "ENEMY_SPECS",
    "DRIFTER_SPECS",
    "WEAPON_SPECS",
    "create_enemy_definition",
    "create_enemy_state",
    "create_drifter",
    "create_weapon",
    "create_weapon_from_persistence_key",
    "get_enemy_spec",
    "get_drifter_spec",
    "get_drifter_spec_by_choice",
    "get_weapon_spec",
    "get_weapon_spec_by_persistence_key",
]

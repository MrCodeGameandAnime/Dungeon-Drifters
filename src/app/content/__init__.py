"""Public content-authoring facade."""


__all__ = [
    "ENEMY_SPECS",
    "DRIFTER_SPECS",
    "ClassMechanicSpec",
    "DrifterSpec",
    "DrifterStatSpec",
    "EnemySpec",
    "StatBlockSpec",
    "WEAPON_SPECS",
    "WeaponSpec",
    "create_enemy_definition",
    "create_drifter",
    "create_enemy_state",
    "create_weapon",
    "create_weapon_from_persistence_key",
    "get_enemy_spec",
    "get_drifter_spec",
    "get_drifter_spec_by_choice",
    "get_weapon_spec",
    "get_weapon_spec_by_persistence_key",
]


def __getattr__(name):
    if name in {"EnemySpec", "StatBlockSpec"}:
        from app.content.enemy_spec import EnemySpec, StatBlockSpec

        return {"EnemySpec": EnemySpec, "StatBlockSpec": StatBlockSpec}[name]
    if name == "WeaponSpec":
        from app.content.weapon_spec import WeaponSpec

        return WeaponSpec
    if name in {"ClassMechanicSpec", "DrifterSpec", "DrifterStatSpec"}:
        from app.content.drifter_spec import (
            ClassMechanicSpec,
            DrifterSpec,
            DrifterStatSpec,
        )

        return {
            "ClassMechanicSpec": ClassMechanicSpec,
            "DrifterSpec": DrifterSpec,
            "DrifterStatSpec": DrifterStatSpec,
        }[name]
    if name in {
        "ENEMY_SPECS",
        "DRIFTER_SPECS",
        "WEAPON_SPECS",
        "create_enemy_definition",
        "create_drifter",
        "create_enemy_state",
        "create_weapon",
        "create_weapon_from_persistence_key",
        "get_enemy_spec",
        "get_drifter_spec",
        "get_drifter_spec_by_choice",
        "get_weapon_spec",
        "get_weapon_spec_by_persistence_key",
    }:
        from app.content import catalog

        return getattr(catalog, name)
    raise AttributeError(name)

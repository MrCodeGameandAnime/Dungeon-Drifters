"""Public content-authoring facade."""


__all__ = [
    "ENEMY_SPECS",
    "ENCOUNTER_SPECS",
    "DRIFTER_SPECS",
    "RECRUITMENT_EVENT_SPECS",
    "PERMANENT_DISCOVERY_SOURCES",
    "ClassMechanicSpec",
    "DrifterSpec",
    "DrifterStatSpec",
    "EncounterSpec",
    "EnemySpec",
    "EnemyTierSpec",
    "ItemDropSpec",
    "StatBlockSpec",
    "RouteNodeKind",
    "RouteNodeSpec",
    "RouteSpec",
    "ROUTE_SPECS",
    "WEAPON_SPECS",
    "WeaponSpec",
    "create_enemy_definition",
    "create_drifter",
    "create_enemy_state",
    "create_weapon",
    "create_weapon_from_persistence_key",
    "get_enemy_spec",
    "get_encounter_spec",
    "get_encounter_rewards",
    "get_encounter_item_rewards",
    "get_encounter_item_drop_tables",
    "get_inspectable_encounter_spec",
    "get_inspectable_route_node_spec",
    "get_drifter_spec",
    "get_recruitment_event",
    "get_permanent_discovery_source",
    "get_drifter_spec_by_choice",
    "get_route_spec",
    "get_route_node_spec",
    "get_route_successor_id",
    "get_weapon_spec",
    "get_weapon_spec_by_persistence_key",
]


def __getattr__(name):
    if name in {"EnemySpec", "EnemyTierSpec", "ItemDropSpec", "StatBlockSpec"}:
        from app.content.enemy_spec import (
            EnemySpec,
            EnemyTierSpec,
            ItemDropSpec,
            StatBlockSpec,
        )

        return {
            "EnemySpec": EnemySpec,
            "EnemyTierSpec": EnemyTierSpec,
            "ItemDropSpec": ItemDropSpec,
            "StatBlockSpec": StatBlockSpec,
        }[name]
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
    if name == "EncounterSpec":
        from app.content.encounter_spec import EncounterSpec

        return EncounterSpec
    if name in {"RouteNodeKind", "RouteNodeSpec", "RouteSpec"}:
        from app.content.route_spec import RouteNodeKind, RouteNodeSpec, RouteSpec

        return {
            "RouteNodeKind": RouteNodeKind,
            "RouteNodeSpec": RouteNodeSpec,
            "RouteSpec": RouteSpec,
        }[name]
    if name in {
        "ENEMY_SPECS",
        "ENCOUNTER_SPECS",
        "DRIFTER_SPECS",
        "RECRUITMENT_EVENT_SPECS",
        "PERMANENT_DISCOVERY_SOURCES",
        "ROUTE_SPECS",
        "WEAPON_SPECS",
        "create_enemy_definition",
        "create_drifter",
        "create_enemy_state",
        "create_weapon",
        "create_weapon_from_persistence_key",
        "get_enemy_spec",
        "get_encounter_spec",
        "get_encounter_rewards",
        "get_encounter_item_rewards",
        "get_encounter_item_drop_tables",
        "get_inspectable_encounter_spec",
        "get_inspectable_route_node_spec",
        "get_drifter_spec",
        "get_recruitment_event",
        "get_permanent_discovery_source",
        "get_drifter_spec_by_choice",
        "get_route_spec",
        "get_route_node_spec",
        "get_route_successor_id",
        "get_weapon_spec",
        "get_weapon_spec_by_persistence_key",
    }:
        from app.content import catalog

        return getattr(catalog, name)
    raise AttributeError(name)

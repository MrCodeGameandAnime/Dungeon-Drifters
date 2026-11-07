import hashlib
import json

import pytest

from app.content.catalog import get_drifter_spec_by_choice, get_route_spec
from app.game.overworld_state import OverworldState
from app.game.weapon_progression import WeaponProgressionService
from app.game.game_state import GameState
from app.items.equipment import EquipmentInstance
from app.persistence.save_document import (
    DISK_SCHEMA_VERSION,
    SaveStateValidationError,
    build_save_document,
    reconstruct_game_state,
)
from app.player.player_state import PlayerState
from game_test_support import completed_hub_game, hub_game


def test_storage_neutral_codec_preserves_starting_payload_bytes():
    character = get_drifter_spec_by_choice("1").create_character()
    payload = build_save_document(GameState(PlayerState(character)))
    canonical_bytes = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    assert len(canonical_bytes) == 2977
    assert hashlib.sha256(canonical_bytes).hexdigest() == (
        "9fb54dde4ebb9c4db4423a20954c28a068db64661ea56a9db094d86ad62f787a"
    )


def test_shared_route_items_survive_save_round_trip_before_dungeon_entry():
    game_state = GameState(
        PlayerState(get_drifter_spec_by_choice("1").create_character())
    )
    game_state.party_state.add_shared_items({"goblin_scrap": 3})

    restored = reconstruct_game_state(build_save_document(game_state))

    assert restored.party_state.shared_items == {"goblin_scrap": 3}


def test_carried_supplies_survive_current_save_round_trip():
    game_state = hub_game()
    game_state.party_state.add_shared_items({"healing_potion": 2})
    assert game_state.party_state.load_carried_supplies({"healing_potion": 1})

    document = build_save_document(game_state)
    restored = reconstruct_game_state(document)

    assert document["schema_version"] == DISK_SCHEMA_VERSION == 21
    assert restored.party_state.carried_items == {"healing_potion": 1}
    assert restored.party_state.shared_items == {"healing_potion": 1}


def test_save_rejects_noncarryable_or_unknown_pack_items():
    game_state = hub_game()
    game_state.party_state.add_shared_items({"healing_potion": 1})
    assert game_state.party_state.load_carried_supplies({"healing_potion": 1})
    document = build_save_document(game_state)

    for invalid_items in ({"grade_i_metal": 1}, {"unknown_supply": 1}):
        invalid = json.loads(json.dumps(document))
        invalid["party"]["carried_items"] = invalid_items
        with pytest.raises(SaveStateValidationError, match="carried item"):
            reconstruct_game_state(invalid)


def test_schema13_migration_adds_empty_pack_without_mutating_source():
    from copy import deepcopy

    game_state = GameState(
        PlayerState(get_drifter_spec_by_choice("1").create_character())
    )
    schema13 = build_save_document(game_state)
    schema13["schema_version"] = 13
    schema13["player"].pop("equipment_refs")
    schema13["party"].pop("equipment_instances")
    schema13["party"].pop("modifier_instances")
    schema13["party"].pop("carried_items")
    schema13["player"].pop("advancement")
    schema13["player"].pop("permanent_discovery_bonuses")
    schema13["world"].pop("permanent_discovery_claims")
    schema13["world"].pop("discovered_permanent_discovery_sources")
    for field in (
        "floor_two_cleared",
        "floor_two_runs_started_after_clear",
        "floor_two_run_id",
        "floor_two_outing_xp_multiplier_percent",
        "resolved_run_events",
    ):
        schema13["party"].pop(field)
    original = deepcopy(schema13)

    restored = reconstruct_game_state(schema13)

    assert schema13 == original
    assert restored.party_state.carried_items == {}
    assert build_save_document(restored)["schema_version"] == 21


def test_signature_weapon_progress_survives_save_round_trip():
    character = get_drifter_spec_by_choice("1").create_character()
    game_state = GameState(PlayerState(character))
    game_state.player_state.signature_weapon_state.set_slot_progress(
        "blade_guard",
        25,
    )

    document = build_save_document(game_state)
    restored = reconstruct_game_state(document)

    assert document["schema_version"] == DISK_SCHEMA_VERSION
    assert restored.player_state.signature_weapon_state.slot_progress == {
        "blade_guard": 25,
        "grip_binding": 0,
        "hilt_handle": 0,
        "crest_core": 0,
    }


def test_tier_five_success_survives_save_round_trip():
    game_state = GameState(
        PlayerState(get_drifter_spec_by_choice("1").create_character())
    )
    game_state.player_state.signature_weapon_state.mark_tier_v_success()

    restored = reconstruct_game_state(build_save_document(game_state))

    assert restored.player_state.signature_weapon_state.tier_v_success is True


def test_crafted_and_installed_component_survives_save_document_round_trip():
    character = get_drifter_spec_by_choice("1").create_character()
    player = PlayerState(character)
    game_state = GameState(player)
    route = get_route_spec("surface")
    for node in route.nodes[:-1]:
        if node.encounter_id is not None:
            game_state.world_state.mark_encounter_defeated(node.encounter_id)
    game_state._overworld_state = OverworldState.from_snapshot(
        {
            "current_route_node_id": route.nodes[-1].node_id,
            "surface_route_begun": True,
            "dungeon_entrance_reached": True,
            "route_complete": True,
            "resolved_rest_node_ids": [
                node.node_id for node in route.nodes if node.kind.value == "rest"
            ],
            "current_contextual_route_phase": "none",
        }
    )
    assert game_state.party_state.arrive_at_hub(player)
    game_state.party_state.add_shared_items({"grade_i_metal": 1})
    progression = WeaponProgressionService(game_state)
    assert progression.craft_component(
        target_drifter_id="branoc",
        component_id="sunder_spire_blade_reinforced",
    ).success
    assert game_state.player_state.signature_weapon_state.components["blade_guard"] == (
        "sunder_spire_blade_reinforced"
    )
    assert game_state.party_state.shared_items.get(
        "sunder_spire_blade_reinforced", 0
    ) == 0

    restored = reconstruct_game_state(build_save_document(game_state))

    assert restored.player_state.signature_weapon_state.components["blade_guard"] == (
        "sunder_spire_blade_reinforced"
    )
    assert restored.party_state.crafting_experience == 10
    assert restored.party_state.shared_items == {}
    assert restored.player_state.combat_moves[0].power == 11


def test_equipment_instance_and_exact_loadout_survive_save_round_trip():
    game_state = completed_hub_game()
    helm = EquipmentInstance.from_snapshot(
        {
            "instance_id": "00000000-0000-4000-8000-000000000021",
            "definition_id": "field_helm",
            "source_id": "test_reward_01",
            "secured": False,
            "stat_bonuses": {"constitution": 1},
            "rarity": "common",
            "upgrade_rank": 0,
            "modifier_slots": {},
        }
    )
    ring = EquipmentInstance.from_snapshot(
        {
            "instance_id": "00000000-0000-4000-8000-000000000022",
            "definition_id": "iron_ring",
            "source_id": "surface_reward_01",
            "secured": True,
            "stat_bonuses": {"intuition": 1},
            "rarity": None,
            "upgrade_rank": 0,
            "modifier_slots": {},
        }
    )
    game_state.party_state.add_equipment_instance(helm)
    game_state.party_state.add_equipment_instance(ring)
    refs = game_state.player_state.equipped_equipment_ids
    refs["helm"] = helm.instance_id
    game_state.player_state._set_equipped_equipment_ids(refs)
    companion = game_state.member_for_drifter_id("azhvielle")
    companion_refs = companion.equipped_equipment_ids
    companion_refs["ring"] = ring.instance_id
    companion._set_equipped_equipment_ids(companion_refs)
    game_state._bind_equipment_state()

    document = build_save_document(game_state)
    restored = reconstruct_game_state(document)

    assert document["schema_version"] == 21
    assert {
        item.instance_id: item.snapshot()
        for item in restored.party_state.equipment_instances
    } == {
        item.instance_id: item.snapshot() for item in (helm, ring)
    }
    assert restored.player_state.equipped_equipment_ids["helm"] == helm.instance_id
    assert restored.member_for_drifter_id(
        "azhvielle"
    ).equipped_equipment_ids["ring"] == ring.instance_id
    assert restored.player_state.effective_stat("constitution") == 16
    assert restored.member_for_drifter_id("azhvielle").effective_stat("intuition") == (
        companion.effective_stat("intuition")
    )

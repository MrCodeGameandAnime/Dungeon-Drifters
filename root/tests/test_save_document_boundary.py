import hashlib
import json

from app.content.catalog import get_drifter_spec_by_choice, get_route_spec
from app.game.overworld_state import OverworldState
from app.game.weapon_progression import WeaponProgressionService
from app.game.game_state import GameState
from app.persistence.save_document import (
    DISK_SCHEMA_VERSION,
    build_save_document,
    reconstruct_game_state,
)
from app.player.player_state import PlayerState


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

    assert len(canonical_bytes) == 2062
    assert hashlib.sha256(canonical_bytes).hexdigest() == (
        "ed092c344cadfac799e74080073832d515f2c7ded558fddaa2d4024b305bdf2e"
    )


def test_shared_route_items_survive_save_round_trip_before_dungeon_entry():
    game_state = GameState(
        PlayerState(get_drifter_spec_by_choice("1").create_character())
    )
    game_state.party_state.add_shared_items({"goblin_scrap": 3})

    restored = reconstruct_game_state(build_save_document(game_state))

    assert restored.party_state.shared_items == {"goblin_scrap": 3}


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
    assert progression.install_component(
        target_drifter_id="branoc",
        slot_id="blade_guard",
        component_id="sunder_spire_blade_reinforced",
    ).success

    restored = reconstruct_game_state(build_save_document(game_state))

    assert restored.player_state.signature_weapon_state.components["blade_guard"] == (
        "sunder_spire_blade_reinforced"
    )
    assert restored.party_state.crafting_experience == 10
    assert restored.party_state.shared_items == {}
    assert restored.player_state.combat_moves[0].power == 11

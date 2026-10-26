import hashlib
import json

from app.content.catalog import get_drifter_spec_by_choice
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

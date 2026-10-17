import hashlib
import json

from app.content.catalog import get_drifter_spec_by_choice
from app.game.game_state import GameState
from app.persistence.save_document import build_save_document
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

    assert len(canonical_bytes) == 1599
    assert hashlib.sha256(canonical_bytes).hexdigest() == (
        "b00f1da7aae94f885336690c2dc1b415470b4267444e095311a4aa65d3bcb65e"
    )

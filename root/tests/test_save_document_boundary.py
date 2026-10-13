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

    assert len(canonical_bytes) == 1441
    assert hashlib.sha256(canonical_bytes).hexdigest() == (
        "41de49b00b15bc7069588d40b77e3ca66dccd0f0ff4f3be50b2ce4aa3f0bd2c1"
    )

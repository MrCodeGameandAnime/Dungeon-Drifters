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

    assert len(canonical_bytes) == 1728
    assert hashlib.sha256(canonical_bytes).hexdigest() == (
        "6693fafc241aceeffc2c708e9a9fd277464fa9a3e727172c46ce4d97feb1ddbe"
    )

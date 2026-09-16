"""Canonical construction of a fresh Dungeon Drifters session."""

from app.content.catalog import get_drifter_spec
from app.game.game_state import GameState
from app.player.player_state import PlayerState


def create_new_game(drifter_id):
    """Build a fresh GameState for the confirmed authored Drifter ID."""
    profile = get_drifter_spec(drifter_id)
    character = profile.create_character()
    return GameState(PlayerState(character))


__all__ = ["create_new_game"]

import pytest

from app.content.catalog import DRIFTER_SPECS
from app.game.game_state import GameState
from app.game.new_game import create_new_game
from app.player.player_state import PlayerState


@pytest.mark.parametrize("drifter_id", tuple(spec.drifter_id for spec in DRIFTER_SPECS))
def test_create_new_game_uses_the_canonical_drifter_path(drifter_id):
    game = create_new_game(drifter_id)

    assert isinstance(game, GameState)
    assert isinstance(game.player_state, PlayerState)
    assert game.player_state.character.profile.drifter_id == drifter_id
    assert game.player_state.character.profile is not None


def test_create_new_game_rejects_unknown_drifter_ids():
    with pytest.raises(ValueError, match="unknown Drifter ID"):
        create_new_game("missing_drifter")


def test_each_new_game_has_independent_persistent_state():
    first = create_new_game("branoc")
    second = create_new_game("branoc")

    assert first is not second
    assert first.player_state is not second.player_state
    assert first.player_state.character is not second.player_state.character
    assert first.player_state.inventory is not second.player_state.inventory
    assert (
        first.player_state.character_run_state
        is not second.player_state.character_run_state
    )

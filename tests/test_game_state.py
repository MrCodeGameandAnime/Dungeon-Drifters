import pytest

from app.game.game_state import GameState
from app.game.story_state import StoryState
from app.game.world_state import WorldState
from app.player.character import Brawler
from app.player.player_state import PlayerState



def test_valid_player_state_constructs_game_state():
    player_state = PlayerState(Brawler())
    game_state = GameState(player_state)

    assert game_state.player_state is player_state
    assert isinstance(game_state.story_state, StoryState)
    assert isinstance(game_state.world_state, WorldState)
    assert game_state.metadata == {}


def test_invalid_player_state_is_rejected():
    with pytest.raises(TypeError):
        GameState(Brawler())
    with pytest.raises(TypeError):
        GameState(None)


def test_ownership_properties_cannot_be_replaced():
    game_state = GameState(PlayerState(Brawler()))

    with pytest.raises(AttributeError):
        setattr(game_state, "player_state", None)
    with pytest.raises(AttributeError):
        setattr(game_state, "story_state", None)
    with pytest.raises(AttributeError):
        setattr(game_state, "world_state", None)
    with pytest.raises(AttributeError):
        setattr(game_state, "metadata", {})


def test_metadata_snapshot_cannot_mutate_internal_metadata():
    game_state = GameState(PlayerState(Brawler()))
    game_state.set_metadata("run_mode", "test")

    metadata = game_state.metadata
    metadata["run_mode"] = "changed"
    metadata["extra"] = True

    assert game_state.metadata == {"run_mode": "test"}


def test_game_state_instances_do_not_share_state_containers():
    first = GameState(PlayerState(Brawler()))
    second = GameState(PlayerState(Brawler()))

    first.set_metadata("session", "first")
    first.story_state.add_story_flag("met_goblin")
    first.world_state.discover_location("woods")

    assert first.metadata == {"session": "first"}
    assert second.metadata == {}
    assert first.story_state is not second.story_state
    assert first.world_state is not second.world_state
    assert first.story_state.story_flags == ("met_goblin",)
    assert second.story_state.story_flags == ()
    assert first.world_state.discovered_locations == ("woods",)
    assert second.world_state.discovered_locations == ()

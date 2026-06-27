"""Persistent root state for one active game session."""

from app.game.story_state import StoryState
from app.game.world_state import WorldState
from app.player.player_state import PlayerState


class GameState:
    def __init__(self, player_state: PlayerState):
        if not isinstance(player_state, PlayerState):
            raise TypeError("player_state must be a PlayerState instance")

        self._player_state = player_state
        self._story_state = StoryState()
        self._world_state = WorldState()
        self._metadata = {}

    @property
    def player_state(self):
        return self._player_state

    @property
    def story_state(self):
        return self._story_state

    @property
    def world_state(self):
        return self._world_state

    @property
    def metadata(self):
        return dict(self._metadata)

    def set_metadata(self, key, value):
        self._metadata[key] = value

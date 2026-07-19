"""Persistent root state for one active game session."""

from app.game.story_state import StoryState
from app.game.overworld_state import OverworldState
from app.game.world_state import WorldState
from app.player.player_state import PlayerState
from app.snapshot import STATE_SCHEMA_VERSION, to_plain_value


class GameState:
    def __init__(self, player_state: PlayerState):
        if not isinstance(player_state, PlayerState):
            raise TypeError("player_state must be a PlayerState instance")

        self._player_state = player_state
        self._story_state = StoryState()
        self._world_state = WorldState()
        self._overworld_state = OverworldState()
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
    def overworld_state(self):
        return self._overworld_state

    @property
    def metadata(self):
        return dict(self._metadata)

    def set_metadata(self, key, value):
        self._metadata[key] = value

    def snapshot(self):
        return to_plain_value(
            {
                "schema_version": STATE_SCHEMA_VERSION,
                "player": self.player_state.snapshot(),
                "story": self.story_state.snapshot(),
                "world": self.world_state.snapshot(),
                "overworld": self.overworld_state.snapshot(),
                "metadata": self.metadata,
            },
            "game",
        )

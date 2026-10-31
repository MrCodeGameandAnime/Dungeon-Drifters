"""Persistent root state for one active game session."""

from app.game.story_state import StoryState
from app.game.overworld_state import OverworldState
from app.game.party_state import PartyState
from app.game.party_state import DungeonPhase
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
        self._party_state = PartyState()
        drifter_id = _canonical_drifter_id(player_state)
        if drifter_id is not None:
            self._party_state._set_active_drifter_ids((drifter_id,))
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
    def party_state(self):
        return self._party_state

    @property
    def recruited_members(self):
        members = (self.player_state,) + self.party_state.companions
        drifter_ids = tuple(
            _canonical_drifter_id(member)
            for member in members
        )
        if any(drifter_id is None for drifter_id in drifter_ids):
            raise ValueError("recruited members must have canonical Drifter profiles")
        if len(drifter_ids) != len(set(drifter_ids)):
            raise ValueError("recruited Drifter IDs must be unique")
        return members

    def member_for_drifter_id(self, drifter_id):
        if not isinstance(drifter_id, str) or not drifter_id:
            raise ValueError("drifter_id must be a canonical Drifter ID")
        for member in self.recruited_members:
            if _canonical_drifter_id(member) == drifter_id:
                return member
        raise ValueError(f"Drifter is not recruited: {drifter_id}")

    @property
    def active_party_members(self):
        return tuple(
            self.member_for_drifter_id(drifter_id)
            for drifter_id in self.party_state.active_drifter_ids
        )

    @property
    def members_available_to_party(self):
        if self.party_state.phase in {DungeonPhase.HUB, DungeonPhase.PARTY_READY}:
            return self.recruited_members
        if self.party_state.phase in {DungeonPhase.OUTING, DungeonPhase.EXTRACTION}:
            return self.active_party_members
        return (self.player_state,)

    @property
    def metadata(self):
        return dict(self._metadata)

    def set_metadata(self, key, value):
        self._metadata[key] = value

    def clone(self):
        player = self.player_state.clone()
        companions = tuple(
            companion.clone() for companion in self.party_state.companions
        )
        party = PartyState.from_snapshot(
            self.party_state.snapshot(),
            companions=companions,
            active_drifter_ids=self.party_state.active_drifter_ids,
        )
        return self.from_persistent_parts(
            player,
            StoryState.from_snapshot(self.story_state.snapshot()),
            WorldState.from_snapshot(self.world_state.snapshot()),
            OverworldState.from_snapshot(self.overworld_state.snapshot()),
            to_plain_value(self.metadata, "game.metadata"),
            party,
        )

    @classmethod
    def from_persistent_parts(
        cls,
        player_state,
        story_state,
        world_state,
        overworld_state,
        metadata,
        party_state=None,
    ):
        game_state = cls(player_state)
        game_state._story_state = story_state
        game_state._world_state = world_state
        game_state._overworld_state = overworld_state
        if party_state is not None:
            game_state._party_state = party_state
            if not party_state.active_drifter_ids:
                default_active_ids = [_canonical_drifter_id(player_state)]
                if party_state.companions:
                    default_active_ids.append(
                        _canonical_drifter_id(party_state.companions[0])
                    )
                default_active_ids = tuple(
                    drifter_id
                    for drifter_id in default_active_ids
                    if drifter_id is not None
                )
                if default_active_ids:
                    party_state._set_active_drifter_ids(default_active_ids)
            game_state._validate_active_membership()
        game_state._metadata = dict(metadata)
        return game_state

    def _validate_active_membership(self):
        member_ids = tuple(
            _canonical_drifter_id(member) for member in self.recruited_members
        )
        active_ids = self.party_state.active_drifter_ids
        expected_active_count = 2 if self.party_state.companions else 1
        if len(active_ids) != expected_active_count:
            raise ValueError("active party size disagrees with the recruited roster")
        if any(
            drifter_id not in member_ids for drifter_id in active_ids
        ):
            raise ValueError("active Drifter IDs must refer to recruited members")

    def snapshot(self):
        return to_plain_value(
            {
                "schema_version": STATE_SCHEMA_VERSION,
                "player": self.player_state.snapshot(),
                "story": self.story_state.snapshot(),
                "world": self.world_state.snapshot(),
                "overworld": self.overworld_state.snapshot(),
                "party": self.party_state.snapshot(),
                "metadata": self.metadata,
            },
            "game",
        )


def _canonical_drifter_id(player_state):
    profile = player_state.character.profile
    return getattr(profile, "drifter_id", None)

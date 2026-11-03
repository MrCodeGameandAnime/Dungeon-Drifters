"""Atomic, player-targeted permanent-discovery claims."""

from dataclasses import dataclass
from enum import StrEnum

from app.content.permanent_discovery_spec import (
    PermanentDiscoveryType,
    is_valid_permanent_discovery_source_id,
    validate_permanent_discovery_sources,
)
from app.game.game_state import GameState
from app.persistence.save_port_contract import (
    SaveLoadStatus,
    SavePortError,
    is_save_port,
)


class DiscoveryClaimStatus(StrEnum):
    CANCELLED = "cancelled"
    CLAIMED = "claimed"
    ALREADY_CLAIMED = "already_claimed"
    INVALID_SOURCE = "invalid_source"
    INVALID_TARGET = "invalid_target"
    SAVE_FAILED = "save_failed"


@dataclass(frozen=True)
class DiscoveryClaimResult:
    status: DiscoveryClaimStatus
    game_state: GameState
    reward_applied: bool = False


class PermanentDiscoveryService:
    def __init__(self, sources, *, save_port):
        self._sources = validate_permanent_discovery_sources(sources)
        if not is_save_port(save_port):
            raise TypeError("save_port must satisfy SavePort")
        self._source_by_id = {source.source_id: source for source in self._sources}
        self._save_port = save_port

    def eligible_targets(self, game_state, source_id):
        if not is_valid_permanent_discovery_source_id(source_id):
            raise ValueError("unknown permanent discovery source")
        source = self._source_by_id.get(source_id)
        if source is None:
            raise ValueError("unknown permanent discovery source")
        if source.source_id in game_state.world_state.permanent_discovery_claims:
            return ()
        return game_state.party_state.active_drifter_ids

    def consume(self, game_state, source_id, target_drifter_id, *, confirmed):
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        if not isinstance(confirmed, bool):
            raise TypeError("confirmed must be a boolean")
        if not is_valid_permanent_discovery_source_id(source_id):
            return DiscoveryClaimResult(
                DiscoveryClaimStatus.INVALID_SOURCE,
                game_state,
            )
        source = self._source_by_id.get(source_id)
        if source is None:
            return DiscoveryClaimResult(
                DiscoveryClaimStatus.INVALID_SOURCE,
                game_state,
            )
        if source.source_id in game_state.world_state.permanent_discovery_claims:
            return DiscoveryClaimResult(
                DiscoveryClaimStatus.ALREADY_CLAIMED,
                game_state,
            )
        if target_drifter_id not in game_state.party_state.active_drifter_ids:
            return DiscoveryClaimResult(
                DiscoveryClaimStatus.INVALID_TARGET,
                game_state,
            )
        if not confirmed:
            return DiscoveryClaimResult(DiscoveryClaimStatus.CANCELLED, game_state)

        candidate = game_state.clone()
        target = candidate.member_for_drifter_id(target_drifter_id)
        _apply_reward(target, source)
        candidate.world_state.claim_permanent_discovery(source.source_id)
        try:
            result = self._save_port.save(candidate)
        except (OSError, SavePortError, TypeError, ValueError):
            result = None
        if result is None or result.status is not SaveLoadStatus.SAVED:
            return DiscoveryClaimResult(
                DiscoveryClaimStatus.SAVE_FAILED,
                game_state,
            )
        return DiscoveryClaimResult(
            DiscoveryClaimStatus.CLAIMED,
            candidate,
            reward_applied=True,
        )


def _apply_reward(player, source):
    if source.discovery_type is PermanentDiscoveryType.ANCIENT_WELL:
        player.increase_permanent_max_hp(source.amount)
    elif source.discovery_type is PermanentDiscoveryType.FORGOTTEN_ALTAR:
        player.increase_permanent_max_mana(source.amount)
    else:
        player.gain_permanent_discovery_growth_points(source.amount)


__all__ = [
    "DiscoveryClaimResult",
    "DiscoveryClaimStatus",
    "PermanentDiscoveryService",
]

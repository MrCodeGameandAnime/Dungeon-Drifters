"""Atomic Hub respecs for one recruited Drifter."""

from dataclasses import dataclass
from enum import StrEnum

from app.game.game_state import GameState
from app.game.party_state import DungeonPhase
from app.persistence.save_port_contract import (
    SaveLoadStatus,
    SavePortError,
    is_save_port,
)


REVISION_PARCHMENT_ITEM_ID = "revision_parchment"


class RespecStatus(StrEnum):
    CANCELLED = "cancelled"
    RESPECCED = "respecced"
    NOT_AT_HUB = "not_at_hub"
    INVALID_TARGET = "invalid_target"
    INSUFFICIENT_PARCHMENT = "insufficient_parchment"
    SAVE_FAILED = "save_failed"


@dataclass(frozen=True)
class RespecPreview:
    drifter_id: str
    first_respec: bool
    revision_parchment_cost: int
    growth_points_refunded: int
    current_growth_points: int
    resulting_growth_points: int
    purchased_stat_points: tuple[tuple[str, int], ...]
    purchased_passive_skill_ids: tuple[str, ...]
    purchased_active_skill_ids: tuple[str, ...]
    resulting_stats: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class RespecResult:
    status: RespecStatus
    game_state: GameState
    preview: RespecPreview | None = None


class RespecService:
    def __init__(self, *, save_port):
        if not is_save_port(save_port):
            raise TypeError("save_port must satisfy SavePort")
        self._save_port = save_port

    def preview(self, game_state, drifter_id):
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        if game_state.party_state.phase is not DungeonPhase.HUB:
            raise ValueError("respec is only available at the Hub")
        try:
            player = game_state.member_for_drifter_id(drifter_id)
        except (TypeError, ValueError) as error:
            raise ValueError("respec target is not a recruited Drifter") from error

        advancement = player.advancement_state
        stat_points = advancement.purchased_stat_points
        current_stats = player.stats.as_dict()
        profile = player.character.profile
        if profile is None:
            raise ValueError("respec requires a canonical Drifter profile")
        resulting_stats = {}
        for stat_name, amount in stat_points.items():
            starting = getattr(profile.stats, stat_name)
            if amount > current_stats[stat_name] - starting:
                raise ValueError(
                    f"purchased {stat_name} points exceed the current stat"
                )
            resulting_stats[stat_name] = current_stats[stat_name] - amount
        refund = advancement.purchased_growth_point_cost
        first_respec = advancement.respec_count == 0
        return RespecPreview(
            drifter_id=drifter_id,
            first_respec=first_respec,
            revision_parchment_cost=0 if first_respec else 1,
            growth_points_refunded=refund,
            current_growth_points=player.growth_points,
            resulting_growth_points=player.growth_points + refund,
            purchased_stat_points=tuple(
                (name, amount)
                for name, amount in stat_points.items()
                if amount
            ),
            purchased_passive_skill_ids=advancement.purchased_passive_skill_ids,
            purchased_active_skill_ids=advancement.purchased_active_skill_ids,
            resulting_stats=tuple(resulting_stats.items()),
        )

    def respec(self, game_state, drifter_id, *, confirmed):
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        if not isinstance(confirmed, bool):
            raise TypeError("confirmed must be a boolean")
        if game_state.party_state.phase is not DungeonPhase.HUB:
            return RespecResult(RespecStatus.NOT_AT_HUB, game_state)
        try:
            preview = self.preview(game_state, drifter_id)
        except (TypeError, ValueError):
            return RespecResult(RespecStatus.INVALID_TARGET, game_state)
        if not confirmed:
            return RespecResult(RespecStatus.CANCELLED, game_state, preview)
        if (
            preview.revision_parchment_cost
            and game_state.party_state.shared_items.get(
                REVISION_PARCHMENT_ITEM_ID,
                0,
            )
            < preview.revision_parchment_cost
        ):
            return RespecResult(
                RespecStatus.INSUFFICIENT_PARCHMENT,
                game_state,
                preview,
            )

        candidate = game_state.clone()
        target = candidate.member_for_drifter_id(drifter_id)
        target.respec_advancement()
        if preview.revision_parchment_cost and not candidate.party_state.spend_shared_items(
            {REVISION_PARCHMENT_ITEM_ID: preview.revision_parchment_cost}
        ):
            return RespecResult(
                RespecStatus.INSUFFICIENT_PARCHMENT,
                game_state,
                preview,
            )
        try:
            save_result = self._save_port.save(candidate)
        except (OSError, SavePortError, TypeError, ValueError):
            save_result = None
        if save_result is None or save_result.status is not SaveLoadStatus.SAVED:
            return RespecResult(RespecStatus.SAVE_FAILED, game_state, preview)
        return RespecResult(RespecStatus.RESPECCED, candidate, preview)


__all__ = [
    "REVISION_PARCHMENT_ITEM_ID",
    "RespecPreview",
    "RespecResult",
    "RespecService",
    "RespecStatus",
]

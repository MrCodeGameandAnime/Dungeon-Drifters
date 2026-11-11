"""Persistent state and deterministic timing for passive expeditions."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4

from app.game.expedition_state import (
    ASSIGNMENT_CATEGORIES,
    EXPEDITION_DURATION_SECONDS,
    EXPEDITION_LAUNCH_COST,
    EXPEDITION_REGENERATION_SECONDS,
    FLOOR_IDS,
    MAX_EXPEDITION_ENERGY,
    ExpeditionState,
    _format_utc,
    _nonnegative_int,
    _now_utc,
    _utc_second,
)
from app.persistence.save_port_contract import (
    SaveLoadStatus,
    SavePortError,
    is_save_port,
)
from app.iteration import first_or_none
from app.player.scaling import secured_xp_bonus_bps_from_intuition


class ExpeditionLaunchStatus(StrEnum):
    CANCELLED = "cancelled"
    LAUNCHED = "launched"
    INVALID_STATE = "invalid_state"
    INELIGIBLE_DESTINATION = "ineligible_destination"
    UNAVAILABLE_CATEGORY = "unavailable_category"
    INSUFFICIENT_ENERGY = "insufficient_energy"
    FLOOR_THREE_BLOCKED = "floor_three_blocked"
    INVALID_OUTING = "invalid_outing"
    ALREADY_ACTIVE = "already_active"
    SAVE_FAILED = "save_failed"


class ExpeditionSettlementStatus(StrEnum):
    NO_ASSIGNMENT = "no_assignment"
    INCOMPLETE = "incomplete"
    SETTLED = "settled"
    INVALID_STATE = "invalid_state"
    SAVE_FAILED = "save_failed"


class ExpeditionClaimStatus(StrEnum):
    CANCELLED = "cancelled"
    CLAIMED = "claimed"
    ALREADY_CLAIMED = "already_claimed"
    INVALID_REPORT = "invalid_report"
    INVALID_STATE = "invalid_state"
    SAVE_FAILED = "save_failed"


@dataclass(frozen=True)
class ExpeditionLaunchResult:
    status: ExpeditionLaunchStatus
    game_state: object
    reason: str | None = None


@dataclass(frozen=True)
class ExpeditionSettlementResult:
    status: ExpeditionSettlementStatus
    game_state: object


@dataclass(frozen=True)
class ExpeditionClaimResult:
    status: ExpeditionClaimStatus
    game_state: object


class ExpeditionService:
    def __init__(
        self,
        save_port,
        *,
        now_factory=lambda: _now_utc(),
        assignment_id_factory=None,
        run_id_factory=None,
    ):
        if not is_save_port(save_port):
            raise TypeError("save_port must satisfy SavePort")
        if not callable(now_factory):
            raise TypeError("now_factory must be callable")
        self._save_port = save_port
        self._now_factory = now_factory
        self._assignment_id_factory = assignment_id_factory or uuid4
        self._run_id_factory = run_id_factory or uuid4

    @staticmethod
    def _is_unlocked(game_state):
        return (
            game_state.party_state.tutorial_complete
            and game_state.party_state.floor_three_cleared
            and len(game_state.recruited_members) == 4
        )

    @staticmethod
    def expedition_pair_for_active_party(game_state):
        roster_ids = tuple(
            member.character.profile.drifter_id
            for member in game_state.recruited_members
        )
        active_ids = tuple(game_state.party_state.active_drifter_ids)
        if len(roster_ids) != 4 or len(active_ids) != 2:
            raise ValueError("M6 requires four recruited Drifters and an active pair")
        if len(set(active_ids)) != 2 or any(item not in roster_ids for item in active_ids):
            raise ValueError("active party does not identify two recruited Drifters")
        return tuple(item for item in roster_ids if item not in active_ids)

    def eligible_destinations(self, game_state):
        if not self._is_unlocked(game_state):
            return ()
        party = game_state.party_state
        flags = {
            "floor_one": party.floor_one_cleared,
            "floor_two": party.floor_two_cleared,
            "floor_three": party.floor_three_cleared,
        }
        return tuple(floor_id for floor_id in FLOOR_IDS if flags[floor_id])

    @staticmethod
    def category_unavailable_reason(destination_floor_id, category):
        if destination_floor_id not in FLOOR_IDS:
            return "This destination has no authored M6 reward source."
        if category in ASSIGNMENT_CATEGORIES:
            return None
        if category == "equipment":
            return "No eligible authored equipment reward exists for this floor."
        if category == "recovery":
            return "No eligible authored recovery item exists for this floor."
        return "That expedition category is not available."

    def current_energy(self, game_state, *, now=None):
        return game_state.expedition_state.preview_energy(
            self._now_factory() if now is None else now
        )

    def launch(
        self,
        game_state,
        *,
        outing_floor_id,
        destination_floor_id,
        category,
        confirmed,
    ):
        from app.game.game_state import GameState
        from app.game.party_state import DungeonPhase

        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        if not isinstance(confirmed, bool):
            raise TypeError("confirmed must be a boolean")
        if not confirmed:
            return ExpeditionLaunchResult(ExpeditionLaunchStatus.CANCELLED, game_state)
        if not self._is_unlocked(game_state):
            return ExpeditionLaunchResult(
                ExpeditionLaunchStatus.INVALID_STATE, game_state,
                "Expeditions unlock after the Floor III clear and full roster.",
            )
        if game_state.expedition_state.active_assignment is not None:
            return ExpeditionLaunchResult(ExpeditionLaunchStatus.ALREADY_ACTIVE, game_state)
        if outing_floor_id == "floor_three":
            return ExpeditionLaunchResult(
                ExpeditionLaunchStatus.FLOOR_THREE_BLOCKED, game_state,
                "An expedition cannot accompany a Floor III outing.",
            )
        if outing_floor_id not in {"floor_one", "floor_two"}:
            return ExpeditionLaunchResult(ExpeditionLaunchStatus.INVALID_OUTING, game_state)
        if destination_floor_id not in self.eligible_destinations(game_state):
            return ExpeditionLaunchResult(
                ExpeditionLaunchStatus.INELIGIBLE_DESTINATION, game_state
            )
        unavailable = self.category_unavailable_reason(destination_floor_id, category)
        if unavailable is not None:
            return ExpeditionLaunchResult(
                ExpeditionLaunchStatus.UNAVAILABLE_CATEGORY, game_state, unavailable
            )
        if game_state.party_state.phase is not DungeonPhase.HUB:
            return ExpeditionLaunchResult(ExpeditionLaunchStatus.INVALID_STATE, game_state)
        try:
            expedition_ids = self.expedition_pair_for_active_party(game_state)
            if (
                outing_floor_id == "floor_two"
                and game_state.party_state.floor_two_cleared
            ):
                from app.game.floor_two_boss_helper import (
                    floor_two_replay_requires_available_helper,
                )

                if floor_two_replay_requires_available_helper(
                    game_state.party_state.active_drifter_ids
                ):
                    return ExpeditionLaunchResult(
                        ExpeditionLaunchStatus.INVALID_OUTING,
                        game_state,
                        "Choose an active pair that leaves D3 or D4 available "
                        "for the Floor II boss.",
                    )
            now = _utc_second(self._now_factory())
            candidate = game_state.clone()
            candidate.expedition_state.update_energy(now)
            if candidate.expedition_state.energy < EXPEDITION_LAUNCH_COST:
                return ExpeditionLaunchResult(
                    ExpeditionLaunchStatus.INSUFFICIENT_ENERGY, game_state
                )
            if outing_floor_id == "floor_one":
                candidate.party_state.start_floor_one_run()
            else:
                candidate.party_state.start_floor_two_run(
                    run_id_factory=self._run_id_factory
                )
            candidate.overworld_state.begin_route(outing_floor_id)
            assignment_id = self._assignment_id_factory()
            if isinstance(assignment_id, UUID):
                assignment_id = str(assignment_id)
            stamp = _format_utc(now)
            candidate.expedition_state.install_assignment({
                "assignment_id": assignment_id,
                "outing_floor_id": outing_floor_id,
                "destination_floor_id": destination_floor_id,
                "category": category,
                "expedition_drifter_ids": list(expedition_ids),
                "started_at_utc": stamp,
                "last_observed_at_utc": stamp,
                "completed_at_utc": None,
            })
            if not candidate.expedition_state.spend_energy(
                EXPEDITION_LAUNCH_COST, now=now
            ):
                return ExpeditionLaunchResult(
                    ExpeditionLaunchStatus.INSUFFICIENT_ENERGY, game_state
                )
        except (TypeError, ValueError):
            return ExpeditionLaunchResult(ExpeditionLaunchStatus.INVALID_OUTING, game_state)

        try:
            saved = self._save_port.save(candidate)
        except (OSError, SavePortError, TypeError, ValueError):
            saved = None
        if saved is None or saved.status is not SaveLoadStatus.SAVED:
            return ExpeditionLaunchResult(ExpeditionLaunchStatus.SAVE_FAILED, game_state)
        return ExpeditionLaunchResult(ExpeditionLaunchStatus.LAUNCHED, candidate)

    def settle_outing(self, game_state, *, secured_base_xp, now=None):
        from app.game.game_state import GameState
        from app.game.party_state import DungeonPhase

        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        _nonnegative_int(secured_base_xp, "secured dungeon XP")
        assignment = game_state.expedition_state.active_assignment
        if assignment is None:
            return ExpeditionSettlementResult(
                ExpeditionSettlementStatus.NO_ASSIGNMENT,
                game_state,
            )
        if game_state.party_state.phase is not DungeonPhase.HUB:
            return ExpeditionSettlementResult(
                ExpeditionSettlementStatus.INVALID_STATE,
                game_state,
            )

        candidate = game_state.clone()
        observed_at = self._now_factory() if now is None else now
        candidate.expedition_state.update_energy(observed_at)
        candidate.expedition_state.observe_assignment_time(observed_at)
        completed = candidate.expedition_state.active_assignment
        if completed["completed_at_utc"] is None:
            candidate.expedition_state.settle_assignment()
            status = ExpeditionSettlementStatus.INCOMPLETE
        else:
            report = _build_report(candidate, completed, secured_base_xp)
            candidate.expedition_state.settle_assignment(report)
            status = ExpeditionSettlementStatus.SETTLED

        try:
            saved = self._save_port.save(candidate)
        except (OSError, SavePortError, TypeError, ValueError):
            saved = None
        if saved is None or saved.status is not SaveLoadStatus.SAVED:
            return ExpeditionSettlementResult(
                ExpeditionSettlementStatus.SAVE_FAILED,
                game_state,
            )
        return ExpeditionSettlementResult(status, candidate)

    def claim_report(self, game_state, report_id, *, confirmed):
        from app.game.game_state import GameState
        from app.game.party_state import DungeonPhase

        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        if not isinstance(confirmed, bool):
            raise TypeError("confirmed must be a boolean")
        report = first_or_none(
            item
            for item in game_state.expedition_state.reports
            if item["report_id"] == report_id
        )
        if report is None:
            return ExpeditionClaimResult(
                ExpeditionClaimStatus.INVALID_REPORT,
                game_state,
            )
        if report["claimed"]:
            return ExpeditionClaimResult(
                ExpeditionClaimStatus.ALREADY_CLAIMED,
                game_state,
            )
        if not confirmed:
            return ExpeditionClaimResult(ExpeditionClaimStatus.CANCELLED, game_state)
        if game_state.party_state.phase is not DungeonPhase.HUB:
            return ExpeditionClaimResult(
                ExpeditionClaimStatus.INVALID_STATE,
                game_state,
            )

        candidate = game_state.clone()
        if report["category"] == "training":
            for drifter_id, amount in report["experience_awards"].items():
                try:
                    member = candidate.member_for_drifter_id(drifter_id)
                except ValueError:
                    return ExpeditionClaimResult(
                        ExpeditionClaimStatus.INVALID_REPORT,
                        game_state,
                    )
                member.gain_experience(amount)
        else:
            candidate.party_state.add_shared_items(
                {report["reward_item_id"]: report["reward_quantity"]}
            )
        if not candidate.expedition_state.mark_report_claimed(report_id):
            return ExpeditionClaimResult(
                ExpeditionClaimStatus.ALREADY_CLAIMED,
                game_state,
            )

        try:
            saved = self._save_port.save(candidate)
        except (OSError, SavePortError, TypeError, ValueError):
            saved = None
        if saved is None or saved.status is not SaveLoadStatus.SAVED:
            return ExpeditionClaimResult(
                ExpeditionClaimStatus.SAVE_FAILED,
                game_state,
            )
        return ExpeditionClaimResult(ExpeditionClaimStatus.CLAIMED, candidate)


def _build_report(game_state, assignment, secured_base_xp):
    awards = {}
    reward_item_id = None
    reward_quantity = 0
    if assignment["category"] == "training":
        expedition_pool = secured_base_xp * 20 // 100
        second_share, remainder = divmod(expedition_pool, 2)
        base_shares = (
            second_share + remainder,
            second_share,
        )
        for drifter_id, base_share in zip(
            assignment["expedition_drifter_ids"],
            base_shares,
        ):
            member = game_state.member_for_drifter_id(drifter_id)
            if member is None:
                raise ValueError("expedition member is not in the permanent roster")
            bonus_bps = secured_xp_bonus_bps_from_intuition(
                member.effective_stat("intuition")
            )
            awards[drifter_id] = base_share + base_share * bonus_bps // 10000
    else:
        grade = ("i", "ii", "iii")[FLOOR_IDS.index(
            assignment["destination_floor_id"]
        )]
        reward_item_id = f"grade_{grade}_metal"
        reward_quantity = 1

    return {
        "report_id": assignment["assignment_id"],
        "outing_floor_id": assignment["outing_floor_id"],
        "destination_floor_id": assignment["destination_floor_id"],
        "category": assignment["category"],
        "expedition_drifter_ids": list(assignment["expedition_drifter_ids"]),
        "started_at_utc": assignment["started_at_utc"],
        "completed_at_utc": assignment["completed_at_utc"],
        "secured_base_xp": secured_base_xp,
        "experience_awards": awards,
        "reward_item_id": reward_item_id,
        "reward_quantity": reward_quantity,
        "claimed": False,
    }


__all__ = [
    "ASSIGNMENT_CATEGORIES",
    "EXPEDITION_DURATION_SECONDS",
    "EXPEDITION_LAUNCH_COST",
    "EXPEDITION_REGENERATION_SECONDS",
    "FLOOR_IDS",
    "MAX_EXPEDITION_ENERGY",
    "ExpeditionState",
]

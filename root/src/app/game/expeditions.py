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
    FLOOR_FIVE_APPROACH_OUTING_ID,
    FLOOR_FIVE_REUNION_OUTING_ID,
    MAX_EXPEDITION_ENERGY,
    ExpeditionState,
    category_unavailable_reason as _category_unavailable_reason,
    report_content_id_for,
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
        equipment_instance_id_factory=None,
        armor_rng=None,
    ):
        if not is_save_port(save_port):
            raise TypeError("save_port must satisfy SavePort")
        if not callable(now_factory):
            raise TypeError("now_factory must be callable")
        self._save_port = save_port
        self._now_factory = now_factory
        self._assignment_id_factory = assignment_id_factory or uuid4
        self._run_id_factory = run_id_factory or uuid4
        self._equipment_instance_id_factory = equipment_instance_id_factory or uuid4
        self._armor_rng = armor_rng

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
            "floor_four": party.floor_four_cleared,
            "floor_five": party.floor_five_cleared,
        }
        return tuple(floor_id for floor_id in FLOOR_IDS if flags[floor_id])

    @staticmethod
    def category_unavailable_reason(destination_floor_id, category, *, game_state=None):
        return _category_unavailable_reason(
            destination_floor_id,
            category,
            game_state=game_state,
        )

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
        if outing_floor_id == FLOOR_FIVE_REUNION_OUTING_ID:
            return ExpeditionLaunchResult(ExpeditionLaunchStatus.INVALID_OUTING, game_state)
        if outing_floor_id not in {
            "floor_one",
            "floor_two",
            "floor_four",
            FLOOR_FIVE_APPROACH_OUTING_ID,
        }:
            return ExpeditionLaunchResult(ExpeditionLaunchStatus.INVALID_OUTING, game_state)
        if destination_floor_id not in self.eligible_destinations(game_state):
            return ExpeditionLaunchResult(
                ExpeditionLaunchStatus.INELIGIBLE_DESTINATION, game_state
            )
        unavailable = self.category_unavailable_reason(
            destination_floor_id,
            category,
            game_state=game_state,
        )
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
            if outing_floor_id in {"floor_four", FLOOR_FIVE_APPROACH_OUTING_ID}:
                from app.game.region_progression import (
                    confirm_destination_entry,
                    destination_availability,
                )

                destination_id = (
                    "drowned_reliquary"
                    if outing_floor_id == "floor_four"
                    else "ashen_vault"
                )
                availability = destination_availability(
                    candidate, destination_id
                )
                if not availability.enabled:
                    return ExpeditionLaunchResult(
                        ExpeditionLaunchStatus.INVALID_OUTING,
                        game_state,
                        availability.reason
                        or "The Drowned Reliquary entry is no longer eligible.",
                    )
                confirm_destination_entry(candidate, destination_id)
            candidate.expedition_state.update_energy(now)
            if candidate.expedition_state.energy < EXPEDITION_LAUNCH_COST:
                return ExpeditionLaunchResult(
                    ExpeditionLaunchStatus.INSUFFICIENT_ENERGY, game_state
                )
            if outing_floor_id == "floor_one":
                candidate.party_state.start_floor_one_run()
            elif outing_floor_id == "floor_two":
                candidate.party_state.start_floor_two_run(
                    run_id_factory=self._run_id_factory
                )
            elif outing_floor_id == "floor_four":
                candidate.party_state.start_floor_four_run(
                    run_id_factory=self._run_id_factory
                )
            elif outing_floor_id == FLOOR_FIVE_APPROACH_OUTING_ID:
                candidate.party_state.start_floor_five_approach_run(
                    run_id_factory=self._run_id_factory
                )
            else:
                from app.content.catalog import get_route_spec

                get_route_spec(outing_floor_id)
                start_approach = getattr(
                    candidate.party_state,
                    "start_floor_five_approach_run",
                    None,
                )
                if not callable(start_approach):
                    return ExpeditionLaunchResult(
                        ExpeditionLaunchStatus.INVALID_OUTING,
                        game_state,
                        "The Floor V approach is not available yet.",
                    )
                start_approach(run_id_factory=self._run_id_factory)
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
                "report_content_id": report_content_id_for(
                    destination_floor_id, category
                ),
                "expedition_drifter_ids": list(expedition_ids),
                "started_at_utc": stamp,
                "last_observed_at_utc": stamp,
                "completed_at_utc": None,
                "frozen_outcome": _build_frozen_outcome(
                    candidate,
                    destination_floor_id,
                    category,
                    equipment_instance_id_factory=self._equipment_instance_id_factory,
                    armor_rng=self._armor_rng,
                ),
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
        elif report["reward_item_id"] is not None:
            candidate.party_state.add_shared_items(
                {report["reward_item_id"]: report["reward_quantity"]}
            )
        elif report["category"] == "equipment":
            from app.items.equipment import EquipmentInstance

            outcome = report["frozen_outcome"]
            try:
                candidate.party_state.add_equipment_instance(
                    EquipmentInstance.from_snapshot(outcome["equipment_instance"])
                )
            except (TypeError, ValueError):
                return ExpeditionClaimResult(
                    ExpeditionClaimStatus.INVALID_REPORT,
                    game_state,
                )
            candidate._bind_equipment_state()
        elif report["category"] == "scouting":
            for fact_id in report["frozen_outcome"]["knowledge_fact_ids"]:
                candidate.story_state.reveal_knowledge_fact(fact_id, "confirmed")
        elif report["category"] == "story":
            candidate.story_state.complete_event(
                report["frozen_outcome"]["story_event_id"]
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


def _build_frozen_outcome(
    game_state,
    destination_floor_id,
    category,
    *,
    equipment_instance_id_factory,
    armor_rng,
):
    if category == "training":
        return None
    if category == "material":
        if destination_floor_id in FLOOR_IDS[:3]:
            grade = ("i", "ii", "iii")[FLOOR_IDS.index(destination_floor_id)]
            return {
                "source_id": None,
                "reward_item_id": f"grade_{grade}_metal",
                "reward_quantity": 1,
            }
        if destination_floor_id == "floor_four":
            return {
                "source_id": "m8_floor_four_metal_drop_01",
                "reward_item_id": "grade_iv_metal",
                "reward_quantity": 1,
            }
        from app.game.expedition_state import _floor_five_material_source_ids

        sources = _floor_five_material_source_ids()
        if not sources:
            raise ValueError("Floor V has no eligible authored Material source")
        return {
            "source_id": sources[0],
            "reward_item_id": "grade_iv_cores",
            "reward_quantity": 1,
        }
    if category == "equipment":
        from app.content.catalog import get_armor_reward_source
        from app.game.armor_generation import ArmorGenerationService

        source = get_armor_reward_source("m8_floor_four_armor_source")
        if armor_rng is None:
            from app import randomness

            armor_rng = randomness
        instance_id = equipment_instance_id_factory()
        if isinstance(instance_id, UUID):
            instance_id = str(instance_id)
        existing_instance_ids = {
            instance.instance_id
            for instance in game_state.party_state.equipment_instances
        }
        for report in game_state.expedition_state.reports:
            if report["category"] == "equipment":
                existing_instance_ids.add(
                    report["frozen_outcome"]["equipment_instance"]["instance_id"]
                )
        if instance_id in existing_instance_ids:
            raise ValueError("generated expedition equipment ID is already in use")
        instance = ArmorGenerationService(rng=armor_rng).generate(
            template_id=source.template_id,
            floor=source.floor,
            source_id=source.source_id,
            instance_id=instance_id,
            secured=True,
        )
        return {
            "source_id": source.source_id,
            "equipment_instance": instance.snapshot(),
        }
    if category == "recovery":
        return {
            "source_id": "m8_floor_four_recovery_source",
            "reward_item_id": "healing_potion",
            "reward_quantity": 1,
        }
    if category == "scouting":
        return {
            "knowledge_fact_ids": [
                "m8_fact_reliquary_threats",
                "m8_fact_ashen_vault",
                "m8_fact_ashen_regent",
            ],
        }
    if category == "story":
        return {"story_event_id": "m8_story_reliquary_echo"}
    if category == "elite":
        return {
            "source_id": "m8_floor_four_core_drop_01",
            "reward_item_id": "grade_iv_cores",
            "reward_quantity": 1,
        }
    raise ValueError("expedition category has no authored outcome")


def _build_report(game_state, assignment, secured_base_xp):
    awards = {}
    reward_item_id = None
    reward_quantity = 0
    outcome = assignment["frozen_outcome"]
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
        reward_item_id, reward_quantity = (
            outcome.get("reward_item_id"),
            outcome.get("reward_quantity", 0),
        )

    return {
        "report_id": assignment["assignment_id"],
        "outing_floor_id": assignment["outing_floor_id"],
        "destination_floor_id": assignment["destination_floor_id"],
        "category": assignment["category"],
        "report_content_id": assignment["report_content_id"],
        "expedition_drifter_ids": list(assignment["expedition_drifter_ids"]),
        "started_at_utc": assignment["started_at_utc"],
        "completed_at_utc": assignment["completed_at_utc"],
        "secured_base_xp": secured_base_xp,
        "experience_awards": awards,
        "reward_item_id": reward_item_id,
        "reward_quantity": reward_quantity,
        "frozen_outcome": outcome,
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

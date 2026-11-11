"""Bounded M6 expedition qualification after the cleared Floor III route."""

import gc


_M6_STAGE_NAMES = (
    "M6_ENERGY_CLOCK_AND_OVERFLOW",
    "M6_FLOOR_THREE_LAUNCH_REJECTION",
    "M6_PASSIVE_TRAINING_LIFECYCLE",
    "M6_SNAPSHOT_RECONSTRUCTION",
    "M6_PROBE_TEARDOWN",
)
_STARTED_AT = 1794312000
_ASSIGNMENT_ID = "00000000-0000-4000-8000-000000000706"


def _energy_clock_and_overflow():
    from app.game.expeditions import (
        EXPEDITION_REGENERATION_SECONDS,
        ExpeditionState,
    )

    state = ExpeditionState.from_snapshot({
        "energy": 100,
        "energy_anchor_utc": "2026-11-10T12:00:00Z",
        "active_assignment": None,
        "reports": [],
    })
    full_after_time = _STARTED_AT + 3 * 60 * 60
    state.update_energy(full_after_time)
    if not state.spend_energy(10, now=full_after_time):
        raise AssertionError("M6 could not spend energy at full capacity")
    if state.energy != 90:
        raise AssertionError("M6 launch energy cost changed")
    state.update_energy(
        full_after_time + EXPEDITION_REGENERATION_SECONDS - 1
    )
    if state.energy != 90:
        raise AssertionError("M6 energy regenerated before nine minutes")
    state.update_energy(
        full_after_time + EXPEDITION_REGENERATION_SECONDS
    )
    if state.energy != 91:
        raise AssertionError("M6 discarded overflow was credited after spending")
    accepted_anchor = state.energy_anchor_utc
    state.update_energy(full_after_time - 24 * 60 * 60)
    if state.energy != 91 or state.energy_anchor_utc != accepted_anchor:
        raise AssertionError("M6 clock rollback changed energy evidence")


def _floor_three_launch_rejection(state):
    from app.game.expeditions import ExpeditionLaunchStatus, ExpeditionService

    game = state["route_game"].clone()
    before = game.snapshot()
    service = ExpeditionService(
        state["route_battle_factory"],
        now_factory=lambda: _STARTED_AT,
        assignment_id_factory=lambda: _ASSIGNMENT_ID,
    )
    result = service.launch(
        game,
        outing_floor_id="floor_three",
        destination_floor_id="floor_one",
        category="training",
        confirmed=True,
    )
    if result.status is not ExpeditionLaunchStatus.FLOOR_THREE_BLOCKED:
        raise AssertionError("M6 allowed an assignment alongside Floor III")
    if result.game_state.snapshot() != before:
        raise AssertionError("rejected M6 Floor III launch mutated state")


def _passive_training_lifecycle(state):
    from app.game.expeditions import (
        ExpeditionClaimStatus,
        ExpeditionLaunchStatus,
        ExpeditionService,
        ExpeditionSettlementStatus,
        EXPEDITION_DURATION_SECONDS,
    )

    game = state["route_game"].clone()
    service = ExpeditionService(
        state["route_battle_factory"],
        now_factory=lambda: _STARTED_AT,
        assignment_id_factory=lambda: _ASSIGNMENT_ID,
    )
    launched = service.launch(
        game,
        outing_floor_id="floor_one",
        destination_floor_id="floor_three",
        category="training",
        confirmed=True,
    )
    if launched.status is not ExpeditionLaunchStatus.LAUNCHED:
        raise AssertionError("M6 training assignment did not launch")
    game = launched.game_state
    if game.expedition_state.energy != 90:
        raise AssertionError("M6 launch did not persist its energy debit")
    assignment = game.expedition_state.active_assignment
    if assignment["assignment_id"] != _ASSIGNMENT_ID:
        raise AssertionError("M6 launch recorded the wrong assignment")
    if tuple(assignment["expedition_drifter_ids"]) != tuple(
        item
        for item in ("branoc", "azhvielle", "zhaivra", "joruun")
        if item not in game.party_state.active_drifter_ids
    ):
        raise AssertionError("M6 assignment did not use the roster complement")

    game.party_state.add_floor_one_rewards(experience=125, gold=0)
    if not game.party_state.begin_floor_one_extraction(partial=False):
        raise AssertionError("M6 qualification outing could not extract")
    secured_base_xp = game.party_state.outing_rewards.experience
    if not game.party_state.complete_extraction(game.active_party_members):
        raise AssertionError("M6 qualification outing did not return to the Hub")

    completed_at = _STARTED_AT + EXPEDITION_DURATION_SECONDS
    settled = service.settle_outing(
        game,
        secured_base_xp=secured_base_xp,
        now=completed_at,
    )
    if settled.status is not ExpeditionSettlementStatus.SETTLED:
        raise AssertionError("M6 completed assignment did not settle")
    game = settled.game_state
    report = game.expedition_state.reports[0]
    if report["completed_at_utc"] != "2026-11-10T12:20:00Z":
        raise AssertionError("M6 assignment timer completed at the wrong time")
    if report["secured_base_xp"] != secured_base_xp:
        raise AssertionError("M6 report lost the secured dungeon XP pool")

    claim = service.claim_report(game, _ASSIGNMENT_ID, confirmed=True)
    if claim.status is not ExpeditionClaimStatus.CLAIMED:
        raise AssertionError("M6 completed report did not claim")
    game = claim.game_state
    if not game.expedition_state.reports[0]["claimed"]:
        raise AssertionError("M6 claim status was not persisted")
    before_duplicate = game.snapshot()
    repeated = service.claim_report(game, _ASSIGNMENT_ID, confirmed=True)
    if repeated.status is not ExpeditionClaimStatus.ALREADY_CLAIMED:
        raise AssertionError("M6 report could be claimed twice")
    if repeated.game_state.snapshot() != before_duplicate:
        raise AssertionError("duplicate M6 claim mutated progression")
    state["m6_game"] = game


def _snapshot_reconstruction(state):
    game = state["m6_game"]
    restored = game.clone()
    if restored.snapshot() != game.snapshot():
        raise AssertionError("M6 energy/report state changed on reconstruction")
    if restored.expedition_state.reports[0]["claimed"] is not True:
        raise AssertionError("M6 report claim was lost on reconstruction")
    state["m6_reconstructed_game"] = restored


def _teardown(state):
    state.pop("m6_game", None)
    state.pop("m6_reconstructed_game", None)
    gc.collect()


def run(state, run_stage):
    run_stage(_M6_STAGE_NAMES[0], _energy_clock_and_overflow)
    run_stage(
        _M6_STAGE_NAMES[1],
        lambda: _floor_three_launch_rejection(state),
    )
    run_stage(
        _M6_STAGE_NAMES[2],
        lambda: _passive_training_lifecycle(state),
    )
    run_stage(
        _M6_STAGE_NAMES[3],
        lambda: _snapshot_reconstruction(state),
    )
    run_stage(_M6_STAGE_NAMES[4], lambda: _teardown(state))


__all__ = ("run",)

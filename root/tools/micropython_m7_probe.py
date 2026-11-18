"""Bounded M7 shared Momentum qualification after the M6.5 probe."""


_M7_STAGE_NAMES = ("M7_SHARED_MOMENTUM",)


def _shared_momentum_projection_and_reset():
    from app.combat.combat_state import CombatState

    combat_state = CombatState()
    momentum = combat_state.momentum
    if momentum.position != 5:
        raise AssertionError("M7 encounter Momentum did not start neutral")

    if momentum.shift(3) != 8 or combat_state.momentum is not momentum:
        raise AssertionError("M7 shared Momentum did not favor the Drifters")
    if momentum.critical_bonus_percent_points(False) != 6:
        raise AssertionError("M7 Drifter +3 critical projection changed")
    if momentum.outgoing_damage_bonus_percent(False) != 5:
        raise AssertionError("M7 Drifter +3 damage projection changed")
    if momentum.incoming_mitigation_percent(False) != 5:
        raise AssertionError("M7 Drifter +3 mitigation projection changed")
    if momentum.critical_bonus_percent_points(True) != 0:
        raise AssertionError("M7 enemy faction received the wrong +3 projection")

    if momentum.shift(20) != 10:
        raise AssertionError("M7 Momentum did not clamp at its upper endpoint")
    if (
        momentum.critical_bonus_percent_points(False) != 10
        or momentum.outgoing_damage_bonus_percent(False) != 10
        or momentum.incoming_mitigation_percent(False) != 10
    ):
        raise AssertionError("M7 Drifter +5 projection changed")

    if momentum.shift(-8) != 2 or combat_state.momentum is not momentum:
        raise AssertionError("M7 shared Momentum did not favor the enemies")
    if momentum.critical_bonus_percent_points(True) != 6:
        raise AssertionError("M7 enemy +3 critical projection changed")
    if momentum.outgoing_damage_bonus_percent(True) != 5:
        raise AssertionError("M7 enemy +3 damage projection changed")
    if momentum.incoming_mitigation_percent(True) != 5:
        raise AssertionError("M7 enemy +3 mitigation projection changed")
    if momentum.critical_bonus_percent_points(False) != 0:
        raise AssertionError("M7 Drifters retained bonuses without control")

    if momentum.shift(-20) != 0:
        raise AssertionError("M7 Momentum did not clamp at its lower endpoint")
    if momentum.reset() != 5 or combat_state.momentum is not momentum:
        raise AssertionError("M7 Momentum did not reset the shared encounter state")
    if (
        momentum.critical_bonus_percent_points(False) != 0
        or momentum.critical_bonus_percent_points(True) != 0
        or momentum.outgoing_damage_bonus_percent(False) != 0
        or momentum.incoming_mitigation_percent(False) != 0
        or momentum.outgoing_damage_bonus_percent(True) != 0
        or momentum.incoming_mitigation_percent(True) != 0
    ):
        raise AssertionError("M7 neutral reset retained Momentum bonuses")


def run(run_stage):
    run_stage(
        _M7_STAGE_NAMES[0],
        _shared_momentum_projection_and_reset,
    )


__all__ = ("run",)

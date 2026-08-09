from dataclasses import FrozenInstanceError, dataclass

import pytest

from app.combat.combat_state import CombatState
from app.combat.result import CombatOutcomeTarget, CombatOutcomeType
from app.combat.status_state import (
    ConductiveStatus,
    StatusKind,
    StunStatus,
    TurbulenceStatus,
)
from app.combat.storm import (
    HYDRO_WHIP_MECHANIC,
    LIGHTNING_PALM_MECHANIC,
    STORM_RULES,
    TEMPEST_SURGE_MECHANIC,
)


class _Health:
    def __init__(self, current=20):
        self.current = current

    def take_damage(self, amount):
        self.current = max(0, self.current - amount)


@dataclass
class _Combatant:
    name: str
    hp: int = 20

    def __post_init__(self):
        self.health = _Health(self.hp)

    def effective_stat(self, _name):
        return 10

    def is_alive(self):
        return self.health.current > 0


def test_storm_rules_and_markers_are_locked():
    assert STORM_RULES.conductive_damage_bonus_percent == 25
    assert STORM_RULES.turbulence_damage_bonus_percent == 35
    assert STORM_RULES.lightning_storm_damage_bonus_percent == 100
    assert STORM_RULES.stun_chance_percent == 35
    assert HYDRO_WHIP_MECHANIC == "hydro_whip"
    assert TEMPEST_SURGE_MECHANIC == "tempest_surge"
    assert LIGHTNING_PALM_MECHANIC == "lightning_palm"


@pytest.mark.parametrize(
    ("apply_name", "active_name", "consume_name", "applied", "refreshed", "consumed"),
    (
        (
            "apply_conductive",
            "conductive_active",
            "consume_conductive",
            CombatOutcomeType.CONDUCTIVE_APPLIED,
            CombatOutcomeType.CONDUCTIVE_REFRESHED,
            CombatOutcomeType.CONDUCTIVE_CONSUMED,
        ),
        (
            "apply_turbulence",
            "turbulence_active",
            "consume_turbulence",
            CombatOutcomeType.TURBULENCE_APPLIED,
            CombatOutcomeType.TURBULENCE_REFRESHED,
            CombatOutcomeType.TURBULENCE_CONSUMED,
        ),
    ),
)
def test_binary_storm_statuses_refresh_and_consume_exact_identity(
    apply_name,
    active_name,
    consume_name,
    applied,
    refreshed,
    consumed,
):
    state = CombatState()
    source = _Combatant("source")
    equal_source = _Combatant("source")
    target = _Combatant("target")
    equal_target = _Combatant("target")

    apply_status = getattr(state, apply_name)
    status_active = getattr(state, active_name)
    consume_status = getattr(state, consume_name)

    assert apply_status(source, target).outcome_type == applied
    assert apply_status(source, target).outcome_type == refreshed
    assert status_active(source, target)
    assert status_active(source, target)
    assert not status_active(equal_source, target)
    assert not status_active(source, equal_target)

    outcome = consume_status(source, target)
    assert outcome.outcome_type == consumed
    assert outcome.target == CombatOutcomeTarget.TARGET
    assert not status_active(source, target)
    assert consume_status(source, target) is None


def test_conductive_and_turbulence_coexist_independently():
    state = CombatState()
    source = _Combatant("source")
    target = _Combatant("target")

    state.apply_conductive(source, target)
    state.apply_turbulence(source, target)

    assert state.conductive_active(source, target)
    assert state.turbulence_active(source, target)
    assert state.active_status_kinds(target) == (
        StatusKind.CONDUCTIVE,
        StatusKind.TURBULENCE,
    )

    state.consume_conductive(source, target)
    assert not state.conductive_active(source, target)
    assert state.turbulence_active(source, target)


def test_stun_refreshes_without_stacking_and_consumes_one_opportunity():
    state = CombatState()
    first_source = _Combatant("first")
    second_source = _Combatant("second")
    target = _Combatant("target")

    assert state.apply_stun(first_source, target).outcome_type == CombatOutcomeType.STUN_APPLIED
    state.apply_stun(second_source, target)
    assert state.stun_status(target) == StunStatus(second_source, target)
    assert state.stun_active(target)

    outcomes = state.consume_stun_for_action_opportunity(target)
    assert tuple(outcome.outcome_type for outcome in outcomes) == (
        CombatOutcomeType.STUN_TRIGGERED,
        CombatOutcomeType.STUN_EXPIRED,
    )
    assert all(outcome.target == CombatOutcomeTarget.ACTOR for outcome in outcomes)
    assert not state.stun_active(target)
    assert state.consume_stun_for_action_opportunity(target) == ()
    assert state.turn_count == 0


def test_defeat_and_encounter_cleanup_remove_storm_statuses():
    state = CombatState()
    source = _Combatant("source")
    target = _Combatant("target")
    state.apply_conductive(source, target)
    state.apply_turbulence(source, target)
    state.apply_stun(source, target)

    target.health.take_damage(20)
    assert state.complete_accepted_action(source, (target,)) == ()
    assert state.active_status_kinds(target) == ()

    next_target = _Combatant("next")
    state.apply_conductive(source, next_target)
    state.apply_turbulence(source, next_target)
    state.apply_stun(source, next_target)
    state.clear_statuses()
    assert state.active_status_kinds(next_target) == ()


def test_status_records_are_immutable():
    source = _Combatant("source")
    target = _Combatant("target")
    for status in (
        ConductiveStatus(source, target),
        TurbulenceStatus(source, target),
        StunStatus(source, target),
    ):
        with pytest.raises(FrozenInstanceError):
            status.target = source

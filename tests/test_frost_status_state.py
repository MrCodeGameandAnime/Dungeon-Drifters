from dataclasses import FrozenInstanceError, dataclass

import pytest

from app.combat.combat_state import CombatState
from app.combat.result import CombatOutcome, CombatOutcomeTarget, CombatOutcomeType
from app.combat.status_state import (
    FROSTBITE_DAMAGE_PER_TICK,
    FROSTBITE_DURATION_TICKS,
    FrostCharge,
    FrostbiteStatus,
    FrozenStatus,
    StatusKind,
)


class Health:
    def __init__(self, current=40):
        self.current = current

    def take_damage(self, amount):
        self.current = max(0, self.current - amount)


@dataclass
class Combatant:
    name: str
    hp: int = 40

    def __post_init__(self):
        self.health = Health(self.hp)

    def effective_stat(self, _name):
        return 10

    def is_alive(self):
        return self.health.current > 0


def outcome_types(outcomes):
    return tuple(outcome.outcome_type for outcome in outcomes)


def test_frost_records_are_immutable_and_charge_count_is_strictly_typed():
    source = Combatant("source")
    target = Combatant("target")

    for status in (
        FrostCharge(source, target, 1),
        FrozenStatus(source, target),
        FrostbiteStatus(source, target, 3, 5),
    ):
        with pytest.raises(FrozenInstanceError):
            status.target = source

    first = CombatOutcome(
        CombatOutcomeType.FROST_APPLIED,
        charge_count=1,
    )
    second = CombatOutcome(
        CombatOutcomeType.FROST_APPLIED,
        charge_count=2,
    )
    assert first.charge_count == 1
    assert second.charge_count == 2
    with pytest.raises(ValueError):
        CombatOutcome(CombatOutcomeType.FROST_APPLIED)
    with pytest.raises(ValueError):
        CombatOutcome(CombatOutcomeType.FROST_APPLIED, charge_count=3)
    with pytest.raises(ValueError):
        CombatOutcome(CombatOutcomeType.FROST_TRIGGERED, charge_count=1)


def test_frost_progresses_to_proc_without_storing_three_charges():
    state = CombatState()
    source = Combatant("source")
    target = Combatant("target")

    first = state.apply_frost_charge(source, target)
    second = state.apply_frost_charge(source, target)
    proc = state.apply_frost_charge(source, target)

    assert outcome_types(first) == (CombatOutcomeType.FROST_APPLIED,)
    assert first[0].charge_count == 1
    assert outcome_types(second) == (CombatOutcomeType.FROST_APPLIED,)
    assert second[0].charge_count == 2
    assert outcome_types(proc) == (
        CombatOutcomeType.FROST_TRIGGERED,
        CombatOutcomeType.FROST_CHARGES_CONSUMED,
        CombatOutcomeType.FROZEN_APPLIED,
        CombatOutcomeType.FROSTBITE_APPLIED,
    )
    assert state.frost_charge_count(source, target) == 0
    assert state.frozen_active(target)
    assert state.frostbite_active(target)


def test_frost_charge_identity_is_exact_and_never_aggregated():
    state = CombatState()
    source_a = Combatant("same")
    source_b = Combatant("same")
    target = Combatant("target")

    state.apply_frost_charge(source_a, target)
    state.apply_frost_charge(source_a, target)
    state.apply_frost_charge(source_b, target)

    assert state.frost_charge_count(source_a, target) == 2
    assert state.frost_charge_count(source_b, target) == 1
    assert state.frost_charge_count(source_a, Combatant("target")) == 0


def test_frozen_consumes_before_stun_and_preserves_stun():
    state = CombatState()
    source = Combatant("source")
    target = Combatant("target")
    state.apply_stun(source, target)
    state.apply_frozen(source, target)

    frozen = state.consume_action_opportunity_suppression(target)
    assert outcome_types(frozen) == (
        CombatOutcomeType.FROZEN_TRIGGERED,
        CombatOutcomeType.FROZEN_EXPIRED,
    )
    assert state.stun_active(target)
    assert state.turn_count == 0

    stunned = state.consume_action_opportunity_suppression(target)
    assert outcome_types(stunned) == (
        CombatOutcomeType.STUN_TRIGGERED,
        CombatOutcomeType.STUN_EXPIRED,
    )
    assert not state.stun_active(target)


def test_frostbite_ticks_after_accepted_actions_and_refreshes():
    state = CombatState()
    source = Combatant("source")
    target = Combatant("target", hp=30)

    state.apply_frostbite(
        source,
        target,
        damage_per_tick=FROSTBITE_DAMAGE_PER_TICK,
        ticks=FROSTBITE_DURATION_TICKS,
    )
    assert target.health.current == 30
    refreshed = state.apply_frostbite(
        Combatant("new-source"),
        target,
        damage_per_tick=9,
        ticks=3,
    )
    assert refreshed.outcome_type == CombatOutcomeType.FROSTBITE_REFRESHED
    assert state.frostbite_status(target).damage_per_tick == 9
    assert state.frostbite_status(target).remaining_ticks == 3

    outcomes = state.complete_accepted_action(target, (source,))
    assert outcome_types(outcomes) == (CombatOutcomeType.FROSTBITE_TICK,)
    assert outcomes[0].amount == 9
    assert state.frostbite_status(target).remaining_ticks == 2

    state.complete_accepted_action(target, (source,))
    final = state.complete_accepted_action(target, (source,))
    assert outcome_types(final) == (
        CombatOutcomeType.FROSTBITE_TICK,
        CombatOutcomeType.FROSTBITE_EXPIRED,
    )
    assert not state.frostbite_active(target)


def test_frozen_skip_does_not_tick_frostbite_or_advance_lifecycle():
    state = CombatState()
    source = Combatant("source")
    target = Combatant("target", hp=30)
    state.apply_frozen(source, target)
    state.apply_frostbite(
        source,
        target,
        damage_per_tick=5,
        ticks=3,
    )

    outcomes = state.consume_action_opportunity_suppression(target)
    assert outcome_types(outcomes) == (
        CombatOutcomeType.FROZEN_TRIGGERED,
        CombatOutcomeType.FROZEN_EXPIRED,
    )
    assert target.health.current == 30
    assert state.frostbite_status(target).remaining_ticks == 3
    assert state.turn_count == 0


def test_source_defeat_clears_only_that_source_frost_state():
    state = CombatState()
    source_a = Combatant("source-a")
    source_b = Combatant("source-b")
    target_a = Combatant("target-a")
    target_b = Combatant("target-b")

    state.apply_frost_charge(source_a, target_a)
    state.apply_frozen(source_a, target_a)
    state.apply_frostbite(source_a, target_a, damage_per_tick=5, ticks=3)
    state.apply_frostbite(source_b, target_b, damage_per_tick=7, ticks=3)
    source_a.health.take_damage(source_a.health.current)

    state.complete_accepted_action(source_a, (target_a,))

    assert state.frost_charge_count(source_a, target_a) == 0
    assert not state.frozen_active(target_a)
    assert not state.frostbite_active(target_a)
    assert state.frostbite_active(target_b)
    assert state.frostbite_status(target_b).source is source_b


def test_target_defeat_and_encounter_cleanup_remove_all_frost_state():
    state = CombatState()
    source = Combatant("source")
    target = Combatant("target")
    state.apply_frost_charge(source, target)
    state.apply_frozen(source, target)
    state.apply_frostbite(source, target, damage_per_tick=5, ticks=3)
    target.health.take_damage(target.health.current)

    assert state.complete_accepted_action(source, (target,)) == ()
    assert state.active_status_kinds(target) == ()

    next_target = Combatant("next-target")
    state.apply_frost_charge(source, next_target)
    state.apply_frozen(source, next_target)
    state.apply_frostbite(source, next_target, damage_per_tick=5, ticks=3)
    state.clear_statuses()
    assert state.active_status_kinds(next_target) == ()

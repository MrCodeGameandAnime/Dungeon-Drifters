from dataclasses import FrozenInstanceError, dataclass, field

import pytest

from app.combat.combat_state import CombatState
from app.combat.result import CombatOutcome, CombatOutcomeTarget, CombatOutcomeType
from app.combat.status_state import (
    BURN_DURATION_TICKS,
    BurnStatus,
    StatusKind,
    StatusState,
    burn_damage_per_tick,
)
from app.player.character import RogueArcher
from app.player.player_state import PlayerState
from app.player.resources import Health


@dataclass(eq=True)
class FakeCombatant:
    name: str
    intelligence: int = 10
    intuition: int = 15
    maximum_hp: int = 100
    health: Health = field(init=False, compare=False)

    def __post_init__(self):
        self.health = Health(self.maximum_hp)

    @property
    def display_name(self):
        return self.name

    def effective_stat(self, name):
        return getattr(self, name)

    def is_alive(self):
        return self.health.is_alive()


def test_standard_burn_identity_and_zhaivra_potency_are_locked():
    zhaivra = PlayerState(RogueArcher())

    assert StatusKind.BURN.value == "burn"
    assert zhaivra.effective_stat("intelligence") == 10
    assert zhaivra.effective_stat("intuition") == 15
    assert burn_damage_per_tick(zhaivra) == 7


def test_burn_application_snapshots_potency_without_immediate_damage():
    source = FakeCombatant("source")
    target = FakeCombatant("target")
    state = StatusState()
    before = target.health.current

    outcome = state.apply_burn(source, target)
    burn = state.burn_status(target)

    assert outcome.outcome_type == CombatOutcomeType.BURN_APPLIED
    assert outcome.target == CombatOutcomeTarget.TARGET
    assert target.health.current == before
    assert burn == BurnStatus(source, target, BURN_DURATION_TICKS, 7)
    with pytest.raises(FrozenInstanceError):
        burn.remaining_ticks = 1

    source.intelligence = 100
    tick = state.advance_after_accepted_action(target)

    assert tick[0].amount == 7


def test_burn_advances_only_after_afflicted_actor_accepted_action():
    source = FakeCombatant("source")
    target = FakeCombatant("target")
    unrelated = FakeCombatant("unrelated")
    state = CombatState()
    state.apply_burn(source, target)

    assert state.complete_accepted_action(source, (target,)) == ()
    assert state.complete_accepted_action(unrelated, (target,)) == ()
    assert target.health.current == 100
    assert state.burn_status(target).remaining_ticks == 3

    outcomes = state.complete_accepted_action(target, (source,))

    assert tuple(outcome.outcome_type for outcome in outcomes) == (
        CombatOutcomeType.BURN_TICK,
    )
    assert outcomes[0].amount == 7
    assert target.health.current == 93
    assert state.burn_status(target).remaining_ticks == 2


def test_burn_ticks_exactly_three_times_then_expires():
    source = FakeCombatant("source")
    target = FakeCombatant("target")
    state = CombatState()
    state.apply_burn(source, target)

    first = state.complete_accepted_action(target, (source,))
    second = state.complete_accepted_action(target, (source,))
    third = state.complete_accepted_action(target, (source,))
    fourth = state.complete_accepted_action(target, (source,))

    assert tuple(outcome.outcome_type for outcome in first) == (
        CombatOutcomeType.BURN_TICK,
    )
    assert tuple(outcome.outcome_type for outcome in second) == (
        CombatOutcomeType.BURN_TICK,
    )
    assert tuple(outcome.outcome_type for outcome in third) == (
        CombatOutcomeType.BURN_TICK,
        CombatOutcomeType.BURN_EXPIRED,
    )
    assert fourth == ()
    assert target.health.current == 79
    assert state.burn_active(target) is False


def test_burn_reports_actual_capped_damage_and_clears_after_defeat():
    source = FakeCombatant("source")
    target = FakeCombatant("target")
    target.health.take_damage(96)
    state = CombatState()
    state.apply_burn(source, target)

    outcomes = state.complete_accepted_action(target, (source,))

    assert target.health.current == 0
    assert tuple(outcome.outcome_type for outcome in outcomes) == (
        CombatOutcomeType.BURN_TICK,
        CombatOutcomeType.BURN_EXPIRED,
    )
    assert outcomes[0].amount == 4
    assert state.burn_active(target) is False


def test_burn_bypasses_defend_and_brace_without_consuming_combat_resources():
    source = FakeCombatant("source")
    target = FakeCombatant("target")
    state = CombatState()
    state.activate_defend(target)
    state.activate_brace(target)
    state.apply_burn(source, target)

    state.complete_accepted_action(target, (source,))

    assert target.health.current == 93
    assert state.is_defending(target) is True
    assert state.brace_incoming_protection_active(target) is True


def test_burn_tick_spends_no_mana_and_grants_no_super():
    target = PlayerState(RogueArcher())
    state = CombatState()
    state.apply_burn(target, target)
    mana_before = target.mana_resource.current
    super_before = target.super_resource.current

    state.complete_accepted_action(target, ())

    assert target.mana_resource.current == mana_before
    assert target.super_resource.current == super_before


def test_burn_refreshes_duration_and_retains_stronger_snapshotted_potency():
    weak = FakeCombatant("weak", intelligence=5, intuition=5)
    strong = FakeCombatant("strong", intelligence=15, intuition=20)
    strongest = FakeCombatant("strongest", intelligence=25, intuition=25)
    target = FakeCombatant("target")
    state = StatusState()

    state.apply_burn(strong, target)
    state.advance_after_accepted_action(target)
    weak_refresh = state.apply_burn(weak, target)
    retained = state.burn_status(target)

    assert weak_refresh.outcome_type == CombatOutcomeType.BURN_REFRESHED
    assert retained.remaining_ticks == 3
    assert retained.damage_per_tick == 9
    assert retained.source is strong

    strong_refresh = state.apply_burn(strongest, target)
    replaced = state.burn_status(target)

    assert strong_refresh.outcome_type == CombatOutcomeType.BURN_REFRESHED
    assert replaced.remaining_ticks == 3
    assert replaced.damage_per_tick == 12
    assert replaced.source is strongest


def test_burn_target_and_source_ownership_are_identity_safe_and_unhashable():
    first_source = FakeCombatant("same")
    second_source = FakeCombatant("same")
    first_target = FakeCombatant("same")
    second_target = FakeCombatant("same")
    state = StatusState()

    state.apply_burn(first_source, first_target)

    assert state.burn_active(first_target) is True
    assert state.burn_active(second_target) is False
    assert state.burn_status(first_target).source is first_source
    assert state.burn_status(first_target).source is not second_source


def test_defeated_afflicted_actor_clears_without_ticking():
    source = FakeCombatant("source")
    target = FakeCombatant("target")
    state = CombatState()
    state.apply_burn(source, target)
    target.health.take_damage(target.health.maximum)

    outcomes = state.complete_accepted_action(target, (source,))

    assert tuple(outcome.outcome_type for outcome in outcomes) == (
        CombatOutcomeType.BURN_EXPIRED,
    )
    assert state.burn_active(target) is False


def test_defeated_opposing_target_is_cleared_without_tick():
    source = FakeCombatant("source")
    target = FakeCombatant("target")
    state = CombatState()
    state.apply_burn(source, target)
    target.health.take_damage(target.health.maximum)

    outcomes = state.complete_accepted_action(source, (target,))

    assert tuple(outcome.outcome_type for outcome in outcomes) == (
        CombatOutcomeType.BURN_EXPIRED,
    )
    assert outcomes[0].target == CombatOutcomeTarget.TARGET
    assert state.burn_active(target) is False


def test_observation_clear_and_new_encounter_state_do_not_leak_or_tick():
    source = FakeCombatant("source")
    target = FakeCombatant("target")
    first = CombatState()
    second = CombatState()
    first.apply_burn(source, target)
    before = target.health.current

    assert first.burn_active(target) is True
    assert first.burn_status(target) == first.burn_status(target)
    assert target.health.current == before
    assert second.burn_active(target) is False

    first.clear_statuses()

    assert first.burn_active(target) is False


def test_burn_tick_outcome_requires_positive_actor_damage():
    with pytest.raises(ValueError):
        CombatOutcome(
            CombatOutcomeType.BURN_TICK,
            amount=0,
            target=CombatOutcomeTarget.ACTOR,
        )
    with pytest.raises(ValueError):
        CombatOutcome(
            CombatOutcomeType.BURN_TICK,
            amount=1,
            target=CombatOutcomeTarget.TARGET,
        )

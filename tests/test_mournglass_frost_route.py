from app.combat.combat_state import CombatState
from app.combat.frost import FROST_ATTACK_MECHANIC
from app.combat.result import CombatOutcomeTarget, CombatOutcomeType
from app.combat.resolver import CombatResolver
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import BlackMage
from app.player.player_state import PlayerState
from app.presentation.battle_presenter import BattlePresenter
from app.presentation.battle_models import InteractionPhase


class ScriptedRng:
    def __init__(self, *rolls):
        self.rolls = list(rolls)
        self.calls = []

    def randint(self, start, end):
        self.calls.append((start, end))
        return self.rolls.pop(0)


def _combatants(target_hp=200):
    actor = PlayerState(BlackMage())
    target = EnemyState(Goblin())
    target.health.set_maximum(target_hp)
    target.health.current = target_hp
    return actor, target


def _cast(actor, target, state, rng):
    return CombatResolver(rng=rng).resolve_move(
        actor,
        target,
        "Mournglass Bloom",
        combat_state=state,
        character_run_state=actor.character_run_state,
    )


def test_mournglass_marker_preserves_authored_values_and_presents_frost_route():
    actor, target = _combatants()
    move = next(move for move in actor.combat_moves if move.name == "Mournglass Bloom")

    assert move.mechanic == FROST_ATTACK_MECHANIC
    assert (move.resource_cost, move.power, move.accuracy) == (6, 12, 90)
    assert move.is_spell is True

    view = BattlePresenter().build(
        player=actor,
        enemy=target,
        combat_state=CombatState(),
        interaction_phase=InteractionPhase.REGULAR_MOVES,
    )
    option = next(option for option in view.move_options if option.name == move.name)
    assert option.tags == ("Magical", "Frost", "6 Mana")
    assert "At 3 Frost" in option.rules_summary


def test_first_and_second_mournglass_hits_apply_frost_without_backlash_rng():
    actor, target = _combatants()
    state = CombatState()

    first_rng = ScriptedRng(1, 100)
    first = _cast(actor, target, state, first_rng)
    second_rng = ScriptedRng(1, 100)
    second = _cast(actor, target, state, second_rng)

    assert [outcome.charge_count for outcome in first.outcomes] == [1]
    assert [outcome.charge_count for outcome in second.outcomes] == [2]
    assert state.frost_charge_count(actor, target) == 2
    assert first_rng.calls == [(1, 100), (1, 100)]
    assert second_rng.calls == [(1, 100), (1, 100)]


def test_third_mournglass_hit_procs_target_then_rolls_one_backlash_check():
    actor, target = _combatants()
    state = CombatState()
    _cast(actor, target, state, ScriptedRng(1, 100))
    _cast(actor, target, state, ScriptedRng(1, 100))

    rng = ScriptedRng(1, 100, 15)
    result = _cast(actor, target, state, rng)

    assert [outcome.outcome_type for outcome in result.outcomes] == [
        CombatOutcomeType.FROST_TRIGGERED,
        CombatOutcomeType.FROST_CHARGES_CONSUMED,
        CombatOutcomeType.FROZEN_APPLIED,
        CombatOutcomeType.FROSTBITE_APPLIED,
        CombatOutcomeType.FROST_BACKLASH_TRIGGERED,
    ]
    assert result.outcomes[-1].target == CombatOutcomeTarget.ACTOR
    assert target.health.current < 200
    assert state.frozen_active(target)
    assert state.frostbite_active(target)
    assert state.frozen_active(actor)
    assert not state.frostbite_active(actor)
    assert state.frost_charge_count(actor, actor) == 0
    assert actor.health.current == actor.health.maximum
    assert rng.calls == [(1, 100), (1, 100), (1, 100)]


def test_sixteen_backlash_roll_fails_and_target_payoff_remains_complete():
    actor, target = _combatants()
    state = CombatState()
    _cast(actor, target, state, ScriptedRng(1, 100))
    _cast(actor, target, state, ScriptedRng(1, 100))

    result = _cast(actor, target, state, ScriptedRng(1, 100, 16))

    assert result.outcomes[-1].outcome_type == CombatOutcomeType.FROSTBITE_APPLIED
    assert all(
        outcome.outcome_type != CombatOutcomeType.FROST_BACKLASH_TRIGGERED
        for outcome in result.outcomes
    )
    assert state.frozen_active(target)
    assert state.frostbite_active(target)
    assert not state.frozen_active(actor)


def test_miss_rejection_and_lethal_hit_never_roll_frost_backlash():
    actor, target = _combatants()
    state = CombatState()
    state.apply_frost_charge(actor, target)
    state.apply_frost_charge(actor, target)

    miss_rng = ScriptedRng(100)
    miss = _cast(actor, target, state, miss_rng)
    assert miss.hit is False
    assert miss_rng.calls == [(1, 100)]
    assert state.frost_charge_count(actor, target) == 2

    actor.mana_resource.spend(actor.mana_resource.current)
    rejected_rng = ScriptedRng()
    rejected = _cast(actor, target, state, rejected_rng)
    assert rejected.accepted is False
    assert rejected_rng.calls == []
    assert state.frost_charge_count(actor, target) == 2

    actor.mana_resource.restore(6)
    target.health.current = 1
    lethal_rng = ScriptedRng(1, 100)
    lethal = _cast(actor, target, state, lethal_rng)
    assert lethal.hit is True
    assert target.is_alive() is False
    assert lethal_rng.calls == [(1, 100), (1, 100)]
    assert all(
        outcome.outcome_type != CombatOutcomeType.FROST_BACKLASH_TRIGGERED
        for outcome in lethal.outcomes
    )
    assert not state.frozen_active(target)
    assert not state.frostbite_active(target)


def test_backlash_frozen_caster_skips_only_one_player_opportunity():
    actor, target = _combatants()
    state = CombatState()
    state.apply_frozen(actor, actor)

    outcomes = state.consume_action_opportunity_suppression(actor)

    assert [outcome.outcome_type for outcome in outcomes] == [
        CombatOutcomeType.FROZEN_TRIGGERED,
        CombatOutcomeType.FROZEN_EXPIRED,
    ]
    assert not state.frozen_active(actor)
    assert state.turn_count == 0

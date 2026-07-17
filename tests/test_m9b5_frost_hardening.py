import random

import app.combat.battle as battle_module
from app.combat.battle import Battle
from app.combat.combat_state import CombatState
from app.combat.resolver import CombatResolver
from app.combat.result import CombatOutcomeType
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import BlackMage, Brawler
from app.player.player_state import PlayerState
from app.presentation.battle_models import ActionIntent, BattleEventType, InteractionPhase
from app.presentation.battle_session import BattlePresentationSession
from app.ui.battle_ui import ChooseAction, ChooseMove


class FixedRng:
    @staticmethod
    def randint(start, _end):
        return start


class NoInputUI:
    def render(self, _view):
        return None

    def read_input(self, _view):
        raise AssertionError("suppressed opportunity must not request input")


class AzhvielleFrostUI:
    def __init__(self):
        self.inputs = 0

    def render(self, _view):
        return None

    def read_input(self, view):
        self.inputs += 1
        if self.inputs > 100:
            raise AssertionError("Azhvielle Frost route did not terminate")
        if view.interaction_phase == InteractionPhase.ACTIONS:
            return ChooseAction(ActionIntent.ATTACK)
        if view.interaction_phase == InteractionPhase.REGULAR_MOVES:
            offered = {option.selection_key: option for option in view.move_options}
            if offered.get("Mournglass Bloom", None) and offered["Mournglass Bloom"].enabled:
                return ChooseMove("Mournglass Bloom")
            return ChooseMove("Scepter Sweep")
        raise AssertionError(f"unexpected phase: {view.interaction_phase}")


def _actors(target_hp=None):
    actor = PlayerState(BlackMage())
    target = EnemyState(Goblin())
    if target_hp is not None:
        target.health.set_maximum(target_hp)
        target.health.current = target_hp
    return actor, target


def _outcome_types(outcomes):
    return tuple(outcome.outcome_type for outcome in outcomes)


def test_frozen_refresh_keeps_exactly_one_pending_skip():
    state = CombatState()
    source = PlayerState(BlackMage())
    refreshed_source = PlayerState(Brawler())
    target = EnemyState(Goblin())

    assert state.apply_frozen(source, target).outcome_type == CombatOutcomeType.FROZEN_APPLIED
    assert state.apply_frozen(refreshed_source, target).outcome_type == CombatOutcomeType.FROZEN_REFRESHED
    assert _outcome_types(state.consume_action_opportunity_suppression(target)) == (
        CombatOutcomeType.FROZEN_TRIGGERED,
        CombatOutcomeType.FROZEN_EXPIRED,
    )
    assert state.consume_action_opportunity_suppression(target) == ()


def test_player_frozen_skips_input_resolver_lifecycle_and_turn_advance():
    player = PlayerState(BlackMage())
    enemy = EnemyState(Goblin())
    battle = Battle(player, enemy, ui=NoInputUI(), resolver=CombatResolver(rng=FixedRng()))
    battle.combat_state.apply_frozen(enemy, player)
    mana_before = player.mana_resource.current

    skipped = battle._skip_action_opportunity_suppression(player)

    assert skipped is True
    assert battle.combat_state.turn_count == 0
    assert player.mana_resource.current == mana_before
    assert battle.combat_state.frozen_active(player) is False
    entry = battle.presentation_session.entries[-1]
    assert entry.event_type == BattleEventType.STATUS
    assert _outcome_types(entry.outcomes) == (
        CombatOutcomeType.FROZEN_TRIGGERED,
        CombatOutcomeType.FROZEN_EXPIRED,
    )


def test_enemy_frozen_skips_resolver_lifecycle_and_turn_advance():
    player = PlayerState(BlackMage())
    enemy = EnemyState(Goblin())
    battle = Battle(player, enemy, ui=NoInputUI(), resolver=CombatResolver(rng=FixedRng()))
    battle.combat_state.apply_frozen(player, enemy)

    skipped = battle._skip_action_opportunity_suppression(enemy)

    assert skipped is True
    assert battle.combat_state.turn_count == 0
    assert battle.combat_state.frozen_active(enemy) is False
    assert _outcome_types(battle.presentation_session.entries[-1].outcomes) == (
        CombatOutcomeType.FROZEN_TRIGGERED,
        CombatOutcomeType.FROZEN_EXPIRED,
    )


def test_frozen_precedes_stun_then_stun_is_consumed_on_next_opportunity():
    state = CombatState()
    source = PlayerState(BlackMage())
    target = EnemyState(Goblin())
    state.apply_stun(source, target)
    state.apply_frozen(source, target)

    first = state.consume_action_opportunity_suppression(target)
    second = state.consume_action_opportunity_suppression(target)

    assert _outcome_types(first) == (
        CombatOutcomeType.FROZEN_TRIGGERED,
        CombatOutcomeType.FROZEN_EXPIRED,
    )
    assert _outcome_types(second) == (
        CombatOutcomeType.STUN_TRIGGERED,
        CombatOutcomeType.STUN_EXPIRED,
    )
    assert state.turn_count == 0


def test_frostbite_rebuilds_during_active_frostbite_without_extra_stack():
    state = CombatState()
    source = PlayerState(BlackMage())
    target = EnemyState(Goblin())
    state.apply_frostbite(source, target, damage_per_tick=5, ticks=3)
    state.apply_frost_charge(source, target)
    state.apply_frost_charge(source, target)

    tick = state.complete_accepted_action(target, (source,))
    proc = state.apply_frost_charge(source, target)

    assert _outcome_types(tick) == (CombatOutcomeType.FROSTBITE_TICK,)
    assert _outcome_types(proc) == (
        CombatOutcomeType.FROST_TRIGGERED,
        CombatOutcomeType.FROST_CHARGES_CONSUMED,
        CombatOutcomeType.FROZEN_APPLIED,
        CombatOutcomeType.FROSTBITE_REFRESHED,
    )
    assert state.frostbite_status(target).remaining_ticks == 3


def test_burn_poison_frostbite_tick_order_and_lethal_burn_cleanup():
    state = CombatState()
    source = PlayerState(BlackMage())
    target = EnemyState(Goblin())
    target.health.current = 1
    state.apply_burn(source, target)
    state.apply_poison(source, target)
    state.apply_frostbite(source, target, damage_per_tick=5, ticks=3)

    outcomes = state.complete_accepted_action(target, (source,))

    assert _outcome_types(outcomes) == (
        CombatOutcomeType.BURN_TICK,
        CombatOutcomeType.BURN_EXPIRED,
        CombatOutcomeType.POISON_EXPIRED,
    )
    assert CombatOutcomeType.POISON_TICK not in _outcome_types(outcomes)
    assert CombatOutcomeType.FROSTBITE_TICK not in _outcome_types(outcomes)
    assert not state.burn_active(target)
    assert not state.poison_active(target)
    assert not state.frostbite_active(target)


def test_poison_then_frostbite_order_and_later_tick_cleanup():
    state = CombatState()
    source = PlayerState(BlackMage())
    target = EnemyState(Goblin())
    target.health.current = 8
    state.apply_burn(source, target)
    state.apply_poison(source, target)
    state.apply_frostbite(source, target, damage_per_tick=5, ticks=3)

    outcomes = state.complete_accepted_action(target, (source,))

    assert _outcome_types(outcomes) == (
        CombatOutcomeType.BURN_TICK,
        CombatOutcomeType.POISON_TICK,
        CombatOutcomeType.POISON_EXPIRED,
        CombatOutcomeType.BURN_EXPIRED,
    )
    assert CombatOutcomeType.FROSTBITE_TICK not in _outcome_types(outcomes)
    assert not state.burn_active(target)
    assert not state.poison_active(target)
    assert not state.frostbite_active(target)


def test_lethal_frostbite_clears_all_statuses_without_natural_expiration():
    state = CombatState()
    source = PlayerState(BlackMage())
    target = EnemyState(Goblin())
    target.health.current = 16
    state.apply_burn(source, target)
    state.apply_poison(source, target)
    state.apply_frostbite(source, target, damage_per_tick=5, ticks=3)
    state.apply_frost_charge(source, target)
    state.apply_frozen(source, target)

    outcomes = state.complete_accepted_action(target, (source,))

    assert _outcome_types(outcomes)[:3] == (
        CombatOutcomeType.BURN_TICK,
        CombatOutcomeType.POISON_TICK,
        CombatOutcomeType.FROSTBITE_TICK,
    )
    assert _outcome_types(outcomes) == (
        CombatOutcomeType.BURN_TICK,
        CombatOutcomeType.POISON_TICK,
        CombatOutcomeType.FROSTBITE_TICK,
        CombatOutcomeType.BURN_EXPIRED,
        CombatOutcomeType.POISON_EXPIRED,
    )
    assert target.health.current == 0
    assert CombatOutcomeType.FROSTBITE_EXPIRED not in _outcome_types(outcomes)
    assert not state.burn_active(target)
    assert not state.poison_active(target)
    assert not state.frostbite_active(target)
    assert not state.frozen_active(target)
    assert state.frost_charge_count(source, target) == 0
    assert state.complete_accepted_action(target, (source,)) == ()


def test_frost_source_defeat_clears_all_its_frost_effects_only():
    state = CombatState()
    source_a = PlayerState(BlackMage())
    source_b = PlayerState(Brawler())
    target = EnemyState(Goblin())
    other_target = EnemyState(Goblin())
    state.apply_frost_charge(source_a, target)
    state.apply_frozen(source_a, target)
    state.apply_frostbite(source_a, target, damage_per_tick=5, ticks=3)
    state.apply_frostbite(source_b, other_target, damage_per_tick=5, ticks=3)
    source_a.health.take_damage(source_a.health.current)

    state.complete_accepted_action(source_a, (target, other_target))

    assert state.frost_charge_count(source_a, target) == 0
    assert not state.frozen_active(target)
    assert not state.frostbite_active(target)
    assert state.frostbite_status(other_target).source is source_b


def test_long_target_completes_three_charge_frozen_and_three_frostbite_ticks():
    actor, target = _actors(target_hp=300)
    state = CombatState()
    resolver = CombatResolver(rng=FixedRng())

    results = [
        resolver.resolve_move(
            actor,
            target,
            "Mournglass Bloom",
            combat_state=state,
            character_run_state=actor.character_run_state,
        )
        for _ in range(3)
    ]

    assert all(result.accepted and result.hit for result in results)
    assert state.frost_charge_count(actor, target) == 0
    assert state.frozen_active(target)
    assert state.frostbite_status(target).remaining_ticks == 3
    skipped = state.consume_action_opportunity_suppression(target)
    assert _outcome_types(skipped) == (
        CombatOutcomeType.FROZEN_TRIGGERED,
        CombatOutcomeType.FROZEN_EXPIRED,
    )
    ticks = [
        state.complete_accepted_action(target, (actor,))
        for _ in range(3)
    ]
    assert [_outcome_types(outcome) for outcome in ticks] == [
        (CombatOutcomeType.FROSTBITE_TICK,),
        (CombatOutcomeType.FROSTBITE_TICK,),
        (CombatOutcomeType.FROSTBITE_TICK, CombatOutcomeType.FROSTBITE_EXPIRED),
    ]
    assert not state.frostbite_active(target)


def test_azhvielle_mournglass_goblin_route_remains_playable(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda _start, _end: 1)
    monkeypatch.setattr(battle_module.random, "choice", lambda moves: moves[0])
    battle = Battle(
        PlayerState(BlackMage()),
        EnemyState(Goblin()),
        ui=AzhvielleFrostUI(),
        resolver=CombatResolver(rng=FixedRng()),
    )

    assert battle.run() == "player"
    assert battle.foe.health.current == 0
    assert battle.player.health.is_alive()


def test_frost_state_is_encounter_local_and_gravemantle_regression_remains_intact():
    actor, target = _actors()
    first = CombatState()
    first.apply_frost_charge(actor, target)
    first.activate_arcane_overcharge(actor, broken_target=target)
    second = CombatState()

    assert second.frost_charge_count(actor, target) == 0
    assert not second.arcane_overcharge_active(actor)
    assert first.frost_charge_count(actor, target) == 1
    assert first.gravemantle_break_active(target)

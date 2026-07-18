from dataclasses import replace

from app.combat.combat_state import CombatState
from app.combat.move import DamageType
from app.combat.result import (
    CombatOutcomeType,
    CombatOutcomeTarget,
)
from app.combat.resolver import CombatResolver
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import BlackMage, Brawler
from app.player.player_state import PlayerState


class ScriptedRng:
    def __init__(self, *rolls):
        self.rolls = list(rolls)
        self.calls = []

    def randint(self, start, end):
        self.calls.append((start, end))
        return self.rolls.pop(0)


def _azhvielle():
    return PlayerState(BlackMage())


def _goblin():
    return EnemyState(Goblin())


def test_atomic_arcane_discharge_returns_facts_and_clears_live_state():
    actor = _azhvielle()
    target = _goblin()
    state = CombatState()
    state.activate_arcane_overcharge(actor, broken_target=target)
    state.activate_arcane_instability(actor)

    discharge = state.consume_arcane_discharge(actor)

    assert discharge.spell_bonus_percent == 30
    assert discharge.broken_target is target
    assert discharge.break_reduction_percent == 30
    assert discharge.instability_was_active is True
    assert state.arcane_overcharge_active(actor) is False
    assert state.gravemantle_break_active(target) is False
    assert state.arcane_instability_active(actor) is False


def test_gravemantle_hit_grants_overcharge_and_break_without_backlash():
    actor = _azhvielle()
    target = _goblin()
    rng = ScriptedRng(1, 100, 100)

    result = CombatResolver(rng=rng).resolve_move(
        actor,
        target,
        "Gravemantle Rupture",
        combat_state=CombatState(),
    )

    assert result.accepted and result.hit and result.damage > 0
    assert actor.mana_resource.current == 44
    assert [outcome.outcome_type for outcome in result.outcomes] == [
        CombatOutcomeType.BREAK_APPLIED,
        CombatOutcomeType.OVERCHARGE_GAINED,
    ]


def test_gravemantle_miss_grants_charge_without_break_and_backlash_can_apply():
    actor = _azhvielle()
    target = _goblin()
    state = CombatState()
    rng = ScriptedRng(100, 1, 6)

    result = CombatResolver(rng=rng).resolve_move(
        actor,
        target,
        "Gravemantle Rupture",
        combat_state=state,
    )

    assert result.accepted and result.hit is False and result.damage == 0
    assert state.arcane_overcharge_active(actor) is True
    assert state.gravemantle_break_active(target) is False
    assert state.arcane_instability_active(actor) is True
    assert any(
        outcome.outcome_type == CombatOutcomeType.BACKLASH_DAMAGE
        and outcome.amount == 6
        and outcome.target == CombatOutcomeTarget.ACTOR
        for outcome in result.outcomes
    )


def test_backlash_outcome_reports_actual_hp_lost_after_capping():
    actor = _azhvielle()
    actor.health.take_damage(actor.health.current - 4)
    target = _goblin()
    rng = ScriptedRng(100, 1, 8)

    result = CombatResolver(rng=rng).resolve_move(
        actor,
        target,
        "Gravemantle Rupture",
        combat_state=CombatState(),
    )

    backlash = next(
        outcome
        for outcome in result.outcomes
        if outcome.outcome_type == CombatOutcomeType.BACKLASH_DAMAGE
    )
    assert actor.health.current == 0
    assert backlash.amount == 4
    assert not any(
        outcome.outcome_type == CombatOutcomeType.INSTABILITY_APPLIED
        for outcome in result.outcomes
    )


def test_same_target_spell_discharge_uses_captured_break_and_clears_once():
    actor = _azhvielle()
    target = _goblin()
    state = CombatState()
    state.activate_arcane_overcharge(actor, broken_target=target)
    state.activate_arcane_instability(actor)
    rng = ScriptedRng(1, 100)

    result = CombatResolver(rng=rng).resolve_move(
        actor,
        target,
        "Gloamweight Sepulcher",
        combat_state=state,
    )

    assert result.accepted and result.hit
    assert [outcome.outcome_type for outcome in result.outcomes[:3]] == [
        CombatOutcomeType.OVERCHARGE_CONSUMED,
        CombatOutcomeType.BREAK_CLEARED,
        CombatOutcomeType.INSTABILITY_CLEARED,
    ]
    assert state.arcane_overcharge_active(actor) is False
    assert state.gravemantle_break_active(target) is False
    assert state.arcane_instability_active(actor) is False


def test_captured_overcharge_increases_spell_damage_before_mitigation():
    charged_actor = _azhvielle()
    charged_target = _goblin()
    charged_state = CombatState()
    charged_state.activate_arcane_overcharge(charged_actor)

    charged = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        charged_actor,
        charged_target,
        "Gloamweight Sepulcher",
        combat_state=charged_state,
    )

    baseline_actor = _azhvielle()
    baseline_target = _goblin()
    baseline = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        baseline_actor,
        baseline_target,
        "Gloamweight Sepulcher",
        combat_state=CombatState(),
    )

    assert charged.damage > baseline.damage


def test_different_target_spell_discharge_gets_bonus_but_not_captured_break():
    actor = _azhvielle()
    broken_target = _goblin()
    other_target = _goblin()
    state = CombatState()
    state.activate_arcane_overcharge(actor, broken_target=broken_target)
    resolver = CombatResolver(rng=ScriptedRng(1, 100))

    result = resolver.resolve_move(
        actor,
        other_target,
        "Gloamweight Sepulcher",
        combat_state=state,
    )

    assert result.accepted and result.damage > 0
    assert state.gravemantle_break_active(broken_target) is False
    assert state.arcane_overcharge_active(actor) is False


def test_scepter_sweep_uses_live_break_without_consuming_overcharge():
    actor = _azhvielle()
    target = _goblin()
    state = CombatState()
    state.activate_arcane_overcharge(actor, broken_target=target)

    result = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        actor,
        target,
        "Scepter Sweep",
        combat_state=state,
    )

    assert result.accepted and result.hit
    assert state.arcane_overcharge_active(actor) is True
    assert state.gravemantle_break_active(target) is True


def test_recast_uses_old_snapshot_and_not_fresh_break():
    actor = _azhvielle()
    target = _goblin()
    state = CombatState()
    state.activate_arcane_overcharge(actor, broken_target=target)
    rng = ScriptedRng(1, 100, 100)

    result = CombatResolver(rng=rng).resolve_move(
        actor,
        target,
        "Gravemantle Rupture",
        combat_state=state,
    )

    assert result.accepted and result.hit
    assert [outcome.outcome_type for outcome in result.outcomes[:2]] == [
        CombatOutcomeType.OVERCHARGE_CONSUMED,
        CombatOutcomeType.BREAK_CLEARED,
    ]
    assert CombatOutcomeType.BREAK_APPLIED in [
        outcome.outcome_type for outcome in result.outcomes
    ]
    assert state.gravemantle_break_active(target) is True


def test_instability_affects_physical_damage_but_not_magical_or_hybrid():
    def resolve_against(target, move_name, *, unstable):
        attacker = PlayerState(Brawler())
        state = CombatState()
        if unstable:
            state.activate_arcane_overcharge(target)
            state.activate_arcane_instability(target)
        return CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
            attacker,
            target,
            move_name,
            combat_state=state,
        )

    physical_unstable_target = _azhvielle()
    physical_baseline_target = _azhvielle()
    physical_unstable = resolve_against(
        physical_unstable_target,
        "Crestgrave Reaping",
        unstable=True,
    )
    physical_baseline = resolve_against(
        physical_baseline_target,
        "Crestgrave Reaping",
        unstable=False,
    )

    magical_unstable_target = _azhvielle()
    magical_baseline_target = _azhvielle()
    magical_unstable = resolve_against(
        magical_unstable_target,
        "Cinderlung Vesper",
        unstable=True,
    )
    magical_baseline = resolve_against(
        magical_baseline_target,
        "Cinderlung Vesper",
        unstable=False,
    )

    assert physical_unstable.damage > physical_baseline.damage
    assert magical_unstable.damage == magical_baseline.damage

    hybrid_actor = _azhvielle()
    hybrid_move = hybrid_actor.combat_moves[2]
    hybrid_move = replace(hybrid_move, name="Test Hybrid Spell")
    hybrid_actor.character._combat_moves = (*hybrid_actor.combat_moves, hybrid_move)
    hybrid_unstable_target = _azhvielle()
    hybrid_baseline_target = _azhvielle()
    hybrid_unstable_state = CombatState()
    hybrid_unstable_state.activate_arcane_overcharge(hybrid_unstable_target)
    hybrid_unstable_state.activate_arcane_instability(hybrid_unstable_target)
    hybrid_unstable = CombatResolver(rng=ScriptedRng(1, 100, 100)).resolve_move(
        hybrid_actor,
        hybrid_unstable_target,
        "Test Hybrid Spell",
        combat_state=hybrid_unstable_state,
    )
    hybrid_baseline = CombatResolver(rng=ScriptedRng(1, 100, 100)).resolve_move(
        hybrid_actor,
        hybrid_baseline_target,
        "Test Hybrid Spell",
        combat_state=CombatState(),
    )

    assert hybrid_unstable.damage == hybrid_baseline.damage
    assert hybrid_unstable_state.arcane_instability_physical_vulnerability_percent(
        hybrid_unstable_target
    ) == 25


def test_simultaneous_death_is_not_player_victory(monkeypatch):
    from app.combat.battle import Battle
    from app.presentation.battle_models import ActionIntent, InteractionPhase
    from app.ui.battle_ui import ChooseAction, ChooseMove

    actor = _azhvielle()
    actor.health.take_damage(actor.health.current - 4)
    target = _goblin()
    target.health.take_damage(target.health.current - 1)
    stateful_rng = ScriptedRng(1, 100, 1, 10)
    class ScriptedUI:
        def render(self, _view):
            return None

        def read_input(self, view):
            if view.interaction_phase == InteractionPhase.ACTIONS:
                return ChooseAction(ActionIntent.ATTACK)
            return ChooseMove("Gravemantle Rupture")

    battle = Battle(
        actor,
        target,
        ui=ScriptedUI(),
        resolver=CombatResolver(rng=stateful_rng),
    )
    monkeypatch.setattr("app.combat.battle.random.randint", lambda _start, _end: 1)

    result = battle.run()

    assert result == "enemy"
    assert not actor.is_alive()
    assert not target.is_alive()

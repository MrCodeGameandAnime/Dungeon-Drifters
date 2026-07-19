import pytest

from app.combat.combat_state import CombatState
from app.combat.result import CombatOutcome, CombatOutcomeType
from app.combat.resolver import CombatResolver, _mitigation, _scaled_damage_power
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import Monk
from app.player.player_state import PlayerState
from app.presentation.battle_models import BattleEventType, BattleLogEntry, InteractionPhase
from app.presentation.battle_presenter import BattlePresenter
from app.ui.terminal_battle_ui import TerminalBattleUI


class ScriptedRng:
    def __init__(self, *rolls):
        self.rolls = list(rolls)
        self.calls = []

    def randint(self, start, end):
        self.calls.append((start, end))
        return self.rolls.pop(0)


def _joruun():
    return PlayerState(Monk())


def _goblin():
    return EnemyState(Goblin())


def _move(actor, name):
    return next(move for move in actor.combat_moves if move.name == name)


@pytest.mark.parametrize(
    "setup_order",
    (("Hydro Whip", "Tempest Surge"), ("Tempest Surge", "Hydro Whip")),
)
def test_both_preparation_orders_produce_lightning_storm(setup_order):
    actor = _joruun()
    target = _goblin()
    state = CombatState()
    resolver = CombatResolver(rng=ScriptedRng(1, 100, 1, 100, 1, 100))

    for move_name in setup_order:
        assert resolver.resolve_move(
            actor, target, move_name, combat_state=state
        ).hit
    result = resolver.resolve_move(
        actor, target, "Lightning Palm", combat_state=state
    )

    assert result.accepted and result.hit and result.move_name == "Lightning Storm"
    assert result.resource_spent == 7
    assert tuple(outcome.outcome_type for outcome in result.outcomes) == (
        CombatOutcomeType.LIGHTNING_STORM_TRIGGERED,
        CombatOutcomeType.CONDUCTIVE_CONSUMED,
        CombatOutcomeType.TURBULENCE_CONSUMED,
    )
    assert not state.conductive_active(actor, target)
    assert not state.turbulence_active(actor, target)
    assert not state.stun_active(target)


def test_lightning_storm_uses_exclusive_double_damage_before_mitigation():
    actor = _joruun()
    target = _goblin()
    state = CombatState()
    state.apply_conductive(actor, target)
    state.apply_turbulence(actor, target)
    rng = ScriptedRng(1, 100)

    result = CombatResolver(rng=rng).resolve_move(
        actor, target, "Lightning Palm", combat_state=state
    )
    move = _move(actor, "Lightning Palm")
    expected = max(
        1,
        _scaled_damage_power(actor, move) * 200 // 100
        - _mitigation(target, move.damage_type),
    )

    assert result.damage == expected
    assert rng.calls == [(1, 100), (1, 100)]
    assert not state.stun_active(target)


def test_lightning_storm_miss_consumes_both_without_stun_rng():
    actor = _joruun()
    target = _goblin()
    state = CombatState()
    state.apply_conductive(actor, target)
    state.apply_turbulence(actor, target)
    rng = ScriptedRng(100)

    result = CombatResolver(rng=rng).resolve_move(
        actor, target, "Lightning Palm", combat_state=state
    )

    assert result.accepted and not result.hit
    assert result.move_name == "Lightning Storm"
    assert tuple(outcome.outcome_type for outcome in result.outcomes) == (
        CombatOutcomeType.LIGHTNING_STORM_TRIGGERED,
        CombatOutcomeType.CONDUCTIVE_CONSUMED,
        CombatOutcomeType.TURBULENCE_CONSUMED,
    )
    assert not state.conductive_active(actor, target)
    assert not state.turbulence_active(actor, target)
    assert rng.calls == [(1, 100)]


def test_rejected_lightning_storm_preserves_both_states_and_rng():
    actor = _joruun()
    actor.mana_resource.spend(actor.mana_resource.current)
    target = _goblin()
    state = CombatState()
    state.apply_conductive(actor, target)
    state.apply_turbulence(actor, target)
    rng = ScriptedRng()

    result = CombatResolver(rng=rng).resolve_move(
        actor, target, "Lightning Palm", combat_state=state
    )

    assert not result.accepted
    assert state.conductive_active(actor, target)
    assert state.turbulence_active(actor, target)
    assert rng.calls == []


def test_lightning_storm_presentation_preserves_stable_selection_and_authored_move():
    actor = _joruun()
    target = _goblin()
    authored_move = _move(actor, "Lightning Palm")
    state = CombatState()
    state.apply_conductive(actor, target)
    state.apply_turbulence(actor, target)
    presenter = BattlePresenter()

    first = presenter.build(
        player=actor,
        enemy=target,
        combat_state=state,
        interaction_phase=InteractionPhase.REGULAR_MOVES,
    )
    second = presenter.build(
        player=actor,
        enemy=target,
        combat_state=state,
        interaction_phase=InteractionPhase.REGULAR_MOVES,
    )
    storm = next(move for move in first.move_options if move.selection_key == "Lightning Palm")

    assert first == second
    assert storm.selection_key == "Lightning Palm"
    assert storm.name == "Lightning Storm"
    assert storm.tags == ("Hybrid", "Conductive + Turbulence", "7 Mana")
    assert "100% increased damage" in storm.rules_summary
    assert authored_move.name == "Lightning Palm"
    assert state.conductive_active(actor, target)
    assert state.turbulence_active(actor, target)


def test_terminal_uses_lightning_storm_identity_and_ordered_outcomes():
    entry = BattleLogEntry(
        event_type=BattleEventType.DAMAGE,
        actor_name="Joruun Veyr",
        target_name="Goblin",
        action_name="Lightning Storm",
        amount=40,
        accepted=True,
        hit=True,
        outcomes=(
            CombatOutcome(CombatOutcomeType.LIGHTNING_STORM_TRIGGERED),
            CombatOutcome(CombatOutcomeType.CONDUCTIVE_CONSUMED),
            CombatOutcome(CombatOutcomeType.TURBULENCE_CONSUMED),
        ),
    )
    ui = TerminalBattleUI(output_func=lambda _line: None)

    assert ui._log_lines(entry) == (
        "Joruun Veyr used Lightning Storm against Goblin. It dealt 40 damage.",
        "Lightning Palm became Lightning Storm.",
        "Joruun Veyr discharged Conductive through Lightning Storm.",
        "Joruun Veyr discharged Turbulence through Lightning Storm.",
    )

import pytest

import app.combat.battle as battle_module
from app.combat.battle import Battle
from app.combat.combat_state import CombatState
from app.combat.resolver import CombatResolver
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.player.player_state import PlayerState
from app.presentation.battle_models import (
    ActionAvailabilityReason,
    ActionIntent,
    BattleEventType,
    BattleLogEntry,
)
from app.presentation.battle_presenter import BattlePresenter
from app.ui.battle_ui import ChooseAction, ChooseMove
from app.ui.terminal_battle_ui import TerminalBattleUI


class FixedRng:
    def __init__(self, *rolls):
        self.rolls = list(rolls)
        self.calls = []

    def randint(self, start, end):
        self.calls.append((start, end))
        return self.rolls.pop(0)


class ScriptedUI:
    def __init__(self, *inputs):
        self.inputs = list(inputs)
        self.views = []

    def render(self, view):
        self.views.append(view)

    def read_input(self, _view):
        return self.inputs.pop(0)


class HealingGoblinUI:
    def __init__(self):
        self.inputs = 0

    def render(self, _view):
        return None

    def read_input(self, view):
        self.inputs += 1
        if self.inputs > 150:
            raise AssertionError("healing Goblin battle did not terminate")

        if view.interaction_phase.value == "actions":
            heal = next(
                option
                for option in view.action_options
                if option.intent == ActionIntent.HEAL
            )
            if heal.enabled:
                return ChooseAction(ActionIntent.HEAL)
            return ChooseAction(ActionIntent.ATTACK)

        move = next(move for move in view.move_options if move.enabled)
        return ChooseMove(move.selection_key)


def _damaged_player(character_type=Brawler, amount=20):
    player = PlayerState(character_type())
    player.health.take_damage(amount)
    return player


def _enemy():
    return EnemyState(Goblin())


def test_heal_uses_minimum_roll_plus_effective_constitution():
    actor = _damaged_player(amount=50)
    state = CombatState()
    rng = FixedRng(10)
    expected = 10 + actor.effective_stat("constitution")

    result = CombatResolver(rng=rng).resolve_heal(actor, combat_state=state)

    assert result.accepted is True
    assert result.healing == expected
    assert actor.health.current == actor.health.maximum - 50 + expected
    assert rng.calls == [(10, 16)]


def test_heal_uses_maximum_roll_and_caps_actual_restoration():
    actor = _damaged_player(amount=5)
    state = CombatState()
    rng = FixedRng(16)

    result = CombatResolver(rng=rng).resolve_heal(actor, combat_state=state)

    assert result.accepted is True
    assert result.healing == 5
    assert actor.health.current == actor.health.maximum


def test_heal_has_no_resource_super_or_critical_side_effects():
    actor = _damaged_player(amount=20)
    actor.super_resource.gain(10)
    state = CombatState()
    rng = FixedRng(10)
    mana_before = actor.mana_resource.current
    super_before = actor.super_resource.current

    result = CombatResolver(rng=rng).resolve_heal(actor, combat_state=state)

    assert result.resource_spent == 0
    assert result.critical is False
    assert actor.mana_resource.current == mana_before
    assert actor.super_resource.current == super_before
    assert rng.calls == [(10, 16)]


def test_heal_starts_three_action_cooldown_without_reducing_itself():
    actor = _damaged_player()
    state = CombatState()

    result = CombatResolver(rng=FixedRng(10)).resolve_heal(
        actor,
        combat_state=state,
    )

    assert result.accepted is True
    assert state.heal_cooldown_remaining(actor) == 3


def test_full_health_and_cooldown_heals_are_rejected_without_mutation():
    full_actor = PlayerState(Brawler())
    full_state = CombatState()
    full_rng = FixedRng()

    full_result = CombatResolver(rng=full_rng).resolve_heal(
        full_actor,
        combat_state=full_state,
    )

    assert full_result.accepted is False
    assert full_result.reason == "heal_at_full_health"
    assert full_rng.calls == []
    assert state_is_ready(full_state, full_actor)

    actor = _damaged_player()
    cooldown_state = CombatState()
    cooldown_state.start_heal_cooldown(actor)
    before = actor.health.current
    cooldown_rng = FixedRng()

    cooldown_result = CombatResolver(rng=cooldown_rng).resolve_heal(
        actor,
        combat_state=cooldown_state,
    )

    assert cooldown_result.accepted is False
    assert cooldown_result.reason == "heal_cooldown"
    assert actor.health.current == before
    assert cooldown_rng.calls == []
    assert cooldown_state.heal_cooldown_remaining(actor) == 3


def state_is_ready(state, actor):
    return state.heal_cooldown_remaining(actor) == 0


def test_heal_cooldown_decrements_only_for_later_accepted_actor_actions():
    actor = _damaged_player()
    enemy = _enemy()
    state = CombatState()
    state.start_heal_cooldown(actor)

    assert state.heal_cooldown_remaining(actor) == 3
    state.complete_accepted_action(actor, (enemy,))
    assert state.heal_cooldown_remaining(actor) == 2
    state.complete_accepted_action(actor, (enemy,))
    assert state.heal_cooldown_remaining(actor) == 1
    state.complete_accepted_action(actor, (enemy,))
    assert state.heal_cooldown_remaining(actor) == 0
    state.complete_accepted_action(actor, (enemy,))
    assert state.heal_cooldown_remaining(actor) == 0


def test_enemy_actions_do_not_reduce_player_heal_cooldown():
    actor = _damaged_player()
    enemy = _enemy()
    state = CombatState()
    state.start_heal_cooldown(actor)

    state.complete_accepted_action(enemy, (actor,))

    assert state.heal_cooldown_remaining(actor) == 3


def test_heal_cooldown_is_identity_safe_and_encounter_local():
    first = _damaged_player()
    second = _damaged_player()
    state = CombatState()
    state.start_heal_cooldown(first)

    assert state.heal_cooldown_remaining(first) == 3
    assert state.heal_cooldown_remaining(second) == 0
    assert CombatState().heal_cooldown_remaining(first) == 0


def test_presenter_reports_ready_full_health_and_cooldown_states():
    player = _damaged_player()
    enemy = _enemy()
    state = CombatState()
    presenter = BattlePresenter()

    ready = presenter.build(player=player, enemy=enemy, combat_state=state)
    heal = next(option for option in ready.action_options if option.intent == ActionIntent.HEAL)
    assert heal.enabled is True
    assert heal.label == "Heal"

    player.health.heal(player.health.maximum)
    full = presenter.build(player=player, enemy=enemy, combat_state=state)
    heal = next(option for option in full.action_options if option.intent == ActionIntent.HEAL)
    assert heal.enabled is False
    assert heal.label == "Heal - Full HP"
    assert heal.disabled_reason == ActionAvailabilityReason.FULL_HP

    player.health.take_damage(20)
    state.start_heal_cooldown(player)
    state.complete_accepted_action(player, (enemy,))
    cooldown = presenter.build(player=player, enemy=enemy, combat_state=state)
    heal = next(option for option in cooldown.action_options if option.intent == ActionIntent.HEAL)
    assert heal.enabled is False
    assert heal.label == "Heal - 2 actions"
    assert heal.disabled_reason == ActionAvailabilityReason.HEAL_COOLDOWN
    assert state.heal_cooldown_remaining(player) == 2


def test_presenter_queries_do_not_change_heal_cooldown():
    player = _damaged_player()
    enemy = _enemy()
    state = CombatState()
    state.start_heal_cooldown(player)
    presenter = BattlePresenter()

    first = presenter.build(player=player, enemy=enemy, combat_state=state)
    second = presenter.build(player=player, enemy=enemy, combat_state=state)

    assert first == second
    assert state.heal_cooldown_remaining(player) == 3


def test_battle_routes_accepted_heal_and_completes_once_without_self_decrement():
    player = _damaged_player()
    battle = Battle(
        player,
        _enemy(),
        ui=ScriptedUI(ChooseAction(ActionIntent.HEAL)),
        resolver=CombatResolver(rng=FixedRng(10)),
    )
    completions = []
    original = battle._complete_accepted_action

    def record_completion(*args, **kwargs):
        completions.append((args, kwargs))
        return original(*args, **kwargs)

    battle._complete_accepted_action = record_completion

    accepted = battle.player_action()

    assert accepted is True
    assert len(completions) == 1
    assert completions[0][1] == {"reduce_heal_cooldown": False}
    assert battle.combat_state.turn_count == 1
    assert battle.combat_state.heal_cooldown_remaining(player) == 3
    assert battle.presentation_session.entries[-1].event_type == BattleEventType.HEALING


def test_rejected_heal_does_not_complete_or_advance():
    player = _damaged_player()
    battle = Battle(
        player,
        _enemy(),
        ui=ScriptedUI(ChooseAction(ActionIntent.HEAL), ChooseAction(ActionIntent.DEFEND)),
        resolver=CombatResolver(rng=FixedRng()),
    )
    battle.combat_state.start_heal_cooldown(player)
    completions = []
    original = battle._complete_accepted_action

    def record_completion(*args, **kwargs):
        completions.append((args, kwargs))
        return original(*args, **kwargs)

    battle._complete_accepted_action = record_completion
    accepted = battle.player_action()

    assert accepted is True
    assert len(completions) == 1
    assert battle.combat_state.turn_count == 1
    assert battle.combat_state.heal_cooldown_remaining(player) == 2
    assert player.health.current == player.health.maximum - 20


def test_terminal_renders_heal_availability_and_actual_recovery_event():
    player = _damaged_player()
    enemy = _enemy()
    state = CombatState()
    view = BattlePresenter().build(player=player, enemy=enemy, combat_state=state)
    output = []
    ui = TerminalBattleUI(
        input_func=lambda _prompt: "",
        output_func=output.append,
        width_provider=lambda: 80,
        unicode_enabled=False,
        ansi_enabled=False,
        interactive=False,
    )

    ui.render(view)

    assert "[H] Heal" in "\n".join(output)

    output.clear()
    healed_view = BattlePresenter().build(
        player=player,
        enemy=enemy,
        combat_state=state,
        log_entries=(
            BattleLogEntry(
                event_type=BattleEventType.HEALING,
                actor_name=player.display_name,
                action_name="Heal",
                accepted=True,
                hit=True,
                amount=5,
            ),
        ),
    )
    ui.render(healed_view)

    rendered = "\n".join(output)
    assert "Brawler used Heal. It restored 5 health." in rendered


@pytest.mark.parametrize("character_type", (Brawler, BlackMage, RogueArcher, Monk))
def test_all_drifters_can_use_universal_heal(character_type):
    player = _damaged_player(character_type)
    battle = Battle(
        player,
        _enemy(),
        ui=ScriptedUI(ChooseAction(ActionIntent.HEAL)),
        resolver=CombatResolver(rng=FixedRng(10)),
    )
    before = player.health.current

    assert battle.player_action() is True
    assert player.health.current > before
    assert battle.combat_state.heal_cooldown_remaining(player) == 3


@pytest.mark.parametrize("character_type", (Brawler, BlackMage, RogueArcher, Monk))
def test_all_drifters_can_complete_goblin_battle_with_heal(monkeypatch, character_type):
    monkeypatch.setattr(battle_module.random, "randint", lambda _start, _end: 1)
    monkeypatch.setattr(battle_module.random, "choice", lambda moves: moves[0])
    player = PlayerState(character_type())
    battle = Battle(
        player,
        _enemy(),
        ui=HealingGoblinUI(),
        resolver=CombatResolver(rng=FixedRng(*([1] * 300))),
    )

    assert battle.run() == "player"
    assert battle.foe.health.current == 0

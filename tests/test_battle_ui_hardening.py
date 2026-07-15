import ast
import inspect

import pytest

import app.combat.battle as battle_module
from app.combat.battle import Battle
from app.combat.combat_state import CombatState
from app.combat.move import TargetType
from app.combat.resolver import CombatResolver
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.player.player_state import PlayerState
from app.presentation.battle_models import (
    ActionIntent,
    BattleEventType,
    InteractionPhase,
)
from app.presentation.battle_presenter import BattlePresenter
from app.ui.battle_ui import ChooseAction, ChooseMove


DRIFTER_TYPES = (Brawler, BlackMage, RogueArcher, Monk)


class AlwaysOneRng:
    @staticmethod
    def randint(_start, _end):
        return 1


class AggressiveScriptedUI:
    def __init__(self):
        self.views = []
        self.input_count = 0

    def render(self, view):
        self.views.append(view)

    def read_input(self, view):
        self.input_count += 1
        if self.input_count > 100:
            raise AssertionError("scripted Goblin encounter did not terminate")
        if view.interaction_phase == InteractionPhase.ACTIONS:
            return ChooseAction(ActionIntent.ATTACK)

        enabled_moves = [move for move in view.move_options if move.enabled]
        if not enabled_moves:
            raise AssertionError("no affordable regular move was offered")
        return ChooseMove(enabled_moves[-1].selection_key)


@pytest.mark.parametrize("character_type", DRIFTER_TYPES)
def test_every_drifter_move_is_presented_and_resolver_compatible(character_type):
    player = PlayerState(character_type())
    enemy = EnemyState(Goblin())
    combat_state = CombatState()
    presenter = BattlePresenter()

    regular_view = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.REGULAR_MOVES,
    )
    super_view = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.SUPER_MOVES,
    )
    presented_names = {
        move.selection_key
        for move in (*regular_view.move_options, *super_view.move_options)
    }

    assert presented_names == {move.name for move in player.combat_moves}

    for authored_move in player.combat_moves:
        actor = PlayerState(character_type())
        target = EnemyState(Goblin())
        actor.super_resource.gain(actor.super_resource.maximum)
        resolution_target = actor if authored_move.target == TargetType.SELF else target
        result = CombatResolver(rng=AlwaysOneRng()).resolve_move(
            actor,
            resolution_target,
            authored_move.name,
            combat_state=CombatState(),
        )

        assert result.accepted is True, (
            character_type.__name__,
            authored_move.name,
            result.reason,
        )


@pytest.mark.parametrize("character_type", DRIFTER_TYPES)
def test_every_drifter_completes_deterministic_goblin_vertical_slice(
    character_type,
    monkeypatch,
):
    monkeypatch.setattr(battle_module.random, "randint", lambda _start, _end: 1)
    monkeypatch.setattr(battle_module.random, "choice", lambda moves: moves[0])
    ui = AggressiveScriptedUI()
    battle = Battle(
        PlayerState(character_type()),
        EnemyState(Goblin()),
        ui=ui,
        resolver=CombatResolver(rng=AlwaysOneRng()),
    )

    winner = battle.run()

    assert winner == "player"
    assert battle.foe.health.current == 0
    assert battle.presentation_session.entries[-1].event_type == BattleEventType.VICTORY
    assert ui.views


def test_battle_source_has_no_direct_terminal_io_or_adapter_dependency():
    source = inspect.getsource(battle_module)
    tree = ast.parse(source)
    direct_calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "input" not in direct_calls
    assert "print" not in direct_calls
    assert "terminal_battle_ui" not in source


def test_presenter_observation_does_not_change_combat_resources():
    player = PlayerState(Brawler())
    enemy = EnemyState(Goblin())
    combat_state = CombatState()
    combat_state.activate_brace(player)
    presenter = BattlePresenter()
    before = (
        player.health.current,
        player.mana_resource.current,
        player.super_resource.current,
        enemy.health.current,
        combat_state.turn_count,
    )

    first = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.REGULAR_MOVES,
    )
    second = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.REGULAR_MOVES,
    )
    after = (
        player.health.current,
        player.mana_resource.current,
        player.super_resource.current,
        enemy.health.current,
        combat_state.turn_count,
    )

    assert first == second
    assert before == after
    assert vars(presenter) == {}
    assert any(
        move.selection_key == "Ironwake Dismemberment"
        and "Empowered +30%" in move.tags
        for move in first.move_options
    )

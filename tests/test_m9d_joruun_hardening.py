import pytest

import app.combat.battle as battle_module
from app.combat.battle import Battle
from app.combat.combat_state import CombatState
from app.combat.result import CombatOutcomeType
from app.combat.resolver import CombatResolver
from app.combat.status_state import StatusKind
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import Monk
from app.player.player_state import PlayerState
from app.presentation.battle_models import ActionIntent, InteractionPhase
from app.presentation.battle_session import BattlePresentationSession
from app.ui.battle_ui import ChooseAction, ChooseMove
from app.ui.terminal_battle_ui import TerminalBattleUI


class AlwaysOneRng:
    @staticmethod
    def randint(_start, _end):
        return 1


class RecordingPresentationSession(BattlePresentationSession):
    def __init__(self):
        super().__init__()
        self.history = []

    def record(self, entry):
        self.history.append(entry)
        super().record(entry)


class JoruunRouteUI:
    def __init__(self, setup_moves):
        self.setup_moves = list(setup_moves)
        self.rendered_views = []
        self.inputs = []

    def render(self, view):
        self.rendered_views.append(view)

    def read_input(self, view):
        if len(self.inputs) >= 100:
            raise AssertionError("Joruun vertical slice did not terminate")
        if view.interaction_phase == InteractionPhase.ACTIONS:
            battle_input = ChooseAction(ActionIntent.ATTACK)
        elif view.interaction_phase == InteractionPhase.REGULAR_MOVES:
            move_name = (
                self.setup_moves.pop(0)
                if self.setup_moves
                else "Bring the Horse to Water"
            )
            battle_input = ChooseMove(move_name)
        else:
            raise AssertionError(f"unexpected interaction phase: {view.interaction_phase}")
        self.inputs.append(battle_input)
        return battle_input


def _outcome_types(entries):
    return tuple(
        outcome.outcome_type
        for entry in entries
        for outcome in entry.outcomes
    )


@pytest.mark.parametrize(
    ("route", "expected", "forbidden"),
    (
        (
            ("Hydro Whip", "Lightning Palm"),
            (
                CombatOutcomeType.CONDUCTIVE_APPLIED,
                CombatOutcomeType.CONDUCTIVE_CONSUMED,
                CombatOutcomeType.STUN_APPLIED,
                CombatOutcomeType.STUN_TRIGGERED,
                CombatOutcomeType.STUN_EXPIRED,
            ),
            (CombatOutcomeType.TURBULENCE_CONSUMED, CombatOutcomeType.LIGHTNING_STORM_TRIGGERED),
        ),
        (
            ("Tempest Surge", "Lightning Palm"),
            (
                CombatOutcomeType.TURBULENCE_APPLIED,
                CombatOutcomeType.TURBULENCE_CONSUMED,
            ),
            (CombatOutcomeType.STUN_APPLIED, CombatOutcomeType.LIGHTNING_STORM_TRIGGERED),
        ),
        (
            ("Hydro Whip", "Tempest Surge", "Lightning Palm"),
            (
                CombatOutcomeType.CONDUCTIVE_APPLIED,
                CombatOutcomeType.TURBULENCE_APPLIED,
                CombatOutcomeType.LIGHTNING_STORM_TRIGGERED,
                CombatOutcomeType.CONDUCTIVE_CONSUMED,
                CombatOutcomeType.TURBULENCE_CONSUMED,
            ),
            (CombatOutcomeType.STUN_APPLIED,),
        ),
        (
            ("Tempest Surge", "Hydro Whip", "Lightning Palm"),
            (
                CombatOutcomeType.TURBULENCE_APPLIED,
                CombatOutcomeType.CONDUCTIVE_APPLIED,
                CombatOutcomeType.LIGHTNING_STORM_TRIGGERED,
                CombatOutcomeType.CONDUCTIVE_CONSUMED,
                CombatOutcomeType.TURBULENCE_CONSUMED,
            ),
            (CombatOutcomeType.STUN_APPLIED,),
        ),
    ),
)
def test_deterministic_joruun_goblin_routes(monkeypatch, route, expected, forbidden):
    monkeypatch.setattr(battle_module.random, "randint", lambda _start, _end: 1)
    monkeypatch.setattr(battle_module.random, "choice", lambda moves: moves[0])
    player = PlayerState(Monk())
    enemy = EnemyState(Goblin())
    ui = JoruunRouteUI(route)
    session = RecordingPresentationSession()
    battle = Battle(
        player,
        enemy,
        ui=ui,
        resolver=CombatResolver(rng=AlwaysOneRng()),
        presentation_session=session,
    )

    assert battle.run() == "player"
    assert not enemy.is_alive()
    outcomes = _outcome_types(session.history)
    position = 0
    for outcome_type in expected:
        position = outcomes.index(outcome_type, position) + 1
    assert all(outcome_type not in outcomes for outcome_type in forbidden)
    assert not battle.combat_state.conductive_active(player, enemy)
    assert not battle.combat_state.turbulence_active(player, enemy)
    assert not battle.combat_state.stun_active(enemy)


def test_lightning_storm_is_recorded_as_primary_action_not_a_new_move_slot(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda _start, _end: 1)
    monkeypatch.setattr(battle_module.random, "choice", lambda moves: moves[0])
    player = PlayerState(Monk())
    session = RecordingPresentationSession()
    battle = Battle(
        player,
        EnemyState(Goblin()),
        ui=JoruunRouteUI(("Hydro Whip", "Tempest Surge", "Lightning Palm")),
        resolver=CombatResolver(rng=AlwaysOneRng()),
        presentation_session=session,
    )

    battle.run()

    assert len(player.combat_moves) == 5
    assert "Lightning Storm" not in tuple(move.name for move in player.combat_moves)
    assert any(entry.action_name == "Lightning Storm" for entry in session.history)


def test_storm_statuses_coexist_with_burn_and_poison_without_changing_ticks():
    source = PlayerState(Monk())
    target = EnemyState(Goblin())
    state = CombatState()
    state.apply_burn(source, target)
    state.apply_poison(source, target)
    state.apply_conductive(source, target)
    state.apply_turbulence(source, target)

    outcomes = state.complete_accepted_action(target, (source,))

    assert tuple(outcome.outcome_type for outcome in outcomes) == (
        CombatOutcomeType.BURN_TICK,
        CombatOutcomeType.POISON_TICK,
    )
    assert state.conductive_active(source, target)
    assert state.turbulence_active(source, target)
    assert state.active_status_kinds(target) == (
        StatusKind.BURN,
        StatusKind.POISON,
        StatusKind.CONDUCTIVE,
        StatusKind.TURBULENCE,
    )


def test_defeated_source_clears_linked_storm_statuses_without_expiration_noise():
    source = PlayerState(Monk())
    target = EnemyState(Goblin())
    state = CombatState()
    state.apply_conductive(source, target)
    state.apply_turbulence(source, target)
    state.apply_stun(source, target)
    source.health.take_damage(source.health.current)

    assert state.complete_accepted_action(source, (target,)) == ()
    assert not state.conductive_active(source, target)
    assert not state.turbulence_active(source, target)
    assert not state.stun_active(target)


def test_new_encounter_has_no_storm_status_leakage():
    source = PlayerState(Monk())
    first_target = EnemyState(Goblin())
    first = CombatState()
    first.apply_conductive(source, first_target)
    first.apply_turbulence(source, first_target)
    first.apply_stun(source, first_target)

    second_target = EnemyState(Goblin())
    second = CombatState()

    assert second.active_status_kinds(second_target) == ()
    assert not second.conductive_active(source, second_target)
    assert not second.turbulence_active(source, second_target)
    assert not second.stun_active(second_target)


@pytest.mark.parametrize(
    ("setup_inputs", "expected_text"),
    (
        (("A", "4", "A", "2"), "discharged Conductive through Lightning Palm"),
        (("A", "3", "A", "2"), "discharged Turbulence through Lightning Palm"),
        (("A", "4", "A", "3", "A", "2"), "used Lightning Storm"),
        (("A", "3", "A", "4", "A", "2"), "used Lightning Storm"),
    ),
)
def test_terminal_adapter_goblin_routes(monkeypatch, setup_inputs, expected_text):
    monkeypatch.setattr(battle_module.random, "randint", lambda _start, _end: 1)
    monkeypatch.setattr(battle_module.random, "choice", lambda moves: moves[0])
    inputs = iter((*setup_inputs, *(("A", "1") * 20)))
    rendered = []
    ui = TerminalBattleUI(
        input_func=lambda _prompt: next(inputs),
        output_func=rendered.append,
        width_provider=lambda: 80,
        unicode_enabled=False,
        ansi_enabled=False,
        interactive=False,
    )
    battle = Battle(
        PlayerState(Monk()),
        EnemyState(Goblin()),
        ui=ui,
        resolver=CombatResolver(rng=AlwaysOneRng()),
    )

    assert battle.run() == "player"
    output = "\n".join(rendered)
    assert expected_text in output
    assert "is victorious over Goblin" in output

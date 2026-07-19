from dataclasses import FrozenInstanceError

import pytest

from app.combat.battle import Battle
from app.combat.result import MoveResult
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import Brawler, Monk, RogueArcher
from app.player.character_run_state import PreparedPayloadId
from app.player.inventory_action import InventoryActionResolver
from app.player.player_state import PlayerState
from app.presentation.battle_models import (
    ActionIntent,
    BattleEventType,
    BattleLogEntry,
    InputRejectionReason,
    InteractionPhase,
)
from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget, GoBack
from app.ui.terminal_battle_ui import TerminalBattleUI


class RecordingResolver:
    def __init__(self, *, accepted=True):
        self.accepted = accepted
        self.calls = []

    def resolve_move(self, actor, target, move_name, **kwargs):
        self.calls.append((actor, target, move_name, kwargs))
        return MoveResult(
            accepted=self.accepted,
            hit=self.accepted,
            move_name=move_name,
            resource_spent=0,
            damage=0,
            healing=0,
            statuses_applied=(),
            reason=None if self.accepted else "rejected",
        )

    def resolve_defend(self, actor, combat_state):
        return _accepted_result()


class RecordingRng:
    def __init__(self):
        self.calls = []

    def randint(self, start, end):
        self.calls.append(("randint", start, end))
        return start

    def choice(self, options):
        self.calls.append(("choice", tuple(options)))
        return tuple(options)[0]


class ScriptedUI:
    def __init__(self, *inputs, before_input=None):
        self.inputs = iter(inputs)
        self.before_input = before_input
        self.views = []

    def render(self, view):
        self.views.append(view)

    def read_input(self, view):
        if self.before_input is not None:
            self.before_input(view)
        return next(self.inputs)


def _accepted_result():
    return MoveResult(
        accepted=True,
        hit=True,
        move_name="test move",
        resource_spent=0,
        damage=0,
        healing=0,
        statuses_applied=(),
        reason=None,
    )


def _battle(character=None, *, enemies=None, resolver=None, ui=None, rng=None):
    player = PlayerState(character or Brawler())
    enemies = enemies or (EnemyState(Goblin()), EnemyState(Goblin()))
    battle = Battle(
        player,
        enemies,
        ui=ui or ScriptedUI(),
        resolver=resolver or RecordingResolver(),
        rng=rng or RecordingRng(),
    )
    return battle, player, tuple(enemies)


def test_choose_target_is_immutable_and_validated():
    choice = ChooseTarget("enemy_2")

    assert choice.target_id == "enemy_2"
    with pytest.raises(FrozenInstanceError):
        choice.target_id = "enemy_1"
    with pytest.raises(ValueError):
        ChooseTarget("")
    with pytest.raises(TypeError):
        ChooseTarget(2)


def test_multi_enemy_move_choice_waits_for_exact_target_without_clearing_log():
    resolver = RecordingResolver()
    ui = ScriptedUI(
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove("Crestgrave Reaping"),
        ChooseTarget("enemy_2"),
    )
    battle, player, enemies = _battle(resolver=resolver, ui=ui)
    previous = BattleLogEntry(
        BattleEventType.STATUS,
        actor_name=player.display_name,
    )
    battle.presentation_session.record(previous)

    assert battle.player_action() is True

    target_view = next(
        view for view in ui.views if view.interaction_phase == InteractionPhase.TARGETS
    )
    assert resolver.calls == [
        (
            player,
            enemies[1],
            "Crestgrave Reaping",
            {
                "combat_state": battle.combat_state,
                "character_run_state": player.character_run_state,
            },
        )
    ]
    assert previous in target_view.log_entries
    assert previous not in battle.presentation_session.entries


def test_one_living_enemy_is_auto_targeted_and_defeated_enemy_is_not_offered():
    first, second = EnemyState(Goblin()), EnemyState(Goblin())
    first.health.take_damage(first.health.maximum)
    resolver = RecordingResolver()
    ui = ScriptedUI(
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove("Crestgrave Reaping"),
    )
    battle, player, _ = _battle(
        enemies=(first, second),
        resolver=resolver,
        ui=ui,
    )

    assert battle.player_action() is True

    assert resolver.calls[0][0:3] == (player, second, "Crestgrave Reaping")
    assert all(view.interaction_phase != InteractionPhase.TARGETS for view in ui.views)


def test_self_targeted_move_resolves_without_target_selection():
    resolver = RecordingResolver()
    ui = ScriptedUI(
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove("Brace"),
    )
    battle, player, _ = _battle(resolver=resolver, ui=ui)

    assert battle.player_action() is True

    assert resolver.calls[0][0:3] == (player, player, "Brace")
    assert all(view.interaction_phase != InteractionPhase.TARGETS for view in ui.views)


@pytest.mark.parametrize(
    ("origin", "first_input", "move_name"),
    [
        (
            InteractionPhase.REGULAR_MOVES,
            ChooseAction(ActionIntent.ATTACK),
            "Crestgrave Reaping",
        ),
        (
            InteractionPhase.SUPER_MOVES,
            ChooseAction(ActionIntent.SUPER),
            "Third Gate Obsequy",
        ),
    ],
)
def test_back_from_targets_returns_to_exact_move_phase_without_resolving(
    origin,
    first_input,
    move_name,
):
    resolver = RecordingResolver()
    rng = RecordingRng()
    ui = ScriptedUI(
        first_input,
        ChooseMove(move_name),
        GoBack(),
        GoBack(),
        ChooseAction(ActionIntent.DEFEND),
    )
    battle, player, _ = _battle(resolver=resolver, ui=ui, rng=rng)
    if origin == InteractionPhase.SUPER_MOVES:
        player.super_resource.gain(player.super_resource.maximum)
    battle.presentation_session.record(BattleLogEntry(BattleEventType.STATUS))

    assert battle.player_action() is True

    phases = tuple(view.interaction_phase for view in ui.views)
    target_index = phases.index(InteractionPhase.TARGETS)
    assert phases[target_index + 1] == origin
    assert resolver.calls == []
    assert rng.calls == []
    assert battle._selected_move_key is None
    assert battle._originating_move_phase is None


def test_stale_defeated_target_is_rejected_without_dispatch_or_resource_mutation():
    resolver = RecordingResolver()
    rng = RecordingRng()
    second = EnemyState(Goblin())
    killed = False

    def defeat_second_after_target_view(view):
        nonlocal killed
        if view.interaction_phase == InteractionPhase.TARGETS and not killed:
            second.health.take_damage(second.health.maximum)
            killed = True

    ui = ScriptedUI(
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove("Infused Barb"),
        ChooseTarget("enemy_2"),
        ChooseTarget("enemy_1"),
        before_input=defeat_second_after_target_view,
    )
    battle, player, enemies = _battle(
        RogueArcher(),
        enemies=(EnemyState(Goblin()), second),
        resolver=resolver,
        ui=ui,
        rng=rng,
    )
    InventoryActionResolver().resolve(
        "prepare_fire_infusion",
        player.character_run_state,
    )
    mana_before = player.mana_resource.current
    super_before = player.super_resource.current
    turn_before = battle.combat_state.turn_count

    assert battle.player_action() is True

    assert resolver.calls[0][1] is enemies[0]
    assert len(resolver.calls) == 1
    assert rng.calls == []
    assert player.mana_resource.current == mana_before
    assert player.super_resource.current == super_before
    assert player.character_run_state.payload_prepared(
        PreparedPayloadId.INFUSED_BARB
    )
    assert battle.combat_state.turn_count == turn_before + 1
    assert any(
        entry.event_type == BattleEventType.INPUT_REJECTED
        and entry.rejection_reason == InputRejectionReason.TARGET_UNAVAILABLE
        for view in ui.views
        if view.interaction_phase == InteractionPhase.TARGETS
        for entry in view.log_entries
    )


def test_unknown_target_is_typed_rejection_and_never_retargets():
    resolver = RecordingResolver()
    ui = ScriptedUI(
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove("Crestgrave Reaping"),
        ChooseTarget("enemy_99"),
        GoBack(),
        GoBack(),
        ChooseAction(ActionIntent.DEFEND),
    )
    battle, _, _ = _battle(resolver=resolver, ui=ui)

    assert battle.player_action() is True

    assert resolver.calls == []
    rejection = next(
        entry
        for view in ui.views
        if view.interaction_phase == InteractionPhase.TARGETS
        for entry in view.log_entries
        if entry.event_type == BattleEventType.INPUT_REJECTED
    )
    assert rejection.rejection_reason == InputRejectionReason.TARGET_UNAVAILABLE


def test_move_that_becomes_unaffordable_is_revalidated_before_target_dispatch():
    resolver = RecordingResolver()
    spent = False

    def spend_mana_after_target_view(view):
        nonlocal spent
        if view.interaction_phase == InteractionPhase.TARGETS and not spent:
            battle.player_state.mana_resource.spend(
                battle.player_state.mana_resource.current
            )
            spent = True

    ui = ScriptedUI(
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove("Cinderlung Vesper"),
        ChooseTarget("enemy_2"),
        GoBack(),
        GoBack(),
        ChooseAction(ActionIntent.DEFEND),
        before_input=spend_mana_after_target_view,
    )
    battle, _, _ = _battle(resolver=resolver, ui=ui)

    assert battle.player_action() is True

    assert resolver.calls == []
    assert any(
        entry.event_type == BattleEventType.INPUT_REJECTED
        and entry.rejection_reason == InputRejectionReason.TARGET_UNAVAILABLE
        for view in ui.views
        for entry in view.log_entries
    )


def test_resolver_rejection_keeps_exact_target_selection_pending():
    resolver = RecordingResolver(accepted=False)
    ui = ScriptedUI(
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove("Crestgrave Reaping"),
        ChooseTarget("enemy_2"),
        GoBack(),
        GoBack(),
        ChooseAction(ActionIntent.DEFEND),
    )
    battle, _, enemies = _battle(resolver=resolver, ui=ui)

    assert battle.player_action() is True

    target_views = tuple(
        view for view in ui.views if view.interaction_phase == InteractionPhase.TARGETS
    )
    assert len(target_views) == 2
    assert resolver.calls[0][1] is enemies[1]
    assert target_views[-1].target_options == target_views[0].target_options
    assert any(
        entry.event_type == BattleEventType.ACTION_REJECTED
        for entry in target_views[-1].log_entries
    )


def test_target_sensitive_lightning_preview_is_exact_for_each_enemy():
    battle, player, enemies = _battle(Monk())
    battle.combat_state.apply_conductive(player, enemies[0])
    battle.combat_state.apply_turbulence(player, enemies[0])
    battle.interaction_phase = InteractionPhase.REGULAR_MOVES

    move_view = battle._build_view()
    palm = next(option for option in move_view.move_options if option.name == "Lightning Palm")
    assert palm.name == "Lightning Palm"
    assert "Conductive" not in palm.tags
    assert "Turbulence" not in palm.tags

    battle._selected_move_key = "Lightning Palm"
    battle._originating_move_phase = InteractionPhase.REGULAR_MOVES
    battle.interaction_phase = InteractionPhase.TARGETS
    target_view = battle._build_view()

    assert tuple(option.move_preview.name for option in target_view.target_options) == (
        "Lightning Storm",
        "Lightning Palm",
    )
    assert target_view.target_options[0].display_label == "Goblin 1"
    assert target_view.target_options[1].display_label == "Goblin 2"


def test_lifecycle_receives_all_enemies_and_logs_the_exact_selected_target():
    resolver = RecordingResolver()
    ui = ScriptedUI(
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove("Crestgrave Reaping"),
        ChooseTarget("enemy_2"),
    )
    battle, player, enemies = _battle(resolver=resolver, ui=ui)
    completion_calls = []
    lifecycle_logs = []

    def complete(actor, opposing, *, reduce_heal_cooldown=True):
        completion_calls.append((actor, opposing, reduce_heal_cooldown))
        return (object(),)

    battle.combat_state.complete_accepted_action = complete
    battle._record_lifecycle_outcomes = (
        lambda actor, target, outcomes: lifecycle_logs.append((actor, target, outcomes))
    )

    assert battle.player_action() is True

    assert completion_calls == [(player, enemies, True)]
    assert lifecycle_logs[0][0] is player
    assert lifecycle_logs[0][1] is enemies[1]


def test_terminal_target_input_uses_offered_number_or_unique_label_not_target_id():
    battle, _, _ = _battle()
    battle._selected_move_key = "Crestgrave Reaping"
    battle._originating_move_phase = InteractionPhase.REGULAR_MOVES
    battle.interaction_phase = InteractionPhase.TARGETS
    view = battle._build_view()
    lines = []
    terminal = TerminalBattleUI(
        output_func=lines.append,
        input_func=lambda _prompt: "2",
        unicode_enabled=False,
        ansi_enabled=False,
        interactive=False,
    )

    assert terminal.read_input(view) == ChooseTarget("enemy_2")
    assert terminal._translate_choice(view, "goblin 1") == ChooseTarget("enemy_1")
    assert terminal._translate_choice(view, "enemy_2") is None

    terminal.render(view)
    rendered = "\n".join(lines)
    assert "Choose a target:" in rendered
    assert "Goblin 1" in rendered
    assert "Goblin 2" in rendered
    assert "enemy_1" not in rendered
    assert "enemy_2" not in rendered

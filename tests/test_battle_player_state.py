import builtins
import contextlib
import io
import random
from types import SimpleNamespace
from app.combat.battle import Battle as DomainBattle
from app.combat.brace import BRACE_RULES
from app.combat.combat_state import CombatState
from app.combat.move import (
    DamageType,
    Move,
    MoveKind,
    ResourceType,
    ScalingAttribute,
    TargetType,
)
from app.combat.resolver import CombatResolver
from app.combat.result import CombatOutcomeType, MoveResult
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import Brawler, Monk, RogueArcher
from app.player.character_run_state import PreparedPayloadId, RunItemId
from app.player.inventory_action import InventoryActionResolver
from app.player.player_state import PlayerState
from app.presentation.battle_models import (
    ActionIntent,
    BattleEventType,
    BattleLogEntry,
    InputRejectionReason,
    InteractionPhase,
)
from app.ui.battle_ui import ChooseAction, ChooseInventoryAction, ChooseMove, GoBack
from app.ui.terminal_battle_ui import TerminalBattleUI
from app.world.character_profiles.roster import get_profile_by_choice


@contextlib.contextmanager
def patched_battle(inputs=(), randint=None):
    original_input = builtins.input
    original_randint = random.randint
    original_choice = random.choice
    answers = iter(inputs)

    def fake_input(prompt=""):
        print(prompt, end="")
        return next(answers)

    builtins.input = fake_input
    random.choice = lambda items: items[0]

    if randint is not None:
        random.randint = randint

    try:
        yield
    finally:
        builtins.input = original_input
        random.randint = original_randint
        random.choice = original_choice


def accepted_result():
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


def rejected_result():
    return MoveResult(
        accepted=False,
        hit=False,
        move_name="test move",
        resource_spent=0,
        damage=0,
        healing=0,
        statuses_applied=(),
        reason="rejected",
    )


def result_with(**overrides):
    values = {
        "accepted": True,
        "hit": True,
        "move_name": "test move",
        "resource_spent": 0,
        "damage": 0,
        "healing": 0,
        "statuses_applied": (),
        "reason": None,
    }
    values.update(overrides)
    return MoveResult(**values)


class RecordingResolver:
    def __init__(self, *results, defend_results=()):
        self._results = list(results)
        self._defend_results = list(defend_results)
        self.calls = []
        self.defend_calls = []

    def resolve_move(self, actor, target, move_name, *, combat_state=None):
        self.calls.append({
            "actor": actor,
            "target": target,
            "move_name": move_name,
            "combat_state": combat_state,
        })
        return self._results.pop(0) if self._results else accepted_result()

    def resolve_defend(self, actor, combat_state):
        self.defend_calls.append({
            "actor": actor,
            "combat_state": combat_state,
        })
        return self._defend_results.pop(0) if self._defend_results else accepted_result()


class ScriptedBattleUI:
    def __init__(self, *inputs):
        self.inputs = list(inputs)
        self.rendered_views = []
        self.input_views = []

    def render(self, view):
        self.rendered_views.append(view)

    def read_input(self, view):
        self.input_views.append(view)
        return self.inputs.pop(0)


class Battle(DomainBattle):
    def __init__(self, player_state, foe, resolver=None, ui=None, **kwargs):
        super().__init__(
            player_state,
            foe,
            ui=ui or TerminalBattleUI(),
            resolver=resolver,
            **kwargs,
        )


class LegacyMovesFailingEnemyState(EnemyState):
    @property
    def moves(self):
        raise AssertionError("enemy_action must not read legacy foe.moves")


class ManaBearingEnemyState(EnemyState):
    def __init__(self, enemy_definition, tier=0):
        super().__init__(enemy_definition, tier=tier)
        self.mana_resource.set_maximum(5)
        self.mana_resource.restore(3)


def test_inventory_navigation_does_not_mutate_or_advance():
    player_state = PlayerState(RogueArcher())
    before = player_state.character_run_state.snapshot()
    ui = ScriptedBattleUI(
        ChooseAction(ActionIntent.ITEMS),
        GoBack(),
        ChooseAction(ActionIntent.DEFEND),
    )
    battle = Battle(
        player_state,
        EnemyState(Goblin()),
        ui=ui,
        resolver=RecordingResolver(defend_results=(accepted_result(),)),
    )

    assert battle.player_action() is True

    assert tuple(view.interaction_phase for view in ui.input_views) == (
        InteractionPhase.ACTIONS,
        InteractionPhase.INVENTORY,
        InteractionPhase.ACTIONS,
    )
    assert battle.combat_state.turn_count == 1
    assert player_state.character_run_state.snapshot() == before


def test_accepted_preparation_consumes_compounds_and_completes_exactly_once():
    player_state = PlayerState(RogueArcher())
    mana_before = player_state.mana_resource.current
    super_before = player_state.super_resource.current
    ui = ScriptedBattleUI(
        ChooseAction(ActionIntent.ITEMS),
        ChooseInventoryAction("prepare_cinderwrit"),
    )
    battle = Battle(player_state, EnemyState(Goblin()), ui=ui)

    assert battle.player_action() is True

    assert battle.combat_state.turn_count == 1
    assert player_state.mana_resource.current == mana_before
    assert player_state.super_resource.current == super_before
    assert player_state.character_run_state.item_quantity(RunItemId.EMBER_SHARD) == 0
    assert player_state.character_run_state.item_quantity(RunItemId.DEEP_COAL) == 0
    assert player_state.character_run_state.payload_prepared(
        PreparedPayloadId.CINDERWRIT
    ) is True
    entry = battle.presentation_session.entries[0]
    assert entry.event_type == BattleEventType.INVENTORY
    assert tuple(outcome.outcome_type for outcome in entry.outcomes) == (
        CombatOutcomeType.COMPOUNDS_CONSUMED,
        CombatOutcomeType.CINDERWRIT_PREPARED,
    )


def test_prepared_payload_persists_through_actions_enemy_response_and_encounters():
    player_state = PlayerState(RogueArcher())
    resolver = RecordingResolver(
        accepted_result(),
        defend_results=(accepted_result(),),
    )
    battle = Battle(
        player_state,
        EnemyState(Goblin()),
        ui=ScriptedBattleUI(
            ChooseAction(ActionIntent.ITEMS),
            ChooseInventoryAction("prepare_cinderwrit"),
        ),
        resolver=resolver,
    )
    battle.player_action()

    battle.ui = ScriptedBattleUI(ChooseAction(ActionIntent.DEFEND))
    battle.player_action()
    battle.enemy_action()
    battle.resolver = CombatResolver(
        rng=SimpleNamespace(randint=lambda start, _end: start)
    )
    player_state.health.take_damage(10)
    battle.ui = ScriptedBattleUI(ChooseAction(ActionIntent.HEAL))
    battle.player_action()
    battle.ui = ScriptedBattleUI(
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove("Mournpoint Verdict"),
    )
    battle.player_action()
    next_battle = Battle(
        player_state,
        EnemyState(Goblin()),
        ui=ScriptedBattleUI(),
    )

    assert player_state.character_run_state.payload_prepared(
        PreparedPayloadId.CINDERWRIT
    ) is True
    assert next_battle.player_state.character_run_state is player_state.character_run_state


class LethalEnemyResolver(RecordingResolver):
    def resolve_move(self, actor, target, move_name, *, combat_state=None):
        self.calls.append({
            "actor": actor,
            "target": target,
            "move_name": move_name,
            "combat_state": combat_state,
        })
        damage = target.health.current
        target.health.take_damage(damage)
        return result_with(move_name=move_name, damage=damage)


class LethalPlayerCompletionState(CombatState):
    def complete_accepted_action(self, actor, opposing_combatants, **kwargs):
        turn = super().complete_accepted_action(actor, opposing_combatants, **kwargs)
        actor.health.take_damage(actor.health.current)
        return turn


def test_accepted_preparation_allows_exactly_one_enemy_response():
    player_state = PlayerState(RogueArcher())
    resolver = LethalEnemyResolver()
    battle = Battle(
        player_state,
        EnemyState(Goblin()),
        ui=ScriptedBattleUI(
            ChooseAction(ActionIntent.ITEMS),
            ChooseInventoryAction("prepare_cinderwrit"),
        ),
        resolver=resolver,
    )

    with patched_battle(randint=lambda _start, _end: 1):
        winner = battle.run()

    assert winner == "enemy"
    assert len(resolver.calls) == 1
    assert battle.combat_state.turn_count == 2


def test_lethal_player_lifecycle_after_preparation_prevents_enemy_response():
    player_state = PlayerState(RogueArcher())
    resolver = RecordingResolver()
    battle = Battle(
        player_state,
        EnemyState(Goblin()),
        ui=ScriptedBattleUI(
            ChooseAction(ActionIntent.ITEMS),
            ChooseInventoryAction("prepare_cinderwrit"),
        ),
        resolver=resolver,
    )
    battle.combat_state = LethalPlayerCompletionState()

    with patched_battle(randint=lambda _start, _end: 1):
        winner = battle.run()

    assert winner == "enemy"
    assert resolver.calls == []
    assert battle.combat_state.turn_count == 1


def test_battle_accepts_player_state_and_uses_wrapped_character():
    character = Brawler()
    player_state = PlayerState(character)
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)

    assert battle.player_state is player_state
    assert battle.player is character
    assert battle.foe is enemy_state
    assert battle.player.name == character.name
    assert battle.player.moves is character.moves
    assert battle.player_state.effective_stat("strength") == character.strength + 3
    assert battle.player_state.effective_stat("constitution") == character.constitution + 1
    assert battle.combat_state.turn_count == 0
    assert not hasattr(battle, "foe_health")
    assert not hasattr(battle, "foe_max_hp")


def test_battle_creates_combat_resolver_by_default():
    battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))

    assert isinstance(battle.resolver, CombatResolver)
    assert isinstance(battle.inventory_action_resolver, InventoryActionResolver)


def test_battle_accepts_injected_resolver():
    resolver = object()
    battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()), resolver=resolver)

    assert battle.resolver is resolver


def test_battle_accepts_injected_semantic_ui():
    ui = ScriptedBattleUI(
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove("Crestgrave Reaping"),
    )
    resolver = RecordingResolver(accepted_result())
    battle = Battle(
        PlayerState(Brawler()),
        EnemyState(Goblin()),
        resolver=resolver,
        ui=ui,
    )

    accepted = battle.player_action()

    assert accepted is True
    assert tuple(view.interaction_phase for view in ui.input_views) == (
        InteractionPhase.ACTIONS,
        InteractionPhase.REGULAR_MOVES,
    )
    assert resolver.calls[0]["move_name"] == "Crestgrave Reaping"


def test_accepted_player_action_replaces_previous_displayed_turn():
    ui = ScriptedBattleUI(
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove("Crestgrave Reaping"),
    )
    resolver = RecordingResolver(accepted_result())
    battle = Battle(
        PlayerState(Brawler()),
        EnemyState(Goblin()),
        resolver=resolver,
        ui=ui,
    )
    battle.presentation_session.record(
        BattleLogEntry(
            event_type=BattleEventType.DAMAGE,
            actor_name="old",
            action_name="old turn",
        )
    )

    assert battle.player_action() is True
    assert tuple(entry.action_name for entry in battle.presentation_session.entries) == (
        "test move",
    )


def test_navigation_and_rejected_action_preserve_displayed_turn():
    ui = ScriptedBattleUI(
        ChooseAction(ActionIntent.ATTACK),
        GoBack(),
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove("Crestgrave Reaping"),
        ChooseMove("Crestgrave Reaping"),
    )
    resolver = RecordingResolver(rejected_result(), accepted_result())
    battle = Battle(
        PlayerState(Brawler()),
        EnemyState(Goblin()),
        resolver=resolver,
        ui=ui,
    )
    battle.presentation_session.record(
        BattleLogEntry(
            event_type=BattleEventType.DAMAGE,
            actor_name="old",
            action_name="old turn",
        )
    )

    assert battle.player_action() is True
    assert any(
        entry.action_name == "old turn"
        for entry in ui.input_views[4].log_entries
    )
    assert any(
        entry.reason == "rejected"
        for entry in ui.input_views[4].log_entries
    )
    names = tuple(entry.action_name for entry in battle.presentation_session.entries)
    assert "old turn" not in names
    assert names[-1] == "test move"


def test_accepted_miss_starts_a_new_displayed_turn():
    ui = ScriptedBattleUI(
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove("Crestgrave Reaping"),
    )
    resolver = RecordingResolver(result_with(hit=False))
    battle = Battle(
        PlayerState(Brawler()),
        EnemyState(Goblin()),
        resolver=resolver,
        ui=ui,
    )
    battle.presentation_session.record(
        BattleLogEntry(
            event_type=BattleEventType.DAMAGE,
            actor_name="old",
            action_name="old turn",
        )
    )

    assert battle.player_action() is True
    assert tuple(entry.action_name for entry in battle.presentation_session.entries) == (
        "test move",
    )


def test_unoffered_semantic_action_never_reaches_resolver_or_advances():
    ui = ScriptedBattleUI(
        ChooseAction(ActionIntent.ITEMS),
        ChooseAction(ActionIntent.DEFEND),
    )
    resolver = RecordingResolver(defend_results=(accepted_result(),))
    battle = Battle(
        PlayerState(Brawler()),
        EnemyState(Goblin()),
        resolver=resolver,
        ui=ui,
    )

    assert battle.player_action() is True

    assert resolver.calls == []
    assert len(resolver.defend_calls) == 1
    assert battle.combat_state.turn_count == 1
    assert any(
        entry.event_type == BattleEventType.INPUT_REJECTED
        and entry.rejection_reason == InputRejectionReason.ACTION_UNAVAILABLE
        for entry in ui.input_views[1].log_entries
    )


def test_go_back_changes_phase_without_resolver_or_lifecycle_completion():
    ui = ScriptedBattleUI(
        ChooseAction(ActionIntent.ATTACK),
        GoBack(),
        ChooseAction(ActionIntent.DEFEND),
    )
    resolver = RecordingResolver(defend_results=(accepted_result(),))
    battle = Battle(
        PlayerState(Brawler()),
        EnemyState(Goblin()),
        resolver=resolver,
        ui=ui,
    )

    assert battle.player_action() is True

    assert tuple(view.interaction_phase for view in ui.input_views) == (
        InteractionPhase.ACTIONS,
        InteractionPhase.REGULAR_MOVES,
        InteractionPhase.ACTIONS,
    )
    assert resolver.calls == []
    assert battle.combat_state.turn_count == 1


def test_super_opens_from_regular_move_phase_without_advancing():
    player_state = PlayerState(Brawler())
    player_state.super_resource.gain(100)
    super_move = player_state.combat_moves[-1]
    ui = ScriptedBattleUI(
        ChooseAction(ActionIntent.ATTACK),
        ChooseAction(ActionIntent.SUPER),
        ChooseMove(super_move.name),
    )
    resolver = RecordingResolver(accepted_result())
    battle = Battle(
        player_state,
        EnemyState(Goblin()),
        resolver=resolver,
        ui=ui,
    )

    assert battle.player_action() is True

    assert tuple(view.interaction_phase for view in ui.input_views) == (
        InteractionPhase.ACTIONS,
        InteractionPhase.REGULAR_MOVES,
        InteractionPhase.SUPER_MOVES,
    )
    assert resolver.calls[0]["move_name"] == super_move.name
    assert battle.combat_state.turn_count == 1


def test_resolver_rejection_retains_move_phase_until_accepted():
    ui = ScriptedBattleUI(
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove("Crestgrave Reaping"),
        ChooseMove("Crestgrave Reaping"),
    )
    resolver = RecordingResolver(rejected_result(), accepted_result())
    battle = Battle(
        PlayerState(Brawler()),
        EnemyState(Goblin()),
        resolver=resolver,
        ui=ui,
    )

    assert battle.player_action() is True

    assert tuple(view.interaction_phase for view in ui.input_views) == (
        InteractionPhase.ACTIONS,
        InteractionPhase.REGULAR_MOVES,
        InteractionPhase.REGULAR_MOVES,
    )
    assert len(resolver.calls) == 2
    assert battle.combat_state.turn_count == 1


def test_structured_move_helpers_read_player_and_enemy_combat_moves():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)

    assert battle._player_moves() is player_state.combat_moves
    assert battle._enemy_moves() is enemy_state.combat_moves


def test_complete_accepted_action_advances_when_result_is_accepted():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)
    battle.combat_state.activate_defend(enemy_state)

    result = battle._complete_accepted_action(
        player_state,
        opposing_combatants=(enemy_state,),
        result=accepted_result(),
    )

    assert result == 1
    assert battle.combat_state.turn_count == 1
    assert not battle.combat_state.is_defending(enemy_state)


def test_complete_accepted_action_does_nothing_when_result_is_rejected():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)
    battle.combat_state.activate_defend(enemy_state)

    result = battle._complete_accepted_action(
        player_state,
        opposing_combatants=(enemy_state,),
        result=rejected_result(),
    )

    assert result is None
    assert battle.combat_state.turn_count == 0
    assert battle.combat_state.is_defending(enemy_state)


def test_move_results_become_structured_semantic_events():
    battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))

    battle._record_move_result(
        result_with(move_name="Cut", damage=7),
        actor=battle.player_state,
        target=battle.foe,
    )
    battle._record_move_result(
        result_with(move_name="Smash", damage=16, critical=True),
        actor=battle.player_state,
        target=battle.foe,
    )
    battle._record_move_result(
        result_with(move_name="Recover", healing=3),
        actor=battle.player_state,
        target=battle.player_state,
    )
    battle._record_move_result(
        result_with(move_name="Whiff", hit=False),
        actor=battle.foe,
        target=battle.player_state,
    )
    battle._record_move_result(
        rejected_result(),
        actor=battle.player_state,
        target=battle.foe,
    )
    battle._record_move_result(
        result_with(
            move_name="Spark",
            resource_spent=4,
            statuses_applied=("burn", "shock"),
        ),
        actor=battle.player_state,
        target=battle.foe,
    )
    battle._record_move_result(
        result_with(move_name="Defend", hit=False),
        actor=battle.player_state,
        event_type=BattleEventType.DEFEND,
    )

    entries = battle.presentation_session.entries
    assert tuple(entry.event_type for entry in entries) == (
        BattleEventType.DAMAGE,
        BattleEventType.DAMAGE,
        BattleEventType.HEALING,
        BattleEventType.MISS,
        BattleEventType.ACTION_REJECTED,
        BattleEventType.UTILITY,
        BattleEventType.DEFEND,
    )
    assert entries[0].amount == 7 and entries[0].critical is False
    assert entries[1].amount == 16 and entries[1].critical is True
    assert entries[4].reason == "rejected"
    assert entries[5].resource_spent == 4
    assert entries[5].statuses_applied == ("burn", "shock")


def test_player_main_menu_shows_structured_actions_without_legacy_recover_or_labels():
    battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))
    output = io.StringIO()

    with patched_battle(inputs=["defend", "attack", "1"]), contextlib.redirect_stdout(output):
        battle.player_action()

    text = output.getvalue()
    assert "[A] Attack" in text
    assert "[D] Defend" in text
    assert "[H] Heal - Full HP [Unavailable]" in text
    assert "[I] Items [Unavailable]" in text
    assert "[E] Escape [Unavailable]" in text
    assert "[S] Super" in text
    assert "SUPER [" in text
    assert "0/100" in text
    assert "Recover (restore health)" not in text
    assert "steady attack" not in text
    assert "risky heavy attack" not in text


def test_attack_submenu_displays_non_super_structured_moves_with_resources_and_descriptions():
    player_state = PlayerState(Brawler())
    battle = Battle(player_state, EnemyState(Goblin()))
    output = io.StringIO()

    with patched_battle(inputs=["attack", "1"]), contextlib.redirect_stdout(output):
        battle.player_action()

    text = output.getvalue()
    non_super_moves = [
        move
        for move in player_state.combat_moves
        if move.resource_type.value != "super"
    ]
    super_moves = [
        move
        for move in player_state.combat_moves
        if move.resource_type.value == "super"
    ]

    for index, move in enumerate(non_super_moves, start=1):
        assert f"{index}. {move.name}" in text
        if move.mechanic == "brace":
            assert (
                f"reducing physical damage by {BRACE_RULES.incoming_reduction_percent}%"
                in text
            )
            assert (
                f"empower your next Heavy attack by "
                f"{BRACE_RULES.follow_up_damage_bonus_percent}%"
                in text
            )
        elif move.presentation is not None and move.presentation.static_summary is not None:
            assert move.presentation.static_summary in text
        else:
            assert move.description in text

    assert "0. Back" in text
    assert all(move.name not in text for move in super_moves)


def test_super_submenu_displays_super_move_separately_and_routes_to_resolver():
    player_state = PlayerState(Brawler())
    player_state.super_resource.gain(100)
    resolver = RecordingResolver(rejected_result(), accepted_result())
    battle = Battle(player_state, EnemyState(Goblin()), resolver=resolver)
    output = io.StringIO()

    with patched_battle(inputs=["super", "1", "0", "attack", "1"]), contextlib.redirect_stdout(output):
        battle.player_action()

    text = output.getvalue()
    super_move = [
        move
        for move in player_state.combat_moves
        if move.resource_type.value == "super"
    ][0]

    assert "Choose a Super:" in text
    assert f"1. {super_move.name}" in text
    assert "[Super | 100 Super]" in text
    assert "A forbidden gate manifests" in text
    assert "Sunder-Spire" in text
    assert "Brawler used test move, but it failed: rejected." in text
    assert battle.combat_state.turn_count == 1
    assert resolver.calls[0] == {
        "actor": player_state,
        "target": battle.foe,
        "move_name": super_move.name,
        "combat_state": battle.combat_state,
    }


def test_items_are_unavailable_and_return_to_main_menu_without_advancing_until_accepted_action():
    battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))
    output = io.StringIO()

    with patched_battle(inputs=["items", "attack", "1"]), contextlib.redirect_stdout(output):
        battle.player_action()

    text = output.getvalue()
    assert "Items is not available." in text
    assert text.count("Actions") == 1
    assert battle.combat_state.turn_count == 1


def test_player_defend_routes_through_resolver_and_completes_accepted_action():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    resolver = RecordingResolver(defend_results=(accepted_result(),))
    battle = Battle(player_state, enemy_state, resolver=resolver)

    with patched_battle(inputs=["defend"]), contextlib.redirect_stdout(io.StringIO()):
        accepted = battle.player_action()

    assert accepted is True
    assert resolver.defend_calls == [{
        "actor": player_state,
        "combat_state": battle.combat_state,
    }]
    assert battle.combat_state.turn_count == 1


def test_player_defend_activates_actor_and_clears_opposing_defend_with_real_resolver():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)
    battle.combat_state.activate_defend(enemy_state)

    with patched_battle(inputs=["defend"]), contextlib.redirect_stdout(io.StringIO()):
        accepted = battle.player_action()

    assert accepted is True
    assert battle.combat_state.is_defending(player_state)
    assert not battle.combat_state.is_defending(enemy_state)
    assert battle.combat_state.turn_count == 1


def test_rejected_player_defend_reprompts_without_completion_or_turn_advance():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    resolver = RecordingResolver(accepted_result(), defend_results=(rejected_result(),))
    battle = Battle(player_state, enemy_state, resolver=resolver)
    completion_calls = []
    original_completion = battle._complete_accepted_action

    def record_completion(*args, **kwargs):
        completion_calls.append((args, kwargs))
        return original_completion(*args, **kwargs)

    battle._complete_accepted_action = record_completion

    with patched_battle(inputs=["defend", "attack", "1"]), contextlib.redirect_stdout(io.StringIO()):
        battle.player_action()

    assert len(resolver.defend_calls) == 1
    assert len(resolver.calls) == 1
    assert len(completion_calls) == 1
    assert battle.combat_state.turn_count == 1


def test_rejected_player_move_preserves_lifecycle_through_back_navigation():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    resolver = RecordingResolver(rejected_result())
    inputs = [
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove(player_state.combat_moves[0].name),
        GoBack(),
        ChooseAction(ActionIntent.DEFEND),
    ]

    class LifecycleInspectingUI(ScriptedBattleUI):
        def read_input(self, view):
            if len(self.input_views) in (2, 3):
                assert battle.combat_state.turn_count == 0
                assert battle.combat_state.is_defending(enemy_state)
            return super().read_input(view)

    ui = LifecycleInspectingUI(*inputs)
    battle = Battle(player_state, enemy_state, resolver=resolver, ui=ui)
    battle.combat_state.activate_defend(enemy_state)

    accepted = battle.player_action()

    assert accepted is True
    assert battle.combat_state.turn_count == 1
    assert not battle.combat_state.is_defending(enemy_state)


def test_defend_is_not_a_structured_combat_move():
    player_state = PlayerState(Brawler())

    assert "Defend" not in [move.name for move in player_state.combat_moves]


def test_player_menu_display_does_not_depend_on_legacy_character_moves():
    player_state = PlayerState(Brawler())
    player_state.character.moves = {1: "legacy only"}
    battle = Battle(player_state, EnemyState(Goblin()))
    output = io.StringIO()

    with patched_battle(inputs=["attack", "1"]), contextlib.redirect_stdout(output):
        battle.player_action()

    text = output.getvalue()
    assert "legacy only" not in text
    assert player_state.combat_moves[0].name in text


def test_attack_and_super_submenus_support_back_and_reprompt_invalid_input():
    player_state = PlayerState(Brawler())
    player_state.super_resource.gain(100)
    battle = Battle(player_state, EnemyState(Goblin()))
    output = io.StringIO()

    with patched_battle(inputs=["attack", "bad", "0", "super", "bad", "0", "attack", "1"]), contextlib.redirect_stdout(output):
        battle.player_action()

    text = output.getvalue()
    assert text.count("Choose a move:") == 2
    assert text.count("Choose a Super:") == 1
    assert text.count("That is not a valid move. Please try again.") == 2
    assert battle.combat_state.turn_count == 1


def test_player_target_helper_uses_move_target_type_and_rejects_unknown_targets():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)

    assert battle._player_target_for_move(SimpleNamespace(target=TargetType.ENEMY)) is enemy_state
    assert battle._player_target_for_move(SimpleNamespace(target=TargetType.SELF)) is player_state
    try:
        battle._player_target_for_move(SimpleNamespace(target="unsupported"))
    except ValueError as error:
        assert str(error) == "Unsupported player move target: 'unsupported'"
    else:
        raise AssertionError("Expected ValueError")


def test_enemy_target_helper_uses_move_target_type_and_rejects_unknown_targets():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)

    assert battle._enemy_target_for_move(SimpleNamespace(target=TargetType.ENEMY)) is player_state
    assert battle._enemy_target_for_move(SimpleNamespace(target=TargetType.SELF)) is enemy_state
    try:
        battle._enemy_target_for_move(SimpleNamespace(target="unsupported"))
    except ValueError as error:
        assert str(error) == "Unsupported enemy move target: 'unsupported'"
    else:
        raise AssertionError("Expected ValueError")


def test_structured_attack_menu_routes_selected_move_through_resolver():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    resolver = RecordingResolver(accepted_result())
    battle = Battle(player_state, enemy_state, resolver=resolver)

    with patched_battle(inputs=["attack", "1"]), contextlib.redirect_stdout(io.StringIO()):
        battle.player_action()

    assert resolver.calls == [{
        "actor": player_state,
        "target": enemy_state,
        "move_name": player_state.combat_moves[0].name,
        "combat_state": battle.combat_state,
    }]


def test_legacy_battle_combat_helpers_are_removed():
    assert not hasattr(Battle, "attack")
    assert not hasattr(Battle, "heal_player")
    assert not hasattr(Battle, "misses")


def test_self_targeting_player_move_routes_player_state_to_resolver():
    player_state = PlayerState(Brawler())
    self_move = Move(
        name="test self move",
        kind=MoveKind.UTILITY,
        resource_type=ResourceType.NONE,
        resource_cost=0,
        power=0,
        scales_with=(ScalingAttribute.NONE,),
        accuracy=100,
        target=TargetType.SELF,
        damage_type=DamageType.NONE,
        mechanic=None,
        description="A test self-targeting move.",
    )
    player_state.character.combat_moves = [self_move]
    resolver = RecordingResolver(accepted_result())
    battle = Battle(player_state, EnemyState(Goblin()), resolver=resolver)

    with patched_battle(inputs=["attack", "1"]), contextlib.redirect_stdout(io.StringIO()):
        battle.player_action()

    assert resolver.calls == [{
        "actor": player_state,
        "target": player_state,
        "move_name": self_move.name,
        "combat_state": battle.combat_state,
    }]


def test_rejected_player_resolver_result_reprompts_without_completion_until_accepted_action():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    resolver = RecordingResolver(rejected_result(), accepted_result())
    battle = Battle(player_state, enemy_state, resolver=resolver)
    completion_calls = []

    original_completion = battle._complete_accepted_action

    def record_completion(*args, **kwargs):
        completion_calls.append((args, kwargs))
        return original_completion(*args, **kwargs)

    battle._complete_accepted_action = record_completion

    with patched_battle(inputs=["attack", "1", "1"]), contextlib.redirect_stdout(io.StringIO()):
        battle.player_action()

    assert len(resolver.calls) == 2
    assert len(completion_calls) == 1
    assert battle.combat_state.turn_count == 1


def test_battles_do_not_share_combat_state():
    first_battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))
    second_battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))

    first_battle.combat_state.advance_turn()
    first_battle.combat_state.statuses["burn"] = 2

    assert first_battle.combat_state is not second_battle.combat_state
    assert first_battle.combat_state.turn_count == 1
    assert second_battle.combat_state.turn_count == 0
    assert second_battle.combat_state.statuses == {}


def test_battle_view_contains_resources_and_temporary_state_when_relevant():
    player_state = PlayerState(Brawler())
    enemy_state = ManaBearingEnemyState(Goblin())
    battle = Battle(player_state, enemy_state)
    player_state.mana_resource.spend(2)
    player_state.super_resource.gain(10)
    enemy_state.super_resource.gain(20)
    battle.combat_state.activate_defend(player_state)
    battle.combat_state.activate_defend(enemy_state)
    view = battle._build_view()

    assert (view.player.hp_current, view.player.hp_maximum) == (116, 116)
    assert (view.player.mana_current, view.player.mana_maximum) == (44, 46)
    assert (view.player.super_current, view.player.super_maximum) == (10, 100)
    assert view.player.temporary_labels == ("Defending",)
    assert (view.enemy.hp_current, view.enemy.hp_maximum) == (60, 60)
    assert (view.enemy.mana_current, view.enemy.mana_maximum) == (3, 5)
    assert (view.enemy.super_current, view.enemy.super_maximum) == (20, 100)
    assert view.enemy.temporary_labels == ("Defending",)


def test_battle_view_omits_enemy_mana_and_super_when_not_relevant():
    battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))
    view = battle._build_view()

    assert (view.enemy.hp_current, view.enemy.hp_maximum) == (60, 60)
    assert view.enemy.mana_current is None
    assert view.enemy.super_current is None


def test_enemy_action_routes_authored_combat_move_through_resolver():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    resolver = RecordingResolver(accepted_result())
    battle = Battle(player_state, enemy_state, resolver=resolver)

    with patched_battle(), contextlib.redirect_stdout(io.StringIO()):
        battle.enemy_action()

    assert resolver.calls == [{
        "actor": enemy_state,
        "target": player_state,
        "move_name": enemy_state.combat_moves[0].name,
        "combat_state": battle.combat_state,
    }]


def test_enemy_action_uses_combat_moves_not_legacy_moves():
    player_state = PlayerState(Brawler())
    enemy_state = LegacyMovesFailingEnemyState(Goblin())
    resolver = RecordingResolver(accepted_result())
    battle = Battle(player_state, enemy_state, resolver=resolver)

    with patched_battle(), contextlib.redirect_stdout(io.StringIO()):
        battle.enemy_action()

    assert resolver.calls[0]["move_name"] == enemy_state.combat_moves[0].name


def test_enemy_action_does_not_use_legacy_misses_damage_or_direct_health_mutation():
    player_state = PlayerState(Brawler())
    resolver = RecordingResolver(accepted_result())
    battle = Battle(player_state, EnemyState(Goblin()), resolver=resolver)

    with patched_battle(randint=lambda _start, end: end), contextlib.redirect_stdout(io.StringIO()):
        battle.enemy_action()

    assert player_state.health.current == player_state.health.maximum
    assert len(resolver.calls) == 1


def test_enemy_action_completes_accepted_actions_in_phase_5():
    player_state = PlayerState(Brawler())
    resolver = RecordingResolver(accepted_result())
    battle = Battle(player_state, EnemyState(Goblin()), resolver=resolver)
    completion_calls = []

    original_completion = battle._complete_accepted_action

    def record_completion(*args, **kwargs):
        completion_calls.append((args, kwargs))
        return original_completion(*args, **kwargs)

    battle._complete_accepted_action = record_completion

    with patched_battle(), contextlib.redirect_stdout(io.StringIO()):
        battle.enemy_action()

    assert len(completion_calls) == 1
    assert completion_calls[0][0] == (
        battle.foe,
        (player_state,),
        accepted_result(),
    )
    assert battle.combat_state.turn_count == 1


def test_rejected_enemy_action_does_not_clear_defend_or_advance():
    player_state = PlayerState(Brawler())
    resolver = RecordingResolver(rejected_result())
    battle = Battle(player_state, EnemyState(Goblin()), resolver=resolver)
    battle.combat_state.activate_defend(player_state)

    with patched_battle(), contextlib.redirect_stdout(io.StringIO()):
        accepted = battle.enemy_action()

    assert accepted is False
    assert battle.combat_state.turn_count == 0
    assert battle.combat_state.is_defending(player_state)


def test_run_does_not_advance_turn_outside_accepted_action_completion():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)
    battle.foe.health.take_damage(battle.foe.health.maximum - 1)

    def fake_complete(actor, opposing_combatants):
        battle.foe.health.take_damage(1)
        battle.combat_state.turn_count += 1
        return battle.combat_state.turn_count

    battle.combat_state.complete_accepted_action = fake_complete
    battle.combat_state.advance_turn = lambda: (_ for _ in ()).throw(
        AssertionError("Battle.run must not advance turns directly")
    )

    with patched_battle(inputs=["attack", "1"], randint=lambda _start, _end: 1), contextlib.redirect_stdout(io.StringIO()):
        winner = battle.run()

    assert winner == "player"
    assert battle.combat_state.turn_count == 1


def test_player_damage_mutates_enemy_state_health_through_resolver():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)

    def fake_randint(start, end):
        if (start, end) == (1, 100):
            return 1
        return end

    with patched_battle(inputs=["attack", "1"], randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        battle.player_action()

    assert enemy_state.health.current < enemy_state.health.maximum


def test_low_health_enemy_does_not_use_universal_recovery_branch():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    enemy_state.health.take_damage(45)
    resolver = RecordingResolver(accepted_result())
    battle = Battle(player_state, enemy_state, resolver=resolver)

    with patched_battle(randint=lambda _start, end: end), contextlib.redirect_stdout(io.StringIO()):
        battle.enemy_action()

    assert enemy_state.health.current == 15
    assert len(resolver.calls) == 1


def test_battle_presentation_uses_canonical_short_identity_when_profile_attached():
    character = get_profile_by_choice("1").create_character()
    player_state = PlayerState(character)
    battle = Battle(player_state, EnemyState(Goblin()))
    battle._record_move_result(
        result_with(move_name="Crestgrave Reaping", damage=12),
        actor=battle.player_state,
        target=battle.foe,
    )
    view = battle._build_view()

    assert view.player.display_name == "Ser Branoc"
    assert view.log_entries[-1].actor_name == "Ser Branoc"
    assert view.player.display_name != "Brawler"


def test_battle_starts_from_existing_persistent_health():
    player_state = PlayerState(Brawler())
    player_state.health.take_damage(10)
    Battle(player_state, EnemyState(Goblin()))

    assert player_state.health.current == player_state.health.maximum - 10


def test_victory_returns_player():
    player_state = PlayerState(Monk())
    battle = Battle(player_state, EnemyState(Goblin()))
    initiative_rolls = 0

    def fake_randint(start, end):
        nonlocal initiative_rolls
        if (start, end) == (1, 2):
            initiative_rolls += 1
            return 1 if initiative_rolls == 1 else 2
        if (start, end) == (1, 100):
            return 1
        return end

    with patched_battle(inputs=["attack", "2", "attack", "2", "attack", "2", "attack", "2"], randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        winner = battle.run()

    assert winner == "player"
    assert battle.combat_state.turn_count == 5


def test_defeat_returns_enemy_and_persists_player_health():
    player_state = PlayerState(Brawler())
    player_state.health.take_damage(player_state.health.maximum - 3)
    battle = Battle(player_state, EnemyState(Goblin()))

    def fake_randint(start, end):
        if (start, end) == (1, 2):
            return 2
        if (start, end) == (1, 100):
            return 1
        return end

    with patched_battle(randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        winner = battle.run()

    assert winner == "enemy"
    assert player_state.health.is_defeated()
    assert player_state.health.current == 0
    assert battle.combat_state.turn_count == 1


def test_invalid_player_input_does_not_advance_turn_count_until_accepted_action():
    player_state = PlayerState(Brawler())
    battle = Battle(player_state, EnemyState(Goblin()))

    with patched_battle(inputs=["bad choice", "attack", "1"]), contextlib.redirect_stdout(io.StringIO()):
        battle.player_action()

    assert battle.combat_state.turn_count == 1


def test_completed_actions_advance_turn_count():
    player_state = PlayerState(Brawler())
    battle = Battle(player_state, EnemyState(Goblin()))
    initiative_rolls = 0

    def fake_randint(start, end):
        nonlocal initiative_rolls
        if (start, end) == (1, 2):
            initiative_rolls += 1
            return 1 if initiative_rolls == 1 else 2
        if (start, end) == (1, 100):
            return 1
        return end

    with patched_battle(inputs=["attack", "4", "attack", "4", "attack", "4", "attack", "4"], randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        winner = battle.run()

    assert winner == "player"
    assert battle.combat_state.turn_count == 7

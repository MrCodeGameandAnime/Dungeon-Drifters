from types import SimpleNamespace

import pytest

from app.combat.battle import Battle
from app.combat.combat_state import CombatState
from app.combat.result import MoveResult
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import Brawler, RogueArcher
from app.player.character_run_state import PreparedPayloadId, RunItemId
from app.player.inventory_action import (
    InventoryActionRejectionReason,
    InventoryActionResolver,
    InventoryActionResult,
)
from app.player.player_state import PlayerState
from app.player.run_items import (
    InventoryCommand,
    RUN_ITEM_DEFINITIONS,
    inventory_recipe_for_pair,
)
from app.presentation.battle_models import (
    ActionAvailabilityReason,
    ActionIntent,
    BattleEventType,
    BattleLogEntry,
    InteractionPhase,
)
from app.presentation.battle_presenter import BattlePresenter
from app.presentation.battle_session import BattlePresentationSession
from app.ui.battle_ui import (
    ChooseAction,
    ChooseInventoryCommand,
    ChooseInventoryCompanion,
    ChooseInventoryItem,
    ConfirmInventoryUse,
    GoBack,
)
from app.ui.terminal_battle_ui import TerminalBattleUI


class ScriptedUI:
    def __init__(self, *inputs):
        self.inputs = list(inputs)
        self.input_views = []

    def render(self, _view):
        pass

    def read_input(self, view):
        self.input_views.append(view)
        return self.inputs.pop(0)


class RecordingInventoryActionResolver(InventoryActionResolver):
    def __init__(self):
        self.calls = []

    def resolve(self, action_id, character_run_state):
        self.calls.append((action_id, character_run_state))
        return super().resolve(action_id, character_run_state)


class RejectingInventoryActionResolver:
    def __init__(self):
        self.calls = []

    def resolve(self, action_id, character_run_state):
        self.calls.append((action_id, character_run_state))
        return InventoryActionResult(
            action_id=action_id,
            accepted=False,
            reason=InventoryActionRejectionReason.MISSING_INGREDIENTS,
        )


class AcceptedDefendResolver:
    @staticmethod
    def resolve_defend(_actor, _combat_state):
        return MoveResult(
            accepted=True,
            hit=True,
            move_name="Defend",
            resource_spent=0,
            damage=0,
            healing=0,
            statuses_applied=(),
            reason=None,
        )


def _option(view, intent):
    return next(option for option in view.action_options if option.intent == intent)


def _preparation_inputs(source_item_id, *, confirmed=True):
    companion_item_id = (
        RunItemId.DEEP_COAL.value
        if source_item_id == RunItemId.EMBER_SHARD.value
        else RunItemId.EMBER_SHARD.value
    )
    return (
        ChooseAction(ActionIntent.ITEMS),
        ChooseInventoryItem(source_item_id),
        ChooseInventoryCommand(InventoryCommand.USE),
        ChooseInventoryCompanion(companion_item_id),
        ConfirmInventoryUse(confirmed),
    )


def test_item_authorship_and_recipe_pairing_are_deterministic_and_order_independent():
    assert tuple(
        (
            definition.item_id.value,
            definition.display_name,
            definition.description,
            definition.commands,
        )
        for definition in RUN_ITEM_DEFINITIONS
    ) == (
        (
            "ember_shard",
            "Ember Shard",
            "A heat-bearing mineral used to empower weapons with fire.",
            (InventoryCommand.INSPECT, InventoryCommand.USE),
        ),
        (
            "deep_coal",
            "Deep Coal",
            "A dense black catalyst used to bind heat into weapon runes.",
            (InventoryCommand.INSPECT, InventoryCommand.USE),
        ),
    )
    forward = inventory_recipe_for_pair("ember_shard", "deep_coal")
    reverse = inventory_recipe_for_pair("deep_coal", "ember_shard")

    assert forward is reverse
    assert forward.action_id.value == "prepare_cinderwrit"
    assert inventory_recipe_for_pair("ember_shard", "ember_shard") is None
    assert inventory_recipe_for_pair("ember_shard", "unknown") is None


def test_presenter_lists_owned_items_not_recipe_actions_and_becomes_empty():
    player = PlayerState(RogueArcher())
    enemy = EnemyState(Goblin())
    presenter = BattlePresenter()
    combat_state = SimpleNamespace(
        is_defending=lambda _actor: False,
        brace_incoming_protection_active=lambda _actor: False,
        arcane_overcharge_active=lambda _actor: False,
        arcane_instability_active=lambda _actor: False,
        gravemantle_break_active=lambda _actor: False,
        burn_active=lambda _actor: False,
        heal_cooldown_remaining=lambda _actor: 0,
        heal_available=lambda _actor: True,
    )
    initial = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.INVENTORY,
    )

    assert tuple(
        (item.item_id, item.display_name, item.quantity)
        for item in initial.inventory_items
    ) == (
        ("ember_shard", "Ember Shard", 1),
        ("deep_coal", "Deep Coal", 1),
    )
    assert not any(
        item.item_id == "prepare_cinderwrit" for item in initial.inventory_items
    )

    InventoryActionResolver().resolve(
        "prepare_cinderwrit",
        player.character_run_state,
    )
    empty_actions = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
    )
    assert _option(empty_actions, ActionIntent.ITEMS).enabled is False
    assert (
        _option(empty_actions, ActionIntent.ITEMS).disabled_reason
        == ActionAvailabilityReason.EMPTY_INVENTORY
    )

    branoc = PlayerState(Brawler())
    branoc_actions = presenter.build(
        player=branoc,
        enemy=enemy,
        combat_state=combat_state,
    )
    assert _option(branoc_actions, ActionIntent.ITEMS).enabled is False


@pytest.mark.parametrize(
    ("item_id", "description"),
    (
        (
            "ember_shard",
            "A heat-bearing mineral used to empower weapons with fire.",
        ),
        (
            "deep_coal",
            "A dense black catalyst used to bind heat into weapon runes.",
        ),
    ),
)
def test_repeated_item_inspection_is_deterministic_and_non_consuming(
    item_id,
    description,
):
    player = PlayerState(RogueArcher())
    enemy = EnemyState(Goblin())
    combat_state = CombatState()
    before = player.character_run_state.snapshot()
    presenter = BattlePresenter()

    first = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.INVENTORY_INSPECT,
        selected_inventory_item_id=item_id,
    )
    repeated = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.INVENTORY_INSPECT,
        selected_inventory_item_id=item_id,
    )

    assert first == repeated
    assert first.inventory_inspection.description == description
    assert player.character_run_state.snapshot() == before


def test_inspect_no_and_back_do_not_invoke_resolver_mutate_or_add_a_turn():
    player = PlayerState(RogueArcher())
    before = player.character_run_state.snapshot()
    inventory_resolver = RecordingInventoryActionResolver()
    session = BattlePresentationSession()
    session.record(BattleLogEntry(BattleEventType.DEFEND, actor_name="Zhaivra"))
    ui = ScriptedUI(
        ChooseAction(ActionIntent.ITEMS),
        ChooseInventoryItem("ember_shard"),
        ChooseInventoryCommand(InventoryCommand.INSPECT),
        GoBack(),
        ChooseInventoryCommand(InventoryCommand.USE),
        ChooseInventoryCompanion("deep_coal"),
        ConfirmInventoryUse(False),
        GoBack(),
        GoBack(),
        ChooseAction(ActionIntent.DEFEND),
    )
    battle = Battle(
        player,
        EnemyState(Goblin()),
        ui=ui,
        resolver=AcceptedDefendResolver(),
        inventory_action_resolver=inventory_resolver,
        presentation_session=session,
    )

    assert battle.player_action() is True

    assert inventory_resolver.calls == []
    assert player.character_run_state.snapshot() == before
    assert battle.combat_state.turn_count == 1
    assert tuple(view.interaction_phase for view in ui.input_views[:-1]) == (
        InteractionPhase.ACTIONS,
        InteractionPhase.INVENTORY,
        InteractionPhase.INVENTORY_ITEM,
        InteractionPhase.INVENTORY_INSPECT,
        InteractionPhase.INVENTORY_ITEM,
        InteractionPhase.INVENTORY_COMBINATION,
        InteractionPhase.INVENTORY_CONFIRMATION,
        InteractionPhase.INVENTORY_ITEM,
        InteractionPhase.INVENTORY,
    )
    assert all(
        view.log_entries == (BattleLogEntry(BattleEventType.DEFEND, actor_name="Zhaivra"),)
        for view in ui.input_views[:-1]
    )


@pytest.mark.parametrize("source_item_id", ("ember_shard", "deep_coal"))
def test_confirming_either_item_order_routes_one_internal_preparation(source_item_id):
    player = PlayerState(RogueArcher())
    inventory_resolver = RecordingInventoryActionResolver()
    ui = ScriptedUI(*_preparation_inputs(source_item_id))
    battle = Battle(
        player,
        EnemyState(Goblin()),
        ui=ui,
        inventory_action_resolver=inventory_resolver,
    )

    assert battle.player_action() is True

    assert inventory_resolver.calls == [
        ("prepare_cinderwrit", player.character_run_state)
    ]
    assert player.character_run_state.item_quantity(RunItemId.EMBER_SHARD) == 0
    assert player.character_run_state.item_quantity(RunItemId.DEEP_COAL) == 0
    assert player.character_run_state.payload_prepared(
        PreparedPayloadId.CINDERWRIT
    ) is True
    assert battle.combat_state.turn_count == 1
    confirmation_view = ui.input_views[-1].inventory_confirmation
    assert confirmation_view.source_item_id == source_item_id
    assert confirmation_view.action_id == "prepare_cinderwrit"


def test_fabricated_item_and_companion_ids_are_rejected_before_resolution():
    player = PlayerState(RogueArcher())
    inventory_resolver = RecordingInventoryActionResolver()
    ui = ScriptedUI(
        ChooseAction(ActionIntent.ITEMS),
        ChooseInventoryItem("fabricated_item"),
        ChooseInventoryItem("ember_shard"),
        ChooseInventoryCommand(InventoryCommand.USE),
        ChooseInventoryCompanion("fabricated_companion"),
        ChooseInventoryCompanion("deep_coal"),
        ConfirmInventoryUse(True),
    )
    battle = Battle(
        player,
        EnemyState(Goblin()),
        ui=ui,
        inventory_action_resolver=inventory_resolver,
    )

    assert battle.player_action() is True

    assert len(inventory_resolver.calls) == 1
    assert battle.combat_state.turn_count == 1
    assert player.character_run_state.payload_prepared(
        PreparedPayloadId.CINDERWRIT
    ) is True


def test_rejected_confirmation_preserves_inventory_and_does_not_complete_action():
    player = PlayerState(RogueArcher())
    before = player.character_run_state.snapshot()
    inventory_resolver = RejectingInventoryActionResolver()
    ui = ScriptedUI(
        *_preparation_inputs("ember_shard"),
        ConfirmInventoryUse(False),
        GoBack(),
        GoBack(),
        ChooseAction(ActionIntent.DEFEND),
    )
    battle = Battle(
        player,
        EnemyState(Goblin()),
        ui=ui,
        resolver=AcceptedDefendResolver(),
        inventory_action_resolver=inventory_resolver,
    )

    assert battle.player_action() is True

    assert len(inventory_resolver.calls) == 1
    assert player.character_run_state.snapshot() == before
    assert battle.combat_state.turn_count == 1


@pytest.mark.parametrize("width", (60, 80, 120))
def test_every_item_first_terminal_phase_remains_within_supported_width(width):
    player = PlayerState(RogueArcher())
    enemy = EnemyState(Goblin())
    combat_state = CombatState()
    presenter = BattlePresenter()
    phase_values = (
        (InteractionPhase.INVENTORY, None, None),
        (InteractionPhase.INVENTORY_ITEM, "ember_shard", None),
        (InteractionPhase.INVENTORY_INSPECT, "ember_shard", None),
        (InteractionPhase.INVENTORY_COMBINATION, "ember_shard", None),
        (InteractionPhase.INVENTORY_CONFIRMATION, "ember_shard", "deep_coal"),
    )
    lines = []
    ui = TerminalBattleUI(
        output_func=lines.append,
        width_provider=lambda: width,
        ansi_enabled=False,
        interactive=False,
    )

    for phase, selected_item, companion in phase_values:
        view = presenter.build(
            player=player,
            enemy=enemy,
            combat_state=combat_state,
            interaction_phase=phase,
            selected_inventory_item_id=selected_item,
            selected_inventory_companion_id=companion,
        )
        ui.render(view)

    assert lines
    assert all(len(line) <= width for line in lines)

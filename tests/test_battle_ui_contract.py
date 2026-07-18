from dataclasses import FrozenInstanceError

import pytest

from app.presentation.battle_models import ActionIntent
from app.player.run_items import InventoryCommand
from app.ui.battle_ui import (
    BattleUI,
    ChooseAction,
    ChooseInventoryCommand,
    ChooseInventoryCompanion,
    ChooseInventoryItem,
    ChooseMove,
    ConfirmInventoryUse,
    GoBack,
)


def test_semantic_input_values_are_frozen_and_validated():
    action = ChooseAction(ActionIntent.ATTACK)
    move = ChooseMove("Ironwake Dismemberment")
    inventory_item = ChooseInventoryItem("ember_shard")
    inventory_command = ChooseInventoryCommand(InventoryCommand.USE)
    inventory_companion = ChooseInventoryCompanion("deep_coal")
    confirmation = ConfirmInventoryUse(True)
    back = GoBack()

    assert action.intent == ActionIntent.ATTACK
    assert move.move_key == "Ironwake Dismemberment"
    assert inventory_item.item_id == "ember_shard"
    assert inventory_command.command == InventoryCommand.USE
    assert inventory_companion.item_id == "deep_coal"
    assert confirmation.confirmed is True
    with pytest.raises(FrozenInstanceError):
        action.intent = ActionIntent.DEFEND
    with pytest.raises(ValueError):
        ChooseAction("unsupported")
    with pytest.raises(ValueError):
        ChooseMove("")
    with pytest.raises(TypeError):
        ChooseMove(1)
    with pytest.raises(ValueError):
        ChooseInventoryItem("")
    with pytest.raises(TypeError):
        ChooseInventoryItem(1)
    with pytest.raises(ValueError):
        ChooseInventoryCommand("unsupported")
    with pytest.raises(ValueError):
        ChooseInventoryCompanion("")
    with pytest.raises(TypeError):
        ConfirmInventoryUse(1)
    assert back == GoBack()


def test_battle_ui_protocol_is_runtime_checkable():
    class Adapter:
        def render(self, view):
            pass

        def read_input(self, view):
            return GoBack()

    assert isinstance(Adapter(), BattleUI)

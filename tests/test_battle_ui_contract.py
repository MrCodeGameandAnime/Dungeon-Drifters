from dataclasses import FrozenInstanceError

import pytest

from app.presentation.battle_models import ActionIntent
from app.ui.battle_ui import BattleUI, ChooseAction, ChooseMove, GoBack


def test_semantic_input_values_are_frozen_and_validated():
    action = ChooseAction(ActionIntent.ATTACK)
    move = ChooseMove("Ironwake Dismemberment")
    back = GoBack()

    assert action.intent == ActionIntent.ATTACK
    assert move.move_key == "Ironwake Dismemberment"
    with pytest.raises(FrozenInstanceError):
        action.intent = ActionIntent.DEFEND
    with pytest.raises(ValueError):
        ChooseAction("unsupported")
    with pytest.raises(ValueError):
        ChooseMove("")
    with pytest.raises(TypeError):
        ChooseMove(1)
    assert back == GoBack()


def test_battle_ui_protocol_is_runtime_checkable():
    class Adapter:
        def render(self, view):
            pass

        def read_input(self, view):
            return GoBack()

    assert isinstance(Adapter(), BattleUI)

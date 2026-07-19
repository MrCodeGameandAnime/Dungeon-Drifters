import pytest

from app.presentation.overworld_models import (
    OverworldAction,
    OverworldAvailabilityReason,
    OverworldOptionView,
    OverworldScreen,
    StatRowView,
)
from app.ui.overworld_ui import ChooseOverworldAction, ChooseOverworldItem, OverworldUI


def test_overworld_options_are_immutable_and_validate_availability():
    option = OverworldOptionView(OverworldAction.CHARACTER, "Character", True)

    with pytest.raises(AttributeError):
        option.label = "Changed"
    with pytest.raises(ValueError, match="availability"):
        OverworldOptionView(OverworldAction.CHARACTER, "Character", False)
    with pytest.raises(ValueError, match="availability"):
        OverworldOptionView(
            OverworldAction.CHARACTER,
            "Character",
            True,
            OverworldAvailabilityReason.SAVE_UNAVAILABLE,
        )


def test_stat_rows_distinguish_hidden_and_disabled_growth_controls():
    overview = StatRowView("Strength", 15)
    skills = StatRowView(
        "Strength",
        15,
        increase_visible=True,
        increase_enabled=False,
        disabled_reason=OverworldAvailabilityReason.GROWTH_UNAVAILABLE,
    )

    assert overview.increase_visible is False
    assert skills.increase_visible is True
    assert skills.increase_enabled is False


def test_semantic_overworld_inputs_validate_and_the_protocol_is_runtime_checkable():
    action = ChooseOverworldAction(OverworldAction.MAP)
    item = ChooseOverworldItem("run-item:ember_shard")

    assert action.action is OverworldAction.MAP
    assert item.selection_key == "run-item:ember_shard"

    class UI:
        def render(self, view):
            pass

        def read_input(self, view):
            pass

    assert isinstance(UI(), OverworldUI)


def test_all_approved_screen_values_are_typed():
    assert tuple(screen.value for screen in OverworldScreen) == (
        "main",
        "character",
        "skills",
        "weapon",
        "equipment",
        "items",
        "item_inspect",
        "map",
        "options",
        "quit_confirmation",
    )

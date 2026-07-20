import pytest

from app.presentation.overworld_models import (
    OverworldAction,
    OverworldAvailabilityReason,
    OverworldOptionView,
    OverworldScreen,
    OverworldView,
    CharacterOverviewView,
    StatRowView,
)
from app.ui.overworld_ui import (
    ChooseOverworldAction,
    ChooseOverworldItem,
    ChoosePermanentStatIncrease,
    OverworldUI,
)


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
    overview = StatRowView("strength", "Strength", 15)
    skills = StatRowView(
        "strength",
        "Strength",
        15,
        increase_visible=True,
        increase_enabled=False,
        disabled_reason=OverworldAvailabilityReason.GROWTH_UNAVAILABLE,
    )

    assert overview.stat_name == "strength"
    assert overview.increase_visible is False
    assert skills.increase_visible is True
    assert skills.increase_enabled is False


def test_character_overview_accepts_missing_cap_threshold_only():
    values = dict(
        display_name="Ser Branoc",
        archetype_label="Brawler",
        stats=(StatRowView("strength", "Strength", 15),),
        level=250,
        exp_current=0,
        exp_threshold=None,
        exp_fill_bps=10_000,
        hp_current=116,
        hp_maximum=116,
        mana_current=46,
        mana_maximum=46,
        super_current=0,
        super_maximum=100,
    )

    overview = CharacterOverviewView(**values)

    assert overview.exp_threshold is None
    with pytest.raises((TypeError, ValueError)):
        CharacterOverviewView(**{**values, "exp_threshold": -1})


def test_semantic_overworld_inputs_validate_and_the_protocol_is_runtime_checkable():
    action = ChooseOverworldAction(OverworldAction.MAP)
    item = ChooseOverworldItem("run-item:ember_shard")
    stat = ChoosePermanentStatIncrease("strength")

    assert action.action is OverworldAction.MAP
    assert item.selection_key == "run-item:ember_shard"
    assert stat.stat_name == "strength"

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
        "map_inspect",
        "options",
        "quit_confirmation",
    )


def test_contextual_route_actions_have_a_dedicated_main_screen_boundary():
    contextual = OverworldOptionView(
        OverworldAction.ENTER_ENCOUNTER,
        "Enter Encounter",
        True,
    )

    view = OverworldView(
        OverworldScreen.MAIN,
        "Goblin Ambush",
        "The road begins here.",
        (),
        contextual_route_option=contextual,
    )

    assert view.options == ()
    assert view.contextual_route_option is contextual
    with pytest.raises(ValueError, match="must not be stored in options"):
        OverworldView(
            OverworldScreen.MAIN,
            "Goblin Ambush",
            "The road begins here.",
            (contextual,),
        )
    with pytest.raises(ValueError, match="only on the Main screen"):
        OverworldView(
            OverworldScreen.OPTIONS,
            "Goblin Ambush",
            "The road begins here.",
            (),
            contextual_route_option=contextual,
        )

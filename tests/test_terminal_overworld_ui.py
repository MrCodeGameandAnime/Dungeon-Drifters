import pytest

from app.game.game_state import GameState
from app.player.character import Brawler, RogueArcher
from app.player.player_state import PlayerState
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.presentation.overworld_presenter import OverworldPresenter
from app.ui.overworld_ui import ChooseOverworldAction, ChooseOverworldItem
from app.ui.terminal_overworld_ui import TerminalOverworldUI


def create_view(screen=OverworldScreen.MAIN, character_type=Brawler, **kwargs):
    game = GameState(PlayerState(character_type()))
    return OverworldPresenter().build(game, screen=screen, **kwargs)


def rendered(view, *, width=100, unicode_enabled=False, interactive=False):
    output = []
    TerminalOverworldUI(
        output_func=output.append,
        width_provider=lambda: width,
        unicode_enabled=unicode_enabled,
        interactive=interactive,
        ansi_enabled=interactive,
    ).render(view)
    return output


def read(view, values):
    output = []
    choices = iter(values)
    result = TerminalOverworldUI(
        input_func=lambda prompt: next(choices),
        output_func=output.append,
        interactive=False,
    ).read_input(view)
    return result, output


def test_main_screen_is_framed_and_matches_the_wireframe_regions():
    lines = rendered(create_view())
    text = "\n".join(lines)

    assert lines[0].startswith("+")
    assert "OVERWORLD  |  Goblin Ambush" in text
    assert "ADVENTURE" in text
    assert "The road through Ketlyv" in text
    assert "[1/C] Character" in text
    assert "[2/I] Items" in text
    assert "[3/M] Map" in text
    assert "[4/O] Options" in text
    assert "[5/E] Enter Encounter" in text
    assert lines[-1].startswith("+")


@pytest.mark.parametrize(
    ("screen", "required_text"),
    (
        (OverworldScreen.CHARACTER, ("CHARACTER", "STATS", "Level 1", "XP [")),
        (OverworldScreen.SKILLS, ("SKILLS", "LEVEL UP", "[+ Unavailable]", "ATTACKS")),
        (OverworldScreen.WEAPON, ("WEAPON", "Sunder-Spire", "BONUSES", "DESCRIPTION")),
        (OverworldScreen.EQUIPMENT, ("EQUIPMENT", "Necklace", "Ring", "BENEFITS", "None")),
        (OverworldScreen.ITEMS, ("ITEMS", "Your persistent inventory is empty.", "Craft")),
        (OverworldScreen.MAP, ("MAP", "SURFACE ROUTE", "Goblin Ambush", "Dungeon Entrance")),
        (OverworldScreen.OPTIONS, ("OPTIONS", "Save", "Quit", "Load", "Back")),
        (OverworldScreen.QUIT_CONFIRMATION, ("QUIT", "Exit this session without saving?", "Confirm", "Cancel")),
    ),
)
def test_each_overworld_screen_has_distinct_structured_regions(
    screen,
    required_text,
):
    text = "\n".join(rendered(create_view(screen)))

    for value in required_text:
        assert value in text


def test_item_screen_uses_authored_labels_and_hides_internal_selection_keys():
    view = create_view(OverworldScreen.ITEMS, RogueArcher)
    selected_key = view.inventory.items[0].selection_key
    selected = create_view(
        OverworldScreen.ITEMS,
        RogueArcher,
        selected_item_key=selected_key,
    )
    inspection = create_view(
        OverworldScreen.ITEM_INSPECT,
        RogueArcher,
        selected_item_key=selected_key,
    )

    item_text = "\n".join(rendered(selected))
    inspection_text = "\n".join(rendered(inspection))

    assert "Ember Shard x1" in item_text
    assert "> 1. Ember Shard" in item_text
    assert "A heat-bearing mineral" in inspection_text
    assert "ember_shard" not in item_text
    assert "run-item:" not in item_text
    assert "surface_" not in item_text


def test_interactive_render_clears_before_the_complete_screen():
    lines = rendered(create_view(), interactive=True)

    assert lines[0].startswith("\033[2J\033[H+")
    assert sum("\033[2J\033[H" in line for line in lines) == 1


def test_narrow_terminal_uses_readable_linear_fallback():
    lines = rendered(create_view(OverworldScreen.CHARACTER), width=42)
    text = "\n".join(lines)

    assert lines[0] == "CHARACTER"
    assert "Location: Goblin Ambush" in text
    assert "STATS" in text
    assert not any(line.startswith("+") for line in lines)
    assert all(len(line) <= 42 for line in lines)


def test_main_and_character_inputs_translate_to_semantic_actions():
    main_result, _ = read(create_view(), ["1"])
    encounter_result, _ = read(create_view(), ["e"])
    character_result, _ = read(create_view(OverworldScreen.CHARACTER), ["weapon"])

    assert main_result == ChooseOverworldAction(OverworldAction.CHARACTER)
    assert encounter_result == ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
    assert character_result == ChooseOverworldAction(OverworldAction.WEAPON)


def test_item_number_selects_the_item_without_exposing_its_key():
    view = create_view(OverworldScreen.ITEMS, RogueArcher)

    result, output = read(view, ["1"])

    assert isinstance(result, ChooseOverworldItem)
    assert result.selection_key == view.inventory.items[0].selection_key
    assert output == []


def test_disabled_action_reports_reason_then_keeps_the_screen_open():
    view = create_view(OverworldScreen.ITEMS)

    result, output = read(view, ["craft", "back"])

    assert result == ChooseOverworldAction(OverworldAction.BACK)
    assert output == ["Crafting is not yet available."]


def test_invalid_input_changes_no_view_and_requires_another_choice():
    view = create_view(OverworldScreen.OPTIONS)

    result, output = read(view, ["nonsense", "q"])

    assert result == ChooseOverworldAction(OverworldAction.QUIT)
    assert output == ["That option is not available."]


def test_quit_confirmation_uses_typed_confirm_and_cancel_inputs():
    view = create_view(OverworldScreen.QUIT_CONFIRMATION)

    confirm, _ = read(view, ["y"])
    cancel, _ = read(view, ["n"])

    assert confirm == ChooseOverworldAction(OverworldAction.CONFIRM)
    assert cancel == ChooseOverworldAction(OverworldAction.CANCEL)


def test_terminal_ui_rejects_non_overworld_views():
    ui = TerminalOverworldUI(interactive=False)

    with pytest.raises(TypeError, match="OverworldView"):
        ui.render(object())
    with pytest.raises(TypeError, match="OverworldView"):
        ui.read_input(object())

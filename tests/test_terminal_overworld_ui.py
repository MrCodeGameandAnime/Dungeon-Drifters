import pytest

from app.game.game_state import GameState
from app.game.overworld_route import SECOND_SURFACE_NODE_ID
from app.game.overworld_state import ContextualRoutePhase
from app.player.character import Brawler, RogueArcher
from app.player.player_state import PlayerState
from app.player.progression import MAXIMUM_LEVEL
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.presentation.overworld_presenter import OverworldPresenter
from app.ui.overworld_ui import (
    ChooseOverworldAction,
    ChooseOverworldItem,
    ChoosePermanentStatIncrease,
)
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
    assert "[C] Character" in text
    assert "[I] Items" in text
    assert "[M] Map" in text
    assert "[O] Options" in text
    assert "[E] Enter Encounter" in text
    contextual_index = next(
        index for index, line in enumerate(lines) if "[E] Enter Encounter" in line
    )
    controls_index = next(
        index for index, line in enumerate(lines) if "[C] Character" in line
    )
    assert contextual_index < controls_index
    assert not any("[1/" in line for line in lines)
    assert lines[-1].startswith("+")


def test_main_contextual_action_tracks_enter_retry_and_paused_route_states():
    game = GameState(PlayerState(Brawler()))
    presenter = OverworldPresenter()
    initial = presenter.build(game)
    game.overworld_state.set_contextual_route_phase(ContextualRoutePhase.RETRY)
    retry = presenter.build(game)
    game.overworld_state.advance_to(SECOND_SURFACE_NODE_ID)
    paused = presenter.build(game)

    initial_text = "\n".join(rendered(initial))
    retry_text = "\n".join(rendered(retry))
    paused_text = "\n".join(rendered(paused))

    assert "[E] Enter Encounter" in initial_text
    assert "[R] Retry" not in initial_text
    assert "[R] Retry" in retry_text
    assert "[E] Enter Encounter" not in retry_text
    assert "[E] Enter Encounter" not in paused_text
    assert "[R] Retry" not in paused_text
    for text in (initial_text, retry_text, paused_text):
        assert all(
            label in text
            for label in (
                "[C] Character",
                "[I] Items",
                "[M] Map",
                "[O] Options",
            )
        )


def test_character_screen_renders_normal_and_capped_exp_at_supported_widths():
    game = GameState(PlayerState(Brawler()))
    game.player_state.exp_state.current = 40
    normal = OverworldPresenter().build(
        game,
        screen=OverworldScreen.CHARACTER,
    )

    game.player_state.level_state.current = MAXIMUM_LEVEL
    game.player_state.exp_state.current = 0
    capped = OverworldPresenter().build(
        game,
        screen=OverworldScreen.CHARACTER,
    )

    for width in (50, 100):
        for unicode_enabled in (False, True):
            normal_text = "\n".join(
                rendered(
                    normal,
                    width=width,
                    unicode_enabled=unicode_enabled,
                )
            )
            capped_text = "\n".join(
                rendered(
                    capped,
                    width=width,
                    unicode_enabled=unicode_enabled,
                )
            )
            assert "XP [" in normal_text
            assert "40/100" in normal_text
            assert "XP MAX LEVEL" in capped_text
            assert "None" not in capped_text


@pytest.mark.parametrize(
    ("screen", "required_text"),
    (
        (
            OverworldScreen.CHARACTER,
            ("CHARACTER", "STATS", "Level 1", "Super 0/100", "XP ["),
        ),
        (
            OverworldScreen.SKILLS,
            (
                "SKILLS",
                "LEVEL UP",
                "Growth Points: 0",
                "[No Growth Points]",
                "ATTACKS",
            ),
        ),
        (OverworldScreen.WEAPON, ("WEAPON", "Sunder-Spire", "BONUSES", "DESCRIPTION")),
        (OverworldScreen.EQUIPMENT, ("EQUIPMENT", "Necklace", "Ring", "BENEFITS", "None")),
        (OverworldScreen.ITEMS, ("ITEMS", "Your persistent inventory is empty.", "Craft")),
        (OverworldScreen.MAP, ("MAP", "SURFACE ROUTE", "Goblin Ambush", "Dungeon Entrance")),
        (
            OverworldScreen.MAP_INSPECT,
            ("ENCOUNTER INSPECTION", "Goblin Ambush", "COMPOSITION", "Goblin"),
        ),
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


@pytest.mark.parametrize("width", (42, 29, 20))
def test_narrow_terminal_uses_width_safe_stacked_linear_fallback(width):
    lines = rendered(create_view(OverworldScreen.CHARACTER), width=width)
    text = "\n".join(lines)

    assert lines[0] == "CHARACTER"
    assert "STATS" in text
    assert not any(line.startswith("+") for line in lines)
    assert all(len(line) <= width for line in lines)
    assert "[S] Skills" in text
    assert "[W] Weapon" in text
    assert "[E] Equipment" in text
    assert "[B] Back" in text
    if width < 30:
        assert "XP 0/100" in text
    else:
        assert "XP [" in text


@pytest.mark.parametrize(
    "screen",
    (
        OverworldScreen.MAIN,
        OverworldScreen.SKILLS,
        OverworldScreen.WEAPON,
        OverworldScreen.EQUIPMENT,
        OverworldScreen.ITEMS,
        OverworldScreen.MAP,
        OverworldScreen.MAP_INSPECT,
        OverworldScreen.OPTIONS,
        OverworldScreen.QUIT_CONFIRMATION,
    ),
)
def test_every_screen_respects_a_terminal_width_below_thirty(screen):
    lines = rendered(create_view(screen), width=24)

    assert all(len(line) <= 24 for line in lines)
    assert not any(line.startswith("+") for line in lines)


def test_character_screen_renders_exact_nondefault_hp_mana_and_super_resources():
    game = GameState(PlayerState(Brawler()))
    game.player_state.health.take_damage(9)
    assert game.player_state.mana_resource.spend(4) is True
    game.player_state.super_resource.gain(41)
    view = OverworldPresenter().build(
        game,
        screen=OverworldScreen.CHARACTER,
    )

    text = "\n".join(rendered(view))

    assert "HP 107/116" in text
    assert "Mana 42/46" in text
    assert "Super 41/100" in text


def test_map_renders_current_completed_and_remaining_markers_exactly():
    game = GameState(PlayerState(Brawler()))
    game.world_state.mark_encounter_defeated("surface_goblin_solo")
    game.overworld_state.advance_to(SECOND_SURFACE_NODE_ID)
    view = OverworldPresenter().build(game, screen=OverworldScreen.MAP)

    text = "\n".join(rendered(view))

    assert "OK [Encounter] Goblin Ambush" in text
    assert ">> [Encounter] Goblin Pair" in text
    assert ".. [Encounter] Goblin Warrior" in text
    assert "surface_goblin" not in text


@pytest.mark.parametrize(
    ("key", "action"),
    (
        ("c", OverworldAction.CHARACTER),
        ("i", OverworldAction.ITEMS),
        ("m", OverworldAction.MAP),
        ("o", OverworldAction.OPTIONS),
        ("e", OverworldAction.ENTER_ENCOUNTER),
    ),
)
def test_main_accepts_only_each_displayed_mnemonic(key, action):
    result, output = read(create_view(), [key])

    assert result == ChooseOverworldAction(action)
    assert output == []


def test_retry_mnemonic_is_available_only_when_retry_is_offered():
    game = GameState(PlayerState(Brawler()))
    game.overworld_state.set_contextual_route_phase(ContextualRoutePhase.RETRY)
    retry = OverworldPresenter().build(game)

    result, output = read(retry, ["r"])
    unavailable, unavailable_output = read(create_view(), ["r", "c"])

    assert result == ChooseOverworldAction(OverworldAction.RETRY)
    assert output == []
    assert unavailable == ChooseOverworldAction(OverworldAction.CHARACTER)
    assert unavailable_output == ["That option is not available."]


def test_encounter_mnemonic_is_rejected_when_no_contextual_action_is_offered():
    game = GameState(PlayerState(Brawler()))
    game.overworld_state.advance_to(SECOND_SURFACE_NODE_ID)
    paused = OverworldPresenter().build(game)

    result, output = read(paused, ["e", "c"])

    assert result == ChooseOverworldAction(OverworldAction.CHARACTER)
    assert output == ["That option is not available."]


def test_numeric_full_label_and_enum_aliases_are_rejected_for_main_commands():
    rejected = (
        "1",
        "2",
        "3",
        "4",
        "5",
        "character",
        "items",
        "map",
        "options",
        "enter encounter",
        "enter_encounter",
    )

    result, output = read(create_view(), (*rejected, "c"))

    assert result == ChooseOverworldAction(OverworldAction.CHARACTER)
    assert output == ["That option is not available."] * len(rejected)


def test_character_submenu_accepts_only_its_displayed_mnemonics():
    view = create_view(OverworldScreen.CHARACTER)

    result, output = read(view, ["weapon", "2", "w"])

    assert result == ChooseOverworldAction(OverworldAction.WEAPON)
    assert output == ["That option is not available."] * 2


def test_skills_numeric_input_translates_to_canonical_stat_and_disables_without_points():
    view = create_view(OverworldScreen.SKILLS)

    result, output = read(view, ["1", "b"])

    assert result == ChooseOverworldAction(OverworldAction.BACK)
    assert output == ["Earn Growth Points by leveling up."]


def test_skills_numeric_input_exposes_enabled_stat_increase():
    game = GameState(PlayerState(Brawler()))
    game.player_state.gain_experience(100)
    view = OverworldPresenter().build(game, screen=OverworldScreen.SKILLS)

    result, output = read(view, ["1"])

    assert result == ChoosePermanentStatIncrease("strength")
    assert output == []


def test_skills_render_maximum_and_enabled_controls():
    game = GameState(PlayerState(Brawler()))
    game.player_state.gain_experience(100)
    game.player_state.character.permanent_stats.set_stat("strength", 100)
    view = OverworldPresenter().build(game, screen=OverworldScreen.SKILLS)

    text = "\n".join(rendered(view))

    assert "Growth Points: 3" in text
    assert "1. Strength" in text
    assert "[Maximum]" in text
    assert "[+1]" in text


def test_item_number_selects_the_item_without_exposing_its_key():
    view = create_view(OverworldScreen.ITEMS, RogueArcher)

    result, output = read(view, ["1"])

    assert isinstance(result, ChooseOverworldItem)
    assert result.selection_key == view.inventory.items[0].selection_key
    assert output == []


def test_item_display_name_is_not_a_hidden_selection_alias():
    view = create_view(OverworldScreen.ITEMS, RogueArcher)

    result, output = read(view, ["Ember Shard", "1"])

    assert isinstance(result, ChooseOverworldItem)
    assert output == ["That option is not available."]


def test_disabled_action_reports_reason_then_keeps_the_screen_open():
    view = create_view(OverworldScreen.ITEMS)

    result, output = read(view, ["c", "b"])

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

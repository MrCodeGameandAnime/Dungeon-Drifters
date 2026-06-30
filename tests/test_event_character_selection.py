import builtins
import contextlib
import io
import random
from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.world.character_profiles.profile import CharacterProfile
import app.world.event as event_module
from app.world.event import Events


class FakeConsole:
    clear_calls = 0

    @classmethod
    def clear_console(cls):
        cls.clear_calls += 1


def run_pick_character_with_inputs(inputs):
    original_input = builtins.input
    original_console = event_module.console
    entered_values = iter(inputs)
    output = io.StringIO()
    FakeConsole.clear_calls = 0

    def fake_input(prompt=""):
        print(prompt, end="")
        return next(entered_values)

    try:
        builtins.input = fake_input
        event_module.console = FakeConsole
        with contextlib.redirect_stdout(output):
            player = Events().pick_character()
    finally:
        builtins.input = original_input
        event_module.console = original_console

    return player, output.getvalue(), FakeConsole.clear_calls


def test_valid_character_choices_return_expected_classes():
    cases = (
        ("1", Brawler, "Ser Branoc, the Unbroken Crest"),
        ("2", BlackMage, "Azhvielle, the Unconfessed"),
        ("3", RogueArcher, "Zhaivra Kelyth, the Uncontrolled Reagent"),
        ("4", Monk, "Joruun Veyr, the Bloody Storm Monk"),
    )

    for choice, expected_class, full_name in cases:
        player, output, clear_calls = run_pick_character_with_inputs([choice, "Y"])

        assert isinstance(player, expected_class)
        assert player.profile is not None
        assert player.name == player.archetype_name
        assert f"You have chosen {full_name}!" in output
        assert clear_calls == 1


def test_invalid_character_choice_reprompts_then_returns_valid_selection():
    player, output, clear_calls = run_pick_character_with_inputs(["bad", "2", "yes"])

    assert isinstance(player, BlackMage)
    assert "That is not a valid character choice. Please try again." in output
    assert "Continue with" not in output.split("That is not a valid character choice. Please try again.")[0]
    assert "You have chosen Azhvielle, the Unconfessed!" in output
    assert clear_calls == 1


def test_declined_confirmation_returns_to_compact_roster():
    player, output, clear_calls = run_pick_character_with_inputs(["1", "N", "4", "Y"])

    assert isinstance(player, Monk)
    assert output.count("1. Ser Branoc, the Unbroken Crest") == 2
    assert "Continue with Ser Branoc? [Y/N]:" in output
    assert "You have chosen Joruun Veyr, the Bloody Storm Monk!" in output
    assert clear_calls == 3


def test_invalid_confirmation_repeats_confirmation_only():
    player, output, clear_calls = run_pick_character_with_inputs(["3", "maybe", "yes"])

    assert isinstance(player, RogueArcher)
    assert output.count("3. Zhaivra Kelyth, the Uncontrolled Reagent") == 1
    assert output.count("Continue with Zhaivra Kelyth? [Y/N]:") == 2
    assert "Please enter Y or N." in output
    assert clear_calls == 1


def test_character_construction_happens_only_after_positive_confirmation():
    original_create_character = CharacterProfile.create_character
    created_profiles = []

    def tracked_create_character(self):
        created_profiles.append(self.short_name)
        return original_create_character(self)

    try:
        CharacterProfile.create_character = tracked_create_character
        player, output, clear_calls = run_pick_character_with_inputs(["1", "maybe", "N", "2", "yes"])
    finally:
        CharacterProfile.create_character = original_create_character

    assert isinstance(player, BlackMage)
    assert created_profiles == ["Azhvielle"]
    assert "Please enter Y or N." in output
    assert clear_calls == 3


def test_avoid_battle_success_behavior_is_unchanged():
    original_randint = random.randint
    output = io.StringIO()

    try:
        random.randint = lambda _start, _end: 10
        with contextlib.redirect_stdout(output):
            escaped = Events().avoid_battle()
    finally:
        random.randint = original_randint

    assert escaped is True
    assert "You escaped in the nick of time. Live to fight another day." in output.getvalue()


def test_avoid_battle_failure_behavior_is_unchanged():
    original_randint = random.randint
    output = io.StringIO()

    try:
        random.randint = lambda _start, _end: 1
        with contextlib.redirect_stdout(output):
            escaped = Events().avoid_battle()
    finally:
        random.randint = original_randint

    assert escaped is False
    assert "You can't escape. It's time for battle!" in output.getvalue()

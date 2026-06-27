import builtins
import contextlib
import io
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.world.event import Events


def run_pick_character_with_inputs(inputs):
    original_input = builtins.input
    entered_values = iter(inputs)
    output = io.StringIO()

    def fake_input(_prompt):
        return next(entered_values)

    try:
        builtins.input = fake_input
        with contextlib.redirect_stdout(output):
            player = Events().pick_character()
    finally:
        builtins.input = original_input

    return player, output.getvalue()


def test_valid_character_choices_return_expected_classes():
    cases = (
        ("1", Brawler),
        ("2", BlackMage),
        ("3", RogueArcher),
        ("4", Monk),
    )

    for choice, expected_class in cases:
        player, output = run_pick_character_with_inputs([choice])

        assert isinstance(player, expected_class)
        assert f"You have chosen the {player.name}!" in output


def test_invalid_character_choice_reprompts_then_returns_valid_selection():
    player, output = run_pick_character_with_inputs(["bad", "2"])

    assert isinstance(player, BlackMage)
    assert "That is not a valid character choice. Please try again." in output
    assert "You have chosen the Black Mage!" in output


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


if __name__ == "__main__":
    test_valid_character_choices_return_expected_classes()
    test_invalid_character_choice_reprompts_then_returns_valid_selection()
    test_avoid_battle_success_behavior_is_unchanged()
    test_avoid_battle_failure_behavior_is_unchanged()
    print("Event character selection tests passed.")

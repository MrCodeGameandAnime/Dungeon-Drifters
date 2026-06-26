import builtins
import contextlib
import io
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import run_game


@contextlib.contextmanager
def patched_game(inputs):
    original_input = builtins.input
    original_randint = random.randint
    original_choice = random.choice
    answers = iter(inputs)

    def fake_input(prompt=""):
        print(prompt, end="")
        return next(answers)

    def fake_randint(start, end):
        if (start, end) == (1, 2):
            return 1  # player initiative
        if (start, end) == (1, 5):
            return 5  # no misses
        if (start, end) == (8, 20):
            return 20  # strong player heavy attack
        if (start, end) == (8, 14):
            return 14
        if (start, end) == (6, 12):
            return 6
        if (start, end) == (1, 10):
            return 10
        return end

    builtins.input = fake_input
    random.randint = fake_randint
    random.choice = lambda items: items[0]

    try:
        yield
    finally:
        builtins.input = original_input
        random.randint = original_randint
        random.choice = original_choice


def test_attack_path_reaches_victory_ending():
    output = io.StringIO()

    with patched_game(["4", "1", "2", "2", "2"]), contextlib.redirect_stdout(output):
        run_game.main()

    text = output.getvalue()
    assert "DUNGEON DRIFTERS" in text
    assert "You have chosen the Monk" in text
    assert "You ready your weapon" in text
    assert "A Goblin blocks your path" in text
    assert "Victory. Your adventure has begun." in text


def test_flee_path_reaches_escape_ending():
    output = io.StringIO()

    with patched_game(["1", "2"]), contextlib.redirect_stdout(output):
        run_game.main()

    text = output.getvalue()
    assert "DUNGEON DRIFTERS" in text
    assert "You have chosen the Brawler" in text
    assert "You escaped in the nick of time" in text
    assert "you break through the brush and escape the ambush" in text


if __name__ == "__main__":
    test_attack_path_reaches_victory_ending()
    test_flee_path_reaches_escape_ending()
    print("Vertical slice smoke test passed.")

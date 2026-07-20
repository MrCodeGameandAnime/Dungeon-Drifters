import builtins
import contextlib
import io
import random
import run_game
import app.game.main_loop as main_loop
import app.world.event as event_module


class FakeConsole:
    @staticmethod
    def wait_for_continue(prompt="Press Enter to continue..."):
        input(prompt)

    @staticmethod
    def clear_console():
        pass


@contextlib.contextmanager
def patched_game(inputs):
    original_input = builtins.input
    original_randint = random.randint
    original_choice = random.choice
    original_main_console = main_loop.console
    original_event_console = event_module.console
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
        if (start, end) == (1, 100):
            return 1
        return end

    builtins.input = fake_input
    random.randint = fake_randint
    random.choice = lambda items: items[0]
    main_loop.console = FakeConsole
    event_module.console = FakeConsole

    try:
        yield
    finally:
        builtins.input = original_input
        random.randint = original_randint
        random.choice = original_choice
        main_loop.console = original_main_console
        event_module.console = original_event_console


def test_attack_path_reaches_victory_ending():
    output = io.StringIO()

    with patched_game([
        "", "4", "Y", "e",
        *("a", "hydro whip") * 4,
        "o", "q", "y",
    ]), contextlib.redirect_stdout(output):
        run_game.main()

    text = output.getvalue()
    assert "A tale from Ketlyv" in text
    assert "You have chosen Joruun Veyr, the Bloody Storm Monk!" in text
    assert "OVERWORLD  |  Goblin Ambush" in text
    assert "A Goblin blocks your path" in text
    assert "Joruun Veyr" in text
    assert "HP 100/100" in text
    assert "OVERWORLD  |  Goblin Pair" in text
    assert "Goblin Ambush is defeated" in text
    assert "The route continues toward Goblin Pair" in text
    assert "Exit this session without saving?" in text


def test_player_can_quit_from_the_initial_overworld_without_starting_battle():
    output = io.StringIO()

    with patched_game(["", "1", "Y", "o", "q", "y"]), contextlib.redirect_stdout(output):
        run_game.main()

    text = output.getvalue()
    assert "A tale from Ketlyv" in text
    assert "You have chosen Ser Branoc, the Unbroken Crest!" in text
    assert "OVERWORLD  |  Goblin Ambush" in text
    assert "Exit this session without saving?" in text
    assert "will go first" not in text

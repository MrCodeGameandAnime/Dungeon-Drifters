import builtins
import contextlib
import io
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.combat.battle import Battle
from app.combat.enemy import Goblin
from app.player.character import Brawler, Monk
from app.player.player_state import PlayerState


@contextlib.contextmanager
def patched_battle(inputs=(), randint=None):
    original_input = builtins.input
    original_randint = random.randint
    original_choice = random.choice
    answers = iter(inputs)

    def fake_input(prompt=""):
        print(prompt, end="")
        return next(answers)

    builtins.input = fake_input
    random.choice = lambda items: items[0]

    if randint is not None:
        random.randint = randint

    try:
        yield
    finally:
        builtins.input = original_input
        random.randint = original_randint
        random.choice = original_choice


def no_misses():
    return False


@contextlib.contextmanager
def patched_misses():
    original_misses = Battle.misses
    Battle.misses = staticmethod(no_misses)

    try:
        yield
    finally:
        Battle.misses = original_misses


def test_battle_accepts_player_state_and_uses_wrapped_character():
    character = Brawler()
    player_state = PlayerState(character)
    battle = Battle(player_state, Goblin())

    assert battle.player_state is player_state
    assert battle.player is character
    assert battle.player.name == character.name
    assert battle.player.moves is character.moves
    assert battle.player.strength == character.strength
    assert battle.player.constitution == character.constitution


def test_enemy_damage_mutates_player_state_health():
    player_state = PlayerState(Brawler())
    battle = Battle(player_state, Goblin())

    def fake_randint(start, end):
        if (start, end) == (6, 12):
            return 6
        return end

    with patched_misses(), patched_battle(randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        battle.enemy_action()

    assert player_state.health.current == player_state.health.maximum - 9


def test_player_recovery_heals_persistent_health_without_exceeding_maximum():
    player_state = PlayerState(Brawler())
    player_state.health.take_damage(5)
    battle = Battle(player_state, Goblin())

    def fake_randint(start, end):
        if (start, end) == (10, 16):
            return 16
        return end

    with patched_battle(randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        battle.heal_player()

    assert player_state.health.current == player_state.health.maximum


def test_battle_starts_from_existing_persistent_health():
    player_state = PlayerState(Brawler())
    player_state.health.take_damage(10)
    Battle(player_state, Goblin())

    assert player_state.health.current == player_state.health.maximum - 10


def test_victory_returns_player():
    player_state = PlayerState(Monk())
    initiative_rolls = 0

    def fake_randint(start, end):
        nonlocal initiative_rolls
        if (start, end) == (1, 2):
            initiative_rolls += 1
            return 1 if initiative_rolls == 1 else 2
        if (start, end) == (8, 20):
            return 20
        return end

    with patched_misses(), patched_battle(inputs=["2", "2", "2", "2"], randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        winner = Battle(player_state, Goblin()).run()

    assert winner == "player"


def test_defeat_returns_enemy_and_persists_player_health():
    player_state = PlayerState(Brawler())
    player_state.health.take_damage(player_state.health.maximum - 5)

    def fake_randint(start, end):
        if (start, end) == (1, 2):
            return 2
        if (start, end) == (6, 12):
            return 12
        return end

    with patched_misses(), patched_battle(randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        winner = Battle(player_state, Goblin()).run()

    assert winner == "enemy"
    assert player_state.health.is_defeated()
    assert player_state.health.current == 0


if __name__ == "__main__":
    test_battle_accepts_player_state_and_uses_wrapped_character()
    test_enemy_damage_mutates_player_state_health()
    test_player_recovery_heals_persistent_health_without_exceeding_maximum()
    test_battle_starts_from_existing_persistent_health()
    test_victory_returns_player()
    test_defeat_returns_enemy_and_persists_player_health()
    print("Battle player state test passed.")

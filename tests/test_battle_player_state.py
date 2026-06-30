import builtins
import contextlib
import io
import random
from app.combat.battle import Battle
from app.combat.enemy import Goblin
from app.combat.enemy_state import EnemyState
from app.player.character import Brawler, Monk
from app.player.player_state import PlayerState
from app.world.character_profiles.roster import get_profile_by_choice


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
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)

    assert battle.player_state is player_state
    assert battle.player is character
    assert battle.foe is enemy_state
    assert battle.player.name == character.name
    assert battle.player.moves is character.moves
    assert battle.player_state.effective_stat("strength") == character.strength
    assert battle.player_state.effective_stat("constitution") == character.constitution
    assert battle.combat_state.turn_count == 0
    assert not hasattr(battle, "foe_health")
    assert not hasattr(battle, "foe_max_hp")


def test_battles_do_not_share_combat_state():
    first_battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))
    second_battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))

    first_battle.combat_state.advance_turn()
    first_battle.combat_state.statuses["burn"] = 2

    assert first_battle.combat_state is not second_battle.combat_state
    assert first_battle.combat_state.turn_count == 1
    assert second_battle.combat_state.turn_count == 0
    assert second_battle.combat_state.statuses == {}


def test_enemy_damage_mutates_player_state_health():
    player_state = PlayerState(Brawler())
    battle = Battle(player_state, EnemyState(Goblin()))

    def fake_randint(start, end):
        if (start, end) == (6, 12):
            return 6
        return end

    with patched_misses(), patched_battle(randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        battle.enemy_action()

    assert player_state.health.current == player_state.health.maximum - 9


def test_player_damage_mutates_enemy_state_health():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)

    def fake_randint(start, end):
        if (start, end) == (8, 14):
            return 8
        return end

    with patched_misses(), patched_battle(randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        battle.attack(player_state, enemy_state, "slash", heavy=False)

    assert enemy_state.health.current == enemy_state.health.maximum - 23


def test_enemy_recovery_mutates_enemy_state_health():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    enemy_state.health.take_damage(45)
    battle = Battle(player_state, enemy_state)

    def fake_randint(start, end):
        if (start, end) == (1, 2):
            return 1
        if (start, end) == (6, 12):
            return 6
        return end

    with patched_battle(randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        battle.enemy_action()

    assert enemy_state.health.current == 23


def test_battle_player_output_uses_canonical_short_identity_when_profile_attached():
    character = get_profile_by_choice("1").create_character()
    player_state = PlayerState(character)
    battle = Battle(player_state, EnemyState(Goblin()))
    output = io.StringIO()

    with patched_misses(), patched_battle(randint=lambda _start, end: end), contextlib.redirect_stdout(output):
        battle.print_health()
        battle.attack(battle.player_state, battle.foe, "slash", heavy=False)
        battle.heal_player()

    text = output.getvalue()
    assert "Ser Branoc health:" in text
    assert "Ser Branoc used slash." in text
    assert "Ser Branoc takes a breath" in text
    assert "Brawler health:" not in text
    assert "Brawler used slash" not in text


def test_player_recovery_heals_persistent_health_without_exceeding_maximum():
    player_state = PlayerState(Brawler())
    player_state.health.take_damage(5)
    battle = Battle(player_state, EnemyState(Goblin()))

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
    Battle(player_state, EnemyState(Goblin()))

    assert player_state.health.current == player_state.health.maximum - 10


def test_victory_returns_player():
    player_state = PlayerState(Monk())
    battle = Battle(player_state, EnemyState(Goblin()))
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
        winner = battle.run()

    assert winner == "player"
    assert battle.combat_state.turn_count == 5


def test_defeat_returns_enemy_and_persists_player_health():
    player_state = PlayerState(Brawler())
    player_state.health.take_damage(player_state.health.maximum - 5)
    battle = Battle(player_state, EnemyState(Goblin()))

    def fake_randint(start, end):
        if (start, end) == (1, 2):
            return 2
        if (start, end) == (6, 12):
            return 12
        return end

    with patched_misses(), patched_battle(randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        winner = battle.run()

    assert winner == "enemy"
    assert player_state.health.is_defeated()
    assert player_state.health.current == 0
    assert battle.combat_state.turn_count == 1


def test_invalid_player_input_does_not_advance_turn_count():
    player_state = PlayerState(Brawler())
    battle = Battle(player_state, EnemyState(Goblin()))

    with patched_misses(), patched_battle(inputs=["bad choice", "1"]), contextlib.redirect_stdout(io.StringIO()):
        battle.player_action()

    assert battle.combat_state.turn_count == 0


def test_completed_actions_advance_turn_count():
    player_state = PlayerState(Brawler())
    battle = Battle(player_state, EnemyState(Goblin()))
    initiative_rolls = 0

    def fake_randint(start, end):
        nonlocal initiative_rolls
        if (start, end) == (1, 2):
            initiative_rolls += 1
            return 1 if initiative_rolls == 1 else 2
        if (start, end) == (8, 14):
            return 14
        return end

    with patched_misses(), patched_battle(inputs=["1", "1", "1"], randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        winner = battle.run()

    assert winner == "player"
    assert battle.combat_state.turn_count == 5


if __name__ == "__main__":
    test_battle_accepts_player_state_and_uses_wrapped_character()
    test_battles_do_not_share_combat_state()
    test_enemy_damage_mutates_player_state_health()
    test_player_damage_mutates_enemy_state_health()
    test_enemy_recovery_mutates_enemy_state_health()
    test_battle_player_output_uses_canonical_short_identity_when_profile_attached()
    test_player_recovery_heals_persistent_health_without_exceeding_maximum()
    test_battle_starts_from_existing_persistent_health()
    test_victory_returns_player()
    test_defeat_returns_enemy_and_persists_player_health()
    test_invalid_player_input_does_not_advance_turn_count()
    test_completed_actions_advance_turn_count()
    print("Battle player state test passed.")

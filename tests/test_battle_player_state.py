import builtins
import contextlib
import io
import random
from types import SimpleNamespace
from app.combat.battle import Battle
from app.combat.move import TargetType
from app.combat.resolver import CombatResolver
from app.combat.result import MoveResult
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
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


def accepted_result():
    return MoveResult(
        accepted=True,
        hit=True,
        move_name="test move",
        resource_spent=0,
        damage=0,
        healing=0,
        statuses_applied=(),
        reason=None,
    )


def rejected_result():
    return MoveResult(
        accepted=False,
        hit=False,
        move_name="test move",
        resource_spent=0,
        damage=0,
        healing=0,
        statuses_applied=(),
        reason="rejected",
    )


class RecordingResolver:
    def __init__(self, *results):
        self._results = list(results)
        self.calls = []

    def resolve_move(self, actor, target, move_name, *, combat_state=None):
        self.calls.append({
            "actor": actor,
            "target": target,
            "move_name": move_name,
            "combat_state": combat_state,
        })
        return self._results.pop(0) if self._results else accepted_result()


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
    assert battle.player_state.effective_stat("strength") == character.strength + 3
    assert battle.player_state.effective_stat("constitution") == character.constitution + 1
    assert battle.combat_state.turn_count == 0
    assert not hasattr(battle, "foe_health")
    assert not hasattr(battle, "foe_max_hp")


def test_battle_creates_combat_resolver_by_default():
    battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))

    assert isinstance(battle.resolver, CombatResolver)


def test_battle_accepts_injected_resolver():
    resolver = object()
    battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()), resolver=resolver)

    assert battle.resolver is resolver


def test_structured_move_helpers_read_player_and_enemy_combat_moves():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)

    assert battle._player_moves() is player_state.combat_moves
    assert battle._enemy_moves() is enemy_state.combat_moves


def test_complete_accepted_action_advances_when_result_is_accepted():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)
    battle.combat_state.activate_defend(enemy_state)

    result = battle._complete_accepted_action(
        player_state,
        opposing_combatants=(enemy_state,),
        result=accepted_result(),
    )

    assert result == 1
    assert battle.combat_state.turn_count == 1
    assert not battle.combat_state.is_defending(enemy_state)


def test_complete_accepted_action_does_nothing_when_result_is_rejected():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)
    battle.combat_state.activate_defend(enemy_state)

    result = battle._complete_accepted_action(
        player_state,
        opposing_combatants=(enemy_state,),
        result=rejected_result(),
    )

    assert result is None
    assert battle.combat_state.turn_count == 0
    assert battle.combat_state.is_defending(enemy_state)


def test_player_main_menu_shows_structured_actions_without_legacy_recover_or_labels():
    battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))
    output = io.StringIO()

    with patched_battle(inputs=["defend", "attack", "1"]), patched_misses(), contextlib.redirect_stdout(output):
        battle.player_action()

    text = output.getvalue()
    assert "1. Attack" in text
    assert "2. Defend" in text
    assert "3. Items" in text
    assert "4. Super" in text
    assert "Recover (restore health)" not in text
    assert "steady attack" not in text
    assert "risky heavy attack" not in text


def test_attack_submenu_displays_non_super_structured_moves_with_resources_and_descriptions():
    player_state = PlayerState(Brawler())
    battle = Battle(player_state, EnemyState(Goblin()))
    output = io.StringIO()

    with patched_battle(inputs=["attack", "1"]), patched_misses(), contextlib.redirect_stdout(output):
        battle.player_action()

    text = output.getvalue()
    non_super_moves = [
        move
        for move in player_state.combat_moves
        if move.resource_type.value != "super"
    ]
    super_moves = [
        move
        for move in player_state.combat_moves
        if move.resource_type.value == "super"
    ]

    for index, move in enumerate(non_super_moves, start=1):
        assert f"{index}. {move.name}" in text
        assert f"[{move.resource_type.value} {move.resource_cost}]" in text
        assert move.description in text

    assert "0. Back" in text
    assert all(move.name not in text for move in super_moves)


def test_super_submenu_displays_super_move_separately_and_routes_to_resolver():
    player_state = PlayerState(Brawler())
    resolver = RecordingResolver(rejected_result(), accepted_result())
    battle = Battle(player_state, EnemyState(Goblin()), resolver=resolver)
    output = io.StringIO()

    with patched_battle(inputs=["super", "1", "0", "attack", "1"]), patched_misses(), contextlib.redirect_stdout(output):
        battle.player_action()

    text = output.getvalue()
    super_move = [
        move
        for move in player_state.combat_moves
        if move.resource_type.value == "super"
    ][0]

    assert "Choose a Super:" in text
    assert f"1. {super_move.name}" in text
    assert f"[{super_move.resource_type.value} {super_move.resource_cost}]" in text
    assert super_move.description in text
    assert "test move failed: rejected" in text
    assert battle.combat_state.turn_count == 0
    assert resolver.calls[0] == {
        "actor": player_state,
        "target": battle.foe,
        "move_name": super_move.name,
        "combat_state": battle.combat_state,
    }


def test_defend_and_items_are_unavailable_and_return_to_main_menu_without_advancing():
    battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))
    output = io.StringIO()

    with patched_battle(inputs=["defend", "items", "attack", "1"]), patched_misses(), contextlib.redirect_stdout(output):
        battle.player_action()

    text = output.getvalue()
    assert "Defend is not available yet." in text
    assert "Items are not available yet." in text
    assert text.count("Choose an action:") == 3
    assert battle.combat_state.turn_count == 0


def test_defend_is_not_a_structured_combat_move():
    player_state = PlayerState(Brawler())

    assert "Defend" not in [move.name for move in player_state.combat_moves]


def test_player_menu_display_does_not_depend_on_legacy_character_moves():
    player_state = PlayerState(Brawler())
    player_state.character.moves = {1: "legacy only"}
    battle = Battle(player_state, EnemyState(Goblin()))
    output = io.StringIO()

    with patched_battle(inputs=["attack", "1"]), patched_misses(), contextlib.redirect_stdout(output):
        battle.player_action()

    text = output.getvalue()
    assert "legacy only" not in text
    assert player_state.combat_moves[0].name in text


def test_attack_and_super_submenus_support_back_and_reprompt_invalid_input():
    battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))
    output = io.StringIO()

    with patched_battle(inputs=["attack", "bad", "0", "super", "bad", "0", "attack", "1"]), patched_misses(), contextlib.redirect_stdout(output):
        battle.player_action()

    text = output.getvalue()
    assert text.count("Choose an attack:") == 3
    assert text.count("Choose a Super:") == 2
    assert text.count("That is not a valid move. Please try again.") == 2
    assert battle.combat_state.turn_count == 0


def test_player_target_helper_uses_move_target_type_and_rejects_unknown_targets():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)

    assert battle._player_target_for_move(SimpleNamespace(target=TargetType.ENEMY)) is enemy_state
    assert battle._player_target_for_move(SimpleNamespace(target=TargetType.SELF)) is player_state
    try:
        battle._player_target_for_move(SimpleNamespace(target="unsupported"))
    except ValueError as error:
        assert str(error) == "Unsupported player move target: 'unsupported'"
    else:
        raise AssertionError("Expected ValueError")


def test_structured_attack_menu_routes_selected_move_through_resolver():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    resolver = RecordingResolver(accepted_result())
    battle = Battle(player_state, enemy_state, resolver=resolver)

    def forbidden_attack(*_args, **_kwargs):
        raise AssertionError("Battle.attack must not be called for player-selected moves")

    def forbidden_heal_player():
        raise AssertionError("Battle.heal_player must not be called for player-selected moves")

    battle.attack = forbidden_attack
    battle.heal_player = forbidden_heal_player
    original_misses = Battle.misses
    Battle.misses = staticmethod(lambda: (_ for _ in ()).throw(AssertionError("Battle.misses must not be called")))

    try:
        with patched_battle(inputs=["attack", "1"]), contextlib.redirect_stdout(io.StringIO()):
            battle.player_action()
    finally:
        Battle.misses = original_misses

    assert resolver.calls == [{
        "actor": player_state,
        "target": enemy_state,
        "move_name": player_state.combat_moves[0].name,
        "combat_state": battle.combat_state,
    }]


def test_self_targeting_player_move_routes_player_state_to_resolver():
    player_state = PlayerState(Brawler())
    self_move = SimpleNamespace(
        name="test self move",
        resource_type=SimpleNamespace(value="none"),
        resource_cost=0,
        description="A test self-targeting move.",
        target=TargetType.SELF,
    )
    player_state.character.combat_moves = [self_move]
    resolver = RecordingResolver(accepted_result())
    battle = Battle(player_state, EnemyState(Goblin()), resolver=resolver)

    with patched_battle(inputs=["attack", "1"]), contextlib.redirect_stdout(io.StringIO()):
        battle.player_action()

    assert resolver.calls == [{
        "actor": player_state,
        "target": player_state,
        "move_name": self_move.name,
        "combat_state": battle.combat_state,
    }]


def test_rejected_player_resolver_result_reprompts_without_completion_or_turn_advance():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    resolver = RecordingResolver(rejected_result(), accepted_result())
    battle = Battle(player_state, enemy_state, resolver=resolver)
    completion_calls = []

    def forbidden_completion(*args, **kwargs):
        completion_calls.append((args, kwargs))
        raise AssertionError("Phase 3 must not complete accepted actions from player_action")

    battle._complete_accepted_action = forbidden_completion

    with patched_battle(inputs=["attack", "1", "1"]), contextlib.redirect_stdout(io.StringIO()):
        battle.player_action()

    assert len(resolver.calls) == 2
    assert completion_calls == []
    assert battle.combat_state.turn_count == 0


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

    assert enemy_state.health.current == enemy_state.health.maximum - 26


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
        if (start, end) == (1, 100):
            return 1
        if (start, end) == (8, 20):
            return 20
        return end

    with patched_misses(), patched_battle(inputs=["attack", "2", "attack", "2", "attack", "2", "attack", "2"], randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        winner = battle.run()

    assert winner == "player"
    assert battle.combat_state.turn_count == 3


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

    with patched_misses(), patched_battle(inputs=["bad choice", "attack", "1"]), contextlib.redirect_stdout(io.StringIO()):
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
        if (start, end) == (1, 100):
            return 1
        if (start, end) == (8, 14):
            return 14
        return end

    with patched_misses(), patched_battle(inputs=["attack", "1", "attack", "1", "attack", "1"], randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        winner = battle.run()

    assert winner == "player"
    assert battle.combat_state.turn_count == 5

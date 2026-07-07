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


def result_with(**overrides):
    values = {
        "accepted": True,
        "hit": True,
        "move_name": "test move",
        "resource_spent": 0,
        "damage": 0,
        "healing": 0,
        "statuses_applied": (),
        "reason": None,
    }
    values.update(overrides)
    return MoveResult(**values)


class RecordingResolver:
    def __init__(self, *results, defend_results=()):
        self._results = list(results)
        self._defend_results = list(defend_results)
        self.calls = []
        self.defend_calls = []

    def resolve_move(self, actor, target, move_name, *, combat_state=None):
        self.calls.append({
            "actor": actor,
            "target": target,
            "move_name": move_name,
            "combat_state": combat_state,
        })
        return self._results.pop(0) if self._results else accepted_result()

    def resolve_defend(self, actor, combat_state):
        self.defend_calls.append({
            "actor": actor,
            "combat_state": combat_state,
        })
        return self._defend_results.pop(0) if self._defend_results else accepted_result()


class LegacyMovesFailingEnemyState(EnemyState):
    @property
    def moves(self):
        raise AssertionError("enemy_action must not read legacy foe.moves")


class ManaBearingEnemyState(EnemyState):
    def __init__(self, enemy_definition, tier=0):
        super().__init__(enemy_definition, tier=tier)
        self.mana_resource.set_maximum(5)
        self.mana_resource.restore(3)


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


def test_result_renderer_prints_actual_damage_healing_miss_rejection_resources_and_statuses():
    battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))
    output = io.StringIO()

    with contextlib.redirect_stdout(output):
        battle._render_move_result(
            result_with(move_name="Cut", damage=7),
            actor=battle.player_state,
            target=battle.foe,
        )
        battle._render_move_result(
            result_with(move_name="Recover", healing=3),
            actor=battle.player_state,
            target=battle.player_state,
        )
        battle._render_move_result(
            result_with(move_name="Whiff", hit=False),
            actor=battle.foe,
            target=battle.player_state,
        )
        battle._render_move_result(
            rejected_result(),
            actor=battle.player_state,
            target=battle.foe,
        )
        battle._render_move_result(
            result_with(
                move_name="Spark",
                resource_spent=4,
                statuses_applied=("burn", "shock"),
            ),
            actor=battle.player_state,
            target=battle.foe,
        )
        battle._render_move_result(
            result_with(move_name="Defend", hit=False),
            actor=battle.player_state,
        )

    text = output.getvalue()
    assert "Brawler used Cut. It dealt 7 damage." in text
    assert "Brawler used Recover. It restored 3 health." in text
    assert "Goblin used Whiff, but missed." in text
    assert "Brawler used test move, but it failed: rejected." in text
    assert "Resource spent: 4." in text
    assert "Statuses applied: burn, shock." in text
    assert "Brawler used Defend." in text
    assert "Defend missed" not in text
    assert "Whiff. It dealt" not in text


def test_player_main_menu_shows_structured_actions_without_legacy_recover_or_labels():
    battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))
    output = io.StringIO()

    with patched_battle(inputs=["defend", "attack", "1"]), contextlib.redirect_stdout(output):
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

    with patched_battle(inputs=["attack", "1"]), contextlib.redirect_stdout(output):
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

    with patched_battle(inputs=["super", "1", "0", "attack", "1"]), contextlib.redirect_stdout(output):
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
    assert "Brawler used test move, but it failed: rejected." in text
    assert battle.combat_state.turn_count == 1
    assert resolver.calls[0] == {
        "actor": player_state,
        "target": battle.foe,
        "move_name": super_move.name,
        "combat_state": battle.combat_state,
    }


def test_items_are_unavailable_and_return_to_main_menu_without_advancing_until_accepted_action():
    battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))
    output = io.StringIO()

    with patched_battle(inputs=["items", "attack", "1"]), contextlib.redirect_stdout(output):
        battle.player_action()

    text = output.getvalue()
    assert "Items are not available yet." in text
    assert text.count("Choose an action:") == 2
    assert battle.combat_state.turn_count == 1


def test_player_defend_routes_through_resolver_and_completes_accepted_action():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    resolver = RecordingResolver(defend_results=(accepted_result(),))
    battle = Battle(player_state, enemy_state, resolver=resolver)

    with patched_battle(inputs=["defend"]), contextlib.redirect_stdout(io.StringIO()):
        accepted = battle.player_action()

    assert accepted is True
    assert resolver.defend_calls == [{
        "actor": player_state,
        "combat_state": battle.combat_state,
    }]
    assert battle.combat_state.turn_count == 1


def test_player_defend_activates_actor_and_clears_opposing_defend_with_real_resolver():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)
    battle.combat_state.activate_defend(enemy_state)

    with patched_battle(inputs=["defend"]), contextlib.redirect_stdout(io.StringIO()):
        accepted = battle.player_action()

    assert accepted is True
    assert battle.combat_state.is_defending(player_state)
    assert not battle.combat_state.is_defending(enemy_state)
    assert battle.combat_state.turn_count == 1


def test_rejected_player_defend_reprompts_without_completion_or_turn_advance():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    resolver = RecordingResolver(accepted_result(), defend_results=(rejected_result(),))
    battle = Battle(player_state, enemy_state, resolver=resolver)
    completion_calls = []
    original_completion = battle._complete_accepted_action

    def record_completion(*args, **kwargs):
        completion_calls.append((args, kwargs))
        return original_completion(*args, **kwargs)

    battle._complete_accepted_action = record_completion

    with patched_battle(inputs=["defend", "attack", "1"]), contextlib.redirect_stdout(io.StringIO()):
        battle.player_action()

    assert len(resolver.defend_calls) == 1
    assert len(resolver.calls) == 1
    assert len(completion_calls) == 1
    assert battle.combat_state.turn_count == 1


def test_rejected_player_move_does_not_clear_defend_or_advance_before_backing_out():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    resolver = RecordingResolver(rejected_result())
    battle = Battle(player_state, enemy_state, resolver=resolver)
    battle.combat_state.activate_defend(enemy_state)

    with patched_battle(inputs=["1", "0"]), contextlib.redirect_stdout(io.StringIO()):
        accepted = battle._player_attack_menu()

    assert accepted is False
    assert battle.combat_state.turn_count == 0
    assert battle.combat_state.is_defending(enemy_state)


def test_defend_is_not_a_structured_combat_move():
    player_state = PlayerState(Brawler())

    assert "Defend" not in [move.name for move in player_state.combat_moves]


def test_player_menu_display_does_not_depend_on_legacy_character_moves():
    player_state = PlayerState(Brawler())
    player_state.character.moves = {1: "legacy only"}
    battle = Battle(player_state, EnemyState(Goblin()))
    output = io.StringIO()

    with patched_battle(inputs=["attack", "1"]), contextlib.redirect_stdout(output):
        battle.player_action()

    text = output.getvalue()
    assert "legacy only" not in text
    assert player_state.combat_moves[0].name in text


def test_attack_and_super_submenus_support_back_and_reprompt_invalid_input():
    battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))
    output = io.StringIO()

    with patched_battle(inputs=["attack", "bad", "0", "super", "bad", "0", "attack", "1"]), contextlib.redirect_stdout(output):
        battle.player_action()

    text = output.getvalue()
    assert text.count("Choose an attack:") == 3
    assert text.count("Choose a Super:") == 2
    assert text.count("That is not a valid move. Please try again.") == 2
    assert battle.combat_state.turn_count == 1


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


def test_enemy_target_helper_uses_move_target_type_and_rejects_unknown_targets():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)

    assert battle._enemy_target_for_move(SimpleNamespace(target=TargetType.ENEMY)) is player_state
    assert battle._enemy_target_for_move(SimpleNamespace(target=TargetType.SELF)) is enemy_state
    try:
        battle._enemy_target_for_move(SimpleNamespace(target="unsupported"))
    except ValueError as error:
        assert str(error) == "Unsupported enemy move target: 'unsupported'"
    else:
        raise AssertionError("Expected ValueError")


def test_structured_attack_menu_routes_selected_move_through_resolver():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    resolver = RecordingResolver(accepted_result())
    battle = Battle(player_state, enemy_state, resolver=resolver)

    with patched_battle(inputs=["attack", "1"]), contextlib.redirect_stdout(io.StringIO()):
        battle.player_action()

    assert resolver.calls == [{
        "actor": player_state,
        "target": enemy_state,
        "move_name": player_state.combat_moves[0].name,
        "combat_state": battle.combat_state,
    }]


def test_legacy_battle_combat_helpers_are_removed():
    assert not hasattr(Battle, "attack")
    assert not hasattr(Battle, "heal_player")
    assert not hasattr(Battle, "misses")


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


def test_rejected_player_resolver_result_reprompts_without_completion_until_accepted_action():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    resolver = RecordingResolver(rejected_result(), accepted_result())
    battle = Battle(player_state, enemy_state, resolver=resolver)
    completion_calls = []

    original_completion = battle._complete_accepted_action

    def record_completion(*args, **kwargs):
        completion_calls.append((args, kwargs))
        return original_completion(*args, **kwargs)

    battle._complete_accepted_action = record_completion

    with patched_battle(inputs=["attack", "1", "1"]), contextlib.redirect_stdout(io.StringIO()):
        battle.player_action()

    assert len(resolver.calls) == 2
    assert len(completion_calls) == 1
    assert battle.combat_state.turn_count == 1


def test_battles_do_not_share_combat_state():
    first_battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))
    second_battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))

    first_battle.combat_state.advance_turn()
    first_battle.combat_state.statuses["burn"] = 2

    assert first_battle.combat_state is not second_battle.combat_state
    assert first_battle.combat_state.turn_count == 1
    assert second_battle.combat_state.turn_count == 0
    assert second_battle.combat_state.statuses == {}


def test_hud_prints_resources_and_temporary_state_when_relevant():
    player_state = PlayerState(Brawler())
    enemy_state = ManaBearingEnemyState(Goblin())
    battle = Battle(player_state, enemy_state)
    player_state.mana_resource.spend(2)
    player_state.super_resource.gain(10)
    enemy_state.super_resource.gain(20)
    battle.combat_state.activate_defend(player_state)
    battle.combat_state.activate_defend(enemy_state)
    battle.combat_state.statuses["burn"] = 1
    battle.combat_state.buffs["guard"] = 1
    battle.combat_state.debuffs["slow"] = 1
    output = io.StringIO()

    with contextlib.redirect_stdout(output):
        battle.print_health()

    text = output.getvalue()
    assert "Brawler HP:" in text
    assert "Brawler Mana:" in text
    assert "Brawler Super: 10/100" in text
    assert "Brawler Defending: yes" in text
    assert "Goblin HP: 60/60" in text
    assert "Goblin Mana: 3/5" in text
    assert "Goblin Super: 20/100" in text
    assert "Goblin Defending: yes" in text
    assert "Statuses: {'burn': 1}" in text
    assert "Buffs: {'guard': 1}" in text
    assert "Debuffs: {'slow': 1}" in text


def test_hud_omits_enemy_mana_and_super_when_not_relevant():
    battle = Battle(PlayerState(Brawler()), EnemyState(Goblin()))
    output = io.StringIO()

    with contextlib.redirect_stdout(output):
        battle.print_health()

    text = output.getvalue()
    assert "Goblin HP: 60/60" in text
    assert "Goblin Mana:" not in text
    assert "Goblin Super:" not in text


def test_enemy_action_routes_authored_combat_move_through_resolver():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    resolver = RecordingResolver(accepted_result())
    battle = Battle(player_state, enemy_state, resolver=resolver)

    with patched_battle(), contextlib.redirect_stdout(io.StringIO()):
        battle.enemy_action()

    assert resolver.calls == [{
        "actor": enemy_state,
        "target": player_state,
        "move_name": enemy_state.combat_moves[0].name,
        "combat_state": battle.combat_state,
    }]


def test_enemy_action_uses_combat_moves_not_legacy_moves():
    player_state = PlayerState(Brawler())
    enemy_state = LegacyMovesFailingEnemyState(Goblin())
    resolver = RecordingResolver(accepted_result())
    battle = Battle(player_state, enemy_state, resolver=resolver)

    with patched_battle(), contextlib.redirect_stdout(io.StringIO()):
        battle.enemy_action()

    assert resolver.calls[0]["move_name"] == enemy_state.combat_moves[0].name


def test_enemy_action_does_not_use_legacy_misses_damage_or_direct_health_mutation():
    player_state = PlayerState(Brawler())
    resolver = RecordingResolver(accepted_result())
    battle = Battle(player_state, EnemyState(Goblin()), resolver=resolver)

    with patched_battle(randint=lambda _start, end: end), contextlib.redirect_stdout(io.StringIO()):
        battle.enemy_action()

    assert player_state.health.current == player_state.health.maximum
    assert len(resolver.calls) == 1


def test_enemy_action_completes_accepted_actions_in_phase_5():
    player_state = PlayerState(Brawler())
    resolver = RecordingResolver(accepted_result())
    battle = Battle(player_state, EnemyState(Goblin()), resolver=resolver)
    completion_calls = []

    original_completion = battle._complete_accepted_action

    def record_completion(*args, **kwargs):
        completion_calls.append((args, kwargs))
        return original_completion(*args, **kwargs)

    battle._complete_accepted_action = record_completion

    with patched_battle(), contextlib.redirect_stdout(io.StringIO()):
        battle.enemy_action()

    assert len(completion_calls) == 1
    assert completion_calls[0][0] == (
        battle.foe,
        (player_state,),
        accepted_result(),
    )
    assert battle.combat_state.turn_count == 1


def test_rejected_enemy_action_does_not_clear_defend_or_advance():
    player_state = PlayerState(Brawler())
    resolver = RecordingResolver(rejected_result())
    battle = Battle(player_state, EnemyState(Goblin()), resolver=resolver)
    battle.combat_state.activate_defend(player_state)

    with patched_battle(), contextlib.redirect_stdout(io.StringIO()):
        accepted = battle.enemy_action()

    assert accepted is False
    assert battle.combat_state.turn_count == 0
    assert battle.combat_state.is_defending(player_state)


def test_run_does_not_advance_turn_outside_accepted_action_completion():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)
    battle.foe.health.take_damage(battle.foe.health.maximum - 1)

    def fake_complete(actor, opposing_combatants):
        battle.foe.health.take_damage(1)
        battle.combat_state.turn_count += 1
        return battle.combat_state.turn_count

    battle.combat_state.complete_accepted_action = fake_complete
    battle.combat_state.advance_turn = lambda: (_ for _ in ()).throw(
        AssertionError("Battle.run must not advance turns directly")
    )

    with patched_battle(inputs=["attack", "1"], randint=lambda _start, _end: 1), contextlib.redirect_stdout(io.StringIO()):
        winner = battle.run()

    assert winner == "player"
    assert battle.combat_state.turn_count == 1


def test_player_damage_mutates_enemy_state_health_through_resolver():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    battle = Battle(player_state, enemy_state)

    def fake_randint(start, end):
        if (start, end) == (1, 100):
            return 1
        return end

    with patched_battle(inputs=["attack", "1"], randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        battle.player_action()

    assert enemy_state.health.current < enemy_state.health.maximum


def test_low_health_enemy_does_not_use_universal_recovery_branch():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())
    enemy_state.health.take_damage(45)
    resolver = RecordingResolver(accepted_result())
    battle = Battle(player_state, enemy_state, resolver=resolver)

    with patched_battle(randint=lambda _start, end: end), contextlib.redirect_stdout(io.StringIO()):
        battle.enemy_action()

    assert enemy_state.health.current == 15
    assert len(resolver.calls) == 1


def test_battle_player_output_uses_canonical_short_identity_when_profile_attached():
    character = get_profile_by_choice("1").create_character()
    player_state = PlayerState(character)
    battle = Battle(player_state, EnemyState(Goblin()))
    output = io.StringIO()

    with contextlib.redirect_stdout(output):
        battle.print_health()
        battle._render_move_result(
            result_with(move_name="Crestgrave Reaping", damage=12),
            actor=battle.player_state,
            target=battle.foe,
        )

    text = output.getvalue()
    assert "Ser Branoc HP:" in text
    assert "Ser Branoc Mana:" in text
    assert "Ser Branoc Super:" in text
    assert "Ser Branoc used Crestgrave Reaping." in text
    assert "Brawler HP:" not in text
    assert "Brawler used Crestgrave Reaping" not in text


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
        return end

    with patched_battle(inputs=["attack", "2", "attack", "2", "attack", "2", "attack", "2"], randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        winner = battle.run()

    assert winner == "player"
    assert battle.combat_state.turn_count == 5


def test_defeat_returns_enemy_and_persists_player_health():
    player_state = PlayerState(Brawler())
    player_state.health.take_damage(player_state.health.maximum - 3)
    battle = Battle(player_state, EnemyState(Goblin()))

    def fake_randint(start, end):
        if (start, end) == (1, 2):
            return 2
        if (start, end) == (1, 100):
            return 1
        return end

    with patched_battle(randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        winner = battle.run()

    assert winner == "enemy"
    assert player_state.health.is_defeated()
    assert player_state.health.current == 0
    assert battle.combat_state.turn_count == 1


def test_invalid_player_input_does_not_advance_turn_count_until_accepted_action():
    player_state = PlayerState(Brawler())
    battle = Battle(player_state, EnemyState(Goblin()))

    with patched_battle(inputs=["bad choice", "attack", "1"]), contextlib.redirect_stdout(io.StringIO()):
        battle.player_action()

    assert battle.combat_state.turn_count == 1


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
        return end

    with patched_battle(inputs=["attack", "4", "attack", "4", "attack", "4", "attack", "4"], randint=fake_randint), contextlib.redirect_stdout(io.StringIO()):
        winner = battle.run()

    assert winner == "player"
    assert battle.combat_state.turn_count == 7

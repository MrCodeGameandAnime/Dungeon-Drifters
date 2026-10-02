import json
import sys

from app.combat.battle import Battle
from app.combat.result import MoveResult
from app.content.catalog import create_enemy_state
from app.game.new_game import create_new_game
from app.game.overworld_session import OverworldSession
from app.presentation.battle_models import InteractionPhase
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget
from app.ui.overworld_ui import ChooseOverworldAction


PYODIDE_VERSION = "314.0.7"
EXPECTED_ENCOUNTERS = (
    "surface_goblin_solo",
    "surface_goblin_pair",
    "surface_warrior_solo",
    "surface_warrior_pair",
    "surface_shaman_solo",
    "surface_shaman_pair",
    "surface_elite_patrol",
    "surface_goblin_lord",
)
EXPECTED_RESTS = (
    "surface_rest_after_warrior_solo",
    "surface_rest_after_shaman_pair",
    "surface_rest_before_goblin_lord",
)
EXPECTED_ROUTE = (
    "surface_goblin_solo",
    "surface_goblin_pair",
    "surface_warrior_solo",
    "surface_rest_after_warrior_solo",
    "surface_warrior_pair",
    "surface_shaman_solo",
    "surface_shaman_pair",
    "surface_rest_after_shaman_pair",
    "surface_elite_patrol",
    "surface_rest_before_goblin_lord",
    "surface_goblin_lord",
    "surface_dungeon_entrance",
)
EXPECTED_COMPOSITIONS = (
    ("goblin",),
    ("goblin", "goblin"),
    ("goblin_warrior",),
    ("goblin_warrior", "goblin_warrior"),
    ("goblin_shaman",),
    ("goblin_shaman", "goblin_shaman"),
    ("goblin_elite", "goblin"),
    ("goblin_lord", "goblin", "goblin_warrior"),
)
EXPECTED_ENCOUNTER_COUNT = 8
EXPECTED_REST_COUNT = 3
EXPECTED_BATTLE_COUNT = 8
EXPECTED_ENEMY_COUNT = 14
MAX_BATTLE_INPUTS = 100


class DeterministicRng:
    def randint(self, start, _end):
        return start

    def choice(self, options):
        return tuple(options)[0]


class DeterministicResolver:
    def resolve_move(
        self,
        actor,
        target,
        move_name,
        *,
        combat_state=None,
        character_run_state=None,
    ):
        del actor, combat_state, character_run_state
        damage = 0
        if hasattr(target, "archetype_id") and target.is_alive():
            damage = target.health.current
            target.health.take_damage(damage)
        return MoveResult(
            accepted=True,
            hit=True,
            move_name=move_name,
            resource_spent=0,
            damage=damage,
            healing=0,
            statuses_applied=(),
            reason=None,
        )


class HeadlessBattleFactory:
    def __init__(self):
        self.battles = []

    def __call__(self, player_state, enemies, *, ui, encounter_label):
        if ui is not None:
            raise AssertionError("route battle must be headless")
        battle = Battle(
            player_state,
            enemies,
            ui=None,
            resolver=DeterministicResolver(),
            rng=DeterministicRng(),
            encounter_label=encounter_label,
        )
        self.battles.append(battle)
        return battle


class HeadlessEnemyFactory:
    def __init__(self):
        self.enemies = []

    def __call__(self, archetype_id, *, tier):
        enemy = create_enemy_state(archetype_id, tier=tier)
        self.enemies.append(enemy)
        return enemy


def _first_enabled(options, label):
    for option in options:
        if option.enabled:
            return option
    raise AssertionError("no enabled " + label + " option")


def _complete_battle(session, first_view):
    view = first_view
    inputs = 0
    while view.interaction_phase is not InteractionPhase.COMPLETE:
        inputs += 1
        if inputs > MAX_BATTLE_INPUTS:
            raise AssertionError("battle exceeded semantic input limit")
        if view.interaction_phase is InteractionPhase.ACTIONS:
            option = _first_enabled(view.action_options, "action")
            view = session.submit(ChooseAction(option.intent))
        elif view.interaction_phase is InteractionPhase.REGULAR_MOVES:
            option = _first_enabled(view.move_options, "move")
            view = session.submit(ChooseMove(option.selection_key))
        elif view.interaction_phase is InteractionPhase.TARGETS:
            option = _first_enabled(view.target_options, "target")
            view = session.submit(ChooseTarget(option.target_id))
        else:
            raise AssertionError("unexpected battle phase: " + str(view.interaction_phase))
    return session.current_view()


def _assert_prefix(actual, expected):
    if tuple(actual) != tuple(expected[: len(actual)]):
        raise AssertionError("route prefix mismatch")


def _assert_live_route_state(game, session, encounter_ids, rest_ids):
    if game.world_state.defeated_encounters != tuple(encounter_ids):
        raise AssertionError("defeated encounter prefix mismatch")
    if game.overworld_state.resolved_rest_node_ids != tuple(rest_ids):
        raise AssertionError("resolved Rest prefix mismatch")
    if session.active_battle is not None:
        raise AssertionError("active battle remained after route advancement")


def _qualify_route():
    game = create_new_game("branoc")
    battle_factory = HeadlessBattleFactory()
    enemy_factory = HeadlessEnemyFactory()
    session = OverworldSession(
        game,
        ui=None,
        battle_factory=battle_factory,
        enemy_factory=enemy_factory,
        battle_ui_factory=None,
        save_repository=None,
    )

    route_trace = []
    encounter_ids = []
    rest_ids = []
    view = session.current_view()
    while not game.overworld_state.route_complete:
        node_id = game.overworld_state.current_route_node_id
        if not route_trace or route_trace[-1] != node_id:
            route_trace.append(node_id)

        if view.screen is OverworldScreen.REST:
            expected_rest = EXPECTED_RESTS[len(rest_ids)]
            if node_id != expected_rest:
                raise AssertionError("unexpected Rest node")
            view = session.submit(ChooseOverworldAction(OverworldAction.REST))
            if view.screen is not OverworldScreen.MAIN:
                raise AssertionError("Rest did not return to MAIN")
            rest_ids.append(node_id)
            _assert_prefix(rest_ids, EXPECTED_RESTS)
            _assert_live_route_state(game, session, encounter_ids, rest_ids)
            continue

        if view.screen is not OverworldScreen.MAIN:
            raise AssertionError("route view is not MAIN")
        route_option = view.contextual_route_option
        if route_option is None:
            raise AssertionError("route option is missing")
        if route_option.action is OverworldAction.ENTER_ENCOUNTER:
            expected_encounter = EXPECTED_ENCOUNTERS[len(encounter_ids)]
            if node_id != expected_encounter:
                raise AssertionError("unexpected encounter node")
            encounter_ids.append(node_id)
            battle_view = session.submit(ChooseOverworldAction(route_option.action))
            view = _complete_battle(session, battle_view)
            _assert_prefix(encounter_ids, EXPECTED_ENCOUNTERS)
            _assert_live_route_state(game, session, encounter_ids, rest_ids)
            continue

        if route_option.action is OverworldAction.REST:
            expected_rest = EXPECTED_RESTS[len(rest_ids)]
            if node_id != expected_rest:
                raise AssertionError("unexpected Rest transition")
            rest_view = session.submit(ChooseOverworldAction(OverworldAction.REST))
            if rest_view.screen is not OverworldScreen.REST:
                raise AssertionError("Rest transition did not open REST")
            view = session.submit(ChooseOverworldAction(OverworldAction.REST))
            if view.screen is not OverworldScreen.MAIN:
                raise AssertionError("Rest resolution did not return to MAIN")
            rest_ids.append(node_id)
            _assert_prefix(rest_ids, EXPECTED_RESTS)
            _assert_live_route_state(game, session, encounter_ids, rest_ids)
            continue

        raise AssertionError("unexpected route action: " + str(route_option.action))

    route_trace.append(game.overworld_state.current_route_node_id)
    if tuple(route_trace) != EXPECTED_ROUTE:
        raise AssertionError("full route sequence mismatch")
    if tuple(encounter_ids) != EXPECTED_ENCOUNTERS:
        raise AssertionError("encounter sequence mismatch")
    if tuple(rest_ids) != EXPECTED_RESTS:
        raise AssertionError("Rest sequence mismatch")
    if len(battle_factory.battles) != EXPECTED_BATTLE_COUNT:
        raise AssertionError("unexpected Battle count")
    if len(enemy_factory.enemies) != EXPECTED_ENEMY_COUNT:
        raise AssertionError("unexpected EnemyState count")
    compositions = tuple(
        tuple(enemy.archetype_id for enemy in battle.enemies)
        for battle in battle_factory.battles
    )
    if compositions != EXPECTED_COMPOSITIONS:
        raise AssertionError("battle compositions mismatch")
    for index, enemy in enumerate(enemy_factory.enemies):
        for previous in enemy_factory.enemies[:index]:
            if enemy is previous:
                raise AssertionError("route reused an EnemyState instance")
    if not all(
        battle.interaction_phase is InteractionPhase.COMPLETE
        for battle in battle_factory.battles
    ):
        raise AssertionError("not all route Battles completed")

    final_view = session.current_view()
    if final_view.screen is not OverworldScreen.MAIN:
        raise AssertionError("final route screen is not MAIN")
    if final_view.contextual_route_option is not None:
        raise AssertionError("final route still offers an action")
    if game.overworld_state.current_route_node_id != "surface_dungeon_entrance":
        raise AssertionError("Dungeon Entrance was not reached")
    if not game.overworld_state.route_complete:
        raise AssertionError("route did not complete")
    if not game.overworld_state.dungeon_entrance_reached:
        raise AssertionError("Dungeon Entrance flag was not set")
    if game.player_state.level_state.current != 9:
        raise AssertionError("unexpected final level")
    if game.player_state.exp_state.current != 68:
        raise AssertionError("unexpected final EXP")
    if game.player_state.growth_points != 24:
        raise AssertionError("unexpected final Growth Points")
    if game.player_state.gold != 75:
        raise AssertionError("unexpected final gold")
    if session.active_battle is not None:
        raise AssertionError("active Battle remained at Dungeon Entrance")
    if session._save_repository is not None:
        raise AssertionError("route materialized persistence")

    return {
        "route_nodes": len(route_trace),
        "encounters": len(encounter_ids),
        "rests": len(rest_ids),
        "battles": len(battle_factory.battles),
        "enemies": len(enemy_factory.enemies),
        "final_node": game.overworld_state.current_route_node_id,
        "level": game.player_state.level_state.current,
        "exp": game.player_state.exp_state.current,
        "growth_points": game.player_state.growth_points,
        "gold": game.player_state.gold,
    }


def boot():
    result = _qualify_route()
    result.update(
        {
            "pyodide_version": PYODIDE_VERSION,
            "python_version": sys.version.split()[0],
        }
    )
    return json.dumps(result)

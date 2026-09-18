"""Progressive raw MicroPython probe for the Dungeon Drifters runtime."""

import gc
import sys


STATE = {}


_ROUTE_NODE_IDS = (
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
_EXPECTED_ENCOUNTERS = (
    "surface_goblin_solo",
    "surface_goblin_pair",
    "surface_warrior_solo",
    "surface_warrior_pair",
    "surface_shaman_solo",
    "surface_shaman_pair",
    "surface_elite_patrol",
    "surface_goblin_lord",
)
_EXPECTED_RESTS = (
    "surface_rest_after_warrior_solo",
    "surface_rest_after_shaman_pair",
    "surface_rest_before_goblin_lord",
)
_EXPECTED_COMPOSITIONS = (
    ("goblin",),
    ("goblin", "goblin"),
    ("goblin_warrior",),
    ("goblin_warrior", "goblin_warrior"),
    ("goblin_shaman",),
    ("goblin_shaman", "goblin_shaman"),
    ("goblin_elite", "goblin"),
    ("goblin_lord", "goblin", "goblin_warrior"),
)
_EXPECTED_ENEMY_COUNT = 14
_EXPECTED_FINAL_NODE = "surface_dungeon_entrance"
_EXPECTED_PROGRESS = (9, 68, 24, 75)


def _emit_memory(label):
    try:
        gc.collect()
        free = gc.mem_free()
        allocated = gc.mem_alloc()
    except (AttributeError, TypeError):
        print("MYP|MEMORY|UNAVAILABLE")
        return
    print("MYP|MEMORY|%s|FREE|%s|ALLOC|%s" % (label, free, allocated))


def _run_stage(name, operation):
    print("MYP|%s|BEGIN" % name)
    _emit_memory("%s|BEFORE" % name)
    try:
        operation()
    except Exception as error:
        print(
            "MYP|%s|FAIL|%s|%s"
            % (name, type(error).__name__, str(error))
        )
        _emit_memory("%s|FAIL" % name)
        raise
    _emit_memory("%s|AFTER" % name)
    print("MYP|%s|PASS" % name)


def _version_text():
    implementation = getattr(sys, "implementation", None)
    version = getattr(implementation, "version", None)
    if isinstance(version, tuple):
        return ".".join(str(part) for part in version[:3])
    return str(version)


def _boot():
    implementation = getattr(sys, "implementation", None)
    print("MYP|IMPLEMENTATION|%s" % getattr(implementation, "name", "unknown"))
    print("MYP|VERSION|%s" % _version_text())
    print("MYP|PLATFORM|%s" % getattr(sys, "platform", "unknown"))


def _configure_source_path():
    source_path = sys.argv[1]
    sys.path.append(source_path)
    STATE["source_path"] = source_path


def _import_catalog():
    import app.content.catalog

    STATE["catalog"] = app.content.catalog


def _resolve_branoc():
    spec = STATE["catalog"].get_drifter_spec("branoc")
    if spec.drifter_id != "branoc":
        raise AssertionError("catalog resolved the wrong Drifter")
    STATE["drifter_spec"] = spec


def _create_game():
    from app.game.new_game import create_new_game

    STATE["game"] = create_new_game("branoc")


def _resolve_first_encounter():
    encounter = STATE["catalog"].get_encounter_spec("surface_goblin_solo")
    if encounter.enemy_archetype_ids != ("goblin",):
        raise AssertionError("unexpected first encounter composition")
    STATE["encounter"] = encounter


def _construct_enemies():
    STATE["enemies"] = tuple(
        STATE["catalog"].create_enemy_state(archetype_id, tier=0)
        for archetype_id in STATE["encounter"].enemy_archetype_ids
    )


class _DeterministicRng:
    def randint(self, start, _end):
        return start

    def choice(self, options):
        return tuple(options)[0]


class _RouteDeterministicResolver:
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
        from app.combat.result import MoveResult

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


class _RouteBattleFactory:
    def __init__(self):
        self.battles = []

    def __call__(self, player_state, enemies, *, ui, encounter_label):
        from app.combat.battle import Battle

        battle = Battle(
            player_state,
            enemies,
            ui=ui,
            resolver=_RouteDeterministicResolver(),
            rng=_DeterministicRng(),
            encounter_label=encounter_label,
        )
        self.battles.append(battle)
        return battle


class _RouteEnemyFactory:
    def __init__(self, factory):
        self._factory = factory
        self.enemies = []

    def __call__(self, archetype_id, *, tier):
        enemy = self._factory(archetype_id, tier=tier)
        self.enemies.append(enemy)
        return enemy


def _construct_battle():
    from app.combat.battle import Battle

    STATE["battle"] = Battle(
        STATE["game"].player_state,
        STATE["enemies"],
        ui=None,
        rng=_DeterministicRng(),
        encounter_label="MYP0 First Encounter",
    )


def _obtain_first_battle_view():
    view = STATE["battle"].current_view()
    if view is None:
        raise AssertionError("Battle did not produce a view")
    STATE["battle_view"] = view


def _first_enabled(options):
    for option in options:
        if option.enabled:
            return option
    raise AssertionError("no enabled option was offered")


def _submit_semantic_battle_input():
    from app.presentation.battle_models import InteractionPhase
    from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget

    battle = STATE["battle"]
    view = battle.current_view()
    if view.interaction_phase is InteractionPhase.COMPLETE:
        STATE["battle_view"] = view
        return
    if view.interaction_phase is InteractionPhase.ACTIONS:
        next_view = battle.submit(ChooseAction("attack"))
    elif view.interaction_phase is InteractionPhase.REGULAR_MOVES:
        option = _first_enabled(view.move_options)
        next_view = battle.submit(ChooseMove(option.selection_key))
    elif view.interaction_phase is InteractionPhase.TARGETS:
        option = _first_enabled(view.target_options)
        next_view = battle.submit(ChooseTarget(option.target_id))
    else:
        raise AssertionError(
            "unexpected first-encounter battle phase: %s"
            % view.interaction_phase
        )
    STATE["battle_view"] = next_view


def _complete_first_battle():
    from app.presentation.battle_models import InteractionPhase

    for _ in range(100):
        if STATE["battle"].is_complete:
            break
        _submit_semantic_battle_input()
    if not STATE["battle"].is_complete:
        raise AssertionError("first Battle did not complete within 100 inputs")
    if STATE["battle"].winner != "player":
        raise AssertionError("first Battle did not produce player victory")
    if STATE["battle_view"].interaction_phase is not InteractionPhase.COMPLETE:
        raise AssertionError("completed Battle did not produce an inactive view")


def _import_overworld_session():
    from app.game.overworld_session import OverworldSession

    STATE["overworld_session_type"] = OverworldSession


def _construct_headless_session():
    session = STATE["overworld_session_type"](
        STATE["game"],
        battle_factory=STATE["battle"].__class__,
        enemy_factory=STATE["catalog"].create_enemy_state,
        ui=None,
        battle_ui_factory=None,
    )
    STATE["session"] = session


def _obtain_session_view():
    view = STATE["session"].current_view()
    if view is None:
        raise AssertionError("session did not produce a view")
    STATE["session_view"] = view


def _enter_first_session_encounter():
    from app.presentation.overworld_models import OverworldAction
    from app.ui.overworld_ui import ChooseOverworldAction

    view = STATE["session"].current_view()
    if view.contextual_route_option.action is not OverworldAction.ENTER_ENCOUNTER:
        raise AssertionError("first session view did not offer encounter entry")
    STATE["session_battle_view"] = STATE["session"].submit(
        ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
    )


def _complete_first_session_encounter():
    from app.presentation.battle_models import InteractionPhase
    from app.presentation.overworld_models import OverworldScreen
    from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget

    session = STATE["session"]
    view = STATE["session_battle_view"]
    for _ in range(100):
        if view.interaction_phase is InteractionPhase.COMPLETE:
            break
        if view.interaction_phase is InteractionPhase.ACTIONS:
            view = session.submit(ChooseAction("attack"))
        elif view.interaction_phase is InteractionPhase.REGULAR_MOVES:
            option = _first_enabled(view.move_options)
            view = session.submit(ChooseMove(option.selection_key))
        elif view.interaction_phase is InteractionPhase.TARGETS:
            option = _first_enabled(view.target_options)
            view = session.submit(ChooseTarget(option.target_id))
        else:
            raise AssertionError(
                "unexpected session battle phase: %s" % view.interaction_phase
            )
    if view.interaction_phase is not InteractionPhase.COMPLETE:
        raise AssertionError("session Battle did not complete")
    next_view = session.current_view()
    if next_view.screen not in (OverworldScreen.MAIN, OverworldScreen.REST):
        raise AssertionError("session did not return to the overworld")
    if STATE["game"].world_state.defeated_encounters != (
        "surface_goblin_solo",
    ):
        raise AssertionError("session did not finalize the first encounter")


def _construct_route_qualification():
    from app.game.new_game import create_new_game
    from app.game.overworld_session import OverworldSession

    game = create_new_game("branoc")
    battle_factory = _RouteBattleFactory()
    enemy_factory = _RouteEnemyFactory(STATE["catalog"].create_enemy_state)
    session = OverworldSession(
        game,
        battle_factory=battle_factory,
        enemy_factory=enemy_factory,
        ui=None,
        battle_ui_factory=None,
        save_repository=None,
    )
    STATE["route_game"] = game
    STATE["route_session"] = session
    STATE["route_battle_factory"] = battle_factory
    STATE["route_enemy_factory"] = enemy_factory


def _obtain_route_initial_view():
    from app.presentation.overworld_models import OverworldAction, OverworldScreen

    view = STATE["route_session"].current_view()
    if view.screen is not OverworldScreen.MAIN:
        raise AssertionError("route did not begin on the overworld main screen")
    if STATE["route_game"].overworld_state.current_route_node_id != _ROUTE_NODE_IDS[0]:
        raise AssertionError("route did not begin at the authored first node")
    if view.contextual_route_option.action is not OverworldAction.ENTER_ENCOUNTER:
        raise AssertionError("route did not offer its first encounter")
    STATE["route_initial_view"] = view


def _first_enabled_option(options):
    for option in options:
        if option.enabled:
            return option
    raise AssertionError("route Battle offered no enabled option")


def _complete_route_battle(first_view):
    from app.presentation.battle_models import InteractionPhase
    from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget

    view = first_view
    for _ in range(100):
        if view.interaction_phase is InteractionPhase.COMPLETE:
            break
        if view.interaction_phase is InteractionPhase.ACTIONS:
            view = STATE["route_session"].submit(ChooseAction("attack"))
        elif view.interaction_phase is InteractionPhase.REGULAR_MOVES:
            option = _first_enabled_option(view.move_options)
            view = STATE["route_session"].submit(
                ChooseMove(option.selection_key)
            )
        elif view.interaction_phase is InteractionPhase.TARGETS:
            option = _first_enabled_option(view.target_options)
            view = STATE["route_session"].submit(
                ChooseTarget(option.target_id)
            )
        else:
            raise AssertionError(
                "unexpected route Battle phase: %s" % view.interaction_phase
            )
    if view.interaction_phase is not InteractionPhase.COMPLETE:
        raise AssertionError("route Battle did not complete within 100 inputs")
    return STATE["route_session"].current_view()


def _assert_enemy_identity_is_fresh(enemies):
    for index, enemy in enumerate(enemies):
        for previous in enemies[:index]:
            if enemy is previous:
                raise AssertionError("route reused an EnemyState instance")


def _run_route_node(node_id, operation):
    print("MYP|ROUTE|%s|BEGIN" % node_id)
    _emit_memory("ROUTE|%s|BEFORE" % node_id)
    try:
        operation()
    except Exception as error:
        print(
            "MYP|ROUTE|%s|FAIL|%s|%s"
            % (node_id, type(error).__name__, str(error))
        )
        _emit_memory("ROUTE|%s|FAIL" % node_id)
        raise
    _emit_memory("ROUTE|%s|AFTER" % node_id)
    print("MYP|ROUTE|%s|PASS" % node_id)


def _drive_route_encounter(node_id, encounter_index):
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseOverworldAction

    session = STATE["route_session"]
    game = STATE["route_game"]
    view = session.current_view()
    if view.screen is not OverworldScreen.MAIN:
        raise AssertionError("encounter node did not present the MAIN screen")
    if game.overworld_state.current_route_node_id != node_id:
        raise AssertionError("route node did not match expected encounter")
    if view.contextual_route_option.action is not OverworldAction.ENTER_ENCOUNTER:
        raise AssertionError("encounter node did not offer encounter entry")

    before_defeated = game.world_state.defeated_encounters
    battle_view = session.submit(
        ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
    )
    final_view = _complete_route_battle(battle_view)
    if session.active_battle is not None:
        raise AssertionError("completed route Battle remained active")
    expected_defeated = _EXPECTED_ENCOUNTERS[: encounter_index + 1]
    if game.world_state.defeated_encounters != expected_defeated:
        raise AssertionError("encounter prefix was not preserved")
    if len(game.world_state.defeated_encounters) != len(before_defeated) + 1:
        raise AssertionError("encounter was not finalized exactly once")
    expected_next = _ROUTE_NODE_IDS[_ROUTE_NODE_IDS.index(node_id) + 1]
    if game.overworld_state.current_route_node_id != expected_next:
        raise AssertionError("route did not advance to its immediate successor")
    if final_view.screen not in (OverworldScreen.MAIN, OverworldScreen.REST):
        raise AssertionError("completed encounter returned an invalid screen")


def _drive_route_rest(node_id, rest_index):
    from app.presentation.overworld_models import OverworldScreen, OverworldAction
    from app.ui.overworld_ui import ChooseOverworldAction

    session = STATE["route_session"]
    game = STATE["route_game"]
    view = session.current_view()
    if view.screen is not OverworldScreen.REST:
        raise AssertionError("Rest node did not present the REST screen")
    if game.overworld_state.current_route_node_id != node_id:
        raise AssertionError("route node did not match expected Rest")
    session.submit(ChooseOverworldAction(OverworldAction.REST))
    view = session.current_view()
    if view.screen is not OverworldScreen.MAIN:
        raise AssertionError("resolved Rest did not return to MAIN")
    if game.overworld_state.resolved_rest_node_ids != _EXPECTED_RESTS[: rest_index + 1]:
        raise AssertionError("Rest prefix was not preserved")
    expected_next = _ROUTE_NODE_IDS[_ROUTE_NODE_IDS.index(node_id) + 1]
    if game.overworld_state.current_route_node_id != expected_next:
        raise AssertionError("Rest did not advance to its immediate successor")


def _complete_surface_route():
    encounter_index = 0
    rest_index = 0
    for node_id in _ROUTE_NODE_IDS:
        if node_id == _EXPECTED_FINAL_NODE:
            def verify_final_node():
                from app.presentation.overworld_models import OverworldScreen

                view = STATE["route_session"].current_view()
                if view.screen is not OverworldScreen.MAIN:
                    raise AssertionError("Dungeon Entrance did not present MAIN")
                if STATE["route_game"].overworld_state.current_route_node_id != node_id:
                    raise AssertionError("route ended at the wrong node")
                if not STATE["route_game"].overworld_state.route_complete:
                    raise AssertionError("route did not complete at Dungeon Entrance")
                if view.contextual_route_option is not None:
                    raise AssertionError("Dungeon Entrance offered another action")

            _run_route_node(node_id, verify_final_node)
            continue

        if node_id in _EXPECTED_RESTS:
            _run_route_node(
                node_id,
                lambda node_id=node_id, rest_index=rest_index: _drive_route_rest(
                    node_id,
                    rest_index,
                ),
            )
            rest_index += 1
        else:
            _run_route_node(
                node_id,
                lambda node_id=node_id, encounter_index=encounter_index: _drive_route_encounter(
                    node_id,
                    encounter_index,
                ),
            )
            encounter_index += 1


def _assert_route_final_state():
    from app.presentation.battle_models import InteractionPhase
    from app.presentation.overworld_models import OverworldScreen

    game = STATE["route_game"]
    session = STATE["route_session"]
    battles = STATE["route_battle_factory"].battles
    enemies = STATE["route_enemy_factory"].enemies
    if len(battles) != len(_EXPECTED_ENCOUNTERS):
        raise AssertionError("unexpected route Battle count")
    if len(enemies) != _EXPECTED_ENEMY_COUNT:
        raise AssertionError("unexpected route EnemyState count")
    _assert_enemy_identity_is_fresh(enemies)
    if tuple(
        tuple(enemy.archetype_id for enemy in battle.enemies)
        for battle in battles
    ) != _EXPECTED_COMPOSITIONS:
        raise AssertionError("route Battle compositions changed")
    if not all(
        battle.interaction_phase is InteractionPhase.COMPLETE
        for battle in battles
    ):
        raise AssertionError("a route Battle did not complete")
    if session.active_battle is not None:
        raise AssertionError("route session retained an active Battle")
    if game.world_state.defeated_encounters != _EXPECTED_ENCOUNTERS:
        raise AssertionError("final defeated encounter state changed")
    if game.overworld_state.resolved_rest_node_ids != _EXPECTED_RESTS:
        raise AssertionError("final Rest state changed")
    if game.overworld_state.current_route_node_id != _EXPECTED_FINAL_NODE:
        raise AssertionError("final route node changed")
    if not game.overworld_state.route_complete:
        raise AssertionError("final route state is incomplete")
    if not game.overworld_state.dungeon_entrance_reached:
        raise AssertionError("Dungeon Entrance was not reached")
    player = game.player_state
    if (
        player.level_state.current,
        player.exp_state.current,
        player.growth_points,
        player.gold,
    ) != _EXPECTED_PROGRESS:
        raise AssertionError("final player progression changed")
    final_view = session.current_view()
    if final_view.screen is not OverworldScreen.MAIN:
        raise AssertionError("final route view did not return MAIN")
    if final_view.contextual_route_option is not None:
        raise AssertionError("final route view offered another action")
    if session._save_repository is not None:
        raise AssertionError("route qualification materialized persistence")


def _assert_route_live_state():
    from app.presentation.overworld_models import OverworldScreen

    game = STATE["route_game"]
    session = STATE["route_session"]
    if session.active_battle is not None:
        raise AssertionError("route session retained an active Battle")
    if game.overworld_state.current_route_node_id != _EXPECTED_FINAL_NODE:
        raise AssertionError("live route node changed during evidence cleanup")
    if not game.overworld_state.route_complete:
        raise AssertionError("live route became incomplete during cleanup")
    if not game.overworld_state.dungeon_entrance_reached:
        raise AssertionError("Dungeon Entrance state changed during cleanup")
    if game.world_state.defeated_encounters != _EXPECTED_ENCOUNTERS:
        raise AssertionError("defeated encounters changed during cleanup")
    if game.overworld_state.resolved_rest_node_ids != _EXPECTED_RESTS:
        raise AssertionError("resolved Rests changed during cleanup")
    player = game.player_state
    if (
        player.level_state.current,
        player.exp_state.current,
        player.growth_points,
        player.gold,
    ) != _EXPECTED_PROGRESS:
        raise AssertionError("player progression changed during cleanup")
    view = session.current_view()
    if view.screen is not OverworldScreen.MAIN:
        raise AssertionError("live route view changed during evidence cleanup")
    if view.contextual_route_option is not None:
        raise AssertionError("live route offered another action after cleanup")
    if session._save_repository is not None:
        raise AssertionError("evidence cleanup materialized persistence")


def _release_route_evidence():
    del STATE["route_battle_factory"].battles[:]
    del STATE["route_enemy_factory"].enemies[:]
    del STATE["route_initial_view"]
    _assert_route_live_state()


def _teardown_route_session():
    del STATE["route_game"]
    del STATE["route_session"]
    del STATE["route_battle_factory"]
    del STATE["route_enemy_factory"]


def main():
    if len(sys.argv) != 2:
        print("MYP|USAGE|FAIL|expected exactly one DD source directory")
        raise SystemExit(2)

    print("MYP|BOOT|PASS")
    _boot()
    _emit_memory("BOOT")

    _run_stage("SOURCE_PATH", _configure_source_path)
    _run_stage("CATALOG_IMPORT", _import_catalog)
    _run_stage("DRIFTER_SPEC", _resolve_branoc)
    _run_stage("NEW_GAME", _create_game)
    _run_stage("FIRST_ENCOUNTER", _resolve_first_encounter)
    _run_stage("ENEMY_STATE", _construct_enemies)
    _run_stage("BATTLE_CONSTRUCTION", _construct_battle)
    _run_stage("BATTLE_VIEW", _obtain_first_battle_view)
    _run_stage("BATTLE_INPUT", _submit_semantic_battle_input)
    _run_stage("BATTLE_COMPLETE", _complete_first_battle)
    _run_stage("SESSION_IMPORT", _import_overworld_session)
    _run_stage("SESSION_CONSTRUCTION", _construct_headless_session)
    _run_stage("SESSION_VIEW", _obtain_session_view)
    _run_stage("SESSION_ENCOUNTER_ENTRY", _enter_first_session_encounter)
    _run_stage("SESSION_ENCOUNTER_COMPLETE", _complete_first_session_encounter)
    _run_stage("ROUTE_CONSTRUCTION", _construct_route_qualification)
    _run_stage("ROUTE_INITIAL_VIEW", _obtain_route_initial_view)
    _run_stage("SURFACE_ROUTE_COMPLETE", _complete_surface_route)
    _run_stage("ROUTE_FINAL_STATE", _assert_route_final_state)
    _run_stage("ROUTE_EVIDENCE_RELEASE", _release_route_evidence)
    _run_stage("ROUTE_SESSION_TEARDOWN", _teardown_route_session)

    print("MYP|RESULT|RAW_PROBE_STAGES_COMPLETE")


main()

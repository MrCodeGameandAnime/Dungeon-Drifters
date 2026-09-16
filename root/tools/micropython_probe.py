"""Progressive raw MicroPython probe for the Dungeon Drifters runtime."""

import gc
import sys


STATE = {}


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

    print("MYP|RESULT|RAW_PROBE_STAGES_COMPLETE")


main()

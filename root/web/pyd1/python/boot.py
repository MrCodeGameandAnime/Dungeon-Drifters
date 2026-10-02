import json
import sys

from app.combat.battle import Battle
from app.content.catalog import create_enemy_state
from app.game.new_game import create_new_game
from app.game.overworld_session import OverworldSession
from app.presentation.battle_models import InteractionPhase
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget
from app.ui.overworld_ui import ChooseOverworldAction


PYODIDE_VERSION = "314.0.7"
MAX_BATTLE_INPUTS = 100


def _first_enabled(options, label):
    for option in options:
        if option.enabled:
            return option
    raise AssertionError("no enabled " + label + " option")


def _drive_battle(session, view):
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
            raise AssertionError(
                "unexpected Battle phase: " + str(view.interaction_phase)
            )
    return session.current_view(), inputs


def boot():
    game = create_new_game("branoc")
    session = OverworldSession(
        game,
        ui=None,
        battle_factory=Battle,
        enemy_factory=create_enemy_state,
        battle_ui_factory=None,
        save_repository=None,
    )

    initial_view = session.current_view()
    if initial_view.screen is not OverworldScreen.MAIN:
        raise AssertionError("initial session screen is not MAIN")
    if game.overworld_state.current_route_node_id != "surface_goblin_solo":
        raise AssertionError("unexpected initial route node")
    route_option = initial_view.contextual_route_option
    if route_option is None or route_option.action is not OverworldAction.ENTER_ENCOUNTER:
        raise AssertionError("initial encounter is not offered")

    battle_view = session.submit(
        ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
    )
    if not hasattr(battle_view, "interaction_phase"):
        raise AssertionError("encounter entry did not produce a BattleView")
    final_view, input_count = _drive_battle(session, battle_view)

    if game.world_state.defeated_encounters != ("surface_goblin_solo",):
        raise AssertionError("first encounter was not defeated exactly once")
    if session.active_battle is not None:
        raise AssertionError("active battle remained after completion")
    if session._save_repository is not None:
        raise AssertionError("headless session materialized persistence")
    if final_view.screen is not OverworldScreen.MAIN:
        raise AssertionError("post-battle view is not MAIN")

    return json.dumps(
        {
            "pyodide_version": PYODIDE_VERSION,
            "python_version": sys.version.split()[0],
            "initial_screen": initial_view.screen.value,
            "initial_route_node": game.world_state.defeated_encounters[0]
            if game.world_state.defeated_encounters
            else "surface_goblin_solo",
            "encounter_entry": "surface_goblin_solo",
            "battle_inputs": input_count,
            "completed_encounter": game.world_state.defeated_encounters[-1],
        }
    )

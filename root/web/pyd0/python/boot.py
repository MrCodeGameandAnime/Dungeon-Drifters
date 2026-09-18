import importlib
import json
import sys


REQUIRED_MODULES = (
    "app.game.new_game",
    "app.game.overworld_session",
    "app.combat.battle",
    "app.content.catalog",
)


def boot():
    for module_name in REQUIRED_MODULES:
        importlib.import_module(module_name)

    from app.game.new_game import create_new_game

    game = create_new_game("branoc")
    return json.dumps(
        {
            "pyodide_version": "314.0.7",
            "python_version": sys.version.split()[0],
            "drifter_id": game.player_state.character.profile.drifter_id,
            "game_state": type(game).__name__,
            "imports": list(REQUIRED_MODULES),
        }
    )

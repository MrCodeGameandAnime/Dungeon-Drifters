from app.combat.battle import Battle
from app.content.catalog import create_enemy_state
from app.game import console
from app.game.new_game import create_new_game
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.persistence.bootstrap import build_default_save_port
from app.persistence.ports import SaveLoadStatus
from app.ui.terminal_battle_ui import TerminalBattleUI
from app.ui.terminal_overworld_ui import TerminalOverworldUI
from app.world.event import Events
from app.world.story import StoryElements


def _new_game_state():
    story = StoryElements()
    events = Events()

    story.opening_screen()
    console.wait_for_continue()
    console.clear_console()
    drifter_id = events.pick_character_id()
    console.clear_console()
    return create_new_game(drifter_id)


def _startup_game_state(save_port):
    inspection = save_port.inspect()
    if inspection.status is SaveLoadStatus.VALID:
        while True:
            choice = input(
                "A saved session was found. [L]oad or [N]ew game? "
            ).strip().lower()
            if choice in {"l", "load", "1"}:
                result = save_port.load()
                if result.status is SaveLoadStatus.LOADED:
                    return result.game_state
                print(result.error or "The saved game could not be loaded.")
                break
            if choice in {"n", "new", "2"}:
                break
            print("Choose L to load the saved session or N to start a new game.")
    elif inspection.status is SaveLoadStatus.INVALID:
        print(inspection.error or "The save file is invalid and was not loaded.")
    return _new_game_state()


def main(*, save_port=None):
    if save_port is None:
        save_port = build_default_save_port()
    game_state = _startup_game_state(save_port)
    while True:
        result = OverworldSession(
            game_state,
            ui=TerminalOverworldUI(),
            battle_factory=Battle,
            enemy_factory=create_enemy_state,
            battle_ui_factory=TerminalBattleUI,
            save_port=save_port,
        ).run()
        if result is not OverworldSessionResult.SELECT_DRIFTER:
            return result
        game_state = _new_game_state()


if __name__ == "__main__":
    main()

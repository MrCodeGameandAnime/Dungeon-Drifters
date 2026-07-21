from app.combat.battle import Battle
from app.enemies.factory import create_enemy_state
from app.game import console
from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession
from app.game.save_repository import SaveLoadStatus, SaveRepository
from app.player.player_state import PlayerState
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
    character = events.pick_character()
    console.clear_console()
    player_state = PlayerState(character)
    return GameState(player_state)


def _startup_game_state(save_repository):
    inspection = save_repository.inspect()
    if inspection.status is SaveLoadStatus.VALID:
        while True:
            choice = input(
                "A saved session was found. [L]oad or [N]ew game? "
            ).strip().lower()
            if choice in {"l", "load", "1"}:
                result = save_repository.load()
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


def main(*, save_repository=None):
    if save_repository is None:
        save_repository = SaveRepository()
    game_state = _startup_game_state(save_repository)
    OverworldSession(
        game_state,
        ui=TerminalOverworldUI(),
        battle_factory=Battle,
        enemy_factory=create_enemy_state,
        battle_ui_factory=TerminalBattleUI,
        save_repository=save_repository,
    ).run()


if __name__ == "__main__":
    main()

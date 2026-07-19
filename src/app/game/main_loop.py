from app.combat.battle import Battle
from app.enemies.factory import create_enemy_state
from app.game import console
from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession
from app.player.player_state import PlayerState
from app.ui.terminal_battle_ui import TerminalBattleUI
from app.ui.terminal_overworld_ui import TerminalOverworldUI
from app.world.event import Events
from app.world.story import StoryElements


def main():
    story = StoryElements()
    events = Events()

    story.opening_screen()
    console.wait_for_continue()
    console.clear_console()
    character = events.pick_character()
    console.clear_console()
    player_state = PlayerState(character)
    game_state = GameState(player_state)
    OverworldSession(
        game_state,
        ui=TerminalOverworldUI(),
        battle_factory=Battle,
        enemy_factory=create_enemy_state,
        battle_ui_factory=TerminalBattleUI,
    ).run()


if __name__ == "__main__":
    main()

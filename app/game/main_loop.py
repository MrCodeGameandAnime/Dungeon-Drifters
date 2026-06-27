from app.combat.battle import Battle
from app.combat.enemy import Goblin
from app.game import console
from app.player.player_state import PlayerState
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
    encounter = story.day_one(events)

    if encounter == "escaped":
        story.escaped_ending(player_state.character)
        return

    winner = Battle(player_state, Goblin()).run()
    story.battle_ending(player_state.character, winner)


if __name__ == "__main__":
    main()

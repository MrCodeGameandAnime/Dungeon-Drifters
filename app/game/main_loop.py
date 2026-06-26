from app.combat.battle import Battle
from app.combat.enemy import Goblin
from app.world.event import Events
from app.world.story import StoryElements


def main():
    story = StoryElements()
    events = Events()

    story.opening_screen()
    player = events.pick_character()
    encounter = story.day_one(events)

    if encounter == "escaped":
        story.escaped_ending(player)
        return

    winner = Battle(player, Goblin()).run()
    story.battle_ending(player, winner)


if __name__ == "__main__":
    main()

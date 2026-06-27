import random

from app.world.character_profiles.roster import get_profile_by_choice, render_character_roster


class Events:
    def avoid_battle(self):
        run_chance = random.randint(1, 10)

        if run_chance > 5:
            print("You escaped in the nick of time. Live to fight another day.")
            return True

        print("You can't escape. It's time for battle!")
        return False

    def pick_character(self):
        print(f"\n{render_character_roster()}")

        while True:
            character_choice = input(
                "Choose your character: 1 for Brawler, 2 for Black Mage, 3 for Rogue Archer, 4 for Monk: "
            ).strip()
            profile = get_profile_by_choice(character_choice)

            if profile is None:
                print("That is not a valid character choice. Please try again.")
                continue

            player = profile.create_character()
            print(f"You have chosen the {player.name}!")
            return player

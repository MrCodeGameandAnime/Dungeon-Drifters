import random

from app.content.catalog import DRIFTER_SPECS, get_drifter_spec_by_choice
from app.game import console
from app.presentation.character_profile_presenter import (
    render_full_profile,
    render_roster,
)


class Events:
    def avoid_battle(self):
        run_chance = random.randint(1, 10)

        if run_chance > 5:
            print("You escaped in the nick of time. Live to fight another day.")
            return True

        print("You can't escape. It's time for battle!")
        return False

    def pick_character(self):
        while True:
            print(f"\n{render_roster(DRIFTER_SPECS)}")
            character_choice = input("Choose your Drifter: ").strip()
            profile = get_drifter_spec_by_choice(character_choice)

            if profile is None:
                print("That is not a valid character choice. Please try again.")
                continue

            console.clear_console()
            print(f"\n{render_full_profile(profile)}")

            while True:
                confirmation = input(f"Continue with {profile.short_name}? [Y/N]: ").strip().lower()

                if confirmation in ("y", "yes"):
                    player = profile.create_character()
                    print(f"You have chosen {player.full_display_name}!")
                    return player

                if confirmation in ("n", "no"):
                    console.clear_console()
                    break

                print("Please enter Y or N.")

import random
import character


class Events:
    def avoid_battle(self):
        run_chance = random.randint(1, 10)

        if run_chance > 5:
            print("You escaped in the nick of time. Live to fight another day.")
            return True

        print("You can't escape. It's time for battle!")
        return False

    def pick_character(self):
        print('''
You have four warriors to choose from who will adventure in the land of Ketlyv.

1. Brawler
Masters of unrestricted combat, Brawlers revel in fighting dirty and decimating their opponent by fighting with every
advantage they have.

2. Black Mage
Black mages are spell casters who focus on obliterating their foes with fire, ice, and lightning.

3. Rogue Archer
Drawn to the ways of the bow, Rogue Archers deal damage with precise shots or volleys of arrows darkening out the sun.

4. Monk
Sendo Monks are martial artists who base their fighting style on versatility, ingenuity, and strange uses of Ki.
        ''')

        choices = {
            "1": character.Brawler,
            "2": character.BlackMage,
            "3": character.RogueArcher,
            "4": character.Monk,
        }

        while True:
            character_choice = input(
                "Choose your character: 1 for Brawler, 2 for Black Mage, 3 for Rogue Archer, 4 for Monk: "
            ).strip()
            selected_character = choices.get(character_choice)

            if selected_character is None:
                print("That is not a valid character choice. Please try again.")
                continue

            player = selected_character()
            print(f"You have chosen the {player.name}!")
            return player

import random
import character
# from Battle import Battle as battle


class Events:
    def __init__(self):
        pass

    def avoid_battle(self):
        run_chance = random.randint(1, 10)

        if run_chance > 5:
            print("You escaped in the nick of time. Live to fight another day.")
            return True
        else:
            print("You can't escape. It's time for battle!")
            return False
            # battle()

    def pick_character(self):
        print('''
You have four warriors to choose from who will adventure in the land of Ketlyv.

Brawler: 
Masters of unrestricted combat, Brawlers revel in fighting dirty and decimating their opponent by fighting with every 
advantage they have. Many brawlers rely on heavy unarmed strikes and forcing the enemy into an unfair battle. 
However, it is not uncommon for them  to use any weapon at their disposal to get the job done.

Black Mage:
Black mages are spell casters who focus on the destructive aspects of the arcane. They eschew almost all forms of 
utility magic and the broader applications of evocation in favor of obliterating their foes with 
fire, ice, and lightning.

Rouge Archer:
Drawn to the ways of the bow dealing damage with precise shots or volleys of arrows darkening out the sun, Rouge Archers 
are trained alongside  the standard fighter but forgo a lot of the versatility to specialize with Bows and arrows.

Monk:
Sendo Monks are martial artists that base their fighting style on versatility and ingenuity. They use their weapons and 
Ki in bizarre ways and take pride in the more outlandish ways to fell foes. Their art relies entirely on how certain 
breathing techniques affect their Ki, allowing them to stretch the limits of the imagination on what one's body and 
spirit are truly capable of. The two most notable traits of their art is its ability to send Ki through liquid and its 
specific uses against the undead. Legend has it that an ancient race that no longer exists in this realm introduced 
Necromancy to the world. In the wake of the great battles that came due to the use of that magic, warriors that trained 
in the mountains, as the thin air allowed them to breath more deeply, developed a new techniques to combat a new menace. 
The art of the Hermit, "Sendo".
        ''')

        character_choice = int(
            input('Choose your character: 1 for Brawler, 2 for Dark Mage, 3 for Rouge Archer, 4 for Monk: '))
        print(character_choice)
        if character_choice == 1:
            print("You have chosen the Brawler!")
            return Character.Brawler()
        if character_choice == 2:
            print("You have chosen the Black Mage!")
            return Character.BlackMage()
        if character_choice == 3:
            print("You have chosen the Rogue Archer!")
            return Character.RogueArcher()
        if character_choice == 4:
            print("You have chosen the Monk!")
            return Character.Monk()

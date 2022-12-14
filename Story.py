from Character import CharacterType as character

class StoryElements:

    def pickCharacterType():
        #character_dict = {1:"Brawler",2:"Dark Mage",3:"Rouge Archer",4:"Monk"}
        print("You have four warriors to choose from who will adventure in the land of Ketlyv." + '''

        Brawler: 
        Masters of unrestricted combat, Brawlers revel in fighting dirty and decimating their opponent by fighting with every advantage 
        they have. Many brawlers rely on heavy unarmed strikes and forcing the enemy into an unfair battle. However, it is not uncommon for them 
        to use any weapon at their disposal to get the job done.

        Black Mage:
        Black mages are spellcasters who focus on the destructive aspects of the arcane. They eschew almost all forms of utility magic and the 
        broader applications of evocation in favor of obliterating their foes with fire, ice and lightning.

        Rouge Archer:
        Drawn to the ways of the bow dealing damage with precise shots or volleys of arrows darkening out the sun, Rouge Archers are trained alongside 
        the standard fighter but forgo a lot of the versatility to specialize with Bows and arrows

        Monk:
        Sendo Monks are martial artists that base their fighting style on versatility and ingenuity. They use their weapons and their Ki in bizarre ways 
        and take pride in the more outlandish ways in which they have felled foes. Their art relies entirely on how certain breathing techniques affect their 
        Ki, allowing them to strech the limits of the imagination on what one's body and spirit are truly capable of. The two most notable traits of their 
        art is its ability to send Ki through liquid and its specific uses against the undead. Legend has it that an ancient race that no longer exists in 
        this realm introduced Necromancy to the world. In the wake of the great battles that came due to the use of that magic, warriors that trained in the 
        mountains, as the thin air allowed them to breath more deeply, developed a new set of techniques to combat the new menace. 
        The art of the Hermit, "Sendo".
        ''')
        character_choice = int(input('Choose your character: 1 for Brawler, 2 for Dark Mage, 3 for Rouge Archer, 4 for Monk: '))
        print(character_choice)
        if character_choice == 1:
            character.Brawler()
            print("You have chosen the Brawler!")
        if character_choice == 2:
            character.BlackMage()
            print("You have chosen the Black Mage!")
        if character_choice == 3:
            character.RougeArcher()
            print("You have chosen the Rouge Archer!")
        if character_choice == 4:
            character.Monk()
            print("You have chosen the Monk!")

    def dayOne():
        print('''
        You awaken to low light flickering from the campfire you setup last night. Your boy is heavy from the endless battles.
        You would like to go back to sleep, but the adventure must carry on. Sitting up and rustling around in your pack, you find your sword,
        put out the fire, and head out of the cave you hunkered down in for the night. "FRESH AIR!"

        You set out through the woods to continue searching for the goblin hoarde that has been attacking a local village. They have requested
        your services, and you will see it to completetion. You hear a sound coming from the right and suddenly a goblin jumps out of the bushes
        What will you do? Attack or attempt to flee?
        ''')

    def openingScreen():
        print('''
        ++====================================================================================================================++
        ||                                                                                                                    ||
        ||                                                                                                                    ||
        ||                                                                                                                    ||
        ||                                                                                                                    ||
        ||                                                                                                                    ||
        ||                                                                                                                    ||
        ||                                                                                                                    ||
        ||                    =============== ||      || ||+        || ========== ========= ============ ||+        ||        ||
        ||                    ||           || ||      || || +       || ||         ||        ||        || || +       ||        ||
        ||                    ||           || ||      || ||  +      || ||         ||        ||        || ||  +      ||        ||
        ||                    ||   =====   || ||      || ||   +     || ||   ===== ||        ||        || ||   +     ||        ||
        ||                    ||   || ||   || ||      || ||    +    || ||      || ========= ||   ++   || ||    +    ||        ||
        ||                    ||   || ||   || ||      || ||     +   || ||      || ||        ||   ++   || ||     +   ||        ||
        ||                    ||   =====   || ||      || ||      +  || ||      || ||        ||        || ||      +  ||        ||
        ||                    ||           || ||      || ||       + || ||      || ||        ||        || ||       + ||        ||
        ||                    =============== ========== ||        +|| ========|| ========= ============ ||        +||        ||
        ||                                                                                                                    ||
        ||                    ****************************************************************************************        ||
        ||                    ****************************************************************************************        ||
        ||                                                                                                                    ||
        ||                    =============== ========== ============ ========== ========== ============ =============        ||
        ||                    ||           || ||      ||      ||      ||             ||     ||           ||         ||        ||
        ||                    ||           || ||      ||      ||      ||             ||     ||           ||         ||        ||
        ||                    ||   ======  || ==========      ||      ||             ||     ||           =============        ||
        ||                    ||   ||  ||  || ||+             ||      ==========     ||     ===========  ||+                  ||
        ||                    ||   ||  ||  || || +            ||      ||             ||     ||           || +                 ||
        ||                    ||   ======  || ||  +           ||      ||             ||     ||           ||  +                ||
        ||                    ||           || ||   +          ||      ||             ||     ||           ||   +               ||
        ||                    =============== ||    +    ============ ||             ||     ===========  ||    +              ||
        ||                                                                                                                    ||
        ||                                                                                                                    ||
        ||                                                                                                                    ||
        ||                                                                                                                    ||
        ||                                                                                                                    ||
        ++====================================================================================================================++
        ''')

StoryElements.pickCharacterType()
StoryElements.openingScreen()
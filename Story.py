# from Character import CharacterType as characterType
from Events import EventType as eventType


# from Battle import Battle as battle

class StoryElements:

    def __init__(self):
        pass

    @staticmethod
    def day_one():
        # eventType.pick_character()
        print('''
You awaken to low light flickering from the campfire you setup last night. Your body is heavy from the endless battles. 
You would like to go back to sleep, but the adventure must carry on. Sitting up and rustling around in your pack, 
you find your sword, put out the fire, and head out of the cave you hunkered down in for the night. 
"FRESH AIR!" You set out through the woods to continue searching for the goblin hoard that has been attacking 
a local village. They have requested your services, and you will see it to completion. 

You hear a sound coming from the right and suddenly a goblin jumps out of the bushes What will you do?
Attack or attempt to flee?
        ''')

        # atk_or_flee = int(input('1 to attack and 2 to run: '))
        # if atk_or_flee == 1:
        #     print(type(atk_or_flee))
        #     print(type(1))
        #     #battle()
        #     None
        # elif atk_or_flee == 2:
        #     result = event.avoidBattle()
        # if result == True:
        #     print("True")
        #     StoryElements.openingScreen()
        # if result == False:
        #     print("False")
        #     #battle()
        #     StoryElements.openingScreen()

        atk_or_flee = int(input('1 to attack and 2 to run: '))
        if atk_or_flee == 1:
            print("detected user input '1'")
        elif atk_or_flee == 2:
            print("detected user input '2'...")
            result = eventType().avoid_battle()
            print(f".. and assigned the value {result} to the variable 'result'")
            if result:
                print("Fleeing ended up being True")
                StoryElements.opening_screen()
            else:
                # battle()
                print("Fleeing ended up False")

    @staticmethod
    def opening_screen():
        print('''
        ++============================================================================================================++
        ||                                                                                                            ||
        ||                                                                                                            ||
        ||                                                                                                            ||
        ||                                                                                                            ||
        ||                                                                                                            ||
        ||                                                                                                            ||
        ||                                                                                                            ||
        ||         =============== ||      || ||+        || ========== ========= ============ ||+        ||           ||
        ||         ||           || ||      || || +       || ||         ||        ||        || || +       ||           ||
        ||         ||           || ||      || ||  +      || ||         ||        ||        || ||  +      ||           ||
        ||         ||   =====   || ||      || ||   +     || ||   ===== ||        ||        || ||   +     ||           ||
        ||         ||   || ||   || ||      || ||    +    || ||      || ========= ||   ++   || ||    +    ||           ||
        ||         ||   || ||   || ||      || ||     +   || ||      || ||        ||   ++   || ||     +   ||           ||
        ||         ||   =====   || ||      || ||      +  || ||      || ||        ||        || ||      +  ||           ||
        ||         ||           || ||      || ||       + || ||      || ||        ||        || ||       + ||           ||
        ||         =============== ========== ||        +|| ========|| ========= ============ ||        +||           ||
        ||                                                                                                            ||
        ||         ****************************************************************************************           ||
        ||         ****************************************************************************************           ||
        ||                                                                                                            ||
        ||         =============== ========== ============ ========== ========== ============ =============           ||
        ||         ||           || ||      ||      ||      ||             ||     ||           ||         ||           ||
        ||         ||           || ||      ||      ||      ||             ||     ||           ||         ||           ||
        ||         ||   ======  || ==========      ||      ||             ||     ||           =============           ||
        ||         ||   ||  ||  || ||   +          ||      ==========     ||     ===========  ||    +                 ||
        ||         ||   ||  ||  || ||    +         ||      ||             ||     ||           ||     +                ||
        ||         ||   ======  || ||     +        ||      ||             ||     ||           ||      +               ||
        ||         ||           || ||      +       ||      ||             ||     ||           ||       +              ||
        ||         =============== ||       + ============ ||             ||     ===========  ||        +             ||
        ||                                                                                                            ||
        ||                                                                                                            ||
        ||                                                                                                            ||
        ||                                                                                                            ||
        ||                                                                                                            ||
        ++============================================================================================================++
        ''')


StoryElements().day_one()

from Character import CharacterType as character
from Events import EventType as event
#from Battle import Battle as battle

class StoryElements:
    def __init__(self):
        None
    
    def dayOne():
        event.pickCharacter()
        print('''
        You awaken to low light flickering from the campfire you setup last night. Your boy is heavy from the endless battles.
        You would like to go back to sleep, but the adventure must carry on. Sitting up and rustling around in your pack, you find your sword,
        put out the fire, and head out of the cave you hunkered down in for the night. "FRESH AIR!"

        You set out through the woods to continue searching for the goblin hoarde that has been attacking a local village. They have requested
        your services, and you will see it to completetion. You hear a sound coming from the right and suddenly a goblin jumps out of the bushes
        What will you do? Attack or attempt to flee?
        ''')


        atk_or_flee = input('1 to attack and 2 to run: ')
        if atk_or_flee == 1: # <--------------------
            #battle()
            None
        if atk_or_flee == 2:
            event.avoidBattle()
        if event.avoidBattle() == True:
            print("True")
            StoryElements.openingScreen()
        if event.avoidBattle() == False:
            print("False")
                #battle()
            StoryElements.openingScreen() # <-------

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

StoryElements.dayOne()
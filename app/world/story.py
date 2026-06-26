class StoryElements:
    @staticmethod
    def opening_screen():
        print('''
++==============================================================++
||                                                              ||
||                    DUNGEON DRIFTERS                         ||
||                                                              ||
||                  A tale from Ketlyv                          ||
||                                                              ||
++==============================================================++
        ''')

    @staticmethod
    def day_one(events):
        print('''
You awaken to low light flickering from the campfire you set up last night. Your body is heavy from the endless battles.
You would like to go back to sleep, but the adventure must carry on. Sitting up and rustling around in your pack,
you find your sword, put out the fire, and head out of the cave you hunkered down in for the night.

"FRESH AIR!"

You set out through the woods to continue searching for the goblin horde that has been attacking a local village. They
have requested your services, and you will see it to completion.

You hear a sound from the right. Suddenly, a goblin jumps out of the bushes.
        ''')

        while True:
            choice = input("What will you do? 1 to attack, 2 to flee: ").strip().lower()

            if choice in ("1", "attack"):
                print("You ready your weapon and face the goblin.")
                return "battle"

            if choice in ("2", "flee", "run"):
                escaped = events.avoid_battle()
                return "escaped" if escaped else "battle"

            print("That is not a valid choice. Please choose attack or flee.")

    @staticmethod
    def escaped_ending(player):
        print(f'''
{player.name}, you break through the brush and escape the ambush.
The village still needs help, but you live to choose the next road.

For now, your first day in Ketlyv continues.
        ''')

    @staticmethod
    def battle_ending(player, winner):
        if winner == "player":
            print(f'''
The goblin falls. {player.name}, you steady your breathing and look deeper into the woods.
The horde is still out there, but the first threat has been handled.

Victory. Your adventure has begun.
            ''')
        else:
            print(f'''
{player.name} falls beneath the goblin's attack.
The woods of Ketlyv grow quiet again.

Defeat. Better luck next time.
            ''')

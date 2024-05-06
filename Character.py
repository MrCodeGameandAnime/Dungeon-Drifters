class CharacterType:
    # 15 stat points per type
    # strength: strike damage
    # constitution: health and defense
    # intelligence: magic damage
    # dexterity: ranged attacks
    # charisma: skil check and better prices
    # hp: 15 points per level
    # mana: 10 points per level

    class Brawler:
        def __init__(self):
            self.strength = 7
            self.constitution = 5
            self.intelligence = 1
            self.dexterity = 1
            self.charisma = 1
            self.hp = 60
            self.mana = 10
            self.exp = 0
            self.name = "Brawler"
            self.level = 1
            self.moves = {1: 'slash', 2: 'jumping slash', 3: 'suplex'}

    class BlackMage:
        def __init__(self):
            self.strength = 1
            self.constitution = 2
            self.intelligence = 7
            self.dexterity = 2
            self.charisma = 3
            self.hp = 30
            self.mana = 70
            self.exp = 0
            self.name = "Black Mage"
            self.level = 1
            self.moves = {1: 'fireball', 2: 'heal', 3: 'thunderbolt'}  # ice shield

    class RougeArcher:
        def __init__(self):
            self.strength = 2
            self.constitution = 3
            self.intelligence = 2
            self.dexterity = 7
            self.charisma = 1
            self.hp = 45
            self.mana = 20
            self.exp = 0
            self.name = "Rouge Archer"
            self.level = 1
            self.moves = {1: 'deadshot', 2: 'triple shot', 3: 'rain of arrows', 4: 'flaming arrow'}

    class Monk:
        def __init__(self):
            self.strength = 4
            self.constitution = 4
            self.intelligence = 2
            self.dexterity = 3
            self.charisma = 2
            self.hp = 60
            self.mana = 20
            self.exp = 0
            self.name = "Monk"
            self.level = 1
            self.moves = {1: 'Bring The Horse To Water',
                          2: 'Sweep The Leaves',
                          3: '5-foot punch',
                          4: 'Waki Gamae Kamae Kata',
                          5: 'Carry Water'}
            # Bring The Horse To Water:
            # brace the quarterstaff (think: set spear vs charge) and pull the target's head into it.
            #
            # Sweep The Leaves:
            # low strike to the shin or foot, could also be a shove (trip) attack.
            #
            # 5-foot punch:
            # straight thrust into the stomach, playing on the name of the 5-inch punch from Jeet Kune Do
            #
            # Waki Gamae Kamae Kata (Wah-Kee Gah-May Ka-May Ka-Ta):
            # a strike from holding the quarterstaff overhead with both hands at the bottom.
            # Best when done at the end of a charge or after defending for a turn (to charge up!)
            #
            # Carry Water:
            # execute a fireman's carry maneuver on the quarterstaff against a prone enemy,
            # using both rotational force and adding your own weight to maximize the blow.


class Level:
    def increase_level(self):
        pass


class Health:
    def increase_health(self):
        pass

    def decrease_health(self):
        pass


class Mana:
    def increase_mana(self):
        pass

    def decrease_mana(self):
        pass

    def mana_pool(self):
        pass


class Stats:
    def attack(self):
        pass

    def defense(self):
        pass

    def health(self):
        pass

    def mana(self):
        pass

    def luck(self):
        pass


class Exp:
    def increase_exp(self):
        pass

    def exp_pool(self):
        pass

class Character:
    def __init__(self, strn, con, intl, dex, char, hp, mana, name, moves):
        self.strength = strn
        self.constitution = con
        self.intelligence = intl
        self.dexterity = dex
        self.charisma = char
        self.hp = hp
        self.mana = mana
        self.exp = 0
        self.name = name
        self.level = 1
        self.moves = moves


class Brawler(Character):
    def __init__(self):
        super().__init__(
            strn=7,
            con=5,
            intl=1,
            dex=1,
            char=1,
            hp=60,
            mana=10,
            name="Brawler",
            moves={1: 'slash', 2: 'jumping slash', 3: 'suplex'})


class BlackMage(Character):
    def __init__(self):
        super().__init__(
            strn=1,
            con=2,
            intl=7,
            dex=2,
            char=3,
            hp=30,
            mana=70,
            name="Black Mage",
            moves={1: 'fireball', 2: 'heal', 3: 'thunderbolt'})  # ice shield


class RogueArcher(Character):
    def __init__(self):
        super().__init__(
            strn=2,
            con=3,
            intl=2,
            dex=7,
            char=1,
            hp=45,
            mana=20,
            name="Rogue Archer",
            moves={1: 'deadshot', 2: 'triple shot', 3: 'rain of arrows', 4: 'flaming arrow'})


class Monk(Character):
    def __init__(self):
        super().__init__(
            strn=4,
            con=4,
            intl=2,
            dex=3,
            char=2,
            hp=60,
            mana=20,
            name="Monk",
            moves={1: 'Bring The Horse To Water',
                      2: 'Sweep The Leaves',
                      3: '5-foot punch',
                      4: 'Waki Gamae Kamae Kata',
                      5: 'Carry Water'})


print(Monk().hp)

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

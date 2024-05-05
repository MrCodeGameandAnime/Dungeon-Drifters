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


class Level:
    def increaseLevel(self):
        pass


class Health:
    def increaseHealth(self):
        pass

    def decreaseHealth(self):
        pass


class Mana:
    def increaseMana(self):
        pass

    def decreaseMana(self):
        pass

    def manaPool(self):
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


class Exp():
    def increaseExp(self):
        pass

    def ExpPool(self):
        pass

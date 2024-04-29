#Types: Level, Health, Mana, Stats, Exp

class CharacterType:

    class Brawler:
        def __init__(self):
            # strength -> attack, constituion -> defense
            self.strength = 3 # raw power
            self.constitution = 3 # defense and health
            self.intelligence = 7 # magic
            self.dexterity = 2 # finnese
            self.charisma = 0 # skill check to talk your way through things or get better prices
            self.health = 100
            self.mana = 20
            self.exp = 0
            self.name = "Hero"
            self.level = 1

    class BlackMage:
        def __init__(self):
            # strength -> attack, constituion -> defense
            # strength -> attack, constituion -> defense
            self.strength = 3
            self.constitution = 3
            self.intelligence = 7
            self.dexterity = 2
            self.charisma = 0
            self.health = 50
            self.mana = 20
            self.exp = 0
            self.name = "Hero"
            self.level = 1

    class RougeArcher:
        def __init__(self):
            # strength -> attack, constituion -> defense
            self.strength = 3
            self.constitution = 3
            self.intelligence = 7
            self.dexterity = 2
            self.charisma = 0
            self.health = 50
            self.mana = 20
            self.exp = 0
            self.name = "Hero"
            self.level = 1

    class Monk:
        def __init__(self):
            # strength -> attack, constituion -> defense
            self.strength = 3
            self.constitution = 3
            self.intelligence = 7
            self.dexterity = 2
            self.charisma = 0
            self.health = 50
            self.mana = 20
            self.exp = 0
            self.name = "Hero"
            self.level = 1

class Level():
    def increaseLevel(self):
        pass

class Health():
    def increaseHealth(self):
        pass

    def decreaseHealth(self):
        pass
        
class Mana():
    def increaseMana(self):
        pass
    
    def decreaseMana(self):
        pass

    def manaPool(self):
        pass

class Stats():
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
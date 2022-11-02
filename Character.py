#Types: Level, Health, Mana, Stats, Exp

class Player:
    # strength -> attack, constituion -> defense
    strength = 3
    constitution = 2
    health = 50
    mana = 20
    exp = 0
    name = "name"
    level = 1

    def __init__(self):
        pass

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
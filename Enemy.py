# Type: Goblin, Orcs, Skelleton Archer, Zombie, Snake Lord

class EnemyType:

    class Goblin:

        def __init__(self):
            # strength -> attack, constituion -> defense
            self.strength = 3
            self.constitution = 2
            self.health = 50
            self.mana = 20
            self.exp = 0
            self.name = "Drak"
            self.level = 1
            
        def printName(self):
            print(self.name)

goblin_worrior = EnemyType.Goblin()
goblin_worrior.printName()
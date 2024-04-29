# Type: Goblin, Orcs, Skelleton Archer, Zombie, Snake Lord

class EnemyType:

    class Goblin:
        def __init__(self):
            self.strength = 3
            self.constitution = 2
            self.health = 50
            self.mana = 20
            self.exp = 0
            self.name = "Drak"
            self.level = 1
            
        def printName(self):
            print(self.name)

    class Orcs:
        def __init__(self):
            self.strength = 3
            self.constitution = 2
            self.health = 50
            self.mana = 20
            self.exp = 0
            self.name = "Drak"
            self.level = 1
            
        def printName(self):
            print(self.name)
    
    class Skelleton:
        def __init__(self):
            self.strength = 3
            self.constitution = 2
            self.health = 50
            self.mana = 20
            self.exp = 0
            self.name = "Drak"
            self.level = 1
            
        def printName(self):
            print(self.name)
    
    class Archer:
        def __init__(self):
            self.strength = 3
            self.constitution = 2
            self.health = 50
            self.mana = 20
            self.exp = 0
            self.name = "Drak"
            self.level = 1
            
        def printName(self):
            print(self.name)
        
    class Zombie:
        def __init__(self):
            self.strength = 3
            self.constitution = 2
            self.health = 50
            self.mana = 20
            self.exp = 0
            self.name = "Drak"
            self.level = 1
            
        def printName(self):
            print(self.name)
        
    class SnakeLord:
        def __init__(self):
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
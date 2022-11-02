from Character import Player as player
from Enemy import Goblin as goblin

class Battle(player,goblin):

    def __init__(self):
        super().__init__()

        
    def loop(self):
        pass

    def displayUserName(self):
        return goblin.health + player.constitution

battle = Battle()
battle.displayUserName()
            

class Events():

    def attackEnemy(self):
        if playerInput == 'attack' or "Attack":
            Battle.loop()
        
        return enterBattleLoop

    def runFromEnenmy(self):
        pass
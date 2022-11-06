from Character import CharacterType as player
from Enemy import EnemyType as enemys

class Battle(player,enemys):

    def __init__(self):
        super().__init__()
        self.goblin_worrir = enemys.Goblin()
        self.player = player()
        
    def loop(self):
        pass

    def print_names(self):
        print(self.player.name +" "+ self.goblin_worrir.name)

battle = Battle()
battle.print_names()
            

class Events():

    def attackEnemy(self):
        if playerInput == 'attack' or "Attack":
            Battle.loop()
        
        return enterBattleLoop

    def runFromEnenmy(self):
        pass
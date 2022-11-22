from Character import CharacterType as player
from Enemy import EnemyType as enemys
import random

class EventTypes:
    pass

# class Battle(player,enemys):

#     def __init__(self):
#         super().__init__()
#         self.goblin_worrir = enemys.Goblin()
#         self.player = player()
        
#     def battleLoop(self):
#         pass


#     # def print_names(self):
#     #     print(self.player.name +" "+ self.goblin_worrir.name)

class Battle(player,enemys):
    def __init__(self):
        self.goblin_worrir = enemys.Goblin()
        self.player = player()
        
        self.moves={'Punch': [18, 25],
        'Mega Punch': [10, 35],
        'Heal': [-25, -20]
       }

        self.moves_list=list(self.moves)
        self.moves_list_lower=[move.lower() for move in self.moves_list]

        self.move_names='\n'+'\n'.join(
            "{0}. {1} (Deal damage between '{2[0]}' - '{2[1]}')".format(
                i,
                move,
                self.moves[move]
            )
            for i, move in enumerate(self.moves_list)
        )
    def select_move(self):
        move = input(self.move_names + '\n> ').lower()
        try:
            return self.moves_list[int(move)]
        except ValueError:
            return self.moves_list[self.moves_list_lower.index(move)]
        except IndexError:
            print('That is not a valid move. Please try again.')

    def use_move(self, other, move):
        # 20% of missing
        if random.randint(1,2):
            print('{} missed!'.format(self.title.capitalize()))
        else:
            # Works as shown earlier.
            magnitude = random.randint(*self.moves[move])
            if self.moves[move][0] < 0:
                # A simple self.health += magnitude
                self.heal(magnitude)
                desc = 'healed for {} health.'
            else:
                # A simple self.health -= magnitude
                other.deal(magnitude)
                desc = 'dealt {} damage.'
            print(('{} used {}. It' + desc).format(
                   self.title.capitalize(),
                   move,
                   magnitude
                   ))


battle = Battle()
#battle.print_names()
            

class Events():

    def attackEnemy(self):
        if playerInput == 'attack' or "Attack":
            Battle.loop()
        
        return enterBattleLoop

    def runFromEnenmy(self):
        pass
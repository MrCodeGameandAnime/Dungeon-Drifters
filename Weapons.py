#Types: Sword, Axe, Spear, Shield, Dagger, Staff

import random as r

class Sword ():

    def attack(self):
        if r.randrange(1,10) >= 5:
            attackSucceeded = True

            return True
        else:
            return False
    
    def defend(self):
        return 1

class Axe ():

    def attack(self):
        return 1
    
    def defend(self):
        return 1
        
class Spear ():

    def attack(self):
        return 1
    
    def defend(self):
        return 1

class Shield ():

    def attack(self):
        return 1
    
    def defend(self):
        return 1

class Dagger():

    def attack(self):
        return 1
    
    def defend(self):
        return 1

class Staff():

    def attack(self):
        return 1
    
    def defend(self):
        return 1
        
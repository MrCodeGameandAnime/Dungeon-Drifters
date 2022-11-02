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
        pass

class Axe ():

    def attack(self):
        pass
    
    def defend(self):
        pass
        
class Spear ():

    def attack(self):
        pass
    
    def defend(self):
        pass

class Shield ():

    def attack(self):
        pass
    
    def defend(self):
        pass

class Dagger():

    def attack(self):
        pass
    
    def defend(self):
        pass

class Staff():

    def attack(self):
        pass
    
    def defend(self):
        pass
        
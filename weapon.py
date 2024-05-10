class Weapon:
    def __init__(self, atk, defs, mgk_atk, mgk_defs, val):
        self.attack = atk
        self.defense = defs
        self.magic_attack = mgk_atk
        self.magic_defense = mgk_defs
        self.value = val


class Sword(Weapon):
    def __init__(self):
        super().__init__(
            atk=2,
            defs=2,
            mgk_atk=0,
            mgk_defs=0,
            val=2)


class Axe(Weapon):
    def __init__(self):
        super().__init__(
            atk=3,
            defs=2,
            mgk_atk=0,
            mgk_defs=0,
            val=3)


class Spear(Weapon):
    def __init__(self):
        super().__init__(
            atk=2,
            defs=2,
            mgk_atk=0,
            mgk_defs=0,
            val=2)


class Shield(Weapon):
    def __init__(self):
        super().__init__(
            atk=1,
            defs=3,
            mgk_atk=0,
            mgk_defs=1,
            val=2)


class Dagger(Weapon):
    def __init__(self):
        super().__init__(
            atk=1,
            defs=2,
            mgk_atk=0,
            mgk_defs=0,
            val=1)


class Staff(Weapon):
    def __init__(self):
        super().__init__(
            atk=1,
            defs=1,
            mgk_atk=3,
            mgk_defs=2,
            val=3)

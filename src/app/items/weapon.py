class Weapon:
    def __init__(self, atk, defs, mgk_atk, mgk_defs, val, name, character):
        self.attack = atk
        self.defense = defs
        self.magic_attack = mgk_atk
        self.magic_defense = mgk_defs
        self.value = val
        self.name = name
        self.character = character

class Sword(Weapon):
    def __init__(self):
        super().__init__(
            character="Branoc",
            name="Sunder-Spire",
            atk=2,
            defs=2,
            mgk_atk=0,
            mgk_defs=0,
            val=2)


class MagicStaff(Weapon):
    def __init__(self):
        super().__init__(
            character="Azhvielle",
            name="Needle of Plain Iron",
            atk=1,
            defs=3,
            mgk_atk=0,
            mgk_defs=1,
            val=2)


class Bow(Weapon):
    def __init__(self):
        super().__init__(
            character="Zhaivra",
            name="Sathren",
            atk=1,
            defs=2,
            mgk_atk=0,
            mgk_defs=0,
            val=1)


class Staff(Weapon):
    def __init__(self):
        super().__init__(
            character="Joruun",
            name="Sky-Needle",
            atk=1,
            defs=1,
            mgk_atk=3,
            mgk_defs=2,
            val=3)

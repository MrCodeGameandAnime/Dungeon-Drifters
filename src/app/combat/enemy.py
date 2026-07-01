class Enemy:
    def __init__(self, strn, con, intl, dex, hp, mana, name, combat_moves, spirit=1, intuition=1):
        self.strength = strn
        self.constitution = con
        self.intelligence = intl
        self.dexterity = dex
        self.spirit = spirit
        self.intuition = intuition
        self.hp = hp
        self.mana = mana
        self.name = name
        self.combat_moves = tuple(combat_moves)
        self.level = 1
        self.exp = 0

    @property
    def moves(self):
        return {
            index: move.name
            for index, move in enumerate(self.combat_moves, start=1)
        }


def __getattr__(name):
    if name == "Goblin":
        from app.combat.enemies.goblin.definition import Goblin

        return Goblin

    raise AttributeError(name)


__all__ = ["Enemy", "Goblin"]

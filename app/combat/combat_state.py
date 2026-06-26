"""Temporary combat state for one encounter."""


class CombatState:
    def __init__(self):
        self.turn_count = 0
        self.defending = False
        self.statuses = {}
        self.buffs = {}
        self.debuffs = {}

    def advance_turn(self):
        self.turn_count += 1
        return self.turn_count

    def set_defending(self, defending=True):
        self.defending = defending

    def clear_turn_flags(self):
        self.defending = False

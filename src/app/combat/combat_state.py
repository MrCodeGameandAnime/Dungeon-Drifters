"""Temporary combat state for one encounter."""


class CombatState:
    def __init__(self):
        self.turn_count = 0
        self._defending_combatants = []
        self.statuses = {}
        self.buffs = {}
        self.debuffs = {}

    def advance_turn(self):
        self.turn_count += 1
        return self.turn_count

    def activate_defend(self, combatant):
        if not self.is_defending(combatant):
            self._defending_combatants.append(combatant)

    def is_defending(self, combatant):
        return any(active is combatant for active in self._defending_combatants)

    def clear_defend(self, combatant):
        self._defending_combatants = [
            active
            for active in self._defending_combatants
            if active is not combatant
        ]

    def complete_accepted_action(self, actor, opposing_combatants):
        for opponent in opposing_combatants:
            if opponent is actor:
                continue

            self.clear_defend(opponent)

        return self.advance_turn()

"""Temporary combat state for one encounter."""

from dataclasses import dataclass

from app.combat.move import DamageType


@dataclass
class _BraceState:
    owner: object
    incoming_protection_active: bool
    incoming_reduction_percent: int
    heavy_payoff_active: bool
    heavy_payoff_damage_bonus_percent: int


class CombatState:
    def __init__(self):
        self.turn_count = 0
        self._defending_combatants = []
        self._brace_states = []
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

    def activate_brace(
        self,
        owner,
        *,
        incoming_reduction_percent=40,
        heavy_payoff_damage_bonus_percent=30,
    ):
        brace_state = _BraceState(
            owner=owner,
            incoming_protection_active=True,
            incoming_reduction_percent=incoming_reduction_percent,
            heavy_payoff_active=True,
            heavy_payoff_damage_bonus_percent=heavy_payoff_damage_bonus_percent,
        )

        existing = self._find_brace_state(owner)
        if existing is None:
            self._brace_states.append(brace_state)
            return

        existing.incoming_protection_active = brace_state.incoming_protection_active
        existing.incoming_reduction_percent = brace_state.incoming_reduction_percent
        existing.heavy_payoff_active = brace_state.heavy_payoff_active
        existing.heavy_payoff_damage_bonus_percent = (
            brace_state.heavy_payoff_damage_bonus_percent
        )

    def brace_incoming_reduction_percent(self, target, damage_type):
        brace_state = self._find_brace_state(target)
        if brace_state is None or not brace_state.incoming_protection_active:
            return 0
        if damage_type != DamageType.PHYSICAL:
            return 0

        return brace_state.incoming_reduction_percent

    def consume_brace_follow_up_damage_bonus_percent(self, actor, move_mechanic):
        if move_mechanic != "heavy_attack":
            return 0

        brace_state = self._find_brace_state(actor)
        if brace_state is None or not brace_state.heavy_payoff_active:
            return 0

        brace_state.heavy_payoff_active = False
        return brace_state.heavy_payoff_damage_bonus_percent

    def complete_accepted_action(self, actor, opposing_combatants):
        for opponent in opposing_combatants:
            if opponent is actor:
                continue

            self.clear_defend(opponent)
            self._clear_brace_incoming_protection(opponent)

        return self.advance_turn()

    def _find_brace_state(self, combatant):
        for brace_state in self._brace_states:
            if brace_state.owner is combatant:
                return brace_state

        return None

    def _clear_brace_incoming_protection(self, combatant):
        brace_state = self._find_brace_state(combatant)
        if brace_state is None:
            return

        brace_state.incoming_protection_active = False

"""Temporary combat state for one encounter."""

from dataclasses import dataclass

from app.combat.brace import BRACE_RULES
from app.combat.move import DamageType


HEAL_COOLDOWN_ACTIONS = 3


@dataclass
class _BraceState:
    owner: object
    incoming_protection_active: bool
    incoming_reduction_percent: int
    heavy_payoff_active: bool
    heavy_payoff_damage_bonus_percent: int


@dataclass
class _HealCooldown:
    owner: object
    remaining_actions: int


class CombatState:
    def __init__(self):
        self.turn_count = 0
        self._defending_combatants = []
        self._brace_states = []
        self._heal_cooldowns = []
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

    def heal_cooldown_remaining(self, actor):
        cooldown = self._find_heal_cooldown(actor)
        return cooldown.remaining_actions if cooldown is not None else 0

    def heal_available(self, actor):
        return (
            actor.health.current < actor.health.maximum
            and self.heal_cooldown_remaining(actor) == 0
        )

    def start_heal_cooldown(self, actor, actions=HEAL_COOLDOWN_ACTIONS):
        cooldown = self._find_heal_cooldown(actor)
        if cooldown is None:
            self._heal_cooldowns.append(
                _HealCooldown(owner=actor, remaining_actions=actions)
            )
            return

        cooldown.remaining_actions = actions

    def activate_brace(
        self,
        owner,
        *,
        incoming_reduction_percent=BRACE_RULES.incoming_reduction_percent,
        heavy_payoff_damage_bonus_percent=BRACE_RULES.follow_up_damage_bonus_percent,
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

    def brace_incoming_protection_active(self, actor):
        brace_state = self._find_brace_state(actor)
        return bool(brace_state and brace_state.incoming_protection_active)

    def brace_follow_up_damage_bonus_percent(self, actor, move_mechanic):
        if move_mechanic != BRACE_RULES.follow_up_mechanic:
            return 0

        brace_state = self._find_brace_state(actor)
        if brace_state is None or not brace_state.heavy_payoff_active:
            return 0

        return brace_state.heavy_payoff_damage_bonus_percent

    def consume_brace_follow_up_damage_bonus_percent(self, actor, move_mechanic):
        if move_mechanic != BRACE_RULES.follow_up_mechanic:
            return 0

        brace_state = self._find_brace_state(actor)
        if brace_state is None or not brace_state.heavy_payoff_active:
            return 0

        brace_state.heavy_payoff_active = False
        return brace_state.heavy_payoff_damage_bonus_percent

    def complete_accepted_action(
        self,
        actor,
        opposing_combatants,
        *,
        reduce_heal_cooldown=True,
    ):
        for opponent in opposing_combatants:
            if opponent is actor:
                continue

            self.clear_defend(opponent)
            self._clear_brace_incoming_protection(opponent)

        if reduce_heal_cooldown:
            self._decrement_heal_cooldown(actor)

        return self.advance_turn()

    def _find_brace_state(self, combatant):
        for brace_state in self._brace_states:
            if brace_state.owner is combatant:
                return brace_state

        return None

    def _find_heal_cooldown(self, combatant):
        for cooldown in self._heal_cooldowns:
            if cooldown.owner is combatant:
                return cooldown

        return None

    def _decrement_heal_cooldown(self, combatant):
        cooldown = self._find_heal_cooldown(combatant)
        if cooldown is None or cooldown.remaining_actions == 0:
            return

        cooldown.remaining_actions -= 1

    def _clear_brace_incoming_protection(self, combatant):
        brace_state = self._find_brace_state(combatant)
        if brace_state is None:
            return

        brace_state.incoming_protection_active = False

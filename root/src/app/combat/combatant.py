"""Shared combat-facing protocol for runtime combatants."""

from typing import Protocol, Sequence, runtime_checkable

from app.combat.move import DamageType, Move
from app.runtime_contracts import has_required_members


_COMBATANT_DATA_MEMBERS = (
    "display_name",
    "health",
    "mana_resource",
    "super_resource",
    "generates_super",
    "can_defend",
    "combat_moves",
)
_COMBATANT_CALLABLE_MEMBERS = (
    "effective_stat",
    "defend_reduction_percent",
    "is_alive",
)
_ENEMY_COMBATANT_DATA_MEMBERS = _COMBATANT_DATA_MEMBERS + (
    "archetype_id",
    "tier",
)
_ENEMY_COMBATANT_CALLABLE_MEMBERS = _COMBATANT_CALLABLE_MEMBERS


@runtime_checkable
class Combatant(Protocol):
    @property
    def display_name(self):
        ...

    @property
    def health(self):
        ...

    @property
    def mana_resource(self):
        ...

    @property
    def super_resource(self):
        ...

    @property
    def generates_super(self):
        ...

    @property
    def can_defend(self):
        ...

    @property
    def combat_moves(self) -> Sequence[Move]:
        ...

    def effective_stat(self, name):
        ...

    def defend_reduction_percent(self, damage_type: DamageType):
        ...

    def is_alive(self):
        ...


@runtime_checkable
class EnemyCombatant(Combatant, Protocol):
    """Combat-facing identity required for an enemy Battle participant."""

    @property
    def archetype_id(self):
        ...

    @property
    def tier(self):
        ...


def is_combatant(value):
    return has_required_members(
        value,
        _COMBATANT_DATA_MEMBERS + _COMBATANT_CALLABLE_MEMBERS,
        _COMBATANT_CALLABLE_MEMBERS,
    )


def is_enemy_combatant(value):
    return has_required_members(
        value,
        _ENEMY_COMBATANT_DATA_MEMBERS + _ENEMY_COMBATANT_CALLABLE_MEMBERS,
        _ENEMY_COMBATANT_CALLABLE_MEMBERS,
    )

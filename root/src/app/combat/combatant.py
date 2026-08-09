"""Shared combat-facing protocol for runtime combatants."""

from typing import Protocol, Sequence, runtime_checkable

from app.combat.move import DamageType, Move


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

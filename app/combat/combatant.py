"""Shared combat-facing protocol for runtime combatants."""

from typing import Protocol, Sequence, runtime_checkable


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
    def combat_moves(self) -> Sequence[object]:
        ...

    def effective_stat(self, name):
        ...

    def is_alive(self):
        ...

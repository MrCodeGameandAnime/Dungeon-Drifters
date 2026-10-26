"""Immutable authored signature-weapon specifications."""

from collections.abc import Mapping
from dataclasses import dataclass

from app.items.weapon import Weapon
from app.readonly_mapping import readonly_mapping
from app.content.weapon_progression_spec import WeaponProgressionSpec


@dataclass(frozen=True)
class WeaponSpec:
    item_id: str
    persistence_key: str
    name: str
    weapon_type: str
    intended_wielder: str
    stat_bonuses: Mapping[str, int]
    value: int
    description: str
    progression: WeaponProgressionSpec | None = None

    def __post_init__(self):
        weapon = self._create_weapon()
        for name in (
            "item_id",
            "persistence_key",
            "name",
            "weapon_type",
            "intended_wielder",
            "value",
            "description",
        ):
            object.__setattr__(self, name, getattr(weapon, name))
        object.__setattr__(
            self,
            "stat_bonuses",
            readonly_mapping(weapon.stat_bonuses),
        )
        if self.progression is not None and not isinstance(
            self.progression,
            WeaponProgressionSpec,
        ):
            raise TypeError("progression must be a WeaponProgressionSpec")

    def _create_weapon(self):
        return Weapon(
            item_id=self.item_id,
            persistence_key=self.persistence_key,
            name=self.name,
            weapon_type=self.weapon_type,
            intended_wielder=self.intended_wielder,
            stat_bonuses=self.stat_bonuses,
            value=self.value,
            description=self.description,
        )

    def create_weapon(self):
        return self._create_weapon()


__all__ = ["WeaponSpec"]

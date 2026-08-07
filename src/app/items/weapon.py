from collections.abc import Mapping
import keyword
import re

from app.player.stats import PermanentStats


class Weapon:
    def __init__(
            self,
            item_id,
            persistence_key,
            name,
            weapon_type,
            intended_wielder,
            stat_bonuses,
            value,
            description):
        self._item_id = self._validate_item_id(item_id)
        self._persistence_key = self._validate_nonempty_string(
            "persistence_key",
            persistence_key,
        )
        self.name = self._validate_nonempty_string("name", name)
        self.weapon_type = self._validate_nonempty_string("weapon_type", weapon_type)
        self.intended_wielder = self._validate_nonempty_string(
            "intended_wielder",
            intended_wielder,
        )
        self._stat_bonuses = self._validate_stat_bonuses(stat_bonuses)
        self.value = self._validate_nonnegative_integer("value", value)
        self.description = self._validate_string("description", description)

    @property
    def item_id(self):
        return self._item_id

    @property
    def persistence_key(self):
        return self._persistence_key

    @property
    def stat_bonuses(self):
        return dict(self._stat_bonuses)

    @classmethod
    def _validate_item_id(cls, value):
        value = cls._validate_nonempty_string("item_id", value)
        if re.fullmatch(r"[a-z][a-z0-9_]*", value) is None or keyword.iskeyword(value):
            raise ValueError(
                "item_id must be a lowercase snake-case Python module name"
            )
        return value

    @classmethod
    def _validate_nonempty_string(cls, name, value):
        value = cls._validate_string(name, value)
        if not value:
            raise ValueError(f"{name} must not be empty")
        return value

    @staticmethod
    def _validate_string(name, value):
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string")
        return value

    @staticmethod
    def _validate_nonnegative_integer(name, value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")
        if value < 0:
            raise ValueError(f"{name} must not be negative")
        return value

    @classmethod
    def _validate_stat_bonuses(cls, stat_bonuses):
        if not isinstance(stat_bonuses, Mapping):
            raise TypeError("stat_bonuses must be a mapping")

        bonuses = {}
        for stat_name, bonus in stat_bonuses.items():
            PermanentStats._validate_stat_name(stat_name)
            bonuses[stat_name] = cls._validate_nonnegative_integer(
                f"stat_bonuses.{stat_name}",
                bonus,
            )
        return bonuses


__all__ = ["Weapon"]

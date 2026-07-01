from collections.abc import Mapping

from app.player.stats import PermanentStats


class Weapon:
    def __init__(
            self,
            name,
            weapon_type,
            intended_wielder,
            stat_bonuses,
            value,
            description):
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
    def stat_bonuses(self):
        return dict(self._stat_bonuses)

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


class SunderSpire(Weapon):
    def __init__(self):
        super().__init__(
            name="Sunder-Spire",
            weapon_type="Great Flamberge",
            intended_wielder="Branoc",
            stat_bonuses={
                "strength": 3,
                "constitution": 1,
            },
            value=2,
            description="A massive Deep-Iron flamberge forged from the broken weapons of Rhom-Ghal.",
        )


class SkyNeedle(Weapon):
    def __init__(self):
        super().__init__(
            name="Sky-Needle",
            weapon_type="Conductive Shakujō",
            intended_wielder="Joruun",
            stat_bonuses={
                "spirit": 2,
                "dexterity": 1,
                "intuition": 1,
            },
            value=2,
            description="An ash-wood shakujō fitted with copper collars and loose conductive rings.",
        )


class Sathren(Weapon):
    def __init__(self):
        super().__init__(
            name="Sathren",
            weapon_type="Alchemical Recurve Bow",
            intended_wielder="Zhaivra",
            stat_bonuses={
                "dexterity": 3,
                "intuition": 1,
            },
            value=2,
            description=(
                "A recurved bow grown from the bone-fiber of the Hollow Colossus "
                "and fitted with six alchemical reservoirs."
            ),
        )


class NeedleOfPlainIron(Weapon):
    def __init__(self):
        super().__init__(
            name="Needle of Plain Iron",
            weapon_type="Ritual Needle",
            intended_wielder="Azhvielle",
            stat_bonuses={
                "intelligence": 3,
                "spirit": 1,
            },
            value=2,
            description="A long, unadorned iron needle used as both a weapon and a precise ritual focus.",
        )

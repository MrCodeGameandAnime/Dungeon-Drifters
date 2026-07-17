"""Validated combat move definitions."""

from dataclasses import dataclass
from enum import StrEnum

from app.combat.move_presentation import MovePresentation


class MoveKind(StrEnum):
    DAMAGE = "damage"
    HEALING = "healing"
    UTILITY = "utility"


class ResourceType(StrEnum):
    NONE = "none"
    MANA = "mana"
    SUPER = "super"


class ScalingAttribute(StrEnum):
    NONE = "none"
    CONSTITUTION = "constitution"
    SPIRIT = "spirit"
    INTELLIGENCE = "intelligence"
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    INTUITION = "intuition"


class TargetType(StrEnum):
    ENEMY = "enemy"
    SELF = "self"


class DamageType(StrEnum):
    NONE = "none"
    PHYSICAL = "physical"
    MAGICAL = "magical"
    HYBRID = "hybrid"
    HEALING = "healing"


@dataclass(frozen=True)
class Move:
    name: str
    kind: MoveKind
    resource_type: ResourceType
    resource_cost: int
    power: int
    scales_with: tuple[ScalingAttribute, ...]
    accuracy: int
    target: TargetType
    damage_type: DamageType
    mechanic: str | None
    description: str
    presentation: MovePresentation | None = None
    is_spell: bool = False
    frost_backlash: bool = False

    def __post_init__(self):
        object.__setattr__(self, "name", _validate_nonempty_string("name", self.name))
        object.__setattr__(self, "kind", _validate_enum("kind", self.kind, MoveKind))
        object.__setattr__(
            self,
            "resource_type",
            _validate_enum("resource_type", self.resource_type, ResourceType),
        )
        object.__setattr__(
            self,
            "resource_cost",
            _validate_nonnegative_integer("resource_cost", self.resource_cost),
        )
        object.__setattr__(self, "power", _validate_nonnegative_integer("power", self.power))
        object.__setattr__(self, "scales_with", _validate_scaling_tuple(self.scales_with))
        object.__setattr__(self, "accuracy", _validate_accuracy(self.accuracy))
        object.__setattr__(self, "target", _validate_enum("target", self.target, TargetType))
        object.__setattr__(
            self,
            "damage_type",
            _validate_enum("damage_type", self.damage_type, DamageType),
        )
        object.__setattr__(self, "mechanic", _validate_optional_string("mechanic", self.mechanic))
        object.__setattr__(
            self,
            "description",
            _validate_nonempty_string("description", self.description),
        )
        object.__setattr__(
            self,
            "presentation",
            _validate_presentation(self.presentation),
        )
        object.__setattr__(self, "is_spell", _validate_bool("is_spell", self.is_spell))
        object.__setattr__(
            self,
            "frost_backlash",
            _validate_bool("frost_backlash", self.frost_backlash),
        )

        if self.resource_type == ResourceType.NONE and self.resource_cost != 0:
            raise ValueError("resource_type 'none' requires resource_cost 0")

    @property
    def mana_cost(self):
        if self.resource_type == ResourceType.MANA:
            return self.resource_cost
        if self.resource_type == ResourceType.NONE:
            return 0

        raise ValueError("mana_cost is only available for mana or no-cost moves")


def _validate_enum(name, value, enum_type):
    try:
        return enum_type(value)
    except ValueError as error:
        raise ValueError(f"invalid {name}: {value!r}") from error


def _validate_nonempty_string(name, value):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must not be empty")

    return value


def _validate_optional_string(name, value):
    if value is None:
        return None
    return _validate_nonempty_string(name, value)


def _validate_presentation(value):
    if value is None or isinstance(value, MovePresentation):
        return value

    raise TypeError("presentation must be MovePresentation or None")


def _validate_nonnegative_integer(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must not be negative")

    return value


def _validate_bool(name, value):
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a boolean")

    return value


def _validate_accuracy(value):
    value = _validate_nonnegative_integer("accuracy", value)
    if value > 100:
        raise ValueError("accuracy must be between 0 and 100")

    return value


def _validate_scaling_tuple(scales_with):
    if not isinstance(scales_with, tuple):
        raise TypeError("scales_with must be a tuple")
    if not scales_with:
        raise ValueError("scales_with must contain at least one scaling attribute")

    normalized = tuple(
        _validate_enum("scales_with", attribute, ScalingAttribute)
        for attribute in scales_with
    )

    if len(set(normalized)) != len(normalized):
        raise ValueError("scales_with must not contain duplicate attributes")
    if ScalingAttribute.NONE in normalized and len(normalized) > 1:
        raise ValueError("ScalingAttribute.NONE cannot be combined with other attributes")

    return normalized

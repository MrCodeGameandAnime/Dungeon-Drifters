"""Small, data-driven passive effects consumed by the combat resolver."""

from dataclasses import dataclass
from enum import StrEnum

from app.combat.move import DamageDefenseClass


class PassiveEffectKind(StrEnum):
    DAMAGE_OUTPUT = "damage_output"
    MITIGATION = "mitigation"
    ACCURACY = "accuracy"
    DODGE = "dodge"
    CRITICAL = "critical"
    MANA_COST = "mana_cost"
    SUPER_GAIN = "super_gain"
    STATUS_POTENCY = "status_potency"
    BRACE_INCOMING = "brace_incoming"
    BRACE_FOLLOW_UP = "brace_follow_up"


class PassiveEffectCondition(StrEnum):
    ALWAYS = "always"
    LOW_HEALTH = "low_health"
    HIGH_HEALTH = "high_health"
    LOW_MANA = "low_mana"
    HIGH_MANA = "high_mana"
    BRACE_READY = "brace_ready"
    ARCANE_OVERCHARGE = "arcane_overcharge"
    OWN_FROST = "own_frost"
    OWN_CONDUCTIVE_OR_TURBULENCE = "own_conductive_or_turbulence"
    LIGHTNING_STORM = "lightning_storm"
    TARGET_HAS_OWN_STATUS = "target_has_own_status"


@dataclass(frozen=True)
class PassiveCombatEffect:
    kind: PassiveEffectKind
    value: int
    damage_class: DamageDefenseClass | None = None
    mechanic: str | None = None
    condition: PassiveEffectCondition = PassiveEffectCondition.ALWAYS
    target_statuses: tuple[str, ...] = ()
    uses_intuition: bool = False

    def __post_init__(self):
        object.__setattr__(self, "kind", _enum(PassiveEffectKind, self.kind, "kind"))
        object.__setattr__(
            self,
            "condition",
            _enum(PassiveEffectCondition, self.condition, "condition"),
        )
        if isinstance(self.value, bool) or not isinstance(self.value, int):
            raise TypeError("passive effect value must be an integer")
        if self.value < 0:
            raise ValueError("passive effect value must not be negative")
        if self.damage_class is not None:
            object.__setattr__(
                self,
                "damage_class",
                _enum(DamageDefenseClass, self.damage_class, "damage_class"),
            )
        if self.kind in {PassiveEffectKind.DAMAGE_OUTPUT, PassiveEffectKind.MITIGATION}:
            if self.damage_class is None:
                raise ValueError(f"{self.kind.value} requires a damage class")
        elif self.damage_class is not None:
            raise ValueError(f"{self.kind.value} does not use a damage class")
        if self.mechanic is not None and (
            not isinstance(self.mechanic, str) or not self.mechanic
        ):
            raise ValueError("passive effect mechanic must be a non-empty string")
        if not isinstance(self.target_statuses, tuple) or any(
            not isinstance(status, str) or not status for status in self.target_statuses
        ):
            raise TypeError("target_statuses must be a tuple of non-empty strings")
        if len(set(self.target_statuses)) != len(self.target_statuses):
            raise ValueError("target_statuses must be unique")
        if self.condition is PassiveEffectCondition.TARGET_HAS_OWN_STATUS:
            if not self.target_statuses:
                raise ValueError("status conditions require target statuses")
        elif self.target_statuses:
            raise ValueError("target statuses require a status condition")
        if not isinstance(self.uses_intuition, bool):
            raise TypeError("uses_intuition must be a boolean")
        if self.uses_intuition and self.kind is not PassiveEffectKind.STATUS_POTENCY:
            raise ValueError("Intuition may only scale special status potency")


def _enum(enum_type, value, field):
    try:
        return enum_type(value)
    except ValueError as error:
        raise ValueError(f"invalid passive effect {field}: {value!r}") from error


__all__ = [
    "PassiveCombatEffect",
    "PassiveEffectCondition",
    "PassiveEffectKind",
]

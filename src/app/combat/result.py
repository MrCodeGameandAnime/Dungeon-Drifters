"""Validated combat move result values."""

from dataclasses import dataclass
from enum import StrEnum


class CombatOutcomeType(StrEnum):
    OVERCHARGE_CONSUMED = "overcharge_consumed"
    OVERCHARGE_GAINED = "overcharge_gained"
    BREAK_CLEARED = "break_cleared"
    BREAK_APPLIED = "break_applied"
    BACKLASH_DAMAGE = "backlash_damage"
    INSTABILITY_CLEARED = "instability_cleared"
    INSTABILITY_APPLIED = "instability_applied"
    COMPOUNDS_CONSUMED = "compounds_consumed"
    FIRE_INFUSION_PREPARED = "fire_infusion_prepared"
    POISON_INFUSION_PREPARED = "poison_infusion_prepared"
    INFUSED_BARB_CONSUMED = "infused_barb_consumed"
    BURN_APPLIED = "burn_applied"
    BURN_REFRESHED = "burn_refreshed"
    BURN_TICK = "burn_tick"
    BURN_EXPIRED = "burn_expired"
    POISON_APPLIED = "poison_applied"
    POISON_REFRESHED = "poison_refreshed"
    POISON_TICK = "poison_tick"
    POISON_EXPIRED = "poison_expired"
    CONDUCTIVE_APPLIED = "conductive_applied"
    CONDUCTIVE_REFRESHED = "conductive_refreshed"
    CONDUCTIVE_CONSUMED = "conductive_consumed"
    TURBULENCE_APPLIED = "turbulence_applied"
    TURBULENCE_REFRESHED = "turbulence_refreshed"
    TURBULENCE_CONSUMED = "turbulence_consumed"
    LIGHTNING_STORM_TRIGGERED = "lightning_storm_triggered"
    STUN_APPLIED = "stun_applied"
    STUN_TRIGGERED = "stun_triggered"
    STUN_EXPIRED = "stun_expired"
    FROST_APPLIED = "frost_applied"
    FROST_TRIGGERED = "frost_triggered"
    FROST_CHARGES_CONSUMED = "frost_charges_consumed"
    FROZEN_APPLIED = "frozen_applied"
    FROZEN_REFRESHED = "frozen_refreshed"
    FROZEN_TRIGGERED = "frozen_triggered"
    FROZEN_EXPIRED = "frozen_expired"
    FROSTBITE_APPLIED = "frostbite_applied"
    FROSTBITE_REFRESHED = "frostbite_refreshed"
    FROSTBITE_TICK = "frostbite_tick"
    FROSTBITE_EXPIRED = "frostbite_expired"
    FROST_BACKLASH_TRIGGERED = "frost_backlash_triggered"


class CombatOutcomeTarget(StrEnum):
    ACTOR = "actor"
    TARGET = "target"


@dataclass(frozen=True)
class CombatOutcome:
    outcome_type: CombatOutcomeType
    amount: int = 0
    target: CombatOutcomeTarget = CombatOutcomeTarget.TARGET
    charge_count: int | None = None

    def __post_init__(self):
        object.__setattr__(
            self,
            "outcome_type",
            _validate_enum("outcome_type", self.outcome_type, CombatOutcomeType),
        )
        object.__setattr__(self, "amount", _validate_nonnegative_integer("amount", self.amount))
        object.__setattr__(
            self,
            "target",
            _validate_enum("target", self.target, CombatOutcomeTarget),
        )
        if self.outcome_type == CombatOutcomeType.FROST_APPLIED:
            if self.charge_count not in (1, 2):
                raise ValueError("FROST_APPLIED charge_count must be 1 or 2")
        elif self.charge_count is not None:
            raise ValueError("charge_count is only valid for FROST_APPLIED")
        if self.outcome_type in (
            CombatOutcomeType.BACKLASH_DAMAGE,
            CombatOutcomeType.BURN_TICK,
            CombatOutcomeType.POISON_TICK,
            CombatOutcomeType.FROSTBITE_TICK,
        ):
            if self.target != CombatOutcomeTarget.ACTOR:
                raise ValueError("secondary damage must target the actor")
            if self.amount == 0:
                raise ValueError("secondary damage must be positive")
        elif self.outcome_type == CombatOutcomeType.FROST_BACKLASH_TRIGGERED:
            if self.target != CombatOutcomeTarget.ACTOR:
                raise ValueError("Frost backlash must target the actor")
        elif self.amount != 0:
            raise ValueError("state outcomes must have amount 0")


@dataclass(frozen=True)
class MoveResult:
    accepted: bool
    hit: bool
    move_name: str
    resource_spent: int
    damage: int
    healing: int
    statuses_applied: tuple[str, ...]
    reason: str | None
    critical: bool = False
    outcomes: tuple[CombatOutcome, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "accepted", _validate_bool("accepted", self.accepted))
        object.__setattr__(self, "hit", _validate_bool("hit", self.hit))
        object.__setattr__(self, "critical", _validate_bool("critical", self.critical))
        object.__setattr__(
            self,
            "outcomes",
            _validate_outcomes(self.outcomes),
        )
        object.__setattr__(self, "move_name", _validate_nonempty_string("move_name", self.move_name))
        object.__setattr__(
            self,
            "resource_spent",
            _validate_nonnegative_integer("resource_spent", self.resource_spent),
        )
        object.__setattr__(self, "damage", _validate_nonnegative_integer("damage", self.damage))
        object.__setattr__(self, "healing", _validate_nonnegative_integer("healing", self.healing))
        object.__setattr__(
            self,
            "statuses_applied",
            _validate_statuses(self.statuses_applied),
        )
        object.__setattr__(self, "reason", _validate_optional_string("reason", self.reason))


def _validate_bool(name, value):
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a boolean")

    return value


def _validate_nonnegative_integer(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must not be negative")

    return value


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


def _validate_statuses(statuses):
    if not isinstance(statuses, tuple):
        raise TypeError("statuses_applied must be a tuple")

    return tuple(
        _validate_nonempty_string("statuses_applied", status)
        for status in statuses
    )


def _validate_enum(name, value, enum_type):
    try:
        return enum_type(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"invalid {name}: {value!r}") from error


def _validate_outcomes(outcomes):
    if not isinstance(outcomes, tuple):
        raise TypeError("outcomes must be a tuple")
    if not all(isinstance(outcome, CombatOutcome) for outcome in outcomes):
        raise TypeError("outcomes must contain CombatOutcome values")
    return outcomes

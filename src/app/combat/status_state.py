"""Narrow encounter-local status ownership and standard Burn behavior."""

from dataclasses import dataclass
from enum import StrEnum

from app.combat.result import CombatOutcome, CombatOutcomeTarget, CombatOutcomeType


BURN_DURATION_TICKS = 3
BURN_BASE_DAMAGE = 2
BURN_STAT_DIVISOR = 5


class StatusKind(StrEnum):
    BURN = "burn"


@dataclass(frozen=True)
class BurnStatus:
    source: object
    target: object
    remaining_ticks: int
    damage_per_tick: int

    def __post_init__(self):
        _validate_positive_integer("remaining_ticks", self.remaining_ticks)
        _validate_positive_integer("damage_per_tick", self.damage_per_tick)


class StatusState:
    def __init__(self):
        self._burns = []

    def apply_burn(self, source, target):
        _validate_burn_source(source)
        _validate_burn_target(target)
        if not target.is_alive():
            raise ValueError("Burn cannot be applied to a defeated target")

        new_damage = burn_damage_per_tick(source)
        existing = self._find_burn(target)
        if existing is None:
            self._burns.append(
                BurnStatus(
                    source=source,
                    target=target,
                    remaining_ticks=BURN_DURATION_TICKS,
                    damage_per_tick=new_damage,
                )
            )
            return CombatOutcome(
                CombatOutcomeType.BURN_APPLIED,
                target=CombatOutcomeTarget.TARGET,
            )

        use_new_potency = new_damage > existing.damage_per_tick
        self._replace_burn(
            existing,
            BurnStatus(
                source=source if use_new_potency else existing.source,
                target=target,
                remaining_ticks=BURN_DURATION_TICKS,
                damage_per_tick=(
                    new_damage if use_new_potency else existing.damage_per_tick
                ),
            ),
        )
        return CombatOutcome(
            CombatOutcomeType.BURN_REFRESHED,
            target=CombatOutcomeTarget.TARGET,
        )

    def burn_active(self, target):
        return self._find_burn(target) is not None

    def burn_status(self, target):
        return self._find_burn(target)

    def advance_after_accepted_action(self, actor):
        burn = self._find_burn(actor)
        if burn is None:
            return ()
        if not actor.is_alive():
            self._remove_burn(burn)
            return (
                CombatOutcome(
                    CombatOutcomeType.BURN_EXPIRED,
                    target=CombatOutcomeTarget.ACTOR,
                ),
            )

        before = actor.health.current
        actor.health.take_damage(burn.damage_per_tick)
        actual_damage = before - actor.health.current
        remaining_ticks = burn.remaining_ticks - 1
        outcomes = [
            CombatOutcome(
                CombatOutcomeType.BURN_TICK,
                amount=actual_damage,
                target=CombatOutcomeTarget.ACTOR,
            )
        ]
        if remaining_ticks == 0 or not actor.is_alive():
            self._remove_burn(burn)
            outcomes.append(
                CombatOutcome(
                    CombatOutcomeType.BURN_EXPIRED,
                    target=CombatOutcomeTarget.ACTOR,
                )
            )
        else:
            self._replace_burn(
                burn,
                BurnStatus(
                    source=burn.source,
                    target=burn.target,
                    remaining_ticks=remaining_ticks,
                    damage_per_tick=burn.damage_per_tick,
                ),
            )
        return tuple(outcomes)

    def clear_defeated_target(self, target):
        burn = self._find_burn(target)
        if burn is None or target.is_alive():
            return False
        self._remove_burn(burn)
        return True

    def clear_all(self):
        self._burns.clear()

    def _find_burn(self, target):
        for burn in self._burns:
            if burn.target is target:
                return burn
        return None

    def _replace_burn(self, existing, replacement):
        self._burns = [
            replacement if burn is existing else burn
            for burn in self._burns
        ]

    def _remove_burn(self, burn):
        self._burns = [active for active in self._burns if active is not burn]


def burn_damage_per_tick(source):
    _validate_burn_source(source)
    intelligence = _validate_nonnegative_integer(
        "effective intelligence",
        source.effective_stat("intelligence"),
    )
    intuition = _validate_nonnegative_integer(
        "effective intuition",
        source.effective_stat("intuition"),
    )
    return max(
        1,
        BURN_BASE_DAMAGE
        + intelligence // BURN_STAT_DIVISOR
        + intuition // BURN_STAT_DIVISOR,
    )


def _validate_burn_source(source):
    if source is None or not callable(getattr(source, "effective_stat", None)):
        raise TypeError("Burn source must expose effective_stat")


def _validate_burn_target(target):
    if target is None or not callable(getattr(target, "is_alive", None)):
        raise TypeError("Burn target must expose is_alive")
    health = getattr(target, "health", None)
    if health is None or not callable(getattr(health, "take_damage", None)):
        raise TypeError("Burn target must expose mutable health")


def _validate_nonnegative_integer(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must not be negative")
    return value


def _validate_positive_integer(name, value):
    value = _validate_nonnegative_integer(name, value)
    if value == 0:
        raise ValueError(f"{name} must be positive")
    return value

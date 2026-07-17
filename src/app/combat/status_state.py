"""Narrow encounter-local ownership for reusable combat statuses."""

from dataclasses import dataclass
from enum import StrEnum

from app.combat.result import CombatOutcome, CombatOutcomeTarget, CombatOutcomeType


BURN_DURATION_TICKS = 3
POISON_DURATION_TICKS = 4
BURN_BASE_DAMAGE = 2
BURN_STAT_DIVISOR = 5
POISON_BASE_DAMAGE = 2
POISON_STAT_DIVISOR = 8


class StatusKind(StrEnum):
    BURN = "burn"
    POISON = "poison"
    CONDUCTIVE = "conductive"
    TURBULENCE = "turbulence"
    STUN = "stun"


@dataclass(frozen=True)
class BurnStatus:
    source: object
    target: object
    remaining_ticks: int
    damage_per_tick: int

    def __post_init__(self):
        _validate_positive_integer("remaining_ticks", self.remaining_ticks)
        _validate_positive_integer("damage_per_tick", self.damage_per_tick)


@dataclass(frozen=True)
class PoisonStatus:
    source: object
    target: object
    remaining_ticks: int
    damage_per_tick: int

    def __post_init__(self):
        _validate_positive_integer("remaining_ticks", self.remaining_ticks)
        _validate_positive_integer("damage_per_tick", self.damage_per_tick)


@dataclass(frozen=True)
class ConductiveStatus:
    source: object
    target: object


@dataclass(frozen=True)
class TurbulenceStatus:
    source: object
    target: object


@dataclass(frozen=True)
class StunStatus:
    source: object
    target: object


class StatusState:
    def __init__(self):
        self._burns = []
        self._poisons = []
        self._conductive_statuses = []
        self._turbulence_statuses = []
        self._stuns = []

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

    def apply_poison(self, source, target):
        _validate_status_source(source)
        _validate_status_target(target)
        if not target.is_alive():
            raise ValueError("Poison cannot be applied to a defeated target")

        new_damage = poison_damage_per_tick(source)
        existing = self._find_poison(target)
        if existing is None:
            self._poisons.append(
                PoisonStatus(
                    source=source,
                    target=target,
                    remaining_ticks=POISON_DURATION_TICKS,
                    damage_per_tick=new_damage,
                )
            )
            return CombatOutcome(
                CombatOutcomeType.POISON_APPLIED,
                target=CombatOutcomeTarget.TARGET,
            )

        use_new_potency = new_damage > existing.damage_per_tick
        self._replace_poison(
            existing,
            PoisonStatus(
                source=source if use_new_potency else existing.source,
                target=target,
                remaining_ticks=POISON_DURATION_TICKS,
                damage_per_tick=(
                    new_damage if use_new_potency else existing.damage_per_tick
                ),
            ),
        )
        return CombatOutcome(
            CombatOutcomeType.POISON_REFRESHED,
            target=CombatOutcomeTarget.TARGET,
        )

    def poison_active(self, target):
        return self._find_poison(target) is not None

    def poison_status(self, target):
        return self._find_poison(target)

    def apply_conductive(self, source, target):
        _validate_binary_status_combatants(source, target, "Conductive")
        existing = self._find_conductive(source, target)
        if existing is None:
            self._conductive_statuses.append(ConductiveStatus(source, target))
            outcome_type = CombatOutcomeType.CONDUCTIVE_APPLIED
        else:
            outcome_type = CombatOutcomeType.CONDUCTIVE_REFRESHED
        return CombatOutcome(outcome_type, target=CombatOutcomeTarget.TARGET)

    def conductive_active(self, source, target):
        return self._find_conductive(source, target) is not None

    def consume_conductive(self, source, target):
        status = self._find_conductive(source, target)
        if status is None:
            return None
        self._conductive_statuses = [
            active for active in self._conductive_statuses if active is not status
        ]
        return CombatOutcome(
            CombatOutcomeType.CONDUCTIVE_CONSUMED,
            target=CombatOutcomeTarget.TARGET,
        )

    def apply_turbulence(self, source, target):
        _validate_binary_status_combatants(source, target, "Turbulence")
        existing = self._find_turbulence(source, target)
        if existing is None:
            self._turbulence_statuses.append(TurbulenceStatus(source, target))
            outcome_type = CombatOutcomeType.TURBULENCE_APPLIED
        else:
            outcome_type = CombatOutcomeType.TURBULENCE_REFRESHED
        return CombatOutcome(outcome_type, target=CombatOutcomeTarget.TARGET)

    def turbulence_active(self, source, target):
        return self._find_turbulence(source, target) is not None

    def consume_turbulence(self, source, target):
        status = self._find_turbulence(source, target)
        if status is None:
            return None
        self._turbulence_statuses = [
            active for active in self._turbulence_statuses if active is not status
        ]
        return CombatOutcome(
            CombatOutcomeType.TURBULENCE_CONSUMED,
            target=CombatOutcomeTarget.TARGET,
        )

    def apply_stun(self, source, target):
        _validate_binary_status_combatants(source, target, "Stun")
        existing = self._find_stun(target)
        replacement = StunStatus(source, target)
        if existing is None:
            self._stuns.append(replacement)
        else:
            self._stuns = [
                replacement if active is existing else active
                for active in self._stuns
            ]
        return CombatOutcome(
            CombatOutcomeType.STUN_APPLIED,
            target=CombatOutcomeTarget.TARGET,
        )

    def stun_active(self, target):
        return self._find_stun(target) is not None

    def stun_status(self, target):
        return self._find_stun(target)

    def consume_stun_for_action_opportunity(self, actor):
        status = self._find_stun(actor)
        if status is None:
            return ()
        self._stuns = [active for active in self._stuns if active is not status]
        return (
            CombatOutcome(
                CombatOutcomeType.STUN_TRIGGERED,
                target=CombatOutcomeTarget.ACTOR,
            ),
            CombatOutcome(
                CombatOutcomeType.STUN_EXPIRED,
                target=CombatOutcomeTarget.ACTOR,
            ),
        )

    def active_status_kinds(self, target):
        active = []
        if self.burn_active(target):
            active.append(StatusKind.BURN)
        if self.poison_active(target):
            active.append(StatusKind.POISON)
        if any(status.target is target for status in self._conductive_statuses):
            active.append(StatusKind.CONDUCTIVE)
        if any(status.target is target for status in self._turbulence_statuses):
            active.append(StatusKind.TURBULENCE)
        if self.stun_active(target):
            active.append(StatusKind.STUN)
        return tuple(active)

    def advance_after_accepted_action(self, actor):
        if self._find_burn(actor) is None and self._find_poison(actor) is None:
            return ()
        if not actor.is_alive():
            return self._clear_defeated_statuses(actor)

        outcomes = list(self._advance_burn(actor))
        if actor.is_alive():
            outcomes.extend(self._advance_poison(actor))
        else:
            poison = self._find_poison(actor)
            if poison is not None:
                self._remove_poison(poison)
                outcomes.append(
                    CombatOutcome(
                        CombatOutcomeType.POISON_EXPIRED,
                        target=CombatOutcomeTarget.ACTOR,
                    )
                )
        return tuple(outcomes)

    def clear_defeated_target(self, target):
        if not self._has_status_associated_with(target) or target.is_alive():
            return False
        self._clear_defeated_statuses(target)
        return True

    def clear_defeated_target_outcomes(self, target):
        if not self._has_status_associated_with(target):
            return ()
        if not callable(getattr(target, "is_alive", None)) or target.is_alive():
            return ()
        return tuple(
            CombatOutcome(
                outcome.outcome_type,
                amount=outcome.amount,
                target=CombatOutcomeTarget.TARGET,
            )
            for outcome in self._clear_defeated_statuses(target)
        )

    def clear_all(self):
        self._burns.clear()
        self._poisons.clear()
        self._conductive_statuses.clear()
        self._turbulence_statuses.clear()
        self._stuns.clear()

    def _find_burn(self, target):
        for burn in self._burns:
            if burn.target is target:
                return burn
        return None

    def _find_poison(self, target):
        for poison in self._poisons:
            if poison.target is target:
                return poison
        return None

    def _find_conductive(self, source, target):
        for status in self._conductive_statuses:
            if status.source is source and status.target is target:
                return status
        return None

    def _find_turbulence(self, source, target):
        for status in self._turbulence_statuses:
            if status.source is source and status.target is target:
                return status
        return None

    def _find_stun(self, target):
        for status in self._stuns:
            if status.target is target:
                return status
        return None

    def _has_status_associated_with(self, combatant):
        return (
            self._find_burn(combatant) is not None
            or self._find_poison(combatant) is not None
            or any(
                status.source is combatant or status.target is combatant
                for status in self._conductive_statuses
            )
            or any(
                status.source is combatant or status.target is combatant
                for status in self._turbulence_statuses
            )
            or any(
                status.source is combatant or status.target is combatant
                for status in self._stuns
            )
        )

    def _advance_burn(self, actor):
        burn = self._find_burn(actor)
        if burn is None:
            return ()

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

    def _advance_poison(self, actor):
        poison = self._find_poison(actor)
        if poison is None:
            return ()

        before = actor.health.current
        actor.health.take_damage(poison.damage_per_tick)
        actual_damage = before - actor.health.current
        remaining_ticks = poison.remaining_ticks - 1
        outcomes = [
            CombatOutcome(
                CombatOutcomeType.POISON_TICK,
                amount=actual_damage,
                target=CombatOutcomeTarget.ACTOR,
            )
        ]
        if remaining_ticks == 0 or not actor.is_alive():
            self._remove_poison(poison)
            outcomes.append(
                CombatOutcome(
                    CombatOutcomeType.POISON_EXPIRED,
                    target=CombatOutcomeTarget.ACTOR,
                )
            )
            if not actor.is_alive():
                outcomes.extend(self._clear_defeated_statuses(actor))
        else:
            self._replace_poison(
                poison,
                PoisonStatus(
                    source=poison.source,
                    target=poison.target,
                    remaining_ticks=remaining_ticks,
                    damage_per_tick=poison.damage_per_tick,
                ),
            )
        return tuple(outcomes)

    def _clear_defeated_statuses(self, target):
        outcomes = []
        burn = self._find_burn(target)
        if burn is not None:
            self._remove_burn(burn)
            outcomes.append(
                CombatOutcome(
                    CombatOutcomeType.BURN_EXPIRED,
                    target=CombatOutcomeTarget.ACTOR,
                )
            )
        poison = self._find_poison(target)
        if poison is not None:
            self._remove_poison(poison)
            outcomes.append(
                CombatOutcome(
                    CombatOutcomeType.POISON_EXPIRED,
                    target=CombatOutcomeTarget.ACTOR,
                )
            )
        self._conductive_statuses = [
            status
            for status in self._conductive_statuses
            if status.source is not target and status.target is not target
        ]
        self._turbulence_statuses = [
            status
            for status in self._turbulence_statuses
            if status.source is not target and status.target is not target
        ]
        self._stuns = [
            status
            for status in self._stuns
            if status.source is not target and status.target is not target
        ]
        return tuple(outcomes)

    def _replace_burn(self, existing, replacement):
        self._burns = [
            replacement if burn is existing else burn
            for burn in self._burns
        ]

    def _remove_burn(self, burn):
        self._burns = [active for active in self._burns if active is not burn]

    def _replace_poison(self, existing, replacement):
        self._poisons = [
            replacement if poison is existing else poison
            for poison in self._poisons
        ]

    def _remove_poison(self, poison):
        self._poisons = [active for active in self._poisons if active is not poison]


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


def poison_damage_per_tick(source):
    _validate_status_source(source)
    dexterity = _validate_nonnegative_integer(
        "effective dexterity",
        source.effective_stat("dexterity"),
    )
    intuition = _validate_nonnegative_integer(
        "effective intuition",
        source.effective_stat("intuition"),
    )
    return max(
        1,
        POISON_BASE_DAMAGE
        + dexterity // POISON_STAT_DIVISOR
        + intuition // POISON_STAT_DIVISOR,
    )


def _validate_burn_source(source):
    _validate_status_source(source)


def _validate_status_source(source):
    if source is None or not callable(getattr(source, "effective_stat", None)):
        raise TypeError("status source must expose effective_stat")


def _validate_burn_target(target):
    _validate_status_target(target)


def _validate_status_target(target):
    if target is None or not callable(getattr(target, "is_alive", None)):
        raise TypeError("status target must expose is_alive")
    health = getattr(target, "health", None)
    if health is None or not callable(getattr(health, "take_damage", None)):
        raise TypeError("status target must expose mutable health")


def _validate_binary_status_combatants(source, target, status_name):
    _validate_status_source(source)
    _validate_status_target(target)
    if not target.is_alive():
        raise ValueError(f"{status_name} cannot be applied to a defeated target")


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

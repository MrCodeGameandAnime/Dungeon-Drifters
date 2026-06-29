"""Validated combat move result values."""

from dataclasses import dataclass


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

    def __post_init__(self):
        object.__setattr__(self, "accepted", _validate_bool("accepted", self.accepted))
        object.__setattr__(self, "hit", _validate_bool("hit", self.hit))
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

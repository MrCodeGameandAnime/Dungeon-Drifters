"""Inert authored presentation metadata for combat moves."""

from dataclasses import dataclass
from enum import StrEnum


class MoveRole(StrEnum):
    NORMAL = "normal"
    HEAVY = "heavy"
    UTILITY = "utility"
    HEALING = "healing"
    SUPER = "super"


@dataclass(frozen=True)
class MovePresentation:
    role: MoveRole
    affinity_label: str | None = None
    static_summary: str | None = None

    def __post_init__(self):
        object.__setattr__(self, "role", _validate_role(self.role))
        object.__setattr__(
            self,
            "affinity_label",
            _validate_optional_string("affinity_label", self.affinity_label),
        )
        object.__setattr__(
            self,
            "static_summary",
            _validate_optional_string("static_summary", self.static_summary),
        )


def _validate_role(value):
    try:
        return MoveRole(value)
    except ValueError as error:
        raise ValueError(f"invalid role: {value!r}") from error


def _validate_optional_string(name, value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must not be empty")

    return value

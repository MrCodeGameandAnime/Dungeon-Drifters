"""Lightweight persistence contract used by game-session orchestration."""

from enum import StrEnum

from app.runtime_contracts import has_required_members


class SaveLoadStatus(StrEnum):
    MISSING = "missing"
    VALID = "valid"
    LOADED = "loaded"
    INVALID = "invalid"


class SaveRepositoryError(RuntimeError):
    """Raised when an atomic save write cannot complete."""


_SAVE_REPOSITORY_CALLABLE_MEMBERS = (
    "save",
    "inspect",
    "load",
)


def is_save_repository(value):
    return has_required_members(
        value,
        _SAVE_REPOSITORY_CALLABLE_MEMBERS,
        _SAVE_REPOSITORY_CALLABLE_MEMBERS,
    )


__all__ = [
    "SaveLoadStatus",
    "SaveRepositoryError",
    "is_save_repository",
]

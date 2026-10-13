"""Lightweight save capability shared by gameplay and host composition."""

from enum import StrEnum

from app.runtime_contracts import has_required_members


class SaveLoadStatus(StrEnum):
    MISSING = "missing"
    VALID = "valid"
    LOADED = "loaded"
    SAVED = "saved"
    INVALID = "invalid"


class SavePortError(RuntimeError):
    """Raised when a host save operation cannot safely complete."""


_SAVE_PORT_METHODS = ("inspect", "save", "load")


def is_save_port(value):
    return has_required_members(value, _SAVE_PORT_METHODS, _SAVE_PORT_METHODS)


__all__ = ["SaveLoadStatus", "SavePortError", "is_save_port"]

"""Typed local profile persistence interfaces and operation results."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from app.game.game_state import GameState
from app.persistence.envelope import ConflictSnapshot, ProfileEnvelope
from app.runtime_contracts import has_required_members


class ProfileStoreStatus(StrEnum):
    MISSING = "missing"
    VALID = "valid"
    INVALID = "invalid"


class ConflictStoreStatus(StrEnum):
    MISSING = "missing"
    VALID = "valid"
    INVALID = "invalid"


class ProfileStoreError(RuntimeError):
    """Raised when a local profile operation cannot safely complete."""


class SaveLoadStatus(StrEnum):
    MISSING = "missing"
    VALID = "valid"
    LOADED = "loaded"
    SAVED = "saved"
    INVALID = "invalid"


class SavePortError(RuntimeError):
    """Raised when a save-port operation cannot safely complete."""


@dataclass(frozen=True)
class ProfileStoreResult:
    status: ProfileStoreStatus
    envelope: ProfileEnvelope | None = None
    error: str | None = None


@dataclass(frozen=True)
class ConflictStoreResult:
    status: ConflictStoreStatus
    snapshot: ConflictSnapshot | None = None
    error: str | None = None


@dataclass(frozen=True)
class SaveLoadResult:
    status: SaveLoadStatus
    game_state: GameState | None = None
    error: str | None = None
    migrated_from_schema_7: bool = False


class ProfileStore(Protocol):
    def inspect(self, profile_id: UUID) -> ProfileStoreResult: ...

    def load(self, profile_id: UUID) -> ProfileStoreResult: ...

    def save(self, envelope: ProfileEnvelope) -> None: ...

    def list_profiles(self) -> tuple[UUID, ...]: ...

    def load_conflict(self, profile_id: UUID) -> ConflictStoreResult: ...

    def save_conflict(self, snapshot: ConflictSnapshot) -> None: ...

    def clear_conflict(self, profile_id: UUID) -> None: ...


class SavePort(Protocol):
    def inspect(self) -> SaveLoadResult: ...

    def save(self, game_state: GameState) -> SaveLoadResult: ...

    def load(self) -> SaveLoadResult: ...


_SAVE_PORT_METHODS = ("inspect", "save", "load")


def is_save_port(value):
    return has_required_members(value, _SAVE_PORT_METHODS, _SAVE_PORT_METHODS)


__all__ = [
    "ConflictStoreResult",
    "ConflictStoreStatus",
    "ProfileStore",
    "ProfileStoreError",
    "ProfileStoreResult",
    "ProfileStoreStatus",
    "SaveLoadResult",
    "SaveLoadStatus",
    "SavePort",
    "SavePortError",
    "is_save_port",
]

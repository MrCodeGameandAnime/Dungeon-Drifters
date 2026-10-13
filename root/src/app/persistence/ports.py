"""Typed local profile persistence interfaces and operation results."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from app.game.game_state import GameState
from app.persistence.envelope import ConflictSnapshot, ProfileEnvelope
from app.persistence.save_port_contract import (
    SaveLoadStatus,
    SavePortError,
    is_save_port,
)


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

    def replace_conflict(
        self,
        expected: ConflictSnapshot,
        replacement: ConflictSnapshot,
    ) -> None: ...

    def clear_conflict(self, profile_id: UUID) -> None: ...

    def archive_recovery(
        self, envelope: ProfileEnvelope, snapshot: ConflictSnapshot | None = None
    ) -> None: ...

    def load_recovery_profile(
        self, profile_id: UUID, client_save_id: UUID
    ) -> ProfileStoreResult: ...

    def load_recovery_conflict(
        self, profile_id: UUID, client_save_id: UUID, remote_revision: int
    ) -> ConflictStoreResult: ...


class SavePort(Protocol):
    def inspect(self) -> SaveLoadResult: ...

    def save(self, game_state: GameState) -> SaveLoadResult: ...

    def load(self) -> SaveLoadResult: ...


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

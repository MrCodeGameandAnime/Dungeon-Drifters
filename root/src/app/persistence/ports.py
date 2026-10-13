"""Typed local profile persistence interfaces and operation results."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from app.persistence.envelope import ConflictSnapshot, ProfileEnvelope


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


class ProfileStore(Protocol):
    def inspect(self, profile_id: UUID) -> ProfileStoreResult: ...

    def load(self, profile_id: UUID) -> ProfileStoreResult: ...

    def save(self, envelope: ProfileEnvelope) -> None: ...

    def list_profiles(self) -> tuple[UUID, ...]: ...

    def load_conflict(self, profile_id: UUID) -> ConflictStoreResult: ...

    def save_conflict(self, snapshot: ConflictSnapshot) -> None: ...

    def clear_conflict(self, profile_id: UUID) -> None: ...


__all__ = [
    "ConflictStoreResult",
    "ConflictStoreStatus",
    "ProfileStore",
    "ProfileStoreError",
    "ProfileStoreResult",
    "ProfileStoreStatus",
]

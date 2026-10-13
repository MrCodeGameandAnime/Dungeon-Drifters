"""Non-destructive migration from the legacy bare game-state save."""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from uuid import UUID, uuid4

from app.persistence.envelope import build_profile_envelope
from app.persistence.ports import (
    ProfileStore,
    ProfileStoreError,
    ProfileStoreStatus,
)
from app.persistence.save_document import (
    DISK_SCHEMA_VERSION,
    reconstruct_game_state,
    validate_save_document,
)


class LegacyMigrationStatus(StrEnum):
    MIGRATED = "migrated"
    ALREADY_PRESENT = "already_present"
    MISSING = "missing"
    INVALID = "invalid"
    FAILED = "failed"


@dataclass(frozen=True)
class LegacyMigrationResult:
    status: LegacyMigrationStatus
    profile_id: UUID | None = None
    migrated_from_schema_7: bool = False
    error: str | None = None


def migrate_legacy_save(
    legacy_path,
    store: ProfileStore,
    *,
    profile_id_factory=uuid4,
    client_save_id_factory=uuid4,
    now_factory=lambda: datetime.now(timezone.utc),
):
    existing_profiles = store.list_profiles()
    if existing_profiles:
        return LegacyMigrationResult(
            status=LegacyMigrationStatus.ALREADY_PRESENT,
            profile_id=existing_profiles[0],
        )

    legacy_path = Path(legacy_path)
    if not legacy_path.exists():
        return LegacyMigrationResult(status=LegacyMigrationStatus.MISSING)

    try:
        document = json.loads(
            legacy_path.read_bytes().decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
        source_schema = document.get("schema_version")
        payload = validate_save_document(document)
        if payload["schema_version"] != DISK_SCHEMA_VERSION:
            raise ValueError("legacy save did not normalize to schema 8")
        reconstruct_game_state(payload)
    except (OSError, UnicodeDecodeError):
        return LegacyMigrationResult(
            status=LegacyMigrationStatus.FAILED,
            error="The legacy save could not be read; the original file was preserved.",
        )
    except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
        return LegacyMigrationResult(
            status=LegacyMigrationStatus.INVALID,
            error="The legacy save is invalid and was not modified.",
        )

    try:
        envelope = build_profile_envelope(
            payload,
            profile_id=profile_id_factory(),
            client_save_id=client_save_id_factory(),
            saved_at=now_factory(),
        )
        store.save(envelope)
        committed = store.load(envelope.profile_id)
        if (
            committed.status is not ProfileStoreStatus.VALID
            or committed.envelope != envelope
        ):
            raise ProfileStoreError("new profile did not validate after commit")
    except (OSError, ProfileStoreError, TypeError, ValueError):
        return LegacyMigrationResult(
            status=LegacyMigrationStatus.FAILED,
            error="The legacy save could not be migrated; the original file was preserved.",
        )

    return LegacyMigrationResult(
        status=LegacyMigrationStatus.MIGRATED,
        profile_id=envelope.profile_id,
        migrated_from_schema_7=source_schema == 7,
    )


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("legacy save contains duplicate object keys")
        result[key] = value
    return result


__all__ = [
    "LegacyMigrationResult",
    "LegacyMigrationStatus",
    "migrate_legacy_save",
]

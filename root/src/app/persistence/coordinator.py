"""Game-state persistence orchestration over a profile-store capability."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.game.game_state import GameState
from app.persistence.envelope import (
    ProfileEnvelopeValidationError,
    SyncState,
    build_profile_envelope,
)
from app.persistence.migration import LegacyMigrationStatus
from app.persistence.ports import (
    ProfileStore,
    ProfileStoreError,
    ProfileStoreStatus,
    SaveLoadResult,
    SaveLoadStatus,
)
from app.persistence.save_document import (
    build_save_document,
    reconstruct_game_state,
)


class SaveCoordinator:
    def __init__(
        self,
        store: ProfileStore,
        profile_id: UUID,
        *,
        migration_result=None,
        sync_coordinator=None,
        client_save_id_factory=uuid4,
        now_factory=lambda: datetime.now(timezone.utc),
    ):
        if not isinstance(profile_id, UUID):
            raise TypeError("profile_id must be a UUID")
        self._store = store
        self._profile_id = profile_id
        self._migration_result = migration_result
        if (
            sync_coordinator is not None
            and getattr(sync_coordinator, "profile_id", None) != profile_id
        ):
            raise ValueError("sync coordinator must use the same profile_id")
        self._sync_coordinator = sync_coordinator
        self._client_save_id_factory = client_save_id_factory
        self._now_factory = now_factory

    @property
    def profile_id(self):
        return self._profile_id

    def inspect(self):
        try:
            result = self._store.inspect(self._profile_id)
        except (OSError, ProfileStoreError):
            return SaveLoadResult(
                status=SaveLoadStatus.INVALID,
                error="The save file could not be inspected.",
            )
        if result.status is ProfileStoreStatus.VALID:
            return SaveLoadResult(status=SaveLoadStatus.VALID)
        if result.status is ProfileStoreStatus.INVALID:
            return SaveLoadResult(
                status=SaveLoadStatus.INVALID,
                error="The save file is invalid and was not loaded.",
            )
        if self._migration_failed:
            return SaveLoadResult(
                status=SaveLoadStatus.INVALID,
                error=self._migration_result.error
                or "The legacy save is invalid and was not loaded.",
            )
        return SaveLoadResult(status=SaveLoadStatus.MISSING)

    def save(self, game_state):
        if not isinstance(game_state, GameState):
            return SaveLoadResult(
                status=SaveLoadStatus.INVALID,
                error="The game could not be saved.",
            )
        try:
            current = self._store.load(self._profile_id)
            if current.status is ProfileStoreStatus.INVALID:
                return SaveLoadResult(
                    status=SaveLoadStatus.INVALID,
                    error="The local profile is invalid and was not replaced.",
                )
            payload = build_save_document(game_state)
            previous = current.envelope
            account_id = None if previous is None else previous.account_id
            remote_revision = (
                None if previous is None else previous.remote_revision
            )
            if account_id is None:
                sync_state = SyncState.LOCAL_ONLY
            elif previous.sync_state is SyncState.CONFLICT:
                sync_state = SyncState.CONFLICT
            else:
                sync_state = SyncState.PENDING
            envelope = build_profile_envelope(
                payload,
                profile_id=self._profile_id,
                account_id=account_id,
                remote_revision=remote_revision,
                local_sequence=(
                    1 if previous is None else previous.local_sequence + 1
                ),
                sync_state=sync_state,
                client_save_id=self._client_save_id_factory(),
                saved_at=self._now_factory(),
            )
            self._store.save(envelope)
            committed = self._store.load(self._profile_id)
            if (
                committed.status is not ProfileStoreStatus.VALID
                or committed.envelope != envelope
            ):
                raise ProfileStoreError("saved profile did not validate after commit")
        except (OSError, ProfileEnvelopeValidationError, ProfileStoreError, TypeError, ValueError):
            return SaveLoadResult(
                status=SaveLoadStatus.INVALID,
                error="The game could not be saved.",
            )
        if (
            self._sync_coordinator is not None
            and committed.envelope.sync_state is SyncState.PENDING
        ):
            self._sync_coordinator.sync_pending()
        return SaveLoadResult(status=SaveLoadStatus.SAVED)

    def load(self):
        try:
            result = self._store.load(self._profile_id)
        except (OSError, ProfileStoreError):
            return SaveLoadResult(
                status=SaveLoadStatus.INVALID,
                error="The save file could not be loaded.",
            )
        if result.status is ProfileStoreStatus.MISSING:
            if self._migration_failed:
                return SaveLoadResult(
                    status=SaveLoadStatus.INVALID,
                    error=self._migration_result.error
                    or "The legacy save is invalid and was not loaded.",
                )
            return SaveLoadResult(status=SaveLoadStatus.MISSING)
        if result.status is ProfileStoreStatus.INVALID:
            return SaveLoadResult(
                status=SaveLoadStatus.INVALID,
                error="The save file is invalid and was not loaded.",
            )
        try:
            game_state = reconstruct_game_state(result.envelope.payload)
            migrated_payload = build_save_document(game_state)
            if migrated_payload != result.envelope.payload:
                previous = result.envelope
                sync_state = previous.sync_state
                if sync_state is SyncState.CLEAN:
                    sync_state = SyncState.PENDING
                upgraded = build_profile_envelope(
                    migrated_payload,
                    profile_id=previous.profile_id,
                    account_id=previous.account_id,
                    remote_revision=previous.remote_revision,
                    local_sequence=previous.local_sequence + 1,
                    sync_state=sync_state,
                    client_save_id=self._client_save_id_factory(),
                    saved_at=self._now_factory(),
                )
                self._store.save(upgraded)
                committed = self._store.load(self._profile_id)
                if (
                    committed.status is not ProfileStoreStatus.VALID
                    or committed.envelope != upgraded
                ):
                    raise ProfileStoreError(
                        "migrated profile did not validate after commit"
                    )
        except (TypeError, ValueError):
            return SaveLoadResult(
                status=SaveLoadStatus.INVALID,
                error="The save file is invalid and was not loaded.",
            )
        except (OSError, ProfileStoreError, ProfileEnvelopeValidationError):
            return SaveLoadResult(
                status=SaveLoadStatus.INVALID,
                error="The save file could not be upgraded safely.",
            )
        return SaveLoadResult(
            status=SaveLoadStatus.LOADED,
            game_state=game_state,
            migrated_from_schema_7=(
                self._migration_result is not None
                and self._migration_result.status is LegacyMigrationStatus.MIGRATED
                and self._migration_result.migrated_from_schema_7
            ),
        )

    @property
    def _migration_failed(self):
        return bool(
            self._migration_result is not None
            and self._migration_result.status
            in {LegacyMigrationStatus.INVALID, LegacyMigrationStatus.FAILED}
        )


__all__ = ["SaveCoordinator"]

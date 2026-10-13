"""Offline-first synchronization for local DD profiles and the v1 profile API."""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.persistence.envelope import (
    ConflictSnapshot,
    ProfileEnvelope,
    ProfileEnvelopeValidationError,
    SyncState,
    build_conflict_snapshot,
    build_profile_envelope,
)
from app.persistence.ports import (
    ConflictStoreStatus,
    ProfileStoreStatus,
)
from app.persistence.remote_client import (
    RemoteAuthenticationRequired,
    RemoteConflict,
    RemoteProfileClient,
    RemoteProfileCreationConflict,
    RemoteProfileError,
    RemoteProfileHead,
    RemoteProfileNotFound,
    RemoteProtocolError,
    RemoteRequestRejected,
    RemoteUnavailable,
)


_UNSET = object()


@dataclass(frozen=True)
class SyncResult:
    sync_state: SyncState | None
    remote_available: bool | None = None
    error: str | None = None
    profile_id: UUID | None = None


class ProfileSyncCoordinator:
    def __init__(
        self,
        store,
        profile_id,
        remote_client: RemoteProfileClient,
        *,
        client_save_id_factory=uuid4,
        now_factory=lambda: datetime.now(timezone.utc),
    ):
        if not isinstance(profile_id, UUID):
            raise TypeError("profile_id must be a UUID")
        if not callable(getattr(remote_client, "get_profile", None)):
            raise TypeError("remote_client must implement the profile API")
        self._store = store
        self._profile_id = profile_id
        self._remote = remote_client
        self._client_save_id_factory = client_save_id_factory
        self._now_factory = now_factory

    @property
    def profile_id(self):
        return self._profile_id

    def enable_cloud(self, account_id):
        if not isinstance(account_id, UUID):
            raise TypeError("account_id must be a UUID")
        loaded = self._store.load(self._profile_id)
        if loaded.status is not ProfileStoreStatus.VALID:
            return self._result(None, error="local_profile_unavailable")
        envelope = loaded.envelope
        if envelope.account_id is not None:
            if envelope.account_id != account_id:
                return self._result(envelope, error="account_mismatch")
            return self.sync_pending()
        self._store.save(
            self._copy_envelope(
                envelope,
                account_id=account_id,
                remote_revision=None,
                sync_state=SyncState.PENDING,
            )
        )
        return self.sync_pending()

    def download_remote(self):
        loaded = self._store.load(self._profile_id)
        if loaded.status is ProfileStoreStatus.VALID:
            return self.refresh()
        if loaded.status is not ProfileStoreStatus.MISSING:
            return self._result(None, error="local_profile_invalid")
        try:
            head = self._remote.get_profile(self._profile_id)
            envelope = build_profile_envelope(
                head.payload,
                profile_id=head.profile_id,
                account_id=head.account_id,
                remote_revision=head.current_revision,
                local_sequence=1,
                sync_state=SyncState.CLEAN,
                client_save_id=head.client_save_id,
                saved_at=self._now_factory(),
            )
            self._store.save(envelope)
        except (RemoteProfileError, RemoteProtocolError) as error:
            return self._remote_error(None, error)
        except ProfileEnvelopeValidationError:
            return self._result(None, remote_available=True, error="invalid_remote_profile")
        return self._result(envelope, remote_available=True)

    def refresh(self):
        loaded = self._store.load(self._profile_id)
        if loaded.status is not ProfileStoreStatus.VALID:
            return self._result(None, error="local_profile_unavailable")
        envelope = loaded.envelope
        if envelope.sync_state is SyncState.LOCAL_ONLY:
            return self._result(envelope)
        if envelope.sync_state is SyncState.PENDING:
            return self.sync_pending()
        if envelope.sync_state is SyncState.CONFLICT:
            return self._result(envelope, remote_available=False)
        try:
            head = self._remote.get_profile(self._profile_id)
            self._require_same_account(envelope, head)
            if head.current_revision < envelope.remote_revision:
                return self._result(
                    envelope, remote_available=True, error="remote_revision_regressed"
                )
            if head.current_revision == envelope.remote_revision:
                if head.payload_sha256 != envelope.payload_sha256:
                    return self._result(
                        envelope,
                        remote_available=True,
                        error="remote_revision_mismatch",
                    )
                return self._result(envelope, remote_available=True)
            if head.payload_sha256 == envelope.payload_sha256:
                updated = self._copy_envelope(
                    envelope,
                    remote_revision=head.current_revision,
                    sync_state=SyncState.CLEAN,
                )
            else:
                updated = build_profile_envelope(
                    head.payload,
                    profile_id=self._profile_id,
                    account_id=envelope.account_id,
                    remote_revision=head.current_revision,
                    local_sequence=envelope.local_sequence + 1,
                    sync_state=SyncState.CLEAN,
                    client_save_id=self._new_save_id(envelope.client_save_id),
                    saved_at=self._now_factory(),
                )
            self._store.save(updated)
            return self._result(updated, remote_available=True)
        except (RemoteProfileError, RemoteProtocolError) as error:
            return self._remote_error(envelope, error)
        except ProfileEnvelopeValidationError:
            return self._result(
                envelope, remote_available=True, error="invalid_remote_profile"
            )

    def sync_pending(self):
        loaded = self._store.load(self._profile_id)
        if loaded.status is not ProfileStoreStatus.VALID:
            return self._result(None, error="local_profile_unavailable")
        envelope = loaded.envelope
        if envelope.sync_state is SyncState.LOCAL_ONLY:
            return self._result(envelope)
        if envelope.sync_state is SyncState.CONFLICT:
            return self._result(envelope, remote_available=False)
        local_conflict = self._store.load_conflict(self._profile_id)
        if local_conflict.status is ConflictStoreStatus.INVALID:
            return self._result(
                envelope, error="local_conflict_invalid", remote_available=False
            )
        if local_conflict.status is ConflictStoreStatus.VALID:
            conflict_envelope = self._copy_envelope(
                envelope,
                remote_revision=local_conflict.snapshot.base_remote_revision,
                sync_state=SyncState.CONFLICT,
            )
            self._store.save(conflict_envelope)
            return self._result(conflict_envelope, remote_available=False)
        if envelope.sync_state is not SyncState.PENDING:
            return self._result(envelope)
        try:
            if envelope.remote_revision is None:
                return self._claim_pending(envelope)
            return self._push_pending(envelope)
        except (RemoteProfileError, RemoteProtocolError) as error:
            return self._remote_error(envelope, error)

    def resolve_use_remote(self):
        loaded = self._load_conflicted_profile()
        if isinstance(loaded, SyncResult):
            return loaded
        envelope, snapshot = loaded
        try:
            head = self._remote.get_profile(self._profile_id)
            self._require_same_account(envelope, head)
            self._store.archive_recovery(envelope, snapshot)
            if head.payload_sha256 == envelope.payload_sha256:
                updated = self._copy_envelope(
                    envelope,
                    remote_revision=head.current_revision,
                    sync_state=SyncState.CLEAN,
                )
            else:
                updated = build_profile_envelope(
                    head.payload,
                    profile_id=self._profile_id,
                    account_id=envelope.account_id,
                    remote_revision=head.current_revision,
                    local_sequence=envelope.local_sequence + 1,
                    sync_state=SyncState.CLEAN,
                    client_save_id=self._new_save_id(envelope.client_save_id),
                    saved_at=self._now_factory(),
                )
            self._store.save(updated)
            self._store.clear_conflict(self._profile_id)
            return self._result(updated, remote_available=True)
        except (RemoteProfileError, RemoteProtocolError) as error:
            return self._remote_error(envelope, error)
        except ProfileEnvelopeValidationError:
            return self._result(
                envelope, remote_available=True, error="invalid_remote_profile"
            )

    def resolve_keep_local(self):
        loaded = self._load_conflicted_profile()
        if isinstance(loaded, SyncResult):
            return loaded
        envelope, snapshot = loaded
        try:
            head = self._remote.get_profile(self._profile_id)
            self._require_same_account(envelope, head)
            if head.payload_sha256 == envelope.payload_sha256:
                return self._finish_keep_local(envelope, snapshot, head)
            pushed = self._remote.push_progression(
                self._profile_id,
                head.current_revision,
                envelope.client_save_id,
                envelope.payload,
            )
            if isinstance(pushed, RemoteConflict):
                latest = self._remote.get_profile(self._profile_id)
                if latest.payload_sha256 == envelope.payload_sha256:
                    return self._finish_keep_local(envelope, snapshot, latest)
                return self._record_conflict(
                    envelope, head.current_revision, latest
                )
            if pushed.payload_sha256 == envelope.payload_sha256:
                return self._finish_keep_local(envelope, snapshot, pushed)
            latest = self._remote.get_profile(self._profile_id)
            if latest.payload_sha256 == envelope.payload_sha256:
                return self._finish_keep_local(envelope, snapshot, latest)
            base_revision = pushed.accepted_revision or head.current_revision
            return self._record_conflict(envelope, base_revision, latest)
        except (RemoteProfileError, RemoteProtocolError) as error:
            return self._remote_error(envelope, error)

    def fork_local(self, new_profile_id, client_save_id=None):
        loaded = self._load_conflicted_profile()
        if isinstance(loaded, SyncResult):
            return loaded
        source_envelope, _ = loaded
        if not isinstance(new_profile_id, UUID) or new_profile_id == self._profile_id:
            raise TypeError("new_profile_id must be a different UUID")
        existing = self._store.load(new_profile_id)
        if existing.status is ProfileStoreStatus.INVALID:
            return self._result(
                source_envelope,
                error="fork_local_profile_invalid",
                profile_id=new_profile_id,
            )
        if existing.status is ProfileStoreStatus.VALID:
            fork = existing.envelope
            if (
                fork.account_id != source_envelope.account_id
                or fork.payload_sha256 != source_envelope.payload_sha256
                or fork.sync_state not in {SyncState.PENDING, SyncState.CLEAN}
            ):
                return self._result(
                    source_envelope,
                    error="fork_profile_mismatch",
                    profile_id=new_profile_id,
                )
            if client_save_id is not None and client_save_id != fork.client_save_id:
                return self._result(
                    source_envelope,
                    error="fork_profile_mismatch",
                    profile_id=new_profile_id,
                )
            if fork.sync_state is SyncState.CLEAN:
                return self._result(
                    fork, remote_available=False, profile_id=new_profile_id
                )
        else:
            client_save_id = (
                self._client_save_id_factory()
                if client_save_id is None
                else client_save_id
            )
            if not isinstance(client_save_id, UUID):
                raise TypeError("client_save_id must be a UUID")
            fork = build_profile_envelope(
                source_envelope.payload,
                profile_id=new_profile_id,
                account_id=source_envelope.account_id,
                remote_revision=None,
                local_sequence=1,
                sync_state=SyncState.PENDING,
                client_save_id=client_save_id,
                saved_at=self._now_factory(),
            )
            self._store.save(fork)
        try:
            head = self._remote.create_profile(
                new_profile_id, fork.client_save_id, fork.payload
            )
        except RemoteProfileCreationConflict:
            try:
                head = self._remote.get_profile(new_profile_id)
            except (RemoteProfileError, RemoteProtocolError) as error:
                return self._remote_error(
                    fork, error, profile_id=new_profile_id
                )
        except (RemoteProfileError, RemoteProtocolError) as error:
            return self._remote_error(fork, error, profile_id=new_profile_id)
        try:
            if (
                head.profile_id != new_profile_id
                or head.account_id != source_envelope.account_id
                or head.payload_sha256 != fork.payload_sha256
            ):
                return self._result(
                    fork,
                    remote_available=True,
                    error="fork_profile_mismatch",
                    profile_id=new_profile_id,
                )
            clean_fork = self._copy_envelope(
                fork,
                remote_revision=head.current_revision,
                sync_state=SyncState.CLEAN,
            )
            self._store.save(clean_fork)
            return self._result(
                clean_fork, remote_available=True, profile_id=new_profile_id
            )
        except ProfileEnvelopeValidationError:
            return self._result(
                fork,
                remote_available=True,
                error="invalid_remote_profile",
                profile_id=new_profile_id,
            )

    def _claim_pending(self, envelope):
        try:
            head = self._remote.create_profile(
                self._profile_id,
                envelope.client_save_id,
                envelope.payload,
            )
        except RemoteProfileCreationConflict:
            head = self._remote.get_profile(self._profile_id)
            self._require_same_account(envelope, head)
            if head.payload_sha256 == envelope.payload_sha256:
                return self._mark_clean(envelope, head)
            if head.current_revision > 1:
                return self._record_conflict(
                    envelope, head.created_revision or 1, head
                )
            return self._result(
                envelope,
                remote_available=True,
                error="profile_claim_conflict",
            )
        except RemoteProfileNotFound:
            local_only = self._copy_envelope(
                envelope,
                account_id=None,
                remote_revision=None,
                sync_state=SyncState.LOCAL_ONLY,
            )
            self._store.save(local_only)
            return self._result(
                local_only, remote_available=True, error="profile_unavailable"
            )
        self._require_same_account(envelope, head)
        if head.payload_sha256 == envelope.payload_sha256:
            return self._mark_clean(envelope, head)
        if head.current_revision > 1:
            return self._record_conflict(
                envelope, head.created_revision or 1, head
            )
        return self._result(
            envelope, remote_available=True, error="profile_claim_conflict"
        )

    def _push_pending(self, envelope):
        pushed = self._remote.push_progression(
            self._profile_id,
            envelope.remote_revision,
            envelope.client_save_id,
            envelope.payload,
        )
        if isinstance(pushed, RemoteConflict):
            head = self._remote.get_profile(self._profile_id)
            self._require_same_account(envelope, head)
            if head.payload_sha256 == envelope.payload_sha256:
                return self._mark_clean(envelope, head)
            return self._record_conflict(
                envelope, pushed.base_revision, head
            )
        self._require_same_account(envelope, pushed)
        if pushed.payload_sha256 == envelope.payload_sha256:
            return self._mark_clean(envelope, pushed)
        latest = self._remote.get_profile(self._profile_id)
        if latest.payload_sha256 == envelope.payload_sha256:
            return self._mark_clean(envelope, latest)
        base_revision = pushed.accepted_revision or envelope.remote_revision
        return self._record_conflict(envelope, base_revision, latest)

    def _record_conflict(self, envelope, base_revision, head):
        if head.current_revision <= base_revision:
            return self._result(
                envelope,
                remote_available=True,
                error="remote_conflict_head_invalid",
            )
        existing = self._store.load_conflict(self._profile_id)
        if existing.status is ConflictStoreStatus.INVALID:
            return self._result(
                envelope,
                remote_available=True,
                error="local_conflict_invalid",
            )
        if existing.status is ConflictStoreStatus.VALID:
            if (
                existing.snapshot.base_remote_revision == base_revision
                and existing.snapshot.remote_current_revision == head.current_revision
                and existing.snapshot.local_payload_sha256 == envelope.payload_sha256
                and existing.snapshot.remote_payload_sha256 == head.payload_sha256
            ):
                conflict_envelope = self._copy_envelope(
                    envelope,
                    remote_revision=base_revision,
                    sync_state=SyncState.CONFLICT,
                )
                if envelope.sync_state is not SyncState.CONFLICT:
                    self._store.save(conflict_envelope)
                return self._result(conflict_envelope, remote_available=True)
            self._store.archive_recovery(envelope, existing.snapshot)
            self._store.clear_conflict(self._profile_id)
        snapshot = build_conflict_snapshot(
            profile_id=self._profile_id,
            local_client_save_id=envelope.client_save_id,
            local_payload=envelope.payload,
            base_remote_revision=base_revision,
            remote_current_revision=head.current_revision,
            remote_payload=head.payload,
            detected_at=self._now_factory(),
        )
        self._store.save_conflict(snapshot)
        conflict_envelope = self._copy_envelope(
            envelope,
            remote_revision=base_revision,
            sync_state=SyncState.CONFLICT,
        )
        if (
            envelope.sync_state is not SyncState.CONFLICT
            or envelope.remote_revision != base_revision
        ):
            self._store.save(conflict_envelope)
        return self._result(conflict_envelope, remote_available=True)

    def _finish_keep_local(self, envelope, snapshot, head):
        self._require_same_account(envelope, head)
        if head.payload_sha256 != envelope.payload_sha256:
            return self._result(
                envelope, remote_available=True, error="keep_local_not_current"
            )
        self._store.archive_recovery(envelope, snapshot)
        updated = self._copy_envelope(
            envelope,
            remote_revision=head.current_revision,
            sync_state=SyncState.CLEAN,
        )
        self._store.save(updated)
        self._store.clear_conflict(self._profile_id)
        return self._result(updated, remote_available=True)

    def _load_conflicted_profile(self):
        loaded = self._store.load(self._profile_id)
        if loaded.status is not ProfileStoreStatus.VALID:
            return self._result(None, error="local_profile_unavailable")
        envelope = loaded.envelope
        conflict = self._store.load_conflict(self._profile_id)
        if envelope.sync_state is not SyncState.CONFLICT:
            return self._result(envelope, error="profile_not_conflicted")
        if conflict.status is not ConflictStoreStatus.VALID:
            return self._result(envelope, error="local_conflict_unavailable")
        return envelope, conflict.snapshot

    def _mark_clean(self, envelope, head):
        self._require_same_account(envelope, head)
        if head.payload_sha256 != envelope.payload_sha256:
            raise RemoteProtocolError("accepted payload differs from local save")
        updated = self._copy_envelope(
            envelope,
            remote_revision=head.current_revision,
            sync_state=SyncState.CLEAN,
        )
        self._store.save(updated)
        return self._result(updated, remote_available=True)

    def _copy_envelope(
        self,
        envelope,
        *,
        payload=None,
        account_id=_UNSET,
        remote_revision=_UNSET,
        local_sequence=None,
        sync_state=None,
        client_save_id=None,
    ):
        return build_profile_envelope(
            envelope.payload if payload is None else payload,
            profile_id=envelope.profile_id,
            account_id=(envelope.account_id if account_id is _UNSET else account_id),
            remote_revision=(
                envelope.remote_revision
                if remote_revision is _UNSET
                else remote_revision
            ),
            local_sequence=(
                envelope.local_sequence if local_sequence is None else local_sequence
            ),
            sync_state=envelope.sync_state if sync_state is None else sync_state,
            client_save_id=(
                envelope.client_save_id
                if client_save_id is None
                else client_save_id
            ),
            saved_at=self._now_factory(),
        )

    def _new_save_id(self, previous):
        save_id = self._client_save_id_factory()
        if not isinstance(save_id, UUID) or save_id == previous:
            raise ValueError("client_save_id_factory must return a new UUID")
        return save_id

    def _require_same_account(self, envelope, head):
        if (
            not isinstance(head, RemoteProfileHead)
            or head.profile_id != self._profile_id
            or head.account_id != envelope.account_id
        ):
            raise RemoteProtocolError("remote profile identity did not match local account")

    def _remote_error(self, envelope, error, *, profile_id=None):
        if isinstance(error, RemoteUnavailable):
            return self._result(
                envelope,
                remote_available=False,
                error="offline",
                profile_id=profile_id,
            )
        if isinstance(error, RemoteAuthenticationRequired):
            code = "authentication_required"
        elif isinstance(error, RemoteProfileNotFound):
            code = "profile_unavailable"
        elif isinstance(error, RemoteProtocolError):
            code = "invalid_remote_response"
        elif isinstance(error, RemoteRequestRejected):
            code = error.code
        else:
            code = "remote_request_failed"
        return self._result(
            envelope,
            remote_available=True,
            error=code,
            profile_id=profile_id,
        )

    def _result(
        self,
        envelope,
        *,
        remote_available=None,
        error=None,
        profile_id=None,
    ):
        return SyncResult(
            sync_state=None if envelope is None else envelope.sync_state,
            remote_available=remote_available,
            error=error,
            profile_id=self._profile_id if profile_id is None else profile_id,
        )


__all__ = ["ProfileSyncCoordinator", "SyncResult"]

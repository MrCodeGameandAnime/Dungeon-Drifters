from datetime import datetime, timezone
from uuid import UUID

from app.persistence.coordinator import SaveCoordinator
from app.persistence.envelope import SyncState, build_profile_envelope
from app.persistence.local_store import LocalProfileStore, ProfileStoreError
from app.persistence.ports import ConflictStoreStatus, SaveLoadStatus
from app.persistence.sync import ProfileSyncCoordinator
from tests.remote_sync_test_support import (
    ACCOUNT_ID,
    DEVICE_A,
    DEVICE_B,
    PROFILE_ID,
    SAVE_A,
    BoundMemoryRemoteClient,
    MemoryRemoteProfileServer,
    SAVE_C,
    make_payload,
)


SAVED_AT = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
NEW_PROFILE_ID = UUID("00000000-0000-4000-8000-000000000007")
NEW_SAVE_ID = UUID("00000000-0000-4000-8000-000000000008")
SAVE_D = UUID("00000000-0000-4000-8000-000000000009")


def _state(gold=0):
    from app.content.catalog import get_drifter_spec_by_choice
    from app.game.game_state import GameState
    from app.player.player_state import PlayerState

    character = get_drifter_spec_by_choice("1").create_character()
    return GameState(PlayerState(character, gold=gold))


def _two_diverged_devices(tmp_path):
    server = MemoryRemoteProfileServer()
    store_a = LocalProfileStore(tmp_path / "device-a")
    store_b = LocalProfileStore(tmp_path / "device-b")
    SaveCoordinator(store_a, PROFILE_ID, now_factory=lambda: SAVED_AT).save(_state())
    sync_a = ProfileSyncCoordinator(
        store_a,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_A),
        now_factory=lambda: SAVED_AT,
    )
    sync_a.enable_cloud(ACCOUNT_ID)
    sync_b = ProfileSyncCoordinator(
        store_b,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_B),
        now_factory=lambda: SAVED_AT,
    )
    assert sync_b.download_remote().sync_state is SyncState.CLEAN
    SaveCoordinator(
        store_a,
        PROFILE_ID,
        sync_coordinator=sync_a,
        now_factory=lambda: SAVED_AT,
    ).save(_state(gold=20))

    server.available = False
    local_result = SaveCoordinator(
        store_b,
        PROFILE_ID,
        sync_coordinator=sync_b,
        now_factory=lambda: SAVED_AT,
    ).save(_state(gold=99))
    assert local_result.status is SaveLoadStatus.SAVED
    server.available = True
    conflict_result = sync_b.sync_pending()

    return server, store_b, sync_b, conflict_result


def test_stale_second_device_save_preserves_both_branches_without_overwrite(tmp_path):
    server, store, _, result = _two_diverged_devices(tmp_path)
    local = store.load(PROFILE_ID).envelope
    conflict = store.load_conflict(PROFILE_ID).snapshot
    remote = server.get_profile(ACCOUNT_ID, PROFILE_ID)

    assert result.sync_state is SyncState.CONFLICT
    assert local.sync_state is SyncState.CONFLICT
    assert local.payload == make_payload(gold=99)
    assert local.remote_revision == 1
    assert conflict.base_remote_revision == 1
    assert conflict.remote_current_revision == 2
    assert conflict.remote_payload == make_payload(gold=20)
    assert remote.current_revision == 2
    assert remote.payload == make_payload(gold=20)


def test_clean_resolution_with_superseded_conflict_residue_does_not_resurrect(
    tmp_path,
):
    server, store, sync, _ = _two_diverged_devices(tmp_path)
    conflicted = store.load(PROFILE_ID).envelope
    snapshot = store.load_conflict(PROFILE_ID).snapshot
    head = server.get_profile(ACCOUNT_ID, PROFILE_ID)
    clean = build_profile_envelope(
        head.payload,
        profile_id=PROFILE_ID,
        account_id=ACCOUNT_ID,
        remote_revision=head.current_revision,
        local_sequence=conflicted.local_sequence + 1,
        sync_state=SyncState.CLEAN,
        client_save_id=head.client_save_id,
        saved_at=SAVED_AT,
    )
    store.save(clean)
    store = LocalProfileStore(store.root)
    fresh_sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_B),
        now_factory=lambda: SAVED_AT,
    )

    result = fresh_sync.sync_pending()

    assert result.sync_state is SyncState.CLEAN
    assert store.load(PROFILE_ID).envelope == clean
    assert store.load_conflict(PROFILE_ID).status is ConflictStoreStatus.MISSING
    assert store.load_recovery_conflict(
        PROFILE_ID,
        snapshot.local_client_save_id,
        snapshot.remote_current_revision,
    ).snapshot == snapshot


def test_pending_envelope_with_valid_conflict_evidence_completes_transition(
    tmp_path,
):
    server, store, _, _ = _two_diverged_devices(tmp_path)
    conflicted = store.load(PROFILE_ID).envelope
    snapshot = store.load_conflict(PROFILE_ID).snapshot
    pending = build_profile_envelope(
        conflicted.payload,
        profile_id=PROFILE_ID,
        account_id=ACCOUNT_ID,
        remote_revision=snapshot.base_remote_revision,
        local_sequence=conflicted.local_sequence,
        sync_state=SyncState.PENDING,
        client_save_id=conflicted.client_save_id,
        saved_at=conflicted.saved_at,
    )
    store.save(pending)
    store = LocalProfileStore(store.root)
    fresh_sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_B),
        now_factory=lambda: SAVED_AT,
    )

    result = fresh_sync.sync_pending()

    active = store.load(PROFILE_ID).envelope
    assert result.sync_state is SyncState.CONFLICT
    assert active.sync_state is SyncState.CONFLICT
    assert active.payload == pending.payload
    assert store.load_conflict(PROFILE_ID).snapshot == snapshot


def test_pending_save_does_not_claim_unrelated_conflict_evidence(tmp_path):
    server, store, _, _ = _two_diverged_devices(tmp_path)
    snapshot = store.load_conflict(PROFILE_ID).snapshot
    active = store.load(PROFILE_ID).envelope
    mismatched = build_profile_envelope(
        make_payload(gold=77),
        profile_id=PROFILE_ID,
        account_id=ACCOUNT_ID,
        remote_revision=snapshot.base_remote_revision,
        local_sequence=active.local_sequence + 1,
        sync_state=SyncState.PENDING,
        client_save_id=NEW_SAVE_ID,
        saved_at=SAVED_AT,
    )
    store.save(mismatched)
    store = LocalProfileStore(store.root)
    fresh_sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_B),
        now_factory=lambda: SAVED_AT,
    )

    result = fresh_sync.sync_pending()

    assert result.error == "local_conflict_unreconciled"
    assert result.sync_state is SyncState.PENDING
    assert store.load(PROFILE_ID).envelope == mismatched
    assert store.load_conflict(PROFILE_ID).snapshot == snapshot


def test_resolved_clean_envelope_survives_restart_if_sidecar_clear_failed(tmp_path):
    server, store, sync, _ = _two_diverged_devices(tmp_path)
    snapshot = store.load_conflict(PROFILE_ID).snapshot
    def fail_clear(profile_id):
        raise ProfileStoreError("injected conflict cleanup failure")

    store.clear_conflict = fail_clear
    result = sync.resolve_use_remote()

    assert result.error == "local_store_unavailable"
    store = LocalProfileStore(store.root)
    assert store.load(PROFILE_ID).envelope.sync_state is SyncState.CLEAN
    assert store.load_conflict(PROFILE_ID).snapshot == snapshot

    fresh_sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_B),
        now_factory=lambda: SAVED_AT,
    )
    resumed = fresh_sync.sync_pending()

    assert resumed.sync_state is SyncState.CLEAN
    assert store.load_conflict(PROFILE_ID).status is ConflictStoreStatus.MISSING
    assert store.load_recovery_conflict(
        PROFILE_ID,
        snapshot.local_client_save_id,
        snapshot.remote_current_revision,
    ).snapshot == snapshot


def test_replacement_failure_after_archival_keeps_previous_sidecar(tmp_path, monkeypatch):
    server, store, sync, _ = _two_diverged_devices(tmp_path)
    previous = store.load_conflict(PROFILE_ID).snapshot
    sync._remote.advance_before_next_push = (SAVE_C, make_payload(gold=31))

    def fail_replace(expected, replacement):
        raise ProfileStoreError("injected replacement failure")

    monkeypatch.setattr(store, "replace_conflict", fail_replace, raising=False)
    result = sync.resolve_keep_local()

    assert result.error == "local_store_unavailable"
    store = LocalProfileStore(store.root)
    assert store.load_conflict(PROFILE_ID).snapshot == previous
    assert store.load_recovery_conflict(
        PROFILE_ID,
        previous.local_client_save_id,
        previous.remote_current_revision,
    ).snapshot == previous


def test_restart_reconciles_replacement_written_before_envelope_update(
    tmp_path, monkeypatch
):
    server, store, sync, _ = _two_diverged_devices(tmp_path)
    sync._remote.advance_before_next_push = (SAVE_C, make_payload(gold=31))
    save = store.save

    def fail_conflict_envelope(envelope):
        if (
            envelope.sync_state is SyncState.CONFLICT
            and envelope.remote_revision == 2
        ):
            raise ProfileStoreError("injected envelope update failure")
        save(envelope)

    monkeypatch.setattr(store, "save", fail_conflict_envelope)
    result = sync.resolve_keep_local()

    assert result.error == "local_store_unavailable"
    store = LocalProfileStore(store.root)
    replacement = store.load_conflict(PROFILE_ID).snapshot
    assert replacement.base_remote_revision == 2
    assert replacement.remote_current_revision == 3
    assert store.load(PROFILE_ID).envelope.remote_revision == 1

    fresh_sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_B),
        now_factory=lambda: SAVED_AT,
    )
    resumed = fresh_sync.sync_pending()

    assert resumed.sync_state is SyncState.CONFLICT
    assert store.load(PROFILE_ID).envelope.remote_revision == 2
    assert store.load_conflict(PROFILE_ID).snapshot == replacement


def test_missing_conflict_sidecar_is_rebuilt_only_from_newer_valid_remote_head(
    tmp_path,
):
    server, store, _, _ = _two_diverged_devices(tmp_path)
    conflicted = store.load(PROFILE_ID).envelope
    store.clear_conflict(PROFILE_ID)
    store = LocalProfileStore(store.root)
    fresh_sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_B),
        now_factory=lambda: SAVED_AT,
    )

    result = fresh_sync.sync_pending()

    repaired = store.load_conflict(PROFILE_ID)
    assert result.sync_state is SyncState.CONFLICT
    assert repaired.status is ConflictStoreStatus.VALID
    assert repaired.snapshot.local_payload == conflicted.payload
    assert repaired.snapshot.base_remote_revision == conflicted.remote_revision
    assert repaired.snapshot.remote_current_revision == 2


def test_missing_conflict_sidecar_is_not_rebuilt_from_the_recorded_head(tmp_path):
    server, store, _, _ = _two_diverged_devices(tmp_path)
    head = server.get_profile(ACCOUNT_ID, PROFILE_ID)
    conflicted = store.load(PROFILE_ID).envelope
    at_head = build_profile_envelope(
        conflicted.payload,
        profile_id=PROFILE_ID,
        account_id=ACCOUNT_ID,
        remote_revision=head.current_revision,
        local_sequence=conflicted.local_sequence,
        sync_state=SyncState.CONFLICT,
        client_save_id=conflicted.client_save_id,
        saved_at=conflicted.saved_at,
    )
    store.save(at_head)
    store.clear_conflict(PROFILE_ID)
    store = LocalProfileStore(store.root)
    fresh_sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_B),
        now_factory=lambda: SAVED_AT,
    )

    result = fresh_sync.sync_pending()

    assert result.sync_state is SyncState.CONFLICT
    assert result.error == "local_conflict_unavailable"
    assert store.load(PROFILE_ID).envelope == at_head
    assert store.load_conflict(PROFILE_ID).status is ConflictStoreStatus.MISSING


def test_invalid_conflict_sidecar_is_preserved_and_reported(tmp_path):
    server, store, _, _ = _two_diverged_devices(tmp_path)
    sidecar = store.root / "conflicts" / f"{PROFILE_ID}.json"
    sidecar.write_bytes(b"invalid conflict evidence")
    store = LocalProfileStore(store.root)
    fresh_sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_B),
        now_factory=lambda: SAVED_AT,
    )

    result = fresh_sync.sync_pending()

    assert result.sync_state is SyncState.CONFLICT
    assert result.error == "local_conflict_invalid"
    assert sidecar.read_bytes() == b"invalid conflict evidence"


def test_use_remote_archives_local_branch_and_conflict_before_fast_forward(tmp_path):
    server, store, sync, _ = _two_diverged_devices(tmp_path)
    local_save_id = store.load(PROFILE_ID).envelope.client_save_id
    conflict = store.load_conflict(PROFILE_ID).snapshot
    remote_save_id = server.get_profile(ACCOUNT_ID, PROFILE_ID).client_save_id

    result = sync.resolve_use_remote()

    active = store.load(PROFILE_ID).envelope
    archived_local = store.load_recovery_profile(PROFILE_ID, local_save_id)
    archived_conflict = store.load_recovery_conflict(
        PROFILE_ID, conflict.local_client_save_id, conflict.remote_current_revision
    )
    assert result.sync_state is SyncState.CLEAN
    assert active.remote_revision == 2
    assert active.payload == make_payload(gold=20)
    assert active.client_save_id == remote_save_id
    assert active.local_sequence > archived_local.envelope.local_sequence
    assert archived_local.envelope.payload == make_payload(gold=99)
    assert archived_conflict.snapshot == conflict
    assert store.load_conflict(PROFILE_ID).status is ConflictStoreStatus.MISSING


def test_keep_local_creates_one_new_revision_and_retries_idempotently(tmp_path):
    server, store, sync, _ = _two_diverged_devices(tmp_path)
    original_conflict = store.load_conflict(PROFILE_ID).snapshot
    SaveCoordinator(
        store,
        PROFILE_ID,
        sync_coordinator=sync,
        now_factory=lambda: SAVED_AT,
    ).save(_state(gold=101))
    assert store.load(PROFILE_ID).envelope.sync_state is SyncState.CONFLICT

    result = sync.resolve_keep_local()
    active = store.load(PROFILE_ID).envelope

    assert result.sync_state is SyncState.CLEAN
    assert active.remote_revision == 3
    assert active.payload == make_payload(gold=101)
    assert server.get_profile(ACCOUNT_ID, PROFILE_ID).payload == make_payload(gold=101)
    assert server.revision_count(PROFILE_ID) == 3
    assert store.load_conflict(PROFILE_ID).status is ConflictStoreStatus.MISSING
    assert store.load_recovery_profile(PROFILE_ID, active.client_save_id).envelope.payload == (
        make_payload(gold=101)
    )
    assert store.load_recovery_conflict(
        PROFILE_ID,
        original_conflict.local_client_save_id,
        original_conflict.remote_current_revision,
    ).snapshot == original_conflict
    assert original_conflict.local_payload == make_payload(gold=99)
    sync.sync_pending()
    assert server.revision_count(PROFILE_ID) == 3


def test_keep_local_replay_fast_forwards_after_another_device_advances(tmp_path):
    server, store, sync, _ = _two_diverged_devices(tmp_path)
    original_conflict = store.load_conflict(PROFILE_ID).snapshot
    server.drop_next_push_after_commit = True

    first_result = sync.resolve_keep_local()

    assert first_result.sync_state is SyncState.CONFLICT
    assert server.revision_count(PROFILE_ID) == 3
    server.advance(
        ACCOUNT_ID, DEVICE_A, PROFILE_ID, 3, SAVE_D, make_payload(gold=31)
    )

    result = sync.resolve_keep_local()

    active = store.load(PROFILE_ID).envelope
    assert result.sync_state is SyncState.CLEAN
    assert result.error is None
    assert active.remote_revision == 4
    assert active.payload == make_payload(gold=31)
    assert active.client_save_id == SAVE_D
    assert store.load_conflict(PROFILE_ID).status is ConflictStoreStatus.MISSING
    assert store.load_recovery_conflict(
        PROFILE_ID,
        original_conflict.local_client_save_id,
        original_conflict.remote_current_revision,
    ).snapshot == original_conflict
    assert server.revision_count(PROFILE_ID) == 4


def test_keep_local_adopts_save_id_of_matching_remote_head(tmp_path):
    server, store, sync, _ = _two_diverged_devices(tmp_path)
    server.advance(
        ACCOUNT_ID, DEVICE_A, PROFILE_ID, 2, SAVE_D, make_payload(gold=99)
    )

    result = sync.resolve_keep_local()

    active = store.load(PROFILE_ID).envelope
    assert result.sync_state is SyncState.CLEAN
    assert active.remote_revision == 3
    assert active.payload == make_payload(gold=99)
    assert active.client_save_id == SAVE_D
    assert store.load_conflict(PROFILE_ID).status is ConflictStoreStatus.MISSING


def test_keep_local_that_races_another_device_records_a_new_conflict(tmp_path):
    server, store, sync, _ = _two_diverged_devices(tmp_path)
    remote_client = sync._remote
    old_conflict = store.load_conflict(PROFILE_ID).snapshot
    remote_client.advance_before_next_push = (SAVE_C, make_payload(gold=31))

    result = sync.resolve_keep_local()

    current = store.load(PROFILE_ID).envelope
    updated_conflict = store.load_conflict(PROFILE_ID).snapshot
    old_archive = store.load_recovery_conflict(
        PROFILE_ID,
        old_conflict.local_client_save_id,
        old_conflict.remote_current_revision,
    )
    assert result.sync_state is SyncState.CONFLICT
    assert current.sync_state is SyncState.CONFLICT
    assert current.remote_revision == 2
    assert updated_conflict.base_remote_revision == 2
    assert updated_conflict.remote_current_revision == 3
    assert updated_conflict.local_payload == make_payload(gold=99)
    assert updated_conflict.remote_payload == make_payload(gold=31)
    assert old_archive.snapshot == old_conflict
    assert server.revision_count(PROFILE_ID) == 3

    remote_client.advance_before_next_push = (SAVE_D, make_payload(gold=40))
    second_result = sync.resolve_keep_local()

    second_conflict = store.load_conflict(PROFILE_ID).snapshot
    current = store.load(PROFILE_ID).envelope
    prior_archive = store.load_recovery_conflict(
        PROFILE_ID,
        updated_conflict.local_client_save_id,
        updated_conflict.remote_current_revision,
    )
    assert second_result.sync_state is SyncState.CONFLICT
    assert current.remote_revision == 3
    assert current.client_save_id == updated_conflict.local_client_save_id
    assert current.payload == make_payload(gold=99)
    assert second_conflict.base_remote_revision == 3
    assert second_conflict.remote_current_revision == 4
    assert second_conflict.remote_payload == make_payload(gold=40)
    assert prior_archive.snapshot == updated_conflict
    assert server.revision_count(PROFILE_ID) == 4


def test_fork_local_creates_a_new_cloud_profile_without_changing_conflicted_source(
    tmp_path,
):
    server, store, sync, _ = _two_diverged_devices(tmp_path)
    old_conflict = store.load_conflict(PROFILE_ID).snapshot

    result = sync.fork_local(NEW_PROFILE_ID, NEW_SAVE_ID)

    source = store.load(PROFILE_ID).envelope
    fork = store.load(NEW_PROFILE_ID).envelope
    assert result.sync_state is SyncState.CLEAN
    assert source.sync_state is SyncState.CONFLICT
    assert source.payload == make_payload(gold=99)
    assert store.load_conflict(PROFILE_ID).snapshot == old_conflict
    assert fork.profile_id == NEW_PROFILE_ID
    assert fork.account_id == ACCOUNT_ID
    assert fork.remote_revision == 1
    assert fork.client_save_id == NEW_SAVE_ID
    assert fork.payload == make_payload(gold=99)
    assert server.revision_count(NEW_PROFILE_ID) == 1


def test_fork_uuid_collision_does_not_adopt_matching_remote_profile(tmp_path):
    server, store, sync, _ = _two_diverged_devices(tmp_path)
    source = store.load(PROFILE_ID).envelope
    remote_payload = make_payload(gold=99)
    server.create_profile(
        ACCOUNT_ID, DEVICE_A, NEW_PROFILE_ID, SAVE_A, remote_payload
    )

    result = sync.fork_local(NEW_PROFILE_ID, NEW_SAVE_ID)

    pending_fork = store.load(NEW_PROFILE_ID).envelope
    source_after = store.load(PROFILE_ID).envelope
    remote_fork = server.get_profile(ACCOUNT_ID, NEW_PROFILE_ID)
    assert result.sync_state is SyncState.PENDING
    assert result.error == "fork_profile_collision"
    assert pending_fork.sync_state is SyncState.PENDING
    assert pending_fork.remote_revision is None
    assert pending_fork.payload == source.payload
    assert pending_fork.client_save_id == NEW_SAVE_ID
    assert source_after == source
    assert remote_fork.client_save_id == SAVE_A
    assert remote_fork.payload == remote_payload
    assert server.revision_count(NEW_PROFILE_ID) == 1


def test_fork_retry_reuses_its_locally_persisted_save_id_after_lost_response(tmp_path):
    server, store, sync, _ = _two_diverged_devices(tmp_path)
    server.drop_next_create_after_commit = True

    first = sync.fork_local(NEW_PROFILE_ID)
    pending_fork = store.load(NEW_PROFILE_ID).envelope

    assert first.sync_state is SyncState.PENDING
    assert pending_fork.sync_state is SyncState.PENDING
    assert pending_fork.account_id == ACCOUNT_ID
    assert pending_fork.remote_revision is None
    assert pending_fork.payload == make_payload(gold=99)
    assert server.revision_count(NEW_PROFILE_ID) == 1

    retry = sync.fork_local(NEW_PROFILE_ID)
    claimed_fork = store.load(NEW_PROFILE_ID).envelope
    assert retry.sync_state is SyncState.CLEAN
    assert claimed_fork.client_save_id == pending_fork.client_save_id
    assert claimed_fork.remote_revision == 1
    assert claimed_fork.sync_state is SyncState.CLEAN
    assert server.revision_count(NEW_PROFILE_ID) == 1

from datetime import datetime, timezone
from uuid import UUID

from app.persistence.coordinator import SaveCoordinator
from app.persistence.envelope import SyncState
from app.persistence.local_store import LocalProfileStore
from app.persistence.ports import ConflictStoreStatus, SaveLoadStatus
from app.persistence.sync import ProfileSyncCoordinator
from tests.remote_sync_test_support import (
    ACCOUNT_ID,
    DEVICE_A,
    DEVICE_B,
    PROFILE_ID,
    BoundMemoryRemoteClient,
    MemoryRemoteProfileServer,
    SAVE_C,
    make_payload,
)


SAVED_AT = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
NEW_PROFILE_ID = UUID("00000000-0000-4000-8000-000000000007")
NEW_SAVE_ID = UUID("00000000-0000-4000-8000-000000000008")


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


def test_use_remote_archives_local_branch_and_conflict_before_fast_forward(tmp_path):
    _, store, sync, _ = _two_diverged_devices(tmp_path)
    local_save_id = store.load(PROFILE_ID).envelope.client_save_id
    conflict = store.load_conflict(PROFILE_ID).snapshot

    result = sync.resolve_use_remote()

    active = store.load(PROFILE_ID).envelope
    archived_local = store.load_recovery_profile(PROFILE_ID, local_save_id)
    archived_conflict = store.load_recovery_conflict(
        PROFILE_ID, conflict.local_client_save_id, conflict.remote_current_revision
    )
    assert result.sync_state is SyncState.CLEAN
    assert active.remote_revision == 2
    assert active.payload == make_payload(gold=20)
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

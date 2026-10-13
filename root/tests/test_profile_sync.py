from datetime import datetime, timezone

from app.persistence.coordinator import SaveCoordinator
from app.persistence.envelope import SyncState
from app.persistence.local_store import LocalProfileStore
from app.persistence.ports import SaveLoadStatus
from app.persistence.sync import ProfileSyncCoordinator
from tests.remote_sync_test_support import (
    ACCOUNT_ID,
    DEVICE_A,
    PROFILE_ID,
    SAVE_B,
    BoundMemoryRemoteClient,
    MemoryRemoteProfileServer,
    make_payload,
)


SAVED_AT = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)


def _state(gold=0):
    from app.content.catalog import get_drifter_spec_by_choice
    from app.game.game_state import GameState
    from app.player.player_state import PlayerState

    character = get_drifter_spec_by_choice("1").create_character()
    return GameState(PlayerState(character, gold=gold))


def _save_local(store, gold=0):
    return SaveCoordinator(
        store,
        PROFILE_ID,
        now_factory=lambda: SAVED_AT,
    ).save(_state(gold))


def test_local_only_sync_never_contacts_the_remote_service(tmp_path):
    store = LocalProfileStore(tmp_path / "profiles")
    _save_local(store)
    server = MemoryRemoteProfileServer()
    sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_A),
        now_factory=lambda: SAVED_AT,
    )

    result = sync.sync_pending()

    assert result.sync_state is SyncState.LOCAL_ONLY
    assert server.profiles == {}


def test_offline_guest_claim_retries_without_changing_profile_identity(tmp_path):
    store = LocalProfileStore(tmp_path / "profiles")
    _save_local(store, gold=17)
    original = store.load(PROFILE_ID).envelope
    server = MemoryRemoteProfileServer()
    server.available = False
    sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_A),
        now_factory=lambda: SAVED_AT,
    )

    offline = sync.enable_cloud(ACCOUNT_ID)
    pending = store.load(PROFILE_ID).envelope
    assert offline.sync_state is SyncState.PENDING
    assert pending.profile_id == original.profile_id
    assert pending.client_save_id == original.client_save_id
    assert pending.account_id == ACCOUNT_ID
    assert pending.remote_revision is None
    assert SaveCoordinator(store, PROFILE_ID).load().status is SaveLoadStatus.LOADED

    server.available = True
    synced = sync.sync_pending()
    claimed = store.load(PROFILE_ID).envelope

    assert synced.sync_state is SyncState.CLEAN
    assert claimed.profile_id == original.profile_id
    assert claimed.payload == original.payload
    assert claimed.remote_revision == 1
    assert claimed.sync_state is SyncState.CLEAN
    assert server.revision_count(PROFILE_ID) == 1
    sync.sync_pending()
    assert server.revision_count(PROFILE_ID) == 1


def test_game_save_commits_locally_before_offline_sync_and_retries_latest_state(tmp_path):
    store = LocalProfileStore(tmp_path / "profiles")
    _save_local(store, gold=1)
    server = MemoryRemoteProfileServer()
    sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_A),
        now_factory=lambda: SAVED_AT,
    )
    sync.enable_cloud(ACCOUNT_ID)
    server.available = False
    coordinator = SaveCoordinator(
        store,
        PROFILE_ID,
        sync_coordinator=sync,
        now_factory=lambda: SAVED_AT,
    )

    saved = coordinator.save(_state(gold=22))
    offline_envelope = store.load(PROFILE_ID).envelope

    assert saved.status is SaveLoadStatus.SAVED
    assert offline_envelope.payload == make_payload(gold=22)
    assert offline_envelope.sync_state is SyncState.PENDING
    assert offline_envelope.remote_revision == 1

    server.available = True
    result = sync.sync_pending()
    uploaded = store.load(PROFILE_ID).envelope

    assert result.sync_state is SyncState.CLEAN
    assert uploaded.payload == make_payload(gold=22)
    assert uploaded.remote_revision == 2
    assert server.revision_count(PROFILE_ID) == 2


def test_ambiguous_claim_and_upload_retries_do_not_create_duplicate_revisions(
    tmp_path,
):
    store = LocalProfileStore(tmp_path / "profiles")
    _save_local(store, gold=3)
    server = MemoryRemoteProfileServer()
    server.drop_next_create_after_commit = True
    sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_A),
        now_factory=lambda: SAVED_AT,
    )

    first_claim = sync.enable_cloud(ACCOUNT_ID)
    assert first_claim.sync_state is SyncState.PENDING
    assert first_claim.error == "offline"
    assert server.revision_count(PROFILE_ID) == 1

    assert sync.sync_pending().sync_state is SyncState.CLEAN
    assert server.revision_count(PROFILE_ID) == 1

    server.drop_next_push_after_commit = True
    SaveCoordinator(
        store,
        PROFILE_ID,
        sync_coordinator=sync,
        now_factory=lambda: SAVED_AT,
    ).save(_state(gold=14))
    pending = store.load(PROFILE_ID).envelope
    assert pending.sync_state is SyncState.PENDING
    assert pending.remote_revision == 1
    assert server.revision_count(PROFILE_ID) == 2

    assert sync.sync_pending().sync_state is SyncState.CLEAN
    assert store.load(PROFILE_ID).envelope.remote_revision == 2
    assert server.revision_count(PROFILE_ID) == 2


def test_clean_profile_fast_forwards_only_to_a_valid_newer_remote_head(tmp_path):
    store = LocalProfileStore(tmp_path / "profiles")
    _save_local(store, gold=1)
    server = MemoryRemoteProfileServer()
    client = BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_A)
    sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        client,
        now_factory=lambda: SAVED_AT,
    )
    sync.enable_cloud(ACCOUNT_ID)
    previous = store.load(PROFILE_ID).envelope
    server.advance(
        ACCOUNT_ID,
        DEVICE_A,
        PROFILE_ID,
        1,
        SAVE_B,
        make_payload(gold=8),
    )

    result = sync.refresh()
    advanced = store.load(PROFILE_ID).envelope

    assert result.sync_state is SyncState.CLEAN
    assert advanced.payload == make_payload(gold=8)
    assert advanced.remote_revision == 2
    assert advanced.local_sequence == previous.local_sequence + 1
    assert advanced.client_save_id != previous.client_save_id

    server.available = False
    offline = sync.refresh()
    assert offline.sync_state is SyncState.CLEAN
    assert offline.error == "offline"
    assert store.load(PROFILE_ID).envelope == advanced


def test_pending_local_saves_replace_the_upload_candidate_with_latest_state(tmp_path):
    store = LocalProfileStore(tmp_path / "profiles")
    _save_local(store, gold=1)
    server = MemoryRemoteProfileServer()
    sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_A),
        now_factory=lambda: SAVED_AT,
    )
    sync.enable_cloud(ACCOUNT_ID)
    server.available = False
    coordinator = SaveCoordinator(
        store,
        PROFILE_ID,
        sync_coordinator=sync,
        now_factory=lambda: SAVED_AT,
    )
    coordinator.save(_state(gold=5))
    first_pending = store.load(PROFILE_ID).envelope
    coordinator.save(_state(gold=6))
    latest_pending = store.load(PROFILE_ID).envelope

    assert latest_pending.local_sequence == first_pending.local_sequence + 1
    assert latest_pending.client_save_id != first_pending.client_save_id
    assert latest_pending.payload == make_payload(gold=6)
    assert latest_pending.remote_revision == 1

    server.available = True
    result = sync.sync_pending()
    assert result.sync_state is SyncState.CLEAN
    assert server.revision_count(PROFILE_ID) == 2
    assert server.get_profile(ACCOUNT_ID, PROFILE_ID).payload == make_payload(gold=6)

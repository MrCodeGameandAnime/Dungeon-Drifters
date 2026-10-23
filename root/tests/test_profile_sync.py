from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.persistence.coordinator import SaveCoordinator
from app.persistence.envelope import SyncState, build_profile_envelope
from app.persistence.local_store import LocalProfileStore
from app.persistence.ports import ProfileStoreError, SaveLoadStatus
from app.persistence.remote_client import RemoteRequestRejected
from app.persistence.sync import ProfileSyncCoordinator, SyncResult
from tests.remote_sync_test_support import (
    ACCOUNT_ID,
    DEVICE_A,
    DEVICE_B,
    PROFILE_ID,
    SAVE_A,
    SAVE_B,
    SAVE_C,
    BoundMemoryRemoteClient,
    MemoryRemoteProfileServer,
    make_legacy_schema8_payload,
    make_payload,
)


SAVED_AT = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
NEW_PROFILE_ID = UUID("00000000-0000-4000-8000-000000000007")


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


def _legacy_schema9_payload(gold=0):
    payload = make_payload(gold)
    payload["schema_version"] = 9
    payload["overworld"].pop("active_route_id")
    for field in (
        "floor_one_cleared",
        "floor_one_runs_started_after_clear",
        "outing_xp_multiplier_percent",
    ):
        payload["party"].pop(field)
    return payload


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


def test_schema8_remote_head_advances_to_schema10_without_rewriting_history(tmp_path):
    store = LocalProfileStore(tmp_path / "profiles")
    server = MemoryRemoteProfileServer()
    old_payload = make_legacy_schema8_payload(gold=14)
    server.create_profile(
        ACCOUNT_ID,
        DEVICE_A,
        PROFILE_ID,
        SAVE_A,
        old_payload,
    )
    old_envelope = build_profile_envelope(
        old_payload,
        profile_id=PROFILE_ID,
        account_id=ACCOUNT_ID,
        remote_revision=1,
        local_sequence=1,
        sync_state=SyncState.CLEAN,
        client_save_id=SAVE_A,
        saved_at=SAVED_AT,
    )
    store.save(old_envelope)
    coordinator = SaveCoordinator(
        store,
        PROFILE_ID,
        client_save_id_factory=lambda: SAVE_B,
        now_factory=lambda: SAVED_AT,
    )
    sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_A),
        now_factory=lambda: SAVED_AT,
    )

    loaded = coordinator.load()
    local_pending = store.load(PROFILE_ID).envelope
    result = sync.sync_pending()

    assert loaded.status is SaveLoadStatus.LOADED
    assert local_pending.payload["schema_version"] == 10
    assert local_pending.sync_state is SyncState.PENDING
    assert result.sync_state is SyncState.CLEAN
    assert server.revision_count(PROFILE_ID) == 2
    assert server.profiles[PROFILE_ID]["revisions"][0].payload == old_payload
    assert server.profiles[PROFILE_ID]["head"].payload["schema_version"] == 10


def test_schema9_cloud_head_advances_to_schema10_without_rewriting_history(
    tmp_path,
):
    store = LocalProfileStore(tmp_path / "profiles")
    server = MemoryRemoteProfileServer()
    old_payload = _legacy_schema9_payload(gold=14)
    server.create_profile(
        ACCOUNT_ID,
        DEVICE_A,
        PROFILE_ID,
        SAVE_A,
        old_payload,
    )
    old_envelope = build_profile_envelope(
        old_payload,
        profile_id=PROFILE_ID,
        account_id=ACCOUNT_ID,
        remote_revision=1,
        local_sequence=1,
        sync_state=SyncState.CLEAN,
        client_save_id=SAVE_A,
        saved_at=SAVED_AT,
    )
    store.save(old_envelope)
    coordinator = SaveCoordinator(
        store,
        PROFILE_ID,
        client_save_id_factory=lambda: SAVE_B,
        now_factory=lambda: SAVED_AT,
    )
    sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_A),
        now_factory=lambda: SAVED_AT,
    )

    loaded = coordinator.load()
    local_pending = store.load(PROFILE_ID).envelope
    result = sync.sync_pending()

    assert loaded.status is SaveLoadStatus.LOADED
    assert local_pending.payload["schema_version"] == 10
    assert local_pending.sync_state is SyncState.PENDING
    assert result.sync_state is SyncState.CLEAN
    assert server.revision_count(PROFILE_ID) == 2
    assert server.profiles[PROFILE_ID]["revisions"][0].payload == old_payload
    assert server.profiles[PROFILE_ID]["head"].payload["schema_version"] == 10


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


@pytest.mark.parametrize("failure_type", (ProfileStoreError, OSError))
def test_save_remains_successful_when_sync_store_fails_after_local_commit(
    tmp_path, failure_type
):
    class FailOnLoadStore:
        def __init__(self, store):
            self.store = store
            self.fail_on_load = None
            self.load_calls = 0

        def __getattr__(self, name):
            return getattr(self.store, name)

        def load(self, profile_id):
            self.load_calls += 1
            if self.load_calls == self.fail_on_load:
                self.fail_on_load = None
                raise failure_type("injected sync read failure")
            return self.store.load(profile_id)

    store = FailOnLoadStore(LocalProfileStore(tmp_path / "profiles"))
    _save_local(store, gold=1)
    server = MemoryRemoteProfileServer()
    sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_A),
        now_factory=lambda: SAVED_AT,
    )
    assert sync.enable_cloud(ACCOUNT_ID).sync_state is SyncState.CLEAN
    store.load_calls = 0
    store.fail_on_load = 3
    coordinator = SaveCoordinator(
        store,
        PROFILE_ID,
        sync_coordinator=sync,
        now_factory=lambda: SAVED_AT,
    )

    saved = coordinator.save(_state(gold=22))

    assert saved.status is SaveLoadStatus.SAVED
    loaded = coordinator.load()
    assert loaded.status is SaveLoadStatus.LOADED
    assert loaded.game_state.player_state.gold == 22
    pending = store.load(PROFILE_ID).envelope
    assert pending.payload == make_payload(gold=22)
    assert pending.sync_state is SyncState.PENDING

    recovered = sync.sync_pending()

    assert recovered.sync_state is SyncState.CLEAN
    assert store.load(PROFILE_ID).envelope.payload == make_payload(gold=22)


@pytest.mark.parametrize(
    ("operation", "store_method"),
    (
        ("enable_cloud", "load"),
        ("enable_cloud", "save"),
        ("download_remote", "load"),
        ("download_remote", "save"),
        ("refresh", "load"),
        ("refresh", "save"),
        ("fork_local", "load"),
        ("fork_local", "save"),
    ),
)
@pytest.mark.parametrize("failure_type", (ProfileStoreError, OSError))
def test_public_sync_entrypoints_normalize_expected_store_failures(
    tmp_path, monkeypatch, operation, store_method, failure_type
):
    store = LocalProfileStore(tmp_path / "profiles")
    server = MemoryRemoteProfileServer()
    sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_A),
        now_factory=lambda: SAVED_AT,
    )

    if operation in {"enable_cloud", "refresh", "fork_local"}:
        _save_local(store)
    if operation == "refresh":
        assert sync.enable_cloud(ACCOUNT_ID).sync_state is SyncState.CLEAN
        server.advance(
            ACCOUNT_ID, DEVICE_B, PROFILE_ID, 1, SAVE_B, make_payload(gold=7)
        )
    elif operation == "fork_local":
        server.available = False
        assert sync.enable_cloud(ACCOUNT_ID).sync_state is SyncState.PENDING
    elif operation == "download_remote" and store_method == "save":
        server.create_profile(
            ACCOUNT_ID, DEVICE_A, PROFILE_ID, SAVE_A, make_payload(gold=5)
        )

    def fail_store_operation(*_args, **_kwargs):
        raise failure_type("injected profile-store failure")

    monkeypatch.setattr(store, store_method, fail_store_operation)
    if operation == "enable_cloud":
        result = sync.enable_cloud(ACCOUNT_ID)
    elif operation == "download_remote":
        result = sync.download_remote()
    elif operation == "refresh":
        result = sync.refresh()
    else:
        result = sync.fork_local(NEW_PROFILE_ID, SAVE_C)

    assert isinstance(result, SyncResult)
    assert result.error == "local_store_unavailable"


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


def test_lost_claim_response_replay_fast_forwards_to_remote_descendant(tmp_path):
    store = LocalProfileStore(tmp_path / "profiles")
    _save_local(store, gold=3)
    server = MemoryRemoteProfileServer()
    server.drop_next_create_after_commit = True
    client = BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_A)
    sync = ProfileSyncCoordinator(store, PROFILE_ID, client, now_factory=lambda: SAVED_AT)

    assert sync.enable_cloud(ACCOUNT_ID).sync_state is SyncState.PENDING
    server.advance(
        ACCOUNT_ID, DEVICE_B, PROFILE_ID, 1, SAVE_B, make_payload(gold=8)
    )

    result = sync.sync_pending()
    installed = store.load(PROFILE_ID).envelope

    assert result.sync_state is SyncState.CLEAN
    assert result.error is None
    assert installed.remote_revision == 2
    assert installed.payload == make_payload(gold=8)
    assert installed.client_save_id == SAVE_B
    assert store.load_conflict(PROFILE_ID).status.value == "missing"
    assert server.revision_count(PROFILE_ID) == 2


def test_lost_progression_response_replay_fast_forwards_to_remote_descendant(
    tmp_path,
):
    store = LocalProfileStore(tmp_path / "profiles")
    _save_local(store, gold=3)
    server = MemoryRemoteProfileServer()
    sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_A),
        now_factory=lambda: SAVED_AT,
    )
    assert sync.enable_cloud(ACCOUNT_ID).sync_state is SyncState.CLEAN
    server.drop_next_push_after_commit = True
    assert SaveCoordinator(
        store,
        PROFILE_ID,
        sync_coordinator=sync,
        now_factory=lambda: SAVED_AT,
    ).save(_state(gold=14)).status is SaveLoadStatus.SAVED
    pending = store.load(PROFILE_ID).envelope
    assert pending.sync_state is SyncState.PENDING
    assert pending.remote_revision == 1

    server.advance(
        ACCOUNT_ID, DEVICE_B, PROFILE_ID, 2, SAVE_C, make_payload(gold=25)
    )
    result = sync.sync_pending()
    installed = store.load(PROFILE_ID).envelope

    assert result.sync_state is SyncState.CLEAN
    assert result.error is None
    assert installed.remote_revision == 3
    assert installed.payload == make_payload(gold=25)
    assert installed.client_save_id == SAVE_C
    assert store.load_conflict(PROFILE_ID).status.value == "missing"
    assert server.revision_count(PROFILE_ID) == 3


def test_real_claim_collision_is_not_resolved_by_matching_payload_or_blocks_fork(
    tmp_path,
):
    store = LocalProfileStore(tmp_path / "profiles")
    payload = make_payload(gold=12)
    _save_local(store, gold=12)
    server = MemoryRemoteProfileServer()
    server.create_profile(
        ACCOUNT_ID, DEVICE_B, PROFILE_ID, SAVE_A, make_payload(gold=9)
    )
    sync = ProfileSyncCoordinator(
        store,
        PROFILE_ID,
        BoundMemoryRemoteClient(server, ACCOUNT_ID, DEVICE_A),
        now_factory=lambda: SAVED_AT,
    )

    first_collision = sync.enable_cloud(ACCOUNT_ID)
    assert first_collision.sync_state is SyncState.PENDING
    server.advance(ACCOUNT_ID, DEVICE_B, PROFILE_ID, 1, SAVE_B, payload)
    collision = sync.sync_pending()
    source = store.load(PROFILE_ID).envelope
    forked = sync.fork_local(NEW_PROFILE_ID, SAVE_C)
    source_after_fork = store.load(PROFILE_ID).envelope
    fork = store.load(NEW_PROFILE_ID).envelope
    remote_source = server.get_profile(ACCOUNT_ID, PROFILE_ID)

    assert collision.sync_state is SyncState.PENDING
    assert collision.error == "profile_claim_conflict"
    assert source.sync_state is SyncState.PENDING
    assert source.remote_revision is None
    assert source.payload == payload
    assert forked.sync_state is SyncState.CLEAN
    assert source_after_fork == source
    assert fork.sync_state is SyncState.CLEAN
    assert fork.payload == payload
    assert fork.client_save_id == SAVE_C
    assert fork.remote_revision == 1
    assert remote_source.client_save_id == SAVE_B
    assert remote_source.payload == payload
    assert remote_source.current_revision == 2


def test_memory_server_rejects_reused_save_id_with_different_payload(tmp_path):
    server = MemoryRemoteProfileServer()
    server.create_profile(ACCOUNT_ID, DEVICE_A, PROFILE_ID, SAVE_A, make_payload())
    server.advance(
        ACCOUNT_ID, DEVICE_A, PROFILE_ID, 1, SAVE_B, make_payload(gold=1)
    )

    with pytest.raises(RemoteRequestRejected) as error:
        server.push_progression(
            ACCOUNT_ID,
            DEVICE_B,
            PROFILE_ID,
            2,
            SAVE_B,
            make_payload(gold=2),
        )

    assert error.value.code == "idempotency_key_reuse"
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
    assert advanced.client_save_id == SAVE_B

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

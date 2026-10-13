import os
from uuid import UUID
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.content.catalog import get_drifter_spec_by_choice
from app.game.game_state import GameState
from app.persistence.coordinator import SaveCoordinator
from app.persistence.envelope import SyncState
from app.persistence.local_store import LocalProfileStore
from app.persistence.remote_client import JsonApiRemoteProfileClient
from app.persistence.sync import ProfileSyncCoordinator
from app.player.player_state import PlayerState
from profile_api.app import create_app
from profile_api.config import Settings
from profile_api.database import Base

from conftest import create_account


DEVICE_A = UUID("00000000-0000-4000-8000-000000000022")
DEVICE_B = UUID("00000000-0000-4000-8000-000000000023")
POSTGRES_URL = os.environ.get("PROFILE_API_TEST_DATABASE_URL")


class ApiTestTransport:
    def __init__(self, client):
        self.client = client

    def request(self, method, path, *, headers, json):
        return self.client.request(method, path, headers=headers, json=json)


def _game_state(gold=0):
    character = get_drifter_spec_by_choice("1").create_character()
    return GameState(PlayerState(character, gold=gold))


def _run_sync_scenarios(api, tmp_path):
    account = create_account(api)
    account_id = UUID(account["account_id"])
    profile_id = uuid4()
    transport = ApiTestTransport(api)
    client_a = JsonApiRemoteProfileClient(
        transport,
        access_token=account["access_token"],
        device_id=DEVICE_A,
    )
    client_b = JsonApiRemoteProfileClient(
        transport,
        access_token=account["access_token"],
        device_id=DEVICE_B,
    )
    store_a = LocalProfileStore(tmp_path / "device-a")
    store_b = LocalProfileStore(tmp_path / "device-b")
    SaveCoordinator(store_a, profile_id).save(_game_state())
    sync_a = ProfileSyncCoordinator(store_a, profile_id, client_a)
    assert sync_a.enable_cloud(account_id).sync_state is SyncState.CLEAN

    listed = client_b.list_profiles()
    assert len(listed) == 1
    assert listed[0].profile_id == profile_id
    assert listed[0].current_revision == 1

    sync_b = ProfileSyncCoordinator(store_b, profile_id, client_b)
    assert sync_b.download_remote().sync_state is SyncState.CLEAN
    assert SaveCoordinator(store_b, profile_id).load().game_state.player_state.gold == 0

    SaveCoordinator(
        store_a, profile_id, sync_coordinator=sync_a
    ).save(_game_state(gold=20))
    SaveCoordinator(store_b, profile_id).save(_game_state(gold=99))
    assert sync_b.sync_pending().sync_state is SyncState.CONFLICT
    assert sync_b.resolve_keep_local().sync_state is SyncState.CLEAN
    assert client_a.get_profile(profile_id).current_revision == 3
    assert client_a.get_profile(profile_id).payload["player"]["gold"] == 99

    assert sync_a.refresh().sync_state is SyncState.CLEAN
    SaveCoordinator(
        store_a, profile_id, sync_coordinator=sync_a
    ).save(_game_state(gold=30))
    SaveCoordinator(store_b, profile_id).save(_game_state(gold=55))
    assert sync_b.sync_pending().sync_state is SyncState.CONFLICT
    assert sync_b.resolve_use_remote().sync_state is SyncState.CLEAN

    active = store_b.load(profile_id).envelope
    remote = client_a.get_profile(profile_id)
    assert active.remote_revision == 4
    assert active.payload["player"]["gold"] == 30
    assert remote.current_revision == 4
    assert remote.payload["player"]["gold"] == 30
    assert store_b.load_conflict(profile_id).snapshot is None


def test_two_device_sync_and_both_resolutions_use_real_profile_api(service, tmp_path):
    api, _ = service
    _run_sync_scenarios(api, tmp_path)


@pytest.mark.skipif(
    not POSTGRES_URL
    or not POSTGRES_URL.startswith(("postgresql://", "postgresql+psycopg://")),
    reason="requires a dedicated PostgreSQL PROFILE_API_TEST_DATABASE_URL",
)
def test_two_device_sync_and_both_resolutions_use_postgresql(tmp_path):
    engine = create_engine(POSTGRES_URL, pool_size=8, max_overflow=2)
    try:
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(engine, expire_on_commit=False)
        app = create_app(session_factory=session_factory, settings=Settings())
        with TestClient(app) as api:
            _run_sync_scenarios(api, tmp_path)
    finally:
        engine.dispose()

import os
from copy import deepcopy
from datetime import datetime, timezone
from uuid import UUID
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.content.catalog import get_drifter_spec_by_choice
from app.game.game_state import GameState
from app.persistence.coordinator import SaveCoordinator
from app.persistence.envelope import SyncState, payload_sha256
from app.persistence.local_store import LocalProfileStore
from app.persistence.remote_client import JsonApiRemoteProfileClient
from app.persistence.save_document import build_save_document
from app.persistence.sync import ProfileSyncCoordinator
from app.player.player_state import PlayerState
from profile_api.app import create_app
from profile_api.config import Settings
from profile_api.database import Base
from profile_api.models import Profile, ProfileRevision

from conftest import authorization, create_account


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


def _run_schema11_history_advancement(api, session_factory):
    account = create_account(api)
    account_id = UUID(account["account_id"])
    profile_id = uuid4()
    historical_save_id = uuid4()
    device_id = UUID("00000000-0000-4000-8000-000000000024")
    current_payload = build_save_document(_game_state())
    historical_payload = deepcopy(current_payload)
    historical_payload["schema_version"] = 11
    historical_players = [historical_payload["player"]]
    historical_players.extend(historical_payload["party"]["companions"])
    for player in historical_players:
        player["signature_weapon"].pop("tier_v_success")
    historical_digest = payload_sha256(historical_payload)

    with session_factory() as session:
        session.add(
            Profile(
                id=profile_id,
                account_id=account_id,
                current_revision=1,
                status="active",
            )
        )
        session.add(
            ProfileRevision(
                profile_id=profile_id,
                revision=1,
                base_revision=None,
                client_save_id=historical_save_id,
                device_id=device_id,
                payload=historical_payload,
                payload_sha256=historical_digest,
                created_at=datetime.now(timezone.utc),
            )
        )
        session.commit()

    head = api.get(
        f"/v1/profiles/{profile_id}",
        headers=authorization(account["access_token"]),
    )
    migrated_payload = deepcopy(current_payload)
    migrated_payload["metadata"]["schema_migration"] = "11"
    advanced = api.put(
        f"/v1/profiles/{profile_id}/progression",
        headers=authorization(account["access_token"]),
        json={
            "base_revision": 1,
            "client_save_id": str(uuid4()),
            "device_id": str(device_id),
            "payload": migrated_payload,
        },
    )

    assert head.status_code == 200, head.text
    assert head.json()["head"]["payload"] == historical_payload
    assert head.json()["head"]["payload_sha256"] == historical_digest
    assert advanced.status_code == 200, advanced.text
    assert advanced.json()["accepted_revision"] == 2
    assert advanced.json()["head"]["payload"]["schema_version"] == 12
    with session_factory() as session:
        historical = session.get(ProfileRevision, (profile_id, 1))
        assert historical.payload == historical_payload
        assert historical.payload_sha256 == historical_digest


def test_schema11_remote_history_advances_to_schema12_without_mutation(service):
    api, session_factory = service
    _run_schema11_history_advancement(api, session_factory)


@pytest.mark.skipif(
    not POSTGRES_URL
    or not POSTGRES_URL.startswith(("postgresql://", "postgresql+psycopg://")),
    reason="requires a dedicated PostgreSQL PROFILE_API_TEST_DATABASE_URL",
)
def test_schema11_remote_history_advances_to_schema12_on_postgresql():
    engine = create_engine(POSTGRES_URL, pool_size=8, max_overflow=2)
    try:
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(engine, expire_on_commit=False)
        app = create_app(session_factory=session_factory, settings=Settings())
        with TestClient(app) as api:
            _run_schema11_history_advancement(api, session_factory)
    finally:
        engine.dispose()


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

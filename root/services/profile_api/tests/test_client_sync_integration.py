import os
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from uuid import UUID
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.content.catalog import (
    get_drifter_spec,
    get_drifter_spec_by_choice,
    get_route_spec,
)
from app.content.route_spec import RouteNodeKind
from app.game.expeditions import ExpeditionService
from app.game.game_state import GameState
from app.persistence.coordinator import SaveCoordinator
from app.persistence.envelope import SyncState, payload_sha256
from app.persistence.local_store import LocalProfileStore
from app.persistence.remote_client import JsonApiRemoteProfileClient
from app.persistence.save_document import build_save_document
from app.persistence.ports import SaveLoadResult
from app.persistence.save_port_contract import SaveLoadStatus
from app.persistence.sync import ProfileSyncCoordinator
from app.player.player_state import PlayerState
from profile_api.app import create_app
from profile_api.config import Settings
from profile_api.database import Base
from profile_api.models import Profile, ProfileRevision

from conftest import (
    authorization,
    create_account,
    remove_m3_advancement,
    remove_m3_discovery_state,
    remove_m3_respec_state,
    remove_m4_run_state,
    remove_m4b_run_state,
    remove_m5_equipment_state,
    remove_m65_party_state,
    remove_m8_floor_four_run_state,
    remove_m8_floor_five_approach_run_state,
    remove_m8_region_progression_state,
)


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


class _AcceptedSavePort:
    def inspect(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def load(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def save(self, _game_state):
        return SaveLoadResult(SaveLoadStatus.SAVED)


def _schema29_expedition_report_payload():
    from app.game.expeditions import ExpeditionLaunchStatus, ExpeditionSettlementStatus

    started = datetime(2026, 11, 26, 12, tzinfo=timezone.utc)
    game = GameState(
        PlayerState(get_drifter_spec("branoc").create_character())
    )
    game.overworld_state.begin_surface_route()
    surface_nodes = get_route_spec("surface").nodes
    for node in surface_nodes[:-1]:
        if node.encounter_id is not None:
            game.world_state.mark_encounter_defeated(node.encounter_id)
        elif node.kind is RouteNodeKind.REST:
            game.overworld_state.record_resolved_rest_node(node.node_id)
    for node in surface_nodes[1:]:
        game.overworld_state.advance_to(node.node_id)
    party = game.party_state
    assert party.arrive_at_hub(game.player_state)
    first_companion = PlayerState(
        get_drifter_spec("azhvielle").create_character()
    )
    assert party.recruit_companion(game.player_state, first_companion, cost=0)
    assert party.begin_outing()
    assert party.begin_extraction(experience=0, gold=0)
    assert party.complete_extraction((game.player_state, first_companion))
    for drifter_id in ("joruun", "zhaivra"):
        companion = PlayerState(get_drifter_spec(drifter_id).create_character())
        assert party.recruit_companion(game.player_state, companion, cost=0)
    party.select_active_pair(
        ("branoc", "azhvielle"),
        recruited_ids=tuple(
            member.character.profile.drifter_id for member in game.recruited_members
        ),
    )
    party._floor_one_cleared = True
    party._floor_two_cleared = True
    party._floor_three_cleared = True
    party._floor_four_cleared = True

    service = ExpeditionService(
        _AcceptedSavePort(),
        now_factory=lambda: started,
        assignment_id_factory=lambda: UUID(
            "00000000-0000-4000-8000-000000000029"
        ),
        run_id_factory=lambda: "schema29-floor-one-run",
    )
    launched = service.launch(
        game,
        outing_floor_id="floor_one",
        destination_floor_id="floor_four",
        category="training",
        confirmed=True,
    )
    assert launched.status is ExpeditionLaunchStatus.LAUNCHED
    outing = launched.game_state
    outing.party_state._add_outing_rewards(experience=100, gold=0)
    assert outing.party_state.begin_floor_one_extraction(partial=False)
    secured_xp = outing.party_state.outing_rewards.experience
    assert outing.party_state.complete_extraction(outing.active_party_members)
    outing.overworld_state.return_to_surface_entrance()
    settled = service.settle_outing(
        outing,
        secured_base_xp=secured_xp,
        now=started + timedelta(minutes=20),
    )
    assert settled.status is ExpeditionSettlementStatus.SETTLED
    assert len(settled.game_state.expedition_state.reports) == 1
    return build_save_document(settled.game_state)


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


def _run_schema_history_advancement(api, session_factory, historical_schema):
    account = create_account(api)
    account_id = UUID(account["account_id"])
    profile_id = uuid4()
    historical_save_id = uuid4()
    device_id = UUID("00000000-0000-4000-8000-000000000024")
    current_payload = build_save_document(_game_state())
    historical_payload = deepcopy(current_payload)
    historical_payload["schema_version"] = historical_schema
    if historical_schema < 30:
        remove_m8_floor_five_approach_run_state(historical_payload)
    if historical_schema < 27:
        remove_m8_floor_four_run_state(historical_payload)
    if historical_schema < 26:
        remove_m8_region_progression_state(historical_payload)
    if historical_schema < 25:
        remove_m65_party_state(historical_payload)
    if historical_schema < 24:
        historical_payload.pop("expedition")
    if historical_schema < 15:
        remove_m3_advancement(historical_payload)
    if historical_schema < 16:
        remove_m3_discovery_state(historical_payload)
    if historical_schema < 17:
        remove_m3_respec_state(historical_payload)
    if historical_schema < 18:
        remove_m4_run_state(historical_payload)
    if historical_schema < 23:
        remove_m4b_run_state(historical_payload)
    remove_m5_equipment_state(historical_payload, historical_schema)
    if historical_schema < 13:
        historical_payload["party"].pop("active_drifter_ids")
        historical_payload["party"].pop("carried_items")
    if historical_schema == 11:
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
    migrated_payload["metadata"]["schema_migration"] = str(historical_schema)
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
    assert advanced.json()["head"]["payload"]["schema_version"] == 30
    with session_factory() as session:
        historical = session.get(ProfileRevision, (profile_id, 1))
        assert historical.payload == historical_payload
        assert historical.payload_sha256 == historical_digest


def test_schema11_remote_history_advances_to_schema30_without_mutation(service):
    api, session_factory = service
    _run_schema_history_advancement(api, session_factory, 11)


def test_schema12_remote_history_advances_to_schema30_without_mutation(service):
    api, session_factory = service
    _run_schema_history_advancement(api, session_factory, 12)


def test_schema15_remote_history_advances_to_schema30_without_mutation(service):
    api, session_factory = service
    _run_schema_history_advancement(api, session_factory, 15)


def test_schema16_remote_history_advances_to_schema30_without_mutation(service):
    api, session_factory = service
    _run_schema_history_advancement(api, session_factory, 16)


def test_schema17_remote_history_advances_to_schema30_without_mutation(service):
    api, session_factory = service
    _run_schema_history_advancement(api, session_factory, 17)


def test_schema18_remote_history_advances_to_schema30_without_mutation(service):
    api, session_factory = service
    _run_schema_history_advancement(api, session_factory, 18)


def test_schema19_remote_history_advances_to_schema30_without_mutation(service):
    api, session_factory = service
    _run_schema_history_advancement(api, session_factory, 19)


def test_schema20_remote_history_advances_to_schema30_without_mutation(service):
    api, session_factory = service
    _run_schema_history_advancement(api, session_factory, 20)


def test_schema21_remote_history_advances_to_schema30_without_mutation(service):
    api, session_factory = service
    _run_schema_history_advancement(api, session_factory, 21)


def test_schema22_remote_history_advances_to_schema30_without_mutation(service):
    api, session_factory = service
    _run_schema_history_advancement(api, session_factory, 22)


def test_schema24_remote_history_advances_to_schema30_without_mutation(service):
    api, session_factory = service
    _run_schema_history_advancement(api, session_factory, 24)


def test_schema26_remote_history_advances_to_schema30_without_mutation(service):
    api, session_factory = service
    _run_schema_history_advancement(api, session_factory, 26)


def test_schema27_remote_history_advances_to_schema30_without_mutation(service):
    api, session_factory = service
    _run_schema_history_advancement(api, session_factory, 27)


def test_schema29_remote_history_with_m85_report_advances_to_schema30(service):
    api, session_factory = service
    account = create_account(api)
    account_id = UUID(account["account_id"])
    profile_id = uuid4()
    historical_save_id = uuid4()
    device_id = UUID("00000000-0000-4000-8000-000000000029")
    current_payload = _schema29_expedition_report_payload()
    assert current_payload["schema_version"] == 30
    assert len(current_payload["expedition"]["reports"]) == 1
    historical_payload = deepcopy(current_payload)
    remove_m8_floor_five_approach_run_state(historical_payload)
    historical_payload["schema_version"] = 29
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
    current_payload["metadata"]["schema_migration"] = "29"
    advanced = api.put(
        f"/v1/profiles/{profile_id}/progression",
        headers=authorization(account["access_token"]),
        json={
            "base_revision": 1,
            "client_save_id": str(uuid4()),
            "device_id": str(device_id),
            "payload": current_payload,
        },
    )

    assert head.status_code == 200, head.text
    assert head.json()["head"]["payload"] == historical_payload
    assert head.json()["head"]["payload_sha256"] == historical_digest
    assert advanced.status_code == 200, advanced.text
    assert advanced.json()["accepted_revision"] == 2
    advanced_payload = advanced.json()["head"]["payload"]
    assert advanced_payload["schema_version"] == 30
    assert advanced_payload["expedition"]["reports"] == historical_payload[
        "expedition"
    ]["reports"]
    with session_factory() as session:
        historical = session.get(ProfileRevision, (profile_id, 1))
        assert historical.payload == historical_payload
        assert historical.payload_sha256 == historical_digest


@pytest.mark.skipif(
    not POSTGRES_URL
    or not POSTGRES_URL.startswith(("postgresql://", "postgresql+psycopg://")),
    reason="requires a dedicated PostgreSQL PROFILE_API_TEST_DATABASE_URL",
)
def test_schema11_remote_history_advances_to_schema30_on_postgresql():
    engine = create_engine(POSTGRES_URL, pool_size=8, max_overflow=2)
    try:
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(engine, expire_on_commit=False)
        app = create_app(session_factory=session_factory, settings=Settings())
        with TestClient(app) as api:
            _run_schema_history_advancement(api, session_factory, 11)
    finally:
        engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL
    or not POSTGRES_URL.startswith(("postgresql://", "postgresql+psycopg://")),
    reason="requires a dedicated PostgreSQL PROFILE_API_TEST_DATABASE_URL",
)
def test_schema12_remote_history_advances_to_schema30_on_postgresql():
    engine = create_engine(POSTGRES_URL, pool_size=8, max_overflow=2)
    try:
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(engine, expire_on_commit=False)
        app = create_app(session_factory=session_factory, settings=Settings())
        with TestClient(app) as api:
            _run_schema_history_advancement(api, session_factory, 12)
    finally:
        engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL
    or not POSTGRES_URL.startswith(("postgresql://", "postgresql+psycopg://")),
    reason="requires a dedicated PostgreSQL PROFILE_API_TEST_DATABASE_URL",
)
def test_schema15_remote_history_advances_to_schema30_on_postgresql():
    engine = create_engine(POSTGRES_URL, pool_size=8, max_overflow=2)
    try:
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(engine, expire_on_commit=False)
        app = create_app(session_factory=session_factory, settings=Settings())
        with TestClient(app) as api:
            _run_schema_history_advancement(api, session_factory, 15)
    finally:
        engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL
    or not POSTGRES_URL.startswith(("postgresql://", "postgresql+psycopg://")),
    reason="requires a dedicated PostgreSQL PROFILE_API_TEST_DATABASE_URL",
)
def test_schema16_remote_history_advances_to_schema30_on_postgresql():
    engine = create_engine(POSTGRES_URL, pool_size=8, max_overflow=2)
    try:
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(engine, expire_on_commit=False)
        app = create_app(session_factory=session_factory, settings=Settings())
        with TestClient(app) as api:
            _run_schema_history_advancement(api, session_factory, 16)
    finally:
        engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL
    or not POSTGRES_URL.startswith(("postgresql://", "postgresql+psycopg://")),
    reason="requires a dedicated PostgreSQL PROFILE_API_TEST_DATABASE_URL",
)
def test_schema17_remote_history_advances_to_schema30_on_postgresql():
    engine = create_engine(POSTGRES_URL, pool_size=8, max_overflow=2)
    try:
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(engine, expire_on_commit=False)
        app = create_app(session_factory=session_factory, settings=Settings())
        with TestClient(app) as api:
            _run_schema_history_advancement(api, session_factory, 17)
    finally:
        engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL
    or not POSTGRES_URL.startswith(("postgresql://", "postgresql+psycopg://")),
    reason="requires a dedicated PostgreSQL PROFILE_API_TEST_DATABASE_URL",
)
@pytest.mark.parametrize("historical_schema", (18, 19, 20, 21))
def test_schema18_through_21_history_advances_to_schema30_on_postgresql(
    historical_schema,
):
    engine = create_engine(POSTGRES_URL, pool_size=8, max_overflow=2)
    try:
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(engine, expire_on_commit=False)
        app = create_app(session_factory=session_factory, settings=Settings())
        with TestClient(app) as api:
            _run_schema_history_advancement(api, session_factory, historical_schema)
    finally:
        engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL
    or not POSTGRES_URL.startswith(("postgresql://", "postgresql+psycopg://")),
    reason="requires a dedicated PostgreSQL PROFILE_API_TEST_DATABASE_URL",
)
def test_schema22_remote_history_advances_to_schema30_on_postgresql():
    engine = create_engine(POSTGRES_URL, pool_size=8, max_overflow=2)
    try:
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(engine, expire_on_commit=False)
        app = create_app(session_factory=session_factory, settings=Settings())
        with TestClient(app) as api:
            _run_schema_history_advancement(api, session_factory, 22)
    finally:
        engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL
    or not POSTGRES_URL.startswith(("postgresql://", "postgresql+psycopg://")),
    reason="requires a dedicated PostgreSQL PROFILE_API_TEST_DATABASE_URL",
)
def test_schema24_remote_history_advances_to_schema30_on_postgresql():
    engine = create_engine(POSTGRES_URL, pool_size=8, max_overflow=2)
    try:
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(engine, expire_on_commit=False)
        app = create_app(session_factory=session_factory, settings=Settings())
        with TestClient(app) as api:
            _run_schema_history_advancement(api, session_factory, 24)
    finally:
        engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL
    or not POSTGRES_URL.startswith(("postgresql://", "postgresql+psycopg://")),
    reason="requires a dedicated PostgreSQL PROFILE_API_TEST_DATABASE_URL",
)
def test_schema26_remote_history_advances_to_schema30_on_postgresql():
    engine = create_engine(POSTGRES_URL, pool_size=8, max_overflow=2)
    try:
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(engine, expire_on_commit=False)
        app = create_app(session_factory=session_factory, settings=Settings())
        with TestClient(app) as api:
            _run_schema_history_advancement(api, session_factory, 26)
    finally:
        engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_URL
    or not POSTGRES_URL.startswith(("postgresql://", "postgresql+psycopg://")),
    reason="requires a dedicated PostgreSQL PROFILE_API_TEST_DATABASE_URL",
)
def test_schema27_remote_history_advances_to_schema30_on_postgresql():
    engine = create_engine(POSTGRES_URL, pool_size=8, max_overflow=2)
    try:
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(engine, expire_on_commit=False)
        app = create_app(session_factory=session_factory, settings=Settings())
        with TestClient(app) as api:
            _run_schema_history_advancement(api, session_factory, 27)
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

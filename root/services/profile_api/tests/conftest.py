import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = SERVICE_ROOT.parents[1]
for source_root in (REPOSITORY_ROOT / "src", SERVICE_ROOT / "src"):
    sys.path.insert(0, str(source_root))

from app.content.catalog import get_drifter_spec_by_choice
from app.game.game_state import GameState
from app.persistence.save_document import build_save_document
from app.player.player_state import PlayerState
from profile_api.app import create_app
from profile_api.config import Settings
from profile_api.database import Base


def make_payload(gold=0, marker=None):
    character = get_drifter_spec_by_choice("1").create_character()
    game_state = GameState(PlayerState(character, gold=gold))
    if marker is not None:
        game_state.set_metadata("profile_api_test", marker)
    return build_save_document(game_state)


def remove_m3_advancement(payload):
    players = [payload.get("player")]
    party = payload.get("party")
    if isinstance(party, dict) and isinstance(party.get("companions"), list):
        players.extend(party["companions"])
    for player in players:
        if isinstance(player, dict):
            player.pop("advancement", None)
    return payload


def remove_m3_discovery_state(payload):
    players = [payload.get("player")]
    party = payload.get("party")
    if isinstance(party, dict) and isinstance(party.get("companions"), list):
        players.extend(party["companions"])
    for player in players:
        if isinstance(player, dict):
            player.pop("permanent_discovery_bonuses", None)
    world = payload.get("world")
    if isinstance(world, dict):
        world.pop("permanent_discovery_claims", None)
    return payload


def remove_m3_respec_state(payload):
    players = [payload.get("player")]
    party = payload.get("party")
    if isinstance(party, dict) and isinstance(party.get("companions"), list):
        players.extend(party["companions"])
    for player in players:
        advancement = player.get("advancement") if isinstance(player, dict) else None
        if isinstance(advancement, dict):
            advancement.pop("purchased_stat_points", None)
            advancement.pop("respec_count", None)
    return payload


def remove_m4_run_state(payload):
    payload.pop("expedition", None)
    party = payload.get("party")
    if isinstance(party, dict):
        for field in (
            "floor_two_cleared",
            "floor_two_runs_started_after_clear",
            "floor_two_run_id",
            "floor_two_outing_xp_multiplier_percent",
            "resolved_run_events",
            "floor_three_cleared",
            "floor_three_runs_started_after_clear",
            "floor_three_run_id",
            "floor_three_outing_xp_multiplier_percent",
        ):
            party.pop(field, None)
    world = payload.get("world")
    if isinstance(world, dict):
        world.pop("discovered_permanent_discovery_sources", None)
    return payload


def remove_m4b_run_state(payload):
    payload.pop("expedition", None)
    party = payload.get("party")
    if isinstance(party, dict):
        for field in (
            "floor_three_cleared",
            "floor_three_runs_started_after_clear",
            "floor_three_run_id",
            "floor_three_outing_xp_multiplier_percent",
        ):
            party.pop(field, None)
    return payload


def remove_m5_equipment_state(payload, historical_schema):
    party = payload.get("party")
    players = [payload.get("player")]
    if isinstance(party, dict) and isinstance(party.get("companions"), list):
        players.extend(party["companions"])
    if historical_schema < 19:
        for player in players:
            if isinstance(player, dict):
                player.pop("equipment_refs", None)
        if isinstance(party, dict):
            party.pop("equipment_instances", None)
    if historical_schema < 21 and isinstance(party, dict):
        party.pop("modifier_instances", None)
    return payload


def create_account(client):
    response = client.post(
        "/v1/accounts/anonymous",
        json={"device_id": "00000000-0000-4000-8000-000000000003"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def authorization(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def service(tmp_path):
    database_path = tmp_path / "profile-api.sqlite3"
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    app = create_app(session_factory=session_factory, settings=Settings())
    with TestClient(app) as client:
        yield client, session_factory
    engine.dispose()


@pytest.fixture
def valid_payload():
    return make_payload()

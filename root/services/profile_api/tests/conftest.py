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

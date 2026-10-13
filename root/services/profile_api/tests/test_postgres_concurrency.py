import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from profile_api.app import create_app
from profile_api.config import Settings
from profile_api.database import Base

from conftest import authorization, create_account, make_payload


POSTGRES_URL = os.environ.get("PROFILE_API_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL or not POSTGRES_URL.startswith(("postgresql://", "postgresql+psycopg://")),
    reason="requires a dedicated PostgreSQL PROFILE_API_TEST_DATABASE_URL",
)


def test_concurrent_same_base_writes_create_only_one_next_revision():
    engine = create_engine(POSTGRES_URL, pool_size=8, max_overflow=2)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    app = create_app(session_factory=session_factory, settings=Settings())
    client = TestClient(app)
    account = create_account(client)
    token_headers = authorization(account["access_token"])
    profile_id = uuid4()
    created = client.post(
        "/v1/profiles",
        headers=token_headers,
        json={
            "profile_id": str(profile_id),
            "client_save_id": str(uuid4()),
            "device_id": str(uuid4()),
            "payload": make_payload(),
        },
    )
    assert created.status_code == 201, created.text

    def push(marker):
        payload = make_payload(marker=marker)
        return client.put(
            f"/v1/profiles/{profile_id}/progression",
            headers=token_headers,
            json={
                "base_revision": 1,
                "client_save_id": str(uuid4()),
                "device_id": str(uuid4()),
                "payload": payload,
            },
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = tuple(pool.map(push, ("writer-a", "writer-b")))

    assert sorted(response.status_code for response in responses) == [200, 409]
    head = client.get(f"/v1/profiles/{profile_id}", headers=token_headers)
    assert head.status_code == 200
    assert head.json()["current_revision"] == 2
    client.close()
    engine.dispose()

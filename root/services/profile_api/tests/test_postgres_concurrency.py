import os
from threading import Barrier
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from profile_api.identity import (
    IdentityRecoveryRequired,
    IdentityService,
    VerifiedIdentity,
)
from profile_api.app import create_app
from profile_api.config import Settings
from profile_api.database import Base
from profile_api.models import AccountSession, LinkedIdentity, utc_now

from conftest import authorization, create_account, make_payload


POSTGRES_URL = os.environ.get("PROFILE_API_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL or not POSTGRES_URL.startswith(("postgresql://", "postgresql+psycopg://")),
    reason="requires a dedicated PostgreSQL PROFILE_API_TEST_DATABASE_URL",
)


class _IdentityVerifier:
    def verify(self, proof):
        return VerifiedIdentity("test-provider", proof)


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


def test_concurrent_unlinks_preserve_one_recovery_identity():
    engine = create_engine(POSTGRES_URL, pool_size=8, max_overflow=2)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    app = create_app(session_factory=session_factory, settings=Settings())
    client = TestClient(app)
    account = create_account(client)
    account_id = UUID(account["account_id"])
    verifier = _IdentityVerifier()

    with session_factory() as session:
        identity_a = IdentityService(session, verifier).link(
            account_id, f"subject-a-{account_id}"
        )
        identity_b = IdentityService(session, verifier).link(
            account_id, f"subject-b-{account_id}"
        )
        for record in session.scalars(
            select(AccountSession).where(AccountSession.account_id == account_id)
        ):
            record.revoked_at = utc_now()
        session.commit()

    start = Barrier(2)

    def unlink(identity_id):
        with session_factory() as session:
            start.wait(timeout=10)
            try:
                IdentityService(session, verifier).unlink(account_id, identity_id)
                session.commit()
                return "unlinked"
            except IdentityRecoveryRequired:
                session.rollback()
                return "recovery_required"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(unlink, (identity_a.id, identity_b.id)))

    assert sorted(results) == ["recovery_required", "unlinked"]
    with session_factory() as session:
        remaining = session.scalar(
            select(func.count()).select_from(LinkedIdentity).where(
                LinkedIdentity.account_id == account_id
            )
        )
        assert remaining == 1
    client.close()
    engine.dispose()


def test_unlink_racing_last_session_revoke_preserves_a_recovery_path():
    engine = create_engine(POSTGRES_URL, pool_size=8, max_overflow=2)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    app = create_app(session_factory=session_factory, settings=Settings())
    client = TestClient(app)
    account = create_account(client)
    account_id = UUID(account["account_id"])
    verifier = _IdentityVerifier()
    with session_factory() as session:
        identity = IdentityService(session, verifier).link(
            account_id, f"only-subject-{account_id}"
        )
        session.commit()

    start = Barrier(2)

    def unlink():
        with session_factory() as session:
            start.wait(timeout=10)
            try:
                IdentityService(session, verifier).unlink(account_id, identity.id)
                session.commit()
                return "unlinked"
            except IdentityRecoveryRequired:
                session.rollback()
                return "recovery_required"

    def revoke():
        start.wait(timeout=10)
        response = client.delete(
            "/v1/sessions/current",
            headers=authorization(account["access_token"]),
        )
        if response.status_code == 204:
            return "revoked"
        if (
            response.status_code == 409
            and response.json()["error"]["code"] == "identity_recovery_required"
        ):
            return "recovery_required"
        return f"unexpected_{response.status_code}"

    with ThreadPoolExecutor(max_workers=2) as pool:
        unlink_future = pool.submit(unlink)
        revoke_future = pool.submit(revoke)
        results = (unlink_future.result(), revoke_future.result())

    assert set(results) in (
        {"unlinked", "recovery_required"},
        {"recovery_required", "revoked"},
    )
    with session_factory() as session:
        remaining_identities = session.scalar(
            select(func.count()).select_from(LinkedIdentity).where(
                LinkedIdentity.account_id == account_id
            )
        )
        remaining_sessions = session.scalar(
            select(func.count()).select_from(AccountSession).where(
                AccountSession.account_id == account_id,
                AccountSession.revoked_at.is_(None),
                AccountSession.refresh_expires_at > utc_now(),
            )
        )
        assert remaining_identities + remaining_sessions >= 1
    client.close()
    engine.dispose()

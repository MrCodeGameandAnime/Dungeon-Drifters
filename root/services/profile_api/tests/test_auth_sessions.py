import hashlib
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select

from profile_api.identity import IdentityService, VerifiedIdentity
from profile_api.models import AccountSession

from conftest import authorization, create_account


def test_anonymous_account_creates_dd_identity_with_hashed_credentials(service):
    client, session_factory = service
    created = create_account(client)

    assert created["account_id"]
    assert len(created["access_token"]) >= 40
    assert len(created["refresh_token"]) >= 40
    assert created["access_expires_at"].endswith("Z")
    assert created["refresh_expires_at"].endswith("Z")

    with session_factory() as session:
        stored = session.scalar(select(AccountSession))
    assert stored.access_token_hash == hashlib.sha256(
        created["access_token"].encode("ascii")
    ).hexdigest()
    assert stored.refresh_token_hash == hashlib.sha256(
        created["refresh_token"].encode("ascii")
    ).hexdigest()
    assert created["access_token"] not in repr(stored)
    assert created["refresh_token"] not in repr(stored)


def test_refresh_reissues_access_token_without_rotating_refresh_token(service):
    client, session_factory = service
    created = create_account(client)

    response = client.post(
        "/v1/sessions/refresh",
        json={"refresh_token": created["refresh_token"]},
    )

    assert response.status_code == 200
    refreshed = response.json()
    assert refreshed["access_token"] != created["access_token"]
    assert refreshed["access_expires_at"].endswith("Z")
    assert "refresh_token" not in refreshed
    with session_factory() as session:
        stored = session.scalar(select(AccountSession))
    assert stored.refresh_token_hash == hashlib.sha256(
        created["refresh_token"].encode("ascii")
    ).hexdigest()
    assert stored.access_token_hash == hashlib.sha256(
        refreshed["access_token"].encode("ascii")
    ).hexdigest()
    assert client.get(
        "/v1/profiles",
        headers=authorization(created["access_token"]),
    ).status_code == 401


def test_revocation_invalidates_access_and_refresh_credentials(service):
    client, session_factory = service
    created = create_account(client)
    headers = authorization(created["access_token"])

    class _Verifier:
        def verify(self, proof):
            return VerifiedIdentity("test-provider", proof)

    with session_factory() as session:
        IdentityService(session, _Verifier()).link(
            UUID(created["account_id"]), "revocation-recovery-subject"
        )
        session.commit()

    response = client.delete("/v1/sessions/current", headers=headers)

    assert response.status_code == 204
    assert client.get("/v1/profiles", headers=headers).status_code == 401
    refreshed = client.post(
        "/v1/sessions/refresh",
        json={"refresh_token": created["refresh_token"]},
    )
    assert refreshed.status_code == 401


def test_auth_errors_use_sanitized_contract_shape(service):
    client, _ = service

    missing = client.get("/v1/profiles")
    invalid = client.get(
        "/v1/profiles",
        headers=authorization("not-a-secret-token"),
    )
    malformed = client.post(
        "/v1/accounts/anonymous",
        content="{",
        headers={"content-type": "application/json"},
    )

    assert missing.status_code == 401
    assert missing.json()["error"]["code"] == "unauthorized"
    assert "token_hash" not in missing.text.lower()
    assert invalid.status_code == 401
    assert "not-a-secret-token" not in invalid.text
    assert malformed.status_code == 400
    assert malformed.json()["error"]["code"] == "invalid_json"


def test_anonymous_account_request_rejects_unknown_fields(service):
    client, _ = service

    response = client.post(
        "/v1/accounts/anonymous",
        json={"device_id": str(uuid4()), "account_id": str(uuid4())},
    )

    assert response.status_code == 422

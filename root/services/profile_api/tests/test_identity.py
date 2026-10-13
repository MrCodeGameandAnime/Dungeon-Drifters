from uuid import UUID

import pytest
from sqlalchemy import func, select

from profile_api.identity import (
    IdentityAlreadyLinked,
    IdentityRecoveryRequired,
    IdentityService,
    IdentityVerificationError,
    VerifiedIdentity,
)
from profile_api.models import AccountSession, LinkedIdentity
from profile_api.models import utc_now

from conftest import create_account


class FakeVerifier:
    def __init__(self, identities):
        self.identities = identities

    def verify(self, proof):
        try:
            return self.identities[proof]
        except (KeyError, TypeError) as error:
            raise IdentityVerificationError("external identity proof was rejected") from error


def test_only_verifier_approved_identity_can_be_linked(service):
    client, session_factory = service
    account = create_account(client)
    verifier = FakeVerifier({"valid-proof": VerifiedIdentity("test-provider", "subject-1")})

    with session_factory() as session:
        service_layer = IdentityService(session, verifier)
        with pytest.raises(IdentityVerificationError):
            service_layer.link(UUID(account["account_id"]), "untrusted-provider-subject")
        linked = service_layer.link(UUID(account["account_id"]), "valid-proof")
        session.commit()

    assert linked.provider == "test-provider"
    assert linked.provider_subject == "subject-1"
    assert client.post(
        "/v1/identities/link",
        headers={"Authorization": f"Bearer {account['access_token']}"},
        json={"provider": "test-provider", "provider_subject": "attacker-choice"},
    ).status_code == 404


def test_identity_already_linked_cannot_move_to_another_account(service):
    client, session_factory = service
    first = create_account(client)
    second = create_account(client)
    identity = VerifiedIdentity("test-provider", "unique-subject")
    verifier = FakeVerifier({"proof": identity})

    with session_factory() as session:
        service_layer = IdentityService(session, verifier)
        service_layer.link(UUID(first["account_id"]), "proof")
        session.commit()
    with session_factory() as session:
        service_layer = IdentityService(session, verifier)
        with pytest.raises(IdentityAlreadyLinked):
            service_layer.link(UUID(second["account_id"]), "proof")
        assert session.scalar(select(func.count()).select_from(LinkedIdentity)) == 1


def test_removing_last_identity_requires_another_recovery_path(service):
    client, session_factory = service
    account = create_account(client)
    account_id = UUID(account["account_id"])
    verifier = FakeVerifier(
        {
            "first-proof": VerifiedIdentity("test-provider", "subject-1"),
            "second-proof": VerifiedIdentity("test-provider", "subject-2"),
        }
    )
    with session_factory() as session:
        service_layer = IdentityService(session, verifier)
        first = service_layer.link(account_id, "first-proof")
        sessions = session.scalars(
            select(AccountSession).where(AccountSession.account_id == account_id)
        ).all()
        for record in sessions:
            record.revoked_at = utc_now()
        session.commit()

    with session_factory() as session:
        service_layer = IdentityService(session, verifier)
        with pytest.raises(IdentityRecoveryRequired):
            service_layer.unlink(account_id, first.id)
        assert session.scalar(select(LinkedIdentity.id)) == first.id

        second = service_layer.link(account_id, "second-proof")
        session.commit()
    with session_factory() as session:
        service_layer = IdentityService(session, verifier)
        service_layer.unlink(account_id, first.id)
        session.commit()
        remaining = session.scalars(
            select(LinkedIdentity).where(LinkedIdentity.account_id == account_id)
        ).all()

    assert len(remaining) == 1
    assert remaining[0].id == second.id


def test_current_session_cannot_be_revoked_after_last_identity_is_removed(service):
    client, session_factory = service
    account = create_account(client)
    account_id = UUID(account["account_id"])
    verifier = FakeVerifier(
        {"only-proof": VerifiedIdentity("test-provider", "only-subject")}
    )
    with session_factory() as session:
        identity = IdentityService(session, verifier).link(account_id, "only-proof")
        session.commit()
    with session_factory() as session:
        IdentityService(session, verifier).unlink(account_id, identity.id)
        session.commit()

    response = client.delete(
        "/v1/sessions/current",
        headers={"Authorization": f"Bearer {account['access_token']}"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "identity_recovery_required"
    with session_factory() as session:
        active = session.scalar(
            select(AccountSession).where(
                AccountSession.account_id == account_id,
                AccountSession.revoked_at.is_(None),
            )
        )
        assert active is not None
        assert session.scalar(select(func.count()).select_from(LinkedIdentity)) == 0

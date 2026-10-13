"""Internal verified-identity boundary; external proof adapters are deferred."""

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from profile_api.models import Account, AccountSession, LinkedIdentity, utc_now


_PROVIDER_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{0,31}\Z")


class IdentityError(RuntimeError):
    """Base error for trusted identity operations."""


class IdentityVerificationError(IdentityError):
    pass


class IdentityAlreadyLinked(IdentityError):
    pass


class IdentityNotFound(IdentityError):
    pass


class IdentityRecoveryRequired(IdentityError):
    pass


@dataclass(frozen=True)
class VerifiedIdentity:
    provider: str
    provider_subject: str = field(repr=False)


class IdentityVerifier(Protocol):
    def verify(self, proof: object) -> VerifiedIdentity: ...


class IdentityService:
    def __init__(self, session: Session, verifier: IdentityVerifier):
        self._session = session
        self._verifier = verifier

    def link(self, account_id: UUID, proof: object) -> LinkedIdentity:
        account = self._lock_account(account_id)
        if account is None or account.status != "active":
            raise IdentityNotFound("account is unavailable")
        identity = self._verify(proof)
        existing = self._find(identity.provider, identity.provider_subject)
        if existing is not None:
            if existing.account_id != account_id:
                raise IdentityAlreadyLinked("external identity belongs to another DD account")
            return existing

        linked = LinkedIdentity(
            id=uuid4(),
            account_id=account_id,
            provider=identity.provider,
            provider_subject=identity.provider_subject,
            created_at=utc_now(),
        )
        try:
            with self._session.begin_nested():
                self._session.add(linked)
                self._session.flush()
        except IntegrityError:
            existing = self._find(identity.provider, identity.provider_subject)
            if existing is None:
                raise
            if existing.account_id != account_id:
                raise IdentityAlreadyLinked(
                    "external identity belongs to another DD account"
                )
            return existing
        return linked

    def unlink(self, account_id: UUID, identity_id: UUID, *, now=None) -> None:
        account = self._lock_account(account_id)
        if account is None or account.status != "active":
            raise IdentityNotFound("account is unavailable")
        linked = self._session.scalar(
            select(LinkedIdentity)
            .where(
                LinkedIdentity.id == identity_id,
                LinkedIdentity.account_id == account_id,
            )
            .with_for_update()
        )
        if linked is None:
            raise IdentityNotFound("linked identity is unavailable")

        other_identities = self._session.scalar(
            select(func.count()).select_from(LinkedIdentity).where(
                LinkedIdentity.account_id == account_id,
                LinkedIdentity.id != identity_id,
            )
        )
        instant = utc_now() if now is None else now
        if not isinstance(instant, datetime) or instant.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        active_session = self._session.scalar(
            select(AccountSession.id)
            .where(
                AccountSession.account_id == account_id,
                AccountSession.revoked_at.is_(None),
                AccountSession.refresh_expires_at > instant,
            )
            .limit(1)
        )
        if not other_identities and active_session is None:
            raise IdentityRecoveryRequired(
                "another linked identity or active refreshable session is required"
            )
        self._session.delete(linked)
        self._session.flush()

    def _lock_account(self, account_id):
        return self._session.scalar(
            select(Account)
            .where(Account.id == account_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

    def _verify(self, proof):
        try:
            identity = self._verifier.verify(proof)
        except IdentityVerificationError:
            raise
        except Exception as error:
            raise IdentityVerificationError("external identity proof was rejected") from error
        if not isinstance(identity, VerifiedIdentity):
            raise IdentityVerificationError("identity verifier returned an invalid result")
        provider = identity.provider
        subject = identity.provider_subject
        if (
            not isinstance(provider, str)
            or not _PROVIDER_PATTERN.fullmatch(provider)
            or not isinstance(subject, str)
            or not subject
            or len(subject) > 255
            or any(ord(character) < 32 for character in subject)
        ):
            raise IdentityVerificationError("verified identity fields are invalid")
        return identity

    def _find(self, provider, provider_subject):
        return self._session.scalar(
            select(LinkedIdentity).where(
                LinkedIdentity.provider == provider,
                LinkedIdentity.provider_subject == provider_subject,
            )
        )

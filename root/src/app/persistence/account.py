"""Host-neutral DD account credentials, separate from local progression data."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


class AccountCredentialError(ValueError):
    """Raised when an API credential response cannot be used safely."""


@dataclass(frozen=True)
class AccountCredentials:
    account_id: UUID
    access_token: str = field(repr=False)
    access_expires_at: datetime
    refresh_token: str = field(repr=False)
    refresh_expires_at: datetime

    def __post_init__(self):
        if not isinstance(self.account_id, UUID):
            raise AccountCredentialError("account_id must be a UUID")
        for name in ("access_token", "refresh_token"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise AccountCredentialError(f"{name} must be a non-empty string")
        for name in ("access_expires_at", "refresh_expires_at"):
            value = getattr(self, name)
            if (
                not isinstance(value, datetime)
                or value.tzinfo is None
                or value.utcoffset() is None
                or value.utcoffset().total_seconds() != 0
            ):
                raise AccountCredentialError(f"{name} must be a UTC datetime")

    @classmethod
    def from_anonymous_response(cls, document):
        expected = {
            "account_id",
            "access_token",
            "access_expires_at",
            "refresh_token",
            "refresh_expires_at",
        }
        if not isinstance(document, dict) or set(document) != expected:
            raise AccountCredentialError("anonymous account response has an invalid shape")
        account_id = _parse_canonical_uuid(document["account_id"])
        return cls(
            account_id=account_id,
            access_token=document["access_token"],
            access_expires_at=_parse_utc_timestamp(document["access_expires_at"]),
            refresh_token=document["refresh_token"],
            refresh_expires_at=_parse_utc_timestamp(document["refresh_expires_at"]),
        )

    def with_refreshed_access_response(self, document):
        expected = {"access_token", "access_expires_at"}
        if not isinstance(document, dict) or set(document) != expected:
            raise AccountCredentialError("session refresh response has an invalid shape")
        return AccountCredentials(
            account_id=self.account_id,
            access_token=document["access_token"],
            access_expires_at=_parse_utc_timestamp(document["access_expires_at"]),
            refresh_token=self.refresh_token,
            refresh_expires_at=self.refresh_expires_at,
        )


def _parse_canonical_uuid(value):
    if not isinstance(value, str):
        raise AccountCredentialError("account_id must be a canonical UUID")
    try:
        parsed = UUID(value)
    except (TypeError, ValueError, AttributeError) as error:
        raise AccountCredentialError("account_id must be a canonical UUID") from error
    if str(parsed) != value:
        raise AccountCredentialError("account_id must be a canonical UUID")
    return parsed


def _parse_utc_timestamp(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise AccountCredentialError("credential timestamps must be UTC RFC 3339")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise AccountCredentialError("credential timestamps must be UTC RFC 3339") from error
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise AccountCredentialError("credential timestamps must be UTC RFC 3339")
    return parsed


__all__ = ["AccountCredentialError", "AccountCredentials"]

"""Authenticated DD profile API boundary over a host-provided JSON transport."""

import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Union
from uuid import UUID

from app.persistence.envelope import payload_sha256
from app.persistence.save_document import validate_save_document


_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


class RemoteProfileError(RuntimeError):
    """Base class for safe, transport-independent profile API errors."""


class RemoteUnavailable(RemoteProfileError):
    """The remote service could not be reached or is temporarily unavailable."""


class RemoteAuthenticationRequired(RemoteProfileError):
    """The current access credential was rejected by the service."""


class RemoteProfileNotFound(RemoteProfileError):
    """The profile is absent or is not owned by the authenticated account."""


class RemoteProfileCreationConflict(RemoteProfileError):
    """The profile already exists with a different initial save."""


class RemoteRequestRejected(RemoteProfileError):
    def __init__(self, code):
        self.code = code if isinstance(code, str) else "request_rejected"
        super().__init__(self.code)


class RemoteProtocolError(ValueError):
    """The remote API response did not satisfy the canonical v1 contract."""


@dataclass(frozen=True)
class RemoteProfileSummary:
    profile_id: UUID
    current_revision: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_response(cls, document):
        expected = {"profile_id", "current_revision", "created_at", "updated_at"}
        if not isinstance(document, dict) or set(document) != expected:
            raise RemoteProtocolError("remote profile summary has an invalid shape")
        return cls(
            profile_id=_parse_uuid(document["profile_id"], "profile_id"),
            current_revision=_positive_int(
                document["current_revision"], "current_revision"
            ),
            created_at=_parse_timestamp(document["created_at"], "created_at"),
            updated_at=_parse_timestamp(document["updated_at"], "updated_at"),
        )


@dataclass(frozen=True)
class RemoteProfileHead:
    profile_id: UUID
    account_id: UUID
    current_revision: int
    client_save_id: UUID
    payload_sha256: str
    payload: dict
    base_revision: int | None = None
    created_revision: int | None = None
    accepted_revision: int | None = None

    def __post_init__(self):
        if not isinstance(self.profile_id, UUID) or not isinstance(self.account_id, UUID):
            raise RemoteProtocolError("remote profile identity is invalid")
        if not isinstance(self.client_save_id, UUID):
            raise RemoteProtocolError("remote save identity is invalid")
        _positive_int(self.current_revision, "current_revision")
        if self.base_revision is not None:
            _positive_int(self.base_revision, "base_revision")
            if self.base_revision >= self.current_revision:
                raise RemoteProtocolError("remote head base revision is invalid")
        for name in ("created_revision", "accepted_revision"):
            revision = getattr(self, name)
            if revision is not None:
                _positive_int(revision, name)
                if revision > self.current_revision:
                    raise RemoteProtocolError(f"{name} exceeds current_revision")
        if (
            not isinstance(self.payload_sha256, str)
            or not _DIGEST_PATTERN.fullmatch(self.payload_sha256)
        ):
            raise RemoteProtocolError("remote payload digest is invalid")
        if not isinstance(self.payload, dict):
            raise RemoteProtocolError("remote payload is invalid")
        try:
            normalized = validate_save_document(self.payload)
            actual_digest = payload_sha256(normalized)
        except (TypeError, ValueError) as error:
            raise RemoteProtocolError("remote payload is invalid") from error
        if normalized != self.payload:
            raise RemoteProtocolError("remote payload is not canonical schema 8")
        if actual_digest != self.payload_sha256:
            raise RemoteProtocolError("remote payload digest does not match payload")
        object.__setattr__(self, "payload", deepcopy(normalized))

    @classmethod
    def from_response(cls, document):
        required = {"profile_id", "account_id", "current_revision", "head"}
        optional = {"created_revision", "accepted_revision"}
        if (
            not isinstance(document, dict)
            or not required.issubset(document)
            or set(document) - required - optional
        ):
            raise RemoteProtocolError("remote profile response has an invalid shape")
        head = document["head"]
        expected_head = {
            "revision",
            "base_revision",
            "client_save_id",
            "device_id",
            "payload_sha256",
            "created_at",
            "payload",
        }
        if not isinstance(head, dict) or set(head) != expected_head:
            raise RemoteProtocolError("remote head response has an invalid shape")
        profile_id = _parse_uuid(document["profile_id"], "profile_id")
        account_id = _parse_uuid(document["account_id"], "account_id")
        current_revision = _positive_int(document["current_revision"], "current_revision")
        revision = _positive_int(head["revision"], "head.revision")
        if revision != current_revision:
            raise RemoteProtocolError("remote head does not match current_revision")
        base_revision = head["base_revision"]
        if base_revision is not None:
            base_revision = _positive_int(base_revision, "head.base_revision")
        if head["device_id"] is not None:
            _parse_uuid(head["device_id"], "head.device_id")
        _parse_timestamp(head["created_at"], "head.created_at")
        return cls(
            profile_id=profile_id,
            account_id=account_id,
            current_revision=current_revision,
            client_save_id=_parse_uuid(head["client_save_id"], "client_save_id"),
            payload_sha256=head["payload_sha256"],
            payload=head["payload"],
            base_revision=base_revision,
            created_revision=_optional_positive_int(
                document.get("created_revision"), "created_revision"
            ),
            accepted_revision=_optional_positive_int(
                document.get("accepted_revision"), "accepted_revision"
            ),
        )


@dataclass(frozen=True)
class RemoteConflict:
    profile_id: UUID
    base_revision: int
    current_revision: int
    client_save_id: UUID
    payload_sha256: str

    def __post_init__(self):
        if not isinstance(self.profile_id, UUID) or not isinstance(self.client_save_id, UUID):
            raise RemoteProtocolError("remote conflict identity is invalid")
        _positive_int(self.base_revision, "base_revision")
        _positive_int(self.current_revision, "current_revision")
        if self.current_revision <= self.base_revision:
            raise RemoteProtocolError("remote conflict revisions are invalid")
        if (
            not isinstance(self.payload_sha256, str)
            or not _DIGEST_PATTERN.fullmatch(self.payload_sha256)
        ):
            raise RemoteProtocolError("remote conflict digest is invalid")


class RemoteProfileClient(Protocol):
    def list_profiles(self) -> tuple[RemoteProfileSummary, ...]: ...

    def get_profile(self, profile_id: UUID) -> RemoteProfileHead: ...

    def create_profile(
        self, profile_id: UUID, client_save_id: UUID, payload: dict
    ) -> RemoteProfileHead: ...

    def push_progression(
        self,
        profile_id: UUID,
        base_revision: int,
        client_save_id: UUID,
        payload: dict,
    ) -> Union[RemoteProfileHead, RemoteConflict]: ...


class JsonApiRemoteProfileClient:
    """Maps persistence operations to API v1 without choosing an HTTP library."""

    def __init__(self, transport, *, access_token, device_id):
        if not callable(getattr(transport, "request", None)):
            raise TypeError("transport must provide request()")
        if not isinstance(access_token, str) or not access_token:
            raise ValueError("access_token must be a non-empty string")
        if not isinstance(device_id, UUID):
            raise TypeError("device_id must be a UUID")
        self._transport = transport
        self._access_token = access_token
        self._device_id = device_id

    def get_profile(self, profile_id):
        _require_uuid(profile_id, "profile_id")
        status, document = self._request("GET", f"/v1/profiles/{profile_id}")
        if status != 200:
            raise RemoteRequestRejected("unexpected_status")
        return self._parse_head(document, profile_id)

    def list_profiles(self):
        status, document = self._request("GET", "/v1/profiles")
        if status != 200:
            raise RemoteRequestRejected("unexpected_status")
        if not isinstance(document, dict) or set(document) != {"profiles"}:
            raise RemoteProtocolError("remote profile list has an invalid shape")
        profiles = document["profiles"]
        if not isinstance(profiles, list):
            raise RemoteProtocolError("remote profile list has an invalid shape")
        return tuple(RemoteProfileSummary.from_response(item) for item in profiles)

    def create_profile(self, profile_id, client_save_id, payload):
        _require_uuid(profile_id, "profile_id")
        _require_uuid(client_save_id, "client_save_id")
        body = {
            "profile_id": str(profile_id),
            "client_save_id": str(client_save_id),
            "device_id": str(self._device_id),
            "payload": deepcopy(payload),
        }
        status, document = self._request("POST", "/v1/profiles", body)
        if status == 409:
            code = _error_code(document)
            if code == "profile_conflict":
                raise RemoteProfileCreationConflict(code)
            raise RemoteRequestRejected(code)
        if status not in {200, 201}:
            raise RemoteRequestRejected("unexpected_status")
        return self._parse_head(document, profile_id)

    def push_progression(self, profile_id, base_revision, client_save_id, payload):
        _require_uuid(profile_id, "profile_id")
        _require_uuid(client_save_id, "client_save_id")
        _positive_int(base_revision, "base_revision")
        body = {
            "base_revision": base_revision,
            "client_save_id": str(client_save_id),
            "device_id": str(self._device_id),
            "payload": deepcopy(payload),
        }
        status, document = self._request(
            "PUT", f"/v1/profiles/{profile_id}/progression", body
        )
        if status == 409:
            code = _error_code(document)
            if code == "stale_revision":
                return self._parse_conflict(document, profile_id, base_revision)
            raise RemoteRequestRejected(code)
        if status != 200:
            raise RemoteRequestRejected("unexpected_status")
        return self._parse_head(document, profile_id)

    def _request(self, method, path, body=None):
        try:
            response = self._transport.request(
                method,
                path,
                headers={"Authorization": f"Bearer {self._access_token}"},
                json=body,
            )
        except (OSError, TimeoutError) as error:
            raise RemoteUnavailable("profile service is unavailable") from error
        status = getattr(response, "status_code", None)
        if type(status) is not int:
            raise RemoteProtocolError("transport returned an invalid HTTP response")
        try:
            document = response.json()
        except (AttributeError, TypeError, ValueError) as error:
            raise RemoteProtocolError("profile service returned invalid JSON") from error
        if status == 401:
            raise RemoteAuthenticationRequired("access credential was rejected")
        if status == 404:
            raise RemoteProfileNotFound("profile is unavailable to this account")
        if status == 429 or status >= 500:
            raise RemoteUnavailable("profile service is temporarily unavailable")
        return status, document

    def _parse_head(self, document, expected_profile_id):
        head = RemoteProfileHead.from_response(document)
        if head.profile_id != expected_profile_id:
            raise RemoteProtocolError("remote profile ID did not match the request")
        return head

    def _parse_conflict(self, document, profile_id, base_revision):
        error = document.get("error") if isinstance(document, dict) else None
        if not isinstance(error, dict) or error.get("code") != "stale_revision":
            raise RemoteProtocolError("stale response has an invalid shape")
        current_head = error.get("current_head")
        expected = {"revision", "client_save_id", "payload_sha256", "created_at"}
        if not isinstance(current_head, dict) or set(current_head) != expected:
            raise RemoteProtocolError("stale response head has an invalid shape")
        _parse_timestamp(current_head["created_at"], "current_head.created_at")
        return RemoteConflict(
            profile_id=profile_id,
            base_revision=base_revision,
            current_revision=_positive_int(current_head["revision"], "current_revision"),
            client_save_id=_parse_uuid(
                current_head["client_save_id"], "current_head.client_save_id"
            ),
            payload_sha256=current_head["payload_sha256"],
        )


def _error_code(document):
    error = document.get("error") if isinstance(document, dict) else None
    code = error.get("code") if isinstance(error, dict) else None
    return code if isinstance(code, str) else "request_rejected"


def _parse_uuid(value, name):
    if not isinstance(value, str):
        raise RemoteProtocolError(f"{name} is not a canonical UUID")
    try:
        parsed = UUID(value)
    except (TypeError, ValueError, AttributeError) as error:
        raise RemoteProtocolError(f"{name} is not a canonical UUID") from error
    if str(parsed) != value:
        raise RemoteProtocolError(f"{name} is not a canonical UUID")
    return parsed


def _require_uuid(value, name):
    if not isinstance(value, UUID):
        raise TypeError(f"{name} must be a UUID")


def _positive_int(value, name):
    if type(value) is not int or value < 1:
        raise RemoteProtocolError(f"{name} must be a positive integer")
    return value


def _parse_timestamp(value, name):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise RemoteProtocolError(f"{name} must be a UTC RFC 3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise RemoteProtocolError(
            f"{name} must be a UTC RFC 3339 timestamp"
        ) from error
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise RemoteProtocolError(f"{name} must be a UTC RFC 3339 timestamp")
    return parsed


def _optional_positive_int(value, name):
    return None if value is None else _positive_int(value, name)


__all__ = [
    "JsonApiRemoteProfileClient",
    "RemoteAuthenticationRequired",
    "RemoteConflict",
    "RemoteProfileClient",
    "RemoteProfileCreationConflict",
    "RemoteProfileError",
    "RemoteProfileHead",
    "RemoteProfileNotFound",
    "RemoteProtocolError",
    "RemoteProfileSummary",
    "RemoteRequestRejected",
    "RemoteUnavailable",
]

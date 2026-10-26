"""Versioned local profile envelopes around versioned game-state payloads."""

import hashlib
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from app.persistence.save_document import (
    validate_legacy_schema8_document,
    validate_legacy_schema9_document,
    validate_legacy_schema10_document,
    validate_save_document,
)
from app.snapshot import validate_plain_value


_ENVELOPE_VERSION = 1
_ENVELOPE_KEYS = {
    "envelope_version",
    "profile_id",
    "account_id",
    "remote_revision",
    "local_sequence",
    "sync_state",
    "client_save_id",
    "saved_at",
    "payload_sha256",
    "payload",
}
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_UTC_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class SyncState(StrEnum):
    LOCAL_ONLY = "local_only"
    CLEAN = "clean"
    PENDING = "pending"
    CONFLICT = "conflict"


class ProfileEnvelopeValidationError(ValueError):
    """Raised when a profile envelope is malformed or inconsistent."""


@dataclass(frozen=True)
class ProfileEnvelope:
    envelope_version: int
    profile_id: UUID
    account_id: UUID | None
    remote_revision: int | None
    local_sequence: int
    sync_state: SyncState
    client_save_id: UUID
    saved_at: datetime
    payload_sha256: str
    payload: dict


@dataclass(frozen=True)
class ConflictSnapshot:
    profile_id: UUID
    local_client_save_id: UUID
    local_payload: dict
    local_payload_sha256: str
    base_remote_revision: int
    remote_current_revision: int
    remote_payload: dict
    remote_payload_sha256: str
    detected_at: datetime


def canonical_json_bytes(value):
    try:
        validate_plain_value(value)
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise ProfileEnvelopeValidationError(
            "value cannot be encoded as DD Canonical Payload JSON v1"
        ) from error
    return encoded


def payload_sha256(payload):
    normalized = _validated_profile_payload(payload)
    return hashlib.sha256(canonical_json_bytes(normalized)).hexdigest()


def build_profile_envelope(
    payload,
    *,
    profile_id=None,
    account_id=None,
    remote_revision=None,
    local_sequence=1,
    sync_state=SyncState.LOCAL_ONLY,
    client_save_id=None,
    saved_at=None,
):
    profile_id = uuid4() if profile_id is None else profile_id
    client_save_id = uuid4() if client_save_id is None else client_save_id
    saved_at = datetime.now(timezone.utc) if saved_at is None else saved_at
    if not isinstance(profile_id, UUID):
        raise ProfileEnvelopeValidationError("profile_id must be a UUID")
    if account_id is not None and not isinstance(account_id, UUID):
        raise ProfileEnvelopeValidationError("account_id must be a UUID or null")
    if not isinstance(client_save_id, UUID):
        raise ProfileEnvelopeValidationError("client_save_id must be a UUID")
    try:
        sync_state = SyncState(sync_state)
    except (TypeError, ValueError) as error:
        raise ProfileEnvelopeValidationError("unknown sync state") from error

    normalized_payload = _validated_profile_payload(payload)
    envelope = ProfileEnvelope(
        envelope_version=_ENVELOPE_VERSION,
        profile_id=profile_id,
        account_id=account_id,
        remote_revision=remote_revision,
        local_sequence=local_sequence,
        sync_state=sync_state,
        client_save_id=client_save_id,
        saved_at=_normalize_datetime(saved_at),
        payload_sha256=hashlib.sha256(
            canonical_json_bytes(normalized_payload)
        ).hexdigest(),
        payload=deepcopy(normalized_payload),
    )
    return validate_profile_envelope(profile_envelope_to_document(envelope))


def validate_profile_envelope(document):
    if not isinstance(document, dict) or set(document) != _ENVELOPE_KEYS:
        raise ProfileEnvelopeValidationError("profile envelope has an invalid shape")
    if type(document["envelope_version"]) is not int or document["envelope_version"] != _ENVELOPE_VERSION:
        raise ProfileEnvelopeValidationError("unsupported profile envelope version")

    profile_id = _parse_uuid(document["profile_id"], "profile_id")
    account_id = (
        None
        if document["account_id"] is None
        else _parse_uuid(document["account_id"], "account_id")
    )
    client_save_id = _parse_uuid(document["client_save_id"], "client_save_id")

    remote_revision = document["remote_revision"]
    if remote_revision is not None and (
        type(remote_revision) is not int or remote_revision < 1
    ):
        raise ProfileEnvelopeValidationError("remote_revision must be null or positive")
    local_sequence = document["local_sequence"]
    if type(local_sequence) is not int or local_sequence < 1:
        raise ProfileEnvelopeValidationError("local_sequence must be positive")

    try:
        sync_state = SyncState(document["sync_state"])
    except (TypeError, ValueError) as error:
        raise ProfileEnvelopeValidationError("unknown sync state") from error
    _validate_sync_state(sync_state, account_id, remote_revision)

    saved_at = _parse_datetime(document["saved_at"])
    payload = _validated_profile_payload(document["payload"])
    digest = document["payload_sha256"]
    if not isinstance(digest, str) or not _SHA256_PATTERN.fullmatch(digest):
        raise ProfileEnvelopeValidationError("payload_sha256 must be lowercase SHA-256 hex")
    expected_digest = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    if digest != expected_digest:
        raise ProfileEnvelopeValidationError("payload_sha256 does not match payload")

    return ProfileEnvelope(
        envelope_version=_ENVELOPE_VERSION,
        profile_id=profile_id,
        account_id=account_id,
        remote_revision=remote_revision,
        local_sequence=local_sequence,
        sync_state=sync_state,
        client_save_id=client_save_id,
        saved_at=saved_at,
        payload_sha256=digest,
        payload=deepcopy(payload),
    )


def profile_envelope_to_document(envelope):
    if not isinstance(envelope, ProfileEnvelope):
        raise TypeError("envelope must be a ProfileEnvelope")
    document = {
        "envelope_version": envelope.envelope_version,
        "profile_id": str(envelope.profile_id),
        "account_id": None if envelope.account_id is None else str(envelope.account_id),
        "remote_revision": envelope.remote_revision,
        "local_sequence": envelope.local_sequence,
        "sync_state": envelope.sync_state.value,
        "client_save_id": str(envelope.client_save_id),
        "saved_at": _format_datetime(envelope.saved_at),
        "payload_sha256": envelope.payload_sha256,
        "payload": deepcopy(envelope.payload),
    }
    validate_profile_envelope(document)
    return document


def serialize_profile_envelope(envelope):
    return canonical_json_bytes(profile_envelope_to_document(envelope))


def parse_profile_envelope(encoded):
    if not isinstance(encoded, bytes):
        raise TypeError("encoded profile envelope must be bytes")
    try:
        document = json.loads(
            encoded.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except ProfileEnvelopeValidationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise ProfileEnvelopeValidationError("profile envelope is not valid UTF-8 JSON") from error
    return validate_profile_envelope(document)


def build_conflict_snapshot(
    *,
    profile_id,
    local_client_save_id,
    local_payload,
    base_remote_revision,
    remote_current_revision,
    remote_payload,
    detected_at,
):
    if not isinstance(profile_id, UUID):
        raise ProfileEnvelopeValidationError("profile_id must be a UUID")
    if not isinstance(local_client_save_id, UUID):
        raise ProfileEnvelopeValidationError("local_client_save_id must be a UUID")
    local_payload = _validated_profile_payload(local_payload)
    remote_payload = _validated_profile_payload(remote_payload)
    snapshot = ConflictSnapshot(
        profile_id=profile_id,
        local_client_save_id=local_client_save_id,
        local_payload=deepcopy(local_payload),
        local_payload_sha256=hashlib.sha256(
            canonical_json_bytes(local_payload)
        ).hexdigest(),
        base_remote_revision=base_remote_revision,
        remote_current_revision=remote_current_revision,
        remote_payload=deepcopy(remote_payload),
        remote_payload_sha256=hashlib.sha256(
            canonical_json_bytes(remote_payload)
        ).hexdigest(),
        detected_at=_normalize_datetime(detected_at),
    )
    return validate_conflict_snapshot(conflict_snapshot_to_document(snapshot))


def validate_conflict_snapshot(document):
    expected_keys = {
        "profile_id",
        "local_client_save_id",
        "local_payload",
        "local_payload_sha256",
        "base_remote_revision",
        "remote_current_revision",
        "remote_payload",
        "remote_payload_sha256",
        "detected_at",
    }
    if not isinstance(document, dict) or set(document) != expected_keys:
        raise ProfileEnvelopeValidationError("conflict snapshot has an invalid shape")

    profile_id = _parse_uuid(document["profile_id"], "profile_id")
    local_client_save_id = _parse_uuid(
        document["local_client_save_id"], "local_client_save_id"
    )
    base_revision = document["base_remote_revision"]
    current_revision = document["remote_current_revision"]
    if type(base_revision) is not int or base_revision < 1:
        raise ProfileEnvelopeValidationError("base_remote_revision must be positive")
    if type(current_revision) is not int or current_revision <= base_revision:
        raise ProfileEnvelopeValidationError(
            "remote_current_revision must be newer than the base"
        )

    local_payload = _validated_profile_payload(document["local_payload"])
    remote_payload = _validated_profile_payload(document["remote_payload"])
    local_digest = _validate_digest(document["local_payload_sha256"])
    remote_digest = _validate_digest(document["remote_payload_sha256"])
    if local_digest != hashlib.sha256(canonical_json_bytes(local_payload)).hexdigest():
        raise ProfileEnvelopeValidationError("local conflict digest does not match payload")
    if remote_digest != hashlib.sha256(canonical_json_bytes(remote_payload)).hexdigest():
        raise ProfileEnvelopeValidationError("remote conflict digest does not match payload")

    return ConflictSnapshot(
        profile_id=profile_id,
        local_client_save_id=local_client_save_id,
        local_payload=deepcopy(local_payload),
        local_payload_sha256=local_digest,
        base_remote_revision=base_revision,
        remote_current_revision=current_revision,
        remote_payload=deepcopy(remote_payload),
        remote_payload_sha256=remote_digest,
        detected_at=_parse_datetime(document["detected_at"]),
    )


def conflict_snapshot_to_document(snapshot):
    if not isinstance(snapshot, ConflictSnapshot):
        raise TypeError("snapshot must be a ConflictSnapshot")
    document = {
        "profile_id": str(snapshot.profile_id),
        "local_client_save_id": str(snapshot.local_client_save_id),
        "local_payload": deepcopy(snapshot.local_payload),
        "local_payload_sha256": snapshot.local_payload_sha256,
        "base_remote_revision": snapshot.base_remote_revision,
        "remote_current_revision": snapshot.remote_current_revision,
        "remote_payload": deepcopy(snapshot.remote_payload),
        "remote_payload_sha256": snapshot.remote_payload_sha256,
        "detected_at": _format_datetime(snapshot.detected_at),
    }
    validate_conflict_snapshot(document)
    return document


def serialize_conflict_snapshot(snapshot):
    return canonical_json_bytes(conflict_snapshot_to_document(snapshot))


def parse_conflict_snapshot(encoded):
    if not isinstance(encoded, bytes):
        raise TypeError("encoded conflict snapshot must be bytes")
    try:
        document = json.loads(
            encoded.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except ProfileEnvelopeValidationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise ProfileEnvelopeValidationError("conflict snapshot is not valid UTF-8 JSON") from error
    return validate_conflict_snapshot(document)


def _validated_profile_payload(payload):
    if not isinstance(payload, dict) or type(payload.get("schema_version")) is not int:
        raise ProfileEnvelopeValidationError(
            "payload must be a schema-8, schema-9, schema-10, or schema-11 object"
        )
    try:
        if payload["schema_version"] == 8 and "party" not in payload:
            return validate_legacy_schema8_document(payload)
        if payload["schema_version"] == 9:
            return validate_legacy_schema9_document(payload)
        if payload["schema_version"] == 10:
            return validate_legacy_schema10_document(payload)
        normalized = validate_save_document(payload)
    except (TypeError, ValueError) as error:
        raise ProfileEnvelopeValidationError("payload is not a valid game-state document") from error
    if normalized != payload:
        raise ProfileEnvelopeValidationError(
            "profile payload must already be normalized for its schema"
        )
    return deepcopy(normalized)


def _validate_sync_state(sync_state, account_id, remote_revision):
    valid = {
        SyncState.LOCAL_ONLY: account_id is None and remote_revision is None,
        SyncState.CLEAN: account_id is not None and remote_revision is not None,
        SyncState.PENDING: account_id is not None,
        SyncState.CONFLICT: account_id is not None and remote_revision is not None,
    }
    if not valid[sync_state]:
        raise ProfileEnvelopeValidationError("sync state disagrees with account/revision fields")


def _parse_uuid(value, field):
    if not isinstance(value, str):
        raise ProfileEnvelopeValidationError(f"{field} must be a canonical UUID")
    try:
        parsed = UUID(value)
    except (AttributeError, TypeError, ValueError) as error:
        raise ProfileEnvelopeValidationError(f"{field} must be a canonical UUID") from error
    if str(parsed) != value:
        raise ProfileEnvelopeValidationError(f"{field} must be a canonical UUID")
    return parsed


def _normalize_datetime(value):
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ProfileEnvelopeValidationError("saved_at must be a timezone-aware UTC datetime")
    try:
        return value.astimezone(timezone.utc)
    except (OverflowError, ValueError) as error:
        raise ProfileEnvelopeValidationError("saved_at is outside the supported range") from error


def _format_datetime(value):
    return _normalize_datetime(value).strftime(_UTC_TIMESTAMP_FORMAT)


def _parse_datetime(value):
    if not isinstance(value, str):
        raise ProfileEnvelopeValidationError("saved_at must be a canonical UTC timestamp")
    try:
        parsed = datetime.strptime(value, _UTC_TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise ProfileEnvelopeValidationError("saved_at must be a canonical UTC timestamp") from error
    if _format_datetime(parsed) != value:
        raise ProfileEnvelopeValidationError("saved_at must be a canonical UTC timestamp")
    return parsed


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProfileEnvelopeValidationError("document contains duplicate keys")
        result[key] = value
    return result


def _validate_digest(value):
    if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value):
        raise ProfileEnvelopeValidationError("payload digest must be lowercase SHA-256 hex")
    return value


__all__ = [
    "ProfileEnvelope",
    "ProfileEnvelopeValidationError",
    "ConflictSnapshot",
    "SyncState",
    "build_conflict_snapshot",
    "build_profile_envelope",
    "canonical_json_bytes",
    "conflict_snapshot_to_document",
    "parse_conflict_snapshot",
    "parse_profile_envelope",
    "payload_sha256",
    "profile_envelope_to_document",
    "serialize_conflict_snapshot",
    "serialize_profile_envelope",
    "validate_conflict_snapshot",
    "validate_profile_envelope",
]

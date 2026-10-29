import hashlib
import json

from app.persistence.save_document import (
    DISK_SCHEMA_VERSION,
    SaveStateValidationError,
    validate_save_document,
)


class InvalidPayload(ValueError):
    pass


def normalize_and_digest(payload):
    if not isinstance(payload, dict):
        raise InvalidPayload("payload must be an object")
    version = payload.get("schema_version")
    if isinstance(version, bool) or version != DISK_SCHEMA_VERSION:
        raise InvalidPayload(
            f"remote progression requires game-state schema {DISK_SCHEMA_VERSION}"
        )
    try:
        normalized = validate_save_document(payload)
        encoded = json.dumps(
            normalized,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (SaveStateValidationError, TypeError, ValueError, UnicodeError) as error:
        raise InvalidPayload(
            f"progression payload failed schema-{DISK_SCHEMA_VERSION} validation"
        ) from error
    if normalized.get("schema_version") != DISK_SCHEMA_VERSION:
        raise InvalidPayload(
            f"remote progression requires game-state schema {DISK_SCHEMA_VERSION}"
        )
    return normalized, hashlib.sha256(encoded).hexdigest()

import copy
import hashlib
from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.content.catalog import get_drifter_spec_by_choice
from app.game.game_state import GameState
from app.persistence.save_document import build_save_document
from app.persistence.envelope import (
    ProfileEnvelopeValidationError,
    SyncState,
    build_profile_envelope,
    canonical_json_bytes,
    parse_profile_envelope,
    profile_envelope_to_document,
    serialize_profile_envelope,
    validate_profile_envelope,
)
from app.player.player_state import PlayerState


PROFILE_ID = UUID("00000000-0000-4000-8000-000000000001")
SAVE_ID = UUID("00000000-0000-4000-8000-000000000002")
ACCOUNT_ID = UUID("00000000-0000-4000-8000-000000000004")
SAVED_AT = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)


def _payload():
    character = get_drifter_spec_by_choice("1").create_character()
    return build_save_document(GameState(PlayerState(character)))


def _legacy_schema9_payload():
    payload = copy.deepcopy(_payload())
    payload["schema_version"] = 9
    payload["player"].pop("signature_weapon")
    payload["overworld"].pop("active_route_id")
    for field in (
        "floor_one_cleared",
        "floor_one_runs_started_after_clear",
        "outing_xp_multiplier_percent",
        "crafting_experience",
    ):
        payload["party"].pop(field)
    return payload


def _envelope(**changes):
    options = {
        "profile_id": PROFILE_ID,
        "client_save_id": SAVE_ID,
        "saved_at": SAVED_AT,
    }
    options.update(changes)
    return build_profile_envelope(_payload(), **options)


def test_canonical_json_bytes_pin_unicode_float_and_key_ordering():
    value = {"z": 2, "note": "é", "a": 1.5}

    assert canonical_json_bytes(value) == b'{"a":1.5,"note":"\xc3\xa9","z":2}'


def test_profile_envelope_round_trip_is_canonical_and_keeps_payload_digest():
    envelope = _envelope()

    encoded = serialize_profile_envelope(envelope)
    restored = parse_profile_envelope(encoded)

    assert restored == envelope
    assert encoded == serialize_profile_envelope(restored)
    assert not encoded.startswith(b"\xef\xbb\xbf")
    assert not encoded.endswith(b"\n")
    assert envelope.payload_sha256 == (
        "ed092c344cadfac799e74080073832d515f2c7ded558fddaa2d4024b305bdf2e"
    )


@pytest.mark.parametrize(
    "mutate",
    (
        lambda document: document.update(extra=True),
        lambda document: document.pop("saved_at"),
        lambda document: document.update(profile_id="NOT-A-UUID"),
        lambda document: document.update(
            profile_id="00000000-0000-4000-8000-00000000000A"
        ),
        lambda document: document.update(payload_sha256="0" * 64),
        lambda document: document.update(local_sequence=True),
        lambda document: document.update(payload={"schema_version": 7}),
    ),
)
def test_profile_envelope_rejects_noncanonical_or_invalid_documents(mutate):
    document = profile_envelope_to_document(_envelope())
    mutate(document)

    with pytest.raises(ProfileEnvelopeValidationError):
        validate_profile_envelope(document)


def test_cloud_sync_states_require_account_and_revision_consistency():
    envelope = _envelope()
    document = profile_envelope_to_document(envelope)
    document["sync_state"] = SyncState.CLEAN.value

    with pytest.raises(ProfileEnvelopeValidationError):
        validate_profile_envelope(document)

    cloud_envelope = _envelope(
        account_id=ACCOUNT_ID,
        remote_revision=3,
        sync_state=SyncState.CLEAN,
    )
    assert cloud_envelope.account_id == ACCOUNT_ID
    assert cloud_envelope.remote_revision == 3


def test_profile_envelope_builder_rejects_string_ids_instead_of_returning_untyped_ids():
    with pytest.raises(ProfileEnvelopeValidationError):
        _envelope(profile_id=str(PROFILE_ID))


def test_profile_envelope_parser_rejects_duplicate_json_keys():
    encoded = serialize_profile_envelope(_envelope())
    duplicate = encoded.replace(b'"envelope_version":1', b'"envelope_version":1,"envelope_version":1')

    with pytest.raises(ProfileEnvelopeValidationError):
        parse_profile_envelope(duplicate)


def test_profile_envelope_validation_does_not_mutate_caller_payload():
    payload = _payload()
    original = copy.deepcopy(payload)
    envelope = build_profile_envelope(
        payload,
        profile_id=PROFILE_ID,
        client_save_id=SAVE_ID,
        saved_at=SAVED_AT,
    )

    envelope.payload["metadata"]["added"] = "after-build"

    assert payload == original


def test_legacy_schema8_envelope_keeps_original_payload_and_digest():
    legacy_payload = copy.deepcopy(_payload())
    legacy_payload["schema_version"] = 8
    legacy_payload.pop("party")
    legacy_payload["player"].pop("signature_weapon")
    legacy_payload["overworld"].pop("active_route_id")
    envelope_document = profile_envelope_to_document(_envelope())
    legacy_digest = hashlib.sha256(canonical_json_bytes(legacy_payload)).hexdigest()
    envelope_document["payload"] = legacy_payload
    envelope_document["payload_sha256"] = legacy_digest

    restored = validate_profile_envelope(envelope_document)

    assert restored.payload == legacy_payload
    assert restored.payload_sha256 == legacy_digest


def test_legacy_schema8_payload_digest_is_checked_before_any_migration():
    legacy_payload = copy.deepcopy(_payload())
    legacy_payload["schema_version"] = 8
    legacy_payload.pop("party")
    legacy_payload["player"].pop("signature_weapon")
    legacy_payload["overworld"].pop("active_route_id")
    envelope_document = profile_envelope_to_document(_envelope())
    envelope_document["payload"] = legacy_payload
    envelope_document["payload_sha256"] = "0" * 64

    with pytest.raises(ProfileEnvelopeValidationError):
        validate_profile_envelope(envelope_document)


def test_legacy_schema9_envelope_keeps_original_payload_and_digest():
    legacy_payload = _legacy_schema9_payload()
    envelope_document = profile_envelope_to_document(_envelope())
    legacy_digest = hashlib.sha256(canonical_json_bytes(legacy_payload)).hexdigest()
    envelope_document["payload"] = legacy_payload
    envelope_document["payload_sha256"] = legacy_digest

    restored = validate_profile_envelope(envelope_document)

    assert restored.payload == legacy_payload
    assert restored.payload_sha256 == legacy_digest

import copy
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
        "41de49b00b15bc7069588d40b77e3ca66dccd0f0ff4f3be50b2ce4aa3f0bd2c1"
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

from uuid import UUID

import pytest

from app.content.catalog import get_drifter_spec_by_choice
from app.game.game_state import GameState
from app.persistence.envelope import payload_sha256
from app.persistence.remote_client import (
    JsonApiRemoteProfileClient,
    RemoteProfileCreationConflict,
    RemoteProtocolError,
)
from app.persistence.save_document import build_save_document
from app.player.player_state import PlayerState


PROFILE_ID = UUID("00000000-0000-4000-8000-000000000001")
SAVE_ID = UUID("00000000-0000-4000-8000-000000000002")
DEVICE_ID = UUID("00000000-0000-4000-8000-000000000003")
ACCOUNT_ID = UUID("00000000-0000-4000-8000-000000000004")


class FakeResponse:
    def __init__(self, status_code, document):
        self.status_code = status_code
        self._document = document

    def json(self):
        return self._document


class RecordingTransport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def request(self, method, path, *, headers, json):
        self.calls.append((method, path, headers, json))
        return self.response


def _payload(gold=0):
    character = get_drifter_spec_by_choice("1").create_character()
    return build_save_document(GameState(PlayerState(character, gold=gold)))


def _legacy_schema8_payload(gold=0):
    payload = _payload(gold)
    payload["schema_version"] = 8
    payload.pop("party")
    return payload


def _profile_response(payload):
    return {
        "profile_id": str(PROFILE_ID),
        "account_id": str(ACCOUNT_ID),
        "created_revision": 1,
        "current_revision": 1,
        "head": {
            "revision": 1,
            "base_revision": None,
            "client_save_id": str(SAVE_ID),
            "device_id": str(DEVICE_ID),
            "payload_sha256": payload_sha256(payload),
            "created_at": "2026-10-13T12:00:00Z",
            "payload": payload,
        },
    }


def test_profile_claim_uses_the_existing_identity_and_full_validated_payload():
    payload = _payload(gold=17)
    transport = RecordingTransport(FakeResponse(201, _profile_response(payload)))
    client = JsonApiRemoteProfileClient(
        transport,
        access_token="opaque-access-token",
        device_id=DEVICE_ID,
    )

    head = client.create_profile(PROFILE_ID, SAVE_ID, payload)

    assert head.profile_id == PROFILE_ID
    assert head.account_id == ACCOUNT_ID
    assert head.current_revision == 1
    assert head.payload == payload
    assert transport.calls == [
        (
            "POST",
            "/v1/profiles",
            {"Authorization": "Bearer opaque-access-token"},
            {
                "profile_id": str(PROFILE_ID),
                "client_save_id": str(SAVE_ID),
                "device_id": str(DEVICE_ID),
                "payload": payload,
            },
        )
    ]


def test_remote_schema8_head_is_verified_without_rewriting_its_payload():
    payload = _legacy_schema8_payload(gold=19)
    client = JsonApiRemoteProfileClient(
        RecordingTransport(FakeResponse(200, _profile_response(payload))),
        access_token="opaque-access-token",
        device_id=DEVICE_ID,
    )

    head = client.get_profile(PROFILE_ID)

    assert head.payload == payload
    assert head.payload["schema_version"] == 8
    assert head.payload_sha256 == payload_sha256(payload)


def test_progression_stale_revision_is_returned_as_a_conflict_value():
    payload = _payload(gold=21)
    current_save_id = UUID("00000000-0000-4000-8000-000000000005")
    response = {
        "error": {
            "code": "stale_revision",
            "message": "The profile changed on another device.",
            "current_head": {
                "revision": 2,
                "client_save_id": str(current_save_id),
                "payload_sha256": payload_sha256(payload),
                "created_at": "2026-10-13T12:01:00Z",
            },
        }
    }
    transport = RecordingTransport(FakeResponse(409, response))
    client = JsonApiRemoteProfileClient(
        transport,
        access_token="opaque-access-token",
        device_id=DEVICE_ID,
    )

    result = client.push_progression(PROFILE_ID, 1, SAVE_ID, payload)

    assert result.current_revision == 2
    assert result.base_revision == 1
    assert transport.calls[0][0:2] == (
        "PUT",
        f"/v1/profiles/{PROFILE_ID}/progression",
    )
    assert transport.calls[0][3] == {
        "base_revision": 1,
        "client_save_id": str(SAVE_ID),
        "device_id": str(DEVICE_ID),
        "payload": payload,
    }


def test_invalid_remote_payload_digest_is_rejected_before_it_can_be_installed():
    response = _profile_response(_payload())
    response["head"]["payload_sha256"] = "0" * 64
    client = JsonApiRemoteProfileClient(
        RecordingTransport(FakeResponse(200, response)),
        access_token="opaque-access-token",
        device_id=DEVICE_ID,
    )

    try:
        client.get_profile(PROFILE_ID)
    except ValueError as error:
        assert "digest" in str(error)
    else:
        raise AssertionError("unverified remote profile payload was accepted")


def test_create_conflict_uses_the_service_contract_code():
    client = JsonApiRemoteProfileClient(
        RecordingTransport(
            FakeResponse(
                409,
                {"error": {"code": "profile_conflict", "message": "Conflict."}},
            )
        ),
        access_token="opaque-access-token",
        device_id=DEVICE_ID,
    )

    with pytest.raises(RemoteProfileCreationConflict):
        client.create_profile(PROFILE_ID, SAVE_ID, _payload())


@pytest.mark.parametrize(
    ("field", "value"),
    (("device_id", "not-a-uuid"), ("created_at", "2026-10-13T12:00:00")),
)
def test_remote_revision_metadata_must_match_the_wire_contract(field, value):
    response = _profile_response(_payload())
    response["head"][field] = value
    client = JsonApiRemoteProfileClient(
        RecordingTransport(FakeResponse(200, response)),
        access_token="opaque-access-token",
        device_id=DEVICE_ID,
    )

    with pytest.raises(RemoteProtocolError):
        client.get_profile(PROFILE_ID)


def test_profile_list_is_parsed_from_the_authoritative_account_scoped_endpoint():
    transport = RecordingTransport(
        FakeResponse(
            200,
            {
                "profiles": [
                    {
                        "profile_id": str(PROFILE_ID),
                        "current_revision": 4,
                        "created_at": "2026-10-13T12:00:00.000000Z",
                        "updated_at": "2026-10-13T12:05:00.000000Z",
                    }
                ]
            },
        )
    )
    client = JsonApiRemoteProfileClient(
        transport,
        access_token="opaque-access-token",
        device_id=DEVICE_ID,
    )

    profiles = client.list_profiles()

    assert len(profiles) == 1
    assert profiles[0].profile_id == PROFILE_ID
    assert profiles[0].current_revision == 4
    assert profiles[0].created_at.isoformat() == "2026-10-13T12:00:00+00:00"
    assert transport.calls[0][0:2] == ("GET", "/v1/profiles")

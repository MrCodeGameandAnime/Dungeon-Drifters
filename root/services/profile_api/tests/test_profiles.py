from copy import deepcopy
from uuid import uuid4

from sqlalchemy import func, select

from profile_api.models import ProfileRevision

from conftest import authorization, create_account, make_payload


def _create_profile(client, token, payload, *, profile_id=None, save_id=None):
    profile_id = uuid4() if profile_id is None else profile_id
    save_id = uuid4() if save_id is None else save_id
    response = client.post(
        "/v1/profiles",
        headers=authorization(token),
        json={
            "profile_id": str(profile_id),
            "client_save_id": str(save_id),
            "device_id": "00000000-0000-4000-8000-000000000003",
            "payload": payload,
        },
    )
    return response, profile_id, save_id


def test_profile_claim_listing_and_head_read_are_account_scoped(service, valid_payload):
    client, _ = service
    first_account = create_account(client)
    second_account = create_account(client)
    created, profile_id, _ = _create_profile(
        client,
        first_account["access_token"],
        valid_payload,
    )

    assert created.status_code == 201, created.text
    body = created.json()
    assert body["profile_id"] == str(profile_id)
    assert body["account_id"] == first_account["account_id"]
    assert body["created_revision"] == body["current_revision"] == 1
    assert body["head"]["base_revision"] is None
    assert body["head"]["payload"] == valid_payload

    listed = client.get(
        "/v1/profiles",
        headers=authorization(first_account["access_token"]),
    )
    assert [row["profile_id"] for row in listed.json()["profiles"]] == [
        str(profile_id)
    ]
    assert "payload" not in listed.text

    read = client.get(
        f"/v1/profiles/{profile_id}",
        headers=authorization(first_account["access_token"]),
    )
    hidden = client.get(
        f"/v1/profiles/{profile_id}",
        headers=authorization(second_account["access_token"]),
    )
    assert read.status_code == 200
    assert read.json()["head"]["payload"] == valid_payload
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "not_found"


def test_profile_claim_retry_is_idempotent_even_after_head_advances(
    service, valid_payload
):
    client, session_factory = service
    account = create_account(client)
    created, profile_id, initial_save_id = _create_profile(
        client,
        account["access_token"],
        valid_payload,
    )
    changed = deepcopy(valid_payload)
    changed["metadata"]["claim_retry"] = "later"
    advanced = client.put(
        f"/v1/profiles/{profile_id}/progression",
        headers=authorization(account["access_token"]),
        json={
            "base_revision": 1,
            "client_save_id": str(uuid4()),
            "device_id": "00000000-0000-4000-8000-000000000003",
            "payload": changed,
        },
    )
    retry, _, _ = _create_profile(
        client,
        account["access_token"],
        valid_payload,
        profile_id=profile_id,
        save_id=initial_save_id,
    )

    assert created.status_code == 201
    assert advanced.status_code == 200
    assert retry.status_code == 200
    assert retry.json()["created_revision"] == 1
    assert retry.json()["current_revision"] == 2
    assert retry.json()["head"]["revision"] == 2
    with session_factory() as session:
        assert session.scalar(
            select(func.count()).select_from(ProfileRevision)
        ) == 2


def test_profile_claim_cannot_overwrite_existing_or_other_account_profile(
    service, valid_payload
):
    client, session_factory = service
    owner = create_account(client)
    other = create_account(client)
    created, profile_id, _ = _create_profile(
        client,
        owner["access_token"],
        valid_payload,
    )
    different = make_payload(gold=7)
    same_account_conflict, _, _ = _create_profile(
        client,
        owner["access_token"],
        different,
        profile_id=profile_id,
    )
    hidden, _, _ = _create_profile(
        client,
        other["access_token"],
        valid_payload,
        profile_id=profile_id,
    )

    assert created.status_code == 201
    assert same_account_conflict.status_code == 409
    assert same_account_conflict.json()["error"]["code"] == "profile_conflict"
    assert hidden.status_code == 404
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(ProfileRevision)) == 1


def test_progression_is_idempotent_and_stale_writes_preserve_head(
    service, valid_payload
):
    client, session_factory = service
    account = create_account(client)
    _, profile_id, _ = _create_profile(
        client,
        account["access_token"],
        valid_payload,
    )
    first_save_id = uuid4()
    first_update_payload = deepcopy(valid_payload)
    first_update_payload["metadata"]["progression"] = "revision-two"
    request = {
        "base_revision": 1,
        "client_save_id": str(first_save_id),
        "device_id": "00000000-0000-4000-8000-000000000003",
        "payload": first_update_payload,
    }
    headers = authorization(account["access_token"])
    accepted = client.put(
        f"/v1/profiles/{profile_id}/progression",
        headers=headers,
        json=request,
    )
    replay = client.put(
        f"/v1/profiles/{profile_id}/progression",
        headers=headers,
        json=request,
    )

    stale_payload = deepcopy(valid_payload)
    stale_payload["metadata"]["progression"] = "stale-device"
    stale = client.put(
        f"/v1/profiles/{profile_id}/progression",
        headers=headers,
        json={
            **request,
            "client_save_id": str(uuid4()),
            "payload": stale_payload,
        },
    )
    reused_key = client.put(
        f"/v1/profiles/{profile_id}/progression",
        headers=headers,
        json={**request, "payload": stale_payload},
    )

    assert accepted.status_code == 200
    assert accepted.json()["accepted_revision"] == 2
    assert replay.status_code == 200
    assert replay.json()["accepted_revision"] == 2
    assert replay.json()["current_revision"] == 2
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "stale_revision"
    assert stale.json()["error"]["current_head"]["revision"] == 2
    assert "payload" not in stale.json()["error"]["current_head"]
    assert reused_key.status_code == 409
    assert reused_key.json()["error"]["code"] == "idempotency_key_reuse"
    head = client.get(f"/v1/profiles/{profile_id}", headers=headers)
    assert head.json()["current_revision"] == 2
    assert head.json()["head"]["payload"] == first_update_payload
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(ProfileRevision)) == 2


def test_invalid_payload_and_client_owned_fields_never_create_revision(
    service, valid_payload
):
    client, session_factory = service
    account = create_account(client)
    _, profile_id, _ = _create_profile(
        client,
        account["access_token"],
        valid_payload,
    )
    headers = authorization(account["access_token"])
    invalid_payload = deepcopy(valid_payload)
    invalid_payload["schema_version"] = 7
    invalid = client.put(
        f"/v1/profiles/{profile_id}/progression",
        headers=headers,
        json={
            "base_revision": 1,
            "client_save_id": str(uuid4()),
            "device_id": "00000000-0000-4000-8000-000000000003",
            "payload": invalid_payload,
        },
    )
    bool_revision = client.put(
        f"/v1/profiles/{profile_id}/progression",
        headers=headers,
        json={
            "base_revision": True,
            "client_save_id": str(uuid4()),
            "device_id": "00000000-0000-4000-8000-000000000003",
            "payload": valid_payload,
        },
    )
    forged_owner = client.post(
        "/v1/profiles",
        headers=headers,
        json={
            "profile_id": str(uuid4()),
            "client_save_id": str(uuid4()),
            "device_id": "00000000-0000-4000-8000-000000000003",
            "account_id": account["account_id"],
            "payload": valid_payload,
        },
    )

    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "invalid_payload"
    assert bool_revision.status_code == 422
    assert forged_owner.status_code == 422
    assert client.post(
        "/v1/entitlements",
        headers=headers,
        json={"product_key": "anything"},
    ).status_code == 405
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(ProfileRevision)) == 1


def test_unowned_and_missing_profiles_have_the_same_not_found_response(service):
    client, _ = service
    account = create_account(client)
    response = client.get(
        f"/v1/profiles/{uuid4()}",
        headers=authorization(account["access_token"]),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"

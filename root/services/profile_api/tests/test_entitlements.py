from datetime import datetime, timezone
from uuid import UUID, uuid4

from profile_api.models import Entitlement

from conftest import authorization, create_account, make_payload


def test_entitlements_are_account_scoped_and_separate_from_progression(service):
    client, session_factory = service
    account_a = create_account(client)
    account_b = create_account(client)
    granted_at = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
    expires_at = datetime(2027, 10, 13, 12, 0, tzinfo=timezone.utc)
    revoked_at = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)

    with session_factory() as session:
        session.add_all(
            (
                Entitlement(
                    id=uuid4(),
                    account_id=UUID(account_a["account_id"]),
                    product_key="founders.pack",
                    source_provider="steam",
                    status="active",
                    granted_at=granted_at,
                    expires_at=expires_at,
                    revoked_at=None,
                    metadata_json={"edition": "founder"},
                ),
                Entitlement(
                    id=uuid4(),
                    account_id=UUID(account_a["account_id"]),
                    product_key="platform.currency.psn_shards",
                    source_provider="playstation",
                    status="active",
                    granted_at=granted_at,
                    expires_at=None,
                    revoked_at=None,
                    metadata_json={
                        "kind": "restricted_currency_balance",
                        "currency_key": "psn_shards",
                        "units": 75,
                    },
                ),
                Entitlement(
                    id=uuid4(),
                    account_id=UUID(account_b["account_id"]),
                    product_key="other.account.product",
                    source_provider="dd",
                    status="revoked",
                    granted_at=granted_at,
                    expires_at=None,
                    revoked_at=revoked_at,
                    metadata_json={},
                ),
            )
        )
        session.commit()

    headers_a = authorization(account_a["access_token"])
    headers_b = authorization(account_b["access_token"])
    entitlements_a = client.get("/v1/entitlements", headers=headers_a)
    entitlements_b = client.get("/v1/entitlements", headers=headers_b)

    assert entitlements_a.status_code == 200
    records_a = entitlements_a.json()["entitlements"]
    assert {record["product_key"] for record in records_a} == {
        "founders.pack",
        "platform.currency.psn_shards",
    }
    founder_entitlement = next(
        record for record in records_a if record["product_key"] == "founders.pack"
    )
    assert founder_entitlement["status"] == "active"
    assert founder_entitlement["expires_at"] == "2027-10-13T12:00:00.000000Z"
    assert founder_entitlement["revoked_at"] is None
    currency = next(
        record
        for record in records_a
        if record["product_key"] == "platform.currency.psn_shards"
    )
    assert currency["source_provider"] == "playstation"
    assert currency["metadata"] == {
        "kind": "restricted_currency_balance",
        "currency_key": "psn_shards",
        "units": 75,
    }
    assert currency["expires_at"] is None
    assert currency["revoked_at"] is None
    assert entitlements_b.status_code == 200
    assert [
        record["product_key"] for record in entitlements_b.json()["entitlements"]
    ] == ["other.account.product"]
    revoked = entitlements_b.json()["entitlements"][0]
    assert revoked["status"] == "revoked"
    assert revoked["revoked_at"].endswith("Z")

    payload = make_payload(gold=23)
    created = client.post(
        "/v1/profiles",
        headers=headers_a,
        json={
            "profile_id": str(uuid4()),
            "client_save_id": str(uuid4()),
            "device_id": str(uuid4()),
            "payload": payload,
        },
    )
    assert created.status_code == 201
    assert created.json()["head"]["payload"]["player"]["gold"] == 23

    forged_payload = dict(payload)
    forged_payload["entitlements"] = [{"product_key": "self-granted"}]
    forged = client.post(
        "/v1/profiles",
        headers=headers_a,
        json={
            "profile_id": str(uuid4()),
            "client_save_id": str(uuid4()),
            "device_id": str(uuid4()),
            "payload": forged_payload,
        },
    )
    assert forged.status_code == 422
    assert len(client.get("/v1/entitlements", headers=headers_a).json()["entitlements"]) == 2

    for method in ("post", "put", "patch", "delete"):
        response = getattr(client, method)("/v1/entitlements", headers=headers_a)
        assert response.status_code == 405

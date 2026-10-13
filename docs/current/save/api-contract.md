# Dungeon Drifters Profile API v1 Contract

**Status:** Normative wire contract for SAVE-ARCH. It preserves the approved DD-owned account/profile service and nested schema-8 payload; it does not select Firebase or another identity/storage vendor.

**Related specification:** [save-spec.md](save-spec.md)
**Implementation plan:** [save-plan.md](save-plan.md)

## Common Rules

- Base path is `/v1`. Game schema, envelope schema, and API version are independent.
- Request and response bodies use UTF-8 `application/json`. Request objects reject unknown fields.
- UUIDs are lowercase, hyphenated canonical strings. Integer fields reject JSON booleans.
- Timestamps are UTC RFC 3339 strings ending in `Z`; clients treat server timestamps as informational.
- The API accepts the full schema-8 game-state payload as a JSON object in `payload`; it never accepts a profile envelope as the progression payload. Schema-7 migration is a local-client responsibility.
- The server applies the canonical payload-byte/digest rules in `save-spec.md` after validating the payload. A client-supplied digest is never authoritative.
- Protected endpoints require `Authorization: Bearer <access_token>`. Access and refresh tokens are opaque, cryptographically random secrets with at least 256 bits of entropy. Secrets are never placed in URLs or logs. Hosted traffic requires HTTPS.
- Except for health, anonymous-account creation, and session refresh, endpoints require an access token.
- Authentication, validation, and service errors use the JSON error shape defined below. Responses never expose token hashes, provider proofs, SQL details, or stack traces.

## Tokens and Sessions

`POST /v1/accounts/anonymous` creates a canonical DD account and a session. It accepts:

```json
{
  "device_id": "00000000-0000-4000-8000-000000000003"
}
```

Success is `201 Created`:

```json
{
  "account_id": "00000000-0000-4000-8000-000000000004",
  "access_token": "opaque-secret",
  "access_expires_at": "2026-10-12T12:15:00Z",
  "refresh_token": "opaque-secret",
  "refresh_expires_at": "2026-11-11T12:00:00Z"
}
```

Expiration instants are server-generated and authoritative; their durations are service configuration, not client assumptions. The initial refresh token is returned only on account creation. In v1, refresh tokens remain stable until expiry or revocation; a successful refresh issues a fresh short-lived access token and does not rotate the refresh token. The service stores hashes only. The client must retain credentials in its separate host `CredentialStore`; local game saves do not depend on them.

`POST /v1/sessions/refresh` is unauthenticated at the access-token layer and accepts the refresh token in its JSON body:

```json
{ "refresh_token": "opaque-secret" }
```

Success is `200 OK`:

```json
{
  "access_token": "new-opaque-secret",
  "access_expires_at": "2026-10-12T12:30:00Z"
}
```

An invalid, expired, or revoked refresh token returns `401`. Refresh does not create a new account or change profile state.

`DELETE /v1/sessions/current` revokes the authenticated session, including its refresh credential, and returns `204 No Content`. Other sessions for the account are unaffected.

## Health

`GET /v1/health` is unauthenticated and returns `200 OK` when the service can serve requests:

```json
{ "status": "ok", "api_version": "v1" }
```

It does not return database credentials, deployment details, or internal diagnostics. A database-dependent readiness check may report unavailable with a non-2xx response without exposing connection details.

## Profiles and Revisions

### List Profiles

`GET /v1/profiles` returns only profiles owned by the authenticated account, ordered by `created_at` then canonical `profile_id`:

```json
{
  "profiles": [
    {
      "profile_id": "00000000-0000-4000-8000-000000000001",
      "current_revision": 2,
      "created_at": "2026-10-12T12:00:00Z",
      "updated_at": "2026-10-12T12:05:00Z"
    }
  ]
}
```

The list does not include progression payloads.

### Create or Claim a Profile

Authenticated `POST /v1/profiles` accepts a locally generated profile ID and the initial complete schema-8 payload:

```json
{
  "profile_id": "00000000-0000-4000-8000-000000000001",
  "client_save_id": "00000000-0000-4000-8000-000000000002",
  "device_id": "00000000-0000-4000-8000-000000000003",
  "payload": { "schema_version": 8 }
}
```

The abbreviated payload above is illustrative, not a valid game save. The server validates it before writing.

If the profile ID is unowned, the server atomically assigns it to the authenticated account and creates revision 1 (`base_revision: null`). This is also the local-guest claim operation; profile identity does not change. A retry with the same profile ID, save ID, and payload digest does not duplicate creation; it returns the current profile head and `created_revision: 1`, even if later revisions now exist. An existing profile owned by another account is reported as `404` without disclosing its owner. A same-account profile with a different initial save is `409`; use the progression endpoint instead.

First success is `201 Created`; an idempotent retry is `200 OK`. Both return the canonical profile head:

```json
{
  "profile_id": "00000000-0000-4000-8000-000000000001",
  "account_id": "00000000-0000-4000-8000-000000000004",
  "created_revision": 1,
  "current_revision": 1,
  "head": {
    "revision": 1,
    "base_revision": null,
    "client_save_id": "00000000-0000-4000-8000-000000000002",
    "device_id": "00000000-0000-4000-8000-000000000003",
    "payload_sha256": "<64 lowercase hexadecimal characters>",
    "created_at": "2026-10-12T12:00:00Z",
    "payload": { "schema_version": 8 }
  }
}
```

### Read a Profile

`GET /v1/profiles/{profile_id}` returns the same profile/head shape as profile creation, including the complete current payload. Unknown and unowned IDs both return `404`.

### Submit Progression

`PUT /v1/profiles/{profile_id}/progression` accepts:

```json
{
  "base_revision": 1,
  "client_save_id": "00000000-0000-4000-8000-000000000005",
  "device_id": "00000000-0000-4000-8000-000000000003",
  "payload": { "schema_version": 8 }
}
```

`base_revision` is the positive revision the client last accepted. The client never supplies the next server revision or account ID. The server validates account ownership and the full payload, recomputes the digest, then transactionally compares the base revision with the current head. If they match, it creates exactly one immutable next revision and returns `200 OK` with the new profile/head shape.

For each profile, `(profile_id, client_save_id)` is an idempotency key. Repeating an accepted save ID with the same payload digest never creates a duplicate. The response contains the current profile head plus `accepted_revision`, the revision originally created by that save ID. Thus a replay after another device advanced the head cannot be mistaken for a clean sync at an older revision. Reusing an accepted save ID with a different payload digest returns `409 idempotency_key_reuse` and changes nothing.

If the base revision is stale, return `409 stale_revision` without mutating the profile. The response includes current-head metadata, but not its payload; the client fetches the head via `GET` before conflict resolution:

```json
{
  "error": {
    "code": "stale_revision",
    "message": "The profile changed on another device.",
    "current_head": {
      "revision": 2,
      "client_save_id": "00000000-0000-4000-8000-000000000006",
      "payload_sha256": "<64 lowercase hexadecimal characters>",
      "created_at": "2026-10-12T12:04:00Z"
    }
  }
}
```

Concurrent writes against the same base may produce only one new head. Database constraints and transaction/locking behavior enforce this; timestamps are not conflict controls. Revision history is immutable.

## Entitlements

`GET /v1/entitlements` returns account-scoped service records:

```json
{
  "entitlements": [
    {
      "id": "00000000-0000-4000-8000-000000000007",
      "product_key": "example.product",
      "source_provider": "dd",
      "status": "active",
      "granted_at": "2026-10-12T12:00:00Z",
      "expires_at": null,
      "revoked_at": null,
      "metadata": {}
    }
  ]
}
```

There are no client grant/revoke endpoints in v1. Purchase-receipt verification and platform commerce adapters are deferred. Entitlements are not read from or written into progression payloads; ordinary gameplay gold remains in the game state.

## Errors and Validation

Errors use:

```json
{
  "error": {
    "code": "invalid_payload",
    "message": "The progression payload is invalid."
  }
}
```

The stable v1 status behavior is:

| HTTP | Meaning |
| ---: | --- |
| `400` | Malformed JSON or malformed request syntax |
| `401` | Missing/invalid/expired access or refresh credential |
| `404` | Profile absent or not owned by caller |
| `409` | Stale revision, conflicting profile creation, or idempotency-key reuse |
| `422` | Well-formed request with invalid schema-8 payload or field values |
| `429` | Rate limit; may include `Retry-After` |
| `5xx` | Unavailable/internal failure with sanitized error body |

Unknown payload schema versions, schema 7 on remote writes, malformed envelope fields sent where not accepted, non-finite numbers, and payloads that fail `validate_save_document` are rejected before database mutation. The service never accepts client-chosen revision numbers, account ownership, entitlements, or provider subjects.

## Identity and Platform Boundary

V1 has no client endpoint for asserting or linking `provider_subject`. A future trusted verifier must validate provider proof server-side before creating a `(provider, provider_subject)` link. The canonical identity returned to all clients remains the DD account UUID.

Browser, MicroPython, and future console hosts may call this HTTPS/JSON contract through their own transport and credential adapters. Firebase SDKs and provider-specific data are not required in game core. Firebase remains an unevaluated option behind these contracts; selecting it, changing PostgreSQL, or changing payload shape requires a separately approved architecture decision.

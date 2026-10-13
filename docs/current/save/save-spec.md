# Dungeon Drifters Save Architecture Specification

**Status:** Authority for SAVE-ARCH implementation. This specification freezes the existing approved architecture; it does not select a cloud identity/storage vendor or change the game-state schema.

**Related plan:** [save-plan.md](save-plan.md)
**API contract:** [api-contract.md](api-contract.md)

## Scope and Authority

SAVE-ARCH replaces the current source-tree JSON repository with a storage-neutral game-state document codec, a versioned local profile envelope, an injected local profile store, a `SaveCoordinator`, and an optional DD-owned profile service. It preserves v0.4 gameplay and the schema-8 game-state document.

The boundaries are:

- `GameState` and the schema-8 payload contain gameplay/progression only.
- The profile envelope owns local profile identity, account association, local sequence, last accepted remote revision, sync state, save identity, timestamp, and payload digest.
- `SaveCoordinator` composes the game-state codec and profile store and later coordinates optional remote sync.
- A standalone DD profile service owns canonical accounts, linked identities, sessions, profile ownership, immutable revisions, and entitlements.
- Host/platform adapters provide filesystem roots, credentials, identity proof, and HTTP transport. Shared game/persistence code does not depend on Firebase or platform SDKs.

No browser, mobile, console, launcher, or platform-specific credential UI is part of SAVE-ARCH. A local-only profile must remain fully playable and saveable without an account, service, or network.

## Frozen Baseline

SAVE-ARCH-0 began on `master` at `8a75ab5cc7b010c7c477ceb1064290b2b0033502` (`Update save-plan.md`), matching `origin/master`, with a clean working tree. Work proceeds on the user's current `master`; no feature branch is part of this task.

Baseline checks from `root/`:

- `python -m pytest tests/test_save_state.py tests/test_save_repository.py -q`: **35 passed**.
- `python -m pytest web_tests -q`: **43 passed**.
- `python -m pytest -q`: **1,467 passed**.

The full-suite run used a pytest temp root outside the repository. Keeping nested pytest fixtures outside `root/` avoids inheriting the repository's `pytest.ini` into generated fixture projects.

## Independent Versions

| Version | Current value | Owns |
| --- | ---: | --- |
| Game-state schema | 8 | The existing `GameState` persistence payload |
| Profile-envelope schema | 1 | Local profile metadata surrounding one game-state payload |
| Remote API | `/v1` | DD account, session, profile, revision, and entitlement wire contract |

These versions are independent. A change to one does not implicitly change the others.

## Game-State Payload

The schema-8 payload remains the existing object:

```text
schema_version
player
story
world
overworld
metadata
```

`build_save_document`, `validate_save_document`, `reconstruct_game_state`, and the existing schema-7 migration retain their gameplay semantics. Schema-7 is accepted only as a local legacy input and is normalized in memory to schema 8 before it is wrapped. New local envelopes and all remote API writes contain schema 8 only. Invalid input is rejected, never repaired silently.

Account, profile, device, provider, session, revision, sync, digest, and entitlement data are not added to this payload. The service validates the payload but does not simulate combat or attest that client-authored progression was earned legitimately.

### Canonical Payload Bytes and Digest

`payload_sha256` is lowercase hexadecimal SHA-256 over the canonical UTF-8 bytes of the normalized schema-8 payload object. DD Canonical Payload JSON v1 is defined as the output of the pinned Python 3.14 standard-library JSON encoder with these exact options:

```python
json.dumps(
    payload,
    ensure_ascii=False,
    allow_nan=False,
    sort_keys=True,
    separators=(",", ":"),
).encode("utf-8")
```

There is no BOM, indentation, insignificant whitespace, or trailing newline in the bytes being hashed. Object keys are sorted by Python string ordering; non-ASCII characters are emitted as UTF-8; JSON-required escapes are emitted by the encoder; non-finite floats are rejected. This is a DD v1 contract, not a claim of RFC 8785/JCS compatibility.

The client store and service recompute the digest; they do not trust a submitted digest. A remote revision stores the payload as a JSON object and the digest computed from the canonical bytes. Every client/runtime that enables cloud sync must pass the same canonical-byte and SHA-256 vectors, including Unicode, escaping, nested-key ordering, integers, and finite floats. A runtime that cannot conform may still use local-only saves, but must not participate in cloud sync until its adapter passes those vectors. Existing schema-8 validation semantics are not narrowed to accommodate a particular runtime.

## Local Profile Envelope v1

The envelope wraps exactly one schema-8 payload:

```json
{
  "envelope_version": 1,
  "profile_id": "00000000-0000-4000-8000-000000000001",
  "account_id": null,
  "remote_revision": null,
  "local_sequence": 1,
  "sync_state": "local_only",
  "client_save_id": "00000000-0000-4000-8000-000000000002",
  "saved_at": "2026-10-12T12:00:00.000000Z",
  "payload_sha256": "<64 lowercase hexadecimal characters>",
  "payload": {
    "schema_version": 8
  }
}
```

The example's payload is abbreviated and is not a valid complete game save. The serialized envelope has exactly the listed keys; unknown or missing keys are invalid.

Validation rules:

- `envelope_version` is the integer `1`; booleans are not integers for validation purposes.
- `profile_id` and non-null `account_id` are canonical lowercase, hyphenated UUID strings.
- `remote_revision` is null or a positive integer; booleans are rejected.
- `local_sequence` is an integer of at least `1`; booleans are rejected.
- `sync_state` is exactly `local_only`, `clean`, `pending`, or `conflict`.
- `client_save_id` is a canonical lowercase, hyphenated UUID string.
- `saved_at` is UTC in the exact `YYYY-MM-DDTHH:MM:SS.ffffffZ` form. It is display/audit metadata only and never decides ordering or conflict winners.
- `payload_sha256` is 64 lowercase hexadecimal characters and must match a recomputed digest.
- `payload` passes the existing validator and has `schema_version == 8` after normalization.
- Auth tokens, refresh tokens, passwords, provider subjects, receipts, and secrets never appear in the envelope.

The sync-state invariants are:

| State | Account | Remote revision | Meaning |
| --- | --- | --- | --- |
| `local_only` | null | null | No remote ownership; network is not required |
| `clean` | non-null | positive | Local payload is the accepted remote head |
| `pending` | non-null | null or positive | Local payload is awaiting remote creation/upload |
| `conflict` | non-null | positive | A pending local branch and a different remote head are preserved |

The local sequence starts at `1` and advances on each successful local save. It never decreases or derives from a timestamp. A new payload gets a new `client_save_id`; retrying an unchanged pending payload reuses its ID. A clean envelope may retain the ID of its most recently accepted save.

## Local Storage and Legacy Migration

The local store receives its storage root through composition. Production composition chooses a host-appropriate per-user writable application-data root; neither the codec nor store derives a user's writable location from `__file__` or the current working directory. Tests inject temporary roots. The v0.4 composition root continues to select one default active profile automatically; the store contract can list multiple profiles without adding profile-management UI in this milestone.

Every write validates the complete new envelope before replacing the old one. It writes a temporary sibling file as UTF-8 deterministic JSON, flushes and `fsync`s it, then atomically replaces the destination with `os.replace`; failed writes clean up the temporary file and preserve the previous valid profile. The envelope file has no BOM and no required final newline. Exact file formatting is not part of the payload digest.

Legacy migration recognizes only the existing bare schema-7/schema-8 save at `root/src/saves/dungeon_drifters.json`. It validates before migration, normalizes schema 7 using the existing 7-to-8 rules, generates one profile UUID, wraps the normalized payload as envelope v1 in `local_only` state, and validates/atomically commits the new profile before changing or removing the original. Invalid legacy input is untouched. A repeat after successful commit selects the committed profile and does not create a new profile ID. Migration may add envelope metadata but must preserve the reconstructed gameplay state.

Conflict files/records are stored separately from the active envelope and are never substituted for one another implicitly.

## Accounts, Profiles, and Credentials

- A DD account owns zero or more profile slots, linked identities, sessions, and entitlements.
- A profile UUID is generated locally once and remains unchanged when a local guest profile is claimed by a DD account.
- An account ID is created by the DD service. A client cannot choose another account ID or assert ownership.
- A provider identity can be linked only after a trusted server-side verifier validates its proof. Clients cannot self-assert provider subjects.
- `device_id` is a pseudonymous client installation identifier used for revision attribution, not authentication or account identity. A host may replace it; it is never placed in game state or the profile envelope.
- Access/refresh credentials are held by a separate `CredentialStore` boundary and are never written into game-state payloads, profile envelopes, entitlements, or logs.
- The service stores token hashes, not bearer-token plaintext. Hosted API traffic uses HTTPS.
- Persistent credential-store implementations, platform identity verifiers, and platform SDKs are deferred to their platform-specific plans.

An anonymous account is a real DD account with a session, not a disposable test identity. It is recoverable only while the client retains its credentials; cross-device recovery requires a subsequently verified linked identity. Losing credentials must not make the local profile unreadable.

## Remote Revisions and Sync

The service is authoritative for account identity, profile ownership, revision ordering/history, session validity, and entitlements. The client authors the gameplay payload. Each profile begins at revision `1`; the client never supplies a server revision number.

An upload identifies `profile_id`, `base_revision`, `client_save_id`, `device_id`, and the complete schema-8 `payload`. The server validates ownership and payload, recomputes the digest, and transactionally compares the base with the current head. A matching base creates exactly one next immutable revision. The same profile/save ID and same payload digest returns the already accepted revision without creating another. Reusing that ID for a different payload is rejected. A stale base returns `409` with current-head metadata and changes nothing.

`saved_at`, filesystem metadata, request arrival time, and device clocks never select a winner. There is no automatic field merge and no silent last-write-wins.

State transitions:

- `local_only`: local save/load needs no network. Enabling cloud explicitly creates/claims the same profile ID and moves to `clean` after remote revision 1 is confirmed; an unavailable/ambiguous request remains retryable as `pending`.
- `clean`: a local save is atomically stored first as `pending`, then uploaded against the last accepted revision. Acceptance advances `remote_revision` and returns to `clean`; network failure stays `pending`.
- `pending`: play continues offline. Further saves advance the local sequence and replace the active pending payload with a new save ID. Upload retries the current payload; an accepted duplicate is idempotent.
- `conflict`: automatic upload stops. The original conflict evidence and active local branch are preserved separately from the remote head. Local gameplay may continue, advancing the active local branch while retaining `conflict` state; it must not erase the captured evidence or trigger an upload.

At launch, local loading never waits indefinitely for the service. If offline, use a valid local cache. If a clean cloud-backed profile has a newer validated remote head, it may fast-forward. If a pending upload is stale, capture both sides and enter conflict. Every fetched payload is validated before it can replace the active cache.

### Conflict Evidence and Resolution

The conflict record captures profile ID, local save ID and payload/digest at detection, local base revision, remote head revision and payload/digest, and detection time. The record is immutable evidence. The active local branch may subsequently advance, but the evidence record remains until resolution/archival.

- **Use Remote:** fetch and validate the current server head; archive the latest local branch and conflict evidence as recovery data; atomically install the remote head; mark `clean` only after the cache is valid.
- **Keep Local:** use the latest active local payload, fetch the current server revision, and submit the local payload against that base. Reuse its save ID if its payload has not changed; use the new ID already assigned by a subsequent local save if it has. Acceptance creates a new server revision and marks `clean`; another stale-base response remains a conflict.
- **Fork Local:** preserve the original profile and evidence; create a new profile UUID and save ID for the local branch; create revision 1 under the same account. A UI for this option is deferred, but the storage and service model must allow it.

No resolution rewrites a server revision. No conflict choice is made from timestamps.

## Entitlements and Trust Boundary

Entitlements are account-scoped service records, separate from game-state currency, inventory, and progression. Only trusted service/provider-verification paths may grant, expire, or revoke them. This milestone represents entitlement records but defers purchase-receipt verification and all platform store integrations. Ordinary earned game gold remains in the game-state payload.

The service rejects malformed/unsupported payloads, cross-account reads/writes, client-selected revisions, and save attempts to grant entitlements. This is synchronization and ownership authority, not server-side combat simulation or anti-cheat: a client that can author its local game state can still author plausible progression.

## Vendor and Platform Decisions

The approved baseline is the DD-owned HTTPS/JSON profile API backed by PostgreSQL. Firebase remains an unevaluated candidate, not a selected provider or replacement architecture. If later selected, Firebase must sit behind DD's account/profile contracts; provider identities map to DD account UUIDs. No Firebase Auth/Firestore schema, Firebase SDK in game core, Cloud Run deployment, or provider-specific payload is authorized by this specification.

Browser, MicroPython, and future console clients may use the same logical API through host adapters. That does not prove a target's filesystem, TLS, credential vault, or network stack works; each target must be qualified independently. Local-only play remains available if a target cannot meet cloud requirements.

## SAVE-ARCH Acceptance Boundary

Completion requires all plan gates through SAVE-ARCH-7: old `SaveRepository` removed, client routed through the permanent persistence boundary, local offline flow retained, DD API/PostgreSQL revisions and account boundaries tested, conflict/idempotency behavior proven, entitlements kept outside gameplay saves, existing campaign behavior preserved, CI/migrations qualified, and no unrelated gameplay changes. Platform clients, identity SDKs, receipt verification, and UI for multi-profile/conflict management are outside this milestone.

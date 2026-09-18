# Dungeon Drifters Cross-Platform Save Architecture Implementation Plan

**Goal:** Replace Dungeon Drifters' single-file persistence boundary with the permanent account/profile/revision architecture needed for offline-capable PC play and future shared progression across PC, mobile, and PlayStation, while preserving the current v0.4 game behavior and schema-8 game-state contract.

**Architecture:** The live game remains independent of storage, accounts, networking, and commerce. `GameState` serializes into the existing versioned game-state payload. A separate versioned profile envelope owns profile identity, local revision state, sync state, hashes, and account association. `SaveCoordinator` owns local persistence and optional remote synchronization. A standalone DD profile service owns canonical accounts, linked identities, profile heads/revision history, sessions, and entitlements. Platform identities authenticate accounts; they never become game-state fields.

**Tech Stack:** Python 3.14 client, existing DD domain/persistence code, stdlib JSON/UUID/hash/atomic filesystem operations, FastAPI profile service, PostgreSQL, SQLAlchemy 2.x, Alembic, pytest, httpx test client, GitHub Actions PostgreSQL service.

**Spec:** `docs/save/save-spec.md` (created by SAVE-ARCH-0 from this plan before implementation).

**Planning baseline observed:** `master` at `474e0b412207cdee6b684a4810e698d72da7d1ba` (`RELEASE - Document v0.4 foundation`). The executor MUST resolve and record the actual starting `master` SHA before branching; do not assume this SHA is still current.

## Global Constraints

- Preserve current v0.4 gameplay, combat, content, route, progression, presentation, and terminal behavior.
- Preserve the current schema-8 **game-state payload** and existing schema-7-to-8 migration behavior unless a later game-state change independently requires a new game schema.
- Account IDs, profile IDs, device IDs, linked-platform identities, revisions, auth data, and entitlements MUST NOT be inserted into the schema-8 game-state payload.
- Version these independently:
  - game-state schema: currently `8`
  - profile-envelope schema: starts at `1`
  - remote API: starts at `/v1`
- Offline play is a first-class supported mode. A player must be able to create, play, save, quit, and load a local-only profile with no backend and no account.
- Cloud synchronization is revision-based optimistic concurrency. Never use filesystem timestamps, "latest modified wins", or silent last-write-wins.
- Never field-merge divergent game-state documents automatically.
- A synchronization conflict must preserve both the local pending payload and the remote head until the player explicitly chooses a resolution.
- The backend is authoritative for **profile ordering/ownership, revision history, identity, sessions, and entitlements**. The game client still authors the gameplay payload; this milestone is cross-progression architecture, not anti-cheat/server-simulated combat.
- Entitlements and purchase evidence are account data, never progression/save fields.
- No raw Steam, PSN, Google, Apple, Epic, or other platform account identifier belongs in a save payload.
- No platform SDK integration is required by this milestone. Provider adapters are future edge integrations against the identity boundary created here.
- Do not build a GUI, launcher, installer, MSIX package, browser client, mobile client, or PlayStation client in SAVE-ARCH.
- No compatibility shim may remain merely because implementation used it temporarily. Temporary adapters are allowed during a task but must be removed by the task's acceptance gate if the plan marks them obsolete.
- Existing content validation and the complete current regression suite must remain green after every gate.

---

# Permanent Model

## Game-state payload

The current game-state document remains the payload:

```text
schema_version
player
story
world
overworld
metadata
```

It answers:

```text
WHAT is the player's game state?
```

It must remain independently validatable and reconstructable as a `GameState`.

## Local profile envelope v1

A local profile cache wraps, rather than modifies, the game-state payload:

```json
{
  "envelope_version": 1,
  "profile_id": "uuid",
  "account_id": null,
  "remote_revision": null,
  "local_sequence": 1,
  "sync_state": "local_only",
  "client_save_id": "uuid",
  "saved_at": "RFC3339-UTC",
  "payload_sha256": "64-lowercase-hex",
  "payload": {
    "schema_version": 8
  }
}
```

Required semantics:

- `profile_id`: canonical UUID created once and retained if a local guest profile later becomes cloud-backed.
- `account_id`: `null` for local-only guest ownership; canonical DD account UUID after claim/link.
- `remote_revision`: last server revision accepted or downloaded; `null` until the profile exists remotely.
- `local_sequence`: monotonically increasing local save counter; it is not a server revision.
- `sync_state`: one of `local_only`, `clean`, `pending`, `conflict`.
- `client_save_id`: UUID identifying the latest unsynchronized client save. Retries reuse it so remote commits are idempotent.
- `saved_at`: display/audit metadata only. It must never determine conflict winners.
- `payload_sha256`: SHA-256 over the canonical UTF-8 payload bytes.
- `payload`: the normal DD game-state document.

## Local conflict snapshot

A conflict must not overwrite either side. Store a separate conflict record containing:

```text
profile_id
local client_save_id
local payload/hash
local base remote_revision
remote current_revision
remote payload/hash
detected_at
```

Conflict resolution choices are explicit:

```text
USE REMOTE
- archive/preserve the local conflicted payload as recovery evidence
- replace active cache with the validated remote head
- mark clean

KEEP LOCAL
- require the user to explicitly choose it
- submit the local payload against the now-known current remote revision
- server creates a NEW revision; it never rewrites old revision history
- mark clean only after acceptance

FORK LOCAL
- reserved contract from day one
- create a new profile_id from the local branch
- may remain UI-deferred, but the storage/service model must not make it impossible
```

## Canonical account model

```text
DD Account
├── account_id
├── linked identities
├── sessions
├── profiles
└── entitlements
```

A profile is a progression slot. An account may own multiple profiles even though the current v0.4 UI continues to operate on one active profile.

## Remote revision model

Remote save submission:

```text
client knows remote revision N
client changes state offline/locally
client submits:
    profile_id
    base_revision = N
    client_save_id
    payload
```

Server behavior:

```text
server head == N
→ validate request
→ create revision N+1 transactionally
→ return N+1

same client_save_id already accepted
→ return the already-created revision
→ do not create a duplicate

server head != N
→ HTTP 409 conflict
→ return current revision metadata
→ do not modify server state
```

No timestamps participate in this decision.

---

# Target Repository Layout

Keep the game client and service separated:

```text
root/
├── src/app/
│   ├── game/
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── save_document.py
│   │   ├── envelope.py
│   │   ├── ports.py
│   │   ├── local_store.py
│   │   ├── migration.py
│   │   ├── coordinator.py
│   │   ├── remote_client.py
│   │   └── sync.py
│   └── ...
├── tests/
└── tools/

services/
└── profile_api/
    ├── requirements.txt
    ├── alembic.ini
    ├── migrations/
    ├── src/profile_api/
    │   ├── __init__.py
    │   ├── app.py
    │   ├── config.py
    │   ├── db.py
    │   ├── models.py
    │   ├── schemas.py
    │   ├── save_contract.py
    │   ├── auth.py
    │   ├── accounts.py
    │   ├── identities.py
    │   ├── profiles.py
    │   ├── entitlements.py
    │   └── routes/
    └── tests/

docs/
└── save/
    ├── save-spec.md
    ├── api-contract.md
    └── operations.md
```

`services/profile_api/src/profile_api/save_contract.py` imports only the persistence validation boundary from `root/src`; it must not import UI/presentation/session orchestration. CI sets both source roots explicitly for service tests.

---

# SAVE-ARCH-0 — Freeze the Contract Before Code

**Purpose:** Turn the architecture into an explicit project authority before implementation starts.

**Files:**
- Create: `docs/save/save-spec.md`
- Create: `docs/save/api-contract.md`
- Modify only if needed for a link: `README.md`

**Required spec content:**
- the three independent versions: game schema, envelope schema, API version
- exact envelope v1 fields and validation rules
- account/profile/identity/entitlement ownership rules
- offline behavior
- optimistic concurrency contract
- idempotency contract
- conflict preservation/resolution contract
- local guest -> cloud-backed profile claim contract
- token/credential boundary
- threat/trust boundary
- explicit statement that remote authority is synchronization/ownership authority, not server-side combat authority
- explicit deferred platform adapters

**Steps:**
- [ ] Resolve current `master`, record exact SHA, confirm clean/synced tree.
- [ ] Capture current save tests and full-suite baseline.
- [ ] Write the two authority docs with no implementation-specific ambiguity.
- [ ] Review every later SAVE-ARCH task against the docs.
- [ ] Commit.

**Commit:** `SAVE-ARCH-0 - Define Cross-Platform Persistence Contract`

**Gate:** docs only; no production behavior changed.

---

# SAVE-ARCH-1 — Isolate the Game-State Save Document

**Purpose:** Make the current schema-8 document a storage-neutral persistence codec instead of a file-repository implementation detail.

**Files:**
- Create: `root/src/app/persistence/__init__.py`
- Move/refactor: `root/src/app/game/save_state.py` -> `root/src/app/persistence/save_document.py`
- Modify imports in:
  - `root/src/app/game/save_repository.py` (temporary during this gate)
  - `root/tools/validate_content.py`
  - affected tests
- Preserve/update: `root/tests/test_save_state.py`

**Interfaces produced:**

```python
DISK_SCHEMA_VERSION: int

class SaveStateValidationError(ValueError): ...

def build_save_document(game_state: GameState) -> dict: ...
def validate_save_document(document: object) -> dict: ...
def reconstruct_game_state(document: object) -> GameState: ...
def migrate_schema_7(document: object) -> dict: ...
```

Names may remain exactly as today to minimize behavioral churn.

**Requirements:**
- [ ] Write/import-boundary tests first.
- [ ] Move the codec without altering document bytes, validation semantics, canonical weapon/profile reconstruction, or schema-7 migration.
- [ ] Update `tools.validate_content` to validate the new persistence boundary.
- [ ] Prove a current schema-8 fixture is byte-identical before/after this refactor.
- [ ] Prove schema-7 migration remains in-memory and non-destructive.
- [ ] Run focused persistence/content tests.
- [ ] Run full regression suite, content validator, compileall, diff-check.
- [ ] Commit.

**Commit:** `SAVE-ARCH-1 - Isolate Save Document Contract`

**Gate:** zero storage or gameplay behavior change.

---

# SAVE-ARCH-2 — Add Profile Envelope and Revisioned Local Storage

**Purpose:** Replace "the save is a JSON file at this source-tree path" with a canonical local profile store that already speaks the long-term profile/revision language.

**Files:**
- Create: `root/src/app/persistence/envelope.py`
- Create: `root/src/app/persistence/ports.py`
- Create: `root/src/app/persistence/local_store.py`
- Create: `root/src/app/persistence/migration.py`
- Create: `root/tests/test_save_envelope.py`
- Create: `root/tests/test_local_profile_store.py`
- Create: `root/tests/test_legacy_save_migration.py`

**Core types:**

```python
class SyncState(StrEnum):
    LOCAL_ONLY = "local_only"
    CLEAN = "clean"
    PENDING = "pending"
    CONFLICT = "conflict"

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
```

Add immutable typed results for missing/valid/invalid/conflict states; do not use untyped dictionaries outside serialization boundaries.

**Local storage contract:**

```python
class ProfileStore(Protocol):
    def inspect(self, profile_id: UUID) -> ...
    def load(self, profile_id: UUID) -> ProfileEnvelope | ...
    def save(self, envelope: ProfileEnvelope) -> ...
    def list_profiles(self) -> tuple[...]: ...
    def load_conflict(self, profile_id: UUID) -> ...
    def save_conflict(self, ...) -> ...
    def clear_conflict(self, profile_id: UUID) -> None: ...
```

**Filesystem requirements:**
- storage root is injected; no persistence class derives ownership from its own `__file__`
- one stable `profile_id` per save slot
- current v0.4 still auto-selects one active/default profile
- writes retain the current atomic-write guarantees:
  - parent creation
  - temp file
  - UTF-8 deterministic JSON
  - validation before replacement
  - `os.replace`
  - temp cleanup on failure
- payload hash is recomputed, never trusted from input
- envelope validation calls `validate_save_document(payload)`
- invalid data is never silently repaired

**Legacy migration:**
- detect the current bare schema-7/schema-8 file
- validate it first
- generate canonical `profile_id`
- wrap normalized game state in envelope v1
- preserve the original file until the new envelope has been atomically committed and validated
- never migrate an invalid file
- repeated migration attempt is idempotent
- schema-7 input still uses the existing 7->8 migration semantics
- migration changes ownership metadata only; game progression must remain equivalent

**Tests must prove:**
- envelope rejects unknown/missing fields
- UUID fields are canonical
- bad hash rejected
- local sequence cannot go backwards through the store
- explicit injected roots work
- failed replace preserves previous valid profile
- invalid envelope does not replace valid state
- legacy schema-8 wraps without gameplay drift
- legacy schema-7 migrates to valid schema-8 payload inside envelope v1
- no source-tree path is required by the store

**Commit:** `SAVE-ARCH-2 - Add Revisioned Local Profile Storage`

**Gate:** local profile persistence works independently before game/session integration.

---

# SAVE-ARCH-3 — Introduce SaveCoordinator and Migrate the Game

**Purpose:** Make gameplay depend on a persistence capability, not a concrete filesystem repository.

**Files:**
- Create: `root/src/app/persistence/coordinator.py`
- Modify: `root/src/app/persistence/ports.py`
- Modify: `root/src/app/game/main_loop.py`
- Modify: `root/src/app/game/overworld_session.py`
- Remove by gate closure: `root/src/app/game/save_repository.py`
- Replace/update: `root/tests/test_save_repository.py`
- Update all tests currently constructing `SaveRepository(...)`
- Preserve M11 save/quit/restart/load tests

**Client-facing persistence port:**

```python
class SavePort(Protocol):
    def inspect(self) -> SaveLoadResult: ...
    def save(self, game_state: GameState) -> SaveLoadResult: ...
    def load(self) -> SaveLoadResult: ...
```

`SaveCoordinator` implements `SavePort`.

**Responsibilities:**

```text
SaveCoordinator
├── build/validate/reconstruct game-state payload
├── own active profile identity
├── increment local_sequence
├── create/reuse client_save_id correctly
├── build profile envelope
├── write through ProfileStore
└── later delegate sync through RemoteProfileClient
```

`LocalProfileStore` knows files but not `GameState`.

`save_document.py` knows `GameState` but not files/network/accounts.

`OverworldSession` knows the `SavePort`, not `LocalProfileStore`, HTTP, account IDs, or paths.

**Composition root:**
Create one default persistence builder used by `main_loop.py`. It composes:
- local profile store
- active profile selection
- legacy migration
- save coordinator
- remote client = `None` at this gate

**Behavior requirements:**
- current title startup load/new flow remains behaviorally equivalent
- in-session Save/Load behavior remains equivalent
- missing save still means normal new-game path
- invalid local save is reported without mutation
- save failures retain the current player-facing error behavior
- tests inject memory/temp stores; they do not depend on production filesystem paths
- remove the concrete `isinstance(save_repository, SaveRepository)` dependency from `OverworldSession`

**Acceptance tests:**
- all four M11 split-campaign save/continue proofs
- repeated load returns fresh reconstructed state
- save->quit->process-style restart->load equivalent snapshot
- active profile identity survives restart
- local-only profile shows `account_id=None`, `remote_revision=None`, `sync_state=local_only`
- full regression suite

**Commit:** `SAVE-ARCH-3 - Route Game Persistence Through SaveCoordinator`

**Gate:** `SaveRepository` is gone; the game is fully running through the permanent persistence boundary.

---

# SAVE-ARCH-4 — Build the DD Account/Profile Backend

**Purpose:** Implement the actual canonical remote authority rather than leaving cloud save as a hypothetical interface.

**Files:**
- Create complete `services/profile_api/` service tree
- Create service dependencies in `services/profile_api/requirements.txt`
- Create Alembic initial migration
- Create service tests
- Create: `docs/save/operations.md`
- Modify CI later in SAVE-ARCH-7, not mid-gate unless required for proof

**Service stack:**
- FastAPI
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Pydantic request/response models
- pytest/httpx

**Database tables:**

### `accounts`
```text
id UUID PK
status
created_at
updated_at
```

### `account_sessions`
```text
id UUID PK
account_id FK
access_token_hash
refresh_token_hash
device_id
access_expires_at
refresh_expires_at
revoked_at nullable
created_at
```

Never store bearer tokens in plaintext.

### `linked_identities`
```text
id UUID PK
account_id FK
provider
provider_subject
created_at

UNIQUE(provider, provider_subject)
```

Do not expose an API that lets a client self-assert `provider_subject`. A provider adapter must verify external proof first.

### `profiles`
```text
id UUID PK
account_id FK
current_revision BIGINT nullable
status
created_at
updated_at
```

A client-created guest `profile_id` may be claimed if it does not already exist, preserving the same profile identity.

### `profile_revisions`
```text
profile_id FK
revision BIGINT
base_revision BIGINT nullable
client_save_id UUID
device_id UUID nullable
payload JSONB
payload_sha256
created_at

PRIMARY KEY(profile_id, revision)
UNIQUE(profile_id, client_save_id)
```

### `entitlements`
```text
id UUID PK
account_id FK
product_key
source_provider
status
granted_at
expires_at nullable
revoked_at nullable
metadata JSONB
```

Entitlements exist now even though platform receipt adapters are deferred.

**API v1:**

```text
GET    /v1/health

POST   /v1/accounts/anonymous
POST   /v1/sessions/refresh
DELETE /v1/sessions/current

GET    /v1/profiles
POST   /v1/profiles
GET    /v1/profiles/{profile_id}
PUT    /v1/profiles/{profile_id}/progression

GET    /v1/entitlements
```

### Anonymous account semantics

`POST /v1/accounts/anonymous` creates a real canonical DD account plus a session. It is recoverable on that credential-bearing device and may later be linked to verified external identities. It is not a fake/test account.

Do not implement username/password auth in this milestone.

### Profile creation/import

Authenticated `POST /v1/profiles` accepts:
- client-created `profile_id`
- `client_save_id`
- validated schema-8 payload
- device ID

If the `profile_id` is unowned, create it for the authenticated account and create revision `1` transactionally.

If it already exists for another account: reject.

### Progression PUT

Request:

```json
{
  "base_revision": 4,
  "client_save_id": "uuid",
  "device_id": "uuid",
  "payload": {}
}
```

Transaction:
1. authenticate account
2. lock/read profile head
3. verify ownership
4. validate payload contract
5. recompute payload hash
6. check duplicate `client_save_id`
7. compare `base_revision` to current head
8. insert exactly one next revision
9. update profile head
10. commit
11. return new head

Return `409` if base revision is stale, with current revision metadata but without mutating the profile.

**Save validation boundary:**
`profile_api/save_contract.py` imports the storage-neutral DD save validator from `root/src/app/persistence/save_document.py`. The service is allowed to depend on persistence/domain validation; it must not import terminal UI, presentation, or game-session orchestration.

**Service tests must prove:**
- cross-account profile reads/writes are denied
- duplicate client save retry is idempotent
- stale base produces 409
- concurrent submissions create only one next head
- revision history is immutable
- invalid game payload never becomes a revision
- client cannot choose server revision number
- client cannot grant itself an entitlement through save data
- raw auth tokens are not stored
- session revoke/refresh behavior works
- database migration up/down proof in test environment

**Commit:** `SAVE-ARCH-4 - Add Canonical DD Profile Service`

**Gate:** backend persistence/concurrency works with PostgreSQL independently of game client sync.

---

# SAVE-ARCH-5 — Account Identity and Guest-to-Cloud Claim

**Purpose:** Make today's no-login player compatible with tomorrow's Steam/Google/Apple/PSN-linked account without changing profile identity.

**Files:**
- Create/modify client credential/account types under `root/src/app/persistence/`
- Modify service account/session/identity modules
- Add tests on both sides

**Rules:**

### Local guest
- no account required
- `account_id=None`
- profile works indefinitely offline
- canonical `profile_id` already exists

### Enabling cloud
1. client obtains/creates authenticated DD account
2. client submits the existing `profile_id` plus current payload
3. backend claims that same profile ID for the account and creates remote revision 1
4. client writes returned `account_id` + `remote_revision=1`
5. cache becomes `clean`

No "new cloud save ID" is created during claim.

### Future platform linking
Define provider-neutral service contracts:

```python
class IdentityVerifier(Protocol):
    def verify(self, proof: object) -> VerifiedIdentity: ...

@dataclass(frozen=True)
class VerifiedIdentity:
    provider: str
    provider_subject: str
```

Only a verified identity may be linked.

Future adapters:
```text
Steam verifier
Google verifier
Apple verifier
PlayStation verifier
Epic verifier
```

are deferred. The account/identity database and service do not change when those adapters arrive.

### Credentials
Auth credentials are NOT stored:
- in save payload
- in profile envelope
- in entitlement records

Define a client **CredentialStore** port. Authentication credentials MUST remain separate from game-state payloads and profile envelopes. Tests use **MemoryCredentialStore**. Persistent platform-specific credential-store implementations are deferred to their respective client/platform plans.

**Critical ownership cases to test:**
- local guest claim succeeds and profile_id is unchanged
- claim retry is idempotent
- cannot claim profile already owned by another account
- linking an already-linked external identity to a second account fails
- linked identity removal cannot orphan an account without another recovery/session policy
- auth/session loss never makes the local save unreadable

**Commit:** `SAVE-ARCH-5 - Add Account Claim and Identity Boundaries`

**Gate:** guest-to-account transition is real and does not rewrite progression identity.

---

# SAVE-ARCH-6 — Remote Sync and Conflict State Machine

**Purpose:** Connect the game client to the backend without making network availability a requirement for single-player play.

**Files:**
- Implement: `root/src/app/persistence/remote_client.py`
- Implement: `root/src/app/persistence/sync.py`
- Modify: `root/src/app/persistence/coordinator.py`
- Add tests:
  - `root/tests/test_remote_profile_client.py`
  - `root/tests/test_profile_sync.py`
  - `root/tests/test_profile_conflicts.py`

**Remote client port:**

```python
class RemoteProfileClient(Protocol):
    def get_profile(self, profile_id: UUID) -> RemoteProfileHead: ...
    def create_profile(...) -> RemoteProfileHead: ...
    def push_progression(...) -> RemoteProfileHead | RemoteConflict: ...
```

Network transport details stay below this interface.

**Sync state machine:**

### `local_only`
- save locally
- no network call required
- if cloud is enabled, create/claim remote profile and transition to `clean`

### `clean`
- local payload equals accepted remote head
- on local save:
  - persist new local payload atomically first
  - set `pending`
  - attempt remote upload
  - if accepted: update `remote_revision`, mark `clean`
  - if unavailable: remain `pending`

### `pending`
- game remains playable
- each new local save replaces the pending payload with the latest local state, increments `local_sequence`, and creates a new `client_save_id`
- `remote_revision` remains the base revision until server accepts
- reconnect attempts current pending payload

### `conflict`
- never overwrite local pending data
- fetch/store remote head in separate conflict snapshot
- block automatic upload
- game may continue locally, but sync remains conflicted
- explicit resolution required

**Launch policy:**
- local load must not wait indefinitely for network
- if cloud-backed and network is available:
  - clean local cache may fast-forward to newer remote head after validation
  - pending local cache attempts upload
  - stale upload becomes conflict
- if network is unavailable:
  - use local valid cache
  - expose sync status but do not block play

**Required two-device acceptance test:**

```text
Device A loads remote rev 1
Device B loads remote rev 1

A changes state
A submits rev 1 -> server creates rev 2

B goes offline
B changes state based on rev 1
B saves locally (pending)

B reconnects
B submits base rev 1
server head is rev 2
→ 409

B preserves local state
B stores remote rev 2 as conflict side
server rev 2 remains untouched
```

Then prove both explicit resolutions:

```text
USE REMOTE
→ local branch archived/recovery-preserved
→ remote rev 2 becomes active
→ clean

KEEP LOCAL
→ user explicitly selects local
→ client resubmits local payload using current server rev 2 as base
→ server creates rev 3
→ no historical revision is rewritten
→ clean
```

Also prove same-request retry does not produce rev 4.

**Commit:** `SAVE-ARCH-6 - Add Offline Cloud Sync and Conflict Safety`

**Gate:** simulated multi-device synchronization is correct under success, offline, retry, and divergence.

---

# SAVE-ARCH-7 — Seal Entitlements, CI, and End-to-End Acceptance

**Purpose:** Close the architectural holes that are expensive to retrofit later and prove the entire system as one vertical slice.

**Entitlement boundary requirements:**
- account-scoped
- service-authoritative
- progression payload cannot grant/revoke entitlement
- source provider retained
- expiration/revocation representable
- purchase receipt verification adapters deferred
- future platform-restricted currency can be represented separately from ordinary game-state currency

Do NOT move ordinary earned gameplay gold into the entitlement service.

**End-to-end scenarios:**

### Scenario A — Pure offline
```text
fresh machine
→ create local guest profile
→ play
→ save
→ quit
→ restart
→ load identical progression
→ no backend available at any point
```

### Scenario B — Guest becomes cloud-backed
```text
existing offline profile
→ create/authenticate DD account
→ claim same profile_id
→ revision 1 created
→ local state unchanged
→ restart
→ same profile loads
```

### Scenario C — Second device
```text
device 2 authenticates same account
→ lists profile
→ downloads head
→ reconstructs valid GameState
→ plays
→ saves
→ revision advances
→ device 1 later fast-forwards cleanly
```

### Scenario D — Divergence
Run the SAVE-ARCH-6 two-device conflict proof.

### Scenario E — Tamper boundaries
Prove:
- another account cannot read/write profile
- client cannot set revision
- client cannot insert an entitlement into save state and gain ownership
- malformed payload rejected
- duplicate network retry remains idempotent

### Scenario F — Existing campaign
Run the existing full surface campaign/save-continuation acceptance so the persistence rewrite proves no v0.4 gameplay regression.

**CI changes:**
Modify `.github/workflows/tests.yml` or split a dedicated service workflow so CI proves:
- authored-content validator
- client pytest suite
- `python -m compileall src tests tools`
- service pytest suite
- PostgreSQL integration tests
- Alembic migration proof
- diff-check/repository hygiene as appropriate

Keep the existing client job working from `root/`.

**Documentation:**
Update README architecture section to explain:
- game-state payload vs profile envelope
- local/offline behavior
- optional cloud-backed profiles
- account identities are external to game state
- entitlements are external to progression

**Final gate commands/evidence:**

From `root/`:
```text
python -m tools.validate_content
python -m pytest
python -m compileall src tests tools
```

Service:
```text
run profile service tests against clean PostgreSQL
run migrations from zero to head
run API/concurrency acceptance
```

Repository:
```text
git diff --check
clean working tree
local branch == origin branch
exact-SHA CI green
```

Then review:
- per-commit diff
- cumulative diff from recorded SAVE-ARCH-0 base
- no unrelated gameplay/content changes
- no stale `SaveRepository` path
- no account/platform metadata inside game payload
- no timestamp-based conflict resolution
- no silent merge
- no entitlement authority in client save

**Commit:** `SAVE-ARCH-7 - Seal Cross-Platform Persistence Foundation`

**Disposition when accepted:** `SAVE-ARCH SEALED`

---

Future Android/iOS/PlayStation clients consume the same logical contracts:

```text
same DD account
same profile_id
same remote revision semantics
same game-state schema family
same entitlement authority
different platform shell / credential store / identity verifier
```

---

# Reviewer Stop Conditions

Stop the implementation and review before continuing if any task introduces one of these:

```text
account_id inside schema-8 payload
platform user IDs inside game state
entitlements inside inventory/save state
timestamp-based "newest wins"
automatic field-level save merging
remote-only requirement for normal single-player startup
network call before a valid local cache can load
client-controlled server revision numbers
plaintext stored auth tokens
concrete FastAPI/HTTP dependencies in game/session/domain code
filesystem path logic in GameState/save-document codec
new gameplay/content/balance behavior bundled into SAVE-ARCH
```

These are architecture failures, not cleanup items.

---

# Expected Commit Chain

```text
SAVE-ARCH-0 - Define Cross-Platform Persistence Contract
SAVE-ARCH-1 - Isolate Save Document Contract
SAVE-ARCH-2 - Add Revisioned Local Profile Storage
SAVE-ARCH-3 - Route Game Persistence Through SaveCoordinator
SAVE-ARCH-4 - Add Canonical DD Profile Service
SAVE-ARCH-5 - Add Account Claim and Identity Boundaries
SAVE-ARCH-6 - Add Offline Cloud Sync and Conflict Safety
SAVE-ARCH-7 - Seal Cross-Platform Persistence Foundation
```

Corrective `A` commits are allowed when review finds a real defect:

```text
SAVE-ARCH-3A
SAVE-ARCH-6A
...
```

Do not advance a gate simply because its tests are green. Each gate requires contract review plus focused/full proof.

---

# Definition of Done

SAVE-ARCH is done only when all of the following are true:

```text
GameState knows nothing about accounts, platforms, HTTP, or files.

Schema 8 remains a game-state payload rather than becoming a cloud/account blob.

A new player can play/save/load forever offline.

Every local profile has a stable canonical profile_id.

A local guest profile can become cloud-backed without changing profile_id.

The backend owns account/profile ownership and immutable revision ordering.

Retries are idempotent.

Two devices cannot silently overwrite each other.

Conflicts preserve both sides.

Linked identities are authentication relationships, not progression data.

Entitlements are account/service data, not save data.

Current v0.4 campaign/save behavior still passes.

The current game runs through SaveCoordinator, not SaveRepository.
```

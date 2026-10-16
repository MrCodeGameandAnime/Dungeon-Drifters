# SAVE-ARCH-R1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Execute natively in the current session unless the user explicitly authorizes delegation.

**Goal:** Correct the five verified post-series persistence defects without replacing the SAVE-ARCH design or changing its wire versions.

**Architecture:** Preserve the eight existing SAVE-ARCH commits and add one cumulative corrective revision on top of `3eb37f5`. Keep `GameState`, envelope v1, the DD `/v1` service, and PostgreSQL revision semantics intact; harden client durability/reconciliation, replay interpretation, the gameplay port boundary, and identity concurrency.

**Tech Stack:** Python 3.14 client, existing DD persistence and sync code, FastAPI, SQLAlchemy 2.x, PostgreSQL, pytest/httpx, existing pinned MicroPython 1.29.0 Windows executable and qualification matrix.

**Spec:** [save-spec.md](save-spec.md), [api-contract.md](api-contract.md), and the existing runtime qualification procedure in [mpy20.md](../../old/mpy/mpy20.md).

## Global Constraints

- Preserve game-state schema `8`, profile-envelope schema `1`, and remote API `/v1`.
- Do not rewrite SAVE-ARCH-0 through SAVE-ARCH-7 or create a second save representation.
- Local-only save/load remains usable without accounts, network, or a service.
- A durable and validated local commit returns `SAVED`; expected subsequent sync failures are represented as `SyncResult`, not raised through gameplay.
- Never blanket-catch `Exception` in persistence orchestration; expected remote/store operational failures are normalized narrowly.
- Preserve both conflict branches and recovery evidence; never infer conflict resolution from timestamps or payload coincidence after a true create collision.
- Do not add Firebase/vendor SDKs, automatic field merges, game-state changes, or gameplay test hooks.
- Keep the Overworld session's import-time graph independent of envelope, filesystem, HTTP, and sync modules.
- MicroPython qualification must launch the pinned executable; synthetic parser output is not runtime evidence.
- Perform PostgreSQL concurrency qualification against real PostgreSQL, not SQLite.
- If any correction requires changing game-state schema `8`, profile-envelope schema `1`, remote API `/v1`, or the existing PostgreSQL migration contract, stop and revise this plan before implementation continues.
- Treat the sealed MPY20 qualification artifacts as fixed evidence authorities. Do not modify `micropython_probe.py`, `micropython_probe_bootstrap.py`, `micropython_heap_sweep.py`, or `runtime_qualification_matrix.py` merely to restore green qualification. A genuine defect in those tools requires an explicit plan revision before changing them.
- If the real MicroPython qualification produces a 448K failure, a 416K success, semantic-contract drift, or a need to change the existing probe contract, stop and investigate rather than moving the qualification boundary.

## Review Focus

- A sync/store failure after local replacement leaves the save durable, pending, loadable, and retryable; prove in Task 1.
- Crashes between conflict archive, sidecar replacement, clean-envelope commit, and sidecar cleanup reconcile without losing evidence or resurrecting a resolved conflict; prove in Task 2.
- Lost create/progression responses followed by later remote writes fast-forward only when the server replay marker proves ancestry; true 409 collisions never become clean through digest coincidence; prove in Task 3.
- The gameplay session's transitive import graph does not load full persistence modules, and the actual pinned runtime still passes the preserved route/heap qualification; prove in Tasks 1 and 5.
- Simultaneous removal of the last two recovery identities cannot leave an account unrecoverable; prove against PostgreSQL in Task 4.

---

## Baseline and Release Shape

- Keep the work on the user's current `master`; require `HEAD` and `origin/master` to equal `3eb37f5993186e41340ac8d51d0638e182a8215b` before implementation. The only pre-existing working-tree changes allowed are the reviewed planning documents `docs/current/save/save-plan.md`, `save-spec.md`, and `save-r1-plan.md`; include them with R1. Stop for any other pre-existing changes or if either baseline ref has moved. Do not reset, stash, or rewrite history.
- Keep SAVE-ARCH-0 through SAVE-ARCH-7 intact. The correction is one post-series revision named `SAVE-ARCH-R1 - Harden Sync Recovery, Replay Semantics, Identity Concurrency, and Runtime Portability`.
- Run focused tests after each task. Run the complete client, web, PostgreSQL-service, migration, content, compile, and runtime qualification only after all four implementation tasks are complete.
- Record observed test totals and MicroPython memory telemetry in this plan after verification; do not predeclare counts.
- Commit R1 only after local qualification. Push and require exact-SHA workflows only with the user's authorization; do not force-push.
- Hard stop conditions: baseline moved; schema/envelope/API/migration contract change required; sealed MicroPython qualification tooling must change; 448K is not stable 3/3; 416K is not `MEMORY_LIMIT` 3/3; or the preserved semantic signature no longer matches. Any of these requires investigation and a plan revision before implementation continues.

### Task 1: Preserve Local-First Results and Restore the Lightweight Port Boundary

**Files:**
- Create: `root/src/app/persistence/save_port_contract.py`
- Modify: `root/src/app/persistence/ports.py`
- Modify: `root/src/app/persistence/coordinator.py`
- Modify: `root/src/app/persistence/sync.py`
- Modify: `root/src/app/game/overworld_session.py`
- Modify: `root/tests/test_save_coordinator.py`
- Modify: `root/tests/test_profile_sync.py`
- Modify: `root/tests/test_overworld_session.py`
- Modify: `root/tests/test_session_persistence_boundary.py`

**Interfaces:**
- `save_port_contract.py` owns lightweight `SaveLoadStatus`, `SavePortError`, and `is_save_port`; it may depend on the existing tiny structural helper but not on profile, filesystem, HTTP, or sync modules.
- `ports.py` may re-export the lightweight contract while retaining storage-facing types.
- `OverworldSession` consumes the lightweight contract only.
- `ProfileSyncCoordinator` returns a `SyncResult` for expected `RemoteProfileError`, `ProfileStoreError`, `OSError`, and `ProfileEnvelopeValidationError`; unexpected programming errors remain visible.

- [x] Add a regression where an account-backed local save is committed and read-back-validated, then automatic sync hits an injected expected storage/remote operational failure. Assert `SaveCoordinator.save()` returns `SAVED`, the new game state loads, the envelope remains `PENDING`, and a later `sync_pending()` succeeds without changing the payload.
- [x] Add focused tests for store `OSError`/`ProfileStoreError` during inspect/load and host `SavePortError` during session inspection/load. Assert the options/session view remains available and loading returns to the options surface with a failure notice rather than raising.
- [x] Replace the direct-import-only boundary test with a transitive module-import check executed in a fresh CPython subprocess so preloaded pytest modules cannot contaminate the result. The subprocess imports only `app.game.overworld_session`, then reports the relevant `sys.modules` entries. Assert that this import reaches neither `app.persistence.ports`, envelope, local store, coordinator, remote client, nor `copy`/`datetime` through a persistence import path.
- [x] Run the new tests and confirm they fail against the current behavior.
- [x] Implement the lightweight contract; normalize expected local-store failures in coordinator inspect/load; keep all local file operations inside the protected save transaction; and normalize expected sync operational failures to `SyncResult` without `except Exception`.
- [x] Change `OverworldSession` to import the lightweight contract and safely handle operational `SavePortError` from inspect/load.
- [x] Run focused persistence, session, and boundary tests; verify the production composition still lazily installs the concrete coordinator.

### Task 2: Make Conflict Transitions Restart-Safe

**Files:**
- Modify: `root/src/app/persistence/sync.py`
- Modify: `root/src/app/persistence/local_store.py`
- Modify: `root/src/app/persistence/ports.py`
- Modify: `root/tests/test_profile_conflicts.py`
- Modify: `root/tests/test_profile_sync.py`
- Modify: `root/tests/test_local_profile_store.py`

**Interfaces:**
- Add an explicit atomic conflict-sidecar replacement operation for valid prior evidence. It must compare the expected prior evidence, replace by sibling-temp plus `os.replace`, and never clear the only valid sidecar before its successor is present.
- Missing and invalid sidecars are different recovery states. A missing sidecar may be reconstructed only from the active local branch plus a validated remote head when the reconciliation rules below prove that reconstruction is safe. An invalid sidecar must not be silently overwritten or cleared. Preserve the malformed bytes through an explicit quarantine/archive operation before any repair, or return `local_conflict_invalid` without mutating the evidence.
- Recovery-profile archive idempotency compares the immutable branch identity: `profile_id`, `client_save_id`, and payload/digest. Mutable sync metadata does not make an otherwise identical branch a different archive.

- [x] Add restart/fault-injection tests for: valid evidence written before the active envelope reaches `CONFLICT`; a replacement interrupted after archival but before replacement; a replacement interrupted after replacement but before active-envelope update; resolution interrupted after clean-envelope commit but before sidecar removal; and repeated recovery archival for the same branch at different remote base revisions. Reconstruct fresh store/coordinator objects after each interruption.
- [x] Add reconciliation tests for `PENDING + valid sidecar -> CONFLICT`; `CLEAN + superseded residue -> archive/clear without conflict resurrection`; `CONFLICT + missing sidecar -> remain recoverably conflicted unless safe online reconstruction succeeds`; `CONFLICT + invalid sidecar -> preserve/quarantine invalid evidence and remain recoverably conflicted`; and online repair only from a validated remote head newer than the recorded base.
- [x] Run the new tests and confirm the current clear-before-replacement / early-return behavior fails the relevant cases.
- [x] Implement restart reconciliation. A clean envelope retires sidecar residue only when its remote revision is newer than the evidence head, or equal with matching validated payload digest. A conflict envelope never becomes clean just because evidence is absent. For a missing sidecar, if online repair is possible, rebuild sidecar evidence from the active local branch and validated current remote head; otherwise preserve state and return a recoverable conflict result. For an invalid sidecar, do not overwrite or clear it in place: first preserve the malformed bytes in a quarantine/archive record, or return `local_conflict_invalid` without mutation.
- [x] Archive the prior branch/evidence before replacement; atomically replace the conflict sidecar; update the active envelope only after the replacement exists. Keep resolution ordering archive -> validated clean envelope -> sidecar clear, relying on restart reconciliation if clear fails.
- [x] Run focused conflict, local-store, and profile-sync tests, including injected failures after every filesystem boundary.

### Task 3: Honor Idempotent Replay Ancestry and Real Creation Collisions

**Files:**
- Modify: `root/src/app/persistence/sync.py`
- Modify: `root/tests/remote_sync_test_support.py`
- Modify: `root/tests/test_profile_sync.py`
- Modify: `root/tests/test_profile_conflicts.py`
- Modify: `root/services/profile_api/tests/test_profiles.py`

**Interfaces:**
- `RemoteProfileHead.created_revision` and `.accepted_revision` are proof that the exact create/progression request was accepted; the returned head may be newer and is its authoritative descendant.
- Installing a fetched/returned remote head uses its actual `client_save_id`; it must not mint a local save ID for a remote-authored revision.
- `RemoteProfileCreationConflict` remains a collision outcome, distinct from an idempotent replay success.

- [x] Add a lost-create-response test: commit initial claim remotely, advance the profile from another device, retry the original claim, and assert marker-based clean fast-forward to the newer head and its actual save ID, with no conflict sidecar.
- [x] Add a lost-progression-response test: accept a pending progression remotely, advance again from another device, retry the original progression, and assert `accepted_revision` causes clean fast-forward to the current descendant head without conflict.
- [x] Add tests proving a real creation `409` remains a collision even when the current head payload coincidentally equals the local payload, and a fork UUID collision never adopts that unrelated remote profile. Assert the source local profile remains intact; allow `fork_local(new_profile_id, ...)` from a pending unclaimed profile after a claim collision so the same branch can be cloned under a fresh UUID for a later cloud claim.
- [x] Fix `MemoryRemoteProfileServer` idempotency bookkeeping to key accepted requests by `client_save_id`, then compare payload digest, matching the service's `(profile_id, client_save_id)` uniqueness contract. Add same-ID/different-digest rejection coverage.
- [x] Add a real profile-service replay-after-head-advance test: create revision 1, accept save A as revision 2, accept save B as revision 3, then replay save A. Require `accepted_revision == 2`, `current_revision == 3`, and the returned head payload/save ID to remain revision 3. Also retain the existing real-service idempotency-key-reuse coverage.
- [x] Run the new client tests and the real-service replay/idempotency tests; confirm marker replay and collision cases distinguish proven ancestry from payload coincidence.
- [x] Implement the client decisions using the server markers, install the validated current descendant head as `CLEAN`, and preserve the head's actual `client_save_id`. Keep a true claim/fork collision pending and retryable only under a fresh profile UUID; never bind the attempted UUID to an unrelated existing remote profile. Do not modify the API contract or database schema.
- [x] Run client sync/conflict tests and profile-service replay/idempotency tests. The full PostgreSQL profile-service suite is run once, cumulatively, in Task 5 as required by the global qualification order.

### Task 4: Serialize Identity Recovery Decisions

**Files:**
- Modify: `root/services/profile_api/src/profile_api/app.py`
- Modify: `root/services/profile_api/src/profile_api/identity.py`
- Modify: `root/services/profile_api/tests/test_auth_sessions.py`
- Modify: `root/services/profile_api/tests/test_postgres_concurrency.py`
- Modify: `root/services/profile_api/tests/test_identity.py` only if focused serial coverage is needed.

**Interfaces:**
- Identity link/unlink recovery decisions acquire the owning `Account` row lock before reading or mutating linked identities. Session revocation acquires the same account lock before removing a refreshable session. Unlink then locks the selected identity and evaluates other identities plus refreshable sessions inside the same transaction, using a stable account-then-child-row lock order.

- [x] Add a PostgreSQL-only concurrency test with two linked identities, all refreshable sessions revoked, and two simultaneous unlink attempts. Assert one succeeds, one raises/returns `IdentityRecoveryRequired`, and at least one identity remains.
- [x] Add a PostgreSQL-only concurrency test racing unlink of the last identity against revocation of the last refreshable session. Assert the account never commits without either recovery path.
- [x] Run the focused tests against the dedicated PostgreSQL test database with synchronized starts. The invariant tests must pass repeatedly; do not require a probabilistic reproduction on every run to establish the current race.
- [x] Lock the active account row before identity-recovery checks and identity link/unlink operations; take the same account lock before session revocation. Preserve existing verified-identity and unique-provider-subject rules.
- [x] Preserve successful session revocation when another verified recovery identity exists, and reject revocation of the final recovery session; verify both outcomes in the service tests.
- [x] Run identity unit tests and the PostgreSQL concurrency test repeatedly; also run the full profile-service PostgreSQL suite.

Identity unit and session tests pass. The three PostgreSQL concurrency tests passed on three consecutive runs (3 passed per run). The full profile-service suite passed with 25 tests; the PostgreSQL migrations and immutable-revision triggers were exercised.

### Task 5: Cumulative Qualification and Closure Evidence

**Files:**
- Modify: `docs/current/save/save-r1-plan.md` to record qualification results and closure evidence in place.
- No production wire-schema or migration-contract changes are authorized in R1. If any earlier task proves such a change is required, stop and revise the plan before continuing.

- [x] Run client tests from `root/`: 1,556 passed using `python -m pytest --basetemp=..\.pytest-tmp-r1-review tests -q`. The sibling scratch directory keeps nested fixture projects outside `root/pyproject.toml` discovery.
- [x] Run web tests from `root/`: 44 passed; build with `python tools/build_browser_site.py --output web/dist` reported 132 runtime files; Playwright browser smoke against the built site passed the full route, semantic round-trip, multi-target, result-to-Overworld, Drifter sprite selection, and responsive viewport checks.
- [x] Run content validation and compilation from `root/`: validation passed (5 enemies, 4 weapons, 4 drifters, 8 encounters, 1 route). Compilation passed for `src`, `tests`, `tools`, and Python web-test sources; stale generated content under `web_tests/.pytest_cache` was excluded and left untouched.
- [x] Run `python -m pytest tests` from `root/services/profile_api/` with `PROFILE_API_TEST_DATABASE_URL` pointing to a dedicated PostgreSQL database and `PROFILE_API_MIGRATION_TEST_DATABASE_URL` pointing to a separate clean migration database: 25 passed. Set `DATABASE_URL` to the dedicated migration database, run `python -m alembic upgrade head` and `python -m alembic check`; upgrade succeeded and check reported no drift. Existing immutable-revision trigger coverage passed.
- [x] Launch the actual pinned MicroPython 1.29.0 Windows executable through the existing sealed qualification matrix command below (replace the executable path only if the local pinned build is elsewhere). Do not modify the sealed probe/bootstrap/heap-sweep/matrix tooling to make the run pass:

```powershell
.\.venv\Scripts\python.exe root\tools\runtime_qualification_matrix.py `
  --python .\.venv\Scripts\python.exe `
  --micropython "$env:LOCALAPPDATA\DungeonDrifters\micropython\v1.29.0\source\ports\windows\build-standard\micropython.exe" `
  --probe root\tools\micropython_probe.py `
  --bootstrap root\tools\micropython_probe_bootstrap.py `
  --source root\src
```

  Require raw/default probe, route, semantic parity, 448K three-run stable pass, and 416K lower-pressure confirmation. Record executable identity and observed memory values; synthetic `MYP|...|PASS` fixtures do not count. If 448K fails even once, 416K passes even once, the semantic signature changes, or the existing qualification tooling/probe contract would need modification, stop and investigate rather than revising the sealed boundary inside R1.
- [x] Run `git diff --check`; verify schema 8, envelope 1, `/v1`, PostgreSQL migration shape, and SAVE-ARCH-0..7 history are unchanged.
- [x] Record exact observed test totals, MicroPython version/platform, heap outcomes and telemetry, then commit as `SAVE-ARCH-R1 - Harden Sync Recovery, Replay Semantics, Identity Concurrency, and Runtime Portability`.
- [x] After push, require every workflow for the exact R1 SHA to complete successfully; report the exact SHA and links. All required workflows passed for `3a127f7303fdddf5b8d218524e67dae548b2e0f8`.

Final qualification evidence:

- Client: 1,556 passed. Web: 44 passed. Browser full-route/responsive smoke: pass. Content validation: pass. Source/test compilation: pass. Static site build: pass, 132 runtime files.
- Runtime matrix: CPython 3.14.6 and MicroPython 1.29.0 on `win32`; raw/default probe, route, and semantic parity passed. The pinned executable is 488,960 bytes with SHA-256 `6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA`.
- Heap measurements below are `gc.mem_free()` / `gc.mem_alloc()` bytes from the sealed probe. At 448K, all three runs passed: boot `396144 / 52048`; lowest free `37648-37696`; highest allocated `410496-410544`; final `37744-37792 / 410400-410448`; after evidence release `61760-61808 / 386384-386432`; after teardown `63840-63888 / 384304-384352`.
- At 416K, all three runs confirmed `MemoryError`: boot `364144 / 52048`, lowest free `50608`, highest allocated `365584`; final/evidence-release/teardown stages were not reached.
- PostgreSQL qualification used an isolated PostgreSQL 17 Docker container with dedicated service-test and clean-migration databases. The three concurrency tests passed on three consecutive runs; the complete service suite passed (25 tests), including immutable-revision trigger coverage. A clean `alembic upgrade head` succeeded and `alembic check` reported no drift.
- After the late Keep Local review fixes, reran the actual pinned MicroPython matrix against clean commit `3a127f7303fdddf5b8d218524e67dae548b2e0f8`: `MYP20|RESULT|CLOSURE_COMPLETE`, semantic parity passed, 448K was stable pass 3/3, and 416K memory limit was confirmed 3/3. The final source tree therefore has direct runtime evidence, not only the earlier pre-review run.
- Exact-SHA GitHub workflows for `3a127f7303fdddf5b8d218524e67dae548b2e0f8`: [Tests and PostgreSQL](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/38485392919), [GitHub Pages](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/38485393047), and [CodeQL](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/38485392722) all succeeded.
- `git diff --check`, schema 8, envelope 1, `/v1`, unchanged migration shape, and intact SAVE-ARCH-0..7 history were verified. The disposable PostgreSQL test container was isolated from the user's other Docker projects and removed after qualification.
- Final self-review found that `resolve_use_remote()` still minted a local `client_save_id` when installing a remote-authored head. The existing Use Remote regression was strengthened, observed failing on the mismatched ID, then passed after routing the transition through the validated remote-head installer. A subsequent review found two missed Keep Local cases: a replay accepted before a later remote descendant was incorrectly recorded as a new conflict, and a matching remote payload authored under a different save ID retained the local ID. Both focused regressions failed before the correction and passed afterward. Keep Local now archives the local branch/evidence, installs the authoritative current head and its actual save ID, then clears conflict residue. The complete client suite passed after these corrections: 1,556 passed in 236.11s. Review was performed inline in accordance with repository conventions; no agent delegation was authorized.

## Completion Boundary

R1 changes no game-state/envelope/API versions and adds no new gameplay or account architecture. Local implementation qualification is complete once the corrective tasks pass their focused tests, the full existing suites and actual pinned MicroPython matrix are green, PostgreSQL concurrency has been exercised, and exact observed evidence is recorded. Persistence closure additionally requires an authorized push and green required workflows for that exact correction SHA; neither is claimed before then.

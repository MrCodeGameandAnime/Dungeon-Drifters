# Dungeon Drifters: M4A Diff Review Corrections

**Review target:** `dungeon` branch, cumulative head `b57ca41fec21988718605b211e56e7a6a5950ce0`  
**Review date:** 2026-11-06  
**Scope:** Seven M4A commits (M4A-1 through M4A-6), focusing on the Floor II run/event, combat, persistence, and settlement boundaries.  
**Review type:** Targeted static code inspection, not a complete line-by-line audit or runtime reproduction of the findings below.

## Verification already established

The [exact-SHA GitHub Actions run](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42273495771) was green for the **cumulative tree** containing all seven commits. It recorded **2,084 root Python tests**, **66 web tests**, **39 PostgreSQL tests**, a **161-file browser build**, built-browser smoke including the Floor II boss clear, and successful migration/Alembic checks. This does **not** establish that the intermediate commits independently passed, nor does it replace the **real pinned MicroPython qualification** required for M4A closure.

The following items are **review findings requiring fail-before reproduction**, except the documentation staleness, which is directly observable. Do not describe an unexecuted regression as a reproduced runtime failure.

## Corrections

### M4A-R1: Validate authored discovery and event references at the save trust boundary

**Priority:** Medium  
**Status:** Potential acceptance gap identified by source inspection; reproduce first.

**Code locations:**

- [`_validate_world()`](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/blob/b57ca41fec21988718605b211e56e7a6a5950ce0/root/src/app/persistence/save_document.py#L1744-L1798)
- [`_run_event()`, `_validate_run_event_result()`, and `validate_run_event_history()`](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/blob/b57ca41fec21988718605b211e56e7a6a5950ce0/root/src/app/game/party_state.py#L994-L1180)
- [`RunEventService.search_discovery()`](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/blob/b57ca41fec21988718605b211e56e7a6a5950ce0/root/src/app/game/run_events.py#L180-L266)

**Observed:** The service checks that the proposed discovery matches authored catalog content. The save validators shown above accept discovery source IDs and run-event node IDs primarily by **string-shape rules**. Their local checks do not prove those IDs exist in the authored catalog or that a saved discovery event points to the correct authored Floor II node. Event-history validation checks event keys, roll consistency, and matching drop totals, but not all authored/world-state relationships.

**Required correction:**

1. Add a **failing profile-payload validation test** using a syntactically valid but unknown discovery `source_id`, including world discovered/claimed lists and a discovery-search event where applicable. Confirm whether it actually passes the existing trust boundary before changing code.
2. Add a failing test for a syntactically valid but unauthored Floor II event `node_id`, with otherwise self-consistent event key and history.
3. Reject unauthored IDs, wrong source/node associations, and contradictions between successful discovery evidence and durable discovered/claimed state **at the current schema-18 boundary**, before reconstruction. Where applicable, verify a searcher ID belongs to the recorded active/eligible roster.
4. Preserve historical save support: do **not** retroactively invalidate valid older revisions if the authored catalog changes; use a compatible historical ID policy when necessary.
5. Test rejection via `validate_profile_payload()` and the normal disk/reconstruction path. Valid existing Floor II saves and immutable legacy revisions must remain accepted.

**Acceptance:** Invalid current-schema references fail closed with no partial mutation; valid records still round-trip; historical digests/revisions remain intact.

### M4A-R2: Restore the entire encounter-local resource state after a failed reward commit

**Priority:** High  
**Status:** Likely rollback gap identified by source inspection; reproduce first.

**Code locations:**

- [`Battle` consumes carried supplies](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/blob/b57ca41fec21988718605b211e56e7a6a5950ce0/root/src/app/combat/battle.py#L815-L825) and [healing potions through `PartyState`](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/blob/b57ca41fec21988718605b211e56e7a6a5950ce0/root/src/app/combat/battle.py#L954-L974)
- [`_finalize_floor_two_battle()` failed-commit branch](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/blob/b57ca41fec21988718605b211e56e7a6a5950ce0/root/src/app/game/overworld_session.py#L2110-L2152)
- [Existing Floor II commit test](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/blob/b57ca41fec21988718605b211e56e7a6a5950ce0/root/tests/test_floor_one_run.py#L633-L682)

**Observed:** A healing potion mutates shared carried inventory during battle. If persisting the victorious encounter reward fails, `_finalize_floor_two_battle()` restores **Drifter battle checkpoints** and offers a retry. The shown failure branch does not restore the **party inventory** spent during that failed attempt. This can leave the in-memory retry state inconsistent with its pre-battle checkpoint or the durable save.

**Required correction:**

1. Write a deterministic failure-injection test: begin Floor II combat with a carried healing potion, use it, win, force the encounter-result save to fail, and assert the Drifter state **and** relevant shared carried supplies return to a consistent pre-attempt checkpoint.
2. Capture an encounter-local checkpoint that includes party resources changed by combat, not only member HP/mana. Restore it on a failed transaction before exposing `RETRY`. Do not rewind earlier committed encounter rewards, roster recruitment, or unrelated progression.
3. Test a normal successful save: consumed supplies remain consumed exactly once and the committed rewards/event evidence match the saved state.
4. Test repeated failed-save/retry attempts and a subsequent success for no resource loss, minting, or duplicate rewards.
5. Keep the established gameplay-save success rule: **later sync/network bookkeeping failure must not retroactively invalidate an already successful local gameplay save**.

**Acceptance:** The retry state, durable state, consumed resources, and event evidence are mutually consistent after both failed and successful encounter commits.

### M4A-R3: Recover a saved boss victory by retrying settlement, not the boss battle

**Priority:** Medium  
**Status:** Confirmed fallback behavior in source; require a deterministic recovery test.

**Code locations:**

- [`_finalize_floor_two_battle()` boss completion](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/blob/b57ca41fec21988718605b211e56e7a6a5950ce0/root/src/app/game/overworld_session.py#L2152-L2181)
- [`RunEventService.resolve_encounter_rewards()` idempotent existing-event path](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/blob/b57ca41fec21988718605b211e56e7a6a5950ce0/root/src/app/game/run_events.py#L52-L101)

**Observed:** Boss victory first persists the encounter reward/evidence, then attempts a **second save** for boss settlement and Hub return. If the second save fails, the game retains the first committed state and explicitly asks the player to **retry the final encounter**. That re-fight is unnecessary once the durable victory evidence exists, even though the event key appears designed to prevent duplicate payouts.

**Required correction:**

1. Add a deterministic test where the boss reward/event save succeeds but the **Hub-settlement save fails**.
2. Verify the last durable state has one boss-clear event record and one pending reward set, with no already-banked duplicate payout.
3. Prefer an idempotent **`Finalize Floor II Clear` / settlement-retry** path derived from the saved boss-victory evidence, rather than requiring another combat victory. Reusing the existing settlement logic is preferable to inventing a second reward owner.
4. Test both same-session retry and save/reload recovery. A successful retry must settle XP/gold/items **once**, clear the active Floor II run, restore the recruited party, and return to Hub.
5. If re-fighting after a committed boss outcome is intentionally retained, explicitly document that behavior and prove its no-duplication and deterministic recovery semantics; do not leave it accidental.

**Acceptance:** A committed boss victory survives failure of the later settlement save and can be completed without duplicate rewards or an invalid state.

### M4A-R4: Update the checkpoint evidence, then run remaining qualification

**Priority:** Documentation/qualification  
**Status:** Confirmed stale checkpoint text; pinned runtime remains open.

**Code location:** [`m4-floor-ii-implementation.md`, M4A-6 and M4A closure](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/blob/b57ca41fec21988718605b211e56e7a6a5950ce0/docs/current/milestones/m4-floor-ii-implementation.md#L155-L185)

The committed plan says that hosted CI and PostgreSQL/migrations have **not** run, but they **have** run successfully for `b57ca41...`. Update the evidence record with the exact SHA, run URL, totals, browser markers, and migration/Alembic result. Keep **pinned MicroPython** open until the real prescribed executable/matrix, semantic parity, and heap-frontier evidence are recorded. If R1–R3 produce a new commit, run the required final cumulative checks **on the new accepted SHA**, rather than using `b57ca41...` CI to qualify changed code.

## Proposed implementation order

1. Reproduce **R2** with a failing combat/save rollback regression; patch and verify.
2. Reproduce **R1** with malformed but syntactically valid save payloads; patch only demonstrated gaps.
3. Add **R3** two-stage boss-save failure/reload coverage; improve settlement recovery if confirmed.
4. Execute the focused suites, full Python/web tests, content checks, browser build and smoke, real PostgreSQL/migrations, and the **pinned MicroPython** matrix.
5. Update **R4** evidence and close M4A only when the final accepted tree meets its documented criteria.

## Out of scope

No rebalance, new Floor III content, M4B, M5 implementation, persistence-provider redesign, new save envelope/API version, unrelated refactor, or reopening sealed Floor I behavior without a reproduced regression.

**Review conclusion:** Cumulative hosted CI is green, but that is not an automatic M4A seal. R1 and R2 are specifically **code-inspection risks pending red tests**; R3 is an observable recovery UX/transaction design issue; R4 is a qualification record update. Close demonstrated defects with fail-before/pass-after evidence and qualify the resulting exact SHA.

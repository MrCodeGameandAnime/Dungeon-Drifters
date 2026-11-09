# M4A Floor II Implementation Plan

> Implementation method: execute this plan gate by gate on the existing `dungeon` branch. This document records the approved M4A party-size correction; it does not authorize unrelated M4B scope.

**Status:** The original M4A implementation and qualification are complete on `a0aaa53d0a31d6d09c95bade188a5e76a3b822ba`; that evidence remains valid only for unaffected behavior. The 2026-11-09 Floor II/III party revision is hosted-qualified on exact SHA `0aa4ecd5c15013af9c1456db8a53ada50e58357b` in [GitHub Actions run 42704099577](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42704099577). A subsequent review approved corrections to recruitment timing, Rest-only helper selection, and Floor II replay eligibility. M4A is reopened pending implementation and exact-SHA requalification of those corrections. The implementation baseline reported at entry was `a64f4461c606dc88698fa45138d5f8a89a231868`.

### Local Review Checkpoints

The implementation is split into these reviewable commits on the existing `dungeon` branch. M4A-3 and M4A-4 share the party/session/persistence transaction boundary and are intentionally one commit; browser integration is separate. The hosted run below qualifies the cumulative baseline at `b57ca41`; the intermediate commits were not independently qualified.

| Gate | Commit | Scope |
| --- | --- | --- |
| M4A-1 | `dcacc08` | Tier I enemy profiles, authored data, and catalog validation |
| M4A-2 | `c3ddac5` | Identity modifiers and the cave-in response |
| M4A-3 / M4A-4 | `6377eb4` | Historical baseline: persisted Floor II run/events, route, midway D3 recruitment, rewards, and schema 18 |
| M4A-5 | `70c55c4` | Browser bridge and built-browser Floor II journey |
| M4 checkpoint | `9c6a70e` | Record gate checkpoint and qualification status |
| M4A-5 | `b110923` | Terminal Floor II journey and terminal action-key routing |
| M4A-6 | `b57ca41` | Record cumulative local qualification checkpoint |
| M4A-6 | `fcc97ae`, `a48903f` | Harden Floor II recovery and protect pending boss settlement |
| M4A-6 | `f2f3785` | Extend and qualify the pinned MicroPython Floor II probe |
| M4A corrective review | `a0aaa53` | Historical correction: bounded settled run-event evidence and permanent-recruit catch-up (now superseded) |

The original cumulative baseline was qualified by [GitHub Actions run 42273495771](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42273495771) on exact SHA `b57ca41fec21988718605b211e56e7a6a5950ce0`: 2,084 root tests, 66 web tests, and 39 PostgreSQL tests passed, with migration/Alembic checks and the 161-file browser build. This is historical baseline evidence; final qualification is recorded below.

### 2026-11-09 Party Revision - Local Status

Implemented and qualified: the scripted pre-boss D3/D4 helper choice, persisted selection, three-member Floor II boss composition, pair-only boss XP, independent Level 1 Hub recruitment for 65 gold, atomic underfunded retry, browser/terminal controls, runtime/disk schema 21/22 migration, and the updated pinned-runtime probe. Exact-SHA hosted CI passed **2,240 root tests**, **72 web tests**, and **47 PostgreSQL tests**; content validation, compileall, the **172-runtime-file browser build**, complete Playwright smoke (including helper save/reload, Hub recruitment, and Floor II boss clear), migration-from-zero, and Alembic parity also passed in [run 42704099577](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42704099577). The exact pinned MicroPython matrix passed locally on the same source tree: native/forced-overlay CPython, default MicroPython, semantic parity, 1152K stable 3/3, 1024K expected memory-limit classification 3/3, with final marker `MYP20|RESULT|CLOSURE_COMPLETE`.

The M4A party revision is hosted-qualified on the exact pushed SHA above. The pinned MicroPython matrix is local evidence; the hosted workflow does not execute that binary. M4B remains a separate future implementation gate and is not claimed complete by this Floor II correction.

### 2026-11-09 Diff-Review Corrections

The approved correction contract is:

- D3/D4 Hub recruitment is unavailable until `floor_two_cleared` is true. Both recruits remain independently available for 65 secured shared gold and start at Level 1.
- The temporary helper must be selected at `floor_two_pre_boss_rest`; continuing without a selection is blocked. The boss node never opens helper selection, and persisted helper evidence must reference the Rest.
- On a cleared Floor II replay, at least one of D3/D4 must be outside the active pair. Disable Start Floor 2 at the Hub with an actionable reason and reject direct attempts before any outing state changes. The restriction is Floor II replay-specific; D3+D4 remains a legal pair for other content.

The implementation and exact-SHA qualification for these review corrections are pending.

### Review Corrections And Final Qualification

The review corrections address the three findings:

- **R1:** Validate current schema-18 discovery sources, route-node references, source/node associations, active searchers, and durable discovery evidence while retaining known historical source IDs for older saves.
- **R2:** Restore the encounter-local carried-supply checkpoint when a victorious Floor II reward save fails, without rewinding earlier committed progress.
- **R3:** Recover a persisted Floor II boss victory through an idempotent settlement action rather than requiring a boss refight, including same-session retry and reload. Return Talisman is unavailable and rejected while boss settlement is pending, leaving finalization as the only resolution.
- The browser smoke's discovery-bonus lookup now keys Drifters by canonical profile choice; the save profile does not expose a `drifter_id` field there.

The corrections and talisman guard are hosted-qualified on exact SHA `a48903f2456adff075a00453fb43c79449a5e0c3` in [Actions run 42296351933](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42296351933). The final M4A-6 code commit is `f2f378563d96bf94e9dd37b57e9238665f32e2b1`; [Actions run 42305392988](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42305392988) passed on that exact SHA. Hosted results: **2,102 root tests**, **66 web tests**, and **39 PostgreSQL tests** passed; content validation and compile passed; migration-from-zero and Alembic parity passed (`No new upgrade operations detected`); the **161-file browser build** and complete headless browser smoke passed through `M4_BROWSER|FLOOR_TWO_BOSS_CLEAR|PASS`.

**Goal:** Add authored enemy Tier 1 behavior and a bounded, replayable Floor II route with the revised temporary boss helper, independent Hub recruitment for D3/D4, Grade-II materials, persisted search/drop outcomes, and one counterable environmental threat without changing sealed Floor I behavior.

**Architecture:** Extend the existing enemy/content catalogs, combat resolver, party/run state, route/session, persistence, and semantic presentation owners. Keep all rules Python-authoritative and preserve existing Floor I behavior through explicit regression tests. Persist resolved event outcomes; do not add live-battle save snapshots.

**Tech stack:** Existing Python domain/content/session/persistence and terminal/browser clients, authored catalog generation/validation, pytest, Playwright, and the pinned MicroPython qualification.

**Authority:** [M4 decisions](m4-enemy-progression.md), [M1 roster](m1-permanent-roster.md), [M2 supplies and exit rules](m2-preparation-trading-escape.md), [M3 advancement/discovery](m3-character-advancement.md), and [weapon components/materials](../weapons/component.md).

## Scope

This plan covers M4A only:

- Tier 0 remains byte-for-byte equivalent in authored combat outputs; Floor II requests authored Tier 1 enemies.
- Enemy rank/archetype/tier/capability remain separate. Tier changes numeric authored stats only; it does not add moves, capabilities, healing, Defend, Super, or automatic reward multipliers.
- Elemental/alchemical resistance and weakness use identity multipliers only. They do not add defense stats, immunity, or a new mitigation class.
- Existing enemy move selection remains random among legal affordable moves; target selection remains random among living active Drifters.
- Floor II has ten battles, a midway Rest after battle 5, a pre-boss Rest after battle 9, and the boss at battle 10.
- The midway Rest does not recruit D3. At the pre-boss Rest, the player chooses D3 or D4 as a temporary helper for the Floor II boss only and must record that choice before continuing. Permanent D3/D4 Hub recruitment for 65 secured shared gold each, at Level 1, unlocks only after Floor II clear.
- Floor II is the first source of Grade-II Metal, Fiber, Timber, and Cores. Use the existing generic Grade-II weapon-improvement recipes; do not add alternate component storage or replace the sealed weapon system.
- One telegraphed physical cave-in uses existing Brace/Defend as its counter. No status effects, injuries, durability, formations, or boss phases.
- Discovery search and enemy-drop outcomes are authored, resolved at their event boundary, and persisted so reloads or repeated inputs cannot reroll or duplicate them.
- Preserve the approved floor-local replay XP schedule: initial clear at 100%; after that, 50%, 40%, 30%, then 20% minimum on later runs. Gold does not dwindle. Do not change Floor I's route or payout behavior.

Out of scope: Floor III content and four-Drifter combat (M4B), formations, boss phases, new enemy archetypes unless existing content cannot fulfill a required role, rebalancing sealed systems, broad discovery placement, or any M6 expedition work.

## Approved Floor II Contract

```text
Hub, after Floor I boss clear
  -> choose Floor I replay or Start Floor II
  -> keep the currently selected two-member active pair
  -> on Floor II replay, leave at least one of D3/D4 outside the active pair
  -> Floor II battles 1-5
  -> Midway Rest: Recover / Continue / Extract
  -> Floor II battles 6-9
  -> Pre-Boss Rest: Recover / Continue / Extract, Search site, and scripted D3/D4 helper choice
  -> Floor II boss (battle 10): active pair plus the selected temporary helper
  -> eligible boss rewards (Floor II XP goes only to the active pair), restore party, return to Hub
  -> independently recruit D3 and/or D4 for 65 shared gold each; each permanent recruit starts at Level 1
```

The Floor II route uses M2's existing payout semantics: Rest extraction banks 50% of already-adjusted XP and gold and all pending items; Return Talisman banks 100% of already-adjusted XP only; boss clear banks all eligible rewards; death loses unsecured XP/gold/items and carried supplies, returns the recruited roster fully restored, and cannot rewind through a Rest save. Continue remains available after Rest recovery.

At the pre-boss Rest, D3 and D4 offer to help with the Floor II boss. The player selects one helper. The helper is included only in that battle: they do not join the permanent roster, alter the active pair, receive XP, or carry any battle-only progression forward. Construct the temporary helper at the lower active Drifter's level using normal level-derived HP/Mana growth and the helper's authored kit/base signature weapon. Distribute the Growth Points earned by catch-up as evenly as possible across all six stats; handle any remainder deterministically. Persist the helper selection across supported Rest save/reload so it cannot produce duplicate battle participants or a partial transition. Keep the Floor II boss XP recipient set equal to the regular active pair; split secured XP between those two, then apply each member's own Intuition bonus independently.

The player cannot continue from the pre-boss Rest until the helper choice is recorded; helper selection is never offered at the boss node. After Floor II has been cleared, a replay can start only if the active pair leaves at least one of D3/D4 available as a temporary helper. This is checked at Hub entry before the outing begins, is recoverable by changing the pair at the Hub, and does not restrict D3+D4 as an active pair for Floor I or other content.

After returning to the Hub following Floor II clear, D3 and D4 are independently recruitable for exactly 65 secured shared gold each, regardless of which one helped. Permanent recruits start at Level 1 with their authored starting state; do not carry over temporary level, GP allocation, XP, or other temporary battle state. An insufficient-gold attempt changes nothing and remains retryable. Preserve the existing Floor II replay/gold path so recruitment affordability cannot softlock progression. Floor III's four-member boss requires the four permanent roster members; do not substitute the temporary Floor II helper for permanent recruitment.

## Authored Initial Values

These are tunable first-pass content values, not locked balance targets:

- Enemy tier: Tier 1 on Floor II, with per-archetype authored stat adjustments. No reward multiplier is inferred from tier.
- Identity multiplier: matching elemental/alchemical resistance uses 75%; weakness uses 125%. Apply after generic mitigation and physical-only Strength negation, before Brace/Defend, using the approved component rounding behavior. A component may resolve to zero; do not add an immunity result.
- Discovery: each source authors its own base chance. The first Floor II searchable source starts at 1,000 basis points (10%). Calculate `effective = min(10_000, base + floor(base * discovery_bonus_bps_from_intuition(searcher.effective_stat("intuition")) / 10_000))`. The selected searching Drifter must be in the active pair. No party average. This Intuition modifier applies to discovery searches only; enemy item-drop entries use their authored odds without an added Intuition modifier.
- Item drops: each authored drop entry has its own chance and quantity. Initial Grade-II common-material drop entries use 2,000 basis points (20%); Grade-II Core entries use 1,000 basis points (10%). Values live in content and are tunable; no rare drop is guaranteed.
- Search fixture: one authored Floor II source at the pre-boss Rest, `ancient_well_floor2_01`, granting its authored +5 max HP under the existing M3 claim flow. Broader source placement remains outside M4A.
- Cave-in: one authored encounter warning, one physical damage component using the existing physical defense path, and one resolution at the designated encounter's next existing enemy-action boundary. Use the existing living-target selection and Brace/Defend resolution; author the initial damage conservatively in encounter content. Do not create a general-purpose hazard framework or new action timing model.

## State And Persistence

Historical M4A entry versions were runtime snapshot schema 16 and disk schema 17; the original M4A-3 advanced them to 17/18. At the reported current baseline, the repository is runtime schema 20/disk schema 21; re-read actual constants at implementation entry. The helper choice must persist across supported Rest save/reload. Add a deliberate schema/migration change if the current shape cannot represent it; preserve immutable history and do not change the profile API, envelope version, or database schema without separate approval.

- `PartyState` owns the active run identity, floor-two clear/replay state, pending run rewards, and run-scoped resolved event outcomes.
- `WorldState` owns globally found/claimed permanent discovery source IDs. Use the existing M3 permanent-discovery claim service and preserve its atomic reward/claim contract.
- Give each event a stable idempotency key derived from floor/run identity, route node, event kind, and (for drops) enemy instance position. A genuine later run gets a new run identity; a repeated submit in the same run gets the stored result.
- At enemy victory, resolve all item-drop entries once, atomically apply the encounter rewards and event record, then present the result. At confirmed search, resolve once, persist the result, and reveal the source if found. A canceled claim does not consume it.
- Persist the resolved result at the authoritative boundary before acknowledging success. Failed persistence must not leave reward without evidence, evidence without reward, or a success message for an uncommitted outcome. Rest saves remain checkpoints; this does not enable saving a live battle.
- Schema-16/runtime and schema-17/disk documents migrate with no Floor II clear, zero Floor II replay runs, no active Floor II run/outcomes, and no fabricated discoveries. Preserve every existing field and historical profile revision/digest.
- Reject impossible states: Floor II cleared before Floor I, active Floor II without the required Floor I unlock, duplicate/malformed event keys, unknown discovery IDs, invalid item/quantity/chance data, and helper selection that is unknown, stale, duplicated in the boss party, or detached from its active Floor II run. Rejection occurs before reconstruction or partial mutation.

## File Ownership Map

Reconfirm exact call sites at implementation entry; do not create parallel owners.

| Responsibility | Existing owner(s) to extend |
| --- | --- |
| Tier values, resistances, encounter drops | `root/src/app/content/enemy_spec.py`, `encounter_spec.py`, `catalog.py`, `root/src/app/enemies/definition.py`, `state.py`, `validation.py` |
| Authored Floor II route, temporary boss helper, and Hub recruitment | `root/src/app/content/route_spec.py`, `routes/`, `encounters/`, recruitment content/catalog owners, and their validation tools |
| Tier validation and generated content checks | `root/tools/validate_content.py`, `root/tools/generate_content_catalog.py`, `root/tests/test_enemy_content.py`, `test_route_content.py`, `test_recruitment_event_content.py`, `test_content_tooling.py` |
| Combat identities and cave-in response | `root/src/app/combat/resolver.py`, `battle.py`, `combat_state.py`, existing Brace/Defend owners and focused combat tests |
| Route launch, settlement, replay, recruitment and search | `root/src/app/game/party_state.py`, `overworld_state.py`, `overworld_session.py`, `recruitment.py`, `permanent_discovery.py`, `world_state.py`, `story_state.py` |
| Save versioning and trust boundary | `root/src/app/snapshot.py`, `root/src/app/persistence/save_document.py`, migration and profile-service historical-fixture tests |
| Terminal/browser actions and visible outcomes | Existing overworld presenter/models, terminal UI/runtime, `root/web/python/dd_bridge.py`, browser renderer and `root/web_tests/browser_smoke.mjs` |
| MicroPython route proof | `root/tools/micropython_probe.py`, shared route probe and runtime qualification tests |

## Implementation Gates

### M4A-1: Enemy Tier Data And Catalog Validation

- [x] Add failing tests that pin the current Tier 0 stats/moves/rewards for all five existing archetypes and reject bool, negative, unsupported, duplicate, or malformed tier data.
- [x] Add per-archetype Tier 1 numeric values in the existing authored enemy content model. Tier 1 creation must be deterministic; it must not change archetype ID, rank, role, behavior, capabilities, or move list.
- [x] Replace the current `(0,)`-only validation in `EnemySpec` and `root/tools/validate_content.py` with the approved authored tier policy. Keep Tier 2 content deferred to M4B.
- [x] Prove fresh `EnemyState` instances created from one definition do not share HP, Mana, or Super mutation; retain separate-`CombatState` status isolation at its owning encounter boundary.

Proof: the tiered fresh-instance test covers independent HP, Mana, and Super resources; separate-`CombatState` tests cover encounter-scoped status isolation. Tier 0 golden outputs remain unchanged. Local verification on Python 3.12.14: 183 focused enemy/content/tooling tests and 44 combat-state/status tests passed; content validation passed (`5 enemies, 4 weapons, 4 drifters, 10 encounters, 2 routes, 1 recruitment_event`); generated dataclass manifest check passed (144 entries); `git diff --check` passed. Pinned MicroPython and cumulative hosted qualification remain in M4A-6.

### M4A-2: Identity Resistance And Cave-In Counter

- [x] Add focused component tests for matching elemental/alchemical resistance (75%), weakness (125%), unrelated identity (100%), no immunity, and preserved physical/magical generic mitigation.
- [x] Apply the identity multiplier in the approved M3 component order, after generic mitigation and Strength physical negation, before Brace/Defend; use existing per-component rounding and zero floor.
- [x] Add the one Floor II telegraphed cave-in to an authored encounter. Display the warning before its response window and resolve it once through the existing physical/Brace/Defend path.
- [x] Test that a rejected/invalid action does not consume its turn/resource or advance the hazard; the hazard resolves once at the battle boundary. Live battles remain unsaveable, so there is no mid-hazard reload path.
- [x] Keep enemy AI move and target choice unchanged; retain coverage for legal-affordable move selection and living active targets without introducing new behavior policies.

Proof: deterministic resolver/Battle tests show the component identity changes only its multiplier and a player can counter the visible hazard with existing actions. Focused combat tests passed (104 tests).

### M4A-3: Run Identity, Drop/Search Outcomes, And Historical Schema 17/18 Baseline

- [x] Add transaction tests for encounter drop resolution and confirmed search: first resolution records the outcome and reward/source; repeated input returns the same result and grants nothing extra.
- [x] Add a run identity and stable event keys to the existing party/run state. A new genuine Floor II run has distinct event keys; reload, UI rebuild, duplicate submit, and Rest checkpoint load do not.
- [x] Implement explicit per-entry drop chance/quantity data and deterministic injected RNG. Roll once at encounter victory, aggregate to unsecured outing items, and persist reward plus outcome evidence atomically.
- [x] Implement one Floor II Rest search using the selected active Drifter's effective Intuition and `discovery_bonus_bps_from_intuition()`. Persist failed and successful results. A failed search can be attempted in a later run; an already found/claimed source cannot be rolled or awarded again.
- [x] Use the M3 permanent-discovery claim transaction for target selection, confirmation, and source claim. Persist the found source separately from claim state so cancel/reload does not lose or duplicate it.
- [x] Bump runtime/disk schemas to 17/18; add migration, exact shape validation, round-trip, malformed-state rejection, source immutability, and current remote-profile advancement tests. Do not change profile API/envelope/database versions.

Historical proof: event outcome, pending reward/source, and durable evidence agree after success; persistence failure leaves no partial committed transaction; pre-M4 saves migrate without changing their old state. Covered by `test_floor_two_run_events.py`, `test_floor_two_run_state.py`, save migration tests, and profile-service history fixtures. Any new helper-selection persistence must be qualified separately against the current schema.

### M4A-4: Floor Selection, Route, Boss Helper, Hub Recruitment, And Settlement

- [x] Add Floor II route nodes for battles 1-5, midway Rest, battles 6-9, pre-boss Rest, and battle 10 boss. The Hub offers Floor I replay or Floor II only after Floor I clear; Floor I route content and payout tests remain unchanged.
- [x] Add floor-two start/clear/replay state. Use the approved floor-local XP replay rates of 100%, then 50%, 40%, 30%, and 20% minimum; do not reduce gold.
- [x] Remove permanent D3 recruitment from the midway Rest while preserving that Rest's recovery/continue/extract behavior.
- [x] Add the scripted D3/D4 choice at the pre-boss Rest. Persist one selected helper across supported checkpoint save/reload; reject stale choices and never duplicate an active Drifter in the boss battle.
- [x] Construct the Floor II boss battle with the two active Drifters plus exactly one temporary helper. The helper matches the lower active level, receives normal level-derived HP/Mana growth, and has catch-up GP allocated evenly across six stats with deterministic remainder handling. Use the helper's authored kit/base signature weapon. Do not mutate roster membership, active IDs, permanent helper progression, or XP.
- [x] Keep Floor II boss XP recipients limited to the regular active pair; split secured XP between them and apply each member's personal Intuition bonus after the split.
- [x] Offer D3 and D4 as independent 65-gold Hub recruits after Floor II return, regardless of helper choice. Permanent recruits start at Level 1; temporary level/GP/XP never carries over. Insufficient gold is atomic and retryable; retain the existing gold-earning/replay path.
- [x] Keep the Floor III four-member boss dependent on permanent recruitment; the temporary Floor II helper cannot satisfy that requirement.
- [x] Author Grade-II sources for all four families, using existing IDs and improvement recipes. No Grade-II materials come from Floor I. Do not add new weapon component variants.
- [x] Preserve Rest Recover + Continue + Extract, Return Talisman, boss eligible non-XP payout, death loss/recovery, carried supply handling, and secured/unsecured separation. Floor II boss clear returns the party to Hub and records the clear once.
- [x] Historical baseline: route cursor, outcome evidence, party, pending rewards, replay counter, original recruitment event, and discovered/claimed state round-trip at supported checkpoints.
- [x] Prove the revised temporary-helper selection and exact three-member boss participant set round-trip at supported Rest checkpoints without duplicating participants or changing permanent party state.

Proof: add full session-flow tests for the pre-boss helper choice and checkpoint round-trip; exact three-member boss composition; no active-pair/roster mutation; no helper XP or progression carry-over; two-member Floor II XP split and personal Intuition; independent Level 1 D3/D4 Hub recruitment at 65 gold with atomic insufficient-funds retry; search/claim, Floor II boss clear, Grade-II rewards, and save reconstruction. Floor I behavior remains unchanged and stays in cumulative regression coverage.

### M4A-5: Terminal/Browser Parity And End-To-End Flow

- [x] Expose the same floor choices, searcher selection, temporary-helper candidates, Hub recruitment choices, blocked reasons, hazard warning, and actual reward results in terminal and browser presenters. Clients submit semantic IDs only; they do not roll or calculate outcomes.
- [x] Historical baseline: presenter/bridge tests cover exact Drifter IDs, unoffered/benched targets, original recruitment offers, duplicate submits, and Rest actions.
- [x] Add presenter/session and bridge tests for the offered D3/D4 temporary-helper choices, stale/duplicate helper submissions, and independent Hub recruitment for each unrecruited Drifter.
- [x] Update and execute the built-browser semantic journey for helper save/reload, three-member boss participation, pair-only XP, and Hub recruitment.
- [x] Update the terminal UI journey to cover the revised helper and Hub recruitment flow through Floor II completion. Keep a separate regression for the unchanged Floor I clear/replay route.

Proof: the terminal journey exercises the actual key mapping and revised helper/recruitment flow, including ten encounters, discovery claim, three-member boss, pair-only XP, and Hub recruitment. The full built-browser smoke passed the same helper save/reload, boss, and Hub recruitment boundaries. Floor I clear/replay remains separately covered.

### M4A-6: Qualification And M5 Handoff

- [x] Baseline: focused M4 selection (492), full root pytest (2,084), and web pytest (66) passed locally; hosted cumulative qualification is recorded for exact SHA `b57ca41fec21988718605b211e56e7a6a5950ce0`.
- [x] Baseline: content validation, compile, generated dataclass manifest check, 161-file browser build, and built-browser smoke passed through `M4_BROWSER|FLOOR_TWO_BOSS_CLEAR|PASS`.
- [x] Baseline hosted profile-service PostgreSQL tests (39), migration-from-zero, and Alembic checks passed in [run 42273495771](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42273495771).
- [x] Pre-commit correction-tree local verification: full root pytest (2,095), web pytest (66), content validation, compile, 161-file browser build, and complete built-browser smoke passed.
- [x] Rerun focused and cumulative qualification for the recovery corrections, including browser smoke and PostgreSQL/migration/Alembic checks.
- [x] Historical pinned MicroPython qualification covers Tier 0/Tier 1 content loading, the original Floor II route/recruitment/drop/search snapshots, teardown, and semantic parity. The formal repeated heap check passed at 1024K (3/3); 944K produced the expected memory-limit classification (3/3). Intermediate heap results varied and are not claimed as a stable frontier.
- [x] Extend the pinned MicroPython probe source for the revised helper, participant composition, Level 1 Hub recruitment, and pair-only Floor II XP attribution.
- [x] Run the pinned MicroPython qualification for the revised helper, three-member participant composition, Level 1 Hub recruitment, and pair-only Floor II XP attribution. The exact pinned executable passed native/overlay CPython, default MicroPython, semantic parity, 1152K stable 3/3, and expected 1024K memory-limit classification 3/3.
- [x] Run `git diff --check` and inspect the final correction diff before commit.
- [x] Preserve the historical accepted code SHA and hosted results here and in the probe record.
- [x] Historical baseline: original M4A closure criteria were met and M5 was unblocked.
- [x] Revised party-size/recruitment contract is implemented locally and has focused regression coverage.
- [x] Push the reviewed implementation and obtain exact-SHA hosted browser/PostgreSQL/migration qualification: run 42704099577 passed on `0aa4ecd5c15013af9c1456db8a53ada50e58357b`.

## Regression And Acceptance Matrix

| Boundary | Required proof |
| --- | --- |
| Tier 0 | All existing authored outputs remain exact. |
| Tier 1 | Only authored numeric stats change; no capability/move/reward inference. |
| Resistance | 75%/125% identity multiplier in the approved component order; no new resistance stat or immunity. |
| Enemy decisions | Existing random legal affordable move and random living active target remain in force. |
| Drop/search | Event outcome resolves once, persists before acknowledgment, and is not rerolled by reload/repeat; a later genuine run has a new event identity. |
| Intuition | Only the selected active searcher affects their search chance via the existing helper; no party average. |
| Discovery claim | Found source persists; claim target is one active Drifter; M3 atomic claim prevents repeat award. |
| Floor II helper | D3 or D4 is selected at pre-boss Rest; only the boss has three participants; helper receives no XP or persistent progression; active pair/roster stay unchanged; saved choice round-trips without duplicates. |
| Hub recruitment | D3 and D4 are independently recruitable for 65 secured shared gold each; each permanent recruit starts at Level 1; insufficient funds changes nothing and retry remains possible. |
| Floor II XP | Only the regular active pair receives the secured-XP split and personal Intuition bonuses. |
| Economy | Rest, talisman, boss, death, and carried supplies match M2; Floor I remains unchanged. |
| Grade gates | Only Floor II yields Grade II; all four families have an authored source; existing weapon recipe machinery is reused. |
| Saves | Historical M4A runtime 17/disk 18 migration remains qualified; the helper choice must round-trip under the current schema with immutable history preserved. |
| Clients | Terminal and built browser share legal actions, result text, and exact-target rules. |

## M4A Closure

The original M4A tree remains historically qualified for its implemented contract. The approved 2026-11-09 party revision is implemented, locally qualified, and hosted-qualified on `0aa4ecd5c15013af9c1456db8a53ada50e58357b`. Existing enemy, hazard, discovery, and Grade-II evidence may be reused only where the corrected flow does not change its boundary. M4A is closed; M4B remains open.

### Post-Review Correction And Final Qualification (2026-11-06)

The post-closure review found three contract issues, corrected without changing the Floor II architecture or save schema:

- Settled Floor II event evidence is cleared at each terminal outcome. A pending boss settlement retains its event evidence until the victory is durably finalized. Loading a legacy settled save validates its recorded events, then discards stale run history so a later active-pair change cannot invalidate the save. Active searcher membership is checked against the participants of the active run, not the currently selected pair after settlement.
- Historical behavior: D3 caught up to the lower active level during mid-run recruitment. This was qualified for the original M4A contract and is now superseded. Under the approved revision, the temporary boss helper is scaled for that battle with evenly distributed GP; permanent D3/D4 Hub recruits start at Level 1.
- The pinned Floor II probe now asserts boss reward/drop evidence before settlement and verifies that settled state no longer retains per-run history.

The correction is committed as `a0aaa53d0a31d6d09c95bade188a5e76a3b822ba` (`M4A: fix event history and recruitment catch-up`). Local verification passed 2,106 root tests, 66 web tests, content validation, compileall, the 161-file browser build, full Playwright smoke through `M4_BROWSER|FLOOR_TWO_BOSS_CLEAR|PASS`, and `git diff --check`. The exact pinned MicroPython v1.29.0 matrix passed native/overlay CPython, default MicroPython, semantic parity, 1024K stable 3/3, and the expected 944K memory-limit result 3/3.

Hosted qualification passed on the exact corrective SHA in [Actions run 42320829998](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42320829998): 2,106 root tests, 66 web tests, browser build and full smoke, 39 PostgreSQL tests, migration-from-zero, and Alembic parity (`No new upgrade operations detected`). The pinned MicroPython matrix is local evidence; the hosted workflow does not execute that binary.

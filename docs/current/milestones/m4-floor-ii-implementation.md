# M4A Floor II Implementation Plan

> Implementation method: execute this plan gate by gate on the existing `dungeon` branch. This document plans M4A only; it does not authorize starting M5 or M4B.

**Status:** M4A implementation and qualification are complete on `f2f378563d96bf94e9dd37b57e9238665f32e2b1`. The Floor II corrections, pending-boss settlement guard, full browser route, PostgreSQL/migration checks, and pinned MicroPython matrix are verified. M5 is next in the roadmap; M4B remains sequenced after M5.

### Local Review Checkpoints

The implementation is split into these reviewable commits on the existing `dungeon` branch. M4A-3 and M4A-4 share the party/session/persistence transaction boundary and are intentionally one commit; browser integration is separate. The hosted run below qualifies the cumulative baseline at `b57ca41`; the intermediate commits were not independently qualified.

| Gate | Commit | Scope |
| --- | --- | --- |
| M4A-1 | `dcacc08` | Tier I enemy profiles, authored data, and catalog validation |
| M4A-2 | `c3ddac5` | Identity modifiers and the cave-in response |
| M4A-3 / M4A-4 | `6377eb4` | Persisted Floor II run/events, route, D3, rewards, and schema 18 |
| M4A-5 | `70c55c4` | Browser bridge and built-browser Floor II journey |
| M4 checkpoint | `9c6a70e` | Record gate checkpoint and qualification status |
| M4A-5 | `b110923` | Terminal Floor II journey and terminal action-key routing |
| M4A-6 | `b57ca41` | Record cumulative local qualification checkpoint |
| M4A-6 | `fcc97ae`, `a48903f` | Harden Floor II recovery and protect pending boss settlement |
| M4A-6 | `f2f3785` | Extend and qualify the pinned MicroPython Floor II probe |

The original cumulative baseline was qualified by [GitHub Actions run 42273495771](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42273495771) on exact SHA `b57ca41fec21988718605b211e56e7a6a5950ce0`: 2,084 root tests, 66 web tests, and 39 PostgreSQL tests passed, with migration/Alembic checks and the 161-file browser build. This is historical baseline evidence; final qualification is recorded below.

### Review Corrections And Final Qualification

The review corrections address the three findings:

- **R1:** Validate current schema-18 discovery sources, route-node references, source/node associations, active searchers, and durable discovery evidence while retaining known historical source IDs for older saves.
- **R2:** Restore the encounter-local carried-supply checkpoint when a victorious Floor II reward save fails, without rewinding earlier committed progress.
- **R3:** Recover a persisted Floor II boss victory through an idempotent settlement action rather than requiring a boss refight, including same-session retry and reload. Return Talisman is unavailable and rejected while boss settlement is pending, leaving finalization as the only resolution.
- The browser smoke's discovery-bonus lookup now keys Drifters by canonical profile choice; the save profile does not expose a `drifter_id` field there.

The corrections and talisman guard are hosted-qualified on exact SHA `a48903f2456adff075a00453fb43c79449a5e0c3` in [Actions run 42296351933](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42296351933). The final M4A-6 code commit is `f2f378563d96bf94e9dd37b57e9238665f32e2b1`; [Actions run 42305392988](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42305392988) passed on that exact SHA. Hosted results: **2,102 root tests**, **66 web tests**, and **39 PostgreSQL tests** passed; content validation and compile passed; migration-from-zero and Alembic parity passed (`No new upgrade operations detected`); the **161-file browser build** and complete headless browser smoke passed through `M4_BROWSER|FLOOR_TWO_BOSS_CLEAR|PASS`.

**Goal:** Add authored enemy Tier 1 behavior and a bounded, replayable Floor II route that introduces D3, Grade-II materials, persisted search/drop outcomes, and one counterable environmental threat without changing sealed Floor I behavior.

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
- D3 is offered at the midway Rest for 65 secured shared gold. Recruitment adds the roster member without changing the locked active pair.
- Floor II is the first source of Grade-II Metal, Fiber, Timber, and Cores. Use the existing generic Grade-II weapon-improvement recipes; do not add alternate component storage or replace the sealed weapon system.
- One telegraphed physical cave-in uses existing Brace/Defend as its counter. No status effects, injuries, durability, formations, or boss phases.
- Discovery search and enemy-drop outcomes are authored, resolved at their event boundary, and persisted so reloads or repeated inputs cannot reroll or duplicate them.
- Preserve the approved floor-local replay XP schedule: initial clear at 100%; after that, 50%, 40%, 30%, then 20% minimum on later runs. Gold does not dwindle. Do not change Floor I's route or payout behavior.

Out of scope: Floor III content or D4 implementation, M5 armor, four-Drifter combat, formations, boss phases, new enemy archetypes unless existing content cannot fulfill a required role, rebalancing sealed systems, broad discovery placement, or any M6 expedition work.

## Approved Floor II Contract

```text
Hub, after Floor I boss clear
  -> choose Floor I replay or Start Floor II
  -> keep the currently selected two-member active pair
  -> Floor II battles 1-5
  -> Midway Rest: Recover / Continue / Extract, plus D3 event
  -> Floor II battles 6-9
  -> Pre-Boss Rest: Recover / Continue / Extract, plus one Search site
  -> Floor II boss (battle 10)
  -> full eligible boss payout, restore party, return to Hub
```

The Floor II route uses M2's existing payout semantics: Rest extraction banks 50% of already-adjusted XP and gold and all pending items; Return Talisman banks 100% of already-adjusted XP only; boss clear banks all eligible rewards; death loses unsecured XP/gold/items and carried supplies, returns the recruited roster fully restored, and cannot rewind through a Rest save. Continue remains available after Rest recovery.

D3 uses the exact 65-gold secured shared-gold cost. The event offers only unrecruited canonical Drifters. If the party has less than 65 secured gold, the attempt changes nothing: it does not charge, add a member, or mark the event complete. The party may continue or extract. Floor I replay remains available as an existing gold source, and Floor II remains launchable/replayable, so the player can return to Hub, obtain sufficient secured gold through existing rewards or permitted sales, and retry. D3 remains recruitable after Floor II is cleared; Floor III progression must not bypass the D3 recruitment position. A successful mid-run recruit joins the permanent roster but cannot replace either active Drifter until Hub return. A recruit starts at the canonical authored Level 1 state with its current kit and base signature weapon; no XP, GP spending, or weapon progress is fabricated.

## Authored Initial Values

These are tunable first-pass content values, not locked balance targets:

- Enemy tier: Tier 1 on Floor II, with per-archetype authored stat adjustments. No reward multiplier is inferred from tier.
- Identity multiplier: matching elemental/alchemical resistance uses 75%; weakness uses 125%. Apply after generic mitigation and physical-only Strength negation, before Brace/Defend, using the approved component rounding behavior. A component may resolve to zero; do not add an immunity result.
- Discovery: each source authors its own base chance. The first Floor II searchable source starts at 1,000 basis points (10%). Calculate `effective = min(10_000, base + floor(base * discovery_bonus_bps_from_intuition(searcher.effective_stat("intuition")) / 10_000))`. The selected searching Drifter must be in the active pair. No party average. This Intuition modifier applies to discovery searches only; enemy item-drop entries use their authored odds without an added Intuition modifier.
- Item drops: each authored drop entry has its own chance and quantity. Initial Grade-II common-material drop entries use 2,000 basis points (20%); Grade-II Core entries use 1,000 basis points (10%). Values live in content and are tunable; no rare drop is guaranteed.
- Search fixture: one authored Floor II source at the pre-boss Rest, `ancient_well_floor2_01`, granting its authored +5 max HP under the existing M3 claim flow. Broader source placement remains outside M4A.
- Cave-in: one authored encounter warning, one physical damage component using the existing physical defense path, and one resolution at the designated encounter's next existing enemy-action boundary. Use the existing living-target selection and Brace/Defend resolution; author the initial damage conservatively in encounter content. Do not create a general-purpose hazard framework or new action timing model.

## State And Persistence

At M4A entry, the versions were runtime snapshot schema 16 and disk schema 17. M4A-3 advances these to runtime schema 17 and disk schema 18 for persisted floor-local clear/replay tracking and run-scoped search/drop outcome evidence. Continue through the existing migration chain; keep the profile API, envelope version, and database schema unchanged.

- `PartyState` owns the active run identity, floor-two clear/replay state, pending run rewards, and run-scoped resolved event outcomes.
- `WorldState` owns globally found/claimed permanent discovery source IDs. Use the existing M3 permanent-discovery claim service and preserve its atomic reward/claim contract.
- Give each event a stable idempotency key derived from floor/run identity, route node, event kind, and (for drops) enemy instance position. A genuine later run gets a new run identity; a repeated submit in the same run gets the stored result.
- At enemy victory, resolve all item-drop entries once, atomically apply the encounter rewards and event record, then present the result. At confirmed search, resolve once, persist the result, and reveal the source if found. A canceled claim does not consume it.
- Persist the resolved result at the authoritative boundary before acknowledging success. Failed persistence must not leave reward without evidence, evidence without reward, or a success message for an uncommitted outcome. Rest saves remain checkpoints; this does not enable saving a live battle.
- Schema-16/runtime and schema-17/disk documents migrate with no Floor II clear, zero Floor II replay runs, no active Floor II run/outcomes, and no fabricated discoveries. Preserve every existing field and historical profile revision/digest.
- Reject impossible states: Floor II cleared before Floor I, active Floor II without the required Floor I unlock, duplicate/malformed event keys, unknown discovery IDs, invalid item/quantity/chance data, and D3 completion without a recruited identity. Rejection occurs before reconstruction or partial mutation.

## File Ownership Map

Reconfirm exact call sites at implementation entry; do not create parallel owners.

| Responsibility | Existing owner(s) to extend |
| --- | --- |
| Tier values, resistances, encounter drops | `root/src/app/content/enemy_spec.py`, `encounter_spec.py`, `catalog.py`, `root/src/app/enemies/definition.py`, `state.py`, `validation.py` |
| Authored Floor II route and D3 event | `root/src/app/content/route_spec.py`, `routes/`, `encounters/`, `recruitment_event_spec.py`, `recruitment_events/`, `catalog.py` |
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

### M4A-3: Run Identity, Drop/Search Outcomes, And Schema 18

- [x] Add transaction tests for encounter drop resolution and confirmed search: first resolution records the outcome and reward/source; repeated input returns the same result and grants nothing extra.
- [x] Add a run identity and stable event keys to the existing party/run state. A new genuine Floor II run has distinct event keys; reload, UI rebuild, duplicate submit, and Rest checkpoint load do not.
- [x] Implement explicit per-entry drop chance/quantity data and deterministic injected RNG. Roll once at encounter victory, aggregate to unsecured outing items, and persist reward plus outcome evidence atomically.
- [x] Implement one Floor II Rest search using the selected active Drifter's effective Intuition and `discovery_bonus_bps_from_intuition()`. Persist failed and successful results. A failed search can be attempted in a later run; an already found/claimed source cannot be rolled or awarded again.
- [x] Use the M3 permanent-discovery claim transaction for target selection, confirmation, and source claim. Persist the found source separately from claim state so cancel/reload does not lose or duplicate it.
- [x] Bump runtime/disk schemas to 17/18; add migration, exact shape validation, round-trip, malformed-state rejection, source immutability, and current remote-profile advancement tests. Do not change profile API/envelope/database versions.

Proof: event outcome, pending reward/source, and durable evidence agree after success; persistence failure leaves no partial committed transaction; all pre-M4 saves migrate without changing their old state. Covered by `test_floor_two_run_events.py`, `test_floor_two_run_state.py`, save migration tests, and profile-service history fixtures. The M4-focused root selection passed (491); full-root hosted/PostgreSQL migration qualification remains open in M4A-6.

### M4A-4: Floor Selection, Route, D3, And Settlement

- [x] Add Floor II route nodes for battles 1-5, midway Rest, battles 6-9, pre-boss Rest, and battle 10 boss. The Hub offers Floor I replay or Floor II only after Floor I clear; Floor I route content and payout tests remain unchanged.
- [x] Add floor-two start/clear/replay state. Use the approved floor-local XP replay rates of 100%, then 50%, 40%, 30%, and 20% minimum; do not reduce gold.
- [x] Add D3 recruitment at the midway Rest for 65 secured shared gold. The candidate list excludes recruited identities. Insufficient gold leaves all state and event evidence unchanged and offers a return/retry path; successful recruitment leaves the active pair unchanged until Hub.
- [x] Ensure skipped D3 recruitment remains available on later Floor II runs and after Floor II clear. Floor III cannot bypass the D3 recruitment position. Do not block extraction, death recovery, or Floor II replay when the player cannot pay.
- [x] Author Grade-II sources for all four families, using existing IDs and improvement recipes. No Grade-II materials come from Floor I. Do not add new weapon component variants.
- [x] Preserve Rest Recover + Continue + Extract, Return Talisman, boss full payout, death loss/recovery, carried supply handling, and secured/unsecured separation. Floor II boss clear returns the party to Hub and records the clear once.
- [x] Prove route cursor, outcome evidence, party, pending rewards, replay counter, recruitment event, and discovered/claimed state round-trip at supported checkpoints.

Proof: full session-flow tests cover insufficient-gold extraction/retry, D3 recruitment, search/claim, Floor II boss clear, Grade-II rewards, and save reconstruction. Floor II has ten battles with the approved Rest placement; sealed Floor I tests remain in the cumulative suite.

### M4A-5: Terminal/Browser Parity And End-To-End Flow

- [x] Expose the same floor choices, searcher selection, D3 candidates, blocked reasons, hazard warning, and actual reward results in terminal and browser presenters. Clients submit semantic IDs only; they do not roll or calculate outcomes.
- [x] Add presenter/bridge tests for exact Drifter IDs, unoffered/benched targets, stale recruitment offers, duplicate submits, and responsive Rest actions.
- [x] Add a built-browser semantic journey: load a qualifying save, enter Floor II, reach the midway Rest, reject D3 for insufficient gold without mutation, return to Hub, obtain gold, replay, recruit D3, reach a Rest search, save/reload the revealed/claimed state, complete the boss, and inspect secured materials/rewards.
- [x] Add a terminal UI journey with the same rules and Floor II completion. Keep a separate regression for the unchanged Floor I clear/replay route.

Proof: `test_terminal_can_start_and_complete_floor_two_with_recruitment_and_discovery` exercises the actual terminal key mapping and full session, including ten encounters, D3 recruitment, discovery claim, and boss clear. The built-browser journey emits `M4_BROWSER|FLOOR_TWO_BOSS_CLEAR|PASS`. Floor I clear/replay remains separately covered.

### M4A-6: Qualification And M5 Handoff

- [x] Baseline: focused M4 selection (492), full root pytest (2,084), and web pytest (66) passed locally; hosted cumulative qualification is recorded for exact SHA `b57ca41fec21988718605b211e56e7a6a5950ce0`.
- [x] Baseline: content validation, compile, generated dataclass manifest check, 161-file browser build, and built-browser smoke passed through `M4_BROWSER|FLOOR_TWO_BOSS_CLEAR|PASS`.
- [x] Baseline hosted profile-service PostgreSQL tests (39), migration-from-zero, and Alembic checks passed in [run 42273495771](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42273495771).
- [x] Pre-commit correction-tree local verification: full root pytest (2,095), web pytest (66), content validation, compile, 161-file browser build, and complete built-browser smoke passed.
- [x] Rerun focused and cumulative qualification for the recovery corrections, including browser smoke and PostgreSQL/migration/Alembic checks.
- [x] Extend and run the actual pinned MicroPython qualification for Tier 0/Tier 1 content loading, Floor II route/recruitment/drop/search snapshots, teardown, and semantic parity. The formal repeated heap check passed at 1024K (3/3); 944K produced the expected memory-limit classification (3/3). Intermediate heap results varied and are not claimed as a stable frontier.
- [x] Run `git diff --check` and inspect the final correction diff before commit.
- [x] Record the accepted code SHA and hosted results here and in the probe record.
- [x] M4A closure criteria are met and the M5 handoff is unblocked. Do not start M4B until M5 is complete.

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
| D3 | 65 secured shared gold; insufficient funds changes nothing; retry remains possible; active pair stays locked. |
| Economy | Rest, talisman, boss, death, and carried supplies match M2; Floor I remains unchanged. |
| Grade gates | Only Floor II yields Grade II; all four families have an authored source; existing weapon recipe machinery is reused. |
| Saves | Runtime 17/disk 18 migration is additive and immutable history is preserved. |
| Clients | Terminal and built browser share legal actions, result text, and exact-target rules. |

## M4A Closure

M4A is closed on the qualified tree: the Floor II loop is playable from Hub through boss and back, D3 can be recruited or safely retried, the approved hazard and identity behavior are exercised, event outcomes survive reload without duplication, Grade-II materials are gated to Floor II, Floor I regression tests remain green, and hosted plus pinned-runtime qualification is recorded. M5 is next; M4B remains open and sequenced after M5.

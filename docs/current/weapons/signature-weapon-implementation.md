# Signature Weapon Progression Implementation Plan

> **For implementation:** Continue through the open gates in order. Use `superpowers:test-driven-development` for each behavior change. Gate 0 decisions are approved and recorded below; do not reopen them without approval.

**Goal:** Add persistent, data-driven signature-weapon progression that lets the roster dismantle eligible loot, improve each Drifter's four weapon slots, cross quality tiers, and configure components through the existing game interfaces.

**Architecture:** Keep Python authoritative. Extend the existing authored weapon catalog, store each weapon's installed components and slot progress with its `PlayerState`, and store Crafting progress plus materials in the existing shared `PartyState` inventory. Route all actions through the existing Overworld session/presenter boundary so terminal and browser use the same rules; retain the current profile API, save envelope, and database architecture.

**Tech Stack:** Existing Python game/runtime and generated content catalog, dataclass state/snapshots, pytest, terminal Overworld UI, browser Python bridge and JavaScript renderer, profile API contract, static browser build, and the pinned MicroPython qualification tools.

**Spec:** [signature-weapon-progression.md](signature-weapon-progression.md).

This plan is the implementation contract where it resolves an ambiguity in the
broader design spec. Unresolved questions not explicitly settled here remain
open; do not infer additional mechanics from the implementation details.

## Audited Current Status (2026-10-28)

This snapshot distinguishes implemented foundations from accepted gates. A gate
remains open until all of its required behavior and verification are complete;
an unchecked task does not mean that no related code exists.

| Gate | Status | Present in the current tree | Still open |
|---|---|---|---|
| 0. Playable baseline | Complete, as recorded below | Shared Crafting/material inventory, Grade-I-IV material and improvement-recipe definitions, Goblin Scrap/Core salvage, basic slot improvement, and Hub merchant actions for improvement and dismantling. | No Gate 0 work identified in this audit. |
| 1. Authored content | Partial | All four weapons have ordered slots, neutral starting parts, and one Grade-I craftable part per slot using its matching material family. The Grade-I material families have Floor I salvage sources; the recipe awards 10 Crafting XP, and components author identity contributions and move modifiers. Tests cover slot/family mapping and verify each modifier names a move on its wielder. | Higher-floor sources and components remain unauthored. Broader validation of malformed/duplicate component definitions and effect values remains open. |
| 2. Persistent state | Implementation present; corrective revision awaiting cumulative verification | Per-Drifter signature-weapon state and shared Crafting/material state are serialized. Runtime schema is 10 and disk schema is 11. The current local revision validates installed component IDs and slot compatibility for lead and companion profiles; four focused regression cases pass. | Run hosted checks on the corrective revision. Learned-technique ID validation remains deferred until eligible techniques are authored. |
| 3. Progression rules | Partial | Basic improvement spends the matching grade/family material, awards authored Crafting XP, applies a 1-5 roll, and enforces shared tier gates. Basic dismantling is atomic. | Full weighted-roll coverage, all gate boundaries, stat/quality projection, and Tier V behavior/tests are absent. |
| 4. Components and combat projection | Partial | Component changes update per-Drifter installed state; identities are derived from installed parts, and authored move modifiers project onto actual combat moves. Tests cover crafting, installation, identity ties, move effects, and save round-trip. | Broader replacement/salvage edge coverage and learned-technique acquisition/replacement behavior remain open. |
| 5. Hub and client parity | Partial | The Hub merchant offers Grade-I component recipes; Character > Weapon selects a current party Drifter and installs an owned compatible part. Terminal and browser bridge paths use explicit target IDs. The built-site smoke passed the craft/install flow and full existing route smoke. | The broader progression-to-save/reload browser smoke required by this plan has not been run. |
| 6. Cumulative qualification | Open | Broader game/browser qualification evidence is recorded in `docs/probe.md`. | The pinned MicroPython probe has not been extended with weapon progression, and final weapon-progression qualification is not recorded. |

Hosted verification for reviewed pushed SHA `64f28601efc951002d4d5a80bb6acf69f1343e67`:
1,750 root Python tests, 53 web tests, and 29 PostgreSQL service tests passed;
content validation, compileall, the 141-file browser build, Playwright smoke,
migrations from zero, and `alembic check` also passed. These results predate the
current local save-validator correction. On this working tree, all four focused
component-validation regressions pass. The full local root run reported 1,737
passed and 17 failures caused by the bundled Python 3.12 test environment
(nested pytest processes could not import pytest, and portability probes could
not import `annotationlib`); hosted checks must be rerun on the corrective
revision. The actual pinned MicroPython matrix remains open.

## Global Constraints

- Every signature weapon has exactly four slots: three body/structural slots and one signature/special slot.
- Slot material families are fixed by slot number: 1 Metal, 2 Fiber, 3 Timber, 4 Cores.
- Slot progress and shared roster-wide Crafting level each use a 0-100 scale.
- Each slot-progress point adds 0.25% of the governed original base stat; at 100 progress this is +25%. Add the cumulative quality bonus from the same original base stat, then round once to the nearest integer with exact halves rounded up.
- A successful ordinary improvement always adds a random 1-5 percentage points; Crafting shifts odds upward, but every result remains possible.
- Tier II, III, IV, and the Tier V attempt gate are 25, 50, 75, and 100. Every slot and shared Crafting must meet the same gate.
- Slot progress cannot overshoot its next gate. A roll that crosses a gate clamps exactly to it with no overflow; that slot remains capped until all four slots and shared Crafting unlock the next tier.
- Ordinary quality bonuses are separate, cumulative +5%, +10%, and +15% of original base stats at Tiers II-IV. Tier V requires all slots and Crafting at 100, uses Grade IV materials, and has a non-guaranteed attempt; failure consumes materials but preserves progress and awards no Crafting progress, while success adds another +25% for +40% cumulative quality bonus.
- Dismantling yields at least one matching material and no more than the source item's authored maximum; Crafting can improve odds but never guarantee the maximum. Dismantling awards no Crafting progress.
- Only successful actual crafting/improvement recipes award Crafting progress, with an explicit authored award per recipe. Alchemy remains separate and does not award Crafting progress.
- Component replacement consumes the old component. Installed component effects are data-driven; learned techniques remain learned after a component is replaced.
- Physical and mystical identities are derived independently; ties above threshold produce no identity on that axis, and identities recalculate after component changes.
- No browser-owned progression rules, automatic field merging, new persistence provider, Firebase SDK, database migration, or API/envelope version change.
- Preserve old save/profile digests and immutable remote revisions. Current versions observed in this tree are runtime schema 10, disk schema 11, envelope v1, and API `/v1`. Weapon progression uses those current schemas; no additional schema/API/database version change is planned, and supported legacy schemas remain readable.
- Keep new gameplay code inside the existing runtime boundary and run the actual pinned MicroPython qualification for the final tree; do not treat a synthetic parser test as runtime evidence.

## Review Focus

- Invalid or incomplete weapon-state snapshots and absent/unknown `target_drifter_id` values must be rejected without partial mutation or fallback to the lead; test in Tasks 2, 3, and 5.
- An improvement with insufficient/wrong-family materials or an ineligible grade must consume nothing and change no progress; test in Task 3 with each rejection path.
- RNG extremes must preserve the authored guarantees: ordinary improvement remains 1-5, salvage remains at least 1 and at most its authored maximum, and Tier V failure preserves progression; test in Task 3 with deterministic RNG.
- A component configuration that ties two identities, drops below threshold, or changes after replacement must derive the documented identity state immediately; test in Task 4.
- A component replacement that removes a move modifier must not erase a technique already learned from a rare core; test in Task 4 and the save round-trip in Task 2.

---

## Current Architecture and Scope

- `root/src/app/content/weapon_spec.py` and the generated weapon catalog are the existing authored-weapon boundary. Extend that pattern rather than introducing a second runtime weapon catalog.
- `root/src/app/player/player_state.py` owns per-Drifter equipment and snapshots. Store that Drifter's signature-weapon progression there; do not duplicate the lead's progression in `PartyState`.
- `root/src/app/game/party_state.py` already owns shared gold, shared item stacks, and dungeon state. Extend it for shared Crafting progression and use its shared item stacks for materials.
- `root/src/app/game/overworld_session.py` and its presenter/models are the action and presentation boundary. Use a dedicated Hub merchant as the crafting entry point; JavaScript only renders offered actions and submits semantic inputs.
- Every weapon-progression semantic action carries a stable `target_drifter_id`; resolve it against the currently instantiated game roster (lead plus recruited companions), never by assuming lead or party-array position. All four Drifters are targetable when instantiated as the lead or a recruited companion. Do not add a separate dormant-roster persistence model in this plan.
- Existing ordinary weapon bonuses must remain unchanged until the new authored slot data explicitly reproduces them.
- This first implementation does not add an overall refinement-level progression: its cap and effects remain unresolved in the spec. Preserve existing weapon behavior and leave overall refinement for a separately approved balance/design pass.
- This plan adds no Alchemy system, inventory-capacity system, respec flow, visual weapon rendering, new stats/scaling rules, or target/scaling changes to moves.

## Gate 0: Start With A Playable Baseline

- [x] Record the starting SHA `266e504f28c15998ef30ab5576a3b50b58bd1216`, branch `hub`, and the two existing weapon-doc modifications; preserve those changes.
- [x] Freeze the gameplay rules already recorded in this plan; use clearly identified first-pass tuning values for the initial implementation rather than requiring a complete balance sign-off.
- [x] Build the playable Floor I progression loop: shared materials and Crafting, one Grade-I improvement recipe for each slot family, Goblin salvage, and the Hub merchant. Tuning values are centralized and data-driven.
- [x] Give the Floor I loop authored Grade-I sources for all four families. Dismantlable Goblin loot supplies Metal, Fiber, and Timber; every Goblin Lord defeat, including replays, guarantees enough Cores for one slot-four improvement.
- [x] Use the recorded Gate 0 first-pass defaults for recipe costs/awards, Crafting thresholds and weights, and salvage odds. These are provisional and will be balanced after playtesting. Component effects, identity scoring, and Tier V remain for their later implementation gates.
- [x] Approve the Floor I source approach: dismantlable Goblin loot supplies Grade-I Metal, Fiber, and Timber; every Goblin Lord defeat, including Floor I replays, guarantees enough Grade-I Cores for one valid slot-four improvement. Exact item IDs, yields, and recipe quantities remain in the balance table.
- [x] Approve the stat conversion and rounding rule: each slot-progress point adds 0.25% of the governed original base stat; improvement and cumulative quality bonuses are combined against that original value and rounded once to the nearest integer, with exact halves rounded up.
- [x] Confirm tier gates of 25/50/75/100. Grade I improves progress up to 25; after a gate is unlocked, the next grade funds progress toward the following gate. A slot cannot improve past a locked gate.
- [x] Use a dedicated Hub merchant as the crafting entry point instead of `Items > Craft`.
- [x] Confirm the Hub merchant handles crafting, weapon improvement recipes, and dismantling. `Character > Weapon` is reserved for inspecting/configuring a signature weapon. Keep these progression interactions Hub-only.
- [x] Set shared Crafting to start at Level 1 with zero progress toward Level 2; later thresholds are first-pass tuning values.
- [x] Set the pacing target that Crafting Level 25 is reachable after about three Hub-returning Floor I runs, before replay XP reaches its 20% minimum, while Grade II materials remain exclusive to Floor II.
- [x] Preserve the starting baseline at the recorded SHA: 239 game tests and 10 browser bridge tests passed before implementation.
- [x] Verify the Gate 0 tree: 1,779 game/web tests passed; the built-site Playwright smoke passed through the Hub Merchant and full Floor I route; content/catalog checks, dataclass-manifest check, and compileall passed.
- [x] Run the profile-service SQLite/unit suite: 24 passed. Five PostgreSQL-only tests were skipped because the Docker engine/test database was not reachable from this execution environment.
- [x] Verify the generated catalog is current with `python tools/generate_content_catalog.py --check` from `root/`.
- [x] Verify the portable dataclass manifest is current with `python tools/generate_dataclass_manifest.py --check` from `root/`.
- [x] Verify baseline authored content with `python -m tools.validate_content`: 5 enemies, 4 weapons, 4 Drifters, 10 encounters, and 2 routes.

**Gate 0 exit:** The approved mechanics and Floor I source approach are sufficient to begin implementation. Provisional tuning values do not block the playable baseline and must remain easy to adjust.

## File Map

- `root/src/app/content/weapon_spec.py` and `root/src/app/content/weapons/*/weapon.py`: attach immutable, authored progression definitions to the four existing signature-weapon records.
- `root/src/app/content/weapon_progression_spec.py` (new): validated immutable definitions for slots, components, recipes, dismantle sources, material grades, identity contributions, and move modifiers.
- `root/src/app/content/catalog.py`, `root/src/app/content/_generated_catalog.py`, `root/tools/generate_content_catalog.py`, `root/tools/validate_content.py`: catalog lookup, deterministic generation, and cross-reference validation for progression data.
- `root/src/app/player/signature_weapon_state.py` (new), `root/src/app/player/player_state.py`: per-Drifter installed slot components, 0-100 slot progress, and persistent learned techniques; quality and identity remain derived.
- `root/src/app/game/party_state.py`: shared Crafting progression and material stock using the existing shared inventory boundary.
- `root/src/app/game/weapon_progression.py` (new): validated, atomic domain actions for recipe crafting, slot improvement, dismantling, component replacement, and Tier V attempts. Every action accepts `target_drifter_id`; validate it against the current game roster and inject RNG through the existing game randomness convention.
- `root/src/app/game/overworld_session.py`, `root/src/app/presentation/overworld_models.py`, `root/src/app/presentation/overworld_presenter.py`: authoritative offered choices, Hub-only action validation, and renderer-neutral progression views.
- `root/src/app/ui/overworld_ui.py`, `root/src/app/ui/terminal_overworld_ui.py`, `root/web/python/dd_bridge.py`, `root/web/play/js/pyd4.js`: terminal and browser presentation/input parity; no progression formulas in JavaScript.
- `root/src/app/content/enemy_spec.py`, `root/src/app/content/encounter_spec.py`, `root/src/app/content/catalog.py`, and the existing reward path: authored eligible loot/material drops where needed for the first progression slice.
- `root/src/app/snapshot.py`, `root/src/app/persistence/save_document.py`, and `root/services/profile_api/src/profile_api/save_contract.py`: runtime/disk schema 10/11 validation and forward migration; no envelope/API/database version change.
- `root/tests/test_weapon_progression.py` (new), `root/tests/test_weapon_content.py`, `root/tests/test_player_state.py`, `root/tests/test_party_state.py`, `root/tests/test_save_document_boundary.py`, `root/tests/test_legacy_save_migration.py`, `root/tests/test_overworld_session.py`, `root/tests/test_overworld_presenter.py`, and focused UI/content tests: domain, serialization, validation, and terminal coverage.
- `root/web_tests/test_browser_bridge_contract.py`, existing Playwright smoke, `root/tools/micropython_hub_probe.py`, `root/tests/test_micropython_route_probe_contract.py`, and `docs/probe.md`: browser parity and progression runtime qualification evidence.
- `root/services/profile_api/tests/test_profiles.py` and the existing PostgreSQL service suite: prove the current service accepts the new save contract without changing persistence schema.

## Gate 1: Authored Progression Content

- [ ] **Red:** Add tests for all four exact weapon-specific slot-label sequences; four distinct ordered slots; slot-family mapping; valid component/material references; recipe costs and Crafting awards; valid modifier targets; and rejection of unknown IDs, negative quantities, duplicate slots, invalid grades, and move target/scaling modifiers.
- [ ] Run the focused content tests and confirm they fail for missing progression content/validation.
- [ ] Add immutable progression definitions in `weapon_progression_spec.py`; attach them to the existing four `WeaponSpec` records without changing item IDs, persistence keys, intended wielders, or current base bonuses.
- [ ] Extend generation and validation to include progression references. Keep authored records in the existing weapon directories unless the generator requires a focused new content directory; do not reorganize the catalog.
- [ ] Author the Gate 0-approved starting components, material grades, recipes, salvage sources, identity contributions, and move modifiers for all four weapons. Do not add unresolved branch names, final affixes, or overall refinement behavior.
- [ ] Author Floor I route-available Grade-I sources for all four material families. Validate that each family can fund at least one valid first improvement; do not require equal drop rates or amounts.
- [ ] **Verify:** `python tools/generate_content_catalog.py --check`, `python -m tools.validate_content`, and focused weapon/content tests pass from `root/`.

## Gate 2: Persistent State and Schema Migration

- [ ] **Red:** Add state and save tests for four initialized slots per signature weapon, independent state for lead and companion, shared Crafting/material state, learned techniques, and stable round-trip serialization.
- [ ] Add rejection tests for missing/extra slots, duplicate or unknown IDs, progress outside 0-100, negative material counts, invalid Crafting values, and learned techniques not authored by eligible content.
- [ ] Add migration tests for current runtime schema 9/disk schema 10 saves and all still-supported earlier schemas. Verify migration does not mutate source snapshots or old envelope payloads/digests.
- [ ] Add `SignatureWeaponState` and snapshot reconstruction with the approved canonical shape. Store only source state: installed component IDs, slot progress, and learned technique IDs. Derive tier, identity, and generated presentation labels from current state/content rather than persisting duplicate derived values.
- [ ] Extend `PlayerState` to own its signature-weapon state. Extend `PartyState` with cumulative shared Crafting progress and shared inventory behavior; derive the 0-100 Crafting level from the Gate 0-approved threshold table. Preserve existing non-material item stacks and dungeon semantics.
- [ ] Bump `STATE_SCHEMA_VERSION` from 9 to 10 and `DISK_SCHEMA_VERSION` from 10 to 11. Read/migrate schema 8, 9, and 10 according to existing migration boundaries; initialize progression deterministically at each signature weapon's authored starting configuration and the approved initial shared Crafting progress.
- [ ] Update `profile_api.save_contract` to validate the new current save schema while continuing to accept the supported legacy read/progression path. Keep envelope v1, API `/v1`, PostgreSQL tables, and immutable historical revisions unchanged.
- [ ] Add a client/service regression proving a schema-10 remote head remains immutable and can be advanced by the current client to schema 11 without changing the old revision payload or digest.
- [ ] **Verify:** focused player/party snapshot, save document, migration, envelope, coordinator, and profile contract tests pass; run the profile-service tests against real PostgreSQL and confirm migration-from-zero plus `alembic check` show no DB schema drift.

## Gate 3: Progression Rules and Atomic Actions

- [ ] **Red:** Add deterministic tests for valid/invalid recipes, insufficient stock, wrong slot family, wrong material grade, exact resource consumption, explicit per-recipe Crafting awards, and no mutation after rejected actions.
- [ ] Add improvement-roll tests at Crafting 0, intermediate values, and 100. Inject a controlled RNG and prove results are 1-5, configured weights shift upward, and each result remains possible at every Crafting level.
- [ ] Validate the authored Crafting curve and Floor I recipe awards: Level 25 is reached after about three Hub-returning Floor I runs, before replay XP reaches its 20% minimum, while Grade II materials remain unavailable until Floor II.
- [ ] Add stat-projection tests for 0/100 slot progress, each ordinary quality tier, successful Tier V's cumulative +40% quality bonus, additive non-compounding behavior, and exact half-up rounding boundaries.
- [ ] Add gate tests at 25/50/75/100: every slot and shared Crafting must meet the gate; a lagging slot or Crafting level blocks the tier; the next grade is used after the prior gate unlocks and progress does not reset.
- [ ] Add clamping and material tests for each gate, including Grade I reaching 25, Grade II being required for progress beyond 25 after Tier II unlocks, no retained overflow, no improvement while the next tier is locked, and later progress continuing from the gate.
- [ ] Add Tier V tests for all requirements, configured material consumption on both outcomes, no progress/Crafting award on failure, and separate +25% base-stat bonus on success.
- [ ] Implement the minimal domain action service in `app/game/weapon_progression.py` using authored recipes and injected RNG. Validate all costs and eligibility before mutation; apply resource/progression changes as one action so exceptions or rejected inputs cannot partially spend materials.
- [ ] Implement quality/tier and stat projection using the Gate 0-approved formula and rounding rule. Keep improvement and quality additive from original governed base stats; do not scale an already-modified value.
- [ ] Add tests proving lower-tier recipes cannot consume next-tier gating materials incorrectly, Grade-I sources cover all four Floor I families, and higher-tier material availability follows authored floor/tier data.
- [ ] **Verify:** focused progression and content tests pass, including deterministic boundary cases and unchanged current weapon behavior when all new progress is at its starting values.

## Gate 4: Salvage, Components, Identities, and Combat Projection

- [ ] **Red:** Add dismantling tests for a minimum yield of one, authored maximum cap, Crafting-weighted yield distribution, no guaranteed maximum, no Crafting award, and no mutation on invalid/non-dismantleable items.
- [ ] Add component-replacement tests for matching slots, consumed old component, consumed new component, rare core consumption, immediate identity recomputation, same-axis ties yielding no identity, and simultaneous physical plus mystical identity.
- [ ] Add move-projection tests for approved modifiers to power, resource cost, accuracy, and damage type only. Assert that target and scaling remain unchanged.
- [ ] Add a rare-core test that learns its authored technique, replaces the core, and confirms the technique remains available while direct component modifiers no longer apply.
- [ ] Extend authored loot/reward definitions only for the approved initial source items and drops. Preserve the existing shared inventory/outing reward flow and make material drops deterministic under injected RNG.
- [ ] Implement salvage, component replacement, identity derivation, and move projection in the progression domain boundary. Recompute identity and direct move effects from the currently installed configuration; retain learned techniques as permanent source state.
- [ ] **Verify:** weapon, combat-move, content reward, and progression test subsets pass; existing combat results for weapons at their initial configuration remain unchanged.

## Gate 5: Hub Actions and Terminal/Browser Parity

- [ ] **Red:** Add Overworld session/presenter tests for opening `Character > Weapon` and the Hub merchant views, receiving only currently legal offered choices, invalid/stale semantic input rejection, and Hub-only access.
- [ ] Add target-resolution tests for each action with `target_drifter_id` set to the lead and recruited companion, including reversed party order; missing, forged, stale, and non-roster IDs must be rejected, never redirected to the lead.
- [ ] Add terminal tests for inspecting slots/progress/tier/Crafting/materials, crafting or improving an offered recipe, dismantling an eligible item, replacing a component, and returning to the previous view.
- [ ] Add browser bridge contract tests that send the same semantic actions and receive the same Python-projected data; verify JavaScript does not calculate costs, probabilities, identity, quality, or stat results.
- [ ] Implement progression view models and actions through the existing `OverworldSession` and presenter. Require `target_drifter_id` in every progression semantic input and resolve the exact current-roster Drifter. Put crafting, weapon improvement recipes, and dismantling at the Hub merchant; reserve `Character > Weapon` for inspection/configuration.
- [ ] Update terminal rendering and browser rendering to display the same offers, resource costs, results, and validation messages. Preserve desktop/mobile layout conventions and do not add an independent progression state machine in the browser.
- [ ] Extend the Playwright full-route smoke from Hub access through at least one dismantle, one successful improvement, one rejected insufficient-resource action, and a save/reload round trip showing the same progression.
- [ ] **Verify:** focused session/presenter/terminal/browser bridge suites pass; build the static browser site and run the pinned Playwright smoke.

## Gate 6: Cumulative Runtime Qualification

- [ ] Run all focused tests from Gates 1-5, then the complete game Python suite and web pytest suite. Run content generation check, content validation, compile checks, and `git diff --check`.
- [ ] Run the full profile-service suite against real PostgreSQL using the new schema-11 save payload, including create/update/replay paths, migration-from-zero, and Alembic drift check. No database migration is expected.
- [ ] Run the browser build and full Playwright flow against the built site; verify the browser remains a renderer/input adapter over Python-authoritative progression state.
- [ ] Extend the real pinned MicroPython probe with progression state initialization, one recipe/improvement, one dismantle/component change, save snapshot round-trip, and teardown. Preserve the existing probe marker protocol and stage ordering; add progression markers before the final closure marker and update its contract test and `docs/probe.md`.
- [ ] Run the actual pinned MicroPython matrix on the final tree, including semantic parity and the established heap-frontier checks. Record exact executable identity, observed results, and memory figures; do not treat the 448K diagnostic target as a product-device memory requirement.
- [ ] Review the cumulative diff for changed default combat behavior, duplicated derived save fields, invalid legacy-digest handling, unintended architecture changes, and browser-owned rules. Report exact observed test totals and qualification evidence. Stop for user review before committing or pushing.

## Acceptance Criteria

- All four signature weapons have the exact authored four-slot label map, use the fixed slot-family mapping, and preserve their current base behavior at initial progression state. Material family denotes dominant modification material, not total part composition.
- Floor I provides Grade-I sources for Metal, Fiber, Timber, and Cores in quantities sufficient to demonstrate at least one valid improvement in each slot family.
- Each Drifter's weapon configuration and learned techniques persist independently; shared Crafting and materials persist once at party scope.
- Successful ordinary recipe/improvement actions spend exactly their authored costs and award only their authored Crafting progress. Improvement always yields 1-5 slot points according to the approved Crafting-weighted distribution.
- Tier II-IV eligibility checks all four slot gates plus shared Crafting at 25/50/75; Tier V attempts require all values at 100. Improvement rolls clamp at 25/50/75/100 without overflow and remain there until the shared gate unlocks the next tier.
- Every weapon-progression action includes a stable `target_drifter_id` and changes the exact targeted lead/recruited Drifter regardless of party order; invalid targets never fall back to the lead.
- Dismantling is bounded by authored yields, never grants Crafting progress, and never guarantees the maximum. Component changes consume the old component, recompute identities, apply only supported direct move modifiers, and preserve learned techniques.
- Terminal and browser offer equivalent progression actions and results from Python-authoritative state.
- Runtime schema 10 and disk schema 11 migrate existing supported saves without data loss or digest mutation; envelope v1, API `/v1`, and database schema remain unchanged.
- The final tree passes the complete Python/web/profile-service/browser/content checks and the actual pinned MicroPython qualification; exact evidence is recorded in `docs/probe.md`.

## Post-Baseline Tuning Review

The following values are deliberately first-pass tuning, not implementation blockers. Review them after the Floor I loop is playable:

- Crafting progress-to-level thresholds and recipe Crafting awards.
- Material quantities, improvement-roll and dismantle-yield weights.
- Tier V cost/chance, identity point thresholds, and component stat/move effects.

Keep all of these values centralized in authored data so playtest tuning does not require changing progression rules or save contracts.
- Whether ordinary overall refinement remains untouched and deferred; this plan recommends deferring its mechanics because its cap/effects are unresolved.

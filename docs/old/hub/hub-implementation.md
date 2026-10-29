# Hub and First Dungeon Loop Implementation Plan

> **For agentic workers:** Implement this plan in order. Use the `superpowers:test-driven-development` skill for each behavior change, then run the focused test before proceeding. Do not begin implementation until this plan is reviewed and approved.

**Goal:** Deliver the first playable dungeon loop: reach the in-dungeon hub after the existing 75-gold surface route, recruit one chosen companion for 65 gold, fight three Goblins as a two-Drifter party, and return to the hub with the outing's rewards secured.

**Architecture:** Python remains authoritative for the party, hub, expedition rewards, combat turns, and transitions. Extend `GameState`, `OverworldSession`, `Battle`, and their renderer-neutral view models. Keep `player_state` as the lead Drifter for existing callers; store only additional party members and shared dungeon progression beside it, avoiding a duplicated lead snapshot. Terminal UI and the browser bridge/renderers consume the same offered views and semantic inputs. Add only the versioned state needed for party membership, secured shared resources, and an outing reward ledger.

**Tech Stack:** Existing Python game/runtime and content catalog, dataclass view models, terminal UI, browser Python bridge, vanilla-JS browser renderer, current save envelope/profile API, pytest, and existing web Playwright smoke.

**Spec:** [hub.md](hub.md). This plan implements only the first hub/recruitment/two-Drifter/three-Goblin/successful-extraction slice. The later-outing warning and death-loss rules remain agreed future direction in `hub.md`, but are deferred so this milestone does not invent a repeatable outing or reward loop.

## Fixed Decisions

- Preserve the authored surface route. At the dungeon entrance, its 75 gold becomes the shared hub balance; the 65-gold recruitment leaves 10 gold.
- The player chooses one of the other three Drifters as the companion. Do not auto-select a companion or add another recruitment price formula.
- The tutorial encounter is exactly three authored Goblins. Existing Goblin rewards total 120 EXP and 9 gold; on a successful extraction each Drifter receives 60 EXP and the 9 gold is secured in the shared balance. Do not invent item drops.
- Each living Drifter and enemy is an individual combatant in one descending-Dexterity order. Equal Dexterity uses the injected RNG for a fair tie order. If Dexterity changes, rerank only actors who have not acted in the current round.
- A defeated tutorial party returns to Drifter selection and starts the tutorial over; it does not retain rewards from the failed tutorial attempt.
- Successful extraction banks the current outing ledger, fully restores the party's HP and Mana, and returns to the hub. It does not advance into another encounter.
- Until enemy targeting AI is developed, each Goblin chooses uniformly at random among living Drifters using the injected RNG.
- Dexterity-queue tests may use a controlled combatant/effect fixture to change a stat during a turn. Do not add an authored move or a new debuff mechanic solely to exercise reordering.
- Keep save envelope version `1`, API route `/v1`, database schema, and persistence provider architecture unchanged. Bump only the game-state runtime/disk schema as needed. Migrate local data forward without invalidating its old digest, and continue to read immutable schema-8 cloud revisions so they can be advanced to schema 9.
- Preserve current one-Drifter gameplay outside this new dungeon flow. No browser-owned game rules or state.
- Stop after the first successful extraction. Do not add a subsequent outing button, later-run warning/loss handling, boss/floor progression, or XP decay in this implementation.

## File Map

- `root/src/app/game/party_state.py` (new): additional Drifter membership, shared secured inventory/balance, and outing ledger with snapshot support.
- `root/src/app/game/game_state.py`, `root/src/app/game/overworld_state.py`, `root/src/app/game/overworld_session.py`: authoritative dungeon phase, hub actions, recruitment, readying, extraction, and defeat transitions.
- `root/src/app/presentation/overworld_models.py`, `root/src/app/presentation/overworld_presenter.py`, `root/src/app/ui/overworld_ui.py`, `root/src/app/ui/terminal_overworld_ui.py`: offered choices and terminal rendering for hub and selection phases.
- `root/src/app/combat/battle.py`, `root/src/app/presentation/battle_models.py`, `root/src/app/presentation/battle_presenter.py`, `root/src/app/ui/battle_ui.py`, `root/src/app/ui/terminal_battle_ui.py`: multi-Drifter combat context, current actor, targeting, and individual Dexterity initiative.
- `root/src/app/content/encounters/dungeon_goblin_trio/` (new), `root/src/app/content/catalog.py`, `root/src/app/content/_generated_catalog.py`: authored encounter and generated catalog.
- `root/src/app/snapshot.py`, `root/src/app/persistence/save_document.py`, `root/src/app/persistence/envelope.py`, `root/src/app/persistence/remote_client.py`, `root/src/app/persistence/sync.py`, `root/src/app/persistence/migration.py`, `root/services/profile_api/src/profile_api/save_contract.py`: forward-compatible state schema and local/remote schema-8 compatibility. Verify legacy envelope digests before migration; keep immutable remote schema-8 revisions readable and advance them with a schema-9 revision. Do not change envelope/API/DB versions.
- `root/src/app/game/main_loop.py`, `root/web/python/dd_bridge.py`, `root/web/play/js/pyd4.js` (and focused CSS only if required): return-to-selection and shared renderer flow.
- Focused gameplay, combat, snapshot, and persistence regressions under `root/tests`; browser-specific contracts and smoke coverage under `root/web_tests`; profile-service contract coverage under `root/services/profile_api/tests`.

## Gate 0: Baseline and Contracts

- [x] Record the starting Git SHA and status; leave unrelated changes untouched.
- [x] Run focused existing tests for `test_overworld_session.py`, `test_runtime_battle.py`, `test_battle_presenter.py`, `test_game_snapshot.py`, `test_save_document_boundary.py`, `test_save_state.py`, and `test_route_content.py`.
- [x] Confirm the generated catalog is current with `root/tools/generate_content_catalog.py --check`.
- [x] Add failing tests first for the hub entry point and the existing 75-gold route total. Keep all tests specific to browser behavior in `root/web_tests`.

## Gate 1: Party State and Save Migration

- [x] **Red:** Add failing tests for empty-party defaults, adding exactly one distinct companion, rejecting duplicate/lead recruitment, the 75-to-shared-balance transfer, paying 65 once, insufficient funds without partial mutation, and party/hub/outing snapshot round-trips.
- [x] **Green:** Add the small party/dungeon state object. Keep the existing lead in `GameState.player_state`; persist only companion `PlayerState` snapshots in the new aggregate. Store shared secured gold/items, tutorial completion/phase, and unbanked outing rewards there. Keep transient battle objects out of snapshots.
- [x] **Red:** Add migration tests for schema-7 runtime saves, old schema-8 disk saves both before and at the dungeon entrance, and a schema-8 local envelope whose digest matches the original payload. Add linked-clean-profile and profile-with-conflict-evidence cases, plus a client reading a schema-8 remote head and advancing it without changing the old revision.
- [x] **Green:** Bump `STATE_SCHEMA_VERSION` from 7 to 8 and `DISK_SCHEMA_VERSION` from 8 to 9. Refactor migration dispatch so schema 7 remains explicitly recognized after the runtime-version bump. Migrate both prior save schemas to 9 with deterministic defaults. At the old dungeon entrance, move the old 75 gold into the shared hub balance exactly once.
- [x] Migrate an old schema-8 profile envelope only after verifying its stored digest against the original schema-8 payload. Keep envelope version 1; leave local-only profiles local-only, and mark a linked migrated profile pending so its schema-9 payload can advance from its existing remote revision. Preserve old conflict evidence; do not silently rewrite immutable evidence or trust a recomputed digest in place of the old one.
- [x] Keep historical schema-8 remote revisions immutable and readable. Validate their original payload digest as received, then allow the current client to advance the profile to schema 9 using the existing revision ancestry contract. Reject unsupported/downgrade writes as appropriate to the existing profile-service contract; do not rewrite old revisions or create a new API/DB version.
- [x] Ensure new schema-9 documents use exact-shape validation. Test malformed companion IDs, duplicate party members, invalid amounts/items, impossible phase/resource combinations, migration non-mutation, lost-response replay, and schema-8-head-to-schema-9 progression.
- [x] **Verify:** Run focused save, legacy migration, envelope, conflict, remote-client, profile-sync, and profile-service tests before continuing.

## Gate 2: Hub and Recruitment Flow

- [x] **Red:** Add failing presenter/session tests for hub arrival, the three eligible companion choices, recruitment, Ready, and stale/forged/unaffordable selections.
- [x] **Green:** Add explicit renderer-neutral hub/recruitment/ready phases and typed semantic inputs for selecting a companion and confirming the offered hub action. Python must reject stale, unoffered, duplicate, or unaffordable selections.
- [x] Transition from the existing surface route's dungeon entrance to the dungeon hub. Preserve the authored route text/result and transfer the 75-gold balance once.
- [x] Offer the three non-lead Drifters from the authoritative roster; show each name/archetype and current shared gold/cost. Selecting one charges 65 and establishes a two-member party. Require an explicit Ready/Set Out action before the encounter begins.
- [x] Add terminal presenter/UI coverage for hub arrival, choices, recruitment, insufficient funds, Ready, and Back/cancel behavior. Keep the main route and the hub as distinct location/phase states.
- [x] Add session tests proving inactive route actions and Battle actions are not offered in the hub, and that direct forged inputs cannot bypass recruitment legality.

## Gate 3: Three-Goblin Party Battle and Dexterity Queue

- [x] **Red:** Add failing content and battle tests for an authored three-Goblin encounter and a party of two using existing battle inputs; include one-player regression assertions.
- [x] **Green:** Add the authored dungeon encounter containing exactly three Goblins and regenerate `_generated_catalog.py`; verify the source/catalog consistency test. Extend `Battle` to accept a party while retaining its current single-`PlayerState` constructor behavior for existing encounters. Track living ally and enemy combatants in one individual-turn queue, ordered by current effective Dexterity, highest first.
- [x] Replace side-based initiative for party combat with individual actors. Every Drifter gets their own action opportunity; each Goblin gets its own enemy action. Keep automatic enemy turns automatic between player input opportunities.
- [x] On equal Dexterity, use the injected RNG to select a fair ordering for the tied actors; stabilize that order until a relevant stat change or the next round. After an accepted Dexterity change, rerank only the remaining unacted actors. Never repeat an actor that already acted this round.
- [x] Preserve the current actor's own moves, mana, Super, status effects, equipment, and HP. Enemy actions target a living Drifter using the injected RNG; test defeated allies are never selected. Keep all existing one-player battle results unchanged.
- [x] **Red/Green:** Drive implementation with deterministic assertions for the agreed `6 -> 5 -> 4 -> 3` interleaving, a tie, a controlled Dexterity change that reranks the remaining queue immediately, dead actors being skipped, victory/defeat when one or both Drifters fall, and no duplicate turns. Do not add a new move to create the test condition.
- [x] **Red:** Add view/presenter/UI contract tests showing the active Drifter, all party status, stable ally target IDs, and existing single-player compatibility before changing projections.
- [x] **Green:** Extend `BattleView` with the active Drifter and party context without losing the existing `player`/single-enemy compatibility accessors. Project each party member's current status and give party targets stable IDs for existing target inputs.
- [x] Run battle engine/model/presenter/UI test subsets before touching the web renderer. Focused result: 80 tests passed.

## Gate 4: Extraction, Reward Ownership, and Failure

- [x] **Red:** Add failing session tests for explicit extraction after victory, delayed reward grant, exact-once bank, full HP/Mana restoration on return (starting with injured and drained Drifters), tutorial defeat reset, and rejection of any unoffered second outing.
- [x] **Green:** On victory against the three Goblins, stop at an explicit Extraction phase. Show the authoritative encounter result and the pending rewards; offer the hub-return action. Do not advance to another route node or start another battle automatically.
- [x] Keep EXP, gold, and any authored item reward in the outing ledger until the player confirms return. On return, bank gold/items in the shared party inventory and award EXP evenly to both Drifters (60 each for the 120-EXP tutorial encounter). Mark the tutorial complete and return to the hub.
- [x] Test that leaving the extraction choice pending does not prematurely award or bank the same reward twice; returning twice must be rejected as stale/unoffered.
- [x] On defeat during the safe tutorial, discard that attempt's outing ledger and return to the existing Drifter-selection flow so the tutorial restarts from the authored surface beginning.
- [x] Keep the hub as the end state after extraction in this milestone. Restore each party member's HP and Mana to full on return. Preserve the secured rewards in the game state/save; do not offer an unimplemented second outing or create a repeatable Goblin reward loop.
- [x] Add transition tests around victory-before-extraction, extraction, tutorial defeat/reset, and serialized state reload. Combined Gate 3/4 + persistence regression result: 268 passed.

## Gate 5: Terminal and Browser Parity

- [x] **Red:** Add terminal and browser bridge contract tests for the same hub/recruitment/Battle/extraction sequence and authoritative offered options.
- [x] **Green:** Update terminal Battle rendering to show both Drifters and the enemies while clearly identifying the currently acting Drifter. Preserve existing contextual action/move/target/inventory phases. Extend the browser bridge only to translate the new semantic inputs and project the new authoritative views. JavaScript must not compute turn order, rewards, recruitment legality, or phase transitions.
- [x] Render hub, companion choice, ready-up, Battle party status, extraction choice, and return-to-selection in the existing browser experience. Reuse the existing Drifter selection screen after tutorial defeat; do not add a second browser-only game state or restart shortcut that skips selection.
- [x] **Red/Green:** Extend Python bridge contract tests in `root/web_tests` and the existing Playwright full-route smoke to select a starting Drifter, reach the hub, recruit a different Drifter, ready, finish the three-Goblin encounter, extract, and verify both party membership and secured rewards. Preserve current desktop/mobile rendering and selection behavior.

## Gate 6: Cumulative Qualification

- [x] Run focused tests from every prior gate, then the complete Python suite and complete web pytest suite.
- [x] Run the profile-service suite against real PostgreSQL, including migration-from-zero and Alembic drift checks; verify schema-9 save payloads round-trip through create/progression/sync paths.
- [x] Rebuild the static browser site and run the pinned Playwright browser smoke against the built site. Confirm the scenario uses Python-authoritative state end to end.
- [x] Run the actual pinned MicroPython qualification applicable to the shared game/runtime changes, not only synthetic parser tests. Record the observed semantic parity and memory results; keep the existing probe marker protocol unchanged.
- [x] Run content validation, compile checks, repository-wide Python tests, and `git diff --check`. Report exact observed test totals and runtime qualification results; do not predeclare counts.
- [x] Review the final diff for unintended gameplay changes, duplicated lead state, unversioned save fields, browser-owned rules, or tests placed outside their required suites. Stop for user review before committing or pushing.

**Observed qualification (2026-10-16):** 1,621 game tests, 46 web tests, and 27 profile-service tests against PostgreSQL passed. The 134-file site build and full Playwright route passed; content validation, compileall, and `git diff --check` passed; Alembic reported no schema drift. On the exact reviewed tree, the pinned MicroPython matrix passed CPython, forced-overlay, and default-runtime probes, but the 448K route qualification failed while building the `surface_goblin_lord` BattleView: allocation of 136 bytes failed with 13,840 bytes reported free. The 416K frontier was not run. At that checkpoint Gate 6 remained open pending investigation and a passing 448K rerun.

**Follow-up qualification (2026-10-17):** The pinned executable at `%LOCALAPPDATA%\DungeonDrifters\micropython\v1.29.0\source\ports\windows\build-standard\micropython.exe` matched the recorded 488,960-byte artifact and SHA-256 `6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA`. The final probe matrix passed CPython native, forced-overlay CPython, default MicroPython, 448K, and semantic parity; 448K was stable 3/3 and 416K reached the expected memory limit 3/3, ending with `MYP20|RESULT|CLOSURE_COMPLETE`. An instrumented earlier retry showed fragmentation at `SESSION_IMPORT` (9,264 GC bytes free; largest free run 11 blocks against a 660-byte allocation). The probe now releases completed standalone-battle/game evidence before importing the session and creates that session's game during `SESSION_CONSTRUCTION`, without changing the marker sequence. The final raw 448K run completed the route, Goblin Lord, Hub recruitment, three-Goblin battle, extraction, and teardown with a lowest reported free heap of 24,480 bytes. On the same working tree, 1,648 Python tests and 47 web tests passed; content validation passed; compileall passed for accessible project Python files outside generated pytest-cache fixtures; the 134-runtime-file browser build and full Playwright Hub outing/defeat-reselect route passed; and `git diff --check` passed. The previously recorded PostgreSQL service and migration checks (27 tests, migration-from-zero, no Alembic drift) remain green; the Docker engine pipe was unavailable for a local repeat during this follow-up. Gate 6 qualification is complete for this probe contract; the measured heap is not a product-device memory requirement.

## Acceptance Criteria

- The existing surface route still completes normally and provides exactly 75 gold before hub entry.
- At the hub the player can choose any one of the other three Drifters, pay exactly 65 gold, and explicitly ready the two-person party.
- The tutorial fight contains exactly three Goblins. Every living actor receives one turn per round in the current Dexterity order, with immediate unacted-queue reordering after a Dexterity change and fair RNG tie ordering.
- Battle and extraction are separate phases. The player explicitly returns to hub; successful extraction banks rewards exactly once, restores both Drifters to full HP and Mana, and awards the tutorial's 120 EXP as 60 EXP per Drifter.
- Tutorial defeat returns to Drifter selection and restarts the tutorial. The first successful extraction returns to the hub, fully restores party HP and Mana, and secures rewards; there is no second outing in this milestone.
- Old save schemas migrate without loss of the existing lead, route progress, or gold. Schema-9 party/hub state round-trips locally and through the existing profile API without envelope/API/database version changes; an existing local schema-8 profile migrates with its original digest verified, and an immutable remote schema-8 head can be advanced without rewriting its history.
- Terminal and browser consume the same Python-authoritative choices and transitions; existing single-Drifter route behavior remains covered and green.

## Review Focus

Before implementation, review especially the additive save shape, preservation of old schema-8 saves/profiles already at the dungeon entrance, and the legacy-envelope/cloud-head upgrade path. Goblins use uniform random targeting among living Drifters until enemy AI is developed; successful extraction restores party HP and Mana to full. Later-outing warnings/loss behavior and its exact copy stay deferred, though the design direction is that later-run death returns to the hub with HP and Mana fully restored. This is intentionally a first-extraction plan, not the full dungeon loop.

# Floor One Dangerous Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the repeatable, dangerous Floor 1 expedition with ten battles, two rest checkpoints, early extraction, death loss, boss completion, and replay XP reduction.

**Architecture:** Keep Python authoritative and extend the existing authored-route, `OverworldSession`, `PartyState`, and save-document boundaries. The route cursor lives in `OverworldState`; the existing party state owns the two-Drifter run, unsecured rewards, Floor 1 clear, and replay count. Terminal and browser consume the same presenter options and session transitions.

**Tech Stack:** Existing Python game/content/runtime, dataclass presentation models, generated content catalog, terminal UI, Pyodide browser bridge/renderer, existing local/profile save pipeline, pytest, Playwright, pinned MicroPython 1.29.0 probe, PostgreSQL profile-service tests.

**Spec:** [floor-one.md](floor-one.md)

## Global Constraints

- Floor 1 has ten battles; the two Rests are after battles 5 and 9, and battle 10 reuses the existing Goblin Lord encounter.
- Battles 1-9 contain only existing Goblins, in groups of one to four; encounter counts are placeholder balance content.
- The current two-Drifter party remains fixed; roster selection and swapping are separate work.
- Early extraction pays half of adjusted XP and gold, rounds fractional gold up, and retains all run items; death loses all unsecured run rewards.
- Rest extraction and death return the party to the Hub with full HP and Mana; boss victory banks all remaining rewards and clears Floor 1.
- Replays after the first Floor 1 clear use XP rates 50%, 40%, 30%, then 20% for every later run; gold has no replay reduction.
- Keep the save envelope at version 1, profile API at `/v1`, database schema, and persistence-provider architecture unchanged. Add a forward game-state migration if needed.
- Keep Python authoritative; browser code only translates inputs and renders returned views.
- Do not add Floor 2, new enemy archetypes, enemy AI, shop/supply systems, new combat rules, or roster swapping.
- Treat MicroPython heap values as probe-pressure settings, not product-device requirements. The Floor 1 extension is qualified at the measured 512K/480K boundary; do not distort gameplay architecture to preserve the earlier 448K probe target.

## Review Focus

- **Rest checkpoint:** Only the two authored Rest nodes are saveable during a Floor 1 outing; loading restores the party, node, rewards, and Rest menu. Pin with `test_floor_one_rest_save_load_resumes_at_same_checkpoint` and `test_floor_one_outing_save_is_rejected_away_from_rest`.
- **Rest-exit durability:** Before Recover or Continue, persist a forfeited Hub fallback; before Extract, persist the completed partial payout in the Hub. If that write fails, the live session remains unchanged at the Rest. Pin with `test_floor_one_rest_exit_stays_at_rest_when_fallback_save_fails`, `test_floor_one_continue_persists_independent_safe_hub_before_advancing`, and `test_floor_one_extract_persists_banked_rewards_before_leaving_rest`.
- **Death after save:** A death after continuing from a saved Rest replaces that save with the Hub outcome, full resources, and no pending rewards. If the final outcome write fails, loading still returns the safe Hub fallback. Pin with `test_floor_one_death_supersedes_saved_rest_checkpoint` and `test_death_save_failure_cannot_restore_the_previous_rest_checkpoint`.
- **Floor 1 Map:** Progress uses the active route cursor, not Surface encounter history; nodes before the cursor are complete, the cursor is current, and later nodes remain. Pin with `test_floor_one_map_tracks_active_route_cursor_not_surface_defeats`.
- **Early-extraction arithmetic:** Apply the replay XP rate, then the half payout; floor each Drifter's equal XP share to an integer and round half-gold upward. Pin odd XP/gold cases with `test_floor_one_partial_extraction_rounding_and_item_retention`.
- **Replay attempt accounting:** A run consumes its replay rate when Set Out is confirmed, including runs ended by death or early extraction; rates clamp at 20%. Pin with `test_floor_one_replay_rates_advance_on_every_started_run`.
- **Repeated encounter identity:** Reusing the same Goblin encounter and the surface Goblin Lord must not be rejected as an already-defeated world encounter. Pin with `test_floor_one_route_replays_reused_encounter_specs`.

---

## File Map

- `root/src/app/content/routes/floor_one/route.py`: authored 12-node Floor 1 route.
- `root/src/app/content/encounters/dungeon_goblin_quad/encounter.py` and generated `root/src/app/content/_generated_catalog.py`: Goblin-only four-enemy encounter and catalog entry.
- `root/src/app/game/overworld_state.py`: active route, route cursor, and per-run Rest resolution.
- `root/src/app/game/party_state.py`: Floor 1 clear/replay metadata, unsecured rewards, extraction, and death outcome.
- `root/src/app/game/overworld_session.py`: warning, route battles, Rest actions, extraction, defeat, boss clear, and save/reload screen restoration.
- `root/src/app/presentation/overworld_models.py`, `root/src/app/presentation/overworld_presenter.py`, `root/src/app/ui/overworld_ui.py`, `root/src/app/ui/terminal_overworld_ui.py`: warning and Rest menu choices using existing view/input patterns.
- `root/src/app/snapshot.py`, `root/src/app/persistence/save_document.py`, `root/services/profile_api/src/profile_api/save_contract.py`: strict forward state migration and current-payload validation without changing envelope/API/database versions.
- `root/web/python/dd_bridge.py`, `root/web/play/js/pyd4.js`, and focused styles only if needed: semantic command translation and screen rendering.
- `root/tools/micropython_hub_probe.py`, `root/tools/micropython_probe.py`, `root/tests/test_micropython_route_probe_contract.py`, `docs/probe.md`: extend the real runtime probe through Floor 1 and record exact results.
- Focused tests in `root/tests/test_route_content.py`, `root/tests/test_overworld_state.py`, `root/tests/test_floor_one_run.py` (new), `root/tests/test_overworld_presenter.py`, `root/tests/test_save_state.py`, `root/tests/test_profile_sync.py`, `root/services/profile_api/tests/test_profiles.py`, `root/web_tests/test_browser_bridge_contract.py`, and `root/web_tests/browser_smoke.mjs`.

## Task 1: Author Floor 1 and Route State

**Files:** Create the Floor 1 route and four-Goblin encounter above. Modify `root/src/app/game/overworld_state.py` and generated catalog. Test `root/tests/test_route_content.py` and `root/tests/test_overworld_state.py`.

**Interfaces:** Add `OverworldState.begin_route(route_id: str) -> None`; it selects the authored route's first node and resets that route's resolved Rest nodes. Keep `advance_to(node_id: str, *, contextual_phase=...)` restricted to the immediate successor of the active route. Add `active_route_id` to the state snapshot. Preserve all existing Surface route behavior and Surface Rest ordering.

- [x] **Step 1: Write failing route tests.** Assert the exact node sequence has 5 `COMBAT`, Rest, 4 `COMBAT`, Rest, and one `BOSS` node; the Rest nodes follow battles 5 and 9; each of the first nine encounters contains only the existing Goblin archetype with counts from one to four; and the final node references `surface_goblin_lord`. Use the placeholder composition `4, 3, 2, 1, 4 | Rest | 2, 3, 4, 3 | Rest | Goblin Lord`.
- [x] **Step 2: Run `python -m pytest tests/test_route_content.py -q` from `root/`.** Confirm the new route/content assertions fail.
- [x] **Step 3: Add the authored route and `dungeon_goblin_quad`; regenerate the catalog with `python tools/generate_content_catalog.py` from `root/`.** Do not duplicate enemy definitions or create a new archetype.
- [x] **Step 4: Write failing route-state tests** for switching to Floor 1, immediate-successor enforcement, Rest tracking, resetting Rest tracking on a new run, and retaining Surface state compatibility.
- [x] **Step 5: Implement the route cursor extension and run `python -m pytest tests/test_route_content.py tests/test_overworld_state.py -q`.** Confirm both new and existing route tests pass.

## Task 2: Party Run Ledger and Payout Rules

**Files:** Modify `root/src/app/game/party_state.py`. Test in new `root/tests/test_floor_one_run.py` and existing `root/tests/test_hub_extraction.py`.

**Interfaces:** Add `start_floor_one_run() -> int`, `add_floor_one_rewards(*, experience: int, gold: int, items: dict | None = None) -> None`, `begin_floor_one_extraction(*, partial: bool) -> bool`, `complete_floor_one_boss(party_members: tuple[PlayerState, PlayerState]) -> bool`, and `fail_floor_one_run(party_members: tuple[PlayerState, PlayerState]) -> bool`. Expose persisted `floor_one_cleared`, `floor_one_runs_started_after_clear`, and the active run's `outing_xp_multiplier_percent`.

- [x] **Step 1: Write failing state tests** for invalid start phases, first-clear state, replay rates `100, 50, 40, 30, 20, 20`, counter advancement on every confirmed replay start, raw reward accumulation, and no reward leakage after failure.
- [x] **Step 2: Run `python -m pytest tests/test_floor_one_run.py -q` from `root/`; confirm failure.**
- [x] **Step 3: Implement the Floor 1 ledger and replay counter** without changing the safe tutorial's recruitment, extraction, or defeat reset.
- [x] **Step 4: Write payout tests** showing full boss payout, early extraction at half of adjusted XP/gold, all items retained, gold rounded upward, and equal whole-number XP for both Drifters. If the equal-share result has a fractional XP remainder, floor each Drifter's share equally; do not award an extra point to one member.
- [x] **Step 5: Implement payout preparation, exact-once banking, boss clear, and death reset.** Death clears unsecured rewards, preserves shared resources/party/clear progress, restores both Drifters, and returns `PartyState` to `HUB`.
- [x] **Step 6: Run `python -m pytest tests/test_floor_one_run.py tests/test_hub_extraction.py -q`.** Confirm new behavior and safe tutorial regressions pass.

## Task 3: Dangerous Run Session Flow

**Files:** Modify `root/src/app/game/overworld_session.py`, `root/src/app/presentation/overworld_models.py`, and `root/src/app/ui/overworld_ui.py`. Test `root/tests/test_floor_one_run.py` and `root/tests/test_overworld_session.py`.

**Interfaces:** Add `OverworldScreen.FLOOR_ONE_WARNING` and `OverworldAction.START_FLOOR_ONE`, plus `OverworldAction.SET_OUT` to confirm the warning. Hub exposes Start Floor 1 after tutorial completion; the warning offers only Set Out and Back. Display: "Death means returning to the Hub. All unsecured XP, gold, and items are lost. No retry, rewind, or continue." Set Out begins the run and first encounter. Reuse existing `ENTER_ENCOUNTER`, `REST`, `SKIP_REST`, and `RETURN_TO_HUB` semantics where suitable; add `OverworldAction.EXTRACT` for the Rest extraction choice.

- [x] **Step 1: Write failing session tests** for Hub -> warning -> explicit Set Out, four-Goblin opening battle, each subsequent route encounter, and stale/unoffered actions.
- [x] **Step 2: Run the focused new tests and confirm failure.**
- [x] **Step 3: Implement warning and route dispatch.** On each victory, add the authored encounter rewards to the unsecured ledger and advance exactly once. Do not add these repeated encounter IDs to the global Surface defeated-encounter set.
- [x] **Step 4: Write failing outcome tests** for defeat after a checkpoint, early extraction, first boss clear, all pending rewards, full party restoration, and post-clear replay. Include an already-defeated `surface_goblin_lord` in the Surface world state before reaching the Floor 1 boss.
- [x] **Step 5: Implement Floor 1 transitions and fail-closed Rest exits.** Before Recover or Continue advances beyond a Rest, persist an independent Hub fallback with the run forfeited; before Extract, persist an independent Hub state with the partial payout banked. If the fallback write fails, leave the live state at the Rest. Defeat, extraction, and boss completion reset the active route to the Surface entrance while preserving Surface completion and Floor 1 progress; a later Set Out starts Floor 1 from its first node. Boss victory immediately banks all remaining adjusted rewards, restores the party, records Floor 1 cleared, and returns to Hub.
- [x] **Step 6: Run `python -m pytest tests/test_floor_one_run.py tests/test_overworld_session.py tests/test_hub_flow.py tests/test_hub_extraction.py -q`.**

## Task 4: Rest Choices and Inspection

**Files:** Modify `root/src/app/presentation/overworld_presenter.py`, `root/src/app/game/overworld_session.py`, and `root/src/app/ui/terminal_overworld_ui.py`. Test `root/tests/test_overworld_presenter.py`, `root/tests/test_terminal_overworld_ui.py`, and `root/tests/test_floor_one_run.py`.

- [x] **Step 1: Write failing presenter/session tests** for Rest offering Recover, Save, Character, Items, Continue Without Rest, and Extract; only Recover heals both party members; Continue advances without healing; Save is unavailable outside Rest; Extract uses the correct payout; and returning from Character/Items resumes the same Rest.
- [x] **Step 2: Run the focused tests and confirm failure.**
- [x] **Step 3: Add the Rest options and return-navigation behavior** using existing semantic actions and current Character/Items views. Do not add party swapping, a new equipment flow, or a new inventory system.
- [x] While an outing is active, project the current Floor 1 node as the location instead of labeling it "Floor 1 Hub"; keep Hub location text after extraction or defeat.
- [x] **Step 4: Restore a loaded `OUTING` save at either Rest directly to the Rest view** with the same route node and unresolved Rest choice. Keep existing Surface Rest and tutorial extraction screens unchanged.
- [x] **Step 5: Run `python -m pytest tests/test_overworld_presenter.py tests/test_terminal_overworld_ui.py tests/test_floor_one_run.py -q`.**

## Task 5: Save Schema and Profile Compatibility

**Files:** Modify `root/src/app/snapshot.py`, `root/src/app/persistence/save_document.py`, `root/services/profile_api/src/profile_api/save_contract.py`, `root/tests/test_save_state.py`, `root/tests/test_profile_sync.py`, and profile-service save-contract tests.

- [x] **Step 1: Add failing migration and validation tests** for prior schema-9 Hub saves and local envelopes with verified original digests, schema-9 saves at the Surface entrance, schema-10 Floor 1 state, valid saves at either Rest, rejected battle-node `OUTING` saves, invalid clear/run-count/cursor combinations, and immutable schema-9 cloud heads advancing without rewriting history.
- [x] **Step 2: Run focused save/profile tests and confirm failure.**
- [x] **Step 3: Bump runtime `STATE_SCHEMA_VERSION` from 8 to 9 and disk `DISK_SCHEMA_VERSION` from 9 to 10.** Migrate schema 9 forward with deterministic Floor 1 defaults and `active_route_id="surface"`; retain schema-7/schema-8 migration, including the old schema-8-with-party case, and original digest validation behavior. Preserve envelope version 1.
- [x] **Step 4: Extend exact-shape validation and reconstruction** for active route, Floor 1 progress, replay multiplier/counter, unsecured rewards, and the only saveable dangerous-run location (the two Rest nodes). Continue rejecting unsaved battle state.
- [x] **Step 5: Update profile payload validation** to accept current schema 10 while preserving immutable historical schema 8 and 9 reads. Keep `/v1` and database models/migrations unchanged. Add service tests that create/progress schema 10 and advance an immutable schema-9 head.
- [x] **Step 6: Run `python -m pytest tests/test_save_state.py tests/test_save_document_boundary.py tests/test_profile_sync.py -q` from `root/`, then `python -m pytest tests` from `root/services/profile_api/` against PostgreSQL.** Run migration-from-zero and `python -m alembic check` against the dedicated migration database.

## Task 6: Terminal, Browser, and Runtime Probe Parity

**Files:** Modify `root/web/python/dd_bridge.py`, `root/web/play/js/pyd4.js`, `root/web_tests/test_browser_bridge_contract.py`, `root/web_tests/browser_smoke.mjs`, `root/tools/micropython_hub_probe.py`, `root/tools/micropython_probe.py`, `root/tests/test_micropython_route_probe_contract.py`, and `docs/probe.md`.

- [x] **Step 1: Write failing bridge/browser contracts** proving that Python offers the warning, Rest, extraction, and Hub-clear options; JavaScript submits only semantic actions; and the rendered flow reaches the dangerous route through the existing browser runtime.
- [x] **Step 2: Extend browser rendering and the smoke flow** for the warning, ten battles, both Rests, early extraction and a boss-clear path. Use deterministic test setup for combat outcomes; do not implement game rules in JavaScript.
- [x] **Step 3: Extend the pinned MicroPython probe through the full Floor 1 loop** after the existing tutorial extraction: complete nine Goblin battles, exercise both Rest transitions, defeat the Goblin Lord, and assert the cleared Hub state, secured rewards, XP split, and full HP/Mana. Keep all existing marker names/protocol intact; add stages only.
- [x] **Step 4: Update probe-contract tests** to assert ordering and that route-owned temporary battle evidence is released before later memory-sensitive stages. Record the exact executable identity and the measured 512K repeated result and 480K frontier result in `docs/probe.md`; preserve the earlier 448K/416K Hub-only result as historical evidence and do not label a different binary as pinned evidence.
- [x] **Step 5: Run `python -m pytest web_tests -q` from `root/`; build the site with `python tools/build_browser_site.py --output web/dist`; run `node web_tests/browser_smoke.mjs` against that build. Run the actual pinned runtime matrix and record observed results.**

## Task 7: Cumulative Qualification and Review

- [x] Run focused tests from each task, then `python -m pytest` and `python -m pytest web_tests` from `root/`.
- [x] Run content validation with `python -m tools.validate_content`, compile Python sources while excluding generated pytest cache fixtures, and run `git diff --check` from `root/`.
- [x] Run profile-service tests against real PostgreSQL, migration-from-zero, and Alembic drift check; confirm no database migration was added.
- [x] Run the built-site Playwright smoke and exact pinned MicroPython matrix on the final implementation tree, including three 512K full-loop passes and three 480K memory-limit confirmations. Record exact observed totals; do not infer results from earlier commits or a different executable.
- [x] Review the cumulative diff for unchanged Surface/tutorial behavior, exactly two Floor 1 Rests, no reward banking before extraction/boss, no rewind after death, correct 50/40/30/20 replay progression, unchanged save envelope/API/database versions, and no browser-owned rules. Stop for user review; do not commit or push without a separate request.

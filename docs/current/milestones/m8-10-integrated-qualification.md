# M8.10: Integrated Campaign Qualification

**Status:** CLOSED AND SEALED at final qualification SHA `745ea4fd91f1affeb5ee2d7c6b11afc1ebfca747`. The owner accepted the final independent PASS on 2026-11-28. Exact-SHA hosted CI [46138482393](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/46138482393) passed. The pinned-runtime evidence was freshly qualified on runtime candidate `4eef22af3b87067fe22a48ec3ee58627a7f71f74`; the final candidate changes only documentation and tests.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `4b37cbdb9aa581c8c34e47e3a2aeece7c9af11d2` (M8.9 sealed baseline).

## Goal

Prove the complete approved Floors IV–V expansion as one persistent, terminal/browser-parity campaign loop and publish the final M8 closure record.

## Approval Boundary

**Already-approved inputs:** all previously sealed M1-M7/M6.5 contracts remain regression-protected; only approved M8 manifest rows may be qualified as delivered.

**Decision status:** the finite M8-D1 manifest, all four M8-D3 fact/reveal mappings, and D2/D4/D5/D6 are approved as recorded in the parent. This package verifies only those approved rows and cannot add or omit content. Region 2's eventual name, routes, and playable release are future work and are not prerequisites for this M8 qualification.

## Qualification Journeys

- Use the normal Hub Region Portal in new and eligible migrated saves. Verify explicit Region 1 membership for Surface/Floors I-V, matching region/destination availability in terminal/browser, and Region 1 remains reachable after later unlocks.
- New and migrated profile reaches Floor IV through the existing Floor I–III/recruitment sequence; verify no early unlock or changed prior behavior.
- Complete Floor IV, use its discoveries/rewards and eligible expedition reports, then enter Floor V with a legal pair.
- Complete the Floor-V approach, persist the approved arena-availability evidence, settle any assignment under its approved rules, and launch the all-four reunion.
- Clear the D1-approved Ashen Regent reunion boss, verify XP/Intuition and approved rewards, record Floor-V completion once, and separately verify durable Region 2 unlock. Return to Hub; the portal must show Region 2 unlocked but unavailable while it has no route, and must continue to offer eligible Region 1 content.
- Reload and repeat portal navigation. Verify no Floor VI/empty route is enterable, returning to Region 1 does not clear newer progress or duplicate rewards, and Region 2 remains unlocked.
- Exercise failed writes, reload/retry, stale/duplicate actions, legacy migration, and uncaught qualification findings across the integrated journey.

## Scope And Dependencies

This is qualification and closure, not a container for unfinished features or silent fixes. M8.1–M8.9 must each have a reviewable closure record. Any defect reopens its owning child package; changes receive a new exact SHA and cumulative requalification. No feature expansion or new content is authorized here.

## Required Evidence

- Root pytest, web-contract pytest, Profile Service/PostgreSQL integration, migration-from-zero and Alembic parity.
- Authored-content validation, Python compile/build checks, browser build and real Playwright smoke.
- Verify all eight D6-approved static asset IDs resolve through the finalized content associations, with responsive presentation, accessibility text, and readable fallback behavior. Confirm terminal functionality and browser parity; no graphical combat renderer, animation, or combat-presentation engine is part of M8 qualification.
- Exercise the missing-enemy-portrait fallback during a real battle: force one approved portrait request to fail, verify the failed image and portrait-specific layout class are removed, enemy name/HP/status labels remain readable, and battle actions remain usable. Retain the existing destination-image fallback coverage.
- Pinned MicroPython qualification for the accepted final SHA; distinguish local from hosted evidence and report memory ceilings/results exactly.
- Terminal and browser semantic journeys, save/reload and no-duplicate reward/report/discovery proofs.
- Migration matrix proving older saves retain existing floor clears and initial-region access, gain no unearned Region 2 unlock, and follow the approved destination visibility/briefing path; exact-SHA portal travel/revisit and unlocked-but-unplayable Region 2 evidence.
- Independent full-diff review, all findings dispositioned, exact commit SHA, hosted CI URLs/results, and updated parent/child status ledger.

## D1-D6 Manifest Reconciliation

This crosswalk accounts for the complete approved manifest in the parent plan; it does not reduce or replace its stable IDs. All listed tests run through the authoritative Python game/session owners unless identified as real-browser smoke.

| Approved scope | Qualification evidence | Result |
| --- | --- | --- |
| D1: Region 1/2 ownership, destinations, prerequisites, migrated access, backward travel, revisit and unlocked-but-unplayable Region 2 | `test_region_progression.py`, `test_region_portal.py`, `test_floor_five_reunion.py`; real-browser marker `M8.1_BROWSER|REGION_PORTAL_FLOOR_I_RETURN_AND_BACKWARD_ACCESS|PASS`; the M8.10 browser journey reaches Region 2 after the Regent and returns to Region 1 | Passed. Region 2 remains unlocked but has no selectable route; no Floor VI route is exposed. |
| D1: Drowned Reliquary and Ashen Vault routes, every approved node/encounter ID and composition, four enemy archetypes, both bosses, pair/full-party restrictions and 48 Grade II-IV component recipes | `test_floor_four_content.py`, `test_floor_four_session.py`, `test_floor_five_approach.py`, `test_floor_five_reunion.py`, `test_weapon_content.py::test_every_weapon_slot_has_starter_and_all_four_grade_components`, `test_weapon_progression.py` (`test_all_m8_power_variants_project_through_the_existing_move_pipeline`, `test_all_m8_resource_cost_variants_project_without_global_cost_changes`), plus authored-content validation; browser markers `M8.3_BROWSER|FLOOR_FOUR_ENTRY_AND_PAIR|PASS`, `M8.3_BROWSER|FLOOR_FOUR_BOSS_CLEAR_AND_REWARDS|PASS`, `M8.7_BROWSER|APPROACH_RELIC_AND_ARENA_REVEAL|PASS`, and `M8.8_BROWSER|REGENT_CLEAR_REGION2_AND_FLOOR5_MATERIAL_LAUNCH|PASS` | Passed. Parent manifest IDs and compositions remain unchanged. |
| D1/D2: six optional pair scenes, Archive Memory and Reliquary Echo, including choices, participation, persistence and duplicate prevention | `test_m86_character_stories.py`; browser markers `M8.6_BROWSER|PAIR_STORY_CHOICE_RELOAD|PASS`, `M8.6_BROWSER|ARCHIVE_MEMORY_CHOICE_KNOWLEDGE_RELOAD_ONCE|PASS`, and `M8.6_BROWSER|STORY_REPORT_ECHO_COMPLETION_RELOAD_ONCE|PASS` | Passed. All eight approved scene IDs remain present; no mechanical relationship progression was added. |
| D3: four knowledge facts, briefing/entry/scouting/clear reveal sources, three permanent discoveries, active-target selection, frozen search outcomes and one-time claims | `test_region_progression.py`, `test_region_portal.py`, `test_m8_floor_four_rewards.py`, `test_floor_five_approach.py`, `test_m8_expeditions.py`; browser markers `M8.4_BROWSER|ANCIENT_WELL_ACTIVE_TARGETED_CLAIM|PASS`, `M8.4_BROWSER|FORGOTTEN_ALTAR_ACTIVE_TARGETED_CLAIM|PASS`, and the persisted archive-memory/scouting journey above | Passed. Claims and knowledge survive reload; failed writes and repeated claims are covered. |
| D4: event/world evidence instead of portable story-critical items; ordinary inventory ownership and historical saves remain intact | `test_floor_five_approach.py`, `test_floor_five_reunion.py`, `test_m8_expeditions.py`, discovery/reward migration tests in `test_m8_floor_four_rewards.py`; full root migration and save-validation suites | Passed. Arena reveal, Floor V clear, Region 2 unlock and reward evidence use their approved durable owners; no portable M8 key item was introduced. |
| D5: all seven report consumers, eligible sources, frozen outcomes, compatible Floor IV/approach assignment, assignment settlement and four-member reunion exclusion | `test_m8_expeditions.py`, `test_expeditions.py`, `test_floor_five_reunion.py`; browser markers `M85_BROWSER|FLOOR_FOUR_CATEGORY_AVAILABILITY|PASS`, `M85_BROWSER|FLOOR_FOUR_LAUNCH_AND_ENERGY|PASS`, and the M8.8 Regent/Material journey | Passed. Floor V Material remains gated on Floor V completion and the authored Regent Core source. |
| D6: both destination illustrations and all six enemy/boss portraits, their canonical associations, packaging, responsive presentation, accessibility and readable failures | `test_visual_assets.py`, the M8.9 delivered-asset manifest, browser marker `M8.9_BROWSER|STATIC_ASSET_RENDERING_FALLBACK_RESPONSIVE|PASS`, and M8.10 marker `M8.10_BROWSER|MISSING_ENEMY_PORTRAIT_TEXT_STATUS_ACTIONS|PASS` | Passed. All eight assets are delivered and packaged; no graphical combat renderer or animation system was introduced. |
| Terminal/browser semantic parity for M8 entry and settlement boundaries | New `test_terminal_portal_selects_floor_four_and_floor_five_semantically`; existing terminal pending-settlement retries in `test_floor_five_approach.py` and `test_floor_five_reunion.py`; real-browser campaign markers above | Passed. Terminal input selects the same canonical region/destination actions and enters the same authoritative paired routes; terminal settlement retry remains usable after reload. |

### Candidate Qualification Record

Candidate `4eef22af3b87067fe22a48ec3ee58627a7f71f74` passed exact-SHA hosted CI [46089857664](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/46089857664): 2,732 root tests, 97 web tests, content validation, compilation, browser build (213 runtime files), cumulative Playwright smoke, PostgreSQL integration, migration-from-zero and Alembic parity. The run checked out the exact candidate SHA. Its fresh pinned MicroPython v1.29.0 matrix passed native CPython, forced-overlay CPython, MicroPython, semantic parity, 1472 KiB stable 3/3 and 1216 KiB expected memory limit 3/3, using executable SHA-256 `6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA` (488,960 bytes).

The final closure candidate `745ea4fd91f1affeb5ee2d7c6b11afc1ebfca747` passed exact-SHA hosted CI [46138482393](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/46138482393): 2,733 root tests, 97 web tests, 55 profile-service tests, authored-content validation, compilation, browser build, cumulative Playwright smoke, PostgreSQL integration, migration-from-zero, and Alembic parity. The terminal portal regression and missing-enemy-portrait fallback both passed. The independent review accepted the D1-D6 crosswalk and M8.1-M8.9 closure records; no blocking findings or unresolved decisions remain.

The final candidate contains only documentation and a terminal qualification test; it does not change the runtime sources tested on `4eef22af3b87067fe22a48ec3ee58627a7f71f74`. The exact pinned MicroPython v1.29.0 matrix on that runtime candidate passed native CPython, forced-overlay CPython, MicroPython, semantic parity, 1472 KiB stable 3/3, and 1216 KiB expected memory limit 3/3. Executable SHA-256: `6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA` (488,960 bytes).

## Closure

M8 closes only when every approved manifest row is implemented or explicitly approved-deferred/excluded, all required exact-SHA qualification is green, no M8 child remains open, and prior sealed M1–M7/M6.5 behavior remains protected. A green subset or a reduced manifest without explicit approval is not closure.

Collect the originating packages' gameplay integration evidence at entry. M8.10 owns cumulative campaign, client and persistence journeys. Return missing live proofs to their named owners before closure.

## Package Gates And Qualification History

- **Gate A, qualification-plan approval:** Approved by the owner's direction to proceed after M8.9 closure on 2026-11-27. Gate 0 is closed; no D1-D6 decisions are to be reopened here.
- **Gate B, cumulative execution:** Complete. Runtime candidate `4eef22af3b87067fe22a48ec3ee58627a7f71f74` passed the pinned matrix; final qualification candidate `745ea4fd91f1affeb5ee2d7c6b11afc1ebfca747` passed exact-SHA hosted CI. The terminal portal regression closed the final identified client-coverage gap.
- **Gate C, independent audit and closure:** PASS. Final independent review found no blocking defects or unresolved product decisions; the owner accepted closure. M8.10 is CLOSED AND SEALED.

| Final qualification SHA | Hosted CI URL/results | Pinned MicroPython runtime candidate | Independent review | Status |
| --- | --- | --- | --- | --- |
| `745ea4fd91f1affeb5ee2d7c6b11afc1ebfca747` | [46138482393](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/46138482393): both jobs passed; 2,733 root, 97 web and 55 profile-service tests; cumulative browser smoke, PostgreSQL, migration-from-zero and Alembic parity passed | Runtime candidate `4eef22af3b87067fe22a48ec3ee58627a7f71f74`; exact pinned MicroPython v1.29.0, native/overlay and semantic parity passed; 1472 KiB stable 3/3; 1216 KiB expected-limit 3/3. Executable SHA-256 `6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA`. | Independent PASS; owner accepted | CLOSED AND SEALED |


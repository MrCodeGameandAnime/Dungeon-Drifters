# T0 Test Architecture Audit And Consolidation

**Status:** T0-A baseline and two local test-only consolidation passes. Current root, web, browser, PostgreSQL/migration, content/build, source-compilation, and pinned-runtime checks are green. T0 remains open pending the final manual ownership audit and exact committed/hosted revision evidence.

**Baseline:** `t0` at `2af6e59b21d1c187ca4f2833fde04f6dd6f44cf8`, 2026-10-29. The captured baseline inventory's 147 source hashes match that commit exactly; its aggregate test-source SHA-256 is recorded in [metrics before](metrics-before.json). Work remains on this existing branch. M1 has not begun. Production/game/service/client/runtime/tool code is read-only for this work.

## Measurement Contract

The measured Python test universe is `root/tests/`, `root/web_tests/`, and `root/services/profile_api/tests/`, including builders/support and independent expected data. The primary application denominator includes `root/src/` and `root/services/profile_api/src/`; the game-only denominator is also reported. All other non-test Python, including tools, portability code and migrations, remains in the separate non-test denominator. Tracked and non-ignored working-tree paths are measured with the same physical-line rule, including blanks/comments/data. No fixture relocation, generated file or formatting trick is credited as a behavioral reduction.

| Before measurement | Observed |
| --- | ---: |
| Total/tracked Python physical lines | 71,801 / 71,801 |
| Python test/support lines | 42,374 |
| Game application lines | 21,923 |
| Profile-service application lines | 1,135 |
| Combined application lines | 23,058 |
| Non-test Python lines | 29,427 |
| Test : combined application | 1.83771 |
| Test : game only | 1.93286 |
| Test : non-test Python | 1.43997 |
| Python test/support files | 147 |
| Files containing test functions | 142 |
| Test functions before parametrization | 1,409 |
| Median / nearest-rank 95th percentile file LOC | 206 / 710 |

[Metrics before](metrics-before.json) records the largest 25 files and exact denominator policy. [Module inventory](module-inventory.csv) covers every Python test/support file with measured LOC/functions, subsystem/layer, builders, repeated calls/assertions, snapshot coupling, provisional disposition and boundary-overlap notes. Structural facts come from AST parsing; a MERGE/REFACTOR candidate is not a finding that every test in its module is redundant. Every actual removal requires the separate named equivalence record.

## Baseline Runs

- Root pytest: **1,809 passed, 149.08 seconds**, in an isolated OS-temp fixture directory.
- Web pytest: **60 passed, 15.27 seconds**.
- Service/PostgreSQL: **31 passed, 25.77 seconds**, including real PostgreSQL concurrency and migration tests against a new T0-only PostgreSQL 17 container. Existing containers/databases are not used.
- Built-browser smoke: **PASS, 57.809 seconds**; the unchanged built site exercised its existing qualification journeys.
- Collected executed cases across these suites: **1,900**. Function count and parametrized case count are deliberately separate.

Raw JUnit/log/AST records are generated in ignored test output under `root/.pytest-tmp-t0/`; they are not application code or added to the denominator. These are local baseline observations, not hosted CI claims.

### Environment Findings, Not Production Fixes

An initial root run using a generated-project temp directory beneath `root/` produced five scaffold-child import failures (1,804 other tests passed). Reproduction showed child pytest inherited the repository's parent `pytest.ini`/`pythonpath=src` rather than using only the copied project's source. An unchanged full run using an isolated OS-temp directory passed all 1,809. The diagnostic run took 231.42 seconds and is not reported as the green baseline. Required baseline/final fixture directories must remain isolated from the repository's parent pytest configuration.

The restricted process environment remaps local application-data paths, so the first browser attempt could not locate the installed Chromium. Running the unchanged smoke with the host environment passed. Use the recorded absolute pinned MicroPython path/identity rather than a remapped environment variable; do not substitute the stock executable. No production change is authorized by either observation.

## Architecture And Ownership Map

| Invariant family | Primary owner | Complementary boundary retained |
| --- | --- | --- |
| Resource bounds, stat scaling, GP costs | player/scaling/progression domain tests | Session delegates exact target; save validates/reconstructs source values |
| Move validation, spending, hit/crit, mitigation, Brace | resolver/combat-state tests | Representative Battle lifecycle and real terminal/headless/browser actions |
| Arcane/Frost/infusion/Storm identity and lifecycle | dedicated mechanic/status tests | Exact-target/multi-enemy and encounter cleanup integration remain separate failure boundaries |
| Immutable authored Drifter/weapon/enemy/route definitions | content tests and independent loadout oracle | Catalog validation/factory isolation, scaffolding and built artifact checks |
| Dexterity party turns and actor-owned resources | party Battle tests | Hub actor projection, terminal/browser representative party journey |
| Recruitment/Hub/Floor I transitions, rewards and recovery | PartyState/session/Floor I flow tests | Save checkpoint outcomes, failed-write/restart proofs, real browser route |
| Craft-and-install, slot gates, Tier V atomicity | weapon progression domain tests | Exact selected Drifter in session, validation at profile boundary, browser save/reload |
| Canonical source snapshots and supported legacy migrations | snapshot/save-document tests | Atomic local store/coordinator, service validation and immutable remote history |
| Sync ancestry/conflict recovery/local-first outcomes | sync/conflict fault-injection tests | Real service integration and PostgreSQL concurrency, not just memory remote |
| Identity recovery and immutable revision writes | service tests and real PostgreSQL concurrency/migrations | HTTP contract/account scoping and migration-from-zero/drift |
| Step-driven versus terminal compatibility runtime | representative headless/terminal runtime tests | Real built browser and actual pinned interpreter, not marker-parser mocks |
| MicroPython import/overlay/heap protocol | focused native/overlay contract tests | Actual pinned executable, parity, stable pressure/frontier observations |

The current lead-plus-companion representation is not obsolete merely because M1 will change it. Preserve tests that actually specify this sealed model; centralize setup so future changes do not require rewriting unrelated flows.

## Audit Findings And Consolidation Plan

### T0-B: Explicit Shared Setup

Repeated Hub/complete-tutorial/Floor I Rest construction is spread across Hub, extraction, terminal, save, session and weapon tests. Some helpers directly replace `_party_state`/`_overworld_state`, duplicating the very shape M1 will evolve. Introduce a small semantic builder module for valid game/Hub/recruited-pair/completed-Hub/Rest states, using domain transitions. Retain specific mutation/population at the test site. Do not hide the recruitment/transition under test inside a fixture for its primary owner.

Repeated scripted UI, deterministic RNG and fake battle scaffolding may be shared only where behavior is actually identical. RNG fallback/call recording, fake battle lifecycle timing and UI attribute semantics differ between modules; similar class names are not equivalence proof. Avoid one giant configurable harness or a test-only gameplay engine.

### T0-C: Unit/Contract Consolidation

The exact authored move data is repeated in per-class roster tests despite an independent all-field loadout oracle. Keep that oracle independent of production. Preserve unique spell classification and presentation metadata while merging redundant names/resources/kinds/cost assertions. Historical identity audit cases overlap current resolver/mechanic owners; map each specifically before moving/deleting, retaining source-boundary guards where unique.

Health/mana/status/move/validation matrices and equivalent Drifter/input/slot cases are parameterization candidates. Preserve distinct errors, mutation and RNG checks; do not merge unrelated action semantics solely to shorten code. Protected migration, schema, concurrency and runtime tests are not removal candidates without equivalent proof at the same boundary.

### T0-D: Flow Consolidation

Reduce repeated state construction and duplicated lifecycle assertions in old milestone flow modules, but retain separate blocking-terminal, step-driven/headless, multi-enemy target and party boundaries. Keep failed construction rollback, Rest recovery then extraction, no-rewind checkpoints, tutorial defeat/reselection, exact per-Drifter progression and repeat reward rejection. Existing historical filenames alone are no reason to delete.

### T0-E: Qualification

Preserve real browser save/reload and race protection, weapon save/reload, Floor I clear/replay extraction, real PostgreSQL immutability/concurrency/migration and pinned runtime qualification. Python tests that inspect browser source or parse probe markers are CONTRACT tests, not substitutes for these real QUALIFICATION runs. Service/qualification consolidation focuses on demonstrably repeated setup, not collapsing distinct engines or failure boundaries.

### T0-F: Closure

Re-measure with identical denominators, compare collected cases and every removed function against its named equivalent, review production-tree identity and test-case ownership, run all applicable local qualification, then report exact evidence and any remaining ratio exception. A passing smaller suite alone does not certify unchanged confidence. No test deletion is justified by the ratio target.

## Change Amplification

The structural constructor/reference scan is now recorded before and after. GameState construction fell from **38 modules / 121 calls** to **35 / 107**; PartyState from **3 / 12** to **2 / 11**. Snapshot references fell from **38 modules / 284 calls** to **37 / 284**; schema mentions fell from **16 / 63** to **15 / 61**. The snapshot call count is unchanged: direct snapshot tests remain concentrated in their owning state/save modules rather than being abstracted away. These are AST counts, not a semantic coverage score.

During consolidation, positional party construction was distinguished from deliberate roster/persistence assertions. The M1 thought experiment is not permission to rewrite the canonical roster now. Scenario-builder use in the current tree includes `game_at_hub` 23 calls, `hub_game` 10, `recruited_pair_game` 3, and `floor_one_rest_game` 1; test-specific transitions and rewards remain visible at callers. The remaining top GameState constructor sites are overworld session (25), terminal overworld (10), game state (8), overworld presenter (7), and M10c route integration (5). Remaining PartyState constructors are its own domain contract (9) and explicit Floor I party setup (2). Snapshot-heavy owners remain overworld session (24), overworld state (19), M11 session ownership/player snapshot/save state (17 each), and Floor I run (14). Schema-heavy owners remain save state (21), save coordinator (6), profile service/game snapshot/legacy migration (5 each). These are not all interchangeable setup.

### Measured First-Pass Result

| Measurement | Before | Current checkpoint |
| --- | ---: | ---: |
| All Python physical LOC | 71,801 | 70,696 |
| Tracked Python physical LOC | 71,801 | 70,696 |
| Test/support Python physical LOC | 42,374 | 41,269 |
| Combined application LOC | 23,058 | 23,058 |
| Game-only application LOC | 21,923 | 21,923 |
| Non-test Python LOC | 29,427 | 29,427 |
| Test : combined application | 1.83771 | 1.78979 |
| Test : game-only application | 1.93286 | 1.88245 |
| Test : non-test Python | 1.43997 | 1.40242 |
| Test/support files | 147 | 147 |
| Files containing test functions | 142 | 140 |
| Test functions | 1,409 | 1,387 |
| Root/web/service executed cases | 1,900 | 1,917 |
| Median / p95 file LOC | 206 / 710 | 198 / 692 |
| GameState constructor modules / calls | 38 / 121 | 35 / 107 |
| PartyState constructor modules / calls | 3 / 12 | 2 / 11 |
| Snapshot-coupled modules / calls | 38 / 284 | 37 / 284 |
| Schema-reference modules / mentions | 16 / 63 | 15 / 61 |

Net reduction at commit `131c217`: **1,105 physical test lines, 2.61%**. The first-pass metric artifact was captured before its new support file became tracked; the captured source inventory matches the committed tree exactly, so tracked and total Python LOC at that commit are both 70,696. No denominator was expanded.

[Metrics after](metrics-after.json), [actual changed-module dispositions](changed-module-dispositions.csv), [removed-test equivalence](removed-test-equivalence.md), and [qualification](qualification.md) distinguish measurements, semantic justification and observed execution. The initial module inventory remains a structural/provisional audit, not a claim that every existing test's unique failure has been manually proved.

### Repetition And Coupling

Baseline fixture use across test functions: `tmp_path` 120, `monkeypatch` 46, service fixture 22, valid-payload fixture 9. The only locally declared pytest fixtures are the service and valid-payload builders in service `conftest.py`. Most other setup is explicit constructors/helpers, not an implicit fixture graph.

Most frequent baseline construction calls: `PlayerState` 454, `create_drifter` 429, `EnemyState` 233, `CombatState` 178, direct `GameState` 120, `make_payload` 52. Related aliases make the constructor-coupling metric 121 rather than 120. Common scenario helpers include `_game` 25 calls, `game_at_hub` 23, `_game_state` and `_create_populated_game` 19 each. Identical names in different modules do not establish equivalent behavior.

Repeated assertion families include accepted-action success (35 `battle.player_action() is True`), one-turn completion (31), subprocess success (27), session quit (23), unchanged snapshot on rejection (20), no RNG before rejection (15), load success (13), and clean synchronization (13). These are candidate transaction/presentation contracts, not permission to delete assertions: different invalid targets, stores, lifecycle phases and runtimes expose different failure boundaries.

Largest remaining GameState coupling: overworld session 25 constructor calls, terminal overworld 10, game state 8, overworld presenter 7, and route/session integration 5 each. Remaining PartyState constructors are in its own domain contract (9) and explicit Floor I party setup (2). Snapshot-heavy owners remain overworld session (24), overworld state (19), session ownership/player snapshot/save state (17 each). Schema-heavy owners remain save state (21 references), save coordinator (6), service profiles/game snapshot/legacy migration (5 each). These are not all interchangeable setup.

### Second Local Review Pass And Ratio Gap

The current test-only working tree is based on `131c217676ce9f077493d093999dc645353faa7f`; its sorted test-source SHA-256 is `edf584d5283a6f74633468eb143fa1c177bc647986d87158e93184ddba669be1` in [metrics after](metrics-after.json). The first-pass committed test tree hashes to `199c99d03f786bcec6021600efc90cc26346be30dd863c79f9182b5273ee6836`. The earlier qualification note's `0a827...` digest was not reproducible from the captured inventory and is corrected there.

| Measurement | Baseline `2af6e59` | First-pass commit `131c217` | Current local tree |
| --- | ---: | ---: | ---: |
| All / tracked Python LOC | 71,801 / 71,801 | 70,696 / 70,696 | 70,573 / 70,558 |
| Test/support Python LOC | 42,374 | 41,269 | 41,146 |
| Combined application LOC | 23,058 | 23,058 | 23,058 |
| Test : combined application | 1.83771 | 1.78979 | 1.78446 |
| Test : game-only application | 1.93286 | 1.88245 | 1.87684 |
| Test : non-test Python | 1.43997 | 1.40242 | 1.39824 |
| Test functions | 1,409 | 1,387 | 1,384 |
| Test files / modules | 147 / 142 | 147 / 140 | 148 / 140 |
| Median / p95 test-file LOC | 206 / 710 | 198 / 692 | 194.5 / 692 |

Cumulative reduction from the clean baseline is **1,228 test/support lines (2.90%)**. At the unchanged combined application denominator, ratio 1.20 permits at most **27,669 test lines**; reaching it would require removing **13,477 lines**, or **32.75% of the current test tree**. The preferred 1.15 and ideal 1.0 targets are farther away. This is a measurement, not a deletion quota. The current aggregate includes one new, untracked 15-line test helper; tracked and total Python LOC are therefore reported separately.

The current Python test LOC, grouped by the inventory's primary layer, is:

| Layer | LOC | Files | Test functions |
| --- | ---: | ---: | ---: |
| Contract | 16,550 | 72 | 602 |
| Flow | 12,372 | 28 | 301 |
| Unit | 11,248 | 40 | 470 |
| Qualification | 772 | 4 | 10 |
| New shared support | 204 | 4 | 1 |

If flow, qualification and shared support are retained, the 13,477-line reduction needed for 1.20 would remove about **48.5% of the combined unit and contract layer**. Those layers contain the focused fail-closed, persistence/schema, migration, combat-rule and adapter-boundary proofs that the consolidation rules explicitly protect. This quantifies why the ratio cannot responsibly be treated as a deletion quota; the remaining per-module ownership audit is still required before asserting that no further safe reduction exists.

The second review consolidated explicit combat, status-lifecycle, and layout cases; shared exact combat fixtures, deterministic overlay-script launch, and content-validator process setup; and reviewed the large combat/Battle/UI owners and M11 defeat/retry cluster. The three retry flows are retained because they prove different real-Battle, party-rollback/reward, and boss/dungeon-completion boundaries. Structurally similar runtime overlay tests likewise enforce different module/import contracts. The dispositions and preserved failure modes are recorded in [changed-module dispositions](changed-module-dispositions.csv) and [removed-test equivalence](removed-test-equivalence.md).

The ratio remains high and the 2.90% LOC reduction is modest. The reviewed areas provide no basis for deleting another 13.5K lines without losing distinct test, persistence, client, service, or runtime boundaries. The baseline inventory is complete structurally, but its generated invariant/equivalence descriptions are not a substitute for a manual owner decision for every untouched module. That final review remains open. Do not claim the target is met. The cumulative local qualification has now been rerun on the current test tree; before T0 can close, finish the ownership review, preserve the ratio exception with evidence, and run hosted checks against the exact committed SHA.

No production defect was fixed. One test-fixture gap was corrected (a nominal hybrid test actually used magical damage); one invalid consolidation attempt exposed unsupported character-specific setup and was withdrawn. The browser readiness timeout remains an intermittent qualification observation, not a production change.

## Progress

- [x] T0-A: structural inventory, green baseline runs, ownership and consolidation candidates captured before test edits.
- [x] T0-B initial pass: justified shared scenario builders and identical strict RNG helper; focused cases and full-suite verification.
- [ ] T0-C: known equivalent unit/contract matrices and shared fixtures consolidated; complete manual per-module ownership review remains open.
- [ ] T0-D: Hub/Rest/Surface setup reduced; M11 defeat/retry candidates reviewed and retained for distinct failure boundaries; complete flow-owner review remains open.
- [x] T0-E local qualification: root/web pytest, browser smoke, PostgreSQL/concurrency, migration-from-zero, Alembic check, content/build, source compilation, and pinned MicroPython matrix rerun on the current test tree.
- [ ] T0-F: checkpoint metrics/equivalence/local qualification recorded; final ownership audit, ratio exception, and exact committed/hosted SHA remain open.

The current local root suite passed **1,825 tests in 161.52 seconds**. No application changes, new branch, M1 implementation, commits or pushes are part of this record. The exact local results are recorded in [qualification](qualification.md); there is not yet a new Git SHA or hosted result for the uncommitted test tree.

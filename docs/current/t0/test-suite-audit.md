# T0 Test Architecture Audit And Consolidation

**Status:** T0-A baseline plus an initial locally qualified consolidation pass. T0 is not closed: the LOC target and broader consolidation remain unfinished.

**Baseline:** `t0` at `2af6e59b21d1c187ca4f2833fde04f6dd6f44cf8`, 2026-10-29. Work remains on this existing branch. M1 has not begun. Production/game/service/client/runtime/tool code is read-only for this work.

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

The baseline inventory records GameState/PartyState constructor calls and snapshot/schema references per module. During consolidation, also distinguish positional party construction from deliberate roster/persistence assertions. The M1 thought experiment is not permission to rewrite the canonical roster now. Success means unrelated flow setup depends on a few valid semantic builders, while actual party/snapshot contracts remain explicit. Record before/after module counts and remaining intentional direct coupling at closure.

### Measured First-Pass Result

| Measurement | Before | Current checkpoint |
| --- | ---: | ---: |
| All Python physical LOC | 71,801 | 70,696 |
| Tracked Python physical LOC | 71,801 | 70,571 |
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

Net reduction: **1,105 physical test lines, 2.61%**. The 125 lines of new test/support Python are counted even though not yet tracked. No denominator was expanded. This is useful local cleanup, not a substantial suite-wide reduction or proof that the requested ratio is unattainable.

[Metrics after](metrics-after.json), [actual changed-module dispositions](changed-module-dispositions.csv), [removed-test equivalence](removed-test-equivalence.md), and [qualification](qualification.md) distinguish measurements, semantic justification and observed execution. The initial module inventory remains a structural/provisional audit, not a claim that every existing test's unique failure has been manually proved.

### Repetition And Coupling

Baseline fixture use across test functions: `tmp_path` 120, `monkeypatch` 46, service fixture 22, valid-payload fixture 9. The only locally declared pytest fixtures are the service and valid-payload builders in service `conftest.py`. Most other setup is explicit constructors/helpers, not an implicit fixture graph.

Most frequent baseline construction calls: `PlayerState` 454, `create_drifter` 429, `EnemyState` 233, `CombatState` 178, direct `GameState` 120, `make_payload` 52. Related aliases make the constructor-coupling metric 121 rather than 120. Common scenario helpers include `_game` 25 calls, `game_at_hub` 23, `_game_state` and `_create_populated_game` 19 each. Identical names in different modules do not establish equivalent behavior.

Repeated assertion families include accepted-action success (35 `battle.player_action() is True`), one-turn completion (31), subprocess success (27), session quit (23), unchanged snapshot on rejection (20), no RNG before rejection (15), load success (13), and clean synchronization (13). These are candidate transaction/presentation contracts, not permission to delete assertions: different invalid targets, stores, lifecycle phases and runtimes expose different failure boundaries.

Largest remaining GameState coupling: overworld session 25 constructor calls, terminal overworld 10, game state 8, overworld presenter 7, and route/session integration 5 each. Remaining PartyState constructors are in its own domain contract (9) and explicit Floor I party setup (2). Snapshot-heavy owners remain overworld session (24), overworld state (19), session ownership/player snapshot/save state (17 each). Schema-heavy owners remain save state (21 references), save coordinator (6), service profiles/game snapshot/legacy migration (5 each). These are not all interchangeable setup.

### Remaining Work And Ratio Gap

At the unchanged application denominator, 1.20 permits at most **27,669 test lines**. A further **13,600** lines would have to be removed from this checkpoint. This pass does not establish equivalent protection for removing that amount and does not claim a justified final exception yet.

Continue with these bounded ownership reviews before considering T0 complete:

1. Decompose and consolidate oversized combat/Battle contracts by rule ownership, retaining the distinct blocking-terminal and step-driven lifecycle boundaries. Current largest files are resolver 1,954, Battle/player state 1,357, overworld session 1,292 and terminal battle 1,128 lines.
2. Review repeated burn/poison/Frost and presentation setup for genuine table-driven equivalence. Do not merge different tick durations, actor/opponent cleanup or status-layer versus Battle-lifecycle boundaries merely because bodies look alike.
3. Audit remaining historical M10/M11 flow groups against canonical route/session/targeting owners. Reused semantic setup is safe; deletion of whole journeys still needs named failure-mode equivalence.
4. Review persistence/coordinator/conflict and client-contract matrices individually. Preserve restart fault windows, source-preserving legacy migration, idempotent ancestry, exact-Drifter state and fail-closed payload validation.
5. Keep real browser/PostgreSQL/pinned-runtime qualification intact. Service tests and browser tests were not edited in this pass; their independently exercised boundaries are not redundant with unit tests.
6. Re-measure and qualify the eventual final tree. If the cleanest defensible end remains above 1.20, provide the final category-by-category exception evidence then, rather than extrapolating from this initial pass.

No production defect was fixed. One test-fixture gap was corrected (a nominal hybrid test actually used magical damage); one invalid consolidation attempt exposed unsupported character-specific setup and was withdrawn. The browser readiness timeout remains an intermittent qualification observation, not a production change.

## Progress

- [x] T0-A: structural inventory, green baseline runs, ownership and consolidation candidates captured before test edits.
- [x] T0-B initial pass: justified shared scenario builders and identical strict RNG helper; focused cases and full-suite verification.
- [ ] T0-C: initial unit/contract matrices and historical merges qualified; broader ownership/consolidation remains.
- [ ] T0-D: repeated Hub/Rest/Surface setup reduced; broader flow consolidation remains.
- [ ] T0-E: qualification boundaries reviewed and rerun unchanged; no redundant journey removal established.
- [ ] T0-F: checkpoint metrics/equivalence/local qualification recorded; final T0 closure, target/exception justification and exact committed/hosted revision remain open.

No application changes, new branch, M1 implementation, commits or pushes are part of this record.

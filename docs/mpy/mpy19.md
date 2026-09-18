# MYP19 - Qualify Constrained Heap Pressure

**Goal:** Characterize Dungeon Drifters' MicroPython memory behavior after full-route qualification by separating probe-retained evidence from live runtime state, verifying that route memory is reclaimable, and repeatedly running the unchanged full-route qualification under progressively smaller GC heaps.

**Baseline:**

```text
branch: myp
SHA: 6eaafc416240b5344570e7dd7e349767f84538a5

MicroPython: v1.29.0
source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
platform: win32
```

Sealed MYP18:

```text
Full suite:       1,443 passed
Cumulative suite:   553 passed

12 route nodes
8 encounters
3 Rests
8 Battles
14 fresh enemies
Goblin Lord
Dungeon Entrance

Level: 9
EXP:   68
GP:    24
Gold:  75

RAW_PROBE_STAGES_COMPLETE
```

MYP18 pinned MicroPython route memory:

```text
lowest FREE:  620416
highest ALLOC:404096

final:
FREE:  620512
ALLOC: 404000

dataclasses:
74 / 73 / 35
```

The default Windows qualification heap observed by MYP18 is approximately:

```text
FREE + ALLOC ≈ 1,024,512 bytes
```

MYP19 must not interpret that ~1 MB heap as a PS5 memory budget. It is deliberately a constrained MicroPython qualification environment.

---

## Controlling Principle

MYP19 answers three separate questions:

```text
1. How much of MYP18's final allocation is retained only because
   the probe deliberately keeps old Battles/enemies for evidence?

2. Once that evidence is released, how much memory remains tied
   to the completed live game/session?

3. How small can the pinned MicroPython GC heap become while the
   exact qualified route still completes correctly?
```

Do not collapse these into one number.

Specifically, distinguish:

```text
QUALIFICATION PEAK
→ complete route while retaining evidence

LIVE ROUTE STATE
→ completed game/session after historical Battle/enemy evidence is released

WARM RUNTIME RESIDUAL
→ route game/session also released and GC collected

CONSTRAINED HEAP FLOOR
→ smallest repeatedly successful explicit -X heapsize qualification
```

None of those numbers is automatically the future PS5 heap allocation.

---

# Upstream Heap-Control Qualification

Before changing DD tooling, independently qualify the pinned executable's command-line heap control.

Run:

```powershell
& $MicroPython -h
```

and confirm the pinned executable exposes:

```text
heapsize=<n>[w][K|M]
```

Then run a tiny independent preflight:

```powershell
& $MicroPython -X heapsize=512K -c "import gc; gc.collect(); print(gc.mem_free(), gc.mem_alloc())"
```

Require both values to be available and their sum to be consistent with a constrained heap substantially below the default ~1 MB environment.

Do not require byte-for-byte equality with `524288`, because GC metadata/alignment reduces the Python-visible total slightly.

If `-X heapsize=` is unavailable on the actual pinned executable, stop and revise MYP19.

Do not rebuild MicroPython to gain heap control.

---

# MYP18 Probe Preservation

The complete MYP18 functional qualification must remain intact through:

```text
SOURCE_PATH
CATALOG_IMPORT
DRIFTER_SPEC
NEW_GAME
FIRST_ENCOUNTER
ENEMY_STATE
BATTLE_CONSTRUCTION
BATTLE_VIEW
BATTLE_INPUT
BATTLE_COMPLETE
SESSION_IMPORT
SESSION_CONSTRUCTION
SESSION_VIEW
SESSION_ENCOUNTER_ENTRY
SESSION_ENCOUNTER_COMPLETE
ROUTE_CONSTRUCTION
ROUTE_INITIAL_VIEW
SURFACE_ROUTE_COMPLETE
ROUTE_FINAL_STATE
```

All twelve route nodes must still pass before any MYP19 cleanup occurs.

MYP19 must **not reduce the memory pressure required to reach `ROUTE_FINAL_STATE`**.

That matters because the constrained-heap sweep should remain conservative: a successful heap size must still support the full MYP18 evidence-retaining qualification.

Only after `ROUTE_FINAL_STATE` is sealed may MYP19 release diagnostic references.

---

# Route Evidence Release

Modify:

```text
root/tools/micropython_probe.py
```

Add:

```text
ROUTE_EVIDENCE_RELEASE
```

immediately after:

```text
ROUTE_FINAL_STATE
```

Its job is to release only evidence that was deliberately retained by the qualification harness.

Clear:

```python
STATE["route_battle_factory"].battles[:]
STATE["route_enemy_factory"].enemies[:]
```

and remove:

```text
route_initial_view
```

from `STATE`.

Do not remove:

```text
route_game
route_session
```

yet.

The completed game and session remain alive so this stage measures the actual completed route state without eight historical Battle graphs and fourteen historical enemy references being artificially pinned by the probe.

Before releasing the evidence, `ROUTE_FINAL_STATE` has already proved:

```text
8 Battles
14 distinct EnemyState objects
all compositions
all Battles COMPLETE
all rewards
all Rest state
Dungeon Entrance
persistence unmaterialized
```

so clearing the evidence afterward does not weaken MYP18 qualification.

---

# Live-State Validation After Evidence Release

`ROUTE_EVIDENCE_RELEASE` must confirm that cleanup did not mutate gameplay state.

After clearing historical evidence, require:

```text
session.active_battle is None

current_route_node_id
== surface_dungeon_entrance

route_complete
== True

dungeon_entrance_reached
== True

defeated_encounters
== all 8 expected encounters

resolved_rest_node_ids
== all 3 expected Rests

Level == 9
EXP   == 68
GP    == 24
Gold  == 75

final view screen == MAIN
contextual_route_option is None

session._save_repository is None
```

Do not call `_assert_route_final_state()` after clearing the evidence because that function deliberately expects the retained Battle/enemy collections.

Use a smaller live-state assertion focused on authoritative runtime state.

The existing `_run_stage()` memory instrumentation will collect before and after the cleanup.

Record:

```text
ROUTE_FINAL_STATE|AFTER

versus

ROUTE_EVIDENCE_RELEASE|AFTER
```

Compute in documentation:

```text
evidence_reclaimed_bytes =
    final_state_alloc
    - evidence_release_alloc
```

Do not hardcode an expected byte count.

Require only that evidence release does not increase live allocation materially due to a logic mistake. The actual reclaimed amount is observational evidence.

---

# Route Session Teardown

Add another stage:

```text
ROUTE_SESSION_TEARDOWN
```

after evidence release.

Remove the MYP18 route qualification references from `STATE`:

```text
route_game
route_session
route_battle_factory
route_enemy_factory
```

plus any remaining MYP18-only route view reference.

Do not remove the sealed earlier MYP0-MYP17 state from `STATE`.

That is intentional.

The comparison becomes:

```text
ROUTE_CONSTRUCTION|BEFORE
```

versus:

```text
ROUTE_SESSION_TEARDOWN|AFTER
```

Both measurements therefore share the same earlier qualification state.

The difference represents the warm-runtime residual attributable to having exercised the full route, including any modules, interned strings, or legitimate runtime caches that remain globally reachable.

Record:

```text
warm_residual_bytes =
    teardown_alloc
    - route_construction_before_alloc
```

Do **not** label a nonzero residual a memory leak automatically.

One-time module imports, qstr interning, and runtime caches can legitimately survive route teardown.

MYP19 is collecting evidence, not declaring every persistent byte erroneous.

---

# Result Marker Semantics

After:

```text
ROUTE_SESSION_TEARDOWN PASS
```

the probe may emit:

```text
MYP|RESULT|RAW_PROBE_STAGES_COMPLETE
```

The MYP19 meaning of that marker becomes:

```text
sealed MYP17 runtime stages
+
full MYP18 surface route
+
MYP19 evidence release
+
MYP19 route-session teardown
```

Update the permanent probe contract accordingly.

---

# Permanent Probe Contract

Modify:

```text
root/tests/test_micropython_route_probe_contract.py
```

Preserve the existing MYP18 route requirements.

Extend the expected post-route sequence to:

```text
ROUTE_CONSTRUCTION
ROUTE_INITIAL_VIEW
SURFACE_ROUTE_COMPLETE
ROUTE_FINAL_STATE
ROUTE_EVIDENCE_RELEASE
ROUTE_SESSION_TEARDOWN
```

Add AST/source assertions that the evidence cleanup occurs **after** `ROUTE_FINAL_STATE`, never before it.

Require that the probe still contains the MYP18 constants:

```text
12 route nodes
8 encounters
3 Rests
14 enemies
surface_dungeon_entrance
(9, 68, 24, 75)
```

Continue prohibiting:

```text
pytest
tempfile
pathlib
shutil
SaveRepository
filesystem scanning
save-file creation
```

No production module may be modified to support cleanup.

---

# Host Heap-Sweep Tool

Create:

```text
root/tools/micropython_heap_sweep.py
```

This tool runs under **CPython**, not MicroPython.

It orchestrates the already-qualified bootstrap/probe executable with explicit heap sizes.

It must not import DD production modules.

## CLI

Require explicit paths rather than committing workstation-specific paths:

```text
--micropython <pinned micropython executable>
--bootstrap <micropython_probe_bootstrap.py>
--source <root/src>
```

Defaults may be provided for repository-relative bootstrap/source paths, but the MicroPython executable path must not be hardcoded into the repo.

Example execution:

```powershell
.\.venv\Scripts\python.exe root\tools\micropython_heap_sweep.py `
  --micropython "$env:LOCALAPPDATA\DungeonDrifters\micropython\v1.29.0\source\ports\windows\build-standard\micropython.exe" `
  --bootstrap root\tools\micropython_probe_bootstrap.py `
  --source root\src
```

Use the actual existing pinned executable path if its build directory differs.

---

# Heap-Sweep Command

For an explicit heap size, execute:

```text
<micropython>
-X
heapsize=<N>K
<bootstrap>
<source>
```

For example:

```text
micropython.exe
-X
heapsize=512K
root/tools/micropython_probe_bootstrap.py
root/src
```

Use `subprocess.run()` with captured text stdout/stderr.

Do not invoke through a shell.

Preserve the exact command and return code in the result structure.

---

# Default Baseline Run

Before explicit heap pressure, run the pinned executable once with **no `-X heapsize` override**.

Require:

```text
return code == 0

all 12:
MYP|ROUTE|<node>|PASS

MYP|ROUTE_FINAL_STATE|PASS
MYP|ROUTE_EVIDENCE_RELEASE|PASS
MYP|ROUTE_SESSION_TEARDOWN|PASS

MYP|RESULT|RAW_PROBE_STAGES_COMPLETE
```

This proves MYP19 instrumentation did not regress the sealed default qualification.

Extract:

```text
lowest FREE
highest ALLOC
route final FREE/ALLOC
evidence-release FREE/ALLOC
teardown FREE/ALLOC
```

from that baseline run.

---

# Explicit 1024K Control Run

Next run:

```text
-X heapsize=1024K
```

It must also complete the full probe.

This proves the heap override mechanism itself does not alter behavior at approximately the baseline budget.

Record the actual observed:

```text
BOOT total heap
route lowest FREE
route highest ALLOC
final state
evidence release
teardown
```

Do not require the observed total to equal exactly 1,048,576 bytes.

---

# Constrained Heap Sweep

Use this coarse requested-heap matrix:

```text
1024K
896K
768K
640K
512K
384K
256K
```

Do not assume all sizes will pass.

For each size classify exactly one of:

```text
PASS
MEMORY_LIMIT
UNEXPECTED_FAILURE
```

## PASS

A run is `PASS` only when:

```text
return code == 0

all 12 route-node PASS markers exist

ROUTE_FINAL_STATE PASS

ROUTE_EVIDENCE_RELEASE PASS

ROUTE_SESSION_TEARDOWN PASS

RAW_PROBE_STAGES_COMPLETE exists
```

## MEMORY_LIMIT

A run is `MEMORY_LIMIT` only if the process fails and its captured output establishes:

```text
MemoryError
```

Preserve:

```text
requested heap
actual observed heap if available
last passing stage
last passing route node
failing stage/node
exception line
stdout
stderr
```

A `MemoryError` at a deliberately reduced heap is pressure evidence, not automatically a DD defect.

## UNEXPECTED_FAILURE

Anything else is:

```text
UNEXPECTED_FAILURE
```

Examples:

```text
AssertionError
TypeError
ImportError
ValueError
route-state mismatch
missing route marker
process crash without MemoryError evidence
```

An unexpected failure stops MYP19.

Do not reinterpret semantic corruption as a memory-limit success.

---

# Boundary Refinement

When the coarse sweep finds:

```text
a passing heap
followed by a lower MEMORY_LIMIT heap
```

refine only that bracket in **32 KiB increments**.

Example:

```text
640K PASS
512K MEMORY_LIMIT
```

then test:

```text
608K
576K
544K
```

in descending order.

Do not binary-search byte-by-byte.

The purpose is to characterize an operating region, not manufacture a fake precision claim.

If all coarse sizes through:

```text
256K
```

pass, stop there.

Report:

```text
no failure found at or above 256K
```

Do not chase a smaller number just for bragging rights. 😂

---

# Stability Confirmation

After refinement identify:

```text
smallest observed passing heap
```

Run that exact requested heap **three additional times**.

Require all three to complete the full route for it to be labeled:

```text
STABLE_PASS
```

If there is a nearest lower observed `MEMORY_LIMIT` candidate, run that candidate three additional times too.

Classify its repeated results.

Possible outcome:

```text
576K: 3/3 PASS
544K: 0/3 MEMORY_LIMIT
```

This creates a clean observed pressure boundary.

If a candidate produces mixed outcomes:

```text
2 PASS
1 MEMORY_LIMIT
```

label it:

```text
TRANSITION
```

Do not call it a stable floor.

The smallest `3/3` candidate above that transition is the stable passing floor.

Near-OOM stochastic variation is pressure evidence, not permission to alter gameplay.

---

# No Arbitrary Product Threshold

MYP19 must **not** say:

```text
DD must run in 512K
```

or:

```text
PS5 should allocate only 512K
```

unless that becomes a separate future product requirement.

The sweep is diagnostic.

MYP19 succeeds by accurately characterizing:

```text
default behavior
reclaimability
stable reduced-heap behavior
transition or MemoryError boundary
```

not by forcing the runtime beneath an invented number.

If the smallest stable pass happens to be 640K, 512K, 384K, or another value, record what the runtime demonstrates.

Do not modify production code to win the benchmark.

---

# Heap-Sweep Parser

The sweep tool should parse the existing line protocol rather than scrape arbitrary prose.

Recognize:

```text
MYP|MEMORY|<label>|FREE|<n>|ALLOC|<n>
MYP|<stage>|PASS
MYP|<stage>|FAIL|<type>|<message>
MYP|ROUTE|<node>|PASS
MYP|ROUTE|<node>|FAIL|<type>|<message>
MYP|RESULT|RAW_PROBE_STAGES_COMPLETE
```

Return a structured result containing at minimum:

```python
requested_heap_kib
returncode
classification
complete
last_stage
last_route_node
failure_type
failure_message
lowest_free
highest_alloc
final_free
final_alloc
evidence_release_free
evidence_release_alloc
teardown_free
teardown_alloc
stdout
stderr
```

Keep this tool host-side and dependency-free beyond the Python standard library.

---

# Heap-Sweep Unit Tests

Create:

```text
root/tests/test_micropython_heap_sweep.py
```

Do **not** spawn the real pinned interpreter from pytest.

Unit-test the deterministic host logic.

Cover at least:

### Command construction

Require:

```python
[
    executable,
    "-X",
    "heapsize=512K",
    bootstrap,
    source,
]
```

and verify paths containing spaces remain individual arguments.

### Successful parsing

Fixture output must include:

```text
12 route PASS markers
ROUTE_FINAL_STATE PASS
ROUTE_EVIDENCE_RELEASE PASS
ROUTE_SESSION_TEARDOWN PASS
RAW_PROBE_STAGES_COMPLETE
```

Require classification:

```text
PASS
```

and exact memory extraction.

### Memory limit

Fixture:

```text
MYP|ROUTE|surface_elite_patrol|FAIL|MemoryError|...
```

Require:

```text
MEMORY_LIMIT
```

with:

```text
last passing route node
failing route node
```

preserved.

### Stage-level MemoryError

Also classify a MemoryError occurring before route traversal.

### Unexpected semantic failure

Fixture:

```text
AssertionError
```

must become:

```text
UNEXPECTED_FAILURE
```

not `MEMORY_LIMIT`.

### Missing completion marker

A zero return code without:

```text
RAW_PROBE_STAGES_COMPLETE
```

must not be classified as PASS.

### Refinement grid

Require:

```text
640 PASS
512 FAIL
```

to produce:

```text
608
576
544
``` 

for 32 KiB refinement.

### Stable confirmation

Test:

```text
3 PASS
→ STABLE_PASS

mixed PASS/MEMORY_LIMIT
→ TRANSITION
```

No live subprocess is needed for these unit tests.

---

# Pressure Result Artifact

The sweep tool should print a compact machine-readable summary such as:

```text
MYP19|HEAP|DEFAULT|PASS|...
MYP19|HEAP|1024K|PASS|...
MYP19|HEAP|896K|PASS|...
MYP19|HEAP|768K|PASS|...
MYP19|HEAP|640K|PASS|...
MYP19|HEAP|512K|MEMORY_LIMIT|...
...
MYP19|STABLE_PASS|640K|3/3
MYP19|BOUNDARY|LOWER|608K|MEMORY_LIMIT|3/3
```

Use whatever exact field order is cleanest, but cover it with parser/formatting tests and document it.

Human-readable explanation may accompany it, but do not make documentation depend on manually reading subprocess dumps.

---

# Interpretation Rules

MYP19 documentation must distinguish the following.

### Qualification peak

The highest `ALLOC` observed while the route still retains:

```text
8 Battles
14 EnemyStates
their presentation/session evidence
```

This is intentionally conservative.

### Evidence-free live state

Allocation after:

```text
ROUTE_EVIDENCE_RELEASE
```

while the completed:

```text
GameState
OverworldSession
PlayerState
WorldState
OverworldState
``` 

remain alive.

### Warm residual

Allocation after:

```text
ROUTE_SESSION_TEARDOWN
```

relative to:

```text
ROUTE_CONSTRUCTION|BEFORE
```

This may include one-time module and qstr residency.

Do not call it a leak without repeated-growth evidence.

### Stable constrained floor

The smallest tested heap that completes:

```text
3 / 3
```

full qualifications.

This is an observed qualification floor for this Windows MicroPython harness, not a console requirement.

---

# Important PS5 Scope Statement

Document explicitly:

```text
The MYP19 heap sweep is a runtime-health stress test.

It is not a PS5 RAM budget.
It does not model PS5 unified-memory allocation.
It does not include native host, graphics, audio, assets, SDK, or GPU memory.
It does not imply the embedded MicroPython VM should receive the minimum
passing heap observed here.
```

The future native console host is free to assign the embedded VM a much larger and more comfortable heap.

MYP19 exists to expose pathological retention, fragmentation sensitivity, or unexpectedly large Python-object pressure before that host exists.

---

# Runtime Qualification Order

Run in this exact order:

```text
1. Full CPython suite

2. MYP19 focused unit/contract suite

3. Exact cumulative portability suite

4. compileall

5. dataclass manifest --check

6. git diff --check

7. native CPython raw probe

8. forced-overlay CPython raw probe

9. pinned MicroPython default full-route probe

10. pinned explicit 1024K probe

11. constrained heap coarse sweep

12. 32K transition refinement if needed

13. 3-run stability confirmations
```

Do not run pressure experiments before normal regression qualification is green.

---

# Native And Forced-Overlay Probes

Both must still reach:

```text
ROUTE_FINAL_STATE PASS
ROUTE_EVIDENCE_RELEASE PASS
ROUTE_SESSION_TEARDOWN PASS
RAW_PROBE_STAGES_COMPLETE
```

Their memory values are informational only because `gc.mem_free()` may be unavailable under CPython.

Do not require CPython to emulate MicroPython heap telemetry.

---

# Pinned Default Qualification

Before the constrained sweep, the default pinned MicroPython run must still reproduce the MYP18 functional result:

```text
12 route nodes
8 encounters
3 Rests
8 Battles
14 fresh enemies
Goblin Lord
Dungeon Entrance

Level 9
EXP 68
GP 24
Gold 75

persistence not materialized
```

The new cleanup stages must then pass.

If default MYP19 qualification fails, do not continue into smaller heaps.

---

# Verification

Run the full suite from `root`.

Run the MYP19 focused tests:

```powershell
Push-Location root

& ..\.venv\Scripts\python.exe -m pytest `
  tests\test_micropython_route_probe_contract.py `
  tests\test_micropython_heap_sweep.py

Pop-Location
```

Report the actual focused count.

Then run the exact sealed MYP18 cumulative suite that produced `553 passed`, plus the new heap-sweep contract:

```powershell
Push-Location root

& ..\.venv\Scripts\python.exe -m pytest `
  tests\test_dataclass_contract.py `
  tests\test_portable_dataclasses.py `
  tests\test_enum_contract.py `
  tests\test_portable_enum.py `
  tests\test_keyword_contract.py `
  tests\test_portable_keyword.py `
  tests\test_regex_contract.py `
  tests\test_portable_regex.py `
  tests\test_collections_contract.py `
  tests\test_portable_collections_abc.py `
  tests\test_string_contract.py `
  tests\test_portable_string_validation.py `
  tests\test_portable_counter_removal.py `
  tests\test_typing_contract.py `
  tests\test_portable_typing.py `
  tests\test_battle_presentation_session.py `
  tests\test_starred_tuple_contract.py `
  tests\test_character_profiles.py `
  tests\test_terminal_battle_ui.py `
  tests\test_strict_zip_contract.py `
  tests\test_save_contract.py `
  tests\test_session_persistence_boundary.py `
  tests\test_save_repository.py `
  tests\test_overworld_session.py `
  tests\test_runtime_overworld.py `
  tests\test_m10b_map_inspection.py `
  tests\test_itertools_contract.py `
  tests\test_next_default_contract.py `
  tests\test_overworld_presenter.py `
  tests\test_battle_presenter.py `
  tests\test_item_first_inventory.py `
  tests\test_inventory_action_resolver.py `
  tests\test_random_contract.py `
  tests\test_combat_resolver.py `
  tests\test_runtime_battle.py `
  tests\test_battle_player_state.py `
  tests\test_heal_action.py `
  tests\test_battle_ui_hardening.py `
  tests\test_micropython_route_probe_contract.py `
  tests\test_runtime_qualification.py `
  tests\test_m11_surface_routes.py `
  tests\test_m10c_route_integration.py `
  tests\test_overworld_state.py `
  tests\test_micropython_heap_sweep.py

Pop-Location
```

Report the actual new total.

Then:

```powershell
.\.venv\Scripts\python.exe -m compileall `
  root\src `
  root\tests `
  root\tools `
  root\portability

.\.venv\Scripts\python.exe `
  root\tools\generate_dataclass_manifest.py --check

git diff --check
```

Require the manifest to remain:

```text
74 entries
```

---

# Expected Diff

Expected probe change:

```text
MODIFY
root/tools/micropython_probe.py
```

Expected host qualification tooling:

```text
CREATE
root/tools/micropython_heap_sweep.py
```

Expected tests:

```text
MODIFY
root/tests/test_micropython_route_probe_contract.py

CREATE
root/tests/test_micropython_heap_sweep.py
```

Expected documentation:

```text
MODIFY
docs/portability/micropython-probe.md
```

Expected production changes:

```text
NONE
```

Final scope:

```text
production source changes:             0
gameplay changes:                      0
combat changes:                        0
route/content changes:                 0
session behavior changes:              0
persistence/schema changes:            0
compatibility overlay changes:         0
bootstrap changes:                     0
MicroPython source/config changes:     0

qualification additions:
  post-route evidence release
  route-session teardown
  explicit heap sweep
  boundary refinement
  stability confirmation

historical docs/mpy changes:           0
```

---

# Documentation

Update:

```text
docs/portability/micropython-probe.md
```

Record sealed MYP18:

```text
6eaafc416240b5344570e7dd7e349767f84538a5
MYP18 - Qualify Full Surface Route
```

Preserve its exact route evidence.

Add MYP19 sections covering:

```text
upstream -X heapsize capability
default heap observation
MYP18 evidence-retention explanation

ROUTE_FINAL_STATE allocation
ROUTE_EVIDENCE_RELEASE allocation
bytes reclaimed by evidence cleanup

ROUTE_SESSION_TEARDOWN allocation
warm runtime residual

default pinned qualification
explicit 1024K qualification

coarse heap matrix
refined 32K transition matrix
stable-pass confirmations

smallest stable passing requested heap
nearest lower MemoryError or transition size
exact failing stage/node at pressure boundary

lowest FREE / highest ALLOC for each successful constrained run
dataclass census
full suite total
focused suite total
cumulative suite total

native CPython result
forced-overlay CPython result
CI result
scope counts
```

Explicitly state:

```text
A low-heap MemoryError is not itself a gameplay defect.

No production optimization was performed to lower the observed floor.

The observed floor includes the conservative MYP18 qualification workload,
including retained Battle/enemy evidence through ROUTE_FINAL_STATE.

The result is not a PS5 RAM requirement.
```

---

# Stop Conditions

Stop and request a revised MYP19 plan if:

```text
the pinned executable does not support -X heapsize

the default MYP19 full route no longer passes

ROUTE_EVIDENCE_RELEASE changes authoritative game/session state

route cleanup requires production changes

heap sweeping requires changing MicroPython source/config

bootstrap modification becomes necessary

a reduced-heap run fails semantically rather than from MemoryError

the route reaches incorrect progression before memory exhaustion

a low-memory run silently skips route nodes or evidence

the host sweep cannot distinguish MemoryError from semantic failure
```

A `MemoryError` caused solely by deliberately shrinking the heap is **expected pressure evidence** and does not require a compatibility repair.

Do not create MYP19A merely because a 384K or 512K heap is too small.

---

# Success Conditions

MYP19 succeeds when:

```text
default pinned full route still passes

post-route evidence is demonstrably releasable

route session can be torn down and GC measured

at least one explicit heap below the default completes the full route

the constrained sweep identifies a stable operating region

the smallest reported stable pass completes 3/3 runs

any lower pressure failure is either cleanly characterized as MemoryError
or reported as a transition region

no semantic corruption appears

no production source changes are required
```

If every tested heap through:

```text
256K
```

passes:

```text
report that result
do not search lower
```

If a clean MemoryError boundary appears above `256K`:

```text
report and refine it
do not optimize gameplay merely to move the number
```

---

# Future Gate

If MYP19 seals cleanly:

```text
MYP20 - Cross-Runtime Regression Qualification And Campaign Closure
```

MYP20 should use the sealed MYP19 default and constrained-memory evidence as inputs, but it should not repeat the heap-floor hunt.

Its job is closure: prove the portable runtime contract remains aligned across the supported execution environments and freeze the MicroPython campaign evidence.

---

# Release

Commit exactly:

```text
MYP19 - Qualify Constrained Heap Pressure
```

Push:

```text
myp
```

Then verify:

```text
local HEAD == origin/myp
tracked worktree clean
exact-SHA CI successful
18 historical docs/mpy files untouched and uncommitted
```

The final MYP19 report must include:

```text
commit SHA/message

full-suite total
focused MYP19 test total
cumulative-suite total

default pinned result
explicit 1024K result

MYP18 final-state FREE/ALLOC
evidence-release FREE/ALLOC
evidence bytes reclaimed
session-teardown FREE/ALLOC
warm residual

coarse heap matrix
refined matrix
stable confirmation runs
smallest stable passing heap
nearest lower MemoryError/transition heap

last passing stage/node at the pressure boundary
failure type/message

lowest FREE
highest ALLOC
final dataclass census

native CPython result
forced-overlay CPython result

CI run/conclusion
local/origin synchronization
tracked worktree state
historical docs/mpy preservation
``

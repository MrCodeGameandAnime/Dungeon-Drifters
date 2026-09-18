# MYP20 - Seal Cross-Runtime Qualification

**Goal:** Close the Dungeon Drifters MicroPython portability campaign by proving that the same sealed headless gameplay qualification contract produces the same semantic result under native CPython, forced portability overlays on CPython, and pinned MicroPython `v1.29.0`, while preserving the sealed MYP19 `448K / 416K` pressure boundary.

**Baseline:**

```text
branch: myp
SHA: 896b1b39f24c0a35768f69d2394b124160c55c15

MYP19 - Qualify Constrained Heap Pressure

MicroPython: v1.29.0
source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
platform: win32
```

Sealed MYP19:

```text
Full suite:       1453 passed
Focused MYP19:      13 passed
Cumulative:        563 passed

Stable heap:
448K -> PASS 3/3

Lower boundary:
416K -> MemoryError 3/3

Production source changes: 0
```

MYP20 is a **closure/qualification gate**.

Expected production changes:

```text
NONE
```

---

# Controlling Closure Contract

The authoritative qualification path is now:

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
ROUTE_EVIDENCE_RELEASE
ROUTE_SESSION_TEARDOWN
RAW_PROBE_STAGES_COMPLETE
```

The route oracle remains exactly:

```text
surface_goblin_solo
surface_goblin_pair
surface_warrior_solo
surface_rest_after_warrior_solo
surface_warrior_pair
surface_shaman_solo
surface_shaman_pair
surface_rest_after_shaman_pair
surface_elite_patrol
surface_rest_before_goblin_lord
surface_goblin_lord
surface_dungeon_entrance
```

Its embedded assertions continue to prove:

```text
8 encounters
3 Rests
8 Battles
14 fresh enemies
Goblin Lord defeated
Dungeon Entrance reached

Level 9
EXP 68
Growth Points 24
Gold 75

route_complete = True
dungeon_entrance_reached = True
active_battle = None
persistence not materialized
```

MYP20 must not weaken or rewrite this contract.

---

# Cross-Runtime Matrix

Create:

```text
root/tools/runtime_qualification_matrix.py
```

This is a **host-side CPython orchestration tool**.

It must not import DD production modules.

It runs the exact same qualification artifact in these execution modes:

```text
CPYTHON_NATIVE
CPYTHON_FORCED_OVERLAY
MICROPYTHON_DEFAULT
MICROPYTHON_448K
```

The first three form the cross-runtime semantic parity matrix.

The constrained MicroPython run requalifies the sealed MYP19 stable floor.

A fixed `416K` pressure confirmation is handled separately because its expected result is `MemoryError`, not semantic parity.

---

# Runtime Commands

## Native CPython

Run the raw probe directly:

```text
<python>
root/tools/micropython_probe.py
root/src
```

No portability bootstrap.

This establishes the normal CPython implementation.

## Forced-overlay CPython

Run:

```text
<python>
root/tools/micropython_probe_bootstrap.py
root/src
```

This deliberately exercises the portability overlays while still using CPython as the interpreter.

## Pinned MicroPython default

Run:

```text
<micropython>
root/tools/micropython_probe_bootstrap.py
root/src
```

No explicit heap override.

## Pinned MicroPython 448K

Run:

```text
<micropython>
-X
heapsize=448K
root/tools/micropython_probe_bootstrap.py
root/src
```

Use:

```text
root/tools/micropython_heap_sweep.py
```

as the existing command/parsing authority where practical.

Do not duplicate its `PASS`, `MEMORY_LIMIT`, or output parsing semantics unnecessarily.

---

# CLI

The matrix tool should accept:

```text
--python
--micropython
--probe
--bootstrap
--source
```

Example:

```powershell
.\.venv\Scripts\python.exe root\tools\runtime_qualification_matrix.py `
  --python .\.venv\Scripts\python.exe `
  --micropython "$env:LOCALAPPDATA\DungeonDrifters\micropython\v1.29.0\source\ports\windows\build-standard\micropython.exe" `
  --probe root\tools\micropython_probe.py `
  --bootstrap root\tools\micropython_probe_bootstrap.py `
  --source root\src
```

Use the actual pinned executable path if the local build path differs.

Do not hardcode a developer workstation path into the repository.

All subprocess calls:

```text
shell = False
```

Paths containing spaces must remain individual argument elements.

---

# Semantic Signature

MYP20 must compare **semantic evidence**, not raw stdout.

Do not compare:

```text
memory addresses
heap values
runtime version strings
runtime platform strings
dataclass census presence/absence
traceback formatting
```

Those legitimately differ by execution mode.

Extract a deterministic semantic signature containing:

```python
(
    stage_pass_sequence,
    route_pass_sequence,
    completion_marker,
)
```

The expected stage sequence is the complete sealed MYP19 sequence through:

```text
ROUTE_SESSION_TEARDOWN
```

The expected route sequence is the exact twelve-node oracle.

The completion marker is exactly:

```text
MYP|RESULT|RAW_PROBE_STAGES_COMPLETE
```

Require it exactly once.

A runtime passes the semantic contract only when:

```text
all expected stages PASS in order
all 12 route nodes PASS in order
no FAIL markers exist
completion marker exists exactly once
process exit code == 0
```

Do not merely say:

```text
all three outputs happen to match each other
```

Three identically wrong runs are still wrong.

Each runtime must independently match the **sealed expected contract**, and then the three signatures must also be identical.

---

# Native Runtime Identity

Parse and record:

```text
MYP|IMPLEMENTATION|...
MYP|VERSION|...
MYP|PLATFORM|...
```

Require:

```text
CPYTHON_NATIVE
implementation == cpython

CPYTHON_FORCED_OVERLAY
implementation == cpython

MICROPYTHON_DEFAULT
implementation == micropython
version == 1.29.0
platform == win32

MICROPYTHON_448K
implementation == micropython
version == 1.29.0
platform == win32
```

Do not hardcode the CPython version unless the repository already declares one as a project requirement.

Record the actual CPython version used for closure.

---

# Cross-Runtime Parity Requirement

After all three primary modes pass individually:

```text
CPYTHON_NATIVE
CPYTHON_FORCED_OVERLAY
MICROPYTHON_DEFAULT
```

require:

```text
native_signature
==
forced_signature
==
micropython_signature
==
expected_signature
```

Emit:

```text
MYP20|SEMANTIC_PARITY|PASS
```

If any signature differs:

```text
MYP20|SEMANTIC_PARITY|FAIL
```

and report the first differing stage or route node.

Do not reduce the comparison to only the last successful stage.

---

# Forced-Overlay Purpose

Document why the middle runtime exists.

The matrix means:

```text
Native CPython
→ proves ordinary DD Python behavior remains valid

Forced-overlay CPython
→ proves the portability compatibility surfaces preserve DD semantics
  even when exercised on CPython

Pinned MicroPython
→ proves the constrained interpreter executes the same qualified contract
```

This is the final evidence for the architecture:

```text
one authoritative gameplay implementation
+
narrow compatibility boundaries
+
multiple Python runtimes
```

not:

```text
three gameplay implementations
```

---

# Final MYP19 Heap Regression

MYP20 must **not perform another heap search**.

The heap floor is already sealed.

Instead, requalify only the two fixed MYP19 boundary points on the final campaign SHA.

## 448K stable boundary

Run:

```text
448K
```

three times.

Require:

```text
PASS
PASS
PASS
```

with every run reaching:

```text
ROUTE_FINAL_STATE
ROUTE_EVIDENCE_RELEASE
ROUTE_SESSION_TEARDOWN
RAW_PROBE_STAGES_COMPLETE
```

Emit:

```text
MYP20|HEAP|448K|STABLE_PASS|3/3
```

## 416K lower boundary

Run:

```text
416K
```

three times.

Require:

```text
MEMORY_LIMIT
MEMORY_LIMIT
MEMORY_LIMIT
```

Do **not** require every MemoryError to occur on exactly the same allocation instruction if low-memory GC behavior shifts slightly.

However, every run must be:

```text
MEMORY_LIMIT
```

and not:

```text
UNEXPECTED_FAILURE
```

Emit:

```text
MYP20|HEAP|416K|MEMORY_LIMIT|3/3
```

Record each actual failure frontier.

If `416K` unexpectedly completes successfully even once, stop.

That would invalidate the sealed deterministic boundary assumption and needs investigation rather than silently rewriting history.

Likewise, if `448K` fails even once, stop.

---

# Do Not Re-Hunt The Floor

MYP20 must not test:

```text
432K
440K
424K
...
```

There is no value in squeezing another number out of the final gate.

The sealed claim remains:

```text
448K = smallest observed stable passing heap from MYP19
416K = clean observed lower MemoryError boundary from MYP19
```

MYP20 only confirms those exact observations still hold on the closure commit.

---

# Closure Tool Output

The host matrix should emit compact machine-readable evidence.

Example shape:

```text
MYP20|RUNTIME|CPYTHON_NATIVE|PASS|IMPLEMENTATION|cpython|VERSION|...
MYP20|RUNTIME|CPYTHON_FORCED_OVERLAY|PASS|IMPLEMENTATION|cpython|VERSION|...
MYP20|RUNTIME|MICROPYTHON_DEFAULT|PASS|IMPLEMENTATION|micropython|VERSION|1.29.0
MYP20|SEMANTIC_PARITY|PASS

MYP20|HEAP|448K|STABLE_PASS|3/3
MYP20|HEAP|416K|MEMORY_LIMIT|3/3

MYP20|RESULT|CLOSURE_COMPLETE
```

Do not emit:

```text
CLOSURE_COMPLETE
```

unless **everything** passes.

---

# Failure Classes

The matrix tool should distinguish:

```text
RUNTIME_FAILURE
SEMANTIC_MISMATCH
PRESSURE_REGRESSION
TOOLING_FAILURE
```

Examples:

```text
CPython probe AssertionError
→ RUNTIME_FAILURE

all runtimes complete but route signatures differ
→ SEMANTIC_MISMATCH

448K fails
or
416K unexpectedly passes
→ PRESSURE_REGRESSION

subprocess cannot launch executable
or parser cannot understand output
→ TOOLING_FAILURE
```

All four block closure.

---

# Tests

Create:

```text
root/tests/test_runtime_qualification_matrix.py
```

Do not execute real MicroPython from pytest.

Use synthetic subprocess/probe output.

Cover at minimum:

1. **Command construction**

Native CPython:

```python
[
    python,
    probe,
    source,
]
```

Forced CPython:

```python
[
    python,
    bootstrap,
    source,
]
```

MicroPython default:

```python
[
    micropython,
    bootstrap,
    source,
]
```

MicroPython constrained:

```python
[
    micropython,
    "-X",
    "heapsize=448K",
    bootstrap,
    source,
]
```

Paths containing spaces must remain intact.

2. **Semantic signature extraction**

Given complete successful output, extract exactly:

```text
expected stage sequence
expected 12 route nodes
completion marker
```

3. **Memory lines ignored**

Two otherwise identical outputs with different:

```text
FREE
ALLOC
```

must produce identical semantic signatures.

4. **Runtime identity ignored for semantic parity**

CPython and MicroPython identity/version lines may differ while semantic signatures remain equal.

5. **Missing stage**

Removing:

```text
ROUTE_EVIDENCE_RELEASE
```

must fail the contract.

6. **Out-of-order stage**

Swapping two PASS stages must fail.

7. **Missing route node**

Eleven route nodes must fail.

8. **Duplicate result marker**

Two:

```text
RAW_PROBE_STAGES_COMPLETE
```

markers must fail.

9. **FAIL marker despite zero exit code**

Must fail.

10. **Cross-runtime mismatch**

Synthetic signatures differing at one route node must identify the first mismatch.

11. **448K confirmation**

```text
PASS / PASS / PASS
→ STABLE_PASS
```

12. **448K instability**

```text
PASS / MEMORY_LIMIT / PASS
→ PRESSURE_REGRESSION
```

13. **416K confirmation**

```text
MEMORY_LIMIT / MEMORY_LIMIT / MEMORY_LIMIT
→ MEMORY_LIMIT_CONFIRMED
```

14. **416K unexpected success**

Any PASS must produce:

```text
PRESSURE_REGRESSION
```

15. **Closure result**

Only the full valid matrix may produce:

```text
CLOSURE_COMPLETE
```

---

# Keep Existing MYP19 Tooling Sealed

Do not modify:

```text
root/tools/micropython_heap_sweep.py
```

unless a genuinely unavoidable defect is discovered.

MYP19 already sealed that tool with 13 focused tests and the real heap sweep.

MYP20 may import its stable host-side helpers, particularly command construction/output classification, rather than forking them.

Likewise do not modify:

```text
root/tools/micropython_probe.py
root/tools/micropython_probe_bootstrap.py
```

unless the matrix reveals a genuine closure-blocking defect.

The desired MYP20 diff contains **no qualification-probe changes**.

That gives us a very clean final statement:

```text
MYP20 did not move the goalposts.
It reran the sealed MYP19 contract.
```

---

# Closure Document

Create:

```text
docs/portability/micropython-closure.md
```

Do not make the final campaign summary depend entirely on the increasingly long historical probe log.

The closure document should be a concise authoritative snapshot.

Include:

```text
qualification date
final branch
final MYP20 SHA after release
pinned MicroPython version/SHA/platform

architecture statement
qualified runtime surfaces
compatibility-boundary inventory
full-route qualification
memory-pressure qualification
cross-runtime matrix
test totals
non-claims
deferred concerns
future requalification triggers
```

---

# Architecture Statement

The closure document should explicitly state:

```text
Dungeon Drifters retains one authoritative Python gameplay implementation.

MicroPython qualification did not introduce:
- a second combat engine
- a second session implementation
- alternate game state
- alternate route/content representation
- platform-specific gameplay forks
- an interpreter fork
```

Compatibility work is implemented through narrow boundaries and portable source adjustments.

---

# Compatibility Inventory

Record the final qualified compatibility mechanisms.

At minimum include:

```text
readonly mapping compatibility
generated dataclass metadata + dataclass overlay
StrEnum compatibility
keyword compatibility
regex fullmatch compatibility
collections.abc compatibility
typing / Protocol compatibility
portable ASCII validation
Counter dependency removal
starred tuple expression portability
strict zip removal
session persistence import boundary
itertools.groupby removal
first_or_none iteration boundary
portable random adapter
```

Distinguish:

```text
portable source corrections
```

from:

```text
MicroPython compatibility overlays
```

Do not imply every mechanism is suitable for extraction as a public library.

---

# Qualified Claims

The closure document may claim that pinned MicroPython `v1.29.0` on `win32` successfully executes the currently qualified DD runtime contract covering:

```text
content catalog loading
DrifterSpec resolution
new-game construction
EnemyState construction
Battle construction
BattleView generation
semantic Battle inputs
Battle completion
OverworldSession import/construction
OverworldView generation
session encounter entry
session encounter completion

the full authored surface route:
8 encounters
3 Rests
Goblin Lord
Dungeon Entrance

progression and rewards:
Level 9
EXP 68
GP 24
Gold 75

state cleanup
evidence reclamation
session teardown
```

It may also state the MYP19 observation:

```text
448K completed the full qualification 3/3
416K reached MemoryError 3/3
```

once MYP20 re-confirms those results on the final campaign SHA.

---

# Explicit Non-Claims

This section is important.

Do **not** claim:

```text
all future DD content is automatically MicroPython compatible

every Drifter-specific combat mechanic has been exhaustively
executed under MicroPython

448K is the recommended production heap

448K is a PS5 RAM requirement

416K is a universal MicroPython failure point

the Windows MicroPython port models PS5 hardware

console graphics/audio/input/platform SDK integration is complete

SAVE-ARCH is solved

desktop filesystem persistence is a console architecture

DD can currently ship on PS5
```

The actual claim is narrower and stronger:

> The current authoritative headless DD gameplay runtime and full authored surface-route contract have been qualified successfully on the pinned MicroPython runtime without introducing a second gameplay implementation.

---

# Deferred Architecture

Carry forward the existing deferred concern:

```text
SAVE-ARCH
```

MYP14 only decoupled the session persistence import boundary.

MYP20 must not accidentally declare persistence architecture finished.

Also distinguish future native-host concerns:

```text
PS5 native host
graphics
audio
input
platform lifecycle
SDK integration
native storage adapter
packaging
certification
```

These are host/platform work, not MicroPython gameplay-portability failures.

---

# Requalification Triggers

After MYP20, the campaign is closed.

Do not create:

```text
MYP21
```

merely because the number comes next. 😂

A new MicroPython qualification campaign is justified only when something material changes, such as:

```text
MicroPython version changes

new Python language/runtime feature enters production gameplay

new standard-library dependency enters the headless runtime

content exercises a previously unqualified gameplay mechanic

core session/combat architecture changes

generated dataclass contract changes

compatibility overlays change

persistence becomes part of the constrained runtime contract

target platform/runtime changes materially
```

Normal DD feature development should continue normally.

MicroPython should become a regression target, not the center of every design decision.

---

# Existing Probe Documentation

Modify:

```text
docs/portability/micropython-probe.md
```

Add MYP20 results and change the final future-gates section from:

```text
MYP20 Cross-runtime regression qualification and campaign closure.
```

to a completed campaign statement.

Example:

```text
MYP20 Cross-runtime regression qualification and campaign closure.

No further nominal MYP gates are scheduled.
Future qualification is evidence-driven and triggered by material
runtime or architecture changes.
```

Do not delete the historical MYP0–19 evidence.

---

# Verification

Run the full suite:

```powershell
Push-Location root

& ..\.venv\Scripts\python.exe -m pytest

Pop-Location
```

Report the actual total.

Do not predict it.

Run the new focused closure tests:

```powershell
Push-Location root

& ..\.venv\Scripts\python.exe -m pytest `
  tests\test_runtime_qualification_matrix.py `
  tests\test_micropython_route_probe_contract.py `
  tests\test_micropython_heap_sweep.py

Pop-Location
```

Report the actual total.

Then run the exact sealed MYP19 cumulative suite plus the new matrix contract:

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
  tests\test_micropython_heap_sweep.py `
  tests\test_runtime_qualification_matrix.py

Pop-Location
```

Report the actual new cumulative count.

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

Require:

```text
manifest: 74 entries
```

---

# Final Runtime Matrix Execution

Run:

```text
runtime_qualification_matrix.py
```

Require:

```text
CPYTHON_NATIVE             PASS
CPYTHON_FORCED_OVERLAY     PASS
MICROPYTHON_DEFAULT        PASS

SEMANTIC_PARITY            PASS
```

Then require fixed pressure confirmation:

```text
448K PASS        3/3
416K MEMORY_LIMIT 3/3
```

Finally:

```text
MYP20|RESULT|CLOSURE_COMPLETE
```

No closure result if any component fails.

---

# Dataclass Evidence

Record the pinned MicroPython final census again.

Expected manifest:

```text
74
```

Do not predict `DECORATED` or `CONSTRUCTED` merely because MYP19 produced:

```text
74 / 73 / 35
```

Require the actual MYP20 result to be recorded.

If it differs, investigate before sealing.

---

# Expected Diff

Expected tooling:

```text
CREATE
root/tools/runtime_qualification_matrix.py
```

Expected tests:

```text
CREATE
root/tests/test_runtime_qualification_matrix.py
```

Expected documentation:

```text
CREATE
docs/portability/micropython-closure.md

MODIFY
docs/portability/micropython-probe.md
```

Expected unchanged files:

```text
root/tools/micropython_probe.py
root/tools/micropython_probe_bootstrap.py
root/tools/micropython_heap_sweep.py
```

Expected production:

```text
root/src/**

NO CHANGES
```

Final scope target:

```text
production source files changed:       0
gameplay code changed:                 0
combat code changed:                   0
session code changed:                  0
route/content changed:                 0
persistence/schema changed:            0
compatibility overlays changed:        0
raw probe changed:                     0
bootstrap changed:                     0
heap-sweep implementation changed:     0
MicroPython source/config changed:     0

new host closure tool:                 1
new closure test file:                 1
new closure document:                  1
existing portability document updated:1

historical docs/mpy changes:           0
```

---

# Stop Conditions

Stop and request a revised MYP20 plan if any of the following occurs:

```text
native CPython no longer completes the sealed probe

forced-overlay CPython no longer completes the sealed probe

pinned MicroPython default no longer completes the sealed probe

semantic signatures differ across the three primary runtimes

448K fails even once during the 3-run confirmation

416K passes even once during the 3-run confirmation

416K fails for a semantic/non-MemoryError reason

MYP20 requires changing production source

MYP20 requires changing compatibility overlays

MYP20 requires changing the raw probe

MYP20 requires changing the bootstrap

MYP20 requires changing MicroPython source/configuration

final dataclass contract differs unexpectedly
```

A closure gate is not the place to quietly repair something.

Any such evidence means the campaign is **not actually ready to close**.

---

# Success Criteria

MYP20 succeeds only when the final exact source tree demonstrates:

```text
native CPython
    PASS

forced-overlay CPython
    PASS

pinned MicroPython v1.29.0 default heap
    PASS

semantic qualification signatures
    identical and equal to sealed contract

pinned MicroPython 448K
    PASS 3/3

pinned MicroPython 416K
    MemoryError 3/3

full CPython suite
    PASS

focused closure suite
    PASS

cumulative portability suite
    PASS

compileall
    PASS

dataclass manifest
    74 entries / current

git diff --check
    PASS

production changes
    0
```

At that point the MicroPython campaign is complete.

---

# Release

Commit exactly:

```text
MYP20 - Seal Cross-Runtime Qualification
```

Push:

```text
myp
```

Then verify:

```text
local HEAD == origin/myp
tracked worktree clean
exact-SHA CI completed successfully
18 historical docs/mpy files untouched and uncommitted
```

The final MYP20 report must include:

```text
commit SHA/message

full-suite total
focused closure-suite total
cumulative-suite total

native CPython version/result
forced-overlay CPython version/result
pinned MicroPython version/SHA/platform/result

exact semantic stage parity
exact 12-node route parity

448K confirmation: 3/3
416K confirmation: 3/3 MemoryError
actual 416K failure frontiers

final MicroPython memory evidence
final dataclass census

production diff count
compatibility-overlay diff count
probe/bootstrap diff count

closure-document path

CI run/conclusion
local/origin synchronization
tracked worktree state
historical docs/mpy preservation
```

And the final documentation should end with something equivalent to:

```text
Dungeon Drifters MicroPython portability campaign MYP0-MYP20: CLOSED.

The current authoritative headless gameplay runtime and authored surface-route
contract are qualified on pinned MicroPython v1.29.0 without a second gameplay
implementation.

Future portability work is evidence-driven rather than gate-number-driven.
```

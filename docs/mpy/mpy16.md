# MPY16 - Repair Portable Next Default Boundary

**Goal:** Advance pinned MicroPython `v1.29.0` beyond the sealed MPY15 `SESSION_VIEW` failure by removing Dungeon Drifters’ runtime dependency on two-argument `next(iterator, None)` while preserving first-match-or-None semantics everywhere it is currently used.

**Baseline:**
```text
branch: mpy
SHA: 133846f6b15b0ea3ed2153af69b104a0945b3fcf

MicroPython: v1.29.0
source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
platform: win32
```

Sealed MPY15 runtime frontier:
```text
SESSION_IMPORT        PASS
SESSION_CONSTRUCTION  PASS
SESSION_VIEW          FAIL

TypeError:
function takes 1 positional argument but 2 were given

FREE: 672400
ALLOC: 352112

DATACLASS EXPECTED:    74
DATACLASS DECORATED:   73
DATACLASS CONSTRUCTED: 28
```

Traceback terminates in:
```text
OverworldSession.current_view()
→ OverworldSession._build_view()
→ OverworldPresenter.build()
→ selected_item = next(..., None)
```

Pinned MicroPython implements two-argument `next()` only when its `MICROPY_PY_BUILTINS_NEXT2` feature is enabled. The observed Windows runtime is exposing the one-argument implementation, which matches the exact arity failure.

MPY16 must not modify or rebuild MicroPython to enable that feature.

## Root-Cause Qualification

Before editing production source, independently reproduce the exact primitive boundary under the pinned interpreter:
```python
iterator = iter(("value",))
print(next(iterator))
```

Require:
```text
value
```

Then independently run:
```python
iterator = iter(("value",))
print(next(iterator, None))
```

Record the exact result. The expected MPY15-correlated result is:
```text
TypeError: function takes 1 positional arguments but 2 were given
```

Also test the empty case:
```python
next(iter(()), None)
```

Record the exact result rather than assuming it.

This establishes that the failure belongs to the built-in `next` default-value surface, not generators, `OverworldPresenter`, dataclasses, or session state.

## Production Census

Before edits, dynamically AST-scan only:
```text
root/src/app/**/*.py
```

Require exactly **8 direct two-positional-argument `next()` calls across 5 production files**, all with `None` as the second argument:
```text
root/src/app/presentation/overworld_presenter.py
  1
  selected inventory item

root/src/app/presentation/battle_presenter.py
  1
  selected move

root/src/app/player/run_items.py
  2
  run-item definition
  inventory recipe pair

root/src/app/player/inventory_action.py
  1
  recipe for inventory action

root/src/app/game/overworld_session.py
  3
  previous stat row
  current stat row
  selected stat row
```

Require:
```text
two-argument next calls: 8
default value None:      8
production files:        5
```

Do not count test/tooling calls.

Stop before implementation if the live census differs. Do not silently expand MPY16 to another built-in compatibility surface.

## Implementation

Create:
```text
root/src/app/iteration.py
```

with one portable primitive:
```python
"""Small portable iteration primitives used by the gameplay runtime."""


def first_or_none(values):
    for value in values:
        return value
    return None
```

This helper deliberately implements only the behavior DD actually requires:
```text
first yielded value
or None when exhausted
```

Do not generalize it into:
```text
next_or_default(values, arbitrary_default)
portable_next(...)
iterator compatibility classes
builtins monkeypatching
MicroPython detection
an app.compat package
```

All eight current production sites use `None`, so arbitrary defaults are not required.

The helper must retain iterator laziness. It must not materialize the iterable into a tuple/list and must stop immediately after the first yielded value.

### Replace all eight production calls

Import:
```python
from app.iteration import first_or_none
```

where required.

Then make these semantic replacements.

`overworld_presenter.py`:
```python
selected_item = first_or_none(
    item
    for item in items
    if item.selection_key == selected_item_key
)
```

`battle_presenter.py`:
```python
selected = first_or_none(
    (number, move)
    for number, move in enumerate(moves, start=1)
    if move.name == selected_move_key
)
```

`run_items.py`, both lookup functions:
```python
return first_or_none(
    definition
    for definition in RUN_ITEM_DEFINITIONS
    if definition.item_id == item_id
)
```

and:
```python
return first_or_none(
    recipe
    for recipe in INVENTORY_RECIPES
    if set(recipe.ingredient_ids) == {first_item_id, second_item_id}
)
```

`inventory_action.py`:
```python
return first_or_none(
    recipe
    for recipe in INVENTORY_RECIPES
    if recipe.action_id == action_id
)
```

`overworld_session.py`, replace all three stat-row lookups with equivalent `first_or_none(...)` generator expressions.

Preserve exactly:
```text
first-match selection
authored iteration order
None when no match exists
short-circuit evaluation
non-StopIteration exception propagation
falsey first values
all existing caller behavior
```

Do not refactor surrounding methods.

## Permanent Contract Tests

Create:
```text
root/tests/test_next_default_contract.py
```

The file owns both the portable primitive contract and the permanent production AST invariant.

Test `first_or_none()` against native CPython:
```python
next(iter(values), None)
```

for at least:
```text
()
(None,)
(0,)
(False,)
("",)
("a",)
("a", "b")
```

Also prove laziness with a generator whose second side effect must never execute after the first yielded value is returned.

Prove non-`StopIteration` exceptions still propagate rather than being converted to `None`.

### AST invariant

Dynamically scan:
```text
root/src/app/**/*.py
```

and reject direct builtin-name calls with two or more positional arguments:
```python
next(iterator, None)
next(iterator, 0)
next(iterator, sentinel)
```

Allow:
```python
next(iterator)
obj.next(iterator, None)
something_else(iterator, None)
```

The permanent invariant is not “no `next` anywhere.”

It is:
```text
direct production next() calls with >= 2 positional args == 0
```

Synthetic AST tests must prove that exact classifier scope.

After implementation require:
```text
two-argument production next calls: 8 → 0
```

## Existing Behavioral Regression Coverage

Do not rewrite existing behavior tests simply to mention portability.

Keep the existing regression coverage authoritative for the eight consumers, particularly:
```text
tests/test_overworld_presenter.py
tests/test_battle_presenter.py
tests/test_item_first_inventory.py
tests/test_inventory_action_resolver.py
tests/test_overworld_session.py
```

These must continue to protect selected-item behavior, selected-move behavior, recipe lookup success/failure, inventory action rejection, stale stat-input handling, and ordinary session presentation.

No gameplay expectations should change.

## Direct MicroPython Qualification

After implementation, using the existing compatibility bootstrap, directly qualify:
```python
from app.iteration import first_or_none

print(first_or_none(iter(())))
print(first_or_none(iter((0,))))
print(first_or_none(iter(("a", "b"))))
```

Require:
```text
None
0
a
```

Also qualify laziness under MicroPython if practical with a tiny iterator/generator case.

Do not patch `builtins.next`.

The direct preflight:
```python
next(iter(("a",)), None)
```

should still fail on pinned MicroPython after MPY16. That failure is desirable evidence that DD crossed the boundary by changing its own required runtime surface rather than masking or modifying the interpreter.

## Raw Probe Qualification

Run the **unchanged**:
```text
root/tools/micropython_probe.py
root/tools/micropython_probe_bootstrap.py
```

The historical failure:
```text
SESSION_VIEW
TypeError: function takes 1 positional arguments but 2 were given
```

must disappear.

The probe may then naturally continue through:
```text
SESSION_VIEW
SESSION_ENCOUNTER_ENTRY
SESSION_ENCOUNTER_COMPLETE
```

Do not assume those later stages will pass.

If a new unrelated failure appears after the `next` boundary is crossed:
```text
record it
preserve the original traceback
finish only MPY16 verification/docs/release
do not repair it
```

Report:
```text
last PASS
first FAIL or RAW_PROBE_STAGES_COMPLETE
exception type
exception message
original traceback
FREE
ALLOC
DATACLASS EXPECTED
DATACLASS DECORATED
DATACLASS CONSTRUCTED
```

Native CPython and forced-overlay CPython probes must still reach:
```text
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

## Cumulative Verification

Run the full suite first.

Then run the exact sealed MPY15 cumulative suite that produced **259 passed**, appending the new MPY16 contract and the existing behavioral modules covering every changed consumer:
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
  tests\test_inventory_action_resolver.py

Pop-Location
```

Report the actual new total. Do not predict it.

Then run:
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

The dataclass manifest should remain structurally unchanged at:
```text
74 expected entries
```

but report the actual freshness result rather than assuming success.

## Expected Diff

Expected production changes:
```text
CREATE
root/src/app/iteration.py

MODIFY
root/src/app/presentation/overworld_presenter.py
root/src/app/presentation/battle_presenter.py
root/src/app/player/run_items.py
root/src/app/player/inventory_action.py
root/src/app/game/overworld_session.py
```

Expected test change:
```text
CREATE
root/tests/test_next_default_contract.py
```

Documentation:
```text
MODIFY
docs/portability/micropython-probe.md
```

Required final scope:
```text
two-argument next calls: 8 → 0
affected production files: 5
portable primitive files added: 1

builtins patching:          0
MicroPython source changes: 0
interpreter branches:       0
bootstrap changes:          0
raw probe changes:          0
gameplay changes:           0
content changes:            0
route changes:              0
persistence/schema changes: 0
historical docs/mpy changes:0
```

## Documentation

Update:
```text
docs/portability/micropython-probe.md
```

Record the sealed MPY15 SHA and evidence:
```text
133846f6b15b0ea3ed2153af69b104a0945b3fcf

SESSION_IMPORT        PASS
SESSION_CONSTRUCTION  PASS
SESSION_VIEW          FAIL
TypeError: function takes 1 positional arguments but 2 were given
```

Document:
```text
exact traceback location
direct pinned next(one-arg) result
direct pinned next(two-arg) result
upstream NEXT2 feature boundary
pre-edit 8-site census
all defaults == None
first_or_none design
CPython semantic oracle
lazy-evaluation evidence
post-edit zero-site AST invariant
full-suite total
cumulative-suite total
native probe result
forced-overlay probe result
direct MicroPython helper result
unchanged raw-probe result
next frontier
memory values
dataclass census
scope counts
```

Explicitly state that MPY16:
```text
does not enable MICROPY_PY_BUILTINS_NEXT2
does not patch builtins.next
does not add interpreter detection
does not alter first-match semantics
does not change gameplay/session state
```

Leave the historical untracked:
```text
docs/mpy/
```

files untouched and uncommitted.

## Stop Conditions

Stop and request a revised MPY16 plan if the baseline AST census is not exactly eight two-argument `next()` calls with `None` defaults, the pinned primitive reproduction does not match the observed `SESSION_VIEW` arity failure, preserving semantics requires something broader than first-or-None selection, a builtins/interpreter/bootstrap change becomes necessary, or the historical `next`-arity failure remains after all eight authorized sites are removed.

If the unchanged raw probe crosses that boundary and then fails for an unrelated reason, **MPY16 has succeeded**. Record the new frontier and finish documentation, verification, commit, push, and CI only.

Do not repair the new frontier inside MPY16.

## Release

Commit exactly:
```text
MPY16 - Repair Portable Next Default Boundary
```

Push:
```text
mpy
```

Then verify:
```text
local HEAD == origin/mpy
tracked worktree clean
exact-SHA CI successful
historical docs/mpy files untouched
```

Final report must include the commit SHA/message, full and cumulative test totals, `8 → 0` production census, CPython semantic-oracle result, pinned one-argument/two-argument `next` evidence, direct `first_or_none` qualification, every raw session stage reached, last pass/next failure or complete marker, traceback, memory, dataclass census, CI run, branch synchronization, and untracked-file preservation.

If the current session track completes after MPY16, MPY17 can remain the planned full-route qualification. If another unrelated session-runtime incompatibility appears first, preserve that evidence and derive the next gate from it rather than forcing the full-route milestone prematurely.

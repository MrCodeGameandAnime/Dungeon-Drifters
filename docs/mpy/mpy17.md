# MPY17 - Repair Portable Runtime Random Boundary

**Goal:** Advance pinned MicroPython `v1.29.0` beyond the sealed MPY16 `SESSION_ENCOUNTER_ENTRY` failure by providing the combat runtime with the narrow `randint` / `choice` surface it requires, using the `random.getrandbits()` primitive shared by CPython and the pinned MicroPython runtime when native convenience functions are unavailable.

**Baseline:**
```text
branch: mpy
SHA: dbc1da7586f209837aede5b04c670aa830e62f62

MicroPython: v1.29.0
source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
platform: win32
```

Sealed MPY16 frontier:
```text
BATTLE_CONSTRUCTION        PASS
BATTLE_VIEW                PASS
BATTLE_INPUT               PASS
BATTLE_COMPLETE            PASS
SESSION_IMPORT             PASS
SESSION_CONSTRUCTION       PASS
SESSION_VIEW               PASS
SESSION_ENCOUNTER_ENTRY    FAIL

TypeError: rng must provide randint

FREE: 671840
ALLOC: 352672

DATACLASS EXPECTED:    74
DATACLASS DECORATED:   73
DATACLASS CONSTRUCTED: 33
```

Original failure path:
```text
OverworldSession.submit()
→ OverworldSession._create_active_battle()
→ Battle(...)
→ Battle.__init__()
→ rng validation
→ TypeError: rng must provide randint
```

The standalone Battle probe already passes because it injects its own deterministic RNG. The session probe constructs the real `Battle` class through `OverworldSession`, allowing `Battle`'s default `rng=random` to take effect.

MPY17 repairs that production runtime boundary. It must not inject probe-only randomness or change `OverworldSession` simply to satisfy qualification.

## Root-Cause Qualification

Before editing DD source, run these independently under the pinned MicroPython interpreter:
```python
import random

print(callable(getattr(random, "getrandbits", None)))
print(callable(getattr(random, "randint", None)))
print(callable(getattr(random, "choice", None)))
print(callable(getattr(random, "randrange", None)))
```

The expected boundary from the pinned upstream configuration is:
```text
getrandbits: True
randint:     False
choice:      False
randrange:   False
```

Then directly prove the primitive:
```python
value = random.getrandbits(8)

assert isinstance(value, int)
assert 0 <= value <= 255
print("GETRANDBITS|PASS")
```

Record the actual results.

Stop before implementation if `getrandbits` is absent or non-callable. Do not design another RNG source inside MPY17.

The upstream explanation must also be recorded: pinned MicroPython places `randint`, `choice`, and `randrange` behind:
```text
MICROPY_PY_RANDOM_EXTRA_FUNCS
```

while the Windows standard build enables `MICROPY_PY_RANDOM` without enabling those extra functions.

Do not rebuild MicroPython with the extra-functions flag.

## Production Census

Before editing, dynamically inspect:
```text
root/src/app/**/*.py
```

Require exactly three direct production stdlib `random` imports:
```text
root/src/app/combat/battle.py
root/src/app/combat/resolver.py
root/src/app/world/event.py
```

Classify them:
```text
battle.py
→ core headless combat runtime
→ randint + choice requirement

resolver.py
→ core mechanical combat runtime
→ randint requirement

world/event.py
→ legacy/terminal event path
→ randint
→ not in the sealed headless session qualification path
```

Within `root/src/app/combat/**/*.py`, require exactly:
```text
stdlib random imports: 2

Battle runtime requirements:
  randint
  choice

CombatResolver runtime requirements:
  randint
```

Also confirm there are no production combat requirements for:
```text
random.random
uniform
shuffle
sample
randrange
```

If this census differs, stop and report instead of silently expanding MPY17.

## Architecture

Add one narrow runtime-random adapter:
```text
root/src/app/randomness.py
```

The adapter preserves native CPython behavior when `random.randint` / `random.choice` exist.

When those conveniences are absent, it derives equivalent DD-required behavior from:
```text
random.getrandbits
```

The boundary becomes:
```text
Battle
        \
         → app.randomness
        /       |
Resolver        |
                ├─ native randint/choice when supplied by runtime
                |
                └─ getrandbits fallback otherwise
```

This is capability-based, not interpreter-based.

There must be no:
```text
sys.implementation check
"micropython" string check
platform branch
builtins patch
random module replacement in sys.modules
MicroPython source modification
alternate Battle implementation
```

## Portable Random Implementation

Create:
```text
root/src/app/randomness.py
```

with this responsibility only:
```python
"""Portable runtime randomness for Dungeon Drifters gameplay."""

import random as _backend


def _randbelow(limit):
    if limit <= 0:
        raise ValueError("random range must be positive")

    getrandbits = getattr(_backend, "getrandbits", None)
    if not callable(getrandbits):
        raise TypeError("random backend must provide getrandbits")

    bits = 0
    maximum = limit - 1
    while maximum:
        bits += 1
        maximum >>= 1

    if bits == 0:
        return 0

    while True:
        candidate = getrandbits(bits)
        if candidate < limit:
            return candidate


def randint(start, end):
    native = getattr(_backend, "randint", None)
    if callable(native):
        return native(start, end)

    span = end - start + 1
    if span <= 0:
        raise ValueError("empty range for randint")

    return start + _randbelow(span)


def choice(values):
    native = getattr(_backend, "choice", None)
    if callable(native):
        return native(values)

    length = len(values)
    if length == 0:
        raise IndexError("cannot choose from an empty sequence")

    return values[_randbelow(length)]
```

The exact wording of private error messages is not a gameplay contract, but the behavioral categories must remain:
```text
invalid randint range → ValueError
empty choice          → IndexError
missing getrandbits   → TypeError
```

### Why rejection sampling is required

Do **not** implement:
```python
getrandbits(32) % limit
```

That introduces modulo bias whenever the range does not divide the random domain evenly.

`_randbelow()` must reject generated values outside the usable range, so:
```text
randint
→ uniform inclusive integer selection

choice
→ uniform sequence-index selection
```

The adapter must not materialize `values` into another collection.

`choice()` may assume the same sequence-like contract already required by the current combat runtime: `len()` plus integer subscription.

## Preserve CPython Behavior

The adapter must prefer native functions when present:
```python
native = getattr(_backend, "randint", None)
if callable(native):
    return native(...)
```

and equivalently for `choice`.

This is important for two reasons.

First, ordinary CPython DD continues to use CPython's existing random behavior instead of replacing it with a home-grown implementation.

Second, existing tests already patch both patterns:
```text
stdlib random.randint / random.choice

and

battle_module.random.randint / battle_module.random.choice
```

The adapter design must preserve both.

Do not cache native callables at import time.

This would be wrong:
```python
_NATIVE_RANDINT = _backend.randint
```

because later monkeypatching of the backend would no longer propagate.

Capability lookup must occur when `randint()` / `choice()` is called.

## Combat Integration

Modify:
```text
root/src/app/combat/battle.py
root/src/app/combat/resolver.py
```

Replace:
```python
import random
```

with:
```python
import app.randomness as random
```

Preserve the existing symbol name `random`.

Do not otherwise alter:
```text
select_enemy_move()
Battle.__init__()
Battle RNG validation
Battle initiative
CombatResolver.__init__()
hit rolls
crit rolls
heal rolls
Frost/backlash rolls
enemy move selection
RNG injection APIs
```

The existing defaults therefore remain conceptually:
```python
rng=random
```

but `random` now refers to the DD runtime adapter.

This preserves all existing injected RNG objects and all tests that construct:
```python
Battle(..., rng=custom_rng)
CombatResolver(rng=custom_rng)
```

## Explicitly Deferred Production Random Site

Do **not** modify:
```text
root/src/app/world/event.py
```

in MPY17.

It is the third production stdlib-random import, but it is outside the sealed headless runtime path and its terminal `Events.avoid_battle()` behavior is unrelated to the observed `SESSION_ENCOUNTER_ENTRY` failure.

After MPY17, the expected whole-app direct stdlib-random census is therefore:
```text
before: 3
after:  2

remaining:
root/src/app/randomness.py
root/src/app/world/event.py
```

and the core combat census becomes:
```text
root/src/app/combat/**/*.py
direct stdlib random imports: 2 → 0
```

Do not broaden this gate merely to achieve a cosmetic whole-repository zero.

## Contract Tests

Create:
```text
root/tests/test_random_contract.py
```

### Native delegation

Use a fake backend exposing native `randint` and `choice`.

Temporarily replace:
```python
app.randomness._backend
```

with that backend.

Prove:
```text
randint forwards exact start/end
choice forwards exact sequence
native return value is returned unchanged
getrandbits fallback is not touched
```

This protects native CPython delegation.

### Fallback randint

Use a fake backend that provides:
```text
getrandbits
```

but deliberately does **not** provide:
```text
randint
choice
```

Use scripted values proving rejection sampling.

Example for:
```python
randint(1, 3)
```

the span is 3 and therefore requires 2 bits.

Script:
```text
3  → rejected
2  → accepted
```

Require:
```text
result == 3
getrandbits calls == [2, 2]
```

Also test degenerate inclusive range:
```python
randint(7, 7) == 7
```

and invalid range:
```python
randint(8, 7)
→ ValueError
```

### Fallback choice

For:
```python
("a", "b", "c")
```

script index generation:
```text
3 → rejected
1 → accepted
```

Require:
```text
choice(...) == "b"
```

and prove:
```python
choice(())
→ IndexError
```

### Missing primitive

With a backend exposing neither convenience APIs nor `getrandbits`, require the fallback path to raise:
```text
TypeError
```

Do not silently use timestamps, hashes, process state, or another pseudo-random source.

## Integration Contract

In `test_random_contract.py`, also prove that the default combat objects are now wired through the DD adapter.

Require:
```python
from app import randomness
from app.combat.resolver import CombatResolver

assert CombatResolver().rng is randomness
```

For `Battle`, monkeypatch:
```python
randomness.randint
randomness.choice
```

to deterministic callables, construct a normal Battle without an explicit `rng`, and require:
```text
Battle construction succeeds
battle.rng is app.randomness
battle.resolver.rng is app.randomness
```

This directly protects the exact path that failed under MPY16.

## Permanent AST Boundary

The new contract test must dynamically scan:
```text
root/src/app/combat/**/*.py
```

and reject direct stdlib random imports:
```python
import random
import random as rng
from random import randint
from random import choice
```

Allow:
```python
import app.randomness as random
from app import randomness
```

The permanent invariant is:
```text
core combat modules directly importing stdlib random == 0
```

Include synthetic AST cases proving the classifier distinguishes stdlib `random` from `app.randomness`.

Do not prohibit test-side `random`.

Do not prohibit the separately deferred:
```text
root/src/app/world/event.py
```

## Existing Regression Coverage

Do not rewrite random-sensitive gameplay tests merely because the provider module moved.

Existing tests must remain authoritative for:
```text
initiative randomness
enemy move selection
resolver hit rolls
critical rolls
healing rolls
Frost/backlash rolls
custom RNG injection
random monkeypatching
all Drifter battle completion
terminal smoke behavior
```

In particular, preserve compatibility with tests that patch:
```python
random.randint
random.choice
```

on CPython.

That compatibility is why `app.randomness` dynamically delegates to the backend instead of capturing the functions at import time.

## Direct CPython Qualification

Before MicroPython qualification, run a direct adapter sanity check under CPython:
```python
from app import randomness

for _ in range(100):
    value = randomness.randint(1, 100)
    assert 1 <= value <= 100

for _ in range(100):
    value = randomness.choice(("a", "b", "c"))
    assert value in ("a", "b", "c")

print("RANDOMNESS|CPYTHON|PASS")
```

Native delegation should be active.

## Direct MicroPython Qualification

Under pinned MicroPython with the existing compatibility bootstrap:
```python
import random

assert callable(getattr(random, "getrandbits", None))
assert not callable(getattr(random, "randint", None))
assert not callable(getattr(random, "choice", None))

from app import randomness

assert randomness.randint(7, 7) == 7
assert randomness.choice(("only",)) == "only"

for _ in range(32):
    value = randomness.randint(1, 100)
    if value < 1 or value > 100:
        raise AssertionError("randint escaped requested range")

for _ in range(32):
    value = randomness.choice(("a", "b", "c"))
    if value not in ("a", "b", "c"):
        raise AssertionError("choice escaped supplied sequence")

print("RANDOMNESS|MPY|PASS")
```

The native MicroPython convenience functions must remain absent after MPY17.

That is expected evidence:
```text
native random.randint: unavailable
native random.choice:  unavailable
DD randomness.randint: PASS
DD randomness.choice:  PASS
```

MPY17 crosses the runtime boundary without modifying the interpreter.

## Raw Probe Qualification

Run the unchanged:
```text
root/tools/micropython_probe.py
root/tools/micropython_probe_bootstrap.py
```

Do not inject `_DeterministicRng` into the session portion of the raw probe.

Do not alter:
```text
OverworldSession
battle_factory invocation
SESSION_ENCOUNTER_ENTRY stage
SESSION_ENCOUNTER_COMPLETE stage
```

The historical failure:
```text
SESSION_ENCOUNTER_ENTRY
TypeError: rng must provide randint
```

must disappear.

The unchanged probe should then naturally attempt:
```text
SESSION_ENCOUNTER_ENTRY
SESSION_ENCOUNTER_COMPLETE
RAW_PROBE_STAGES_COMPLETE
```

Do not assume either later result.

If the probe crosses the RNG validation and reaches a new unrelated failure, that is successful MPY17 evidence.

Record:
```text
last PASS
first FAIL or RAW_PROBE_STAGES_COMPLETE
exception type
exception message
full original traceback
FREE
ALLOC
DATACLASS EXPECTED
DATACLASS DECORATED
DATACLASS CONSTRUCTED
```

Do not repair another incompatibility inside this gate.

## Native And Forced-Overlay Qualification

Both CPython probe modes must continue to reach:
```text
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

This specifically verifies that introducing `app.randomness` did not alter the normal host runtime or forced portability overlay environment.

## Verification

Run the full suite first.

Then run the exact sealed MPY16 cumulative portability suite plus the new MPY17 contract and the random-sensitive combat regressions:
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
  tests\test_battle_ui_hardening.py

Pop-Location
```

Report the actual cumulative total.

Do not predict it.

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

Require the dataclass manifest to remain current with:
```text
74 entries
```

No dataclass declarations should change.

## Expected Diff

Expected production:
```text
CREATE
root/src/app/randomness.py

MODIFY
root/src/app/combat/battle.py

MODIFY
root/src/app/combat/resolver.py
```

Expected tests:
```text
CREATE
root/tests/test_random_contract.py
```

Expected documentation:
```text
MODIFY
docs/portability/micropython-probe.md
```

No other production files should be required.

Final scope should report:
```text
new portable random adapter:          1
existing production files modified:   2

core combat stdlib random imports:    2 → 0
whole-app stdlib random imports:      3 → 2

remaining direct stdlib imports:
  app/randomness.py
  app/world/event.py

MicroPython source changes:            0
MicroPython config changes:            0
builtins patches:                      0
sys.modules random overlays:           0
interpreter detection:                 0
OverworldSession changes:              0
raw probe changes:                     0
bootstrap changes:                     0
gameplay rule changes:                 0
content changes:                       0
route changes:                         0
persistence/schema changes:            0
historical docs/mpy changes:           0
```

## Documentation

Update:
```text
docs/portability/micropython-probe.md
```

Record the sealed MPY16 baseline:
```text
dbc1da7586f209837aede5b04c670aa830e62f62
```

and its frontier:
```text
SESSION_VIEW               PASS
SESSION_ENCOUNTER_ENTRY    FAIL
TypeError: rng must provide randint

FREE: 671840
ALLOC: 352672

EXPECTED:    74
DECORATED:   73
CONSTRUCTED: 33
```

Document the exact failure traceback and the relationship:
```text
OverworldSession
→ Battle default RNG
→ native MicroPython random module
→ randint absent
```

Record the pinned native capability evidence:
```text
random import
getrandbits
randint
choice
randrange
```

and the upstream feature boundary:
```text
MICROPY_PY_RANDOM
MICROPY_PY_RANDOM_EXTRA_FUNCS
Windows standard/core configuration
```

Then document:
```text
pre-edit random-import census
combat runtime requirements
adapter design
native delegation
getrandbits rejection-sampling fallback
fallback contract tests
existing monkeypatch compatibility
post-edit AST census
direct CPython adapter qualification
direct MicroPython adapter qualification
native and forced-overlay raw probes
pinned raw-probe result
full suite total
cumulative suite total
memory
dataclass census
next frontier
scope counts
```

Explicitly state:
```text
MPY17 does not enable MICROPY_PY_RANDOM_EXTRA_FUNCS.
MPY17 does not replace MicroPython's random module.
MPY17 does not patch builtins or sys.modules.
MPY17 does not add interpreter detection.
MPY17 preserves CPython's native randint/choice behavior when available.
MPY17 changes no combat probabilities or gameplay rules.
```

Leave historical:
```text
docs/mpy/
```

untouched and uncommitted.

## Stop Conditions

Stop and request a revised MPY17 plan if any of these occurs:
```text
pinned random.getrandbits is unavailable

the native random capability census differs materially

core combat requires a random operation beyond randint/choice

the production random-import census differs

preserving CPython behavior requires changing gameplay RNG contracts

the getrandbits fallback requires interpreter detection

OverworldSession or raw-probe changes become necessary

the rng validation failure remains after Battle defaults to app.randomness
```

If:
```text
SESSION_ENCOUNTER_ENTRY
```

passes and a new unrelated failure appears later, **MPY17 succeeded**.

Record that failure and continue only with:
```text
documentation
verification
commit
push
exact-SHA CI
```

Do not repair it inside MPY17.

## Gate Renumbering

Because MPY17 is now consumed by a real evidence-derived compatibility frontier, do not force the old route milestone into this commit.

Update future gates to:
```text
MPY17 Portable runtime random boundary.

MPY18 Eight encounters, three Rests, Dungeon Entrance.

MPY19 Constrained-target memory and runtime pressure.

MPY20 Cross-runtime regression qualification.
```

If MPY17 exposes another unrelated compatibility failure before the current raw session stages complete, derive the next gate from that evidence instead of pretending MPY18 is ready for the entire route.

## Release

Commit exactly:
```text
MPY17 - Repair Portable Runtime Random Boundary
```

Push:
```text
mpy
```

Verify:
```text
local HEAD == origin/mpy
tracked worktree clean
exact-SHA CI completed successfully
historical docs/mpy files unchanged and uncommitted
```

The final MPY17 report must include the commit SHA/message, full-suite and cumulative totals, exact pre/post random census, pinned native random capability results, CPython delegation result, fallback rejection-sampling result, direct MicroPython adapter result, all raw session stages reached, last PASS, next FAIL or complete marker, traceback, memory, dataclass census, CI run ID/conclusion, branch synchronization, and historical-file preservation.

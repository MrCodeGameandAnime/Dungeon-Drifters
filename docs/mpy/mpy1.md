```markdown
# MPY1 - Add Portable Read-Only Mapping Boundary

## Summary

Begin from the verified sealed MPY0 state on branch:

```text
mpy
```

Expected baseline:

```text
HEAD:
f39770a236568db7f2fa9002bf6725611682ac06

MPY0:
SEALED

Working tree:
clean

Remote:
origin/mpy synchronized
```

MPY0 successfully provisioned and executed the pinned upstream MicroPython `v1.29.0` Windows runtime against untouched Dungeon Drifters production source.

The first observed incompatibility was:

```text
MPY|CATALOG_IMPORT|BEGIN
MPY|CATALOG_IMPORT|FAIL|ImportError|no module named 'types'
```

Original traceback:

```text
root/src/app/content/catalog.py, line 3
ImportError: no module named 'types'
```

The MicroPython source and runtime evidence were:

```text
Tag:
v1.29.0

Source SHA:
0fd6c573ea815774668bbb16b8e197c8822368b2

Source checkout:
clean

Runtime:
MicroPython 1.29.0

Platform:
win32
```

MPY1 will address only this first observed compatibility wall.

It will not proactively migrate other expected incompatibilities such as:

- dataclasses
- enum / StrEnum
- typing
- annotations
- collections
- regex
- keyword
- persistence
- pathlib
- tempfile

Those remain out of scope until the raw probe reaches them.

The objective is:

```text
Preserve DD's existing read-only mapping semantics
        ↓
remove the hard runtime dependency on types.MappingProxyType
        ↓
rerun the unchanged MPY0 probe
        ↓
prove CATALOG_IMPORT passes
        ↓
stop at the next observed MicroPython failure
```

## Governing Rule

MPY1 is evidence-driven.

The only compatibility problem authorized for correction is the one demonstrated by MPY0:

```text
ImportError: no module named 'types'
```

No speculative portability migration is allowed.

The governing rule remains:

```text
No production compatibility change without an observed MicroPython failure
or a directly proven prerequisite of that failure.
```

## Gate Objective

Determine exactly how Dungeon Drifters uses:

```python
types.MappingProxyType
```

and introduce the smallest host-neutral abstraction necessary to preserve those semantics across:

- CPython
- Pyodide
- Chaquopy
- MicroPython

The solution must preserve one authoritative gameplay and content implementation.

MPY1 must not create a MicroPython-specific content catalog or fork.

## Phase 1 - Repository Usage Audit

Before modifying production code, identify every production use of:

```text
types
MappingProxyType
```

Search the complete production runtime under:

```text
root/src/app
```

Do not limit the audit to `catalog.py`.

Record:

- every importing file
- every construction site
- every exposed field or property using the resulting object
- every read operation performed against those mappings
- every equality assumption
- every mutation attempt or mutation-prevention test
- every serialization/reconstruction assumption
- every type check involving the proxy
- whether the backing dictionaries are ever mutated after wrapping

Explicitly determine whether DD depends on true CPython `MappingProxyType` live-view semantics.

A CPython mapping proxy is not merely an immutable dictionary.

The audit must distinguish between:

```text
A. Read-only mapping contract only

mapping[key]
key in mapping
iteration
len(mapping)
.get()
.keys()
.values()
.items()
equality

and

B. True live proxy behavior

backing dictionary changes
        ↓
existing read-only proxy immediately reflects those changes
```

If DD never mutates the backing dictionary after construction, do not emulate live-proxy behavior merely because CPython provides it.

## Required Behavioral Contract

Derive the minimum actual DD contract from live code and tests.

Expected candidate behavior includes:

```text
lookup by key
membership
iteration
length
get
keys
values
items
equality where currently relied upon
mutation rejection
stable authored values
```

Do not assume all of these are required.

Prove each requirement from the repository.

Also explicitly determine whether DD requires:

```text
hashability
copy support
deepcopy support
repr equivalence
pickling
isinstance(..., MappingProxyType)
identity behavior
live backing-map reflection
```

If not used, they are not part of the compatibility contract.

## Phase 2 - Choose the Narrowest Architecture

Do not create a broad generic compatibility framework in MPY1.

Do not introduce:

```text
app.compat
```

unless the repository evidence demonstrates that a broader runtime-compatibility package is already necessary for this single problem.

Prefer a narrow semantic helper.

Candidate shape:

```text
readonly_mapping(...)
```

The exact module location must follow existing DD ownership and package conventions after inspecting the repository.

Possible conceptual examples:

```text
app/runtime/readonly_mapping.py
```

or another existing shared utility location if one already fits better.

Do not create a new architectural layer merely to host one function.

The production call sites should depend on the semantic operation:

```python
readonly_mapping(source)
```

rather than directly depending on:

```python
types.MappingProxyType
```

## Preferred Runtime Strategy

Where the host provides the mature CPython implementation, preserve it.

Conceptually:

```python
try:
    from types import MappingProxyType
except ImportError:
    MappingProxyType = None
```

followed by a narrow helper or equivalent implementation boundary.

The exact implementation must be based on repository evidence and MicroPython capability, not this pseudocode.

Preferred behavior:

```text
CPython
    → use native MappingProxyType where possible

Pyodide
    → use native CPython MappingProxyType

Chaquopy
    → use native CPython MappingProxyType

MicroPython
    → use the smallest DD-compatible read-only mapping substitute
```

Do not force CPython, Pyodide, or Chaquopy through a weaker homemade implementation unless there is a compelling reason.

## MicroPython Fallback Requirements

If a fallback read-only mapping object is necessary, it must implement only the behavior DD actually requires.

It must not attempt to recreate the entire CPython `types` module.

It must not become a general-purpose MappingProxyType clone.

It must preserve DD's required immutability boundary.

For example, if DD requires:

```text
mapping[key]
len(mapping)
iteration
membership
get
keys
values
items
```

the fallback should support those operations.

Mutation through the exposed object must fail.

Operations such as:

```python
mapping["x"] = value
del mapping["x"]
mapping.clear()
mapping.update(...)
mapping.pop(...)
```

must not silently mutate the underlying authored data if those operations are exposed.

Do not weaken authored content immutability merely to satisfy MicroPython.

## Backing Mapping Ownership

Explicitly determine whether the compatibility helper should:

```text
A. Wrap the provided mapping directly

or

B. Copy the mapping and expose a read-only snapshot
```

This decision must follow DD's actual behavior.

If production code never mutates the backing dictionary after wrapping, a snapshot may be sufficient and safer under MicroPython.

If DD depends on live reflection of backing-dictionary changes, the fallback must preserve that behavior or MPY1 must stop and report that the compatibility requirement is larger than expected.

Do not make this choice by assumption.

## Scope of Production Changes

MPY1 may modify only production files directly required to replace the observed `MappingProxyType` dependency cleanly.

Expected change categories:

```text
one narrow read-only mapping helper
MappingProxyType import replacement at actual production call sites
targeted contract tests
MPY documentation update
```

Do not touch unrelated models or runtime features.

No changes are authorized to:

```text
Battle
CombatResolver
OverworldSession behavior
GameState behavior
PlayerState behavior
progression
Drifter mechanics
enemy mechanics
route logic
reward logic
Rest behavior
semantic inputs
semantic views
save schema
browser code
Android code
terminal behavior
```

unless compilation requires a purely mechanical import update directly caused by the new read-only mapping helper.

## Tests

Add focused behavioral tests for the compatibility boundary.

The tests must prove the DD contract, not implementation details.

At minimum, where applicable, test:

```text
construction from an ordinary mapping

key lookup

membership

iteration

length

get / keys / values / items
if DD relies on them

equality
if DD relies on it

mutation rejection

source-value preservation

nested authored values remain unchanged

native CPython path behaves exactly as before
```

If DD relies on live backing-map behavior, test it explicitly.

If DD does not rely on live behavior, do not create an artificial requirement for it.

## Native CPython Preservation

Under normal CPython, verify that the compatibility boundary still uses native:

```python
types.MappingProxyType
```

if that remains the chosen architecture.

The fallback implementation should not be exercised accidentally under CPython.

If practical, add a targeted test proving the native implementation is selected under CPython without coupling unrelated tests to implementation internals.

## MicroPython Probe

After the MPY1 change is implemented and all CPython tests pass, rerun the exact MPY0 probe under the exact same pinned MicroPython runtime:

```text
MicroPython:
v1.29.0

Source SHA:
0fd6c573ea815774668bbb16b8e197c8822368b2

Platform:
win32
```

Invocation remains:

```powershell
<external>\micropython.exe root/tools/micropython_probe.py root/src
```

Do not alter the raw probe merely to make MPY1 pass unless the probe itself contains a demonstrated defect.

The desired progression is:

```text
MPY|CATALOG_IMPORT|BEGIN
MPY|CATALOG_IMPORT|PASS
```

The probe should then continue naturally until the next real incompatibility.

When the next failure occurs:

```text
STOP.
```

Do not fix the next failure during MPY1.

Record it as evidence for the next gate.

## Probe Success Interpretation

MPY1 succeeds if the previous failure is crossed.

Example:

```text
MPY|CATALOG_IMPORT|PASS
MPY|DRIFTER_SPEC|BEGIN
...
MPY|<NEXT_STAGE>|FAIL|<ExceptionType>|<message>
```

That is a successful MPY1 result.

MPY1 is not required to reach:

```text
create_new_game()
Battle
BattleView
OverworldSession
full route
```

unless the runtime naturally reaches them before encountering another incompatibility.

The next failure is useful evidence, not an MPY1 defect.

## Memory Evidence

Preserve the existing MPY0 memory reporting.

Compare:

```text
MPY0 CATALOG_IMPORT failure memory
```

against:

```text
MPY1 CATALOG_IMPORT success memory
```

where possible.

Do not optimize based on Windows-port heap measurements.

The purpose is only to detect obvious pathological growth caused by the fallback.

Hardware-specific memory qualification remains MPY5 work.

## Cross-Runtime Safety

The new boundary must remain suitable for:

```text
CPython / Windows

Pyodide / Browser

Chaquopy / Android

MicroPython / future constrained host
```

The compatibility helper must not:

- import browser APIs
- import Android APIs
- depend on Windows
- depend on PS5 assumptions
- contain gameplay behavior
- know about authored Drifters
- know about enemies
- know about routes
- know about combat
- know about persistence

It must remain a tiny Python runtime compatibility primitive.

## Documentation Update

Update:

```text
docs/portability/micropython-probe.md
```

with an MPY1 evidence section recording:

```text
MPY0 failure:
types / MappingProxyType import

Observed location:
root/src/app/content/catalog.py

MPY1 adaptation:
<exact implemented boundary>

DD semantics preserved:
<summary>

CPython implementation:
<native MappingProxyType or actual chosen behavior>

MicroPython implementation:
<actual fallback>

MPY1 probe result:
<exact stage progression>

Next observed failure:
<stage / exception / message>

MicroPython runtime:
v1.29.0

MicroPython source SHA:
0fd6c573ea815774668bbb16b8e197c8822368b2
```

Do not rewrite MPY0 history.

MPY0 remains the sealed raw baseline.

## Verification

Before running MicroPython:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall root/src root/tests root/tools
git diff --check
```

The full existing suite must remain green.

Expected baseline suite size before new MPY1 tests:

```text
1,262 passed
```

The final total should therefore be:

```text
>= 1,262 passed
```

with any additional count attributable only to new MPY1 tests.

Run the raw probe under CPython:

```powershell
.\.venv\Scripts\python.exe root/tools/micropython_probe.py root/src
```

This verifies the ordinary runtime remains healthy.

Then run the exact same raw probe under pinned MicroPython:

```powershell
<external>\micropython.exe root/tools/micropython_probe.py root/src
```

Capture the complete output.

Review:

```powershell
git diff --stat
git diff --check
git status --short
```

Confirm every changed production file is directly justified by the observed MappingProxyType compatibility requirement.

## CI

After local verification:

1. Commit MPY1.
2. Push `mpy`.
3. Run the normal DD CI suite.
4. Require CI green.
5. Verify:

```text
local HEAD == origin/mpy
```

6. Require clean working tree.

## Commit

Use:

```text
MPY1 - Add Portable Read-Only Mapping Boundary
```

## Acceptance Criteria

MPY1 is accepted when all of the following are true:

- The actual DD `MappingProxyType` usage has been audited.
- The minimum required read-only mapping semantics are documented.
- True live-proxy semantics are preserved only if DD actually requires them.
- The direct hard dependency on unavailable MicroPython `types.MappingProxyType` is removed from the failing runtime path.
- CPython continues using its native implementation where appropriate.
- MicroPython uses only a narrow DD-compatible substitute where required.
- Authored content remains immutable through the exposed mapping boundary.
- No gameplay semantics change.
- No content values change.
- No semantic API changes.
- No broad `app.compat` architecture is introduced without demonstrated need.
- Focused compatibility tests pass.
- Full pytest passes.
- Compileall passes.
- Diff-check passes.
- CPython probe passes.
- The pinned MicroPython probe passes `CATALOG_IMPORT`.
- The MicroPython probe stops at the next real incompatibility, if one exists.
- The next incompatibility is recorded but not repaired.
- CI is green.
- Local and remote SHA match.
- Working tree is clean.

## Explicit Stop Rules

Stop MPY1 immediately if:

- DD materially depends on `MappingProxyType` semantics that cannot be reproduced narrowly.
- Preserving the behavior requires changing content ownership.
- Preserving the behavior requires modifying combat or session logic.
- The proposed fallback becomes a substantial reimplementation of CPython's `types` module.
- The compatibility boundary requires widespread platform conditionals.
- CPython behavior changes unexpectedly.
- Existing DD tests regress.
- content immutability must be weakened.
- the MicroPython probe crosses the `types` failure and reaches a new incompatibility.

When the next MicroPython incompatibility appears:

```text
DO NOT FIX IT IN MPY1.
```

Record:

```text
stage
exception type
exception message
traceback
memory evidence
```

and derive the next gate from that evidence.

## Non-Goals

MPY1 does not attempt to solve:

```text
dataclasses
StrEnum
typing
Protocol
runtime_checkable
PEP 604 annotations
built-in generic annotations
collections.Counter
collections.abc
keyword
re differences
pathlib
tempfile
SaveRepository coupling
MicroPython memory optimization
browser integration
Android integration
PS5 integration
```

Even if those are expected future incompatibilities.

They remain speculative until the probe actually reaches them.

## MPY1 Completion State

The desired gate transition is:

```text
MPY0

CATALOG_IMPORT
FAIL
ImportError: no module named 'types'

        ↓

MPY1

introduce minimal portable read-only mapping boundary

        ↓

CATALOG_IMPORT
PASS

        ↓

probe continues naturally

        ↓

NEXT REAL FAILURE

        ↓

STOP
```

MPY1 is successful when the evidence frontier moves forward without changing Dungeon Drifters gameplay behavior.

## Governing Principle

MicroPython is allowed to influence DD's Python compatibility surface.

MicroPython is not allowed to influence DD's gameplay ownership architecture.

The compatibility effort must continue to preserve:

```text
one authoritative gameplay implementation
one CombatResolver
one Battle
one OverworldSession
one content authority
one progression system
one semantic runtime API
```

MPY1 exists only to move that same implementation one compatibility boundary farther.
```

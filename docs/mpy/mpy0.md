# MPY0 - Add Raw MicroPython Runtime Probe

## Summary

Begin from the verified clean `mpy` branch:

```text
HEAD:
4cfa883333c73478a188acf01fc88881f3d33633

Working tree:
clean

Remote:
origin/mpy synchronized
```

MPY0 will identify the first real MicroPython incompatibility without changing DD production code, adding compatibility shims, or altering gameplay.

The target is the upstream stable MicroPython `v1.29.0` Windows port. The runtime source will be cloned externally, checked out at the exact release tag, built using the official build procedure for that pinned release, and recorded by full resolved commit SHA.

References:

- [MicroPython v1.29.0 release](https://github.com/micropython/micropython/releases/tag/v1.29.0)
- [MicroPython v1.29.0 Windows port build instructions](https://github.com/micropython/micropython/blob/v1.29.0/ports/windows/README.md)

The Windows port is being used for MPY0 to qualify DD's MicroPython language, import, and standard-library compatibility without introducing arbitrary microcontroller hardware, flashing, serial transport, or board-specific memory constraints.

Hardware-specific memory qualification is deferred to a later gate.

## Tracked Changes

Add only:

```text
root/tools/micropython_probe.py
docs/portability/micropython-probe.md
```

No:

- `app.compat`
- production edits
- test behavior changes
- save changes
- browser code
- Android code
- content changes
- permanent MicroPython architecture

Runtime provisioning remains outside the repository.

The documentation will use this exact external layout:

```text
%LOCALAPPDATA%\DungeonDrifters\micropython\v1.29.0\
├── source\
└── build\
```

Provisioning will:

1. Clone:

   ```text
   https://github.com/micropython/micropython.git
   ```

2. Check out exactly:

   ```text
   v1.29.0
   ```

3. Record:

   ```powershell
   git rev-parse HEAD
   git status --porcelain
   ```

4. Require the checkout to be clean.

5. Follow the official Windows-port build procedure for the pinned `v1.29.0` source.

6. Build `mpy-cross` only if it is required by the pinned Windows-port build procedure or one of its documented dependencies. MPY0 will not introduce an unnecessary `mpy-cross` build requirement merely because other MicroPython ports use it.

7. Build the standard Windows port with the documented MSBuild workflow.

8. Verify that the resulting runtime identifies itself as stable MicroPython `v1.29.0`.

9. Reject:

   - preview builds
   - development builds
   - dirty source checkouts
   - unexpected MicroPython versions
   - source revisions not corresponding to the recorded pinned checkout

10. Invoke the resulting `micropython.exe` against the raw DD probe.

No MicroPython binary, object file, build output, or source checkout will be committed to Dungeon Drifters.

## Runtime Evidence Contract

The MicroPython source tag, commit SHA, and source cleanliness are external provisioning evidence.

They will be recorded from the actual MicroPython Git checkout, not inferred by the DD probe.

The run evidence must therefore contain:

```text
MicroPython tag:
v1.29.0

Resolved source SHA:
<full-sha>

Source checkout:
clean
```

using Git as the authority.

The probe itself is responsible only for reporting what the executing interpreter can directly identify about itself.

This avoids requiring the DD probe to know or reconstruct metadata about an external MicroPython source checkout.

## Probe Contract

`root/tools/micropython_probe.py` will use only conservative Python.

It will use:

- no dataclasses
- no typing
- no enum
- no pathlib
- no JSON
- no pytest
- no DD compatibility helpers
- no filesystem scanning
- no dynamic imports
- no MicroPython-specific production abstractions

The probe accepts the DD source directory as its only argument.

Example:

```powershell
<external>\micropython.exe root/tools/micropython_probe.py root/src
```

It emits deterministic machine-readable lines such as:

```text
MPY|BOOT|PASS
MPY|IMPLEMENTATION|micropython
MPY|VERSION|1.29.0
MPY|PLATFORM|win32
MPY|MEMORY|...
MPY|<STAGE>|BEGIN
MPY|<STAGE>|PASS
MPY|<STAGE>|FAIL|<ExceptionType>|<message>
```

The probe will not emit a MicroPython source SHA because that information belongs to the external provisioning checkout and cannot be reliably derived from `micropython.exe` alone.

Each stage will:

- emit `BEGIN`
- collect optional memory information
- execute exactly one operation
- emit `PASS` or `FAIL`
- re-raise failures after the structured failure line

Re-raising is required so the original MicroPython traceback and failing import or source line remain visible.

The probe must not swallow, normalize away, or silently continue past a failed stage.

## Memory Evidence

Where supported, the probe will use MicroPython's native garbage-collector information:

```python
gc.collect()
gc.mem_free()
gc.mem_alloc()
```

Memory evidence should be taken immediately around meaningful stages.

Where these APIs are unavailable, the probe emits:

```text
MPY|MEMORY|UNAVAILABLE
```

and continues.

Lack of heap-reporting APIs is not itself a failure of MPY0.

MPY0 memory measurements are diagnostic only. The Windows port is not being treated as representative of future PS5 or constrained-hardware memory limits.

Hardware-specific heap qualification remains deferred.

## Progressive Stages

The probe stops at the first failure in the active track.

MPY0 does not attempt to collect a complete list of theoretical incompatibilities in one run.

The first real observed incompatibility is sufficient evidence to close the raw-probe portion of MPY0 and derive the next gate.

### Core Track

```text
0. Boot and identify MicroPython
1. Add root/src to sys.path
2. Import app.content.catalog
3. Resolve Branoc's DrifterSpec
4. Call create_new_game("branoc")
5. Resolve the canonical first Goblin encounter
6. Construct canonical EnemyState instances
7. Construct Battle(..., ui=None) with deterministic RNG
8. Obtain the first BattleView
9. Submit existing semantic Battle inputs
10. Complete the first Battle
```

The canonical first encounter should be resolved through the existing content authorities rather than duplicated in the probe.

For the current surface route this is expected to resolve to:

```text
surface_goblin_solo
```

but the probe must use DD's existing catalog and construction paths rather than recreate authored encounter values.

The core track will use the real:

- content catalog
- DrifterSpec
- `create_new_game()`
- GameState
- PlayerState
- canonical encounter construction
- canonical EnemyState construction
- Battle
- BattlePresenter
- semantic Battle inputs
- CombatResolver
- combat lifecycle

The deterministic RNG used by the probe may control randomness only.

It must not:

- calculate damage
- determine winners
- bypass CombatResolver
- fake enemy behavior
- bypass Battle lifecycle
- alter rewards
- replace gameplay logic

The core track will not use:

- TerminalBattleUI
- TerminalOverworldUI
- `input()`
- terminal `print()` as gameplay control flow
- `Battle.run()`
- `OverworldSession.run()`

### Session Track

The session track begins only if the core track succeeds.

```text
11. Import OverworldSession
12. Construct a headless OverworldSession
13. Obtain session.current_view()
14. Enter the first encounter through session.submit()
15. Complete the first encounter through semantic inputs
16. Return to the overworld and verify reward/route state
17. Continue the route only when all prior stages succeed
```

The session track deliberately exposes the current concrete `SaveRepository` import closure without invoking save or load behavior and without intentionally writing a persistence file.

A failure involving:

- `pathlib`
- `tempfile`
- filesystem behavior
- `SaveRepository`
- another transitive persistence dependency

must be reported as a persistence-edge failure rather than misclassified as a core combat failure.

This stage separation is intentional.

For example:

```text
create_new_game()
PASS

Battle
PASS

BattleView
PASS

OverworldSession import
FAIL due to persistence dependency
```

would demonstrate a persistence compatibility edge while preserving evidence that the underlying game and combat runtime successfully execute.

MPY0 may eventually reach the complete surface route, but it is not required to do so.

Its primary success condition is a trustworthy first-failure report.

## Raw Probe Versus Compatibility Probe

MPY0 is a raw probe.

It asks:

```text
How far can untouched Dungeon Drifters execute under the pinned
MicroPython runtime before encountering the first real incompatibility?
```

It does not ask:

```text
How many compatibility problems can we repair in one pass?
```

Therefore MPY0 will not create:

```text
app.compat
```

or any equivalent permanent compatibility package.

Experimental shims are also outside the initial raw run.

Future gates may use disposable compatibility experiments to determine whether an observed incompatibility can be crossed safely, but those experiments must be derived from actual probe evidence.

No permanent compatibility abstraction is authorized by MPY0.

## Documentation

`docs/portability/micropython-probe.md` will document:

- MPY0 scope
- MPY0 non-goals
- pinned MicroPython version
- why the Windows port is used for the raw qualification
- external provisioning directory
- exact clone command
- exact `v1.29.0` checkout command
- exact source-SHA command
- exact clean-check command
- pinned Windows build instructions
- required Windows build prerequisites
- whether `mpy-cross` is actually required by the pinned build
- exact probe invocation command
- probe stage order
- output format
- memory measurement behavior
- external runtime evidence versus probe-emitted evidence
- raw probe versus future compatibility probe
- core-track versus session-track failures
- how to interpret import and runtime failures
- the rule that no production compatibility change is allowed without observed evidence
- later MPY1 through MPY6 gate boundaries
- hardware-specific heap qualification as deferred work

The guide will explicitly state that MPY0 does not create permanent compatibility architecture.

## Verification

Before commit:

```powershell
.\.venv\Scripts\python.exe -m compileall root/src root/tests root/tools
git diff --check
```

Provision and verify the external MicroPython runtime.

Record from the MicroPython checkout:

```powershell
git rev-parse HEAD
git status --porcelain
```

Verify the runtime version independently.

Run the probe under MicroPython:

```powershell
<external>\micropython.exe root/tools/micropython_probe.py root/src
```

Also run the probe once under CPython:

```powershell
.\.venv\Scripts\python.exe root/tools/micropython_probe.py root/src
```

The CPython run exists only to verify:

- harness syntax
- argument handling
- structured output
- stage ordering
- failure reporting
- ordinary DD reachability

CPython success is not MicroPython compatibility evidence.

Review the diff to confirm:

- only the two planned files changed
- no production imports changed
- no compatibility shim was added
- no runtime filesystem discovery was introduced
- no persistence behavior changed
- no gameplay behavior changed
- no MicroPython-specific conditionals entered DD runtime code
- no MicroPython binary or source checkout entered the repository

Commit exactly:

```text
MPY0 - Add Raw MicroPython Runtime Probe
```

Push `mpy`.

Verify:

```text
local HEAD == origin/mpy
```

Run the existing DD CI suite for the documentation/tooling change.

Stop after reporting:

- MicroPython tag
- resolved MicroPython source SHA
- source checkout cleanliness
- reported runtime version
- reported runtime platform
- exact probe output
- exact first-failure stage
- exception type
- exception message
- original traceback
- available memory evidence

## Acceptance Criteria

MPY0 is accepted when:

- MicroPython `v1.29.0` is provisioned reproducibly.
- The runtime was built from the pinned upstream `v1.29.0` source.
- The exact source commit SHA is recorded from the external Git checkout.
- The external source checkout is clean.
- The executing runtime reports the expected stable MicroPython version.
- The raw probe runs against untouched DD production source.
- The first incompatibility, if any, includes:
  - stage
  - exception type
  - exception message
  - original traceback
  - available memory state
- Core-track and session-track failures are distinguishable.
- The core combat path can be evaluated independently of the current persistence import edge.
- No production code changes exist.
- No compatibility layer exists.
- No speculative compatibility migration exists.
- The probe cannot silently continue past its first failure.
- No external MicroPython source or binaries are committed.
- The DD repository remains clean and synchronized after commit.

## Explicit Stop Rules

Stop MPY0 immediately when:

- the first DD incompatibility is identified
- runtime provisioning cannot produce the exact stable `v1.29.0` runtime
- the external source checkout cannot be tied to an exact clean commit
- the produced interpreter reports an unexpected version
- MSBuild prerequisites are unavailable and cannot be resolved without expanding the experiment into a substantial environment project
- provisioning itself becomes a larger engineering effort than the compatibility probe
- the probe becomes more complex than a conservative diagnostic harness
- the probe begins recreating DD gameplay behavior
- a proposed fix would require modifying production code before evidence exists

Do not attempt to solve the first incompatibility inside MPY0.

The next gate must be derived from the first observed failure.

No speculative:

- dataclass migration
- enum migration
- typing migration
- annotation migration
- persistence redesign
- content redesign
- presentation redesign

will be included in MPY0.

## Future Gate Direction

MPY0 determines the first real compatibility wall.

Later gates are expected to follow the evidence rather than a predetermined conversion list.

The current conceptual sequence is:

```text
MPY0
Raw MicroPython compatibility probe.
No production changes.
Find the first real incompatibility.

MPY1
First evidence-backed compatibility primitive or adaptation.
Advance the probe beyond the MPY0 failure.

MPY2
Core combat qualification.
Reach a real BattleView and complete the canonical first battle.

MPY3
Session qualification.
Drive the first encounter through OverworldSession.

MPY4
Surface-route qualification.
Complete all 8 encounters, 3 Rests, and reach Dungeon Entrance.

MPY5
Memory and runtime-pressure qualification.
Measure retained and peak memory behavior under an appropriate constrained target.

MPY6
Cross-runtime regression qualification.
Prove the resulting authoritative source remains correct under normal CPython
and remains suitable for Pyodide and Chaquopy qualification.
```

The governing rule across the entire effort is:

```text
No production compatibility change without an observed MicroPython failure
or a directly proven prerequisite of that failure.
```

MPY0 exists to produce that evidence.
```

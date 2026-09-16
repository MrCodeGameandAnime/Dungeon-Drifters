# MYP0: Raw MicroPython Runtime Probe

MYP0 qualifies the untouched Dungeon Drifters runtime against the upstream stable MicroPython `v1.29.0` Windows port. It is a diagnostic gate, not a compatibility migration.

## Scope

The probe answers one question:

```text
How far can the current DD source execute before the first real
MicroPython incompatibility?
```

MYP0 does not add `app.compat`, change production code, alter gameplay, redesign persistence, or add browser, Android, hardware, or board-specific support. The Windows port is used to qualify the language, import, and standard-library surface without making an MCU memory claim. Hardware-specific heap qualification is deferred.

The raw probe must run against the current DD source without experimental shims. No production compatibility change is allowed without an observed probe failure or a directly proven prerequisite of that failure.

## Pinned Runtime

Provision the upstream source outside the repository:

```text
%LOCALAPPDATA%\DungeonDrifters\micropython\v1.29.0\
├── source\
└── build\
```

Use the stable tag `v1.29.0` only. Do not use a preview, development, or dirty checkout.

From PowerShell:

```powershell
$runtime = "$env:LOCALAPPDATA\DungeonDrifters\micropython\v1.29.0"
New-Item -ItemType Directory -Force "$runtime" | Out-Null
git clone https://github.com/micropython/micropython.git "$runtime\source"
git -C "$runtime\source" fetch --tags
git -C "$runtime\source" checkout --detach v1.29.0
git -C "$runtime\source" rev-parse HEAD
git -C "$runtime\source" status --porcelain
```

The final Git command must produce no output. Record the full SHA from `rev-parse` as external runtime evidence:

```text
MicroPython tag: v1.29.0
Resolved source SHA: <full SHA from Git>
Source checkout: clean
```

Build the standard Windows port using the pinned source's documented MSBuild workflow. From the Windows port directory:

```powershell
Push-Location "$runtime\source\ports\windows"
msbuild ..\..\mpy-cross\mpy-cross.vcxproj
msbuild micropython.vcxproj
Pop-Location
```

Build `mpy-cross` only if the pinned Windows build requires it. MYP0 does not add that build as an independent requirement. The resulting standard runtime is normally under:

```text
<source>\ports\windows\build-standard\ReleaseWin32\micropython.exe
```

Verify the executable independently before probing DD:

```powershell
& "$runtime\source\ports\windows\build-standard\ReleaseWin32\micropython.exe" -c "import sys; print(sys.implementation.name); print(sys.implementation.version)"
```

It must report MicroPython `1.29.0`. The official MicroPython documentation notes that the Windows port can be built with MSBuild and that the port has its own build requirements. [Windows port instructions](https://github.com/micropython/micropython/blob/v1.29.0/ports/windows/README.md)

## Invocation

Run from the repository directory:

```powershell
& "$runtime\source\ports\windows\build-standard\ReleaseWin32\micropython.exe" `
  root/tools/micropython_probe.py `
  root/src
```

The probe accepts exactly one argument: the DD source directory. It does not scan the filesystem or dynamically discover modules.

For harness validation only, run the same script once under CPython:

```powershell
.\.venv\Scripts\python.exe root/tools/micropython_probe.py root/src
```

CPython success confirms argument handling, stage ordering, and structured reporting. It is not MicroPython compatibility evidence.

## Evidence Format

The probe reports interpreter facts directly:

```text
MYP|BOOT|PASS
MYP|IMPLEMENTATION|micropython
MYP|VERSION|1.29.0
MYP|PLATFORM|win32
MYP|<STAGE>|BEGIN
MYP|MEMORY|<STAGE>|BEFORE|FREE|...|ALLOC|...
MYP|<STAGE>|PASS
```

If an optional garbage-collector measurement is unavailable, it reports:

```text
MYP|MEMORY|UNAVAILABLE
```

The probe does not emit the MicroPython source SHA. Git in the external provisioning checkout is the authority for that value.

On the first failure it emits:

```text
MYP|<STAGE>|FAIL|<ExceptionType>|<message>
```

and then re-raises the exception. The original MicroPython traceback, import path, and source line must remain visible. The probe never normalizes away an exception or continues to a later stage after failure.

## Stage Order

The core track isolates the game and combat runtime from persistence:

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
```

It uses the existing catalog, `DrifterSpec`, `create_new_game()`, `GameState`, `PlayerState`, canonical enemy factories, `Battle`, `BattlePresenter`, semantic Battle inputs, and the real `CombatResolver`. The deterministic RNG controls randomness only.

It does not use `TerminalBattleUI`, `TerminalOverworldUI`, `input()`, terminal control flow, `Battle.run()`, or `OverworldSession.run()`.

The session track begins only after the core track succeeds:

```text
SESSION_IMPORT
SESSION_CONSTRUCTION
SESSION_VIEW
SESSION_ENCOUNTER_ENTRY
SESSION_ENCOUNTER_COMPLETE
```

`OverworldSession` currently imports a concrete `SaveRepository`. A failure involving `pathlib`, `tempfile`, filesystem behavior, or another persistence dependency is reported as a session/persistence-edge failure. It must not be mistaken for evidence that the core game or combat path failed.

MYP0 may be extended in a later run to qualify the full surface route, but reaching Dungeon Entrance is not required to identify the first raw incompatibility. Full-route qualification belongs to a later gate after evidence-backed compatibility work.

## Raw Versus Compatibility Probe

MYP0 is intentionally raw:

```text
untouched DD source
-> pinned MicroPython runtime
-> first observed failure
```

Do not add a compatibility package, alter annotations, replace dataclasses, add enum shims, or change persistence in this gate. A future compatibility experiment must be disposable and derived from the exact failure recorded here.

## MYP1 Evidence

MYP0's first failure was the direct `types.MappingProxyType` import in:

```text
root/src/app/content/catalog.py
```

The complete production audit found the same dependency in `root/src/app/content/weapon_spec.py`. DD uses these mappings for catalog lookup and immutable authored weapon bonuses. The observed read contract is lookup, membership, iteration, length, `keys()`, and `items()`; DD does not mutate a backing dictionary after wrapping, and does not require live reflection, proxy identity, hashing, or pickling.

MYP1 replaces those direct construction sites with:

```text
app.readonly_mapping.readonly_mapping(source)
```

CPython continues to use native `types.MappingProxyType`. When that module is unavailable, the helper uses a private `_ReadonlyMapping` around a copied dictionary. The fallback exposes only the required read operations and has no inherited dictionary mutation API.

The unchanged probe under the pinned MicroPython runtime produced this MYP1 result:

```text
MYP|BOOT|PASS
MYP|IMPLEMENTATION|micropython
MYP|VERSION|1.29.0
MYP|PLATFORM|win32
MYP|MEMORY|BOOT|FREE|1015472|ALLOC|9040
MYP|SOURCE_PATH|BEGIN
MYP|MEMORY|SOURCE_PATH|BEFORE|FREE|1015424|ALLOC|9088
MYP|MEMORY|SOURCE_PATH|AFTER|FREE|1015408|ALLOC|9104
MYP|SOURCE_PATH|PASS
MYP|CATALOG_IMPORT|BEGIN
MYP|MEMORY|CATALOG_IMPORT|BEFORE|FREE|1015408|ALLOC|9104
MYP|CATALOG_IMPORT|FAIL|ImportError|no module named 'dataclasses'
MYP|MEMORY|CATALOG_IMPORT|FAIL|FREE|1004688|ALLOC|19824
```

The original traceback is:

```text
root/tools/micropython_probe.py, line 262, in <module>
root/tools/micropython_probe.py, line 244, in main
root/tools/micropython_probe.py, line 25, in _run_stage
root/tools/micropython_probe.py, line 59, in _import_catalog
root/src/app/content/catalog.py, line 3, in <module>
root/src/app/content/_generated_catalog.py, line 3, in <module>
root/src/app/content/enemies/goblin/__init__.py, line 1, in <module>
root/src/app/content/enemies/goblin/enemy.py, line 1, in <module>
root/src/app/combat/move.py, line 3, in <module>
ImportError: no module named 'dataclasses'
```

MYP1 therefore crossed the observed `types` incompatibility and stopped at the next real incompatibility. `CATALOG_IMPORT` remains incomplete because the next failure occurs during its transitive imports. Dataclasses are intentionally deferred to the next evidence-driven gate.

MicroPython runtime evidence remains:

```text
MicroPython tag: v1.29.0
MicroPython source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Source checkout: clean
Runtime: MicroPython 1.29.0
Platform: win32
```

## Future Gates

```text
MYP0  Raw probe; find the first real incompatibility.
MYP1  First evidence-backed compatibility primitive.
MYP2  Core combat qualification.
MYP3  Session qualification.
MYP4  Eight encounters, three Rests, Dungeon Entrance.
MYP5  Constrained-target memory and runtime pressure.
MYP6  Cross-runtime regression qualification.
```

Hardware-specific heap results remain separate from the Windows-port language/import qualification.

## Repository Verification

Before committing the probe and guide:

```powershell
.\.venv\Scripts\python.exe -m compileall root/src root/tests root/tools
git diff --check
```

Review that only these files changed:

```text
root/tools/micropython_probe.py
docs/portability/micropython-probe.md
```

The MYP0 commit must not contain DD production changes, compatibility scaffolding, save behavior, gameplay changes, downloaded MicroPython sources, binaries, object files, or build output.

Commit exactly:

```text
MYP0 - Add Raw MicroPython Runtime Probe
```

Push `myp`, verify the local and remote commit match, run the existing DD CI suite, and stop with the exact external runtime evidence and first-failure output.

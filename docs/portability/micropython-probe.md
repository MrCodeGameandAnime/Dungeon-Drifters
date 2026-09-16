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

## MYP2 Evidence

MYP2 qualifies the dataclass behavior that Dungeon Drifters actually uses. It does not install a compatibility implementation, change production imports, or advance the raw MicroPython probe. The unchanged probe remains expected to stop at the first missing `dataclasses` import.

### Production audit

The production audit covers every Python file under `root/src/app`:

```text
Production files using dataclasses: 23
Production dataclass declarations: 74
Frozen declarations: 71
Mutable declarations: 3
__post_init__ methods: 58
field() calls: 1
default_factory calls: 1
Dataclass inheritance: none
Dataclass ordering: none
unsafe_hash: none
slots: none
InitVar: none
field metadata: none
General dataclass reflection helpers: none
Observed __dataclass_fields__ users: 2
```

The complete declaration ledger is grouped below by production file. Every declaration uses either bare `@dataclass` or `@dataclass(frozen=True)`; no other decorator options are present.

| Production file | Dataclass declarations | Variant and role |
| --- | --- | --- |
| `combat/arcane.py` | `GravemantleRules`, `ArcaneDischarge` | frozen; authored rules and mechanical result |
| `combat/brace.py` | `BraceRules` | frozen; authored mechanic rules with defaults |
| `combat/combat_state.py` | `_BraceState`, `_HealCooldown`, `_ArcaneChargeState` | mutable; private encounter-local runtime records |
| `combat/frost.py` | `FrostRules` | frozen; authored mechanic rules with defaults |
| `combat/move_presentation.py` | `MovePresentation` | frozen; authored presentation metadata |
| `combat/move.py` | `Move` | frozen; authored move value object with defaults and post-init validation |
| `combat/result.py` | `CombatOutcome`, `MoveResult` | frozen; internal immutable combat results with defaults and post-init validation |
| `combat/status_state.py` | `BurnStatus`, `PoisonStatus`, `ConductiveStatus`, `TurbulenceStatus`, `StunStatus`, `FrostCharge`, `FrozenStatus`, `FrostbiteStatus` | frozen; encounter-local status values, including post-init validation where required |
| `combat/storm.py` | `StormRules` | frozen; authored mechanic rules |
| `content/drifter_spec.py` | `DrifterStatSpec`, `ClassMechanicSpec`, `DrifterSpec` | frozen; authored Drifter specifications, defaults, validation, and name-only metadata iteration |
| `content/encounter_spec.py` | `EncounterSpec` | frozen; authored encounter specification |
| `content/enemy_spec.py` | `StatBlockSpec`, `EnemySpec` | frozen; authored enemy specifications, defaults, validation, and name-only metadata iteration |
| `content/route_spec.py` | `RouteNodeSpec`, `RouteSpec` | frozen; authored route specifications with post-init validation |
| `content/weapon_spec.py` | `WeaponSpec` | frozen; authored weapon specification with post-init validation |
| `game/save_repository.py` | `SaveLoadResult` | frozen; immutable persistence operation result |
| `player/character_run_state.py` | `CharacterRunCheckpoint` | frozen; immutable run-state checkpoint |
| `player/inventory_action.py` | `InventoryActionResult` | frozen; immutable inventory result with defaults and post-init validation |
| `player/player_state.py` | `PlayerBattleCheckpoint` | frozen; immutable battle checkpoint |
| `player/run_items.py` | `RunItemDefinition`, `InventoryRecipeDefinition` | frozen; authored run-item and recipe definitions with post-init validation |
| `presentation/battle_models.py` | `CombatantView`, `EnemyCombatantView`, `ActionOptionView`, `MoveOptionView`, `TargetOptionView`, `InventoryItemOptionView`, `InventoryCommandOptionView`, `InventoryInspectionView`, `InventoryConfirmationView`, `SuperMeterView`, `BattleLogEntry`, `BattleVisualView`, `BattleView` | frozen; immutable frontend-facing views; `BattleView.visual` uses the only default factory |
| `presentation/overworld_models.py` | `OverworldOptionView`, `StatRowView`, `CharacterOverviewView`, `SkillMoveView`, `SkillsView`, `StatBonusView`, `WeaponView`, `AccessorySlotView`, `EquipmentView`, `OverworldItemView`, `InventoryView`, `MapNodeView`, `MapView`, `MapEncounterInspectionView`, `OverworldView` | frozen; immutable frontend-facing views |
| `ui/battle_ui.py` | `ChooseAction`, `ChooseMove`, `ChooseTarget`, `ChooseInventoryItem`, `ChooseInventoryCommand`, `ChooseInventoryCompanion`, `ConfirmInventoryUse`, `GoBack` | frozen; semantic battle inputs |
| `ui/overworld_ui.py` | `ChooseOverworldAction`, `ChooseOverworldItem`, `ChoosePermanentStatIncrease` | frozen; semantic overworld inputs |

`DrifterStatSpec.__post_init__` and `DrifterStatSpec.as_dict()` iterate `self.__dataclass_fields__` as an ordered collection of field names. `StatBlockSpec.__post_init__` uses the same name-only pattern. Neither class reads `Field` attributes, metadata, defaults, or dataclass parameters.

### Feature ledger

The required portable contract is:

```text
Required:
- generated __init__
- positional and keyword field ordering
- ordinary field defaults
- field(default_factory=...)
- per-instance default-factory isolation
- attribute storage
- structural equality
- frozen attribute-assignment rejection
- __post_init__ invocation
- object.__setattr__ during frozen post-init normalization
- __dataclass_fields__ behavior exactly sufficient for the observed
  DrifterStatSpec and StatBlockSpec access pattern:
  iterable declaration-ordered field names only
- tuple, mapping, enum, optional, and nested-record values
```

The following are explicitly not required by current DD production behavior:

```text
- ordering
- unsafe_hash
- dataclass hashing
- slots
- kw_only
- InitVar
- field metadata
- asdict
- astuple
- fields()
- replace()
- is_dataclass()
- make_dataclass()
- MISSING
- KW_ONLY
- dataclass inheritance
- live reflection beyond the observed field-name iteration
- exact generated repr compatibility
```

Hashability, ordering, repr, and other incidental CPython behavior are not asserted as absent. They are documented as unnecessary only when static production inspection proves DD does not depend on them.

The 58 post-init methods are behaviorally important because they perform enum normalization, validation, derived checks, and frozen writes through `object.__setattr__`. Mutable nested values remain owned by the existing runtime classes; frozen dataclasses provide shallow attribute protection, not deep immutability.

### Persistence and annotations

Save schema 8 does not depend on dataclass metadata. `save_state.py` validates explicit dictionary shapes, builds explicit payloads, and reconstructs objects through canonical constructors. It does not call `asdict()`, `fields()`, `replace()`, or inspect dataclass parameters. Dataclass equality is not a gameplay dispatch authority; persistence and route logic compare explicit identifiers and values.

Annotations are needed by the native decorator to discover fields, but DD does not inspect `__annotations__` or evaluate type hints at runtime. PEP 604 annotations appear in production and remain a separate future MicroPython syntax/annotation concern. MYP2 does not migrate them.

### Strategy decision

The qualified result is:

```text
D2 - Moderate compatibility subset
Risk: MODERATE
```

| Strategy | Assessment |
| --- | --- |
| Import overlay | Recommended. Keeps the 23 production imports unchanged and lets CPython, Pyodide, and Chaquopy retain native dataclasses. MicroPython-specific bootstrap must inject the overlay path explicitly. |
| DD compatibility import | Viable but would touch the broad production import surface and permanently make every model aware of an internal compatibility boundary. |
| Build/source transform | Avoids runtime imports but adds a second source representation and debugging/build complexity. |
| Manual records | Unjustified for the qualified subset; would rewrite 74 models and risk behavior drift. |
| Third-party implementation | Not selected during MYP2 because no dependency is pinned or required by the audit. |

An eventual overlay must live outside the normal `root/src` import path and be selected only by a MicroPython-specific launcher or bootstrap. A local `dataclasses.py` must never shadow the CPython standard library during tests, packaging, Pyodide, or Chaquopy execution.

The estimated later implementation is one portable compatibility module plus one MicroPython-only path/bootstrap integration, with zero expected engine production-file changes. The semantic runtime API, save schema, gameplay ownership, and one authoritative implementation can remain unchanged.

### MYP2 conformance result

The implementation-neutral conformance suite is `root/tests/test_dataclass_contract.py`. It locks construction, defaults, default-factory isolation, equality, frozen assignment rejection, post-init normalization, validation, nested values, and the exact ordered-name metadata seam. It does not assert that incidental CPython methods are absent.

The raw probe remains unchanged. Under the pinned runtime it is expected to report:

```text
MYP|CATALOG_IMPORT|BEGIN
MYP|CATALOG_IMPORT|FAIL|ImportError|no module named 'dataclasses'
```

MYP2 therefore qualifies the next implementation boundary without implementing it. The next gate may proceed only with the strict contract above; it must not broaden into annotation, enum, typing, persistence, or gameplay migration.

## DD PORTABLE DATACLASS VERDICT

Production files using dataclasses: 23

Production dataclass declarations: 74

Required features: generated initialization, defaults, one default factory, structural equality, frozen assignment rejection, post-init normalization, and ordered-name `__dataclass_fields__` access

Features not required: ordering, hashing, slots, keyword-only fields, InitVar, metadata, general reflection helpers, inheritance, live reflection, and exact repr compatibility

Frozen semantics required: YES

Structural equality required: YES

default_factory required: YES

__post_init__ required: YES

Dataclass inheritance complexity: NONE

Runtime reflection required: LIMITED

Persistence depends on dataclass metadata: NO

Annotations materially affect implementation: LIMITED

Recommended portability strategy: IMPORT OVERLAY

Estimated production blast radius: 0-2 non-engine integration files; no gameplay-model rewrites

Estimated implementation complexity: MODERATE

Normal CPython can retain native dataclasses: YES

Pyodide can retain native dataclasses: YES

Chaquopy can retain native dataclasses: YES

Semantic runtime API can remain unchanged: YES

Gameplay architecture changes required: NO

One authoritative gameplay implementation remains practical: YES WITH STRICT COMPATIBILITY BOUNDARY

Recommendation: PROCEED WITH STRICT BOUNDARY

## Future Gates

```text
MYP0  Raw probe; find the first real incompatibility.
MYP1  First evidence-backed compatibility primitive.
MYP2  Qualify the portable dataclass contract.
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

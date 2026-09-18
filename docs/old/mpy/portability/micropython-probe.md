# MPY0: Raw MicroPython Runtime Probe

MPY0 qualifies the untouched Dungeon Drifters runtime against the upstream stable MicroPython `v1.29.0` Windows port. It is a diagnostic gate, not a compatibility migration.

## Scope

The probe answers one question:

```text
How far can the current DD source execute before the first real
MicroPython incompatibility?
```

MPY0 does not add `app.compat`, change production code, alter gameplay, redesign persistence, or add browser, Android, hardware, or board-specific support. The Windows port is used to qualify the language, import, and standard-library surface without making an MCU memory claim. Hardware-specific heap qualification is deferred.

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

Build `mpy-cross` only if the pinned Windows build requires it. MPY0 does not add that build as an independent requirement. The resulting standard runtime is normally under:

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
MPY|BOOT|PASS
MPY|IMPLEMENTATION|micropython
MPY|VERSION|1.29.0
MPY|PLATFORM|win32
MPY|<STAGE>|BEGIN
MPY|MEMORY|<STAGE>|BEFORE|FREE|...|ALLOC|...
MPY|<STAGE>|PASS
```

If an optional garbage-collector measurement is unavailable, it reports:

```text
MPY|MEMORY|UNAVAILABLE
```

The probe does not emit the MicroPython source SHA. Git in the external provisioning checkout is the authority for that value.

On the first failure it emits:

```text
MPY|<STAGE>|FAIL|<ExceptionType>|<message>
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

MPY0 may be extended in a later run to qualify the full surface route, but reaching Dungeon Entrance is not required to identify the first raw incompatibility. Full-route qualification belongs to a later gate after evidence-backed compatibility work.

## Raw Versus Compatibility Probe

MPY0 is intentionally raw:

```text
untouched DD source
-> pinned MicroPython runtime
-> first observed failure
```

Do not add a compatibility package, alter annotations, replace dataclasses, add enum shims, or change persistence in this gate. A future compatibility experiment must be disposable and derived from the exact failure recorded here.

## MPY1 Evidence

MPY0's first failure was the direct `types.MappingProxyType` import in:

```text
root/src/app/content/catalog.py
```

The complete production audit found the same dependency in `root/src/app/content/weapon_spec.py`. DD uses these mappings for catalog lookup and immutable authored weapon bonuses. The observed read contract is lookup, membership, iteration, length, `keys()`, and `items()`; DD does not mutate a backing dictionary after wrapping, and does not require live reflection, proxy identity, hashing, or pickling.

MPY1 replaces those direct construction sites with:

```text
app.readonly_mapping.readonly_mapping(source)
```

CPython continues to use native `types.MappingProxyType`. When that module is unavailable, the helper uses a private `_ReadonlyMapping` around a copied dictionary. The fallback exposes only the required read operations and has no inherited dictionary mutation API.

The unchanged probe under the pinned MicroPython runtime produced this MPY1 result:

```text
MPY|BOOT|PASS
MPY|IMPLEMENTATION|micropython
MPY|VERSION|1.29.0
MPY|PLATFORM|win32
MPY|MEMORY|BOOT|FREE|1015472|ALLOC|9040
MPY|SOURCE_PATH|BEGIN
MPY|MEMORY|SOURCE_PATH|BEFORE|FREE|1015424|ALLOC|9088
MPY|MEMORY|SOURCE_PATH|AFTER|FREE|1015408|ALLOC|9104
MPY|SOURCE_PATH|PASS
MPY|CATALOG_IMPORT|BEGIN
MPY|MEMORY|CATALOG_IMPORT|BEFORE|FREE|1015408|ALLOC|9104
MPY|CATALOG_IMPORT|FAIL|ImportError|no module named 'dataclasses'
MPY|MEMORY|CATALOG_IMPORT|FAIL|FREE|1004688|ALLOC|19824
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

MPY1 therefore crossed the observed `types` incompatibility and stopped at the next real incompatibility. `CATALOG_IMPORT` remains incomplete because the next failure occurs during its transitive imports. Dataclasses are intentionally deferred to the next evidence-driven gate.

MicroPython runtime evidence remains:

```text
MicroPython tag: v1.29.0
MicroPython source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Source checkout: clean
Runtime: MicroPython 1.29.0
Platform: win32
```

## MPY2 Evidence

MPY2 qualifies the dataclass behavior that Dungeon Drifters actually uses. It does not install a compatibility implementation, change production imports, or advance the raw MicroPython probe. The unchanged probe remains expected to stop at the first missing `dataclasses` import.

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

Annotations are needed by the native decorator to discover fields, but DD does not inspect `__annotations__` or evaluate type hints at runtime. PEP 604 annotations appear in production and remain a separate future MicroPython syntax/annotation concern. MPY2 does not migrate them.

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
| Third-party implementation | Not selected during MPY2 because no dependency is pinned or required by the audit. |

An eventual overlay must live outside the normal `root/src` import path and be selected only by a MicroPython-specific launcher or bootstrap. A local `dataclasses.py` must never shadow the CPython standard library during tests, packaging, Pyodide, or Chaquopy execution.

The estimated later implementation is one portable compatibility module plus one MicroPython-only path/bootstrap integration, with zero expected engine production-file changes. The semantic runtime API, save schema, gameplay ownership, and one authoritative implementation can remain unchanged.

### MPY2 conformance result

The implementation-neutral conformance suite is `root/tests/test_dataclass_contract.py`. It locks construction, defaults, default-factory isolation, equality, frozen assignment rejection, post-init normalization, validation, nested values, and the exact ordered-name metadata seam. It does not assert that incidental CPython methods are absent.

The raw probe remains unchanged. Under the pinned runtime it is expected to report:

```text
MPY|CATALOG_IMPORT|BEGIN
MPY|CATALOG_IMPORT|FAIL|ImportError|no module named 'dataclasses'
```

MPY2 therefore qualifies the next implementation boundary without implementing it. The next gate may proceed only with the strict contract above; it must not broaden into annotation, enum, typing, persistence, or gameplay migration.

## MPY3 - Portable dataclass field discovery and overlay

MPY3 continued after the stock annotation discovery failure instead of treating it as evidence that portable dataclass behavior was impossible. The pinned runtime preserves class identity but does not preserve class annotations:

```text
MicroPython: 1.29.0
Platform: win32

class Example:
    required: int
    optional: str = "default"

Example.__dict__:
    optional is present
    required is absent

Example.__annotations__:
    AttributeError / unavailable
```

The runtime does preserve the identity required for generated metadata:

```text
__module__: preserved
__name__: preserved
__qualname__: preserved for DD's top-level dataclasses
```

### Field-discovery decision

The discovery ladder was evaluated in this order:

```text
1. annotation-retaining MicroPython configuration or build option
2. minimal MicroPython compiler/runtime patch
3. generated field metadata
4. explicit production field metadata
```

The pinned source exposes no existing annotation-preservation option. A broad interpreter fork or production rewrite was not justified. MPY3 therefore selected generated metadata while preserving every DD production dataclass unchanged.

The generator is `root/tools/generate_dataclass_manifest.py`. It imports the authoritative production modules under normal CPython and reads native `__dataclass_fields__` metadata. It fails closed for duplicate identities and terminal-input imports; current dataclass-bearing imports require no application startup, terminal interaction, persistence activity, or filesystem mutation. AST extraction remains the documented fallback if a future production addition makes native imports unsuitable.

The generated artifact is `root/portability/micropython/_dataclass_fields.py`. Its canonical identity is:

```text
(module, qualified class name)
```

The generated set is checked dynamically at generation time:

```text
discovered production dataclasses == generated manifest entries
0 missing
0 unexpected
0 duplicates
exact native field-order match
```

The MPY2 count of 74 is historical evidence, not a permanent limit. Every portable dataclass must resolve exactly one manifest key. There is no bare-name fallback, ambiguous matching, or silent missing metadata.

The manifest contains only ordered field names. Ordinary defaults remain on the class, and `field(default_factory=...)` remains represented by the overlay field marker. It is compatibility metadata, not a second gameplay representation.

### Portable overlay

The MicroPython-only implementation is `root/portability/micropython/dataclasses.py`. It implements only the MPY2-qualified subset:

```text
generated positional and keyword initialization
ordinary defaults
field(default_factory=...)
per-instance factory isolation
structural equality
frozen assignment rejection
__post_init__ invocation
object.__setattr__ normalization
ordered iterable __dataclass_fields__ names
```

It does not implement ordering, hashing compatibility, slots, keyword-only fields, `InitVar`, field metadata, general reflection, inheritance, or exact generated repr behavior.

`root/tools/micropython_probe_bootstrap.py` selects the overlay by prepending `root/portability/micropython` only for the isolated probe process. The normal CPython path, Pyodide, Chaquopy, pytest, and packaging continue to use native standard-library `dataclasses`. The unchanged raw probe remains the stage authority.

### MPY3 evidence

Portable conformance under CPython:

```text
13 passed
```

Direct overlay smoke test under MicroPython:

```text
MPY|OVERLAY|FIELDS|('value', 'items')
MPY|OVERLAY|FACTORY_ISOLATED|True
MPY|OVERLAY|POST_SETATTR|5
MPY|OVERLAY|FROZEN|TypeError
MPY|OVERLAY|PASS
```

Native CPython raw probe:

```text
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

Forced-overlay CPython raw probe:

```text
MPY|CATALOG_IMPORT|PASS
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

Pinned MicroPython raw probe:

```text
MPY|BOOT|PASS
MPY|IMPLEMENTATION|micropython
MPY|VERSION|1.29.0
MPY|PLATFORM|win32
MPY|CATALOG_IMPORT|BEGIN
MPY|CATALOG_IMPORT|FAIL|ImportError|no module named 'enum'
MPY|MEMORY|CATALOG_IMPORT|FAIL|FREE|978336|ALLOC|46176
```

The previous `ImportError: no module named 'dataclasses'` failure was crossed. The next compatibility frontier is the unrelated `enum` import in `root/src/app/combat/move.py`. MPY3 stops there; it does not repair enum, typing, collections, pathlib, persistence, annotations, or gameplay.

MPY3 production impact:

```text
production dataclass imports changed: 0
gameplay changes: 0
content changes: 0
persistence changes: 0
semantic API changes: 0
```

The external MicroPython evidence remains:

```text
MicroPython tag: v1.29.0
Resolved source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Source checkout: clean
```

MPY3 establishes that the dataclass contract is portable when field identity is supplied separately. It does not claim that the full DD runtime is yet MicroPython-compatible.

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

## MPY4 - Portable StrEnum overlay

MPY4 advances the raw MicroPython qualification past the `enum` import wall. It preserves the authoritative DD source and adds no production changes under `root/src`.

### Enum audit

The production enum surface was discovered dynamically from `root/src/app`, rather than from a fixed count. The historical MPY4 baseline is 14 importing files and 34 direct `StrEnum` declarations. Every declaration derives directly from `StrEnum` and uses uppercase names assigned literal string values.

The current declaration surface is:

| Production module | Direct `StrEnum` declarations |
| --- | --- |
| `app.combat.move` | `MoveKind`, `ResourceType`, `ScalingAttribute`, `TargetType`, `DamageType` |
| `app.combat.move_presentation` | `MoveRole` |
| `app.combat.result` | `CombatOutcomeType`, `CombatOutcomeTarget` |
| `app.combat.status_state` | `StatusKind` |
| `app.enemies.definition` | `EnemyRank`, `EnemyRole`, `EnemyBehavior`, `EnemyCapability` |
| `app.presentation.battle_models` | `ActionIntent`, `InteractionPhase`, `InputRejectionReason`, `BattleEventType`, `ActionAvailabilityReason`, `MoveAvailabilityReason`, `InventoryAvailabilityReason` |
| `app.presentation.overworld_models` | `OverworldScreen`, `OverworldAction`, `OverworldAvailabilityReason`, `MapNodeState` |
| `app.player.character_run_state` | `RunItemId`, `PreparedPayloadId`, `InfusionKind`, `InventoryActionId` |
| `app.player.run_items` | `InventoryCommand` |
| `app.player.inventory_action` | `InventoryActionRejectionReason` |
| `app.content.route_spec` | `RouteNodeKind` |
| `app.game.overworld_state` | `ContextualRoutePhase` |
| `app.game.overworld_session` | `OverworldSessionResult` |
| `app.game.save_repository` | `SaveLoadStatus` |

The audit verifies dynamically that:

```text
all production enum bases are direct StrEnum bases
all candidate member names are uppercase public names
all candidate member values are literal strings
there are no aliases
there is no enum inheritance
there are no custom enum methods
there are no unsupported enum operations in production
```

DD requires direct member access, `EnumType(value)` lookup, canonical singleton identity, `.name`, `.value`, `isinstance(member, EnumType)`, identity/equality comparisons, string compatibility, and hashing for dictionary and set use. In particular, `RunItemId` is used as a dictionary key and `EnemyCapability` is used in a `frozenset`.

DD does not require enum iteration, `len(EnumType)`, `EnumType["NAME"]`, pickling, enum reflection, ordering, or CPython-specific repr behavior. Hash behavior may exist because string-backed members are hashable; the portable requirement is that DD's dictionary and set operations continue to work, not that incidental CPython enum internals be reproduced.

### MicroPython evidence and mechanism

The pinned MicroPython `v1.29.0` runtime preserves `__module__`, `__name__`, and `__qualname__` for the top-level DD enum classes. It does not provide a useful `__init_subclass__` interception point. A class statement with `metaclass=` is rejected, and `str.__new__` is unavailable as a directly callable construction primitive. `builtins.__build_class__` is available and can be wrapped.

The selected implementation is the narrow `root/portability/micropython/enum.py` overlay. It exports only `StrEnum` and captures the original `builtins.__build_class__` once. The wrapper is installed when the overlay imports, before DD enum declarations execute. It transforms only classes whose sole base is the overlay's `StrEnum`; every unrelated class delegates to the original builder unchanged.

Member creation and later lookup are deliberately separate:

```text
class X(StrEnum):
    VALUE = "value"

original __build_class__ creates the ordinary subclass
hook recognizes the direct StrEnum subclass
raw supported string-subclass construction creates canonical members
member names and values are exposed
lookup registry is installed

later X("value")
    -> existing X.VALUE singleton
```

The raw construction path uses the demonstrated MicroPython string-subclass behavior and does not assume a usable `str.__new__`. Unknown values raise `ValueError`; duplicate values and malformed uppercase candidate members fail loudly. Dunder names, helper methods, and arbitrary non-member attributes are ignored unless they are qualified as candidate members.

The overlay preserves string equality, `str(member)`, hash behavior, dictionary/set use, `.name`, `.value`, canonical identity, and `isinstance`. It is not a general metaclass system, enum inheritance framework, source transformer, or replacement for Python's complete enum module.

Hook safety is locked by subprocess-based forced-overlay tests. The original builder is captured exactly once, forced qualification proves the overlay module is active instead of using cached CPython `enum`, and unrelated classes and native dataclasses remain unaffected. Test-local hooks are isolated and restored in `finally` where installed. The CPython bootstrap preloads host standard-library modules that depend on native enum behavior before replacing the cached `enum` module; this is qualification harness setup and is not a normal CPython runtime change.

### Dataclass census

The MPY3 overlay now records unique identities rather than construction totals:

```text
EXPECTED    = set(FIELD_MANIFEST)
DECORATED   = set()
CONSTRUCTED = set()
```

`DECORATED` receives a class identity only after decoration completes successfully. `CONSTRUCTED` receives it only after field assignment and `__post_init__` complete successfully. Counts are emitted from those sets, so repeated instances of one class cannot masquerade as coverage of multiple classes. `EXPECTED` is derived dynamically from the generated manifest; the historical count of 74 is not a permanent requirement.

The bootstrap emits census diagnostics from a `finally` path without changing the raw probe or masking its original exception. If census access is unavailable it emits an explicit diagnostic-unavailable line.

### MPY4 evidence

Native CPython raw probe:

```text
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

Forced-overlay CPython raw probe:

```text
MPY|CATALOG_IMPORT|PASS
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|74
MPY|DATACLASS|CONSTRUCTED|33
```

Direct portable enum smoke test under the pinned runtime:

```text
MPY|ENUM|MICROPYTHON|PASS
```

Pinned MicroPython `v1.29.0` raw probe after the enum wall was crossed:

```text
MPY|BOOT|PASS
MPY|IMPLEMENTATION|micropython
MPY|VERSION|1.29.0
MPY|PLATFORM|win32
MPY|MEMORY|BOOT|FREE|1003456|ALLOC|21056
MPY|SOURCE_PATH|BEGIN
MPY|SOURCE_PATH|PASS
MPY|CATALOG_IMPORT|BEGIN
MPY|CATALOG_IMPORT|FAIL|ImportError|no module named 'keyword'
MPY|MEMORY|CATALOG_IMPORT|FAIL|FREE|967856|ALLOC|56656
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|2
MPY|DATACLASS|CONSTRUCTED|0
```

The original `ImportError: no module named 'dataclasses'` wall was crossed by MPY3, and the `ImportError: no module named 'enum'` wall was crossed by MPY4. The next observed incompatibility is the unrelated `keyword` import from `root/src/app/content/enemy_spec.py`. MPY4 stops there. It does not repair `keyword`, typing, collections, pathlib, persistence, annotations, or gameplay.

The external runtime evidence remains:

```text
MicroPython tag: v1.29.0
Resolved source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Source checkout: clean
Reported platform: win32
```

MPY4 production impact is:

```text
root/src production files changed: 0
gameplay changes: 0
content changes: 0
persistence changes: 0
semantic API changes: 0
```

The overlay is a MicroPython-only portability boundary. Native CPython, Pyodide, Chaquopy, pytest, and packaging continue using the standard-library `enum`. MPY4 establishes that DD's qualified StrEnum behavior is portable through the observed enum wall without claiming that the full DD runtime is yet MicroPython-compatible.

## MPY5 - Portable keyword boundary

MPY5 advances the raw MicroPython qualification past the observed `keyword` import failure while preserving DD production source, gameplay, content, persistence, semantic APIs, and the unchanged raw probe.

MPY4 was sealed at:

```text
0a9677d58f80e90f80d50e6ac885a43c4279878e
MPY4 - Add Portable StrEnum Overlay
```

The starting MPY4 evidence was:

```text
CATALOG_IMPORT
ImportError: no module named 'keyword'
root/src/app/content/enemy_spec.py
FREE 967856
ALLOC 56656
DATACLASS EXPECTED 74
DATACLASS DECORATED 2
DATACLASS CONSTRUCTED 0
```

### Production keyword audit

The runtime dependency was discovered dynamically under `root/src/app`. Current production callers are:

```text
app.content.enemy_spec
app.content.drifter_spec
app.content.route_spec
app.items.weapon
```

Every runtime call is exactly:

```python
keyword.iskeyword(value)
```

The audit does not include `root/tools`; tooling has its own source-analysis variables named `keyword` but does not expand the runtime module contract. DD production does not require `kwlist`, `softkwlist`, `issoftkeyword`, keyword-module reflection, or mutation.

The semantic authority is native CPython behavior for string inputs. The portable boundary recognizes hard Python keywords and deliberately excludes soft keywords. On the current CPython host, the hard-keyword set is the 35 values in `keyword.kwlist`; the soft-keyword set is `_, case, match, type`. The overlay contains the deterministic hard-keyword tuple and does not derive it from MicroPython.

### Portable overlay

The MicroPython-only module is:

```text
root/portability/micropython/keyword.py
```

It exports only `iskeyword` and performs immutable tuple membership. It contains no filesystem access, dynamic discovery, parser internals, runtime generation, or DD content knowledge. Existing validators remain authoritative for lowercase snake-case syntax, punctuation, whitespace, and casing.

Native CPython, Pyodide, Chaquopy, pytest, packaging, and development tooling continue to use the standard-library `keyword`. Forced-overlay tests run in subprocesses, remove a preloaded native `keyword`, and assert that the resolved module origin is the portability file. This prevents a cached native module or path ordering accident from producing a false green.

The real DD validation paths are exercised under the forced stack for enemy archetype IDs, Drifter IDs, starting weapon IDs, route/content IDs, and weapon item IDs. Valid authored identifiers are accepted, Python hard keywords are rejected by the existing validators, and punctuation, whitespace, and casing remain rejected by those production validators. Portable dataclasses and StrEnum behavior remain active through the same forced environment.

### MPY5 evidence

Native CPython raw probe:

```text
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

Forced-overlay CPython raw probe:

```text
MPY|CATALOG_IMPORT|PASS
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|74
MPY|DATACLASS|CONSTRUCTED|33
```

Pinned MicroPython runtime:

```text
MPY|BOOT|PASS
MPY|IMPLEMENTATION|micropython
MPY|VERSION|1.29.0
MPY|PLATFORM|win32
MPY|MEMORY|BOOT|FREE|1003456|ALLOC|21056
MPY|SOURCE_PATH|BEGIN
MPY|MEMORY|SOURCE_PATH|BEFORE|FREE|1003408|ALLOC|21104
MPY|MEMORY|SOURCE_PATH|AFTER|FREE|1003376|ALLOC|21136
MPY|SOURCE_PATH|PASS
MPY|CATALOG_IMPORT|BEGIN
MPY|MEMORY|CATALOG_IMPORT|BEFORE|FREE|1003376|ALLOC|21136
Warning: exception chaining not supported
MPY|CATALOG_IMPORT|FAIL|ValueError|invalid kind: 'damage'
MPY|MEMORY|CATALOG_IMPORT|FAIL|FREE|945088|ALLOC|79424
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|4
MPY|DATACLASS|CONSTRUCTED|1
```

The previous `ImportError: no module named 'keyword'` wall is crossed. The first unrelated post-keyword failure is:

```text
stage: CATALOG_IMPORT
exception: ValueError
message: invalid kind: 'damage'
origin: root/src/app/combat/move.py, Move.__post_init__
traceback path: Move.__post_init__ -> _validate_enum
```

The original MicroPython traceback ends at:

```text
root/src/app/combat/move.py, line 63, in __post_init__
root/src/app/combat/move.py, line 118, in _validate_enum
ValueError: invalid kind: 'damage'
```

MPY5 does not repair this enum-conversion frontier. It belongs to the next evidence-derived gate. The dataclass census remains diagnostic and dynamic; the new frontier was reached after four classes were decorated and one was successfully constructed.

External runtime evidence:

```text
MicroPython tag: v1.29.0
Resolved source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Source checkout: clean
Reported platform: win32
```

MPY5 impact remains:

```text
root/src production files changed: 0
gameplay changes: 0
content changes: 0
persistence changes: 0
semantic API changes: 0
raw probe changes: 0
```

MPY5 closes only the observed keyword boundary. No speculative enum, typing, collections, pathlib, persistence, annotation, or gameplay compatibility work is included.



## MPY6 - Portable StrEnum member normalization

MPY6 advances the pinned MicroPython qualification past the existing-member
lookup failure recorded by MPY5. The compatibility boundary remains outside
`root/src`; DD production source, gameplay, content, persistence, semantic
APIs, and the unchanged raw probe remain untouched.

### MPY6 diagnosis

The MPY5 failure occurred while `Move.__post_init__` normalized authored enum
members through `EnumType(value)`:

```text
Move.__post_init__
-> _validate_enum("kind", MoveKind.DAMAGE, MoveKind)
-> MoveKind(MoveKind.DAMAGE)
-> portable registry lookup
-> ValueError: 'damage' is not a valid MoveKind
```

The pinned runtime already supported raw-string construction. The precise
qualification result was:

```text
Sample("first")              PASS
Sample(Sample.FIRST)         FAIL
MoveKind("damage")           PASS
MoveKind(MoveKind.DAMAGE)    FAIL
```

This was not a failure of the `__build_class__` hook, canonical member
creation, string subclassing, or ordinary value lookup. MicroPython's mapping
behavior does not reliably resolve an existing portable string-subclass member
as a string registry key.

### MPY6 correction

`root/portability/micropython/enum.py` now performs the smallest possible
normalization before registry lookup:

```python
if isinstance(value, cls):
    return value
```

An existing member therefore returns unchanged, preserving canonical identity.
Raw strings continue through the existing value registry. Unknown values,
duplicate values, malformed members, string equality, hashing, and `isinstance`
behavior remain unchanged.

The forced-overlay regression covers both forms for every dynamically
discovered DD enum member:

```text
EnumType(raw_value)   is MEMBER
EnumType(MEMBER)      is MEMBER
```

It also constructs a real `Move` twice: once with authored enum members and
once with raw string values. The test subprocess uses a member-sensitive
registry to reproduce the lookup behavior observed on MicroPython while
remaining runnable in the CPython CI environment.

### MPY6 qualification evidence

The direct qualification under the pinned MicroPython `v1.29.0` runtime
reported:

```text
MPY6|OVERLAY| enum
MPY6|SAMPLE|RAW| True
MPY6|SAMPLE|MEMBER| True
MPY6|SAMPLE|INVALID|PASS
MPY6|MOVEKIND|RAW| True
MPY6|MOVEKIND|MEMBER| True
MPY6|MOVE|MEMBERS|PASS| True True
MPY6|MOVE|STRINGS|PASS| True True
MPY6|RESULT|PASS
```

Native CPython and the forced overlay both completed the unchanged raw probe.
The forced overlay retained the dynamic dataclass census:

```text
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|74
MPY|DATACLASS|CONSTRUCTED|33
```

The unchanged raw probe under pinned MicroPython crossed the enum frontier and
stopped at the next unrelated compatibility wall:

```text
MPY|BOOT|PASS
MPY|IMPLEMENTATION|micropython
MPY|VERSION|1.29.0
MPY|PLATFORM|win32
MPY|MEMORY|BOOT|FREE|1003456|ALLOC|21056
MPY|SOURCE_PATH|BEGIN
MPY|MEMORY|SOURCE_PATH|BEFORE|FREE|1003408|ALLOC|21104
MPY|MEMORY|SOURCE_PATH|AFTER|FREE|1003376|ALLOC|21136
MPY|SOURCE_PATH|PASS
MPY|CATALOG_IMPORT|BEGIN
MPY|MEMORY|CATALOG_IMPORT|BEFORE|FREE|1003376|ALLOC|21136
MPY|CATALOG_IMPORT|FAIL|AttributeError|'re' object has no attribute 'fullmatch'
MPY|MEMORY|CATALOG_IMPORT|FAIL|FREE|945040|ALLOC|79472
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|4
MPY|DATACLASS|CONSTRUCTED|2
```

The original traceback was preserved and re-raised:

```text
Warning: exception chaining not supported
Traceback (most recent call last):
  File "root\\tools\\micropython_probe_bootstrap.py", line 83, in <module>
  File "root\\tools\\micropython_probe_bootstrap.py", line 76, in main
  File "<string>", line 262, in <module>
  File "<string>", line 244, in main
  File "<string>", line 25, in _run_stage
  File "<string>", line 59, in _import_catalog
  File "root\\src/app/content/catalog.py", line 3, in <module>
  File "root\\src/app/content/_generated_catalog.py", line 3, in <module>
  File "root\\src/app/content/enemies/goblin/__init__.py", line 1, in <module>
  File "root\\src/app/content/enemies/goblin/enemy.py", line 57, in <module>
  File "C:/Users/User/Documents/Dev/Python/Dungeon Drifters/root/portability/micropython/dataclasses.py", line 90, in __init__
  File "root\\src/app/content/enemy_spec.py", line 76, in __post_init__
AttributeError: 're' object has no attribute 'fullmatch'
```

The next gate must be derived from this observed `re.fullmatch` failure.
MPY6 does not repair `re`, typing, collections, pathlib, persistence,
annotation syntax, or gameplay.

MPY6 impact remains:

```text
root/src production files changed: 0
gameplay changes: 0
content changes: 0
persistence changes: 0
semantic API changes: 0
raw probe changes: 0
```

External runtime evidence remains:

```text
MicroPython tag: v1.29.0
Resolved source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Source checkout: clean
Reported platform: win32
```

## MPY7 - Portable Regex Fullmatch Boundary

MPY7 advances the pinned MicroPython qualification past the missing
`re.fullmatch` behavior recorded by MPY6. The compatibility boundary remains
outside `root/src`; the raw probe, gameplay, content, persistence, semantic
APIs, and schema remain unchanged.

MPY6 was sealed at:

```text
a97def8f26d811b08fe650157296a8da57bcb6a8
MPY6 - Repair Portable StrEnum Construction
```

### Production regex audit

The production regex surface was discovered dynamically from
`root/src/app/**/*.py`. The current runtime call shapes are:

```text
re.compile(pattern)
compiled_pattern.fullmatch(value)
re.fullmatch(pattern, value)
```

The current compiled patterns validate enemy, Drifter, and route content IDs.
`Weapon._validate_item_id()` uses the module-level unanchored pattern. The
audit excludes `root/tools`, tests, and documentation, and rejects future
production use of unsupported regex operations, match-position APIs, match
metadata, bytes patterns, scanners, or reflection.

DD does not require module-level or compiled `match`, `search`, `sub`, `subn`,
`split`, `findall`, `finditer`, or `escape` behavior. It does not inspect
`start()`, `end()`, `span()`, groups, or other match-object metadata.

### Pinned MicroPython evidence

The native MicroPython `re` module provides `compile`, `match`, and `search`,
but not `fullmatch`. Compiled patterns also provide `match` and `search`, but
not `fullmatch`. Match objects expose only `group` for the relevant operation;
`start`, `end`, and `span` are unavailable. `group(0)` returns the consumed
text:

```text
pattern.match("goblin").group(0)       -> "goblin"
pattern.match("goblin!").group(0)     -> "goblin"
pattern.match("goblin extra").group(0) -> "goblin"
```

The native module accepts a path-inserted portability directory but remains a
frozen module with no file origin. A `root/portability/micropython/re.py`
module would therefore not override it. The native module object also rejects
adding attributes directly.

### Selected compatibility boundary

MPY7 uses:

```text
root/portability/micropython/re_compat.py
```

The existing bootstrap imports native `re` first, calls `install(native_re)`
only when the interpreter identifies itself as MicroPython, and then stores the
returned proxy in `sys.modules["re"]` before DD imports execute:

```text
native frozen re
    -> install(native_re)
    -> proxy privately retains native_re
    -> sys.modules["re"] = proxy
    -> DD imports re normally
```

The proxy delegates unknown module and compiled-pattern operations to the
native engine. It adds only module-level `fullmatch` and compiled-pattern
`fullmatch`. It does not implement a regex engine, parser, translator, or
second match-object representation.

Full-match behavior is:

```python
match = native_pattern.match(string)
if match is None or match.group(0) != string:
    return None
return match
```

Successful calls return the original native match object. DD does not pass
regex flags, so the proxy calls native `compile(pattern)` with one argument;
nonzero flags fail explicitly rather than becoming an unqualified compatibility
promise. Installation is idempotent, and patterns compiled before installation
remain native and are not retroactively wrapped.

Normal CPython, Pyodide, Chaquopy, pytest, and packaging continue using the
standard-library `re`. Forced CPython qualification imports native `re`, calls
the adapter explicitly in an isolated subprocess, and verifies the proxy
marker and retained native module. It does not fake a MicroPython
`sys.implementation` value or change normal bootstrap behavior.

### MPY7 qualification evidence

The direct qualification under pinned MicroPython `v1.29.0` reported:

```text
MPY7|NATIVE|COMPILE| True
MPY7|NATIVE|FULLMATCH| False
MPY7|NATIVE|PATTERN_FULLMATCH| False
MPY7|PROXY|ACTIVE| True
MPY7|PROXY|DELEGATED_SEARCH| True
MPY7|PROXY|COMPILED| True
MPY7|PROXY|COMPILED_FULLMATCH| True True
MPY7|PROXY|MODULE_FULLMATCH| True True
```

The forced compatibility CPython raw probe completed every unchanged stage:

```text
MPY|CATALOG_IMPORT|PASS
MPY|DRIFTER_SPEC|PASS
MPY|NEW_GAME|PASS
MPY|FIRST_ENCOUNTER|PASS
MPY|ENEMY_STATE|PASS
MPY|BATTLE_CONSTRUCTION|PASS
MPY|BATTLE_VIEW|PASS
MPY|BATTLE_INPUT|PASS
MPY|BATTLE_COMPLETE|PASS
MPY|SESSION_IMPORT|PASS
MPY|SESSION_CONSTRUCTION|PASS
MPY|SESSION_VIEW|PASS
MPY|SESSION_ENCOUNTER_ENTRY|PASS
MPY|SESSION_ENCOUNTER_COMPLETE|PASS
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

The pinned MicroPython raw probe crossed the `re.fullmatch` frontier and
stopped at the next unrelated compatibility wall:

```text
MPY|BOOT|PASS
MPY|IMPLEMENTATION|micropython
MPY|VERSION|1.29.0
MPY|PLATFORM|win32
MPY|MEMORY|BOOT|FREE|1001952|ALLOC|22560
MPY|SOURCE_PATH|PASS
MPY|CATALOG_IMPORT|BEGIN
MPY|MEMORY|CATALOG_IMPORT|BEFORE|FREE|1001872|ALLOC|22640
MPY|CATALOG_IMPORT|FAIL|ImportError|no module named 'collections.abc'
MPY|MEMORY|CATALOG_IMPORT|FAIL|FREE|934288|ALLOC|90224
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|4
MPY|DATACLASS|CONSTRUCTED|3
```

The next gate must be derived from the observed `collections.abc` import
failure. No speculative repair is documented here.

## MPY8 - Portable `collections.abc` Boundary

MPY8 advances the pinned MicroPython qualification past the missing
`collections.abc` module without changing `root/src`, gameplay, content,
persistence, semantic APIs, or the raw probe. MPY7 was sealed at:

```text
6b4883a833d53ce6bf412ed7957a7b72a5a51736
MPY7 - Add Portable Regex Fullmatch Boundary
```

### Production audit

The production audit scans only `root/src/app/**/*.py` and discovers the
following runtime dependencies:

```text
from collections.abc import Mapping
    app.items.weapon: isinstance(stat_bonuses, Mapping)
    app.content.weapon_spec: Mapping[str, int] annotation

from collections.abc import Sequence
    app.combat.battle: isinstance(enemies, Sequence)

from collections import Counter
    app.combat.battle: Counter(iterable), mapping lookup, += 1
```

The `Sequence` imported by `app.combat.combatant` comes from `typing` and is
not a `collections.abc` runtime dependency. The audit dynamically classifies
imports, `isinstance` checks, generic subscriptions, Counter construction,
mapping lookup, and increment operations. It excludes `root/tools`, tests,
and documentation and uses no permanent file or call counts.

### Native MicroPython evidence

MicroPython `v1.29.0` reports:

```text
collections.Mapping: False
collections.Sequence: False
collections.Counter: False
collections.deque: True
collections.namedtuple: True
collections.OrderedDict: True
```

The native `collections` module has no usable `__file__` or `__path__`, does
not accept an `abc` attribute, and native `import collections.abc` fails:

```text
ImportError: no module named 'collections.abc'
AttributeError: 'module' object has no attribute 'abc'
```

A path-inserted child or parent package cannot outrank the frozen native
module. Directly placing a module-like child in
`sys.modules["collections.abc"]` does support the exact current import form:
`from collections.abc import Mapping, Sequence`.

MicroPython ignores class annotation evaluation for the tested form
`Mapping[str, int]`; the resulting class has no `__annotations__`. Generic
subscription is therefore not a runtime requirement for this gate and no
typing system is added.

### Selected boundary

MPY8 adds:

```text
root/portability/micropython/collections_abc_compat.py
```

The MicroPython-only bootstrap retains native `collections` and installs only
the `collections.abc` child through `sys.modules` before DD imports execute.
It obtains the existing `_ReadonlyMapping` class through a temporary source
path insertion so the exported runtime contract is:

```python
Mapping = (dict, _ReadonlyMapping)
Sequence = (list, tuple)
```

This preserves dictionary and MPY1 read-only mapping recognition, ordered
list/tuple enemy groups, and DD's explicit exclusion of strings, bytes, and
bytearrays at the Battle call site. No global `isinstance` replacement,
parent-module proxy, general ABC framework, or `Counter` implementation is
introduced. Installation is idempotent and native top-level `collections`
attributes remain owned by the native module.

Under forced CPython qualification, the compatibility child exposes native
`collections.abc.Mapping` and `Sequence`, keeping real DD annotations such
as `Mapping[str, int]` valid while still proving that the compatibility module
was explicitly installed in an isolated subprocess. Normal CPython imports
remain standard-library imports.

### MPY8 qualification evidence

The direct qualification under the pinned MicroPython runtime passed the
qualified imports, mapping/sequence checks, annotation probe, and real
Weapon/WeaponSpec construction:

```text
MPY8|NATIVE|ABC_IMPORT|FAIL|ImportError|no module named 'collections.abc'
MPY8|IMPORT|MAPPING_SEQUENCE|PASS
MPY8|ANNOTATION|EVALUATED| False
MPY8|WEAPON|REAL_PATH|PASS
MPY8|COUNTER|NATIVE_AVAILABLE| False
```

The forced CPython subprocess tests passed native-module retention,
idempotent installation, Mapping/Sequence behavior, DD validator behavior,
real Weapon/WeaponSpec paths, and Battle's list/tuple normalization boundary.
The native and forced compatibility contract tests passed `7` tests.

The unchanged raw probe crossed `collections.abc` and stopped at the next
unrelated runtime incompatibility:

```text
MPY|BOOT|PASS
MPY|IMPLEMENTATION|micropython
MPY|VERSION|1.29.0
MPY|PLATFORM|win32
MPY|MEMORY|BOOT|FREE|999552|ALLOC|24960
MPY|SOURCE_PATH|PASS
MPY|CATALOG_IMPORT|BEGIN
MPY|MEMORY|CATALOG_IMPORT|BEFORE|FREE|999488|ALLOC|25024
MPY|CATALOG_IMPORT|FAIL|AttributeError|'str' object has no attribute 'isascii'
MPY|MEMORY|CATALOG_IMPORT|FAIL|FREE|906848|ALLOC|117664
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|10
MPY|DATACLASS|CONSTRUCTED|7
```

The original traceback identifies `DrifterSpec.__post_init__` at
`root/src/app/content/drifter_spec.py:126`, where `choice.isascii()` is
called while the generated catalog constructs Azhvielle's specification:

```text
AttributeError: 'str' object has no attribute 'isascii'
```

That `str.isascii` frontier is the next evidence-derived gate. MPY8 does not
repair or speculate about it. The pinned external runtime evidence remains:

```text
MicroPython tag: v1.29.0
Resolved source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Source checkout: clean
Reported platform: win32
```

MPY8 changed zero `root/src` production files, gameplay behavior, content,
persistence, semantic APIs, and raw-probe code. Dataclass, enum, keyword, and
regex boundaries remain unchanged.

## MPY9 - Portable ASCII String Validation

MPY9 advances the pinned MicroPython qualification past the missing
`str.isascii()` and `str.isdecimal()` methods without adding a compatibility
module or changing the raw probe. MPY8 was sealed at:

```text
bb99b7e1e9360078b157a85400e3c9dea73a386f
MPY8 - Add Portable Collections ABC Boundary
```

### Historical failure and runtime evidence

The MPY8 probe stopped during `CATALOG_IMPORT` while the generated catalog
constructed a `DrifterSpec`. Its `__post_init__` used two methods that the
pinned runtime does not provide:

```text
AttributeError: 'str' object has no attribute 'isascii'
```

Direct qualification under MicroPython `v1.29.0` recorded:

```text
str.isascii: false
str.isdecimal: false
str.isdigit: true
setattr(str, "isascii", ...): AttributeError: 'type' object has no attribute 'isascii'
builtins.str replacement: literal strings remain builtin str
```

Replacing `builtins.str` therefore cannot repair literal-string behavior, and
the built-in string type cannot be extended. MPY9 uses the already qualified
regex boundary instead of global string patching or a string wrapper.

### Production audit and equivalent expression

The dynamic audit scans only `root/src/app/**/*.py`. After the correction it
discovers no production calls to `isascii` or `isdecimal`, and no unsupported
string methods in the qualified audit surface. The remaining
`isdecimal()` call in `root/tools/scaffold_content.py` is tooling and is
intentionally outside the runtime audit.

The former validation contract was:

```python
isinstance(value, str)
and bool(value)
and value.isascii()
and value.isdecimal()
and int(value) >= 1
```

The production implementation now uses:

```python
_ASCII_DECIMAL_PATTERN = re.compile(r"^[0-9]+$")
choice = _nonempty_string("choice", self.choice)
if _ASCII_DECIMAL_PATTERN.fullmatch(choice) is None or int(choice) < 1:
    raise ValueError("choice must be a positive ASCII integer string")
```

The regex plus positive integer check agrees with the native CPython
reference across the accepted and rejected corpus, including leading zeroes,
signs, whitespace, punctuation, letters, Unicode decimal characters,
superscript digits, fractions, Roman numerals, and mixed strings. Empty and
non-string values continue to use the existing `_nonempty_string()` type and
empty-value errors.

No validation rule is duplicated in a portability module. The pattern is
ASCII-specific by design: `isdigit()` was not substituted because it would
accept values that the combined `isascii()` and `isdecimal()` contract
rejects.

### Qualification results

The real catalog and Drifter path now construct successfully under the full
existing compatibility stack:

```text
MPY9|STR|ISASCII|False
MPY9|STR|ISDECIMAL|False
MPY9|STR|ISDIGIT|True
MPY9|STR|SETATTR|AttributeError|'type' object has no attribute 'isascii'
MPY9|DRIFTER_SPEC|PASS|branoc|1
MPY9|CATALOG|IMPORT|PASS
```

The unchanged raw probe completes every stage under native CPython `3.14.6`,
and the forced CPython regex-proxy subprocess also completes every stage.
Those runs qualify harness reachability only; they are not MicroPython
compatibility evidence.

The unchanged raw probe through the pinned MicroPython bootstrap now reports:

```text
MPY|BOOT|PASS
MPY|IMPLEMENTATION|micropython
MPY|VERSION|1.29.0
MPY|PLATFORM|win32
MPY|MEMORY|BOOT|FREE|999552|ALLOC|24960
MPY|SOURCE_PATH|BEGIN
MPY|MEMORY|SOURCE_PATH|BEFORE|FREE|999504|ALLOC|25008
MPY|MEMORY|SOURCE_PATH|AFTER|FREE|999488|ALLOC|25024
MPY|SOURCE_PATH|PASS
MPY|CATALOG_IMPORT|BEGIN
MPY|MEMORY|CATALOG_IMPORT|BEFORE|FREE|999488|ALLOC|25024
MPY|MEMORY|CATALOG_IMPORT|AFTER|FREE|860288|ALLOC|164224
MPY|CATALOG_IMPORT|PASS
MPY|DRIFTER_SPEC|BEGIN
MPY|MEMORY|DRIFTER_SPEC|BEFORE|FREE|860288|ALLOC|164224
MPY|MEMORY|DRIFTER_SPEC|AFTER|FREE|860272|ALLOC|164240
MPY|DRIFTER_SPEC|PASS
MPY|NEW_GAME|BEGIN
MPY|MEMORY|NEW_GAME|BEFORE|FREE|860288|ALLOC|164224
MPY|MEMORY|NEW_GAME|AFTER|FREE|834000|ALLOC|190512
MPY|NEW_GAME|PASS
MPY|FIRST_ENCOUNTER|BEGIN
MPY|MEMORY|FIRST_ENCOUNTER|BEFORE|FREE|833984|ALLOC|190528
MPY|MEMORY|FIRST_ENCOUNTER|AFTER|FREE|833968|ALLOC|190544
MPY|FIRST_ENCOUNTER|PASS
MPY|ENEMY_STATE|BEGIN
MPY|MEMORY|ENEMY_STATE|BEFORE|FREE|833968|ALLOC|190544
MPY|MEMORY|ENEMY_STATE|AFTER|FREE|833440|ALLOC|191072
MPY|ENEMY_STATE|PASS
MPY|BATTLE_CONSTRUCTION|BEGIN
MPY|MEMORY|BATTLE_CONSTRUCTION|BEFORE|FREE|833440|ALLOC|191072
MPY|BATTLE_CONSTRUCTION|FAIL|ImportError|can't import name Counter
MPY|MEMORY|BATTLE_CONSTRUCTION|FAIL|FREE|822256|ALLOC|202256
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|15
MPY|DATACLASS|CONSTRUCTED|13
```

The original traceback is preserved by the probe:

```text
ImportError: can't import name Counter
```

The first post-MPY9 frontier is therefore the unrelated `Counter` import in
`root/src/app/combat/battle.py`. MPY9 does not repair or speculate about it.
The dataclass census remains dynamic and diagnostic: `EXPECTED` is the
generated manifest set, while the decorated and constructed values are unique
identity counts emitted by the bootstrap's `finally` path.

Pinned external runtime evidence remains:

```text
MicroPython tag: v1.29.0
Resolved source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Source checkout: clean
Reported platform: win32
```

### Scope and release result

MPY9 changed exactly one production file:
`root/src/app/content/drifter_spec.py`. It added no overlay, bootstrap, raw
probe, tooling, generated-catalog, save-schema, gameplay, content, or
semantic-API changes. The production impact is:

```text
root/src production files changed: 1
semantic behavior changed: 0
gameplay changed: 0
content changed: 0
persistence changed: 0
semantic API changed: 0
raw probe changed: 0
compatibility framework changes: 0
bootstrap changes: 0
```

The next gate must be derived from the observed `Counter` failure. No
speculative repair is documented here.

## MPY10 - Remove Counter Runtime Dependency

MPY10 advances the pinned MicroPython qualification past the `Counter` import
failure without adding a Counter compatibility layer. MPY9 was sealed at:

```text
d78c07293219116f04f9c203b6654bf8b9728e35
MPY9 - Repair Portable ASCII String Validation
```

### Historical failure and production audit

The MPY9 raw probe stopped at `BATTLE_CONSTRUCTION` because
`root/src/app/combat/battle.py` imported `Counter` from `collections`. The
audited production use was limited to enemy display-label bookkeeping:

```python
counts = Counter(enemy.display_name for enemy in enemies)
positions = Counter()
positions[name] += 1
counts[name]
```

The dynamic audit scans only `root/src/app/**/*.py`. After MPY10 it discovers:

```text
production Counter imports: none
production Counter calls: none
production Counter-dependent operations: none
```

The audit continues to discover the existing `Mapping` and `Sequence`
contracts. Tooling, tests, and documentation are excluded from the runtime
dependency census. The test-only native `Counter` reference is an oracle for
equivalence and is not a production dependency.

### Selected source-portable replacement

DD only needs to count string keys, default missing values to zero, increment
them, and read them. `_build_enemy_display_labels()` now uses ordinary
dictionaries:

```python
counts = {}
for enemy in enemies:
    name = enemy.display_name
    counts[name] = counts.get(name, 0) + 1

positions = {}
```

This preserves the exact label contract:

```text
Goblin                         -> Goblin
Goblin, Goblin                 -> Goblin 1, Goblin 2
Goblin, Shaman, Goblin         -> Goblin 1, Shaman, Goblin 2
Goblin, Shaman, Goblin, Shaman -> Goblin 1, Shaman 1, Goblin 2, Shaman 2
```

Labels remain based on authored enemy order. Distinct runtime enemy instances
with the same display name are accepted and numbered independently. The
existing rejection of the same `EnemyState` instance supplied twice remains
unchanged. Enemy identity, target IDs, Battle views, combat ordering, and
resolution are unaffected.

Counter emulation was rejected because it would add unrelated semantics such
as `most_common()`, `elements()`, arithmetic, subtraction, update behavior,
and missing-key conventions that DD does not require. Ordinary portable Python
expresses the complete production contract directly.

### Qualification results

The focused semantic tests compare the dictionary implementation with a
test-only native CPython `Counter` reference over generated name sequences and
real catalog-backed enemies. The result was:

```text
MPY10 focused collections and Battle-label tests: 13 passed
```

Native CPython `3.14.6` and a forced regex-compatibility CPython subprocess
both complete the unchanged raw probe through `SESSION_ENCOUNTER_COMPLETE`.
This confirms no regression in the ordinary runtime or previously qualified
compatibility boundaries.

The direct pinned MicroPython qualification recorded the native capability and
the next import wall:

```text
MPY10|COUNTER|AVAILABLE|False
ImportError: no module named 'typing'
```

`Counter` was therefore crossed naturally. The direct Battle attempt imported
the updated module and then stopped at the next unrelated `typing` dependency
from `root/src/app/combat/combatant.py`. No later direct label step was
attempted after that frontier.

The unchanged raw probe through the pinned MicroPython bootstrap reports:

```text
MPY|BOOT|PASS
MPY|IMPLEMENTATION|micropython
MPY|VERSION|1.29.0
MPY|PLATFORM|win32
MPY|MEMORY|BOOT|FREE|999552|ALLOC|24960
MPY|SOURCE_PATH|BEGIN
MPY|MEMORY|SOURCE_PATH|BEFORE|FREE|999504|ALLOC|25008
MPY|MEMORY|SOURCE_PATH|AFTER|FREE|999488|ALLOC|25024
MPY|SOURCE_PATH|PASS
MPY|CATALOG_IMPORT|BEGIN
MPY|MEMORY|CATALOG_IMPORT|BEFORE|FREE|999488|ALLOC|25024
MPY|MEMORY|CATALOG_IMPORT|AFTER|FREE|860288|ALLOC|164224
MPY|CATALOG_IMPORT|PASS
MPY|DRIFTER_SPEC|BEGIN
MPY|MEMORY|DRIFTER_SPEC|BEFORE|FREE|860288|ALLOC|164224
MPY|DRIFTER_SPEC|AFTER|FREE|860272|ALLOC|164240
MPY|DRIFTER_SPEC|PASS
MPY|NEW_GAME|BEGIN
MPY|MEMORY|NEW_GAME|BEFORE|FREE|860288|ALLOC|164224
MPY|NEW_GAME|AFTER|FREE|834000|ALLOC|190512
MPY|NEW_GAME|PASS
MPY|FIRST_ENCOUNTER|BEGIN
MPY|MEMORY|FIRST_ENCOUNTER|BEFORE|FREE|833984|ALLOC|190528
MPY|FIRST_ENCOUNTER|AFTER|FREE|833968|ALLOC|190544
MPY|FIRST_ENCOUNTER|PASS
MPY|ENEMY_STATE|BEGIN
MPY|MEMORY|ENEMY_STATE|BEFORE|FREE|833968|ALLOC|190544
MPY|ENEMY_STATE|AFTER|FREE|833440|ALLOC|191072
MPY|ENEMY_STATE|PASS
MPY|BATTLE_CONSTRUCTION|BEGIN
MPY|MEMORY|BATTLE_CONSTRUCTION|BEFORE|FREE|833440|ALLOC|191072
MPY|BATTLE_CONSTRUCTION|FAIL|ImportError|no module named 'typing'
MPY|MEMORY|BATTLE_CONSTRUCTION|FAIL|FREE|783840|ALLOC|240672
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|31
MPY|DATACLASS|CONSTRUCTED|15
```

The original traceback is preserved:

```text
ImportError: no module named 'typing'
```

The next gate must be derived from this observed `typing` failure. MPY10 does
not repair or speculate about it. The dataclass census remains dynamic and
diagnostic, with unique identity sets rather than construction totals.

Pinned external runtime evidence remains:

```text
MicroPython tag: v1.29.0
Resolved source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Source checkout: clean
Reported platform: win32
```

### Scope and release result

MPY10 changed exactly one production file:
`root/src/app/combat/battle.py`. It changed no compatibility overlay,
bootstrap, raw probe, save schema, content, or semantic API. The production
impact is:

```text
root/src production files changed: 1
semantic behavior changed: 0
gameplay behavior changed: 0
content changed: 0
persistence changed: 0
semantic API changed: 0
raw probe changed: 0
compatibility framework changed: 0
bootstrap changed: 0
dataclass overlay changed: 0
enum overlay changed: 0
keyword overlay changed: 0
regex overlay changed: 0
collections.abc changed: 0
string-validation changed: 0
portable Counter implementation: 0
schema changed: 0
generated catalog changed: 0
```

## MPY11 - Portable Typing and Protocol Boundary

MPY11 advances the raw MicroPython qualification past the `typing` import
failure recorded at MPY10. The baseline was:

```text
MPY10 sealed SHA: 00b7733c02a8b78ebfb856ccbe5fc9ea119f6fe9
MicroPython: v1.29.0
Source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Platform: win32
```

The original MPY10 frontier was:

```text
MPY|BATTLE_CONSTRUCTION|FAIL|ImportError|no module named 'typing'
```

MPY11 keeps native `typing` for CPython and static tooling. Its only
MicroPython compatibility module is the import-only subset at
`root/portability/micropython/typing.py`. No file under `root/src` imports the
overlay directly.

### Dynamic typing audit

The audit scans only `root/src/app/**/*.py`, so tests, tools, documentation,
and portability modules cannot become accidental runtime dependencies. The
current production typing surface is discovered rather than guarded by fixed
file or use counts. It contains imports of:

```text
Protocol
runtime_checkable
TypeAlias
Sequence
Union
```

The four runtime aliases are:

```text
app.ui.battle_ui.BattleInput
app.ui.overworld_ui.OverworldInput
app.game.overworld_session.SessionView
app.game.overworld_session.SessionInput
```

They are now constructed with native `typing.Union[...]` under CPython and
the portable `Union[...]` marker under MicroPython. The audit classifies all
PEP 604 `A | B` expressions by context. Annotation-only unions, such as
`ArcaneDischarge.broken_target: object | None`, remain unchanged because the
pinned runtime accepts them as class annotations. Only runtime-evaluated
alias assignments required correction.

The audit also proves that no alias is passed to `isinstance` or `issubclass`
and that aliases are not used as dispatch authority, persistence values, or
reflection targets. Unsupported future typing imports, attribute uses, alias
operands, or runtime union expressions fail the audit visibly.

### Protocol contracts

The authoritative Protocol declarations remain in the existing production
modules:

```text
Combatant
    data: display_name, health, mana_resource, super_resource,
          generates_super, can_defend, combat_moves
    methods: effective_stat, defend_reduction_percent, is_alive

EnemyCombatant
    Combatant requirements plus data: archetype_id, tier

BattleUI
    methods: render, read_input

OverworldUI
    methods: render, read_input
```

The dynamic AST audit derives those groups, including inherited Combatant
members for EnemyCombatant, and compares them exactly with the module-local
requirement tuples consumed by `is_combatant`, `is_enemy_combatant`,
`is_battle_ui`, and `is_overworld_ui`. This Protocol/predicate parity
invariant fails if a declaration gains, loses, or reclassifies a member
without the corresponding portable contract changing.

The shared `app.runtime_contracts.has_required_members()` primitive requires
data members to be accessible and declared method members to be callable. It
does not inspect signatures, emulate Protocol metaclasses, or patch global
`isinstance`. Native CPython Protocol behavior remains available for its
existing callers; the portable predicates preserve the DD contract where
runtime Protocol checks were previously used:

```text
Battle._normalize_enemies
resolver._is_valid_combatant
OverworldSession.__init__
```

The resolver's existing explicit property and callability checks remain in
place, including their rejection reasons. BattleUI remains a public Protocol
contract and gains no new production runtime check.

### MicroPython typing evidence

The pinned runtime preflight established the relevant boundary:

```text
typing import: unavailable on stock MicroPython v1.29.0
metaclass= on the relevant portable class boundary: unusable
custom __instancecheck__: unusable for this purpose
object subscription UnionMarker()[A, B]: PASS
class subscription Marker[A, B]: FAIL
```

The selected overlay therefore exports only `Protocol`,
`runtime_checkable`, `TypeAlias`, `Sequence`, and `Union`. `Protocol` is a
basic subclassable class, `runtime_checkable` is an identity decorator,
`TypeAlias` is an inert marker, `Sequence` is a subscriptable annotation
marker, and `Union[...]` returns an inert tuple-like representation. It does
not implement generic runtime checking, type reflection, or a general
typing system. The overlay is selected solely by MicroPython's existing
path/bootstrap arrangement; native CPython, Pyodide, Chaquopy, pytest, and
packaging continue to use the standard-library module.

### Qualification results

The focused MPY11 contract and forced-overlay tests pass. The forced tests
run in subprocesses and verify the overlay's module origin, all four aliases,
real combatants, structural UI values, callability rejection, and process
isolation. Native tests continue to exercise CPython Protocol acceptance and
the existing dataclass, enum, keyword, regex, collections, string, Counter,
Battle, M10, and M11 contracts.

The native CPython raw probe reaches every current stage:

```text
MPY|CATALOG_IMPORT|PASS
MPY|DRIFTER_SPEC|PASS
MPY|NEW_GAME|PASS
MPY|FIRST_ENCOUNTER|PASS
MPY|ENEMY_STATE|PASS
MPY|BATTLE_CONSTRUCTION|PASS
MPY|BATTLE_VIEW|PASS
MPY|BATTLE_INPUT|PASS
MPY|BATTLE_COMPLETE|PASS
MPY|SESSION_IMPORT|PASS
MPY|SESSION_CONSTRUCTION|PASS
MPY|SESSION_VIEW|PASS
MPY|SESSION_ENCOUNTER_ENTRY|PASS
MPY|SESSION_ENCOUNTER_COMPLETE|PASS
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

The unchanged raw probe through the complete pinned MicroPython bootstrap
crosses the former typing wall. Its first unrelated frontier is:

```text
MPY|BATTLE_CONSTRUCTION|FAIL|SyntaxError|*x must be assignment target
MPY|MEMORY|BATTLE_CONSTRUCTION|FAIL|FREE|733248|ALLOC|291264
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|46
MPY|DATACLASS|CONSTRUCTED|17
```

The original traceback is preserved and identifies the next wall:

```text
File "root/src/app/presentation/battle_session.py", line 30, in entries
SyntaxError: *x must be assignment target
```

The preceding MicroPython stages all pass through `ENEMY_STATE`. The typing
failure is therefore crossed; MPY11 does not repair this unrelated syntax
limitation, nor does it speculate about the next gate.

### Scope and boundary

```text
root/src production files changed: 6
root/src/app/runtime_contracts.py: added
runtime Protocol checks replaced: 3
runtime TypeAlias unions rewritten: 4
gameplay behavior changed: 0
content changed: 0
persistence or save schema changed: 0
semantic API changed: 0
presenter behavior changed: 0
raw probe changed: 0
browser, Android, C++, or platform architecture changed: 0
```

MPY11 preserves one authoritative gameplay implementation. The new portable
boundary is limited to import markers and the three runtime structural checks;
it does not introduce nominal combatant fallbacks, Protocol metaclass
emulation, global type patching, source transformation, or a bootstrap
redesign. The next gate must be derived from the observed
`battle_session.py` syntax failure.

## MPY12 - Portable Starred Tuple Expressions

MPY12 advances the pinned MicroPython qualification past the parser failure
recorded at MPY11. The baseline was:

```text
MPY11 sealed SHA: bd7726bb7d73cb7d2c3967071828de05ebdc72a9
MicroPython: v1.29.0
Source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Platform: win32
```

The previous raw-probe frontier was:

```text
MPY|BATTLE_CONSTRUCTION|FAIL|SyntaxError|*x must be assignment target
```

The pinned parser rejects a load-context starred tuple display such as:

```python
return (*entries, self._transient_rejection)
```

This is a presentation-only tuple assembly convenience. It is not a general
restriction on every use of `*`.

### Complete production audit

The pre-change AST census scanned only `root/src/app/**/*.py` and found nine
load-context starred tuple displays across four files:

```text
app.presentation.battle_session: 1
app.presentation.character_profile_presenter: 1
app.ui.terminal_battle_ui: 4
app.ui.terminal_overworld_ui: 3
```

The audit classifies every `ast.Starred` occurrence by context. It separately
recognizes tuple-display loads, function-call arguments, assignment targets,
comprehension or `for` targets, list displays, set displays, and other
contexts. The permanent invariant is only:

```text
unsupported production load-context starred tuple displays: 0
```

Other forms are classified but are not declared MicroPython-compatible by
this gate and are not mechanically rewritten.

### Source correction

All nine tuple-display occurrences now use ordinary tuple construction. The
replacement pattern is:

```python
(*values, final_value)
    -> tuple(values) + (final_value,)

("prefix", *values)
    -> ("prefix",) + tuple(values)

("prefix", *values_a, *values_b)
    -> ("prefix",) + tuple(values_a) + tuple(values_b)
```

The corrections preserve tuple result types, evaluation order, multiplicity,
presentation ordering, conditional behavior, and snapshot isolation. No
unpacking compatibility layer, runtime source transformation, tuple wrapper,
bootstrap change, or raw-probe change was added.

### Qualification evidence

The direct pinned-runtime syntax qualification recorded:

```text
entries = (1, 2)
value = 3
result = (*entries, value)
    -> SyntaxError: *x must be assignment target

result = entries + (value,)
    -> (1, 2, 3)
entries
    -> (1, 2)
type(result) is tuple
    -> True
```

The semantic regression suite covers empty history, retained history order,
transient rejection placement and replacement, bounded-history behavior,
snapshot isolation, tuple results, and unchanged list-backed internal state.
The four changed presentation surfaces are protected by their existing
character-profile and terminal UI tests:

```text
MPY12 presentation and syntax-focused tests: 109 passed
MPY12 cumulative portability and presentation suite: 222 passed
Full DD suite: 1,383 passed
```

Native CPython and the isolated forced-overlay CPython raw probes both reach
`MPY|RESULT|RAW_PROBE_STAGES_COMPLETE`.

The direct pinned-MicroPython qualification imported
`battle_session` and `character_profile_presenter` successfully, then
reached the next unrelated dependency while importing `terminal_battle_ui`:

```text
ImportError: no module named 'shutil'
```

This stopped that direct terminal-module qualification without stubbing or
repairing the unrelated standard-library boundary. `terminal_overworld_ui`
was not forced past that same frontier.

The unchanged raw probe through the complete MPY compatibility bootstrap
crosses all nine starred tuple displays. Its first unrelated frontier is now
in Battle view construction:

```text
MPY|BATTLE_CONSTRUCTION|PASS
MPY|BATTLE_VIEW|FAIL|TypeError|function doesn't take keyword arguments
MPY|MEMORY|BATTLE_VIEW|FAIL|FREE|711808|ALLOC|312704
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|55
MPY|DATACLASS|CONSTRUCTED|18
```

The original traceback is preserved:

```text
Traceback (most recent call last):
File "root/tools/micropython_probe_bootstrap.py", line 116, in <module>
File "root/tools/micropython_probe_bootstrap.py", line 109, in main
File "<string>", line 262, in <module>
File "<string>", line 250, in main
File "<string>", line 25, in _run_stage
File "<string>", line 112, in _obtain_first_battle_view
File "root/src/app/combat/battle.py", line 174, in current_view
File "root/src/app/combat/battle.py", line 413, in _build_view
File "root/src/app/presentation/battle_presenter.py", line 92, in build
TypeError: function doesn't take keyword arguments
```

All prior raw stages through `BATTLE_CONSTRUCTION` pass. MPY12 does not
repair this next keyword-argument limitation or speculate about MPY13.

### Scope and release result

```text
root/src production files changed: 4
starred tuple-display corrections: 9
semantic behavior changed: 0
gameplay behavior changed: 0
presentation contract changed: 0
content changed: 0
persistence or save schema changed: 0
semantic API changed: 0
raw probe changed: 0
bootstrap changed: 0
compatibility overlays changed: 0
historical docs/mpy changed: 0
```

The next gate is derived from the observed `BattleView` construction failure.

## MPY13 - Repair Portable Strict Zip Boundary

MPY13 advances the pinned MicroPython qualification past the `BattleView`
failure recorded at the sealed MPY12 baseline:

```text
MPY12 sealed SHA: d421a5b7bbfb5f39006983d01b66818de6aea7c0
MicroPython: v1.29.0
Source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Platform: win32
```

The previous raw-probe frontier was:

```text
MPY|BATTLE_CONSTRUCTION|PASS
MPY|BATTLE_VIEW|FAIL|TypeError|function doesn't take keyword arguments
MPY|MEMORY|BATTLE_VIEW|FAIL|FREE|711808|ALLOC|312704
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|55
MPY|DATACLASS|CONSTRUCTED|18
```

### Strict-zip capability evidence

The pinned MicroPython runtime directly produced:

```text
tuple(zip((1, 2), (3, 4), strict=True))
    -> TypeError: function doesn't take keyword arguments

tuple(zip((1, 2), (3, 4), strict=False))
    -> TypeError: function doesn't take keyword arguments

tuple(zip((1, 2), (3, 4)))
    -> ((1, 3), (2, 4))
```

Native CPython provided the semantic reference:

```text
tuple(zip((1, 2), (3,), strict=True))
    -> ValueError: zip() argument 2 is shorter than argument 1

tuple(zip((1, 2), (3,)))
    -> ((1, 3),)
```

Native strict zip prevents silent truncation for mismatched inputs. The audit
therefore checked every production strict-zip invariant before permitting the
keyword to be removed.

### Complete production audit

The dynamic AST census scanned only `root/src/app/**/*.py` and found:

```text
total production zip calls:           5
zip calls with strict keyword:        5
zip(..., strict=True):                5
zip(..., strict=False):               0
zip(..., strict=<expression>):        0
ordinary production zip calls:        0
other calls with strict keyword:      0
```

The five calls are:

```text
app.combat.battle:307
    Battle._display_name_for
app.combat.battle:697
    Battle._enemy_for_target_id
app.presentation.battle_presenter:92
    BattlePresenter.build
app.presentation.battle_presenter:547
    BattlePresenter._target_options
app.ui.terminal_battle_ui:286
    TerminalBattleUI._enemy_side_lines
```

All five direct `zip` names resolve to builtin `zip`. The production AST has
no local binding, definition, parameter, import, alias, assignment,
`builtins.zip` replacement, or module-state monkey patch for `zip`.

### Invariant classifications

```text
Battle._display_name_for
    REDUNDANT_BY_CONSTRUCTION
    _enemies and _enemy_display_labels are fixed tuples created from the
    same normalized enemy tuple during Battle.__init__.

Battle._enemy_for_target_id
    REDUNDANT_BY_CONSTRUCTION
    enemy_target_ids is generated with one entry for every enemy and both
    tuples have no supported mutation surface.

BattlePresenter.build
    REDUNDANT_BY_EXPLICIT_VALIDATION
    _metadata_values() validates supplied metadata tuple lengths before the
    three-way zip; defaults are generated from len(enemies).

BattlePresenter._target_options
    REDUNDANT_BY_CONSTRUCTION
    enemy_views is produced immediately beforehand with one view per
    validated enemy.

TerminalBattleUI._enemy_side_lines
    REDUNDANT_BY_CONSTRUCTION
    enemy_blocks and widths are both derived from participant_count, and
    width distribution changes values without changing list length.

ACTIVE_VALIDATION: 0
UNCERTAIN: 0
```

The presenter’s existing validation remains authoritative:

```text
enemy_target_ids length mismatch
    -> ValueError: enemy_target_ids must align with enemies

enemy_display_labels length mismatch
    -> ValueError: enemy_display_labels must align with enemies
```

### Source correction and regression evidence

The five unsupported keywords were removed from the three audited production
modules. No portable zip helper, iterator emulation, builtin replacement,
bootstrap change, or source transformation was added:

```text
strict-keyword production zip calls: 5 -> 0
```

The permanent AST contract targets only direct builtin-name `zip(...)` calls
and rejects a `strict` keyword of any value. It does not reject ordinary zip,
unrelated keyword calls, attribute calls such as `obj.zip(...)`, tooling, or
tests. Presenter regression tests prove both existing metadata mismatch
messages remain unchanged.

Existing behavioral tests continue to protect target-ID stability,
duplicate-name numbering, identity-preserving multi-enemy views,
target-option association, four-enemy terminal layout, and the Counter-based
label equivalence oracle.

### Qualification results

The native CPython raw probe and forced-overlay CPython raw probe both reach:

```text
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

The focused MPY13 contract and presenter regression tests pass:

```text
MPY13 focused tests: 23 passed
Cumulative portability suite: 194 passed
Full DD suite: 1,387 passed
```

The unchanged pinned MicroPython probe now reports:

```text
MPY|BATTLE_CONSTRUCTION|PASS
MPY|BATTLE_VIEW|PASS
MPY|BATTLE_INPUT|PASS
MPY|BATTLE_COMPLETE|PASS
MPY|SESSION_IMPORT|FAIL|ImportError|no module named 'tempfile'
MPY|MEMORY|SESSION_IMPORT|FAIL|FREE|708720|ALLOC|315792
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|55
MPY|DATACLASS|CONSTRUCTED|28
```

The last passing stage is `BATTLE_COMPLETE`. The next unrelated frontier is
the concrete persistence import closure used by `OverworldSession`:

```text
Traceback (most recent call last):
  File "root\\tools\\micropython_probe_bootstrap.py", line 116, in <module>
  File "root\\tools\\micropython_probe_bootstrap.py", line 109, in main
  File "<string>", line 262, in <module>
  File "<string>", line 253, in main
  File "<string>", line 25, in _run_stage
  File "<string>", line 166, in _import_overworld_session
  File "C:\\Users\\User\\Documents\\Dev\\Python\\Dungeon Drifters/root\\src/app/game/overworld_session.py", line 15, in <module>
  File "C:\\Users\\User\\Documents\\Dev\\Python\\Dungeon Drifters/root\\src/app/game/save_repository.py", line 5, in <module>
ImportError: no module named 'tempfile'
```

MPY13 does not repair `tempfile`, persistence, or the separately deferred
terminal `shutil` boundary.

### Scope and release result

```text
root/src production files changed: 3
strict zip keyword removals: 5
semantic behavior changed: 0
gameplay behavior changed: 0
content changed: 0
persistence changed: 0
save schema changed: 0
semantic API changed: 0
raw probe changed: 0
bootstrap changed: 0
compatibility overlays changed: 0
historical docs/mpy changed: 0
```

MPY14 is derived only from the new `SESSION_IMPORT` failure at `tempfile`.

## MPY14 - Decouple Session Persistence Import Boundary

MPY13 was sealed at:

```text
cc66563cd94c442ca4b1a95afbe09d1dca3a4828
```

The unchanged pinned MicroPython probe had reached:

```text
BATTLE_CONSTRUCTION: PASS
BATTLE_VIEW: PASS
BATTLE_INPUT: PASS
BATTLE_COMPLETE: PASS
SESSION_IMPORT: FAIL
ImportError: no module named 'tempfile'
```

The failure was caused by `OverworldSession` eagerly importing and
constructing the concrete disk `SaveRepository`. That adapter imports
`tempfile`, `pathlib`, JSON, and filesystem persistence machinery. The
session itself only needs the status/error types and the injected repository
method contract during ordinary headless gameplay.

### Persistence boundary correction

MPY14 added the lightweight `app.game.save_contract` module containing:

```text
SaveLoadStatus
SaveRepositoryError
is_save_repository(value)
```

`is_save_repository()` uses the existing structural contract helper and
requires callable `save`, `inspect`, and `load` members. The concrete
`SaveRepository` remains the host disk adapter. `save_repository.py` imports
and re-exports the moved status and error types through its existing
`__all__`, so legacy imports remain identical.

`OverworldSession` now imports only the lightweight contract at module scope.
When `save_repository` is `None`, the value remains unresolved until an
actual persistence boundary calls `_save_repository_instance()`. The local
import constructs the same default `SaveRepository` exactly once. MAIN views,
encounter creation, battle finalization, rests, and ordinary session
construction do not resolve it. Explicit structural repository injection
continues to bypass the default adapter.

This is not SAVE-ARCH. MPY14 adds no backend, save schema, payload shape,
filesystem overlay, `tempfile` shim, `pathlib` shim, or MicroPython-specific
gameplay branch. Save/load, atomic replacement, schema-7 migration reporting,
and schema-8 behavior remain owned by the existing concrete repository.

### Contract and regression evidence

The new boundary tests prove:

```text
None is not a repository
callable save/inspect/load members are accepted
missing or non-callable members are rejected
save_repository.py re-exports the exact contract types
default construction is lazy through initial current_view()
Options load availability constructs the default once and reuses it
injected repositories bypass the default constructor
overworld_session has no module-level save_repository import
```

The existing save repository, overworld session, runtime overworld, desktop
composition, save/load, quit/restart/load, atomic-write, and migration tests
remain part of the verification set.

### Runtime evidence

The independent pinned MicroPython preflight still reports:

```text
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ImportError: no module named 'tempfile'
```

This confirms MPY14 crossed an import boundary rather than repairing or
masking the unavailable filesystem module. The lightweight contract import
passes:

```text
SAVE_CONTRACT|PASS
```

With the existing regex and `collections.abc` setup applied, a direct
`OverworldSession` import now reaches the next unrelated dependency:

```text
ImportError: no module named 'itertools'
```

The traceback identifies the first post-MPY14 frontier as:

```text
app.game.overworld_session
  -> app.presentation.overworld_presenter
  -> from itertools import groupby
```

No `itertools` repair is included in MPY14. Because session import stops at
this unrelated wall, direct session construction and initial view are not
claimed beyond the point proven by the unchanged raw probe.

The unchanged pinned MicroPython raw probe reports:

```text
MPY|BOOT|PASS
MPY|IMPLEMENTATION|micropython
MPY|VERSION|1.29.0
MPY|PLATFORM|win32
MPY|SESSION_IMPORT|BEGIN
MPY|SESSION_IMPORT|FAIL|ImportError|no module named 'itertools'
MPY|MEMORY|SESSION_IMPORT|FAIL|FREE|689632|ALLOC|334880
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|70
MPY|DATACLASS|CONSTRUCTED|28
```

The last passing stage is `BATTLE_COMPLETE`. `SESSION_IMPORT` itself begins
and then fails at the next unrelated `itertools` dependency. The original
traceback was:

```text
Traceback (most recent call last):
  File "root/tools/micropython_probe_bootstrap.py", line 116, in <module>
  File "root/tools/micropython_probe_bootstrap.py", line 109, in main
  File "<string>", line 262, in <module>
  File "<string>", line 253, in main
  File "<string>", line 25, in _run_stage
  File "<string>", line 166, in _import_overworld_session
  File "C:\\Users\\User\\Documents\\Dev\\Python\\Dungeon Drifters/root/src/app/game/overworld_session.py", line 27, in <module>
  File "C:\\Users\\User\\Documents\\Dev\\Python\\Dungeon Drifters/root/src/app/presentation/overworld_presenter.py", line 3, in <module>
ImportError: no module named 'itertools'
```

For comparison, native CPython and the forced-overlay CPython bootstrap both
still complete every unchanged raw-probe stage. The forced-overlay bootstrap
also emitted its normal dynamic census after completion:

```text
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|73
MPY|DATACLASS|CONSTRUCTED|33
```

The final CPython verification totals are:

```text
Full DD suite: 1,404 passed
Cumulative MPY13 plus MPY14 suite: 233 passed
```

### Scope and release result

```text
root/src production files changed: 3
  root/src/app/game/save_contract.py
  root/src/app/game/save_repository.py
  root/src/app/game/overworld_session.py
new focused test files: 2
  root/tests/test_save_contract.py
  root/tests/test_session_persistence_boundary.py
gameplay behavior changed: 0
content changed: 0
persistence semantics changed: 0
save schema changed: 0
save payload changed: 0
semantic API changed: 0
bootstrap changed: 0
raw probe changed: 0
filesystem compatibility layers added: 0
historical docs/mpy changes: 0
```

MPY15 is derived only from the new `itertools` frontier. Historical
`docs/mpy/` files remain untracked, untouched, and uncommitted.

## MPY15 - Remove Itertools Groupby Runtime Dependency

MPY14 was sealed at:

```text
3af2e4d2da435f29b6559f087aeb0a705cbe0fd0
```

Its unchanged pinned MicroPython probe reached:

```text
BATTLE_COMPLETE: PASS
SESSION_IMPORT: FAIL
ImportError: no module named 'itertools'
```

The failure came from the eager import chain:

```text
app.game.overworld_session
  -> app.presentation.overworld_presenter
  -> from itertools import groupby
```

### Production audit

The pre-edit AST census was dynamically restricted to `root/src/app/**/*.py`
and found:

```text
production itertools imports: 1
imported member: groupby
groupby calls: 1
production files: 1
```

The single site was:

```text
root/src/app/presentation/overworld_presenter.py
OverworldPresenter._map_encounter_inspection_view
```

The test and tooling trees were excluded from this runtime census. The
operation was adjacent-run grouping, not global counting. For example:

```text
("goblin", "goblin", "warrior", "goblin")
-> (("goblin", 2), ("warrior", 1), ("goblin", 1))
```

### Source correction

MPY15 removed the production `itertools` import and added the private
`_adjacent_run_counts(values)` helper in the same presenter module. It uses
ordinary tuple/list operations to preserve contiguous run boundaries and
authored order. It does not implement or add an `itertools` compatibility
module.

The production census after the correction is:

```text
production itertools imports: 0
production groupby calls: 0
```

The permanent `test_itertools_contract.py` audit enforces zero production
imports dynamically and separately verifies that unrelated imports and
test-only CPython `itertools` usage remain outside the boundary.

### Semantic evidence

The test-only CPython `groupby` oracle agrees with `_adjacent_run_counts()` for
empty input, singleton input, adjacent duplicates, separated duplicates,
alternating values, and multiple duplicate groups. Existing authored map
inspection tests remain green for all surface encounters, including Goblin
Pair, Warrior Patrol, Elite Patrol, Goblin Lord, rest-node lookahead, boss
state, immutable output, non-mutating inspection, and no runtime enemy
construction.

The helper qualification under pinned MicroPython produced:

```text
()
(('a', 1),)
(('a', 2), ('b', 1), ('a', 1))
```

### Pinned runtime evidence

The independent preflights confirm that the runtime lacks the module itself:

```text
import itertools
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ImportError: no module named 'itertools'

from itertools import groupby
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ImportError: no module named 'itertools'
```

The unchanged pinned MicroPython bootstrap probe reports:

```text
MPY|BOOT|PASS
MPY|IMPLEMENTATION|micropython
MPY|VERSION|1.29.0
MPY|PLATFORM|win32
MPY|SESSION_IMPORT|PASS
MPY|SESSION_CONSTRUCTION|PASS
MPY|SESSION_VIEW|FAIL|TypeError|function takes 1 positional arguments but 2 were given
MPY|MEMORY|SESSION_VIEW|FAIL|FREE|672400|ALLOC|352112
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|73
MPY|DATACLASS|CONSTRUCTED|28
```

The last passing stage is `SESSION_CONSTRUCTION`. The next frontier is a new,
unrelated `SESSION_VIEW` failure. The original traceback is preserved:

```text
Traceback (most recent call last):
  File "root\\tools\\micropython_probe_bootstrap.py", line 116, in <module>
  File "root\\tools\\micropython_probe_bootstrap.py", line 109, in main
  File "<string>", line 262, in <module>
  File "<string>", line 255, in main
  File "<string>", line 25, in _run_stage
  File "<string>", line 183, in _obtain_session_view
  File "C:\\Users\\User\\Documents\\Dev\\Python\\Dungeon Drifters/root/src/app/game/overworld_session.py", line 134, in current_view
  File "C:\\Users\\User\\Documents\\Dev\\Python\\Dungeon Drifters/root/src/app/game/overworld_session.py", line 279, in _build_view
  File "C:\\Users\\User\\Documents\\Dev\\Python\\Dungeon Drifters/root/src/app/presentation/overworld_presenter.py", line 81, in build
TypeError: function takes 1 positional arguments but 2 were given
```

MPY15 does not investigate or repair this `SESSION_VIEW` frontier. It is the
MPY16 starting point.

Native CPython and the forced-overlay CPython bootstrap both report:

```text
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

The verification totals are:

```text
Full DD suite: 1,415 passed
MPY15 cumulative portability suite: 259 passed
MPY15 helper/audit focus: 26 passed
```

### Scope and release result

```text
root/src production files changed: 1
  root/src/app/presentation/overworld_presenter.py
production itertools imports: 1 -> 0
production groupby calls: 1 -> 0
gameplay behavior changed: 0
content or encounter definitions changed: 0
route or session state changed: 0
persistence or save schema changed: 0
semantic APIs changed: 0
bootstrap changed: 0
raw probe changed: 0
itertools compatibility overlay added: 0
historical docs/mpy changes: 0
```

MPY15 adds no authored encounter composition changes and no gameplay or
session-state changes. Historical `docs/mpy/` files remain untracked,
untouched, and uncommitted.

## MPY16 - Repair Portable Next Default Boundary

MPY15 was sealed at:

```text
133846f6b15b0ea3ed2153af69b104a0945b3fcf
```

Its unchanged pinned MicroPython probe had reached:

```text
SESSION_IMPORT: PASS
SESSION_CONSTRUCTION: PASS
SESSION_VIEW: FAIL
TypeError: function takes 1 positional arguments but 2 were given
```

The traceback terminated at `OverworldPresenter.build()` while evaluating
the selected-inventory-item lookup with `next(..., None)`. The pinned
MicroPython Windows runtime exposes the one-argument `next()` implementation;
the two-argument form is available only when `MICROPY_PY_BUILTINS_NEXT2` is
enabled. MPY16 did not enable that feature or rebuild the interpreter.

### Root-cause evidence

The direct pinned preflight produced:

```text
iterator = iter(("value",))
next(iterator)
-> value

iterator = iter(("value",))
next(iterator, None)
-> TypeError: function takes 1 positional arguments but 2 were given

next(iter(()), None)
-> TypeError: function takes 1 positional arguments but 2 were given
```

This confirms that the failure is the built-in default-value arity surface,
not generator behavior, presenter state, dataclasses, or session state.

### Production audit and correction

The pre-edit AST census was dynamically restricted to `root/src/app/**/*.py`.
It found exactly eight direct `next()` calls with two positional arguments,
all using `None` as the default, across five existing production files:

```text
root/src/app/presentation/overworld_presenter.py: selected inventory item
root/src/app/presentation/battle_presenter.py: selected move
root/src/app/player/run_items.py: run-item definition and recipe pair
root/src/app/player/inventory_action.py: recipe for action
root/src/app/game/overworld_session.py: previous, current, and selected stat rows
```

The permanent AST contract excludes test and tooling code and enforces the
runtime invariant that direct production `next()` calls with two or more
positional arguments remain absent.

MPY16 added `root/src/app/iteration.py` with the deliberately narrow
`first_or_none(values)` primitive. It returns the first yielded value or
`None` when the iterable is exhausted, without materializing the iterable or
consuming a second value. All eight callers now use this primitive while
preserving authored order, first-match selection, falsey values, short
circuiting, and non-`StopIteration` exception propagation.

The post-edit census is:

```text
direct production next() calls with >= 2 positional arguments: 0
two-argument calls: 8 -> 0
```

### Semantic and regression evidence

The contract suite compares `first_or_none()` against native CPython
`next(iter(values), None)` for empty, `None`, zero, false, empty-string,
single-value, and multi-value inputs. It also proves first-value laziness and
propagation of non-`StopIteration` exceptions. Existing presenter, inventory,
and session tests remain authoritative for all eight consumers and remain
green.

### Direct pinned qualification

The direct pinned MicroPython qualification produced:

```text
None
0
a
```

The direct two-argument preflight still fails after MPY16:

```text
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: function takes 1 positional arguments but 2 were given
```

This is intentional evidence that DD changed its own required runtime
surface instead of patching `builtins.next` or changing MicroPython.

### Raw probe result

Native CPython and the forced-overlay CPython bootstrap both still report:

```text
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

The unchanged pinned MicroPython bootstrap probe now reports:

```text
MPY|BOOT|PASS
MPY|IMPLEMENTATION|micropython
MPY|VERSION|1.29.0
MPY|PLATFORM|win32
MPY|BATTLE_CONSTRUCTION|PASS
MPY|BATTLE_VIEW|PASS
MPY|BATTLE_INPUT|PASS
MPY|BATTLE_COMPLETE|PASS
MPY|SESSION_IMPORT|PASS
MPY|SESSION_CONSTRUCTION|PASS
MPY|SESSION_VIEW|PASS
MPY|SESSION_ENCOUNTER_ENTRY|FAIL|TypeError|rng must provide randint
MPY|MEMORY|SESSION_ENCOUNTER_ENTRY|FAIL|FREE|671840|ALLOC|352672
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|73
MPY|DATACLASS|CONSTRUCTED|33
```

The last passing stage is `SESSION_VIEW`. The next unrelated frontier is
`SESSION_ENCOUNTER_ENTRY`, where the existing deterministic route driver
reaches a battle construction path requiring an RNG with `randint`. MPY16
does not investigate or repair that frontier; it is the MPY17 starting point.

The original traceback is preserved:

```text
Traceback (most recent call last):
  File "root\\tools\\micropython_probe_bootstrap.py", line 116, in <module>
  File "root\\tools\\micropython_probe_bootstrap.py", line 109, in main
  File "<string>", line 262, in <module>
  File "<string>", line 256, in main
  File "<string>", line 25, in _run_stage
  File "<string>", line 197, in _enter_first_session_encounter
  File "C:\\Users\\User\\Documents\\Dev\\Python\\Dungeon Drifters/root/src/app/game/overworld_session.py", line 185, in submit
  File "C:\\Users\\User\\Documents\\Dev\\Python\\Dungeon Drifters/root/src/app/game/overworld_session.py", line 517, in _create_active_battle
  File "C:\\Users\\User\\Documents\\Dev\\Python\\Dungeon Drifters/root/src/app/combat/battle.py", line 76, in __init__
TypeError: rng must provide randint
```

### Scope and release result

```text
new portable production helper: 1
existing production consumer files changed: 5
production next() calls with two arguments: 8 -> 0
builtins patching: 0
MicroPython source changes: 0
interpreter feature changes: 0
bootstrap changes: 0
raw probe changes: 0
gameplay or session-state changes: 0
content or route changes: 0
persistence or save-schema changes: 0
historical docs/mpy changes: 0
```

MPY16 does not enable `MICROPY_PY_BUILTINS_NEXT2`, patch `builtins.next`,
add interpreter detection, alter first-match semantics, or change gameplay or
session state. Historical `docs/mpy/` files remain untracked, untouched, and
uncommitted.

## MPY17 - Repair Portable Runtime Random Boundary

MPY16 was sealed at:

```text
dbc1da7586f209837aede5b04c670aa830e62f62
```

Its final session stages were:

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

The traceback path was:

```text
OverworldSession.submit()
-> OverworldSession._create_active_battle()
-> Battle(...)
-> Battle.__init__()
-> default RNG validation
-> TypeError: rng must provide randint
```

The standalone Battle qualification injected a deterministic RNG, while the
session path used Battle's default `random` object. The pinned MicroPython
random module exposes `getrandbits` but not the convenience functions required
by the combat runtime:

```text
getrandbits: True
randint:     False
choice:      False
randrange:   False
```

An independent pinned-runtime call to `random.getrandbits(8)` returned an
`int` in the inclusive range `0..255`. This is the available primitive. The
upstream boundary is `MICROPY_PY_RANDOM_EXTRA_FUNCS`: the Windows standard
build enables `MICROPY_PY_RANDOM` without enabling the extra `randint`,
`choice`, and `randrange` functions. MPY17 does not rebuild MicroPython or
enable that feature.

### Production random census

The pre-edit AST census was dynamically restricted to `root/src/app/**/*.py`.
It found exactly three direct standard-library `random` imports:

```text
root/src/app/combat/battle.py
root/src/app/combat/resolver.py
root/src/app/world/event.py
```

The two combat imports were the sealed runtime surface:

```text
Battle:          randint, choice
CombatResolver:  randint
```

No combat code required `random`, `uniform`, `shuffle`, `sample`, or
`randrange`. `world/event.py` remains a separate legacy/terminal path and was
not changed in MPY17.

### Portable adapter

MPY17 added `root/src/app/randomness.py` and changed only the combat imports
in `battle.py` and `resolver.py` to use `app.randomness as random`. The adapter
performs capability lookup at call time, delegates to native
`random.randint` and `random.choice` when available, and otherwise derives
the required operations from `getrandbits` using rejection sampling. It does
not use modulo reduction, materialize choice sequences, cache patched native
functions, detect MicroPython, replace `sys.modules`, or patch builtins.

The contract tests cover native delegation, rejected candidates, inclusive
`randint` ranges, empty choices, missing `getrandbits`, default Battle and
CombatResolver wiring, and the combat-only AST import boundary. The fallback
preserves the existing injected-RNG API and the existing CPython monkeypatch
patterns.

The post-edit census is:

```text
core combat direct stdlib random imports: 2 -> 0
whole-app direct stdlib random imports:    3 -> 2
remaining direct stdlib imports:
  root/src/app/randomness.py
  root/src/app/world/event.py
```

### Qualification results

The direct CPython adapter qualification passed:

```text
RANDOMNESS|CPYTHON|PASS
```

The direct pinned MicroPython qualification passed while native convenience
functions remained unavailable:

```text
NATIVE True False False
7
only
MPY_RANGE True
MPY_CHOICE True
RANDOMNESS|MPY|PASS
```

Both native CPython and forced-overlay CPython raw probes continued to reach:

```text
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

The unchanged pinned MicroPython probe now reaches every current stage:

```text
MPY|IMPLEMENTATION|micropython
MPY|VERSION|1.29.0
MPY|PLATFORM|win32
MPY|BATTLE_CONSTRUCTION|PASS
MPY|BATTLE_VIEW|PASS
MPY|BATTLE_INPUT|PASS
MPY|BATTLE_COMPLETE|PASS
MPY|SESSION_IMPORT|PASS
MPY|SESSION_CONSTRUCTION|PASS
MPY|SESSION_VIEW|PASS
MPY|SESSION_ENCOUNTER_ENTRY|PASS
MPY|SESSION_ENCOUNTER_COMPLETE|PASS
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
MPY|DATACLASS|EXPECTED|74
MPY|DATACLASS|DECORATED|73
MPY|DATACLASS|CONSTRUCTED|33
```

The session-entry memory evidence after the adapter was installed was:

```text
MPY|MEMORY|SESSION_ENCOUNTER_ENTRY|AFTER|FREE|668112|ALLOC|356400
MPY|MEMORY|SESSION_ENCOUNTER_COMPLETE|AFTER|FREE|669536|ALLOC|354976
```

There is no post-MPY17 failure traceback: the previous `rng must provide
randint` failure is crossed and the raw probe completes. The native
MicroPython `random.randint` and `random.choice` functions remain absent;
DD's adapter supplies only the qualified runtime surface.

### Verification and scope

The full CPython suite passed `1,440` tests. The exact cumulative MPY16 suite
plus MPY17 random contract and combat regressions passed `519` tests. The
random-focused qualification subset passed `175` tests. Compileall,
dataclass-manifest freshness, and `git diff --check` were also run after the
implementation.

```text
new portable random adapter:          1
existing production files modified:   2
core combat stdlib random imports:     2 -> 0
whole-app stdlib random imports:       3 -> 2
MicroPython source/config changes:     0
builtins patches:                      0
sys.modules random overlays:           0
interpreter detection:                 0
OverworldSession changes:              0
raw probe/bootstrap changes:           0
gameplay rule changes:                 0
content, route, persistence/schema:    0
historical docs/mpy changes:           0
```

MPY17 does not enable `MICROPY_PY_RANDOM_EXTRA_FUNCS`, replace MicroPython's
random module, patch builtins or `sys.modules`, add interpreter detection, or
change combat probabilities and gameplay rules. Historical `docs/mpy/` files
remain untracked, untouched, and uncommitted.

## MPY18 - Full Surface Route Qualification

MPY17 was sealed at:

```text
4ac69098c173d7fecbd590eb329c3222af00876b
MPY17 - Repair Portable Runtime Random Boundary
```

Its real default session path completed the first encounter and reached:

```text
SESSION_ENCOUNTER_ENTRY     PASS
SESSION_ENCOUNTER_COMPLETE  PASS
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

MPY18 changed no production source. It extended the qualification artifact
after the sealed stages, using a fresh Branoc game and fresh headless
`OverworldSession` for the full authored route. The route driver uses the
real session, `Battle`, `EnemyState`, `BattlePresenter`, and
`BattlePresentationSession` objects. Its only deterministic pieces are a
probe-local Battle factory, resolver, and RNG so this gate measures route
orchestration and progression rather than combat-balance randomness.

MPY17 already qualified the real default session Battle, RNG adapter, and
CombatResolver path. MPY18 therefore uses deterministic combat to make all
eight encounters finish through the semantic Battle view/input contract:
actions, enabled moves, and enabled targets. It does not claim statistically
representative combat balance under MicroPython.

### Route oracle

The live authored route and the CPython qualification oracle agree on exactly
12 nodes, 8 encounters, 3 Rests, 1 boss, and `surface_dungeon_entrance` as
the terminal node:

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

Encounter IDs:

```text
surface_goblin_solo
surface_goblin_pair
surface_warrior_solo
surface_warrior_pair
surface_shaman_solo
surface_shaman_pair
surface_elite_patrol
surface_goblin_lord
```

Rest IDs:

```text
surface_rest_after_warrior_solo
surface_rest_after_shaman_pair
surface_rest_before_goblin_lord
```

Encounter compositions remained authored and unchanged:

```text
(goblin)
(goblin, goblin)
(goblin_warrior)
(goblin_warrior, goblin_warrior)
(goblin_shaman)
(goblin_shaman, goblin_shaman)
(goblin_elite, goblin)
(goblin_lord, goblin, goblin_warrior)
```

The route probe asserts each immediate successor, encounter and Rest prefix,
semantic action flow, exactly-once encounter finalization, fresh enemy
identity, final progression, and final route state. It does not visit the
Options screen and keeps `save_repository=None`; the lazy disk repository
remained unmaterialized.

### Route results

Native CPython, forced-overlay CPython, and pinned MicroPython all passed the
sealed MPY17 stage prefix, all 12 route nodes, `SURFACE_ROUTE_COMPLETE`, and
`ROUTE_FINAL_STATE`, ending with:

```text
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

The route markers were:

```text
MPY|ROUTE|surface_goblin_solo|PASS
MPY|ROUTE|surface_goblin_pair|PASS
MPY|ROUTE|surface_warrior_solo|PASS
MPY|ROUTE|surface_rest_after_warrior_solo|PASS
MPY|ROUTE|surface_warrior_pair|PASS
MPY|ROUTE|surface_shaman_solo|PASS
MPY|ROUTE|surface_shaman_pair|PASS
MPY|ROUTE|surface_rest_after_shaman_pair|PASS
MPY|ROUTE|surface_elite_patrol|PASS
MPY|ROUTE|surface_rest_before_goblin_lord|PASS
MPY|ROUTE|surface_goblin_lord|PASS
MPY|ROUTE|surface_dungeon_entrance|PASS
```

Pinned MicroPython final state:

```text
encounters defeated:       8
Rests resolved:            3
fresh EnemyState objects: 14
Battle instances:          8
boss:                      Goblin Lord
current route node:        surface_dungeon_entrance
route_complete:            True
dungeon_entrance_reached:  True
active_battle:             None
level:                     9
EXP:                       68
growth points:             24
gold:                      75
save repository:           not materialized
```

Every recorded Battle reached `InteractionPhase.COMPLETE`, all fourteen
EnemyState objects were distinct by identity, and the final view was MAIN
with no contextual route action.

### Route memory evidence

Pinned MicroPython emitted the following per-node memory observations. Values
are `FREE / ALLOC` bytes; no MPY18 threshold was applied.

```text
ROUTE_CONSTRUCTION                 646656/377856 -> 644816/379696
ROUTE_INITIAL_VIEW                 644816/379696 -> 644384/380128
surface_goblin_solo                644272/380240 -> 641824/382688
surface_goblin_pair                641808/382704 -> 638624/385888
surface_warrior_solo               638608/385904 -> 636272/388240
surface_rest_after_warrior_solo    636272/388240 -> 636256/388256
surface_warrior_pair               636256/388256 -> 633008/391504
surface_shaman_solo                633008/391504 -> 630592/393920
surface_shaman_pair                630576/393936 -> 627360/397152
surface_rest_after_shaman_pair     627344/397168 -> 627408/397104
surface_elite_patrol               627408/397104 -> 624272/400240
surface_rest_before_goblin_lord    624272/400240 -> 624320/400192
surface_goblin_lord                624320/400192 -> 620432/404080
surface_dungeon_entrance           620416/404096 -> 620416/404096
ROUTE_FINAL_STATE                   620528/403984 -> 620512/404000
```

The lowest observed route `FREE` was `620416`; the highest observed route
`ALLOC` was `404096`. The final route-final-state measurement was
`FREE 620512 / ALLOC 404000`. The final dataclass census was:

```text
EXPECTED:    74
DECORATED:   73
CONSTRUCTED: 35
```

### Verification and scope

The full CPython suite passed `1,443` tests. The exact sealed MPY17
cumulative portability suite plus MPY18 route qualification coverage passed
`553` tests. Compileall passed for `root/src`, `root/tests`, `root/tools`,
and `root/portability`; the dataclass manifest remained current at 74
entries; and `git diff --check` was clean.

The permanent route-probe contract test checks the sealed MPY17 stage prefix,
the exact twelve-node oracle, eight encounters, three Rests, fourteen enemy
instances, final progression, final node, and the absence of filesystem or
test-framework dependencies in the raw probe.

```text
production source files changed:       0
gameplay code changed:                 0
combat rules changed:                  0
route/content changed:                 0
session implementation changed:        0
persistence/schema changed:            0
compatibility overlays changed:        0
bootstrap changed:                     0
MicroPython source/config changed:     0
new runtime compatibility primitive:   0
raw qualification horizon:             1 encounter -> full 12-node route
encounters qualified:                  8
Rests qualified:                        3
enemy instances qualified:             14
historical docs/mpy changes:           0
```

MPY18 is a qualification gate only. It adds no compatibility repair, does
not alter authored route/content, does not change gameplay or session state,
and does not import or instantiate desktop persistence during route traversal.
The meaning of `MPY|RESULT|RAW_PROBE_STAGES_COMPLETE` is now the expanded
full-route probe rather than only the MPY17 first-encounter horizon.

## MPY19 - Constrained Heap Pressure

MPY18 was sealed at:

```text
6eaafc416240b5344570e7dd7e349767f84538a5
MPY18 - Qualify Full Surface Route
```

MPY19 preserved the complete MPY18 evidence-retaining route through:

```text
ROUTE_CONSTRUCTION
ROUTE_INITIAL_VIEW
SURFACE_ROUTE_COMPLETE
ROUTE_FINAL_STATE
```

Only after `ROUTE_FINAL_STATE` passed did the probe release its deliberately
retained Battle and EnemyState evidence, validate the authoritative live game
and session state, tear down the route references, and emit the final result
marker. The marker now means the sealed MPY17 stages, the full MPY18 route,
MPY19 evidence release, and MPY19 route-session teardown all passed.

### Heap-control qualification

The pinned executable advertises:

```text
heapsize=<n>[w][K|M] -- set the heap size for the GC
```

The independent `-X heapsize=512K` preflight succeeded with:

```text
FREE:  511696
ALLOC: 560
```

The Python-visible total is `512256` bytes, which is below the requested
524288 bytes as expected from GC metadata and alignment. No MicroPython
rebuild or configuration change was used.

MPY19 distinguishes four observations:

```text
qualification peak     route complete while Battle/enemy evidence is retained
live route state        completed GameState/session after evidence release
warm residual           route/session released and GC collected
constrained heap floor  smallest repeatedly successful explicit heap
```

The approximately 1 MiB Windows qualification heap is not a PS5 memory
budget.

### Evidence release and teardown

The representative default pinned run recorded:

```text
ROUTE_CONSTRUCTION|BEFORE       FREE 643440 / ALLOC 381072
ROUTE_FINAL_STATE|AFTER         FREE 617296 / ALLOC 407216
ROUTE_EVIDENCE_RELEASE|AFTER    FREE 641312 / ALLOC 383200
ROUTE_SESSION_TEARDOWN|AFTER    FREE 643392 / ALLOC 381120
```

Evidence reclaimed:

```text
407216 - 383200 = 24016 bytes
```

Warm residual relative to the route-construction baseline was:

```text
381120 - 381072 = 48 bytes
```

The cleanup validated the completed route node, all 8 defeated encounters,
all 3 Rests, progression `9 / 68 / 24 / 75`, MAIN final view, no contextual
action, no active Battle, and an unmaterialized lazy SaveRepository. It did
not call the retained-evidence final-state assertion after clearing the
evidence. A nonzero warm residual is not classified as a leak; module imports,
qstr interning, and legitimate runtime caches may remain reachable.

### Heap sweep

The host-only `root/tools/micropython_heap_sweep.py` runs the pinned executable
without importing DD production modules. It uses `subprocess.run()` without a
shell, preserves each command and return code, parses the existing `MPY|...`
line protocol, and classifies each run as `PASS`, `MEMORY_LIMIT`, or
`UNEXPECTED_FAILURE`. MemoryError output is pressure evidence; semantic or
other runtime failures are not reclassified as memory limits.

The default and explicit 1024K control runs completed the full route. The
explicit 1024K control observed:

```text
BOOT:              FREE 972400 / ALLOC 52112
lowest FREE:       617152
highest ALLOC:     407360
ROUTE_FINAL_STATE: FREE 617248 / ALLOC 407264
EVIDENCE_RELEASE:  FREE 641264 / ALLOC 383248
TEARDOWN:          FREE 643344 / ALLOC 381168
```

The coarse sweep and 32K refinement were:

```text
requested heap   classification     lowest FREE   highest ALLOC
1024K            PASS               617152        407360
896K             PASS               489088        407360
768K             PASS               361024        407360
640K             PASS               232960        407360
512K             PASS               104896        407360
384K             MEMORY_LIMIT        74256         309936
256K             MEMORY_LIMIT        99840         156288
480K             PASS                72800        407392
448K             PASS                40832        407360
416K             MEMORY_LIMIT        53648        362544
```

The 384K run failed during `BATTLE_CONSTRUCTION`. The 256K run failed during
`CATALOG_IMPORT`. The nearest lower 416K run failed after `BATTLE_COMPLETE`
at `SESSION_IMPORT` with:

```text
MemoryError: memory allocation failed, allocating 2344 bytes
```

The 416K pressure run's observed census at failure was `74 / 70 / 28`.
The 448K run completed the full route in all three additional confirmations:

```text
MPY19|STABLE_PASS|448K|STABLE_PASS|3/3
MPY19|BOUNDARY|LOWER|416K|MEMORY_LIMIT|3/3
```

Therefore the smallest observed stable passing heap for this Windows
MicroPython qualification harness is `448K`, with a clean observed pressure
boundary at `416K`. No product threshold is being proposed, and no production
optimization was performed to lower the floor.

### Cross-runtime and verification results

Native CPython and forced-overlay CPython both passed:

```text
ROUTE_FINAL_STATE PASS
ROUTE_EVIDENCE_RELEASE PASS
ROUTE_SESSION_TEARDOWN PASS
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

Pinned MicroPython passed the same stages at default heap, explicit 1024K,
and every stable successful constrained heap listed above. The full CPython
suite passed `1453` tests. The focused MPY19 contract suite passed `13`
tests. The cumulative MPY18 suite plus MPY19 heap-sweep contract passed
`563` tests. Compileall, the 74-entry dataclass manifest check, and
`git diff --check` passed.

```text
production source changes:             0
gameplay/combat/route changes:         0
session/persistence/schema changes:    0
compatibility overlay changes:         0
bootstrap changes:                     0
MicroPython source/config changes:     0
qualification additions:               evidence release, teardown, heap sweep
historical docs/mpy changes:           0
final dataclasses:                      74 / 73 / 35
```

MPY19 is a runtime-health stress test. It is not a PS5 RAM budget, does not
model PS5 unified memory, and excludes native host, graphics, audio, assets,
SDK, and GPU memory. It does not imply that an embedded MicroPython VM should
receive the minimum passing heap observed here. A low-heap `MemoryError` is
not itself a gameplay defect. The observed floor includes the conservative
MPY18 workload with retained Battle/enemy evidence through
`ROUTE_FINAL_STATE`.

## Future Gates

```text
MPY0  Raw probe; find the first real incompatibility.
MPY1  First evidence-backed compatibility primitive.
MPY2  Qualify the portable dataclass contract.
MPY3  Portable dataclass field discovery and overlay; stop at enum.
MPY4  Portable StrEnum overlay; stop at keyword.
MPY5  Portable keyword boundary; stop at the next unrelated wall.
MPY6  Qualify the next evidence-derived compatibility frontier.
MPY7  Portable regex fullmatch boundary; stop at collections.abc.
MPY8  Portable collections.abc boundary; stop at str.isascii.
MPY9  Portable ASCII string validation; stop at the next unrelated wall.
MPY10 Next evidence-derived compatibility frontier.
MPY11 Portable typing and Protocol boundary; stop at battle_session.py syntax.
MPY12 Portable starred tuple expressions; stop at BattleView construction.
MPY13 Portable strict zip boundary; stop at the tempfile persistence edge.
MPY14 Session persistence import boundary; stop at itertools.
MPY15 Remove the itertools groupby dependency; stop at SESSION_VIEW.
MPY16 Derived only from the new SESSION_VIEW MicroPython failure.
MPY17 Portable runtime random boundary.
MPY18 Full surface route qualification.
MPY19 Constrained heap pressure qualification.
MPY20 Cross-runtime regression qualification and campaign closure: sealed.

No further nominal MPY gates are scheduled. Future qualification is
evidence-driven and triggered by material runtime or architecture changes.
```

Hardware-specific heap results remain separate from the Windows-port language/import qualification.

## Repository Verification

MPY13 verification was run from the nested `root/` project directory and
included the full suite, cumulative portability suite, compileall,
dataclass-manifest freshness, and `git diff --check`. Runtime verification
also included native CPython, forced-overlay CPython, the pinned strict-zip
preflights, and the unchanged pinned MicroPython bootstrap probe.

The expected tracked MPY13 changes are limited to:

```text
root/src/app/combat/battle.py
root/src/app/presentation/battle_presenter.py
root/src/app/ui/terminal_battle_ui.py
root/tests/test_battle_presenter.py
root/tests/test_strict_zip_contract.py
docs/portability/micropython-probe.md
```

No compatibility overlay, bootstrap, raw probe, generated metadata, save
schema, gameplay, content, or historical `docs/mpy/` file changed.

## MPY20 - Cross-Runtime Qualification Closure

MPY20 was executed from the sealed MPY19 baseline:

```text
896b1b39f24c0a35768f69d2394b124160c55c15
MPY19 - Qualify Constrained Heap Pressure
```

The closure tool is host-side only:

```text
root/tools/runtime_qualification_matrix.py
```

It does not import production modules and does not modify the raw probe,
bootstrap, heap-sweep tool, or production source. It runs the same probe in
native CPython, forced-overlay CPython, pinned MicroPython at its default
heap, and pinned MicroPython at the sealed 448K stable heap.

### Cross-runtime semantic contract

The matrix compares the exact semantic signature:

```text
(stage PASS sequence, route PASS sequence, completion marker)
```

It ignores memory values, traceback formatting, runtime identity, and
dataclass census values for parity purposes. Each runtime must independently
match the sealed expected contract before signatures are compared. The
expected route remains the twelve authored nodes from `surface_goblin_solo`
through `surface_dungeon_entrance`; the completion marker must occur exactly
once.

Runtime identity evidence was:

```text
CPYTHON_NATIVE          cpython 3.14.6 win32
CPYTHON_FORCED_OVERLAY  cpython 3.14.6 win32
MICROPYTHON_DEFAULT     micropython 1.29.0 win32
MICROPYTHON_448K        micropython 1.29.0 win32
```

The matrix result was:

```text
MPY20|RUNTIME|CPYTHON_NATIVE|PASS
MPY20|RUNTIME|CPYTHON_FORCED_OVERLAY|PASS
MPY20|RUNTIME|MICROPYTHON_DEFAULT|PASS
MPY20|RUNTIME|MICROPYTHON_448K|PASS
MPY20|SEMANTIC_PARITY|PASS
```

The forced-overlay run is retained as a distinct middle runtime: native
CPython proves ordinary DD behavior, forced-overlay CPython exercises the
compatibility surfaces on CPython, and pinned MicroPython proves the same
authoritative headless runtime executes under the constrained interpreter.
This is one gameplay implementation, not three gameplay implementations.

### Fixed MPY19 pressure confirmation

MPY20 did not re-hunt the heap floor. It reran only the sealed boundary:

```text
MPY20|HEAP|448K|STABLE_PASS|3/3
MPY20|HEAP|416K|MEMORY_LIMIT_CONFIRMED|3/3
```

The 448K runs reached `ROUTE_FINAL_STATE`, `ROUTE_EVIDENCE_RELEASE`,
`ROUTE_SESSION_TEARDOWN`, and the completion marker. The 416K runs remained
clean `MemoryError` pressure results; their exact failure frontiers were
retained in the matrix subprocess output. The 448K result is an observed
Windows MicroPython qualification floor, not a product or PS5 memory budget.

### Closure result

```text
MPY20|RESULT|CLOSURE_COMPLETE
```

The qualified runtime surface remains:

```text
catalog loading, DrifterSpec resolution, new-game construction,
EnemyState and Battle construction, BattleView generation, semantic Battle
inputs and completion, OverworldSession import/construction/view generation,
session encounter entry/completion, the full eight-encounter three-Rest
surface route, Goblin Lord defeat, Dungeon Entrance, progression/rewards,
evidence release, and route-session teardown.
```

The compatibility inventory is unchanged and consists of narrow portable
source corrections and MicroPython-only overlays: readonly mappings,
generated dataclass metadata and the dataclass overlay, StrEnum, keyword and
regex boundaries, `collections.abc`, typing/Protocol, portable ASCII
validation, Counter removal, starred tuple portability, strict-zip removal,
the lazy session persistence import boundary, `itertools.groupby` removal,
`first_or_none`, and the portable random adapter.

The campaign retains one authoritative Python gameplay implementation. It
does not claim universal future-content compatibility, exhaustive mechanic
coverage, a PS5 RAM budget, PS5 host integration, completed SAVE-ARCH,
desktop persistence portability, or PS5 shipping readiness. SAVE-ARCH,
graphics, audio, input, platform lifecycle, SDK integration, native storage,
packaging, and certification remain separate host/platform concerns.

Future MicroPython qualification is triggered only by material changes such
as a runtime version change, new headless standard-library dependency,
unqualified gameplay content, core session/combat architecture changes,
dataclass-contract or overlay changes, persistence entering the constrained
runtime contract, or a material target runtime change. No nominal MPY21 gate
is scheduled.

```text
Dungeon Drifters MicroPython portability campaign MPY0-MPY20: CLOSED.

The current authoritative headless gameplay runtime and authored surface-route
contract are qualified on pinned MicroPython v1.29.0 without a second
gameplay implementation.

Future portability work is evidence-driven rather than gate-number-driven.
```

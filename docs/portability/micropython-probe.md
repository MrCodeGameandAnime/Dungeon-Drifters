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

## MYP3 - Portable dataclass field discovery and overlay

MYP3 continued after the stock annotation discovery failure instead of treating it as evidence that portable dataclass behavior was impossible. The pinned runtime preserves class identity but does not preserve class annotations:

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

The pinned source exposes no existing annotation-preservation option. A broad interpreter fork or production rewrite was not justified. MYP3 therefore selected generated metadata while preserving every DD production dataclass unchanged.

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

The MYP2 count of 74 is historical evidence, not a permanent limit. Every portable dataclass must resolve exactly one manifest key. There is no bare-name fallback, ambiguous matching, or silent missing metadata.

The manifest contains only ordered field names. Ordinary defaults remain on the class, and `field(default_factory=...)` remains represented by the overlay field marker. It is compatibility metadata, not a second gameplay representation.

### Portable overlay

The MicroPython-only implementation is `root/portability/micropython/dataclasses.py`. It implements only the MYP2-qualified subset:

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

### MYP3 evidence

Portable conformance under CPython:

```text
13 passed
```

Direct overlay smoke test under MicroPython:

```text
MYP|OVERLAY|FIELDS|('value', 'items')
MYP|OVERLAY|FACTORY_ISOLATED|True
MYP|OVERLAY|POST_SETATTR|5
MYP|OVERLAY|FROZEN|TypeError
MYP|OVERLAY|PASS
```

Native CPython raw probe:

```text
MYP|RESULT|RAW_PROBE_STAGES_COMPLETE
```

Forced-overlay CPython raw probe:

```text
MYP|CATALOG_IMPORT|PASS
MYP|RESULT|RAW_PROBE_STAGES_COMPLETE
```

Pinned MicroPython raw probe:

```text
MYP|BOOT|PASS
MYP|IMPLEMENTATION|micropython
MYP|VERSION|1.29.0
MYP|PLATFORM|win32
MYP|CATALOG_IMPORT|BEGIN
MYP|CATALOG_IMPORT|FAIL|ImportError|no module named 'enum'
MYP|MEMORY|CATALOG_IMPORT|FAIL|FREE|978336|ALLOC|46176
```

The previous `ImportError: no module named 'dataclasses'` failure was crossed. The next compatibility frontier is the unrelated `enum` import in `root/src/app/combat/move.py`. MYP3 stops there; it does not repair enum, typing, collections, pathlib, persistence, annotations, or gameplay.

MYP3 production impact:

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

MYP3 establishes that the dataclass contract is portable when field identity is supplied separately. It does not claim that the full DD runtime is yet MicroPython-compatible.

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

## MYP4 - Portable StrEnum overlay

MYP4 advances the raw MicroPython qualification past the `enum` import wall. It preserves the authoritative DD source and adds no production changes under `root/src`.

### Enum audit

The production enum surface was discovered dynamically from `root/src/app`, rather than from a fixed count. The historical MYP4 baseline is 14 importing files and 34 direct `StrEnum` declarations. Every declaration derives directly from `StrEnum` and uses uppercase names assigned literal string values.

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

The MYP3 overlay now records unique identities rather than construction totals:

```text
EXPECTED    = set(FIELD_MANIFEST)
DECORATED   = set()
CONSTRUCTED = set()
```

`DECORATED` receives a class identity only after decoration completes successfully. `CONSTRUCTED` receives it only after field assignment and `__post_init__` complete successfully. Counts are emitted from those sets, so repeated instances of one class cannot masquerade as coverage of multiple classes. `EXPECTED` is derived dynamically from the generated manifest; the historical count of 74 is not a permanent requirement.

The bootstrap emits census diagnostics from a `finally` path without changing the raw probe or masking its original exception. If census access is unavailable it emits an explicit diagnostic-unavailable line.

### MYP4 evidence

Native CPython raw probe:

```text
MYP|RESULT|RAW_PROBE_STAGES_COMPLETE
```

Forced-overlay CPython raw probe:

```text
MYP|CATALOG_IMPORT|PASS
MYP|RESULT|RAW_PROBE_STAGES_COMPLETE
MYP|DATACLASS|EXPECTED|74
MYP|DATACLASS|DECORATED|74
MYP|DATACLASS|CONSTRUCTED|33
```

Direct portable enum smoke test under the pinned runtime:

```text
MYP|ENUM|MICROPYTHON|PASS
```

Pinned MicroPython `v1.29.0` raw probe after the enum wall was crossed:

```text
MYP|BOOT|PASS
MYP|IMPLEMENTATION|micropython
MYP|VERSION|1.29.0
MYP|PLATFORM|win32
MYP|MEMORY|BOOT|FREE|1003456|ALLOC|21056
MYP|SOURCE_PATH|BEGIN
MYP|SOURCE_PATH|PASS
MYP|CATALOG_IMPORT|BEGIN
MYP|CATALOG_IMPORT|FAIL|ImportError|no module named 'keyword'
MYP|MEMORY|CATALOG_IMPORT|FAIL|FREE|967856|ALLOC|56656
MYP|DATACLASS|EXPECTED|74
MYP|DATACLASS|DECORATED|2
MYP|DATACLASS|CONSTRUCTED|0
```

The original `ImportError: no module named 'dataclasses'` wall was crossed by MYP3, and the `ImportError: no module named 'enum'` wall was crossed by MYP4. The next observed incompatibility is the unrelated `keyword` import from `root/src/app/content/enemy_spec.py`. MYP4 stops there. It does not repair `keyword`, typing, collections, pathlib, persistence, annotations, or gameplay.

The external runtime evidence remains:

```text
MicroPython tag: v1.29.0
Resolved source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Source checkout: clean
Reported platform: win32
```

MYP4 production impact is:

```text
root/src production files changed: 0
gameplay changes: 0
content changes: 0
persistence changes: 0
semantic API changes: 0
```

The overlay is a MicroPython-only portability boundary. Native CPython, Pyodide, Chaquopy, pytest, and packaging continue using the standard-library `enum`. MYP4 establishes that DD's qualified StrEnum behavior is portable through the observed enum wall without claiming that the full DD runtime is yet MicroPython-compatible.

## MYP5 - Portable keyword boundary

MYP5 advances the raw MicroPython qualification past the observed `keyword` import failure while preserving DD production source, gameplay, content, persistence, semantic APIs, and the unchanged raw probe.

MYP4 was sealed at:

```text
0a9677d58f80e90f80d50e6ac885a43c4279878e
MYP4 - Add Portable StrEnum Overlay
```

The starting MYP4 evidence was:

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

### MYP5 evidence

Native CPython raw probe:

```text
MYP|RESULT|RAW_PROBE_STAGES_COMPLETE
```

Forced-overlay CPython raw probe:

```text
MYP|CATALOG_IMPORT|PASS
MYP|RESULT|RAW_PROBE_STAGES_COMPLETE
MYP|DATACLASS|EXPECTED|74
MYP|DATACLASS|DECORATED|74
MYP|DATACLASS|CONSTRUCTED|33
```

Pinned MicroPython runtime:

```text
MYP|BOOT|PASS
MYP|IMPLEMENTATION|micropython
MYP|VERSION|1.29.0
MYP|PLATFORM|win32
MYP|MEMORY|BOOT|FREE|1003456|ALLOC|21056
MYP|SOURCE_PATH|BEGIN
MYP|MEMORY|SOURCE_PATH|BEFORE|FREE|1003408|ALLOC|21104
MYP|MEMORY|SOURCE_PATH|AFTER|FREE|1003376|ALLOC|21136
MYP|SOURCE_PATH|PASS
MYP|CATALOG_IMPORT|BEGIN
MYP|MEMORY|CATALOG_IMPORT|BEFORE|FREE|1003376|ALLOC|21136
Warning: exception chaining not supported
MYP|CATALOG_IMPORT|FAIL|ValueError|invalid kind: 'damage'
MYP|MEMORY|CATALOG_IMPORT|FAIL|FREE|945088|ALLOC|79424
MYP|DATACLASS|EXPECTED|74
MYP|DATACLASS|DECORATED|4
MYP|DATACLASS|CONSTRUCTED|1
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

MYP5 does not repair this enum-conversion frontier. It belongs to the next evidence-derived gate. The dataclass census remains diagnostic and dynamic; the new frontier was reached after four classes were decorated and one was successfully constructed.

External runtime evidence:

```text
MicroPython tag: v1.29.0
Resolved source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Source checkout: clean
Reported platform: win32
```

MYP5 impact remains:

```text
root/src production files changed: 0
gameplay changes: 0
content changes: 0
persistence changes: 0
semantic API changes: 0
raw probe changes: 0
```

MYP5 closes only the observed keyword boundary. No speculative enum, typing, collections, pathlib, persistence, annotation, or gameplay compatibility work is included.



## MYP6 - Portable StrEnum member normalization

MYP6 advances the pinned MicroPython qualification past the existing-member
lookup failure recorded by MYP5. The compatibility boundary remains outside
`root/src`; DD production source, gameplay, content, persistence, semantic
APIs, and the unchanged raw probe remain untouched.

### MYP6 diagnosis

The MYP5 failure occurred while `Move.__post_init__` normalized authored enum
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

### MYP6 correction

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

### MYP6 qualification evidence

The direct qualification under the pinned MicroPython `v1.29.0` runtime
reported:

```text
MYP6|OVERLAY| enum
MYP6|SAMPLE|RAW| True
MYP6|SAMPLE|MEMBER| True
MYP6|SAMPLE|INVALID|PASS
MYP6|MOVEKIND|RAW| True
MYP6|MOVEKIND|MEMBER| True
MYP6|MOVE|MEMBERS|PASS| True True
MYP6|MOVE|STRINGS|PASS| True True
MYP6|RESULT|PASS
```

Native CPython and the forced overlay both completed the unchanged raw probe.
The forced overlay retained the dynamic dataclass census:

```text
MYP|DATACLASS|EXPECTED|74
MYP|DATACLASS|DECORATED|74
MYP|DATACLASS|CONSTRUCTED|33
```

The unchanged raw probe under pinned MicroPython crossed the enum frontier and
stopped at the next unrelated compatibility wall:

```text
MYP|BOOT|PASS
MYP|IMPLEMENTATION|micropython
MYP|VERSION|1.29.0
MYP|PLATFORM|win32
MYP|MEMORY|BOOT|FREE|1003456|ALLOC|21056
MYP|SOURCE_PATH|BEGIN
MYP|MEMORY|SOURCE_PATH|BEFORE|FREE|1003408|ALLOC|21104
MYP|MEMORY|SOURCE_PATH|AFTER|FREE|1003376|ALLOC|21136
MYP|SOURCE_PATH|PASS
MYP|CATALOG_IMPORT|BEGIN
MYP|MEMORY|CATALOG_IMPORT|BEFORE|FREE|1003376|ALLOC|21136
MYP|CATALOG_IMPORT|FAIL|AttributeError|'re' object has no attribute 'fullmatch'
MYP|MEMORY|CATALOG_IMPORT|FAIL|FREE|945040|ALLOC|79472
MYP|DATACLASS|EXPECTED|74
MYP|DATACLASS|DECORATED|4
MYP|DATACLASS|CONSTRUCTED|2
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
MYP6 does not repair `re`, typing, collections, pathlib, persistence,
annotation syntax, or gameplay.

MYP6 impact remains:

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

## MYP7 - Portable Regex Fullmatch Boundary

MYP7 advances the pinned MicroPython qualification past the missing
`re.fullmatch` behavior recorded by MYP6. The compatibility boundary remains
outside `root/src`; the raw probe, gameplay, content, persistence, semantic
APIs, and schema remain unchanged.

MYP6 was sealed at:

```text
a97def8f26d811b08fe650157296a8da57bcb6a8
MYP6 - Repair Portable StrEnum Construction
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

MYP7 uses:

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

### MYP7 qualification evidence

The direct qualification under pinned MicroPython `v1.29.0` reported:

```text
MYP7|NATIVE|COMPILE| True
MYP7|NATIVE|FULLMATCH| False
MYP7|NATIVE|PATTERN_FULLMATCH| False
MYP7|PROXY|ACTIVE| True
MYP7|PROXY|DELEGATED_SEARCH| True
MYP7|PROXY|COMPILED| True
MYP7|PROXY|COMPILED_FULLMATCH| True True
MYP7|PROXY|MODULE_FULLMATCH| True True
```

The forced compatibility CPython raw probe completed every unchanged stage:

```text
MYP|CATALOG_IMPORT|PASS
MYP|DRIFTER_SPEC|PASS
MYP|NEW_GAME|PASS
MYP|FIRST_ENCOUNTER|PASS
MYP|ENEMY_STATE|PASS
MYP|BATTLE_CONSTRUCTION|PASS
MYP|BATTLE_VIEW|PASS
MYP|BATTLE_INPUT|PASS
MYP|BATTLE_COMPLETE|PASS
MYP|SESSION_IMPORT|PASS
MYP|SESSION_CONSTRUCTION|PASS
MYP|SESSION_VIEW|PASS
MYP|SESSION_ENCOUNTER_ENTRY|PASS
MYP|SESSION_ENCOUNTER_COMPLETE|PASS
MYP|RESULT|RAW_PROBE_STAGES_COMPLETE
```

The pinned MicroPython raw probe crossed the `re.fullmatch` frontier and
stopped at the next unrelated compatibility wall:

```text
MYP|BOOT|PASS
MYP|IMPLEMENTATION|micropython
MYP|VERSION|1.29.0
MYP|PLATFORM|win32
MYP|MEMORY|BOOT|FREE|1001952|ALLOC|22560
MYP|SOURCE_PATH|PASS
MYP|CATALOG_IMPORT|BEGIN
MYP|MEMORY|CATALOG_IMPORT|BEFORE|FREE|1001872|ALLOC|22640
MYP|CATALOG_IMPORT|FAIL|ImportError|no module named 'collections.abc'
MYP|MEMORY|CATALOG_IMPORT|FAIL|FREE|934288|ALLOC|90224
MYP|DATACLASS|EXPECTED|74
MYP|DATACLASS|DECORATED|4
MYP|DATACLASS|CONSTRUCTED|3
```

The next gate must be derived from the observed `collections.abc` import
failure. No speculative repair is documented here.

## Future Gates

```text
MYP0  Raw probe; find the first real incompatibility.
MYP1  First evidence-backed compatibility primitive.
MYP2  Qualify the portable dataclass contract.
MYP3  Portable dataclass field discovery and overlay; stop at enum.
MYP4  Portable StrEnum overlay; stop at keyword.
MYP5  Portable keyword boundary; stop at the next unrelated wall.
MYP6  Qualify the next evidence-derived compatibility frontier.
MYP7  Portable regex fullmatch boundary; stop at collections.abc.
MYP8  Next evidence-derived compatibility frontier.
MYP9  Core runtime qualification.
MYP10 Session qualification.
MYP11 Eight encounters, three Rests, Dungeon Entrance.
MYP12 Constrained-target memory and runtime pressure.
MYP13 Cross-runtime regression qualification.
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

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

## MYP8 - Portable `collections.abc` Boundary

MYP8 advances the pinned MicroPython qualification past the missing
`collections.abc` module without changing `root/src`, gameplay, content,
persistence, semantic APIs, or the raw probe. MYP7 was sealed at:

```text
6b4883a833d53ce6bf412ed7957a7b72a5a51736
MYP7 - Add Portable Regex Fullmatch Boundary
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

MYP8 adds:

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

This preserves dictionary and MYP1 read-only mapping recognition, ordered
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

### MYP8 qualification evidence

The direct qualification under the pinned MicroPython runtime passed the
qualified imports, mapping/sequence checks, annotation probe, and real
Weapon/WeaponSpec construction:

```text
MYP8|NATIVE|ABC_IMPORT|FAIL|ImportError|no module named 'collections.abc'
MYP8|IMPORT|MAPPING_SEQUENCE|PASS
MYP8|ANNOTATION|EVALUATED| False
MYP8|WEAPON|REAL_PATH|PASS
MYP8|COUNTER|NATIVE_AVAILABLE| False
```

The forced CPython subprocess tests passed native-module retention,
idempotent installation, Mapping/Sequence behavior, DD validator behavior,
real Weapon/WeaponSpec paths, and Battle's list/tuple normalization boundary.
The native and forced compatibility contract tests passed `7` tests.

The unchanged raw probe crossed `collections.abc` and stopped at the next
unrelated runtime incompatibility:

```text
MYP|BOOT|PASS
MYP|IMPLEMENTATION|micropython
MYP|VERSION|1.29.0
MYP|PLATFORM|win32
MYP|MEMORY|BOOT|FREE|999552|ALLOC|24960
MYP|SOURCE_PATH|PASS
MYP|CATALOG_IMPORT|BEGIN
MYP|MEMORY|CATALOG_IMPORT|BEFORE|FREE|999488|ALLOC|25024
MYP|CATALOG_IMPORT|FAIL|AttributeError|'str' object has no attribute 'isascii'
MYP|MEMORY|CATALOG_IMPORT|FAIL|FREE|906848|ALLOC|117664
MYP|DATACLASS|EXPECTED|74
MYP|DATACLASS|DECORATED|10
MYP|DATACLASS|CONSTRUCTED|7
```

The original traceback identifies `DrifterSpec.__post_init__` at
`root/src/app/content/drifter_spec.py:126`, where `choice.isascii()` is
called while the generated catalog constructs Azhvielle's specification:

```text
AttributeError: 'str' object has no attribute 'isascii'
```

That `str.isascii` frontier is the next evidence-derived gate. MYP8 does not
repair or speculate about it. The pinned external runtime evidence remains:

```text
MicroPython tag: v1.29.0
Resolved source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Source checkout: clean
Reported platform: win32
```

MYP8 changed zero `root/src` production files, gameplay behavior, content,
persistence, semantic APIs, and raw-probe code. Dataclass, enum, keyword, and
regex boundaries remain unchanged.

## MYP9 - Portable ASCII String Validation

MYP9 advances the pinned MicroPython qualification past the missing
`str.isascii()` and `str.isdecimal()` methods without adding a compatibility
module or changing the raw probe. MYP8 was sealed at:

```text
bb99b7e1e9360078b157a85400e3c9dea73a386f
MYP8 - Add Portable Collections ABC Boundary
```

### Historical failure and runtime evidence

The MYP8 probe stopped during `CATALOG_IMPORT` while the generated catalog
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
the built-in string type cannot be extended. MYP9 uses the already qualified
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
MYP9|STR|ISASCII|False
MYP9|STR|ISDECIMAL|False
MYP9|STR|ISDIGIT|True
MYP9|STR|SETATTR|AttributeError|'type' object has no attribute 'isascii'
MYP9|DRIFTER_SPEC|PASS|branoc|1
MYP9|CATALOG|IMPORT|PASS
```

The unchanged raw probe completes every stage under native CPython `3.14.6`,
and the forced CPython regex-proxy subprocess also completes every stage.
Those runs qualify harness reachability only; they are not MicroPython
compatibility evidence.

The unchanged raw probe through the pinned MicroPython bootstrap now reports:

```text
MYP|BOOT|PASS
MYP|IMPLEMENTATION|micropython
MYP|VERSION|1.29.0
MYP|PLATFORM|win32
MYP|MEMORY|BOOT|FREE|999552|ALLOC|24960
MYP|SOURCE_PATH|BEGIN
MYP|MEMORY|SOURCE_PATH|BEFORE|FREE|999504|ALLOC|25008
MYP|MEMORY|SOURCE_PATH|AFTER|FREE|999488|ALLOC|25024
MYP|SOURCE_PATH|PASS
MYP|CATALOG_IMPORT|BEGIN
MYP|MEMORY|CATALOG_IMPORT|BEFORE|FREE|999488|ALLOC|25024
MYP|MEMORY|CATALOG_IMPORT|AFTER|FREE|860288|ALLOC|164224
MYP|CATALOG_IMPORT|PASS
MYP|DRIFTER_SPEC|BEGIN
MYP|MEMORY|DRIFTER_SPEC|BEFORE|FREE|860288|ALLOC|164224
MYP|MEMORY|DRIFTER_SPEC|AFTER|FREE|860272|ALLOC|164240
MYP|DRIFTER_SPEC|PASS
MYP|NEW_GAME|BEGIN
MYP|MEMORY|NEW_GAME|BEFORE|FREE|860288|ALLOC|164224
MYP|MEMORY|NEW_GAME|AFTER|FREE|834000|ALLOC|190512
MYP|NEW_GAME|PASS
MYP|FIRST_ENCOUNTER|BEGIN
MYP|MEMORY|FIRST_ENCOUNTER|BEFORE|FREE|833984|ALLOC|190528
MYP|MEMORY|FIRST_ENCOUNTER|AFTER|FREE|833968|ALLOC|190544
MYP|FIRST_ENCOUNTER|PASS
MYP|ENEMY_STATE|BEGIN
MYP|MEMORY|ENEMY_STATE|BEFORE|FREE|833968|ALLOC|190544
MYP|MEMORY|ENEMY_STATE|AFTER|FREE|833440|ALLOC|191072
MYP|ENEMY_STATE|PASS
MYP|BATTLE_CONSTRUCTION|BEGIN
MYP|MEMORY|BATTLE_CONSTRUCTION|BEFORE|FREE|833440|ALLOC|191072
MYP|BATTLE_CONSTRUCTION|FAIL|ImportError|can't import name Counter
MYP|MEMORY|BATTLE_CONSTRUCTION|FAIL|FREE|822256|ALLOC|202256
MYP|DATACLASS|EXPECTED|74
MYP|DATACLASS|DECORATED|15
MYP|DATACLASS|CONSTRUCTED|13
```

The original traceback is preserved by the probe:

```text
ImportError: can't import name Counter
```

The first post-MYP9 frontier is therefore the unrelated `Counter` import in
`root/src/app/combat/battle.py`. MYP9 does not repair or speculate about it.
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

MYP9 changed exactly one production file:
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

## MYP10 - Remove Counter Runtime Dependency

MYP10 advances the pinned MicroPython qualification past the `Counter` import
failure without adding a Counter compatibility layer. MYP9 was sealed at:

```text
d78c07293219116f04f9c203b6654bf8b9728e35
MYP9 - Repair Portable ASCII String Validation
```

### Historical failure and production audit

The MYP9 raw probe stopped at `BATTLE_CONSTRUCTION` because
`root/src/app/combat/battle.py` imported `Counter` from `collections`. The
audited production use was limited to enemy display-label bookkeeping:

```python
counts = Counter(enemy.display_name for enemy in enemies)
positions = Counter()
positions[name] += 1
counts[name]
```

The dynamic audit scans only `root/src/app/**/*.py`. After MYP10 it discovers:

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
MYP10 focused collections and Battle-label tests: 13 passed
```

Native CPython `3.14.6` and a forced regex-compatibility CPython subprocess
both complete the unchanged raw probe through `SESSION_ENCOUNTER_COMPLETE`.
This confirms no regression in the ordinary runtime or previously qualified
compatibility boundaries.

The direct pinned MicroPython qualification recorded the native capability and
the next import wall:

```text
MYP10|COUNTER|AVAILABLE|False
ImportError: no module named 'typing'
```

`Counter` was therefore crossed naturally. The direct Battle attempt imported
the updated module and then stopped at the next unrelated `typing` dependency
from `root/src/app/combat/combatant.py`. No later direct label step was
attempted after that frontier.

The unchanged raw probe through the pinned MicroPython bootstrap reports:

```text
MYP|BOOT|PASS
MYP|IMPLEMENTATION|micropython
MYP|VERSION|1.29.0
MYP|PLATFORM|win32
MYP|MEMORY|BOOT|FREE|999552|ALLOC|24960
MYP|SOURCE_PATH|BEGIN
MYP|MEMORY|SOURCE_PATH|BEFORE|FREE|999504|ALLOC|25008
MYP|MEMORY|SOURCE_PATH|AFTER|FREE|999488|ALLOC|25024
MYP|SOURCE_PATH|PASS
MYP|CATALOG_IMPORT|BEGIN
MYP|MEMORY|CATALOG_IMPORT|BEFORE|FREE|999488|ALLOC|25024
MYP|MEMORY|CATALOG_IMPORT|AFTER|FREE|860288|ALLOC|164224
MYP|CATALOG_IMPORT|PASS
MYP|DRIFTER_SPEC|BEGIN
MYP|MEMORY|DRIFTER_SPEC|BEFORE|FREE|860288|ALLOC|164224
MYP|DRIFTER_SPEC|AFTER|FREE|860272|ALLOC|164240
MYP|DRIFTER_SPEC|PASS
MYP|NEW_GAME|BEGIN
MYP|MEMORY|NEW_GAME|BEFORE|FREE|860288|ALLOC|164224
MYP|NEW_GAME|AFTER|FREE|834000|ALLOC|190512
MYP|NEW_GAME|PASS
MYP|FIRST_ENCOUNTER|BEGIN
MYP|MEMORY|FIRST_ENCOUNTER|BEFORE|FREE|833984|ALLOC|190528
MYP|FIRST_ENCOUNTER|AFTER|FREE|833968|ALLOC|190544
MYP|FIRST_ENCOUNTER|PASS
MYP|ENEMY_STATE|BEGIN
MYP|MEMORY|ENEMY_STATE|BEFORE|FREE|833968|ALLOC|190544
MYP|ENEMY_STATE|AFTER|FREE|833440|ALLOC|191072
MYP|ENEMY_STATE|PASS
MYP|BATTLE_CONSTRUCTION|BEGIN
MYP|MEMORY|BATTLE_CONSTRUCTION|BEFORE|FREE|833440|ALLOC|191072
MYP|BATTLE_CONSTRUCTION|FAIL|ImportError|no module named 'typing'
MYP|MEMORY|BATTLE_CONSTRUCTION|FAIL|FREE|783840|ALLOC|240672
MYP|DATACLASS|EXPECTED|74
MYP|DATACLASS|DECORATED|31
MYP|DATACLASS|CONSTRUCTED|15
```

The original traceback is preserved:

```text
ImportError: no module named 'typing'
```

The next gate must be derived from this observed `typing` failure. MYP10 does
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

MYP10 changed exactly one production file:
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

## MYP11 - Portable Typing and Protocol Boundary

MYP11 advances the raw MicroPython qualification past the `typing` import
failure recorded at MYP10. The baseline was:

```text
MYP10 sealed SHA: 00b7733c02a8b78ebfb856ccbe5fc9ea119f6fe9
MicroPython: v1.29.0
Source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Platform: win32
```

The original MYP10 frontier was:

```text
MYP|BATTLE_CONSTRUCTION|FAIL|ImportError|no module named 'typing'
```

MYP11 keeps native `typing` for CPython and static tooling. Its only
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

The focused MYP11 contract and forced-overlay tests pass. The forced tests
run in subprocesses and verify the overlay's module origin, all four aliases,
real combatants, structural UI values, callability rejection, and process
isolation. Native tests continue to exercise CPython Protocol acceptance and
the existing dataclass, enum, keyword, regex, collections, string, Counter,
Battle, M10, and M11 contracts.

The native CPython raw probe reaches every current stage:

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

The unchanged raw probe through the complete pinned MicroPython bootstrap
crosses the former typing wall. Its first unrelated frontier is:

```text
MYP|BATTLE_CONSTRUCTION|FAIL|SyntaxError|*x must be assignment target
MYP|MEMORY|BATTLE_CONSTRUCTION|FAIL|FREE|733248|ALLOC|291264
MYP|DATACLASS|EXPECTED|74
MYP|DATACLASS|DECORATED|46
MYP|DATACLASS|CONSTRUCTED|17
```

The original traceback is preserved and identifies the next wall:

```text
File "root/src/app/presentation/battle_session.py", line 30, in entries
SyntaxError: *x must be assignment target
```

The preceding MicroPython stages all pass through `ENEMY_STATE`. The typing
failure is therefore crossed; MYP11 does not repair this unrelated syntax
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

MYP11 preserves one authoritative gameplay implementation. The new portable
boundary is limited to import markers and the three runtime structural checks;
it does not introduce nominal combatant fallbacks, Protocol metaclass
emulation, global type patching, source transformation, or a bootstrap
redesign. The next gate must be derived from the observed
`battle_session.py` syntax failure.

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
MYP8  Portable collections.abc boundary; stop at str.isascii.
MYP9  Portable ASCII string validation; stop at the next unrelated wall.
MYP10 Next evidence-derived compatibility frontier.
MYP11 Portable typing and Protocol boundary; stop at battle_session.py syntax.
MYP12 Next evidence-derived compatibility frontier.
MYP13 Core runtime qualification.
MYP14 Session qualification.
MYP15 Eight encounters, three Rests, Dungeon Entrance.
MYP16 Constrained-target memory and runtime pressure.
MYP17 Cross-runtime regression qualification.
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

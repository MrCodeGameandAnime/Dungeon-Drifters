# MYP2 - Qualify Portable Dataclass Contract

**Goal:** Audit DD’s actual dataclass dependency, define the minimum portable contract, and select a compatibility strategy without changing production behavior.

**Architecture:** Keep native CPython dataclasses and the raw MicroPython probe unchanged. Add implementation-neutral conformance tests and extend the existing MicroPython documentation with the complete audit and decision record.

**Tech Stack:** Python, pytest, static inspection, pinned MicroPython `v1.29.0`.

**Spec:** User-provided MYP2 qualification plan in this thread.

## Global Constraints

- Baseline: `myp` at `783f9dd9ab69ea8408218e8391adc532c4d32647`.
- No production imports, gameplay, persistence, content, semantic APIs, or probe changes.
- Raw MicroPython remains stopped at `ImportError: no module named 'dataclasses'`.
- Leave historical untracked paths untouched.
- Commit exactly `MYP2 - Qualify Portable Dataclass Contract`.

### Task 1: Record the Complete Production Audit

**Files:**
- Modify: `docs/portability/micropython-probe.md`

Record every production dataclass declaration under `root/src/app`, including its class, decorator options, defaults, post-init behavior, nested values, and role.

Current verified baseline:

- 23 production files import `dataclasses`.
- 74 production dataclass declarations.
- 71 use `@dataclass(frozen=True)`.
- 3 mutable declarations are private combat-state records.
- 1 `field()` call exists: `BattleView.visual` uses `field(default_factory=BattleVisualView)`.
- 58 declarations define `__post_init__`.
- No dataclass inheritance, `order=True`, `unsafe_hash`, `slots`, `kw_only`, `InitVar`, or field metadata usage exists.
- No production calls to `asdict`, `astuple`, `fields`, `replace`, `is_dataclass`, or `make_dataclass` exist.
- `DrifterStatSpec` and `StatBlockSpec` directly iterate `self.__dataclass_fields__` and use only the field names to call `getattr`; no individual `Field` attributes are accessed.
- Persistence uses explicit dictionaries and constructors rather than dataclass metadata.
- No `from __future__ import annotations` usage exists; annotations are not otherwise inspected at runtime.

Classify all declarations as authored specifications, runtime state, semantic inputs, presentation models, or internal result/value objects.

### Task 2: Add the Dataclass Conformance Suite

**Files:**
- Create: `root/tests/test_dataclass_contract.py`

Add implementation-neutral tests for:

- positional and keyword construction with actual field order;
- ordinary defaults;
- `field(default_factory=...)` isolation using `BattleView.visual`;
- structural equality for representative immutable records;
- frozen attribute-assignment rejection;
- `__post_init__` invocation and normalization through `object.__setattr__`;
- validation failure behavior;
- nested tuple, mapping, enum, optional, and record values;
- `DrifterStatSpec.__dataclass_fields__` and `StatBlockSpec.__dataclass_fields__` existing and iterating names in declaration order;
- `DrifterStatSpec.as_dict()` preserving the required field-name/value mapping.

Do not assert that dataclass instances are unhashable, lack ordering, lack repr support, or lack incidental CPython methods.

Instead, document and statically verify that DD production behavior does not depend on hashing, ordering, slots, or dataclass reflection helpers beyond the observed `__dataclass_fields__` access pattern.

### Task 3: Define the Minimum Portable Contract

**Files:**
- Modify: `docs/portability/micropython-probe.md`

Document the qualified contract:

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

Not required:
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

Evaluate Options A through E. Recommend **IMPORT OVERLAY** with a strict portable subset because it avoids changing the 23 production imports.

The documentation must state that the overlay may be selected only by MicroPython-specific bootstrap or launch-path injection. It must never be placed where CPython, Pyodide, Chaquopy, ordinary tests, or packaging can accidentally shadow native `dataclasses`.

Classify the result as:

```text
D2 - Moderate compatibility subset
Risk: MODERATE
Estimated implementation: one compatibility module plus one
MicroPython-only path/bootstrap integration
Expected engine production-file changes: 0
```

### Task 4: Document Persistence and Annotation Boundaries

Update the portability document with:

- save schema 8 remains unchanged;
- persistence is constructor/schema-driven, not dataclass-metadata-driven;
- equality is not a gameplay dispatch authority;
- annotations define dataclass fields but are not directly inspected by DD;
- PEP 604 syntax is a separate future compatibility concern;
- the `__dataclass_fields__` seam is the only observed runtime metadata dependency;
- no migration of typing, enums, collections, pathlib, or persistence is authorized.

End the MYP2 section with the required `DD PORTABLE DATACLASS VERDICT`, populated as:

```text
Recommended portability strategy:
IMPORT OVERLAY

Frozen semantics required:
YES

Structural equality required:
YES

default_factory required:
YES

__post_init__ required:
YES

Dataclass inheritance complexity:
NONE

Runtime reflection required:
LIMITED

Persistence depends on dataclass metadata:
NO

Annotations materially affect implementation:
LIMITED

Semantic runtime API can remain unchanged:
YES

Gameplay architecture changes required:
NO

One authoritative gameplay implementation remains practical:
YES WITH STRICT COMPATIBILITY BOUNDARY

Recommendation:
PROCEED WITH STRICT BOUNDARY
```

### Task 5: Verify and Close MYP2

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pytest root/tests/test_dataclass_contract.py
.\.venv\Scripts\python.exe -m compileall root/src root/tests root/tools
git diff --check
.\.venv\Scripts\python.exe root/tools/micropython_probe.py root/src
& "$env:LOCALAPPDATA\DungeonDrifters\micropython\v1.29.0\source\ports\windows\build-standard\ReleaseWin32\micropython.exe" root/tools/micropython_probe.py root/src
```

Confirm:

- CPython probe still completes normally.
- MicroPython still reports `1.29.0` on `win32`.
- The raw MicroPython probe still fails unchanged at `CATALOG_IMPORT` with `ImportError: no module named 'dataclasses'`.
- No production compatibility implementation entered the diff.
- No gameplay, content, save, or semantic API behavior changed.
- Only the focused conformance tests and portability documentation changed.

Commit, push `myp`, verify local SHA equals `origin/myp`, wait for exact-SHA green CI, and stop. Do not implement the dataclass boundary or begin MYP3 in this gate.

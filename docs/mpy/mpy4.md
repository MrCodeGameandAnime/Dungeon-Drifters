# MYP4 - Add Portable StrEnum Overlay

## Summary

Advance the pinned MicroPython v1.29.0 probe past the observed `enum` failure while preserving DD production source, gameplay, persistence, content, and semantic APIs.

Baseline:

- Branch: `myp`
- HEAD: `28b0e7e48b9b1f214a2b0621a0518043a42f776e`
- MicroPython tag: `v1.29.0`
- Source SHA: `0fd6c573ea815774668bbb16b8e197c8822368b2`
- Source checkout: clean
- Historical untracked `docs/mpy/` paths remain untouched

Current audit evidence is 14 importing files and 34 direct `StrEnum` declarations. Those counts are historical evidence only and must never become fixed validator constants.

## Enum Audit

Document and dynamically inspect the current production enum surface.

The audit must verify:

- every production enum derives directly from `StrEnum`;
- every candidate member has an uppercase public name;
- every candidate member value is a literal string;
- no aliases exist;
- no enum inheritance exists;
- no custom enum methods exist;
- no unsupported enum operations appear in production.

Observed required behavior must include:

- direct member access;
- `EnumType(value)` lookup;
- canonical singleton identity;
- `.value`;
- `.name`;
- `isinstance(member, EnumType)`;
- identity/equality comparisons;
- string compatibility;
- hashing for dictionary and set usage.

The audit must record that DD does not require enum iteration, `len(EnumType)`, `EnumType["NAME"]`, pickling, enum reflection, ordering, or CPython-specific repr behavior.

## MicroPython Overlay

Add:

```text
root/portability/micropython/enum.py
```

Export only `StrEnum`.

Use the following lifecycle:

```text
overlay import
→ capture builtins.__build_class__ exactly once
→ install the wrapper before DD enum declarations execute

class X(StrEnum):
    VALUE = "value"

→ original class builder creates an ordinary subclass
→ wrapper recognizes only direct StrEnum subclasses
→ wrapper creates canonical string-backed members
→ wrapper exposes member names and values
→ wrapper installs value lookup for later construction
```

The raw member-construction mechanism must use the supported MicroPython v1.29.0 string-subclass path. The implementation must preserve the conceptual separation:

```text
member creation:
raw construction with lookup disabled

later EnumType(value):
StrEnum.__new__ or equivalent lookup
→ existing singleton
```

The pinned runtime does not expose a usable `str.__new__`, so the implementation must use the demonstrated equivalent construction path rather than assuming CPython internals.

The wrapper must:

- delegate every unrelated class to the original `__build_class__`;
- recognize only direct subclasses of the portable `StrEnum`;
- preserve canonical member identity;
- expose correct `.name` and `.value` behavior;
- preserve string equality and `str(member)`;
- preserve hashing and dictionary/set behavior;
- preserve `isinstance(member, EnumType)`;
- raise `ValueError` for unknown values;
- fail loudly for duplicate values or malformed candidate members;
- ignore dunder names, helper methods, and arbitrary non-member class attributes.

It must not become:

- a general metaclass system;
- a replacement for all Python enums;
- an enum inheritance framework;
- a source transformer;
- a second DD content or gameplay representation.

## Hook Safety

The implementation and tests must prove:

- the original `__build_class__` is captured exactly once;
- the wrapper is installed before DD enum declarations execute;
- only direct `StrEnum` subclasses are transformed;
- ordinary classes are delegated unchanged;
- ordinary DD dataclasses remain unaffected;
- the forced-overlay tests run in subprocesses so the hook cannot leak into host tests;
- any test-local installation restores the original builder in `finally`;
- forced-overlay qualification proves the overlay module is active rather than accidentally using cached CPython `enum`.

## Dataclass Census

Extend the existing MicroPython dataclass overlay with unique identity sets:

```text
EXPECTED    = set(FIELD_MANIFEST)
DECORATED   = set()
CONSTRUCTED = set()
```

Rules:

- add a class identity to `DECORATED` only after `_decorate()` completes successfully;
- add a class identity to `CONSTRUCTED` only after field assignment and `__post_init__` complete successfully;
- retain identities internally rather than using incrementing counters;
- derive `EXPECTED` dynamically from the generated manifest;
- never require `74` as a permanent value.

Extend the MicroPython bootstrap, not the raw probe, to emit deterministic census counts from a `finally` path. The `finally` block must not catch, normalize, or replace the original probe exception.

Expected diagnostic shape:

```text
MYP|DATACLASS|EXPECTED|N
MYP|DATACLASS|DECORATED|N
MYP|DATACLASS|CONSTRUCTED|N
```

If census access itself is unavailable, emit an explicit diagnostic-unavailable line without masking the original failure.

## Tests

Add focused enum contract and portable overlay tests covering:

- dynamic discovery of all current production enum declarations;
- direct `StrEnum` inheritance;
- uppercase literal-string member rules;
- no aliases, inheritance, or custom enum methods;
- native CPython imports of the standard-library `enum`;
- synthetic overlay enum declaration;
- singleton member identity;
- `EnumType("value")`;
- invalid lookup failure;
- `.name` and `.value`;
- member/string equality;
- `str(member)`;
- hashing and dictionary/set keys;
- `isinstance(member, EnumType)`;
- malformed candidate and duplicate-value rejection;
- ordinary class isolation;
- dataclass isolation;
- all relevant real DD enum classes under the forced overlay;
- real `Move` construction through portable dataclasses and enums;
- real DD validators that call enum constructors;
- unique dataclass census behavior.

The forced-overlay tests must use subprocesses or restore all process-global hooks in `finally`.

## Documentation

Update:

```text
docs/portability/micropython-probe.md
```

Record:

- the original `CATALOG_IMPORT` failure at `from enum import StrEnum`;
- the dynamically audited enum surface;
- required enum operations;
- unsupported enum operations;
- MicroPython evidence for `__module__`, `__name__`, and `__qualname__`;
- failure of useful `__init_subclass__`;
- rejection of `metaclass=`;
- availability of `builtins.__build_class__`;
- the selected narrow hook mechanism;
- the raw-member construction and later lookup distinction;
- hook safety guarantees;
- dynamic dataclass census semantics;
- native CPython and forced-overlay results;
- exact MicroPython output after the enum wall is crossed;
- the next observed stage, exception, message, traceback, and memory evidence;
- zero `root/src` production changes;
- zero gameplay, content, persistence, and semantic API changes.

Do not document or implement speculative repairs for the next compatibility wall.

## Verification And Release

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pytest root\tests\test_dataclass_contract.py root\tests\test_portable_dataclasses.py root\tests\test_enum_contract.py root\tests\test_portable_enum.py
.\.venv\Scripts\python.exe -m compileall root\src root\tests root\tools root\portability
.\.venv\Scripts\python.exe root\tools\generate_dataclass_manifest.py --check
git diff --check
```

Run:

- the unchanged probe under native CPython;
- the forced-overlay probe under CPython;
- the pinned MicroPython probe through `micropython_probe_bootstrap.py`.

Confirm:

- the previous `enum` import failure is gone;
- the next unrelated MicroPython incompatibility is reported with original traceback and memory evidence;
- the census counts are emitted from unique identity sets;
- no production source file under `root/src` changed;
- no gameplay, persistence, content, or semantic API changed;
- no external MicroPython source or binary entered the repository;
- historical untracked `docs/mpy/` files remain untouched.

Commit exactly:

```text
MYP4 - Add Portable StrEnum Overlay
```

Push `myp`, verify local and remote SHA equality, require exact-SHA green CI, and stop at the next observed compatibility frontier.

## Stop Conditions

Stop without repairing the next wall if:

- the hook affects unrelated classes;
- canonical members cannot be deterministic;
- required behavior needs full `EnumMeta`;
- the overlay requires DD production edits;
- a significant MicroPython fork is necessary;
- the hook becomes a general compatibility framework;
- the next failure is unrelated to `enum`.

MYP5 must be derived from the first real post-enum failure.

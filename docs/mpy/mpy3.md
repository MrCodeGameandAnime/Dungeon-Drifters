# MYP3 - Establish Portable Dataclass Field Discovery

## Summary

Continue MYP3 after the stock MicroPython annotation failure. Dataclass behavior remains viable; only runtime field discovery is blocked.

Preserve:

```text
one authoritative DD source
zero broad production rewrites
zero gameplay changes
zero second gameplay representation
```

Baseline remains MYP2 commit `34f697d419a1e67103bb3e18a23c8fc762b60991`.

## Discovery Ladder

Evaluate in order:

1. Existing MicroPython annotation-retaining configuration or build option.
2. Minimal MicroPython compiler/runtime patch.
3. Generated field metadata.
4. Explicit metadata in production classes as a final fallback only.

Accept options 1 or 2 only when they are reproducible from MicroPython `v1.29.0`, narrowly scoped, and do not create a significant interpreter fork.

Before using generated metadata, qualify:

```text
cls.__module__
cls.__name__
cls.__qualname__ if available
```

Use manifest keys in this order:

```text
(module, qualified class name)
```

Fallback to:

```text
(module, class name)
```

only when `__qualname__` is unavailable or unreliable and the audit proves all relevant classes are top-level.

No bare-name fallback or ambiguous matching is permitted.

## Generated Metadata

Prefer native CPython inspection:

```python
cls.__dataclass_fields__
```

Generation must fail closed if complete discovery requires:

- application startup;
- terminal interaction;
- persistence activity;
- filesystem mutation;
- other unacceptable import side effects.

If those side effects occur, evaluate deterministic AST extraction instead.

At generation time, compare discovered and generated sets dynamically:

```text
discovered production dataclasses
==
generated manifest entries

0 missing
0 unexpected
0 duplicates
exact field-order match
```

The MYP2 count of 74 remains historical evidence, not a permanent limit.

Each MicroPython dataclass must resolve to exactly one manifest key:

```text
missing entry:
hard compatibility error

duplicate or ambiguous entry:
hard generation/validation error

silent fallback:
forbidden
```

The manifest contains only module/class identity and ordered field names. Ordinary defaults remain in class attributes; `field(default_factory=...)` remains represented by the overlay’s field marker.

## Overlay

After field discovery is qualified, add the MicroPython-only overlay outside `root/src`:

```text
root/portability/micropython/dataclasses.py
```

Implement only the MYP2 contract:

- positional and keyword initialization;
- declaration-order fields;
- ordinary defaults;
- `field(default_factory=...)`;
- per-instance factory isolation;
- structural equality;
- frozen assignment rejection;
- `__post_init__`;
- `object.__setattr__` normalization;
- ordered iterable `__dataclass_fields__`.

Do not implement ordering, hashing compatibility, slots, inheritance, metadata, general reflection, or exact repr compatibility.

Use a MicroPython-only bootstrap/path mechanism. Native CPython, Pyodide, Chaquopy, pytest, and packaging must continue using standard-library `dataclasses`.

## Tests And Evidence

Add isolated conformance tests for the qualified contract, manifest freshness, exact identity resolution, missing/duplicate entries, and native import protection.

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pytest root/tests/test_dataclass_contract.py
.\.venv\Scripts\python.exe -m pytest root/tests/test_portable_dataclasses.py
.\.venv\Scripts\python.exe -m compileall root/src root/tests root/tools root/portability
git diff --check
```

Qualify:

```text
native CPython:
native dataclasses pass

forced-overlay CPython:
portable dataclasses pass

MicroPython v1.29.0:
previous dataclasses failure crossed
```

Stop at the first unrelated MicroPython incompatibility. Do not repair unrelated enum, typing, collections, pathlib, persistence, annotation syntax, or gameplay failures in MYP3.

## Documentation And Release

Update `docs/portability/micropython-probe.md` with:

- stock annotation failure;
- class-identity evidence;
- evaluated discovery options;
- import-side-effect decision;
- selected manifest key;
- dynamic discovered-set equality;
- exact one-key resolution requirement;
- overlay contract and unsupported features;
- native, forced-overlay, and MicroPython results;
- memory evidence;
- production/gameplay/content/persistence change counts.

Leave historical untracked paths untouched.

Commit the completed implementation as:

```text
MYP3 - Add Portable Dataclass Overlay
```

Push `myp`, verify local and remote SHA equality, require exact-SHA green CI, and stop at the next observed compatibility frontier.

MYP3 is blocked only if all discovery mechanisms require architectural contamination, broad source rewriting, a significant MicroPython fork, or a second gameplay representation.

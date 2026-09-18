# MPY8 - Add Portable `collections.abc` Boundary

## Summary

Advance MicroPython `v1.29.0` beyond the observed `collections.abc` import failure without modifying `root/src`, gameplay, content, persistence, semantic APIs, or the raw probe.

Repository evidence confirms:

- `Mapping` is used at runtime by `Weapon`.
- `Mapping[str, int]` appears only as a type annotation in `WeaponSpec`.
- `Sequence` is used by `Battle._normalize_enemies`.
- `Counter` is imported separately by `Battle` for duplicate labels.
- MicroPython provides `deque`, `namedtuple`, and `OrderedDict`, but not `Mapping`, `Sequence`, or `Counter`.
- Native `collections` is frozen/non-package-like, rejects adding `abc`, but direct `sys.modules["collections.abc"]` injection supports `from collections.abc import ...`.

MPY8 will cross only the `Mapping`/`Sequence` boundary and stop at the next unrelated raw-probe failure.

## Implementation Changes

Add a MicroPython-only compatibility module at:

```text
root/portability/micropython/collections_abc_compat.py
```

Its installation API will:

- retain the native top-level `collections` module;
- inject only a module-like `collections.abc` child into `sys.modules`;
- export only `Mapping` and `Sequence`;
- install idempotently;
- preserve all native top-level `collections` attributes;
- never synthesize `Counter` or other unqualified ABCs.

On MicroPython, the qualified representations will be:

```python
Mapping = (dict, _ReadonlyMapping)
Sequence = (list, tuple)
```

The bootstrap will temporarily make `root/src` importable to obtain the existing `_ReadonlyMapping` class, install the child module, and restore the prior path arrangement. This is bootstrap plumbing only; no production source changes are permitted.

On CPython forced-compatibility tests, native `collections.abc.Mapping` and `collections.abc.Sequence` will remain available so real annotations such as `Mapping[str, int]` continue to evaluate normally. Under MicroPython, class annotation expressions are not evaluated and `__annotations__` is absent, so generic subscription is recorded as **not runtime-required**, not reimplemented as a typing system.

No global `isinstance` or `issubclass` replacement, metaclass framework, parent-module proxy, or broad ABC implementation will be added.

## Tests And Qualification

Add dynamic contract tests that inspect only `root/src/app/**/*.py` and classify:

- `collections` and `collections.abc` imports;
- imported ABC names;
- `isinstance` and `issubclass` usage;
- generic subscriptions;
- top-level `Counter` imports and operations.

The audit will use discovered sets and fail visibly if unsupported future APIs appear. Tooling, tests, and documentation will remain excluded.

Add isolated compatibility tests proving:

- native CPython still uses standard-library `collections.abc`;
- forced compatibility is active in a subprocess;
- installation is idempotent;
- native `collections` remains retained;
- `from collections.abc import Mapping, Sequence` works;
- dictionaries and `_ReadonlyMapping` values satisfy `Mapping`;
- lists and tuples satisfy `Sequence`;
- strings, bytes, bytearrays, sets, and generators are rejected where DD requires rejection;
- `Mapping[str, int]` is documented according to actual runtime evaluation;
- no speculative `Counter` implementation exists;
- prior dataclass, enum, keyword, and regex overlays remain unaffected.

Exercise the real DD paths for:

- `Weapon(..., stat_bonuses=dict(...))`;
- `WeaponSpec(...)`;
- `WeaponSpec.create_weapon()`;
- valid and invalid content identifiers.

Do not force Battle import past the separate `Counter` dependency merely to manufacture Sequence coverage.

## MicroPython Evidence And Documentation

Run direct qualification under the pinned runtime, then run the unchanged bootstrap probe.

Record:

- native `collections` capabilities;
- failed native `collections.abc` imports;
- dotted-import injection behavior;
- Mapping and Sequence checks;
- `_ReadonlyMapping` recognition;
- annotation-subscription result;
- native `Counter` availability without repairing it;
- real Weapon and WeaponSpec results;
- exact first post-ABC raw-probe stage, exception, message, traceback, memory values, and dataclass census.

Update `docs/portability/micropython-probe.md` with the MPY7 sealed SHA, the dynamic audit, selected mechanism, precise runtime contract, and zero production/gameplay/content/persistence/semantic/raw-probe changes. Do not document speculative MPY9 repairs.

## Verification And Release

Run the full suite, the complete focused portability set including the new collection tests, compileall for `root/src`, `root/tests`, `root/tools`, and `root/portability`, dataclass-manifest freshness, and `git diff --check`.

Review that no `root/src` files, save schema, gameplay, content, raw probe, or prior overlays changed.

Commit exactly:

```text
MPY8 - Add Portable Collections ABC Boundary
```

Push `mpy`, verify local and remote SHA equality, wait for exact-SHA green CI, and stop at the first unrelated MicroPython incompatibility.

Assume the next raw wall may be `Counter`, but do not treat that as fact until the unchanged probe produces the evidence.

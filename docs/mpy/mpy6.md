# MYP6 - Repair Portable StrEnum Construction

**Goal:** Advance the pinned MicroPython probe past the existing-member lookup failure while preserving DD production behavior.

**Baseline:**

```text
Branch: myp
HEAD: 2f656ba3b176e3f8c812d2b12c57a713e5cc8960
MicroPython: v1.29.0
Source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Source checkout: clean
```

## Confirmed Finding

The current overlay already supports:

```text
Sample("first")      -> canonical member
MoveKind("damage")   -> canonical member
```

The actual failure is specifically:

```text
Sample(Sample.FIRST)       -> ValueError
MoveKind(MoveKind.DAMAGE)  -> ValueError
```

DD authored `Move` objects pass existing enum members into `Move.__post_init__`, which normalizes them through `EnumType(value)`. That is why real `Move` construction currently fails under MicroPython.

## Implementation

Modify only:

```text
root/portability/micropython/enum.py
root/tests/test_portable_enum.py
docs/portability/micropython-probe.md
```

In `_lookup_member`, add the narrow canonical-member fast path:

```python
def _lookup_member(cls, value):
    if isinstance(value, cls):
        return value

    try:
        return cls.__members__[value]
    except (KeyError, TypeError):
        raise ValueError(
            "%r is not a valid %s" % (value, cls.__name__)
        )
```

Preserve the existing build-class hook, registry, raw member construction, duplicate detection, malformed-member handling, string behavior, hashing, and `ValueError` semantics.

Do not modify:

```text
root/src
root/tools/micropython_probe.py
dataclass overlay
keyword overlay
bootstrap behavior
gameplay
content
persistence
semantic APIs
```

## Tests

Extend the existing forced-overlay subprocess tests to prove:

- `EnumType("value") is EnumType.MEMBER`.
- `EnumType(EnumType.MEMBER) is EnumType.MEMBER`.
- Unknown values raise `ValueError`.
- Both lookup forms work for every discovered member of every production DD enum.
- `MoveKind("damage") is MoveKind.DAMAGE`.
- `MoveKind(MoveKind.DAMAGE) is MoveKind.DAMAGE`.
- A real `Move` constructed with authored enum members succeeds and preserves canonical enum identity.
- A real `Move` constructed with raw string enum values still succeeds.
- All existing forced-overlay, native-import, ordinary-class, dataclass, duplicate, malformed-member, and census tests remain green.
- Forced-overlay tests use subprocesses and prove the overlay module is active rather than cached CPython `enum`.

The real `Move` regression must use the authored-content form:

```python
Move(
    name="probe",
    kind=MoveKind.DAMAGE,
    resource_type=ResourceType.NONE,
    resource_cost=0,
    power=1,
    scales_with=(ScalingAttribute.STRENGTH,),
    accuracy=100,
    target=TargetType.ENEMY,
    damage_type=DamageType.PHYSICAL,
    mechanic="basic_attack",
    description="probe",
)
```

Also retain the complementary raw-string form.

## MicroPython Qualification

Run a disposable direct qualification under the pinned interpreter covering:

```text
synthetic enum raw-string lookup
synthetic enum existing-member lookup
MoveKind raw-string lookup
MoveKind existing-member lookup
real Move construction with enum members
real Move construction with strings
```

Then run the unchanged raw probe through the existing bootstrap.

Record:

- exact `MoveKind` and `Move` results;
- the first post-enum stage reached;
- exact stage, exception type, message, and traceback;
- memory evidence;
- dynamic dataclass census values;
- confirmation that the enum failure is crossed;
- confirmation that no unrelated failure was repaired in MYP6.

The next unrelated MicroPython incompatibility is the stop point.

## Documentation

Update `docs/portability/micropython-probe.md` with:

- the original MYP5 failure;
- the distinction between raw-string and existing-member lookup;
- the authored `Move` normalization path that exposed the defect;
- the selected `isinstance(value, cls)` correction;
- exact native CPython and forced-overlay results;
- exact pinned MicroPython output after the correction;
- the next compatibility frontier and original traceback;
- memory and dataclass census evidence;
- zero `root/src` production changes;
- zero gameplay, content, persistence, semantic API, and raw-probe changes.

## Verification And Release

Run:

```powershell
Push-Location root
& ..\.venv\Scripts\python.exe -m pytest
& ..\.venv\Scripts\python.exe -m pytest `
  tests\test_dataclass_contract.py `
  tests\test_portable_dataclasses.py `
  tests\test_enum_contract.py `
  tests\test_portable_enum.py `
  tests\test_keyword_contract.py `
  tests\test_portable_keyword.py
Pop-Location

.\.venv\Scripts\python.exe -m compileall root\src root\tests root\tools root\portability
.\.venv\Scripts\python.exe root\tools\generate_dataclass_manifest.py --check
git diff --check
```

Review the diff for:

```text
root/src production changes: 0
gameplay changes: 0
content changes: 0
persistence changes: 0
semantic API changes: 0
raw probe changes: 0
speculative compatibility work: 0
```

Commit exactly:

```text
MYP6 - Repair Portable StrEnum Construction
```

Push `myp`, verify local HEAD equals `origin/myp`, require exact-SHA green CI, and stop at the next unrelated MicroPython incompatibility.

MYP6 is blocked only if canonical existing-member normalization cannot be implemented without DD production rewrites, a general compatibility framework, or a significant MicroPython fork.

# MYP5 - Add Portable Keyword Overlay

## Summary

Advance the pinned MicroPython `v1.29.0` probe beyond the observed `keyword` import failure at `app.content.enemy_spec`, without modifying `root/src`, gameplay, content, persistence, semantic APIs, or the raw probe.

Baseline:

```text
Branch: myp
HEAD: 0a9677d58f80e90f80d50e6ac885a43c4279878e
MicroPython: v1.29.0
Source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Platform: win32
```

Historical untracked `docs/mpy/` files remain untouched.

## Implementation

Add `root/portability/micropython/keyword.py`.

Expose only:

```python
iskeyword(value)
```

Use a private immutable tuple containing the current CPython hard-keyword set:

```text
False, None, True, and, as, assert, async, await, break,
class, continue, def, del, elif, else, except, finally, for,
from, global, if, import, in, is, lambda, nonlocal, not, or,
pass, raise, return, try, while, with, yield
```

Do not include soft keywords:

```text
_, case, match, type
```

The function must match native CPython `keyword.iskeyword()` for string inputs. No broader arbitrary-object compatibility is required.

The existing portability bootstrap remains the only authority that selects the overlay. Native CPython, Pyodide, Chaquopy, pytest, packaging, and tooling must continue importing the standard-library `keyword` module.

Do not modify:

```text
root/src
root/tools/micropython_probe.py
```

Do not add content-specific validation to the overlay. Existing DD validators remain responsible for ID syntax, casing, punctuation, and whitespace rules.

## Audit, Tests, And Documentation

Add focused tests:

```text
root/tests/test_keyword_contract.py
root/tests/test_portable_keyword.py
```

The contract audit must dynamically inspect `root/src/app` and verify:

- every runtime `keyword` import is identified;
- every current runtime use is exactly `keyword.iskeyword(...)`;
- unsupported APIs such as `kwlist`, `softkwlist`, `issoftkeyword`, reflection, and mutation are not used;
- tooling references under `root/tools` are not mistaken for runtime dependencies;
- future production use of an unsupported keyword API fails the audit.

The portable tests must prove:

- native CPython resolves the standard-library `keyword`;
- forced overlay resolution points directly to `root/portability/micropython/keyword.py`;
- cached native `keyword` cannot silently satisfy the forced test;
- hard keywords return `True`;
- ordinary identifiers return `False`;
- soft-keyword behavior matches the running CPython version;
- portable and native behavior agree across the authoritative hard-keyword set;
- representative DD identifiers such as `goblin`, `ember_shard`, and `dungeon_entrance` behave correctly;
- real `EnemySpec`, `DrifterSpec`, route-ID, and weapon-ID validators accept valid IDs and reject Python keywords through the existing production paths;
- punctuation, whitespace, and casing remain rejected by the existing combined validators;
- no validation rules are duplicated inside `keyword.py`;
- portable dataclass and StrEnum behavior remain unaffected.

Forced-overlay tests must run in subprocesses and explicitly verify module origin. Normal host imports must remain native.

Update `docs/portability/micropython-probe.md` with a new MYP5 section covering:

- the original `keyword` failure;
- dynamically discovered production call sites;
- the supported and unsupported keyword APIs;
- hard-keyword authority and soft-keyword distinction;
- overlay design and native-module isolation;
- real DD validator evidence;
- native CPython and forced-overlay results;
- pinned MicroPython output;
- updated dataclass census and memory evidence;
- the first post-keyword failure and original traceback;
- zero `root/src` production, gameplay, content, persistence, and semantic API changes.

Do not add a special keyword stage to the raw probe and do not document speculative repairs for the next failure.

## Verification And Release

Run from the actual nested project root so repository-relative tests resolve correctly:

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
```

Then run:

```powershell
.\.venv\Scripts\python.exe -m compileall root\src root\tests root\tools root\portability
.\.venv\Scripts\python.exe root\tools\generate_dataclass_manifest.py --check
git diff --check
```

Run:

```text
native CPython raw probe
forced-overlay CPython raw probe
pinned MicroPython v1.29.0 probe through the existing bootstrap
```

The pinned run must demonstrate that:

```text
ImportError: no module named 'keyword'
```

is gone, then stop at the first unrelated compatibility failure. Preserve the exact stage, exception, message, traceback, memory values, and dataclass census.

Review the diff to confirm:

```text
root/src production changes: 0
gameplay changes: 0
content changes: 0
persistence changes: 0
semantic API changes: 0
raw probe changes: 0
no speculative compatibility work
```

Commit exactly:

```text
MYP5 - Add Portable Keyword Overlay
```

Push `myp`, verify local and remote SHA equality, require green exact-SHA CI, and stop at the next observed compatibility frontier.

## Assumptions

- The existing bootstrap’s overlay path insertion is sufficient; no bootstrap modification is expected.
- The current CPython `3.14.6` hard-keyword list is the authoritative data source for this gate.
- A future Python-version change should make tests fail visibly rather than silently changing the overlay.
- The next unrelated MicroPython failure defines MYP6.

# MPY7 - Add Portable Regex Fullmatch Boundary

**Goal:** Advance MicroPython `v1.29.0` past the missing `re.fullmatch` behavior while preserving DD production source and native regex semantics.

**Baseline:**

```text
Branch: mpy
HEAD: a97def8f26d811b08fe650157296a8da57bcb6a8
MicroPython: v1.29.0
Source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
Platform: win32
```

## Confirmed Runtime Findings

MicroPython provides:

```text
re.compile   PASS
re.match     PASS
re.search    PASS
re.fullmatch FAIL
```

Compiled patterns provide `.match()` and `.search()`, but not `.fullmatch()`. Match objects do not provide `.start()`, `.end()`, or `.span()`, but do provide:

```python
match.group(0)
```

Import precedence confirms MicroPython’s frozen native `re` wins over a path-inserted `re.py`.

The selected mechanism is therefore a bootstrap-installed proxy around the retained native `re` module.

## Implementation

### Native Regex Proxy

Create:

```text
root/portability/micropython/re_compat.py
```

Expose:

```python
install(native_re)
```

The module must never import `re` internally after installation. The ownership flow is:

```text
bootstrap imports native frozen re
        ↓
install(native_re)
        ↓
proxy privately retains native_re
        ↓
sys.modules["re"] = proxy
        ↓
DD imports re normally
```

The proxy will:

- delegate unknown module attributes to native `re`;
- expose `compile(pattern, flags=0)`;
- expose module-level `fullmatch(pattern, string)`;
- return a wrapped pattern from `compile`;
- expose compiled `.fullmatch(string)`;
- return the original native match object on success;
- use `native_match.group(0) == string` for complete-consumption detection.

The qualified call shape is:

```python
re.compile(pattern)
compiled.fullmatch(value)
re.fullmatch(pattern, value)
```

Because DD does not use flags, `flags=0` will call native compile with one argument. Nonzero flags will fail explicitly rather than being silently widened into an unsupported contract.

The installation API must be idempotent:

```text
install(native_re) -> proxy
install(proxy)     -> same proxy
install(native_re) -> same retained proxy within the process
```

A native pattern created before installation must remain native and must not gain `.fullmatch()` retroactively. Only patterns created through the proxy receive the wrapper.

### Bootstrap

Modify only:

```text
root/tools/micropython_probe_bootstrap.py
```

Install the proxy only when:

```python
sys.implementation.name == "micropython"
```

Normal CPython bootstrap behavior must remain unchanged and must continue using standard-library `re`.

No fake MicroPython mode, `sys.implementation` mutation, `root/portability/micropython/re.py`, raw-probe modification, DD production edit, gameplay change, persistence change, or schema change is permitted.

## Tests

Create:

```text
root/tests/test_regex_contract.py
root/tests/test_portable_regex.py
```

### Contract audit

Dynamically inspect only `root/src/app/**/*.py` and verify:

- every production `re` import is discovered;
- every `re.compile` call is classified;
- every module-level regex call is classified;
- every compiled-pattern call is classified;
- the current runtime surface uses only `compile`, compiled `fullmatch`, and module-level `fullmatch`;
- unsupported future regex APIs fail the audit;
- tooling, tests, and documentation are excluded from runtime dependency results;
- no production code depends on match-position APIs, match metadata, bytes patterns, scanners, reflection, or unsupported compiled operations.

Do not use fixed file, pattern, or call counts.

### Forced compatibility tests

Run in subprocesses to prevent module mutation from leaking into pytest.

Prove:

- native CPython imports standard-library `re`;
- the forced subprocess imports native `re` before installation;
- `install(native_re)` creates the proxy;
- repeated installation is idempotent;
- `sys.modules["re"]` resolves to the proxy;
- the proxy retains the original native module;
- a pre-existing native pattern remains unwrapped;
- `re.compile(...)` returns a wrapped pattern;
- unknown module and pattern operations delegate to native `re`;
- nonzero compile flags fail explicitly.

### Fullmatch behavior

Cover:

```text
module-level fullmatch success
module-level fullmatch prefix rejection
compiled fullmatch success
compiled fullmatch prefix rejection
anchored patterns
unanchored patterns
empty strings
invalid characters
uppercase identifiers
leading underscores
whitespace
trailing punctuation
```

Use:

```text
goblin
goblin_2
a
goblin!
goblin extra
Goblin
_goblin
""
```

Require native CPython and forced compatibility to agree on match versus no-match for every dynamically discovered production regex literal.

### DD validators

Under forced compatibility, exercise:

- `EnemySpec.archetype_id`;
- `DrifterSpec.drifter_id`;
- `DrifterSpec.starting_weapon_id`;
- route/content IDs;
- `Weapon.item_id`.

Verify valid identifiers are accepted and invalid syntax remains rejected by existing DD validators.

Retain keyword cases:

```text
class
for
return
```

These must continue to be rejected through the existing regex plus MPY5 keyword boundary. No validation rules may be duplicated inside `re_compat`.

Re-run existing portable dataclass, StrEnum, and keyword tests.

## MicroPython Qualification

Before the raw probe, run a direct disposable qualification under the pinned interpreter covering:

```text
native re import
native compile
native pattern match/search capabilities
compiled fullmatch on exact input
compiled fullmatch rejection of prefix input
module-level fullmatch on exact input
module-level fullmatch rejection of prefix input
one real DD compiled pattern
EnemySpec validation
Weapon validation
```

Then run the unchanged raw probe through:

```text
root/tools/micropython_probe_bootstrap.py
```

Record:

- exact output after crossing the `re.fullmatch` wall;
- first unrelated failure;
- stage;
- exception type;
- exception message;
- original traceback;
- memory evidence;
- dynamic dataclass census.

Do not repair the next failure.

## Documentation

Update:

```text
docs/portability/micropython-probe.md
```

Record:

- MPY6 sealed SHA;
- original `re.fullmatch` failure;
- dynamic production regex audit;
- native MicroPython capabilities;
- absence of match-position APIs;
- `group(0)` full-consumption strategy;
- frozen-module import precedence;
- why `re.py` overlay is not viable;
- bootstrap-installed proxy design;
- native module ownership and lifetime;
- idempotent installation;
- explicit nonzero-flags behavior;
- native-pattern versus proxy-pattern behavior;
- native and forced CPython results;
- direct MicroPython results;
- next raw-probe frontier;
- memory and dataclass census;
- zero `root/src` changes;
- zero gameplay, content, persistence, semantic API, and raw-probe changes.

Do not document speculative MPY8 repairs.

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
  tests\test_portable_keyword.py `
  tests\test_regex_contract.py `
  tests\test_portable_regex.py

Pop-Location

.\.venv\Scripts\python.exe -m compileall `
  root\src `
  root\tests `
  root\tools `
  root\portability

.\.venv\Scripts\python.exe root\tools\generate_dataclass_manifest.py --check
git diff --check
```

Review the exact diff for:

```text
root/src changes: 0
gameplay changes: 0
content changes: 0
persistence changes: 0
semantic API changes: 0
raw probe changes: 0
regex engine/parser: 0
schema changes: 0
historical docs/mpy changes: 0
```

Commit exactly:

```text
MPY7 - Add Portable Regex Fullmatch Boundary
```

Push `mpy`, verify local HEAD equals `origin/mpy`, require exact-SHA green CI, and stop at the next unrelated MicroPython incompatibility.

MPY7 is blocked if full-match semantics cannot be reproduced from native MicroPython regex behavior, the proxy requires production rewrites, authored-pattern changes, a general regex implementation, or a significant MicroPython fork.

# MYP10 - Remove Counter Runtime Dependency

## Summary

Remove Battle’s narrow `collections.Counter` dependency using ordinary dictionary operations, preserving exact enemy-label behavior and stopping at the next unrelated MicroPython incompatibility.

Baseline:

- Branch: `myp`
- HEAD: `d78c07293219116f04f9c203b6654bf8b9728e35`
- MicroPython: `v1.29.0`
- Source SHA: `0fd6c573ea815774668bbb16b8e197c8822368b2`
- Historical `docs/mpy/` files remain untouched and untracked.

## Implementation

Modify `root/src/app/combat/battle.py`:

- Remove `from collections import Counter`.
- Replace Counter construction, lookup, and increment operations with dictionaries using `.get(name, 0)`.
- Preserve unique labels, duplicate numbering, authored enemy order, target IDs, Battle views, and identity rejection.

Update `root/tests/test_collections_contract.py` to dynamically inspect only `root/src/app/**/*.py` and require:

- no production `Counter` imports;
- no production `Counter(...)` calls;
- no Counter-backed subscriptions;
- no Counter-backed mutations;
- existing `Mapping` and `Sequence` behavior unchanged.

Add `root/tests/test_portable_counter_removal.py` for semantic equivalence and real Battle qualification.

Do not add a Counter overlay, collections proxy, bootstrap change, raw-probe change, API change, persistence change, or gameplay change.

## Tests And Qualification

Cover labels for:

- one unique enemy;
- two distinct enemy instances with the same display name;
- three distinct enemy instances with the same display name;
- two different names;
- duplicate names separated by another name;
- multiple duplicate groups;
- the four-enemy maximum composition.

Explicitly prove:

```text
distinct same-name enemy instances
-> accepted
-> numbered independently

the same EnemyState or EnemyCombatant instance supplied twice
-> existing identity rejection remains unchanged
```

Preserve `enemy_target_ids` and `enemy_display_labels` exactly.

Compare the new implementation against a test-only native `Counter` reference over generated display-name sequences.

Re-run all MYP3 through MYP9 portability tests, including dataclasses, StrEnum, keyword, regex, collections.abc, and ASCII string validation.

## Direct MicroPython Qualification

Record:

```text
collections.Counter: unavailable
```

Then run the complete compatibility stack and attempt these checks in order:

```text
import app.combat.battle
real single-enemy Battle
real multi-enemy Battle
duplicate labels
mixed duplicate labels
```

The historical failure:

```text
ImportError: can't import name Counter
```

must not recur.

If a direct qualification step exposes a new unrelated MicroPython incompatibility, record its exact stage, exception, message, traceback, memory evidence, and dataclass census, then stop. Later direct qualification steps are not required to pass after that frontier is reached.

Run the unchanged raw probe through the existing bootstrap. Continue only until the first unrelated failure. Do not repair that failure in MYP10.

## Documentation

Update `docs/portability/micropython-probe.md` with:

- MYP9 sealed SHA;
- original Counter import failure;
- dynamic production Counter audit;
- exact Battle label contract;
- dictionary rewrite rationale;
- rejection of Counter emulation;
- CPython semantic-equivalence results;
- real Battle qualification results;
- direct MicroPython results;
- unchanged raw-probe output through the next frontier;
- memory values and dataclass census;
- exact scope counts.

Record:

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
```

Do not document speculative repairs for the next frontier.

## Verification And Release

From the repository root, run:

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
  tests\test_portable_regex.py `
  tests\test_collections_contract.py `
  tests\test_portable_collections_abc.py `
  tests\test_string_contract.py `
  tests\test_portable_string_validation.py `
  tests\test_portable_counter_removal.py
Pop-Location

.\.venv\Scripts\python.exe -m compileall `
  root\src `
  root\tests `
  root\tools `
  root\portability

.\.venv\Scripts\python.exe root\tools\generate_dataclass_manifest.py --check
git diff --check
```

Also run:

- native CPython raw probe;
- forced compatibility CPython raw probe;
- direct pinned MicroPython qualification;
- pinned MicroPython raw probe through the existing bootstrap.

Review that only Battle, focused tests, and portability documentation changed. Confirm:

- no overlay changes;
- no bootstrap changes;
- no raw-probe changes;
- no save/schema changes;
- no generated catalog changes;
- no MYP3 through MYP9 changes;
- no historical `docs/mpy/` changes.

Commit exactly:

```text
MYP10 - Remove Counter Runtime Dependency
```

Push `myp`, verify local and remote SHA equality, require exact-SHA green CI, and stop at the next observed compatibility frontier.

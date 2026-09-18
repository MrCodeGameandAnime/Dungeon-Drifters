# MYP12 - Repair Portable Starred Tuple Expressions

## Summary

Advance pinned MicroPython `v1.29.0` beyond the `*x must be assignment target` parser failure from MYP11 baseline `bd7726bb7d73cb7d2c3967071828de05ebdc72a9`.

The complete audit found 9 load-context starred tuple displays across 4 production presentation files:

- `battle_session.py`: 1
- `character_profile_presenter.py`: 1
- `terminal_battle_ui.py`: 4
- `terminal_overworld_ui.py`: 3

Treat them as one syntax boundary and replace all nine with equivalent ordinary tuple construction.

## Implementation

Update only these production files:

- `root/src/app/presentation/battle_session.py`
- `root/src/app/presentation/character_profile_presenter.py`
- `root/src/app/ui/terminal_battle_ui.py`
- `root/src/app/ui/terminal_overworld_ui.py`

Use tuple concatenation or an equivalent ordinary-Python expression preserving:

- tuple result type;
- evaluation order;
- multiplicity;
- conditional behavior;
- presentation ordering;
- snapshot isolation;
- existing return contracts.

Examples:

```python
("prefix", *values)
→ ("prefix",) + tuple(values)

(*values, final_value)
→ tuple(values) + (final_value,)

("prefix", *values_a, *values_b)
→ ("prefix",) + tuple(values_a) + tuple(values_b)
```

Do not modify:

- `*args` or `**kwargs`;
- assignment-target unpacking;
- `for` or comprehension targets;
- list or set starred displays;
- other starred syntax not identified as this gate’s failure;
- test-only reference syntax;
- compatibility overlays;
- bootstrap files;
- the raw probe;
- battle-log retention, gameplay, persistence, or schema behavior.

## Tests and Documentation

Add `root/tests/test_starred_tuple_contract.py`.

The AST audit must dynamically inspect only `root/src/app/**/*.py` and enforce:

```text
production load-context starred tuple displays == 0
```

It must classify, but not automatically reject or label as MicroPython-proven, these other forms:

```text
function-call starred arguments
assignment targets
comprehension and for targets
list displays
set displays
other non-target contexts
```

Test the classifier itself with synthetic AST samples for each category. Do not require the post-change working tree to rediscover the original nine occurrences; record the baseline census and exact locations in `docs/portability/micropython-probe.md`.

Strengthen `root/tests/test_battle_presentation_session.py` to prove:

- empty entries return `()`;
- history order and snapshot isolation remain unchanged;
- transient rejection appears exactly once at the end;
- replacement rejection replaces only the transient value;
- history capacity is unaffected;
- results are tuples;
- reads do not mutate the internal list-backed history.

The focused MYP12 suite must include protection for all four changed production surfaces:

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
  tests\test_portable_counter_removal.py `
  tests\test_typing_contract.py `
  tests\test_portable_typing.py `
  tests\test_battle_presentation_session.py `
  tests\test_starred_tuple_contract.py `
  tests\test_character_profiles.py `
  tests\test_terminal_battle_ui.py `
  tests\test_terminal_overworld_ui.py

Pop-Location
```

Update `docs/portability/micropython-probe.md` with:

- MYP11 sealed SHA;
- baseline evidence of 9 unsupported tuple displays across 4 files;
- the AST classification boundary;
- direct MicroPython parser failure;
- tuple-concatenation qualification;
- semantic-equivalence results;
- direct qualification of all four changed-module imports;
- representative corrected-path results;
- exact post-change raw-probe output;
- next unrelated stage, exception, traceback, memory, and census;
- MYP12 scope counts;
- MYP13 derived from the next observed frontier.

Historical `docs/mpy/` files remain untouched and uncommitted.

## MicroPython Qualification

Before source edits, directly qualify under the pinned runtime:

```text
(*entries, value)
→ SyntaxError: *x must be assignment target

entries + (value,)
→ PASS
```

Verify empty, single-entry, multi-entry, ordering, unchanged source tuple, and tuple result type.

After the corrections, use the complete existing compatibility stack and import all four changed modules:

```text
app.presentation.battle_session
app.presentation.character_profile_presenter
app.ui.terminal_battle_ui
app.ui.terminal_overworld_ui
```

All four imports must pass. Also exercise one inexpensive corrected path from each module where possible:

- `BattlePresentationSession.entries` with transient rejection;
- `render_roster()` with canonical Drifter specifications;
- a terminal battle control or render path;
- a terminal overworld option, equipment, or render path.

If a later step exposes a new unrelated MicroPython wall, record it and stop without repairing it in MYP12.

Run the unchanged raw probe through `root/tools/micropython_probe_bootstrap.py`. The previous `battle_session.py:30` syntax failure must disappear. Continue only to the first unrelated frontier and preserve its original traceback, memory evidence, and dynamic dataclass census.

## Verification and Release

After implementation, run the full pytest suite first, followed by the focused cumulative suite above.

Then run:

```powershell
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
- forced-overlay CPython raw probe;
- direct pinned-MicroPython starred-tuple qualification;
- direct pinned-MicroPython qualification of all four changed modules;
- unchanged pinned-MicroPython bootstrap probe.

Review the final diff and require:

```text
production files changed: 4
load-context starred tuple displays: 9 → 0
typing/dataclass/enum/keyword/regex/collections overlays changed: 0
runtime contracts changed: 0
bootstrap changed: 0
raw probe changed: 0
gameplay changed: 0
content changed: 0
persistence/save schema changed: 0
historical docs/mpy changed: 0
```

Commit exactly:

```text
MYP12 - Repair Portable Starred Tuple Expression
```

Push `myp`, verify local HEAD equals `origin/myp`, wait for exact-SHA green CI, and report the commit, full/focused test totals, exact next MicroPython frontier, memory/census evidence, synchronization, and preserved historical untracked files.

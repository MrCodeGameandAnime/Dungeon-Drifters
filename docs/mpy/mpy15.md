# MYP15 - Remove Itertools Groupby Runtime Dependency

**Goal:** Advance pinned MicroPython v1.29.0 beyond the sealed MYP14 `itertools` import failure without adding compatibility machinery or changing encounter behavior.

**Baseline:** `myp` at `3af2e4d2da435f29b6559f087aeb0a705cbe0fd0`, synchronized with `origin/myp`. Historical `docs/mpy/` files remain untouched.

## Implementation

1. Before editing, dynamically audit `root/src/app/**/*.py` and require exactly:
   - one `itertools` import;
   - one imported member, `groupby`;
   - one `groupby` call at `OverworldPresenter._map_encounter_inspection_view`.

   Stop and report if the census differs.

2. Modify only `root/src/app/presentation/overworld_presenter.py`:
   - remove `from itertools import groupby`;
   - add private `_adjacent_run_counts(values)`;
   - replace the single `groupby` loop with the helper;
   - preserve authored order, adjacent-run boundaries, empty/singleton behavior, naive pluralization, boss flags, immutable views, and non-mutating inspection.

   Required helper behavior:
   ```python
   () -> ()
   ("a",) -> (("a", 1),)
   ("a", "a", "b", "a") -> (("a", 2), ("b", 1), ("a", 1))
   ```

3. Do not modify `Battle`, `OverworldSession`, content, route definitions, persistence, bootstrap, raw probes, or any portability overlay.

## Tests

Modify `root/tests/test_m10b_map_inspection.py` to import test-only CPython `itertools.groupby`, the private helper, and add a `groupby_reference()` oracle. Compare the helper against that oracle for empty, singleton, duplicate, separated-duplicate, alternating, and multi-run sequences.

Preserve all authored map-inspection tests, including composition labels, rest lookahead, boss handling, immutability, non-mutation, and the prohibition on runtime enemy construction.

Create `root/tests/test_itertools_contract.py` with a dynamic AST audit restricted to `root/src/app/**/*.py`. It must:

- reject all `import itertools` and `from itertools import ...` production imports;
- classify aliases and multi-member imports;
- allow unrelated imports and test-only `itertools`;
- enforce zero production `itertools` imports;
- include synthetic AST cases proving the classifier’s scope.

## Runtime Qualification

Record pinned MicroPython evidence independently:

```text
import itertools
→ ImportError: no module named 'itertools'

from itertools import groupby
→ independently observed failure
```

After the correction, qualify `_adjacent_run_counts` under the existing compatibility bootstrap with:

```text
()
("a",)
("a", "a", "b", "a")
```

If importing `overworld_presenter` to qualify `_adjacent_run_counts` reaches a new unrelated MicroPython dependency first, record that dependency as the next MYP16 frontier. Do not broaden MYP15 or treat that unrelated import failure as evidence that the helper correction failed. The CPython `groupby` oracle remains the semantic authority.

Then run the unchanged bootstrap probe. The historical failure specifically caused by:

```text
SESSION_IMPORT
ImportError: no module named 'itertools'
```

must disappear.

`SESSION_IMPORT` may still fail at a new unrelated dependency. If so, record that failure as the MYP16 frontier and do not repair it. Continue only with MYP15 documentation, verification, commit, push, and exact-SHA CI.

Record the last passing stage, first new failing stage or complete-result marker, exception type/message, original traceback, `FREE`, `ALLOC`, and the dynamic dataclass census. Native and forced-overlay CPython probes must still complete all stages.

## Verification And Release

Run the full suite from `root`.

Run the exact sealed MYP14 cumulative suite, which produced 233 passed, with these two additions appended:

```text
tests/test_dataclass_contract.py
tests/test_portable_dataclasses.py
tests/test_enum_contract.py
tests/test_portable_enum.py
tests/test_keyword_contract.py
tests/test_portable_keyword.py
tests/test_regex_contract.py
tests/test_portable_regex.py
tests/test_collections_contract.py
tests/test_portable_collections_abc.py
tests/test_string_contract.py
tests/test_portable_string_validation.py
tests/test_portable_counter_removal.py
tests/test_typing_contract.py
tests/test_portable_typing.py
tests/test_battle_presentation_session.py
tests/test_starred_tuple_contract.py
tests/test_character_profiles.py
tests/test_terminal_battle_ui.py
tests/test_strict_zip_contract.py
tests/test_save_contract.py
tests/test_session_persistence_boundary.py
tests/test_save_repository.py
tests/test_overworld_session.py
tests/test_runtime_overworld.py
tests/test_m10b_map_inspection.py
tests/test_itertools_contract.py
```

Run compileall for `root/src`, `root/tests`, `root/tools`, and `root/portability`; run the dataclass manifest freshness check and `git diff --check`.

Review the final diff to require:

```text
production itertools imports: 1 -> 0
groupby calls: 1 -> 0
production files changed: 1
itertools overlay: 0
bootstrap changes: 0
raw probe changes: 0
gameplay/content/route changes: 0
persistence/schema changes: 0
historical docs/mpy changes: 0
```

Update `docs/portability/micropython-probe.md` with the MYP14 frontier, exact census, adjacent-run semantics, helper correction, CPython oracle evidence, authored map-inspection evidence, runtime results, next MYP16 frontier, memory/census values, test totals, and scope counts. Explicitly state that MYP15 adds no `itertools` overlay and changes no authored encounter composition, gameplay, or session state.

Commit exactly:

```text
MYP15 - Remove Itertools Groupby Runtime Dependency
```

Push `myp`, verify local HEAD equals `origin/myp`, wait for exact-SHA green CI, confirm the tracked worktree is clean, and report the next frontier.

Stop and request a revised MYP15 plan only if the historical `itertools` failure is not crossed or crossing it requires work outside the authorized MYP15 scope. Do not repair or investigate a new unrelated frontier during MYP15.

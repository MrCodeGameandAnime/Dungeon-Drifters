# MYP14 - Decouple Session Persistence Import Boundary

**Goal:** Remove the eager concrete `SaveRepository` dependency from `OverworldSession` so pinned MicroPython can import and construct a headless session without porting disk persistence.

**Baseline:** Branch `myp`, commit `cc66563cd94c442ca4b1a95afbe09d1dca3a4828`; MicroPython `v1.29.0`, source SHA `0fd6c573ea815774668bbb16b8e197c8822368b2`.

## Implementation

- Create `root/src/app/game/save_contract.py` containing `SaveLoadStatus`, `SaveRepositoryError`, and `is_save_repository(value)` using structural callable requirements for `save`, `inspect`, and `load`.
- Modify `root/src/app/game/save_repository.py` to import those definitions from `save_contract.py`.
- Preserve `save_repository.py`’s existing `__all__` exports for `SaveLoadStatus` and `SaveRepositoryError`, along with all existing public imports.
- Leave `SaveLoadResult`, `SaveRepository`, schema handling, JSON serialization, atomic temporary writes, cleanup, migration behavior, and save semantics unchanged.
- Modify `root/src/app/game/overworld_session.py` to remove its module-level `save_repository` import.
- Validate injected repositories structurally while preserving the existing `TypeError` message.
- Store `None` unresolved and add `_save_repository_instance()` with a function-local concrete `SaveRepository` import.
- Use the lazy resolver only in `_load_available()`, `_save_current_session()`, and `_load_saved_session()`.
- Preserve desktop `main_loop.py`, gameplay, route progression, and all persistence behavior. Add no filesystem overlay, interpreter branch, bootstrap change, raw-probe change, or SAVE-ARCH design.

## Tests

Create exactly:

```text
root/tests/test_save_contract.py
root/tests/test_session_persistence_boundary.py
```

`test_save_contract.py` will cover structural repository acceptance/rejection and identity-preserving re-exports.

`test_session_persistence_boundary.py` will cover:

- no default repository construction during session construction or initial `current_view()`;
- one lazy construction when Options inspects load availability, followed by reuse;
- injected repositories bypassing the default constructor;
- immediate rejection of incomplete/non-callable repositories;
- the module-level import boundary, allowing only the function-local lazy import;
- unchanged real `SaveRepository` behavior through existing save/load tests.

## Qualification And Documentation

- Confirm pinned MicroPython still fails on `import tempfile`.
- Confirm `save_contract` import, `overworld_session` import, headless session construction, and initial view.
- Run the unchanged raw probe and record the actual last pass or complete-result marker, next failure, traceback, memory, and dataclass census.
- Update `docs/portability/micropython-probe.md` with the MYP13 frontier, concrete import closure, lazy contract correction, qualification evidence, test totals, and explicit MYP14-not-SAVE-ARCH scope.

## Verification

Run the full suite, then use the exact sealed MYP13 cumulative command that produced 194 passing tests:

```powershell
Push-Location root

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
  tests\test_strict_zip_contract.py `
  tests\test_save_contract.py `
  tests\test_session_persistence_boundary.py `
  tests\test_save_repository.py `
  tests\test_overworld_session.py `
  tests\test_runtime_overworld.py

Pop-Location
```

Then run compileall for `root/src`, `root/tests`, `root/tools`, and `root/portability`, dataclass-manifest freshness, `git diff --check`, native/forced CPython probes, and all pinned MicroPython qualifications.

Commit exactly:

```text
MYP14 - Decouple Session Persistence Import Boundary
```

Push `myp`, verify local SHA equals `origin/myp`, require exact-SHA green CI, and confirm the only remaining untracked files are the untouched historical `docs/mpy/` paths.

Stop if crossing `SESSION_IMPORT` requires porting `SaveRepository`, changing save schema or payload behavior, modifying the probe/bootstrap, adding interpreter-specific gameplay branches, or repairing the next unrelated MicroPython frontier.

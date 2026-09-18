# MPY13 - Repair Portable Strict Zip Boundary

## Summary

Remove the five unsupported `strict=True` keyword arguments identified by the sealed MPY13 audit. Preserve all existing alignment guarantees, presenter validation, Battle ownership, terminal rendering, and gameplay behavior.

No compatibility helper, bootstrap change, raw-probe change, or broader keyword portability work is included.

## Implementation

- Remove `strict=True` from:
  - `Battle._display_name_for`
  - `Battle._enemy_for_target_id`
  - `BattlePresenter.build`
  - `BattlePresenter._target_options`
  - `TerminalBattleUI._enemy_side_lines`
- Keep `BattlePresenter._metadata_values()` unchanged as the authoritative validation for caller-supplied metadata lengths.
- Preserve Battle-owned tuple construction and terminal width derivation exactly.
- Add a dynamic `root/tests/test_strict_zip_contract.py` audit enforcing zero production builtin `zip` calls with any `strict` keyword.
- Add presenter regression tests for mismatched `enemy_target_ids` and `enemy_display_labels`, including exact `ValueError` messages.
- Update `docs/portability/micropython-probe.md` with the audit evidence, runtime preflight results, classifications, test totals, and post-change MicroPython frontier.

## Verification

Run the full pytest suite, cumulative portability tests, compileall, dataclass-manifest freshness, and `git diff --check`.

Run native and forced-overlay probes, then pinned MicroPython qualifications for:

- `zip(strict=True)` failure;
- `zip(strict=False)` failure;
- ordinary zip success;
- unchanged raw probe through the existing bootstrap.

Confirm:

- production strict-zip calls change from `5` to `0`;
- BattlePresenter mismatch validation remains intact;
- valid multi-enemy associations remain unchanged;
- the raw probe crosses the previous `BattlePresenter.build()` failure;
- the next unrelated compatibility frontier is recorded without repair.

Commit exactly:

`MPY13 - Repair Portable Strict Zip Boundary`

Push `mpy`, verify exact local/remote SHA equality and green exact-SHA CI, then stop.

## Assumptions

- All five audited sites are safe to convert to ordinary `zip()` based on their existing construction or validation guarantees.
- No explicit replacement length checks are needed at the four construction-guaranteed sites.
- The terminal `shutil` frontier remains deferred.
- MPY14 will be derived only from the next observed MicroPython failure.

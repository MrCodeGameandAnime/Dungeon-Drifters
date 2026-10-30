# T0 Local Qualification Evidence

**Date:** 2026-10-29. **Status:** this consolidation checkpoint passes the local checks below; T0 as a whole is not closed.

## Revision Identity

- Branch: existing `t0`; no branch/worktree was created.
- Baseline: `2af6e59b21d1c187ca4f2833fde04f6dd6f44cf8`. The first-pass tests were committed at `131c217676ce9f077493d093999dc645353faa7f`.
- Current `HEAD`: `131c217676ce9f077493d093999dc645353faa7f`; the second-pass test and T0-document changes are uncommitted. This is not qualification of a new committed SHA or a hosted CI result.
- The exact first-pass test-tree SHA-256, recomputed from the captured inventory and verified against all 147 files in commit `131c217`, is `199c99d03f786bcec6021600efc90cc26346be30dd863c79f9182b5273ee6836`.
- Current uncommitted test-tree SHA-256 is `edf584d5283a6f74633468eb143fa1c177bc647986d87158e93184ddba669be1`, computed from sorted `path + NUL + source_sha256 + LF` records for the measured test/support Python files, with UTF-8 decoded normalized line endings.
- The earlier recorded first-pass digest `0a827...` could not be reproduced from the source inventory and is superseded by the verified digest above. The current diff is limited to `root/tests/` and `docs/current/t0/`; production/game/service/client/runtime/tool code and browser/service test sources are unchanged. Application denominators are unchanged.

## Actual Local Results

| Check | Observed result |
| --- | --- |
| Root pytest, first-pass tree at `131c217` | **1,826 passed, 169.10 seconds** |
| Root pytest, first-pass tree at `131c217` | **1,826 passed, 169.10 seconds** |
| Root pytest, current uncommitted test tree | **1,825 passed, 161.52 seconds** |
| Web pytest, current uncommitted test tree | **60 passed, 9.54 seconds** |
| PostgreSQL 17 service tests, current uncommitted test tree | **31 passed, 13.29 seconds**, including real concurrency cases |
| Authored content | **PASS**: 5 enemies, 4 weapons, 4 Drifters, 10 encounters, 2 routes |
| Python source compilation | **PASS**, 318 source, test, tool, service, and migration files outside ignored pytest caches |
| Browser site build | **PASS**, 142 files |
| Playwright browser smoke, current built site | **PASS**, all existing route, Hub, Floor I, defeat/reselect, save/reload, and weapon save/reload markers |
| Migration from zero | **PASS**, `alembic upgrade head` on the dedicated T0 migration database |
| Alembic model parity | **PASS**, `No new upgrade operations detected.` |
| Real pinned MicroPython runtime matrix, current test tree | **PASS**, native/forced-overlay/default/608K and semantic parity |
| Pinned heap pressure | **608K STABLE_PASS 3/3**; **576K MEMORY_LIMIT_CONFIRMED 3/3** |
| `git diff --check` | **PASS** |

At the first-pass checkpoint, root/web/service totaled **1,917 executed pytest cases**, versus 1,900 before. The current root/web/service runs total **1,916 cases**. More collected cases partly reflect unpacking existing loop rows into individually reported parameters; this is not by itself evidence of greater behavioral coverage.

Root tests use an isolated OS-temp fixture directory to avoid parent-repository pytest configuration leaking into generated-project child tests. Service tests use only the newly created T0 PostgreSQL container/databases, not existing application databases. The dedicated container is stopped after qualification. There is one unchanged Starlette/httpx deprecation warning in service tests.

The browser smoke retains its full existing journeys, including semantic actions, exact targets, Hub outing/extraction, merchant/components, full Surface route, Floor I boss clear/replay extraction, defeat/reselection, ordinary save/reload and weapon progression save/reload. No journey or timeout was removed to obtain a pass. The first launch used the desktop process's remapped Playwright cache path and stopped before Chromium launched; an unchanged rerun pointed Playwright at the already-installed matching user cache and passed. This was an environment-path correction, not a test or application edit.

## Failed Attempts Kept In The Record

- First cumulative root run after consolidation: **1,825 passed, 245.72 seconds**. One additional explicit eight-ID world-snapshot assertion was retained during equivalence review; the subsequent first-pass root rerun passed 1,826. The later local consolidation tree has its own 1,825-case result in the table above.
- First cumulative browser attempt: **FAIL, 141.354 seconds**, at the 30-second `__DD_BROWSER_READY__` wait after reload, after Hub/Floor I/defeat journeys passed. An unchanged isolated rerun passed the entire smoke. Load contention is a hypothesis, not a demonstrated root cause. This intermittent observation remains a risk, not a claimed fix.
- Unfiltered compilation found a pre-existing ignored generated fixture containing intentionally invalid Python under `web_tests/.pytest_cache/`, and unreadable stale cache directories. Re-running source compilation with `-x '(^|[\\/])(\.pytest_cache|__pycache__)([\\/]|$)'` passed. No unrelated cache was deleted or authored source excluded.
- The first browser launch for this final local pass could not find Chromium under the remapped sandbox cache path. With `PLAYWRIGHT_BROWSERS_PATH` directed to the existing matching user cache, the unchanged full smoke passed. No browser package was downloaded.

Timing observations are not controlled performance benchmarks: several cumulative checks overlapped. No runtime-speed improvement is claimed from this pass.

## Pinned Interpreter Identity

Actual executable used:

`C:/Users/User/AppData/Local/DungeonDrifters/micropython/v1.29.0/source/ports/windows/build-standard/micropython.exe`

- Size: **488,960 bytes**.
- SHA-256: **6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA**.
- Runtime: MicroPython **1.29.0**, Windows.

The real matrix ended with `MYP20|RESULT|CLOSURE_COMPLETE`. This is the runtime harness's result, not a declaration that T0 meets its architectural/LOC closure criteria. Raw logs/JUnit/evidence remain in ignored `root/.pytest-tmp-t0/` output.

## Still Required For T0 Closure

All local qualification boundaries have now been rerun against the current test tree: root and web pytest, browser smoke, PostgreSQL/concurrency, migration-from-zero, Alembic drift, content validation/build, Python source compilation, and the actual pinned MicroPython matrix. The test/app ratio remains above target, and the complete manual file-by-file ownership review has not been claimed complete; the inventory is a structural baseline, with changed-file decisions and removed-test equivalences recorded separately. T0 therefore remains open for that final audit decision and an exact committed/hosted SHA. No commit or hosted run was created here.

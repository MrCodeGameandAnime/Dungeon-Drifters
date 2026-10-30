# T0 First-Pass Qualification

**Date:** 2026-10-29. **Status:** this consolidation checkpoint passes the local checks below; T0 as a whole is not closed.

## Revision Identity

- Branch: existing `t0`; no branch/worktree was created.
- Base/HEAD: `2af6e59b21d1c187ca4f2833fde04f6dd6f44cf8`.
- The changes are uncommitted. This is not qualification of a new committed SHA and not a hosted CI result.
- Working test-tree SHA-256: `0a82741853f9e33828806d930573a241f0ff7fc19711620dc990345ed435d6b4`. This is SHA-256 of sorted `path + NUL + source_sha256 + LF` records for all measured test/support Python files, where source is UTF-8 decoded with normalized line endings. New support files are included.
- `git diff --name-only` reports no changes in production source, profile-service source, web/client code, portability overlays, tools, browser tests or workflows. Application and non-test Python denominators are unchanged.

## Actual Local Results

| Check | Observed result |
| --- | --- |
| Root pytest, final test tree | **1,826 passed, 169.10 seconds** |
| Web pytest | **60 passed, 19.70 seconds** |
| Real PostgreSQL 17 service tests | **31 passed, 51.32 seconds**, including concurrency and migration tests |
| Authored content | **PASS**: 5 enemies, 4 weapons, 4 Drifters, 10 encounters, 2 routes |
| Source/test/tool/service/migration compilation | **PASS**, excluding ignored pytest-cache/generated fixture directories |
| Browser site build | **PASS**, 142 files |
| Real Chromium smoke, isolated rerun | **PASS, 54.537 seconds** |
| Migration from zero | **PASS**, `alembic upgrade head` on dedicated T0 migration database |
| Alembic model parity | **PASS**, `No new upgrade operations detected.` |
| Real pinned MicroPython runtime matrix | **PASS**, native/forced-overlay/default/608K modes and semantic parity |
| Pinned heap pressure | **608K STABLE_PASS 3/3**; **576K MEMORY_LIMIT_CONFIRMED 3/3** |
| `git diff --check` | **PASS** |

Root/web/service total: **1,917 executed pytest cases**, versus 1,900 before. More collected cases partly reflect unpacking existing loop rows into individually reported parameters; this is not by itself evidence of greater behavioral coverage.

Root tests use an isolated OS-temp fixture directory to avoid parent-repository pytest configuration leaking into generated-project child tests. Service tests use only the newly created T0 PostgreSQL container/databases, not existing application databases. The dedicated container is stopped after qualification. There is one unchanged Starlette/httpx deprecation warning in service tests.

The browser smoke retains its full existing journeys, including semantic actions, exact targets, Hub outing/extraction, merchant/components, full Surface route, Floor I boss clear/replay extraction, defeat/reselection, ordinary save/reload and weapon progression save/reload. No journey or timeout was removed to obtain a pass.

## Failed Attempts Kept In The Record

- First cumulative root run after consolidation: **1,825 passed, 245.72 seconds**. One additional explicit eight-ID world-snapshot assertion was retained during equivalence review; the final full root rerun collected/passed 1,826.
- First cumulative browser attempt: **FAIL, 141.354 seconds**, at the 30-second `__DD_BROWSER_READY__` wait after reload, after Hub/Floor I/defeat journeys passed. An unchanged isolated rerun passed the entire smoke. Load contention is a hypothesis, not a demonstrated root cause. This intermittent observation remains a risk, not a claimed fix.
- Unfiltered compilation found a pre-existing ignored generated fixture containing intentionally invalid Python under `web_tests/.pytest_cache/`, and unreadable stale cache directories. Re-running source compilation with `-x '(^|[\\/])(\.pytest_cache|__pycache__)([\\/]|$)'` passed. No unrelated cache was deleted or authored source excluded.

Timing observations are not controlled performance benchmarks: several cumulative checks overlapped. No runtime-speed improvement is claimed from this pass.

## Pinned Interpreter Identity

Actual executable used:

`C:/Users/User/AppData/Local/DungeonDrifters/micropython/v1.29.0/source/ports/windows/build-standard/micropython.exe`

- Size: **488,960 bytes**.
- SHA-256: **6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA**.
- Runtime: MicroPython **1.29.0**, Windows.

The real matrix ended with `MYP20|RESULT|CLOSURE_COMPLETE`. This is the runtime harness's result, not a declaration that T0 meets its architectural/LOC closure criteria. Raw logs/JUnit/evidence remain in ignored `root/.pytest-tmp-t0/` output.

## Still Required For T0 Closure

The ratio target is not met, giant test modules remain, and broader semantic consolidation has not been exhausted. No conclusion that 1.20 is impossible is justified by this first pass. Continue the audit/consolidation plan, preserve the equivalence ledger, and repeat qualification for subsequent test changes. A later commit/hosted run must be recorded against its actual new SHA; none was created or run here.

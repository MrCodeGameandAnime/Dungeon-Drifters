# MicroPython Probe Notes

**Status:** supplemental run log. The Hub-only probe passed its exact pinned MicroPython v1.29.0 Gate 6 matrix on 2026-10-17. The extended Floor One probe was separately requalified on 2026-10-22 at a measured 512K/480K pressure boundary. These values qualify this Windows probe contract only; they are not a hardware-wide MicroPython compatibility or product memory-budget claim.

## Earlier Sealed Baseline

There is already substantial historical probe evidence; this Hub run does not erase it:

- `docs/old/mpy/portability/micropython-closure.md` records the MPY20 closure dated 2026-09-18. Its pinned MicroPython v1.29.0 source was `0fd6c573ea815774668bbb16b8e197c8822368b2` on `win32`. That probe covered the twelve-node surface route through Goblin Lord defeat and Dungeon Entrance, not the later Hub tutorial/extraction loop.
- `docs/old/save/save-r1-plan.md` records a fresh run after the late SAVE-ARCH-R1 fixes on exact commit `3a127f7303fdddf5b8d218524e67dae548b2e0f8`. It identifies the pinned executable as 488,960 bytes with SHA-256 `6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA`; 448K passed 3/3 and 416K reached the expected `MemoryError` 3/3.

Those are valid qualifications for their recorded source trees and probe contract. They are not evidence that the later Hub-enabled game tree or the extended Hub probe passes the same heap points. The 448K value is a qualification boundary for that harness, not a product memory ceiling or a PS5 requirement.

## First Hub-Tree 448K Failure

The Gate 6 record in `docs/current/hub/hub-implementation.md` describes the first relevant qualification on the exact reviewed Hub tree, dated 2026-10-16:

- CPython, forced-overlay, and default-runtime probes passed.
- The pinned MicroPython 1.29.0 Windows qualification reached `surface_goblin_lord` and failed while building its `BattleView`.
- MicroPython raised `MemoryError` while allocating 136 bytes, despite reporting 13,840 bytes free.
- The Goblin Lord stage did not pass; this was a failure constructing the view, not evidence that the Goblin Lord battle completed.
- The 416K lower-pressure frontier was not run. Gate 6 remained open.

The free-heap figure is not proof that a contiguous 136-byte allocation should have succeeded. Fragmentation is one possible explanation, but this run alone does not establish the cause.

## Probe Findings

While investigating the memory pressure, the route battle factory was found to retain every completed `Battle` object in a list. That kept full battle graphs alive across the route. The probe was changed to retain lightweight battle-composition summaries and a completion count instead. This reduces avoidable probe retention; it does not by itself prove that retained battles were the sole cause of the original Goblin Lord failure.

Keep these observations separate because they came from different probe revisions or runtime artifacts:

| Run | Runtime / probe | Result |
|---|---|---|
| Hub-tree Gate 6 qualification, 448K | Pinned MicroPython 1.29.0 Windows build; exact reviewed Hub tree | Failed constructing `surface_goblin_lord` BattleView; 136-byte allocation failed with 13,840 bytes reported free. |
| Local 448K control before the Hub probe extension | Locally available stock MicroPython 1.29.0 Windows build | Reached `surface_elite_patrol`, then failed allocating 136 bytes. This was a diagnostic reproduction, not the pinned Gate 6 run. |
| Extended probe, 448K | Same locally available stock build; lazy-loaded Hub probe | Failed during `SESSION_IMPORT` on a 2,344-byte allocation, with 61,824 bytes reported free. It did not reach the route. The added probe footprint may contribute; that has not been isolated as the cause. |
| Extended probe, 512K | Same locally available stock build | Passed the complete surface route and Hub tutorial/extraction loop. |

The locally available executable was:

`C:\Users\User\Documents\Dev\Python\micropython\enum_980\root\build\stock\ports\windows\build-standard\micropython.exe`

It reported MicroPython 1.29.0 on `win32`. Its identity was not verified as the exact pinned executable used by the Gate 6 run, so its results must not be substituted for pinned qualification evidence.

## Full Loop Reached at 512K

The extended raw probe passed 27 semantic stages and all 12 surface-route nodes (8 encounters and 3 rests), then exercised:

1. Recruit Azhvielle for the fixed 65-gold cost, leaving 10 of the route's 75 gold.
2. Ready the two-Drifter party.
3. Enter the tutorial battle against exactly three Goblins and complete it through the existing battle logic.
4. Reach Extraction with 120 EXP and 9 gold pending, and verify those rewards are not banked before choosing to return.
5. Return explicitly to the Hub; verify the tutorial rewards are secured, 60 EXP is awarded to each Drifter, shared gold is 19, pending rewards are cleared, and both Drifters have full HP and Mana.

The lowest reported free heap during this 512K run was about 80,096 bytes. The CPython native and forced-overlay raw probes also completed the route and Hub loop. These are exploratory results from the current probe work, not three-run MicroPython stability qualification.

After moving route-evidence release before the Hub probe, the local stock executable was rerun on 2026-10-17 at 512K. It completed the full route and Hub loop with `ROUTE_FINAL_STATE` → `ROUTE_EVIDENCE_RELEASE` → `HUB_RECRUITMENT`, and reported a lowest free heap of 87,168 bytes. This diagnostic used the 486,912-byte local binary with SHA-256 `E90AFC976ED7CB2EE530BE7F5D8C769C1F3B562DF4DDB04A6C589177ED912EFE`, not the pinned executable; it does not close Gate 6.

## Interim Test Evidence and Limits

The following records intermediate runs before the pinned Gate 6 rerun below; their open-gate status is superseded by the final qualification section.

- Focused probe-contract, runtime-matrix, and Hub-extraction tests: 24 passed in the prior run.
- A full root test run reported 1,618 passed and 5 failures in nested content-tooling cases. Those failures came from running with a repository-local pytest temporary directory, which caused nested pytest processes to discover the repository `pytest.ini` and import the repository `app` package instead of each generated project's package. Treat that run as an environment/configuration issue to rerun cleanly, not as a clean full-suite result.
- The final spot rerun in the current shell could not start because the available Python runtime did not have pytest installed.
- `git diff --check` passed after the probe edits.
- At this interim point, the Hub-extended tree's 448K stability and 416K frontier were unqualified. The earlier R1 results remain historical evidence for the R1 tree, not this new game loop. The 2026-10-17 follow-up below supersedes this interim status.

## Final Gate 6 Verification (2026-10-17)

The executable at `%LOCALAPPDATA%\DungeonDrifters\micropython\v1.29.0\source\ports\windows\build-standard\micropython.exe` matched the recorded pinned artifact exactly: 488,960 bytes, SHA-256 `6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA`; it reported MicroPython v1.29.0 on `win32`.

The first instrumented 448K retry failed during `SESSION_IMPORT`, requesting a 660-byte allocation. Before error formatting or collection, `micropython.mem_info(1)` showed 9,264 free GC bytes and a maximum free run of 11 blocks (176 bytes). This established fragmentation at that failure point, rather than relying on the later post-collection free count. The completed standalone Battle, view, enemy list, and game were probe-only state no longer needed after their assertions. Releasing those references before session import and constructing the session's independent game at `SESSION_CONSTRUCTION` allowed the same marker sequence and full scenario to run at 448K.

The formal `runtime_qualification_matrix.py` run on the resulting tree reported:

- CPython native, CPython forced overlay, and pinned MicroPython default: `PASS`.
- Pinned MicroPython 448K and semantic parity: `PASS`.
- 448K repeated stability: `STABLE_PASS`, 3/3.
- 416K lower frontier: `MEMORY_LIMIT_CONFIRMED`, 3/3.
- Final marker: `MYP20|RESULT|CLOSURE_COMPLETE`.

A raw final-tree 448K run completed all 12 route nodes, Goblin Lord, Hub recruitment, the three-Goblin tutorial battle, extraction, and teardown. Its lowest reported free heap was 24,480 bytes. The 448K and 416K values qualify this Windows probe contract only; they are not gameplay-device limits.

Final local checks on this working tree: 1,648 Python tests passed; 47 web tests passed; content validation passed (5 enemies, 4 weapons, 4 Drifters, 9 encounters, 1 route); compileall passed for the 285 accessible Python files outside generated pytest-cache fixtures; the 134-runtime-file browser build and full Playwright Hub outing/defeat-reselect route passed; and `git diff --check` passed. The profile-service suite, clean migration, and Alembic drift checks remain as previously recorded in the 2026-10-16 qualification; a local repeat was unavailable because the Docker engine pipe was not reachable in this shell.

No Gate 6 MicroPython qualification step remained for the Hub-only probe represented by this section. The later Floor One extension has its own qualification record below. Future changes to shared gameplay/runtime behavior or the probe contract should rerun the pinned matrix and record a new observation rather than treating the measured heap as a product budget.

The Hub stages are in `root/tools/micropython_hub_probe.py`; the route harness and lazy Hub-probe loader are in `root/tools/micropython_probe.py`; the stage contract is in `root/tools/runtime_qualification_matrix.py`.

## Floor One Extension Qualification (2026-10-22)

This qualification covers the Floor One dangerous run added after the Hub-only Gate 6 result. It was run on branch `hub`, with the working tree based on `25a2936dbe0ea22b6b82570283dd32b74773e77a`; the implementation was not committed during qualification.

The exact pinned executable was re-identified before the run:

- MicroPython v1.29.0, `win32`
- Size: 488,960 bytes
- SHA-256: `6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA`

The completed `runtime_qualification_matrix.py` run reported:

- CPython native, CPython forced overlay, and pinned MicroPython default: `PASS`.
- Pinned MicroPython at 512K: `PASS`; semantic parity: `PASS`.
- 512K repeated full-loop stability: `STABLE_PASS`, 3/3.
- 480K lower pressure point: `MEMORY_LIMIT_CONFIRMED`, 3/3.
- Final marker: `MYP20|RESULT|CLOSURE_COMPLETE`.

The probe completed the existing Surface route and safe Hub tutorial/extraction, then verified the Floor One warning, all ten battles, both Rest transitions, Goblin Lord clear, secured rewards, equal XP award, full HP/Mana restoration, and run save replacement. It also started a post-clear replay at the 50% XP rate, exercised the midway Rest, and extracted there. Assertions include 670 XP per Drifter for the first clear, 115 shared gold after it, 140 EXP and 21 gold for the partial replay extraction, and 136 shared gold afterward. These are current authored placeholder encounter rewards, not a balance target.

The earlier 448K target did not survive the expanded probe: the pinned executable failed before completing the route at that heap. It was not relabeled as a pass. Three independent full-loop runs at 512K passed, and three at 480K reached the expected `MemoryError` classification. This is a harness pressure boundary only; it does not set a memory limit for web, PC, mobile, PS5, or future hardware, and does not justify changing gameplay architecture to chase 448K.

Final cumulative checks on this working tree:

- Root Python suite: 1,689 passed.
- Web test suite: 48 passed.
- Profile service against isolated PostgreSQL 17: 29 passed.
- Migration database upgraded from zero; `alembic check`: no new upgrade operations.
- Content validation: 5 enemies, 4 weapons, 4 Drifters, 10 encounters, 2 routes.
- Static browser build: 138 runtime files; built-site Playwright smoke passed through the Floor One clear, replay extraction, and existing selection/defeat flows.
- Python compilation and `git diff --check`: passed (generated pytest cache fixtures excluded from compilation).

The temporary PostgreSQL qualification container and its databases were stopped and removed after the run. No production service, existing container, or migration was changed.

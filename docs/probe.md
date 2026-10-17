# MicroPython Probe Notes

**Status:** exploratory run log. This is not a replacement for the Gate 6 qualification record or a claim that MicroPython is sealed.

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

## Test Evidence and Limits

- Focused probe-contract, runtime-matrix, and Hub-extraction tests: 24 passed in the prior run.
- A full root test run reported 1,618 passed and 5 failures in nested content-tooling cases. Those failures came from running with a repository-local pytest temporary directory, which caused nested pytest processes to discover the repository `pytest.ini` and import the repository `app` package instead of each generated project's package. Treat that run as an environment/configuration issue to rerun cleanly, not as a clean full-suite result.
- The final spot rerun in the current shell could not start because the available Python runtime did not have pytest installed.
- `git diff --check` passed after the probe edits.
- For the Hub-extended tree, 448K three-run stability and the 416K frontier remain unqualified. The earlier R1 results above remain historical evidence for the R1 tree, not this new game loop. If actual gameplay needs more memory, investigate and revise the target based on measured runtime needs rather than treating the probe limit as a design constraint.

## Next Qualification Steps

1. Re-run the unchanged full-route-plus-Hub probe with the exact pinned MicroPython executable and record its path/version.
2. Investigate the difference between the first Goblin Lord `BattleView` failure and the later local reproduction; keep probe overhead and runtime artifact identity in view.
3. Once the executable and probe are stable, run the required 448K repeated qualification and the 416K lower frontier. Record exact outputs and minimum free-heap observations.
4. Rerun the complete Python and web suites using a pytest temporary directory that does not alter nested project test discovery.

The Hub stages are in `root/tools/micropython_hub_probe.py`; the route harness and lazy Hub-probe loader are in `root/tools/micropython_probe.py`; the stage contract is in `root/tools/runtime_qualification_matrix.py`.

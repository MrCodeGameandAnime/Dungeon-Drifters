# M8.8: Floor V Reunion Boss And Full-Party Settlement

**Status:** Proposed work package. Regional architecture, the M8-D1 reunion boss identity/ID/composition/reward sources, and M8-D5 are approved. Numerical tuning and implementation details remain package-level review; no implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate M4B and expedition settlement owners at package entry.

## Goal

Deliver the separate four-permanent-Drifter reunion battle, its exactly-once Floor-V clear and reward settlement, and return to ordinary two-plus-two play.

## Approval Boundary

**Already-approved inputs:** M8-D5 requires a separate Hub-launched four-permanent-Drifter Floor V boss; no active expedition assignment during the boss; no automatic cancellation/refund; completed and settled but unclaimed reports do not block entry; preserve M6's coexistence and settlement rules; use M4B's shared boss XP divided four ways then each Drifter's individual Intuition adjustment; preserve earlier pair-earned XP attribution.

**Also approved:** a genuine Floor V boss victory records Floor V completion and unlocks Region 2 through the Hub Region Portal; Region 2 has no playable M8 routes and cannot be entered until playable content exists. `Ashen Regent`, `m8_ashen_regent_boss`, and its approved encounter composition are fixed by D1.

**Already approved:** boss identity/ID/composition, reward/source relationships, and M8-D5's assignment, entry, settlement, and XP rules. **Package review remains:** permitted numeric combat/reward tuning and technical entry/settlement plan details.

M8-D6 approves `m8_portrait_ashen_regent` as a static boss portrait associated with the approved `ashen_regent` identity. M8.9 owns live integration.

## Scope

- Launch the approved Floor V reunion boss from Hub only after M8.7's durable `m8_ashen_arena_revealed` evidence; use the approved `m8_ashen_regent_boss` ID.
- Require all four permanent Drifters, with no active expedition assignment. A completed, settled but unclaimed report does not block entry. Do not pull assigned members into combat or refund/cancel an assignment.
- Reuse M4B's four-member battle, defeat and XP contract: shared boss XP split four ways, then each Drifter's own Intuition bonus. Preserve prior pair XP attribution.
- On genuine victory, atomically durably record Floor V clear and Region 2 unlock as distinct facts, grant the approved first-clear rewards/source mappings, record `m8_ashen_regent_defeated`, and return the reunited roster to Hub/two-plus-two deployment.
- Through the normal Hub Region Portal, show Region 2 as unlocked but unavailable with a clear explanation because no route is authored. Preserve access to Region 1 and its eligible completed content. Do not fabricate a Floor VI or grant a Region 2 floor clear/reward.

## Exclusions And Handoff

No mid-run party swap, active assignment during the boss, all-four ordinary Floor-V route, additional recruit, new boss phase, or playable Region 2 route. Region 2's final name, visual identity, routes, enemies, and release scope remain future content decisions.

## Ownership

Revalidate M4B participant/reward settlement in `root/src/app/game/overworld_session.py` and `party_state.py`, M8.1 clear/entry evidence, M8.5 assignment/report state, and current save validation. No parallel XP or settlement algorithm.

**Persistence impact:** M8.1 owns canonical floor-clear and region-unlock state/migration. M8.8 must atomically set Floor V clear and Region 2 unlocked through that owner after the genuine boss victory; it must not conflate those facts or add competing markers. Failed persistence must leave neither fact nor associated reward partially committed.

M8.8 owns the live Floor V Material report test. Verify ineligibility before the reunion clear, win through normal play, then use M8.5 to launch the eligible assignment, settle and claim its approved Grade-IV Core result once. Verify provenance and no duplicate after reload or retry.

## Tests, Package Gates, And Qualification History

Cover all-four required, any active pair restored afterward, assignment rejection/settlement boundary, unclaimed settled report allowed, victory/defeat, XP split and personal Intuition rounding, pre-boss pair history unchanged, one-time Floor-V clear/rewards, and Region 2 unlock exactly once. Inject failed writes to prove clear, unlock and rewards remain atomic. After reload, exercise the normal Hub portal: Region 2 is visible/unlocked but unavailable, Region 1 is revisit-able, and revisiting cannot erase Floor V or repeat one-time rewards. Verify terminal/browser parity and no duplicate combatants.

- **Gate A, plan approval:** Open; review the atomic entry/settlement implementation plan, numerical tuning within the approved profile, and upstream M8.1/M8.5/M8.7 integration contracts. D1 boss/reward entries and D5 are approved and must not be reopened.
- **Gate B, implementation and focused tests:** Not started; entry, combat, XP, settlement and retry red/green tests.
- **Gate C, exact-SHA qualification and closure:** Not run; root/web, content/build, PostgreSQL/migration/Alembic, browser smoke and pinned MicroPython.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Not implemented | Not run | Not run | Pending | Open |

Close with independent review and linked hosted evidence.


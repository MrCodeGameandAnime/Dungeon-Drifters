# M8.8: Ashen Regent And Full-Party Reunion

**Status:** Proposed work package. M8-D1 and M8-D5 are pending; no implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate M4B and expedition settlement owners at package entry.

## Goal

Deliver the separate four-permanent-Drifter reunion battle, its exactly-once Floor-V clear and reward settlement, and return to ordinary two-plus-two play.

## Approval Boundary

**Already-approved inputs:** preserve M4B's existing four-member battle, shared XP split among participants followed by personal Intuition, and prior pair-earned XP attribution; preserve M6's assignment energy/settlement contract.

**Still pending:** M8-D1 final boss/reward scope and M8-D5 assignment availability, entry sequence, and confirmation that the M4B XP contract is used here.

## Scope

- Launch `m8_ashen_regent_boss` from Hub only after M8.7's durable `m8_ashen_arena_revealed` evidence.
- Require all four permanent Drifters, with no active expedition assignment. A completed, settled but unclaimed report does not block entry. Do not pull assigned members into combat or refund/cancel an assignment.
- Reuse M4B's four-member battle, defeat and XP contract: shared boss XP split four ways, then each Drifter's own Intuition bonus. Preserve prior pair XP attribution.
- On genuine victory, durably record Floor V clear once, grant only approved first-clear rewards and the named Grade-IV Core source, record `m8_ashen_regent_defeated` and the finite future-region rumor, then return the reunited roster to Hub/two-plus-two deployment.

## Exclusions And Handoff

No mid-run party swap, active assignment during the boss, all-four ordinary Floor-V route, additional recruit, new boss phase, or actual next-region route. Whether post-boss content merely foreshadows or unlocks another region remains under M8-D1; the current manifest proposes a rumor only.

## Ownership

Revalidate M4B participant/reward settlement in `root/src/app/game/overworld_session.py` and `party_state.py`, M8.1 clear/entry evidence, M8.5 assignment/report state, and current save validation. No parallel XP or settlement algorithm.

**Persistence impact:** M8.1 owns Floor-V clear migration/state. This package must use that boundary for boss settlement and add no competing clear marker.

## Tests, Package Gates, And Qualification History

Cover all-four required, any active pair restored afterward, assignment rejection/settlement boundary, unclaimed settled report allowed, victory/defeat, XP split and personal Intuition rounding, pre-boss pair history unchanged, one-time Floor-V clear/rewards, failed writes/retry/reload, no duplicate combatants, and terminal/browser journeys.

- **Gate A, plan approval:** Open; resolve M8-D1/D5 and upstream M8.1/M8.5/M8.7 state contracts.
- **Gate B, implementation and focused tests:** Not started; entry, combat, XP, settlement and retry red/green tests.
- **Gate C, exact-SHA qualification and closure:** Not run; root/web, content/build, PostgreSQL/migration/Alembic, browser smoke and pinned MicroPython.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Not implemented | Not run | Not run | Pending | Open |

Close with independent review and linked hosted evidence.


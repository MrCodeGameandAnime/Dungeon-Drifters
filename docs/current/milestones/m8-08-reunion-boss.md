# M8.8: Floor V Reunion Boss And Full-Party Settlement

**Status:** Implementation delivered; exact-SHA cumulative qualification is in progress. M8.8 remains open for owner review and is not sealed.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Sealed prerequisite:** M8.7 is CLOSED AND SEALED at `0fcd64347e7b2af5673e5ba9785b5bba5676edf8`, qualified by exact-SHA hosted CI [45832492446](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/45832492446).

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

## Authored Boss Profile

`ashen_regent` is a Tier-3 boss with 520 HP, 160 Mana, and base awards of 720 XP and 45 gold. Its Tier-3 attributes are Constitution 23, Spirit 19, Intelligence 20, Strength 19, Dexterity 14, and Intuition 17. The encounter `m8_ashen_regent_boss` pairs it with `brine_oracle`.

The authored single-target moves are:

| Move | Damage class | Power/scaling | Accuracy | Cost |
| --- | --- | --- | ---: | ---: |
| Cindersteel Sweep | Physical | 18, Strength | 88% | None |
| Ashfall Verdict | Magical | 21, Intelligence/Spirit | 84% | 14 Mana |
| Regent's Last Decree | Magical | 27, Intelligence | 76% | 22 Mana |

The Regent's Tier-3 profile can drop one Grade-IV Core at 10,000 bps from source `m8_ashen_regent_grade_iv_core_01`. The one-time Floor V first-clear reward `m8_floor_five_first_clear_reward` grants exactly one Grade-IV Magic Crystal.

## Pinned Runtime Profile

M8.8's pinned MicroPython v1.29.0 candidate was intermittent at 1408 KiB: 2/3 runs passed, while one failed allocating 584 bytes during `M4_FLOOR_THREE_PROBE`. At 1472 KiB, 3/3 runs passed; 1216 KiB produced the expected `MemoryError` at `SESSION_CONSTRUCTION` in 3/3 runs. The proposed M8.8 qualification profile is 1472 KiB stable / 1216 KiB expected memory limit. Per-run free/allocated heap measurements and the pinned executable identity are recorded in [probe notes](../../probe.md). Earlier M8.2/M8.7 1408/1216 results remain unchanged as historical evidence.

## Tests, Package Gates, And Qualification History

Cover all-four required, any active pair restored afterward, assignment rejection/settlement boundary, unclaimed settled report allowed, victory/defeat, XP split and personal Intuition rounding, pre-boss pair history unchanged, one-time Floor-V clear/rewards, and Region 2 unlock exactly once. Inject failed writes to prove clear, unlock and rewards remain atomic. After reload, exercise the normal Hub portal: Region 2 is visible/unlocked but unavailable, Region 1 is revisit-able, and revisiting cannot erase Floor V or repeat one-time rewards. Verify terminal/browser parity and no duplicate combatants.

- **Gate A:** Implementation authorization received; the approved D1/D3/D5 contracts remain unchanged.
- **Gate B:** Implemented. Focused reunion/route/persistence regressions pass, including all six pair selections, four-member restoration, transactional retries, portal state, and the live Floor V Material report.
- **Gate C:** Exact-SHA cumulative qualification is in progress. The package remains open until evidence is reported and owner review is complete.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Implementation commit pending | Local: 2,716 root tests, 96 web tests, and 38 profile-service tests passed (19 PostgreSQL-only skips); full browser smoke, authored-content validation, compile, and 212-file browser build passed. Hosted exact-SHA run pending. | Schema 31 adds the distinct reunion run ID; schema-30 immutable-history migration covered. Pinned native/overlay/runtime and semantic parity passed; proposed M8.8 profile 1472 KiB stable 3/3 / 1216 KiB expected limit 3/3. | Pending owner review | Open |

Close with independent review and linked hosted evidence.


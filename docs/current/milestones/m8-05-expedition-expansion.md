# M8.5: Expedition Expansion

**Status:** Implementation in progress under the approved M8 manifest. Focused service, persistence, UI and browser coverage is being completed; M8.5 remains open pending cumulative and exact-SHA hosted qualification.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**M8.4 baseline:** M8.4 is CLOSED AND SEALED at `0a73019f9acdfcdbad4c3f2d910c212e38ddc154`, qualified by [exact-SHA hosted CI 45625705219](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/45625705219). M8.5 increments disk schema 28 to 29.

## Goal

Extend M6's passive, timer-based, exactly-once report contract to the approved completed M8 floors and eligible reward categories, without adding simulated expedition gameplay.

## Approval Boundary

**Already-approved inputs:** retain M6's 100-energy cap, 10-energy launch cost, 20-minute real-time assignment, offline/rollback behavior, completed-floor eligibility, deterministic frozen outcomes, and exactly-once claim semantics. Under M8-D3, Scouting is eligible only for a corresponding floor already completed. Under M8-D5, preserve M6/M4 coexistence and settlement restrictions; an active assignment cannot coexist with the four-member Floor V boss, a completed/settled but unclaimed report does not block it, and no assignment is canceled or refunded automatically.

**Approved and implemented:** all seven report IDs, destination/category eligibility, source prerequisites and deterministic outcomes in the parent; the Floor-IV Scouting report confirms all three approved facts. Training retains the existing collective 20% secured-XP pool and permanent-roster-order remainder rule. No owner-level D1/D3 product mapping remains open.

## Scope

- Extend completed-floor eligibility to Floor IV and later Floor V only after its approved completion event. Preserve 100 energy, launch cost, 20-minute elapsed timer, offline/rollback protection and no-energy dungeon gameplay.
- Add the seven approved report IDs: Floor-IV Material, Equipment, Recovery, Scouting, Story and Elite; Floor-V Material. Categories without an eligible authored source stay unavailable with an explanation.
- Freeze report outcomes at launch. Equipment reports carry/reference the complete unique `EquipmentInstance`; stack rewards use legitimate floor source IDs; Scouting/Story effects are applied once at Hub claim.
- Use only the floor-eligible material and source matrix approved at Gate 0; no expedition-exclusive item or invented content.
- Preserve pair assignment rules and the Floor-III launch restriction. Do not deploy an expedition-assigned permanent Drifter in ordinary combat; retain only M4's already-authorized temporary Floor-II helper proxy exception. Do not allow an active assignment during the four-member Floor V boss; settled, completed but unclaimed reports remain nonblocking.
- Compatible outing launch is supported for Floors I, II and IV. Floor III remains blocked. The `floor_five_approach` contract is accepted but remains dormant until M8.7 authors that route and its authoritative run starter; the four-member `floor_five_reunion` is never expedition-compatible. A Floor-V Material report remains unavailable until a genuine Floor-V clear and an eligible Grade-IV Core source are both present.

## Exclusions And Handoff

No new energy economics, expedition combat, M6-D6 general full-party event redesign, Floor-V reunion deployment, or story scene authoring. M8.1 provides clear/fact owners; M8.3/8.8 provide completion and reward sources; M8.4 provides armor/recovery sources; M8.6 consumes the Story result. M8.7/M8.8 must obey the assignment restrictions approved under D5.

## Ownership And Persistence

`ExpeditionService`, `ExpeditionState`, `PartyState`, the session/presenter flow and `save_document.py` remain the authorities. Schema 29 stores each assignment/report's stable content ID and frozen outcome. Stack results retain authored source ID, item ID and quantity; Scouting and Story effects apply to a candidate state and publish only after a successful save. Equipment reports freeze the complete secured `EquipmentInstance`; IDs are checked against owned gear and other expedition evidence, and an unclaimed report cannot duplicate party inventory. Claiming adds the exact frozen instance and marks the report claimed in one save transaction.

Schema-28 history remains immutable and is validated using the fixed M8.4 introduction boundary. The schema-29 migration adds only the M8.5 fields/defaults to legitimate legacy M6 assignments and reports; it rejects post-M8.5 report evidence in schema 28. Qualification explicitly includes a real schema-28 save with M8.4 discovery, armor and recovery evidence. M8.1 remains the sole owner of floor-clear and knowledge evidence.

The Floor-V Material contract is guarded by both the authoritative Floor-V completion flag and a scan of authored Grade-IV Core drops on the approved approach/reunion routes. No Floor-V route/source currently exists, so the category stays unavailable. The live clear-to-report journey remains deferred to M8.8.

## Tests, Package Gates, And Qualification History

Cover all seven report categories and source gates, frozen results, timer completion/incompletion, outing termination, launch and claim save failures, stale/duplicate launch, one-time claim, reload/retry, unique equipment identity, floor-grade provenance, all three Floor-IV Scouting facts, Story effect adoption, deployment restrictions, and no energy effect on ordinary play. Verify the Scouting report confirms all three facts exactly once and that all remain Confirmed after save/reload. Terminal/browser journeys use the real Python runtime and preserve exact report/item/equipment identities.

- **Gate A:** Not a separate approval checkpoint; the owner authorized implementation against the approved parent manifest.
- **Gate B:** In progress; report, migration, failure-atomicity, browser and terminal tests are implemented and focused suites are green.
- **Gate C:** Pending cumulative root/web, content/build, browser journeys, PostgreSQL/migration/Alembic, pinned MicroPython, and exact-SHA hosted qualification.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| In progress | Pending | Schema 29; schema-28 M8.4 evidence migration tested locally | Pending | Open |

Record the final implementation SHA, exact-SHA CI URL/results, runtime evidence and owner closure here after qualification.


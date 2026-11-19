# M8.5: Expedition Expansion

**Status:** Proposed work package. M8-D1, M8-D3, and M8-D5 remain pending; no implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate current M6/M8 state owners at package entry.

## Goal

Extend M6's passive, timer-based, exactly-once report contract to completed M8 floors and eligible reward categories if approved, without adding simulated expedition gameplay.

## Approval Boundary

**Already-approved inputs:** retain M6's 100-energy cap, 10-energy launch cost, 20-minute real-time assignment, offline/rollback behavior, completed-floor eligibility, deterministic frozen outcomes, and exactly-once claim semantics.

**Still pending:** M8-D1 category/destination manifest, M8-D3 knowledge effects, and M8-D5 assignment coexistence with approach outings and reunion settlement. No report type is approved solely because it appears in the proposal.

## Scope

- Extend completed-floor eligibility to Floor IV and later Floor V only after its approved completion event. Preserve 100 energy, launch cost, 20-minute elapsed timer, offline/rollback protection and no-energy dungeon gameplay.
- Add the parent report IDs: Floor-IV Material, Equipment, Recovery, Scouting, Story and Elite; Floor-V Material. Categories without an eligible authored source stay unavailable with an explanation.
- Freeze report outcomes at launch. Equipment reports carry/reference the complete unique `EquipmentInstance`; stack rewards use legitimate floor source IDs; Scouting/Story effects are applied once at Hub claim.
- Use only the floor-eligible material and source matrix approved at Gate 0; no expedition-exclusive item or invented content.
- Preserve pair assignment rules, Floor-III launch restriction, M4 temporary Floor-II helper exception only, and no assignment participant in a general battle.

## Exclusions And Handoff

No new energy economics, expedition combat, M6-D6 general full-party event redesign, Floor-V reunion deployment, or story scene authoring. M8.1 provides clear/fact owners; M8.3/8.8 provide completion and reward sources; M8.4 provides armor/recovery sources; M8.6 consumes the Story result. M8.7/M8.8 must obey the assignment restrictions approved under D5.

## Ownership And Persistence

Current owners to revalidate: `root/src/app/game/expeditions.py`, `expedition_state.py`, `party_state.py`, report claim/session/presenter flow, and `root/src/app/persistence/save_document.py`. Current reports support XP and stackable items; new frozen outcome types require validated ownership and a migration from the actual schema. Do not store duplicated client-side results or reroll on reload.

M8.5 owns any report-state schema migration and legacy defaulting for report payloads. M8.1 remains the sole owner of floor-clear and knowledge evidence.

M8.5 qualifies the Floor V Material report with controlled clear and source evidence. Record the live reunion-to-report journey as deferred to M8.8.

## Tests, Package Gates, And Qualification History

Cover each category's availability by destination/source, frozen result, timer completion and incompletion, outing termination, launch/save failure, stale/duplicate launch, one-time claim, reload/retry, unique equipment identity, floor-grade provenance, scouting/story fact adoption, and no energy effect on ordinary play.

- **Gate A, plan approval:** Open; resolve M8-D1/D3/D5 and the report payload contract.
- **Gate B, implementation and focused tests:** Not started; timer/report/claim/migration red/green tests.
- **Gate C, exact-SHA qualification and closure:** Not run; root/web, content/build, browser journeys, PostgreSQL/migration/Alembic and pinned MicroPython.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Not implemented | Not run | Not run | Pending | Open |

Record independent review, exact SHA, CI URL and closure evidence.


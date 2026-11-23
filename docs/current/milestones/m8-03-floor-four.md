# M8.3: Drowned Reliquary, Floor IV

**Status:** Proposed work package. The Floor-IV manifest, regional architecture, and M8-D6 static assets/associations are approved. Numerical enemy profiles, drop probabilities/quantities, and implementation details remain package-level review. No implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate current route/content owners at package entry.

## Goal

Deliver the first playable M8 route using the approved two-Drifter ordinary and paired-boss loop, existing combat resolver, M7 Momentum, and authoritative Floor-IV clear evidence.

## Approval Boundary

**Already-approved inputs:** preserve M1's two-person ordinary outings and legal pair selection, M4's recruitment/XP ownership rules, M7's shared Momentum contract, and M6's completed-floor eligibility.

**Already approved:** Floor-IV IDs, compositions, reward/source relationships, and D6 portrait associations. **Package review remains:** numerical enemy profiles/move values and tunable drop probabilities or quantities. Fixed discovery/source relationships and the defined first-clear Grade-IV Crystal reward must not be rebalanced or changed.

## Scope

- Add the parent manifest's approved 12-node `floor_four` route: nine ordinary battles, midpoint Rest, pre-boss Rest, and paired Floor-IV boss. `Tidebound Curator` is the approved boss identity.
- Author this destination as a member of Region 1 through M8.1's explicit membership contract; do not infer region from `floor_four` numbering.
- Use the approved encounter IDs `m8_floor_four_encounter_01` through `_09` and `m8_tidebound_curator_boss` with their accepted D1 compositions.
- Author the approved ordinary-enemy and Curator identities/compositions. Reuse supported combat mechanics; no new phases, formations, hazards, or renderer are authorized. M8.9 owns integration of the D6-approved static assets with their now-approved D1 associations; asset production/delivery remains a separate responsibility.
- Author the four named Grade-IV material source IDs in the parent manifest and the Floor-IV first-clear Grade-IV Crystal reward. Actual probabilities, quantities and recipe values require the approved balance pass; source provenance must remain floor-eligible.
- Record Floor-IV clear only through M8.1's canonical clear boundary; preserve pair XP splitting and ordinary two-member deployment.

## Exclusions And Handoff

No permanent discoveries, live armor/recovery rewards, expedition category/report work, Floor-V route, extra recruitment, or four-member boss. M8.4 owns discovery, armor and recovery reward integration. Until M8.4, Rest nodes must not imply those sources are available. M8.5 owns expedition access to the completed destination.

**Persistence impact:** Floor-IV clear storage and migration belong to M8.1. This package authors the genuine victory that sets that evidence; it must not add a second completion record.

## Ownership

Route and encounter catalog owners are `root/src/app/content/route_spec.py`, `root/src/app/content/routes/`, `enemy_spec.py`, `catalog.py`, and generated catalog tooling. Session, route cursor, reward, and clear ownership remain in `root/src/app/game/overworld_session.py`, `overworld_state.py`, `party_state.py`, and existing run-event owners. Revalidate exact call sites before implementation; do not add new APIs to this plan by assumption.

## Tests, Package Gates, And Qualification History

Test route reachability/node order, every encounter definition, tier-3 validation, Floor-IV unlock from M8.1, two-member deployment, pair XP and Intuition, M7 symmetry, material grade provenance, first-clear idempotency, Rest checkpoint reload, boss settlement retry, failed writes and unchanged I-III behavior.

- **Gate A, plan approval:** Open; approve the Floor-IV implementation/test plan and permitted numerical tuning. D1 identities, compositions, source mappings, and D6 associations are settled and must not be reopened.
- **Gate B, implementation and focused tests:** Not started; route, enemy, reward and progression red/green coverage.
- **Gate C, exact-SHA qualification and closure:** Not run; root/web, content, compile/build, terminal/browser journeys, PostgreSQL/migrations and pinned MicroPython.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Not implemented | Not run | Not run | Pending | Open |

Close only with independent review and green hosted evidence recorded here and in the parent.


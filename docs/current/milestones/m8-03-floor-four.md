# M8.3: Drowned Reliquary, Floor IV

**Status:** Proposed work package. M8-D1's detailed Floor-IV manifest remains open; the floor/route/count direction, regional architecture, and M8-D6's limited static-asset scope are approved. No implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate current route/content owners at package entry.

## Goal

Deliver the first playable M8 route using the approved two-Drifter ordinary and paired-boss loop, existing combat resolver, M7 Momentum, and authoritative Floor-IV clear evidence.

## Approval Boundary

**Already-approved inputs:** preserve M1's two-person ordinary outings and legal pair selection, M4's recruitment/XP ownership rules, M7's shared Momentum contract, and M6's completed-floor eligibility.

**Still pending:** detailed M8-D1 IDs/compositions and reward/source mapping. Enemy profiles, drop rates, and first-clear values remain proposals until their package review. The four ordinary-enemy and Floor-IV boss portrait IDs are approved by D6, but their content associations remain contingent on D1 finalizing the enemy and boss identities.

## Scope

- Add the parent manifest's proposed 12-node `floor_four` route: nine ordinary battles, midpoint Rest, pre-boss Rest, and paired Floor-IV boss. `Tidebound Curator` is the current proposed boss identity, not an approved identity.
- Author this destination as a member of Region 1 through M8.1's explicit membership contract; do not infer region from `floor_four` numbering.
- Use the proposed encounter IDs `m8_floor_four_encounter_01` through `_09` and `m8_tidebound_curator_boss` only if accepted with the detailed D1 manifest and compositions.
- Add the proposed ordinary-enemy and Curator definitions only after detailed D1 content approval. Reuse supported combat mechanics; no new phases, formations, hazards, or renderer are authorized. M8.9 owns integration of the D6-approved static assets after D1 confirms their content associations; asset production/delivery remains a separate responsibility.
- Author the four named Grade-IV material source IDs in the parent manifest and the Floor-IV first-clear Grade-IV Crystal reward. Actual probabilities, quantities and recipe values require the approved balance pass; source provenance must remain floor-eligible.
- Record Floor-IV clear only through M8.1's canonical clear boundary; preserve pair XP splitting and ordinary two-member deployment.

## Exclusions And Handoff

No permanent discoveries, live armor/recovery rewards, expedition category/report work, Floor-V route, extra recruitment, or four-member boss. M8.4 owns discovery, armor and recovery reward integration. Until M8.4, Rest nodes must not imply those sources are available. M8.5 owns expedition access to the completed destination.

**Persistence impact:** Floor-IV clear storage and migration belong to M8.1. This package authors the genuine victory that sets that evidence; it must not add a second completion record.

## Ownership

Route and encounter catalog owners are `root/src/app/content/route_spec.py`, `root/src/app/content/routes/`, `enemy_spec.py`, `catalog.py`, and generated catalog tooling. Session, route cursor, reward, and clear ownership remain in `root/src/app/game/overworld_session.py`, `overworld_state.py`, `party_state.py`, and existing run-event owners. Revalidate exact call sites before implementation; do not add new APIs to this plan by assumption.

## Tests, Package Gates, And Qualification History

Test route reachability/node order, every encounter definition, tier-3 validation, Floor-IV unlock from M8.1, two-member deployment, pair XP and Intuition, M7 symmetry, material grade provenance, first-clear idempotency, Rest checkpoint reload, boss settlement retry, failed writes and unchanged I-III behavior.

- **Gate A, plan approval:** Open; resolve the detailed M8-D1 content and content/balance review. D6 scope is approved; confirm the relevant asset associations against the accepted D1 identities.
- **Gate B, implementation and focused tests:** Not started; route, enemy, reward and progression red/green coverage.
- **Gate C, exact-SHA qualification and closure:** Not run; root/web, content, compile/build, terminal/browser journeys, PostgreSQL/migrations and pinned MicroPython.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Not implemented | Not run | Not run | Pending | Open |

Close only with independent review and green hosted evidence recorded here and in the parent.


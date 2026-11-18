# M8.7: Ashen Vault, Floor V Approach

**Status:** Proposed work package. M8-D1, M8-D3, and M8-D5 are pending; no implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate route and expedition owners at package entry.

## Goal

Deliver the paired seven-node approach that reveals the reunion arena through a real victory and returns to the Hub without inserting or swapping party members.

## Approval Boundary

**Already-approved inputs:** preserve the two-plus-two roster loop, M1 pair selection, M2 outing settlement, M6 passive expedition behavior, and M7 Momentum.

**Still pending:** M8-D1 Floor-V content, M8-D3 discovery/knowledge rules, and M8-D5 expedition coexistence. The route and arena reveal remain proposals until those decisions are resolved.

## Scope

- Add the six parent-manifest Floor-V ordinary encounters and `floor_five_approach`: six battles plus `floor_five_rest_midpoint`.
- Keep ordinary encounters two-Drifter and allow any legal active pair.
- Place `spirit_relic_floor5_01` at the midpoint Rest using the reward/search contract delivered by M8.4; do not duplicate its effect or claim logic.
- Record `m8_ashen_arena_revealed` only after the route's genuine final victory is durably committed. Failed/abandoned battle or failed save cannot reveal it.
- Preserve M7 Momentum, Grade-IV provenance, normal extraction/death settlement, and the two-plus-two roster loop.

## Exclusions And Handoff

No reunion boss, Floor-V clear, first-clear boss reward, new discovery service, or item key. M8.1 owns the arena eligibility evidence; M8.4 owns the Spirit Relic reward; M8.5 must establish the approved assignment coexistence behavior before this package qualifies those journeys. M8.8 consumes the arena reveal.

## Ownership And Persistence

Use existing route/content/session/run-event/save owners, revalidated at package entry. The route is a paired outing and uses normal durable outcome/return semantics. Do not add a parallel campaign engine or client-side arena unlock.

**Persistence impact:** M8.1 owns durable arena-reveal state. This package records it through that owner after genuine victory; no separate route-completion schema is proposed.

## Tests, Package Gates, And Qualification History

Test all six encounters and route order, all legal pairs, midway Rest/search/save/reload, source idempotency, assignment coexistence as approved by D5, final victory vs defeat/extraction/save failure, no premature arena option, reload/retry, and terminal/browser parity.

- **Gate A, plan approval:** Open; resolve M8-D1/D3/D5 and upstream M8.4/M8.5 contracts.
- **Gate B, implementation and focused tests:** Not started; route, reveal, discovery-placement and settlement red/green tests.
- **Gate C, exact-SHA qualification and closure:** Not run; root/web, content, compile/build, real browser smoke, PostgreSQL/migration/Alembic and pinned MicroPython.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Not implemented | Not run | Not run | Pending | Open |

Require independent review and record CI/closure evidence.


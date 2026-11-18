# M8.3: Drowned Reliquary, Floor IV

**Status:** Proposed work package. M8-D1 and M8-D6 are pending; no implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate current route/content owners at package entry.

## Goal

Deliver the first playable M8 route using the approved two-Drifter ordinary and paired-boss loop, existing combat resolver, M7 Momentum, and authoritative Floor-IV clear evidence.

## Scope

- Add the parent manifest's 12-node `floor_four` route: nine ordinary battles, midpoint Rest, pre-boss Rest, and paired Tidebound Curator boss.
- Add encounter IDs `m8_floor_four_encounter_01` through `_09` and `m8_tidebound_curator_boss` with the parent compositions.
- Add `reliquary_sentinel`, `brine_oracle`, `drowned_stalker`, `ashbound_hound`, and the Curator content definitions; author tier-3 profiles only after D1/D6 approval. Reuse supported combat mechanics; no phases or renderer.
- Author the four named Grade-IV material source IDs in the parent manifest and the Floor-IV first-clear Grade-IV Crystal reward. Actual probabilities, quantities and recipe values require the approved balance pass; source provenance must remain floor-eligible.
- Record Floor-IV clear only through M8.1's canonical clear boundary; preserve pair XP splitting and ordinary two-member deployment.

## Exclusions And Handoff

No permanent discoveries, live armor/recovery rewards, expedition category/report work, Floor-V route, extra recruitment, or four-member boss. M8.4 owns discovery, armor and recovery reward integration. Until M8.4, Rest nodes must not imply those sources are available. M8.5 owns expedition access to the completed destination.

## Ownership

Route and encounter catalog owners are `root/src/app/content/route_spec.py`, `root/src/app/content/routes/`, `enemy_spec.py`, `catalog.py`, and generated catalog tooling. Session, route cursor, reward, and clear ownership remain in `root/src/app/game/overworld_session.py`, `overworld_state.py`, `party_state.py`, and existing run-event owners. Revalidate exact call sites before implementation; do not add new APIs to this plan by assumption.

## Tests And Closure

Test route reachability/node order, every encounter definition, tier-3 validation, Floor-IV unlock from M8.1, two-member deployment, pair XP and Intuition, M7 symmetry, material grade provenance, first-clear idempotency, Rest checkpoint reload, boss settlement retry, failed writes and unchanged I-III behavior. Qualify root/web suites, content validation, compile/build, terminal and real browser journeys, PostgreSQL/migrations and pinned MicroPython on the exact SHA. Close only with independent review and green hosted evidence recorded here and in the parent.


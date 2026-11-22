# M8.6: Character Stories And Pair Interactions

**Status:** Proposed work package. M8-D2's optional-scene direction is approved; detailed M8-D1 event IDs and authored content remain open. No implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate current story/presenter owners at package entry.

## Goal

Deliver the finite optional pair and character story content without changing the permanent roster, combat rules, or global pair eligibility.

## Approval Boundary

**Already-approved inputs:** all six permanent Drifter pairs remain legal under M1; M8-D2 approves six optional pair scenes and an optional Azhvielle scene, with no relationship meter, mandatory pair locks, combo attacks, or new combat synergy; story state uses the authoritative Python runtime and existing save semantics.

**Still pending:** the exact M8-D1 event/source mapping and M8-D2's authored dialogue, choices, and optional story-report scene details. Those content details require review; no mechanical consequences are approved.

## Scope

- Author six optional pair scenes and one optional Azhvielle scene. The current parent IDs, placements, active-pair requirements, and knowledge reveal mapping are proposals until the relevant D1/D3 details are approved.
- Consume the `m8_story_reliquary_echo` evidence from M8.5 and author `m8_reliquary_echo_scene` at the Hub.
- Persist authored completion/decision evidence through the accepted story owner. Dialogue and choices remain subject to content review; they may not grant unapproved stat, combat, currency, or progression effects.

## Exclusions And Handoff

No relationship score, mandatory pair gate, combo attack, combat synergy, auto-recruitment, or new route. M8.1 owns knowledge/fact eligibility; M8.5 owns the expedition Story report and its exactly-once claim; this package owns only story text, optional interaction and its durable completion evidence.

## Ownership And Tests

Revalidate `root/src/app/game/story_state.py`, `world_state.py`, `overworld_session.py`, terminal presenters/inputs, `root/web/python/dd_bridge.py`, and `root/web/play/js/pyd4.js`. Test all six pairs in both active orders, only active pair participation where required, repeated interaction, cancelled choice, save failure, reload, migrated saves, report-before-scene ordering, and terminal/browser semantic parity.

**Persistence impact:** use the current durable event/decision owner where it can express the scenes selected for approval. No new schema is assumed; if validation requires a schema change, define its migration and backward-compatibility tests before implementation.

## Package Gates And Qualification History

- **Gate A, plan approval:** Open; review the M8-D1 event mapping and the authored M8-D2 dialogue, choices, and optional report-scene content.
- **Gate B, implementation and focused tests:** Not started; story content/state red/green tests and content validation.
- **Gate C, exact-SHA qualification and closure:** Not run; relevant root/web and browser tests, hosted cumulative CI, and pinned MicroPython because shared Python story state is touched.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Not implemented | Not run | Not run | Pending | Open |

Record the tested SHA, CI URL/results, reviewer disposition and closure in this document and the parent.


# M8.6: Character Stories And Pair Interactions

**Status:** Proposed work package. M8-D1 and M8-D2 are pending; no implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate current story/presenter owners at package entry.

## Goal

Deliver the finite optional pair and character story content without changing the permanent roster, combat rules, or global pair eligibility.

## Scope

- Author the six parent-manifest pair scenes at `floor_four_rest_midpoint`, keyed by sorted permanent Drifter identities, for all six legal pairs.
- Author optional `m8_azh_archive_memory`, requiring Azhvielle in the active pair; it may reveal `m8_fact_ashen_regent` through M8.1's knowledge owner.
- Consume the `m8_story_reliquary_echo` evidence from M8.5 and author `m8_reliquary_echo_scene` at the Hub.
- Persist authored completion/decision evidence through the accepted story owner. Any actual player choice must be specified under approved D2; no choice may grant an unapproved stat, combat, currency, or progression effect.

## Exclusions And Handoff

No relationship score, mandatory pair gate, combo attack, combat synergy, auto-recruitment, or new route. M8.1 owns knowledge/fact eligibility; M8.5 owns the expedition Story report and its exactly-once claim; this package owns only story text, optional interaction and its durable completion evidence.

## Ownership And Tests

Revalidate `root/src/app/game/story_state.py`, `world_state.py`, `overworld_session.py`, terminal presenters/inputs, `root/web/python/dd_bridge.py`, and `root/web/play/js/pyd4.js`. Test all six pairs in both active orders, only active pair participation where required, repeated interaction, cancelled choice, save failure, reload, migrated saves, report-before-scene ordering, and terminal/browser semantic parity.

## Work-Package Completion

Approve D1/D2 first; implement with focused story-state tests and content validation; obtain independent review; run relevant root/web and browser tests plus exact-SHA hosted cumulative qualification. Because shared Python story state is touched, run the pinned MicroPython probe. Record the tested SHA, CI URL/results, and closure in this document and parent.


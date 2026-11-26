# M8.6: Character Stories And Pair Interactions

**Status:** CLOSED AND SEALED. Implementation `2b16c38ebd9d904a53cae52c3b0228ac6b7ad4f5` passed independent narrative/source review and exact-SHA hosted CI. The pinned MicroPython matrix also passed at the established boundaries.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate current story/presenter owners at package entry.

## Goal

Deliver the finite optional pair and character story content without changing the permanent roster, combat rules, or global pair eligibility.

## Approval Boundary

**Already-approved inputs:** all six permanent Drifter pairs remain legal under M1; M8-D2 approves six optional pair scenes and an optional Azhvielle scene, with no relationship meter, mandatory pair locks, combo attacks, or new combat synergy; story state uses the authoritative Python runtime and existing save semantics. The owner-approved dialogue preserves pair-specific character voices, makes the Reliquary Echo a discussion of the two expedition members' report without assigning fixed Drifters as eyewitnesses, keeps Azhvielle's role in the historical record ambiguous, retains Zhaivra's living homeland and First Turning motivation, and distinguishes prayer from invoking holy magic.

**Already approved:** the event IDs, placements, reveal/source relationships, optional-scene counts, and revised narrative direction in the parent manifest. No mechanical consequences are approved.

## Scope

- Author the six approved optional pair-scene IDs and the approved optional Azhvielle archive-memory ID at their manifest placements. Use the approved M8-D3 knowledge reveal mapping and the owner-approved dialogue/choice direction.
- Consume the `m8_story_reliquary_echo` evidence from M8.5 and author `m8_reliquary_echo_scene` at the Hub.
- Persist authored completion/decision evidence through the accepted story owner. Scenes do not grant stat, combat, currency, or progression effects beyond the explicitly approved Archive Memory knowledge confirmation.

## Exclusions And Handoff

No relationship score, mandatory pair gate, combo attack, combat synergy, auto-recruitment, or new route. M8.1 owns knowledge/fact eligibility; M8.5 owns the expedition Story report and its exactly-once claim; this package owns only story text, optional interaction and its durable completion evidence.

## Ownership And Tests

Revalidate `root/src/app/game/story_state.py`, `world_state.py`, `overworld_session.py`, terminal presenters/inputs, `root/web/python/dd_bridge.py`, and `root/web/play/js/pyd4.js`. Test all six pairs in both active orders, only active pair participation where required, repeated interaction, cancelled choice, save failure, reload, migrated saves, report-before-scene ordering, and terminal/browser semantic parity.

**Persistence impact:** use the current durable event/decision owner where it can express the scenes selected for approval. No new schema is assumed; if validation requires a schema change, define its migration and backward-compatibility tests before implementation.

## Package Gates And Qualification History

- **Gate A:** Owner-authorized implementation; the final dialogue direction and four localized corrections are approved.
- **Gate B:** Complete; approved scene content, session ownership, terminal/browser presentation, and focused persistence tests are implemented. No schema increment is introduced.
- **Gate C:** CLOSED; owner acceptance and independent review accepted the exact-SHA evidence below.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| `2b16c38ebd9d904a53cae52c3b0228ac6b7ad4f5` | [45739394737](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/45739394737), passed | Pinned MicroPython 1.29.0 binary `6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA`; 1408 KiB stable 3/3, 1216 KiB expected memory limit 3/3; CPython native, forced overlay, and semantic parity passed | Accepted | CLOSED AND SEALED |

Record the tested SHA, CI URL/results, reviewer disposition and closure in this document and the parent.


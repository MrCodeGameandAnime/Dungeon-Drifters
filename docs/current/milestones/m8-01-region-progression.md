# M8.1: Region Progression, Dungeon Selection, And Knowledge

**Status:** CLOSED AND SEALED. The owner accepted the clean independent review of implementation SHA `9ef0e6fd05da8a57602372d8b431c1a27b3bb36a` and formally sealed M8.1.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`, runtime/disk schema 25. The implementation at `9ef0e6fd05da8a57602372d8b431c1a27b3bb36a` adds schema 26 and the approved progression/knowledge foundation.

## Goal

Provide the authoritative, persistent regional progression, Hub Region Portal, and knowledge foundation for approved content. This package owns region/destination eligibility and facts, not the playable floor content that sets later clear outcomes.

## Approval Boundary

**Already-approved inputs:** M8-D1's Hub Region Portal, explicit authored membership, Region 1 containing Floors I-V, permanent backward travel, and durable Region 2 unlock after the genuine Floor V boss; M8-D3's Unknown/Rumored/Confirmed model and completed-floor Scouting eligibility; and M8-D5's separate four-Drifter reunion/assignment boundary. Preserve M1's permanent roster/active-pair separation, M6's energy independence from dungeon play, M7's combat state, and the existing save/history trust boundary.

**Decision status:** no owner-level M8 product decisions remain open. M8-D6's limited static-asset scope is approved and is not a prerequisite for this progression package. Gate A was approved at plan commit `0cc3cb878203a9ca817d5af0d84baaf960e2d09a`; exact-SHA CI run `45108637173` passed.

## Scope

- Represent Floor IV and Floor V completion and the M8 arena-revealed event using the existing typed progression/story/world owners where safe.
- Define explicit authored `region_1` membership for the existing Surface/Floors I-III and approved Drowned Reliquary/Floor IV and Ashen Vault/Floor V. Never derive membership from floor-number arithmetic. Treat five floors as a design target, not an engine ceiling.
- Implement the Region Portal in the existing Hub. Region 1 remains available through existing campaign progression; a known, unlocked region with playable content can be selected and entered from the Hub. Region 2 stays hidden until legitimately unlocked, then appears as unlocked but unavailable with a clear no-playable-content explanation until routes exist.
- Preserve permanent backward travel to eligible content. Revisit cannot erase later clears, claims, roster, equipment, or expedition progression and cannot repeat one-time rewards.
- Define destination visibility and entry rules: Floor IV after Floor III clear and all four permanent recruits; Floor-V approach after Floor-IV clear; reunion only after the arena reveal, with all four permanent Drifters and no active expedition assignment.
- Apply the approved Unknown/Rumored/Confirmed knowledge model and the four approved fact IDs/reveal mappings in the parent manifest; viewing or loading never promotes a fact.
- Keep the six legal active pairs legal in ordinary content. Floor IV and the Floor-V approach accept any legal active pair; the reunion is a separate four-person Hub event.
- Make the same authoritative eligibility/fact result available to terminal and browser presenters.

## Exclusions

No routes, combat content, recruitment changes, item keys, expedition report implementation, numeric pair relationship system, parallel progression API/save representation, or client-owned progression logic. Do not broaden or change Floors I-III semantics. Extend existing typed owners and the existing migration chain as required; do not preassign a future schema version.

## Ownership And Handoff

| Concern | Existing owner to revalidate | Contract produced |
| --- | --- | --- |
| Clear and roster eligibility | `root/src/app/game/party_state.py`, `overworld_state.py`, `overworld_session.py` | Stable Floor-IV/V clear and entry evidence; M8.3 and M8.8 write only through the accepted clear boundary. |
| Region membership and portal | Authored destination/route catalog, `overworld_session.py`, Hub presenter/input and browser Python bridge | M8.1 owns the Region Portal and authoritative region availability; explicit authored membership maps existing and approved destinations to regions. M8.8 records Region 2 unlock only through this canonical progression owner. |
| Knowledge and story evidence | `root/src/app/game/story_state.py`, `world_state.py` | Persist fact/event identities and visibility state; M8.5 reports and M8.6 scenes use the named reveal/consumer IDs. |
| Persistence | `root/src/app/persistence/save_document.py` and current migration chain | Schema-25 legacy defaults do not imply new clears or discoveries; remote historical revisions stay immutable. |
| Client projection | Existing terminal presenter/input and browser Python bridge | Clients display authoritative options and reasons; no JavaScript unlock calculation. |

## M8.1 Gate A Plan And Approval

### State Ownership And Migration

- Keep floor-clear and region-unlock authority in the existing `PartyState`; Region 1 remains available through the existing campaign path. Add distinct durable Floor-IV clear, Floor-V clear, and Region-2-unlocked state, with monotonic transitions. A floor clear must not imply a region unlock, and a region unlock must not imply a floor clear.
- Keep briefing/arena event evidence and the approved four-fact knowledge map in the existing `StoryState`. Unrecorded facts read as Unknown; updates are monotonic (`Unknown -> Rumored -> Confirmed`). Reuse the existing event/decision snapshot owner rather than introducing a parallel campaign state object.
- At the approved entry baseline, runtime and disk schema were 25. The implementation adds the typed snapshot fields through an additive migration to schema 26. Legacy defaults are Floor IV/V uncleared, Region 2 locked, and all four facts Unknown. Historical remote payloads and digests remain immutable.

### Authored Content And Client Flow

- Add explicit authored region/destination membership and prerequisite data for the approved IDs; never infer a region from a floor number. Keep this as finite catalog data, not a general campaign engine.
- The Region Portal and destination offers are projected by Python from persisted progression, roster, knowledge, and implemented route availability. Session handlers revalidate every submitted action. A destination whose route belongs to a later M8 package may be shown as unavailable until that package supplies the route; it cannot start a missing route.
- Add semantic controls to the existing `OverworldScreen`/`OverworldAction` and `OverworldSession` flow. Terminal bindings and `dd_bridge.py`/`pyd4.js` only translate and render the Python-owned view; JavaScript does not calculate unlocks or mutate progression.

### Focused And Cumulative Proof

- Domain/persistence tests cover defaults and migration from schema 25, current-schema validation, monotonic state transitions, all approved destination prerequisites, all six legal pairs, full-roster reunion eligibility, no active expedition, independent clear/unlock evidence, save failure without candidate-state publication, reload, and immutable remote history.
- Presenter/session and terminal/browser contract tests cover equivalent enabled/disabled destination offers, clear explanations, stale/forged submissions, and no fact promotion from viewing or loading. The briefing journey verifies its Rumored transition once; each approved confirmation path verifies save/reload and no duplicate effect.
- Gate C runs root and web pytest, authored-content validation, compile/build, real browser smoke, PostgreSQL service tests, migration-from-zero/Alembic parity, and the pinned MicroPython qualification on the exact candidate SHA.

**Approved:** preserve `PartyState`/`StoryState` ownership, use an additive migration, expose later destinations only as knowledge and implemented-route prerequisites allow, keep all unlock calculations in Python, and qualify the live Hub journey plus independently testable downstream clear/reveal contracts. The full Floor IV/V gameplay journeys remain with M8.3, M8.5, M8.7, and M8.8 when those routes and consumers become reachable; no unfinished routes are manufactured for M8.1.

## Dependencies

Gate 0 is closed. M8.2 consumes the Floor-IV eligibility signal for Grade-IV recipes. M8.3 supplies the real Floor-IV clear; M8.5 consumes completed-floor eligibility; M8.7 supplies the arena reveal; M8.8 supplies the Floor-V clear. These child packages may not invent competing clear flags.

## Persistence And Regression Requirements

Plan the schema migration from the actual entry schema. New saves and migrated saves must agree; Region 1 preserves the existing campaign path; old saves do not gain a Region 2 unlock, missing facts remain Unknown, and missing new floor clears remain false. Region unlock state is separate from each floor clear. Test portal entry/return, all six pairs, valid/invalid/stale destination offers, four-member eligibility, the expedition block, duplicate event submission, save failure, reload, and terminal/browser parity. Test that viewing a region/destination never upgrades a fact.

M8.1 owns migration for region membership/unlock, floor-clear, and knowledge state. M8.3 and M8.8 write through its canonical progression boundary and must not introduce duplicate completion or unlock fields.

M8.1 owns the first end-to-end Region Portal journey because it first makes the portal/navigation reachable in normal Hub play. Cover a new campaign and an eligible migrated save, enter a legitimately available Region 1 destination, return through the Hub, revisit earlier eligible content, and verify newer clears/rewards remain intact. M8.10 repeats the cross-package journey after Region 2 unlock.

M8.1 owns the trigger and durable reveal for the approved `m8_drowned_reliquary_briefing` event and `m8_fact_drowned_reliquary` mapping. Its authored scene text remains subject to package content review. Exercise the normal Hub path on a newly eligible campaign and a migrated save already holding the Floor III clear and four recruits. Verify the approved Rumored state once, reload preserves it, and unlearned enemy details stay hidden. Also cover a save missing each prerequisite.

## Package Gates And Qualification History

- **Gate A, plan approval:** Approved at `0cc3cb878203a9ca817d5af0d84baaf960e2d09a`; exact-SHA CI run `45108637173` passed.
- **Gate B, implementation and focused tests:** Implemented. Focused state, migration, portal, briefing, presenter, terminal, browser-bridge, and browser-smoke coverage is included; root and web suites pass locally.
- **Gate C, exact-SHA qualification:** Passed on implementation SHA `9ef0e6fd05da8a57602372d8b431c1a27b3bb36a`; exact-SHA hosted run `45195824408` passed both jobs. Local root/web, content, compile/build, browser, pinned MicroPython, and service-unit checks also passed. Local Docker was unavailable; hosted PostgreSQL, migration-from-zero, and Alembic parity passed.

| Implementation SHA | Hosted CI URL/results | Migration/runtime evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| `9ef0e6fd05da8a57602372d8b431c1a27b3bb36a` | [Actions run 45195824408](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/45195824408): Tests and Profile Service (PostgreSQL) passed | Schema 25-to-26 migration tests pass; migration-from-zero and Alembic parity pass hosted; pinned MicroPython v1.29.0 matrix passes locally | Clean independent review accepted by owner; no blocking findings | CLOSED AND SEALED |

Qualification-record commit `141513ff8946e4992e2f99472e27f79151150362` passed exact-SHA CI [run 45197625564](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/45197625564). This records the reviewed evidence; it does not replace the implementation SHA as the gameplay baseline.

The independent review covered the schema-25-to-26 migration, authoritative region availability, monotonic knowledge persistence and failed-write behavior, and sync/regression fixtures. The owner accepted its clean disposition. Preserve the sealed migration, progression, knowledge and terminal/browser contracts as the baseline for later packages.


# M8.1: Region Progression, Dungeon Selection, And Knowledge

**Status:** Proposed work package. M8-D1, M8-D3, and M8-D5 are pending; no implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate source paths and current HEAD when this package is approved for implementation.

## Goal

Provide the authoritative, persistent progression and knowledge foundation required by the proposed Floor-IV/V manifest if approved. This package owns eligibility and facts, not the playable floor content that sets the later clear outcomes.

## Approval Boundary

**Already-approved inputs:** preserve M1's permanent roster/active-pair separation, M6's completed-floor expedition rule and energy independence from dungeon play, M7's combat state, and the existing save/history trust boundary.

**Still pending:** M8-D1 (finite scope), M8-D3 (knowledge/reveal contract), and M8-D5 (reunion/assignment boundary). No implementation begins until Gate 0 resolves them.

## Scope

- Represent Floor IV and Floor V completion and the M8 arena-revealed event using the existing typed progression/story/world owners where safe.
- Define destination visibility and entry rules: Floor IV after Floor III clear and all four permanent recruits; Floor-V approach after Floor-IV clear; reunion only after the arena reveal, with all four permanent Drifters and no active expedition assignment.
- Define Unknown/Rumored/Confirmed knowledge for the parent manifest's four stable fact IDs and the exact reveal sources listed there.
- Keep the six legal active pairs legal in ordinary content. Floor IV and the Floor-V approach accept any legal active pair; the reunion is a separate four-person Hub event.
- Make the same authoritative eligibility/fact result available to terminal and browser presenters.

## Exclusions

No routes, combat content, recruitment changes, item keys, expedition report implementation, numeric pair relationship system, new APIs/schema number, or client-owned progression logic. Do not broaden or change Floors I-III semantics.

## Ownership And Handoff

| Concern | Existing owner to revalidate | Contract produced |
| --- | --- | --- |
| Clear and roster eligibility | `root/src/app/game/party_state.py`, `overworld_state.py`, `overworld_session.py` | Stable Floor-IV/V clear and entry evidence; M8.3 and M8.8 write only through the accepted clear boundary. |
| Knowledge and story evidence | `root/src/app/game/story_state.py`, `world_state.py` | Persist fact/event identities and visibility state; M8.5 reports and M8.6 scenes use the named reveal/consumer IDs. |
| Persistence | `root/src/app/persistence/save_document.py` and current migration chain | Schema-25 legacy defaults do not imply new clears or discoveries; remote historical revisions stay immutable. |
| Client projection | Existing terminal presenter/input and browser Python bridge | Clients display authoritative options and reasons; no JavaScript unlock calculation. |

## Dependencies

Entry requires approval of the relevant parent decisions. M8.2 consumes the Floor-IV eligibility signal for Grade-IV recipes. M8.3 supplies the real Floor-IV clear; M8.5 consumes completed-floor eligibility; M8.7 supplies the arena reveal; M8.8 supplies the Floor-V clear. These child packages may not invent competing clear flags.

## Persistence And Regression Requirements

Plan the schema migration from the actual entry schema. New saves and migrated saves must agree; missing facts remain Unknown and missing clears remain false. Test valid/invalid/stale entry offers, all six pairs, four-member eligibility, the expedition block, duplicate event submission, save failure, reload, and terminal/browser parity. Test that viewing a destination never upgrades a fact.

M8.1 owns the migration for clear/knowledge state. M8.3 and M8.8 write through its canonical clear boundary and must not introduce duplicate completion fields.

M8.1 owns the trigger, authored Hub scene, and durable reveal for `m8_drowned_reliquary_briefing`. Exercise the normal Hub path on both a newly eligible campaign and a migrated save already holding the Floor III clear and four recruits. Verify the briefing reveals the destination as Rumored once, reload preserves the fact, and unlearned enemy details stay hidden. Also cover a save missing each prerequisite.

## Package Gates And Qualification History

- **Gate A, plan approval:** Open; resolve M8-D1/D3/D5 and review this scope before implementation.
- **Gate B, implementation and focused tests:** Not started; use red/green tests and independent diff review.
- **Gate C, exact-SHA qualification and closure:** Not run; root/web, content, compile/build, browser, PostgreSQL/migrations and pinned MicroPython are required because shared state/save code is touched.

| Implementation SHA | Hosted CI URL/results | Migration/runtime evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Not implemented | Not run | Not run | Pending | Open |

Do not close on local tests alone. Record exact SHA, exact run URL/results, migration evidence, reviewer disposition and closure status here and in the parent.


# M4 Enemy Progression And Dungeon Pressure Implementation Plan

> Implementation method: use `superpowers:executing-plans` for native gate-by-gate execution. This is a planning contract, not authorization to select every possible enemy or hazard mechanic.

**Status:** Gate 0 decisions approved, 2026-11-05. M4A implementation is bounded by [the Floor II plan](m4-floor-ii-implementation.md). M4B remains sequenced after M5; revalidate integration APIs at that entry without reopening the approved M4-D6/D7 product contracts.

**Goal:** Deliver authored enemy scaling, bounded decision policies, reward/discovery integration, and meaningful counterplay, then prove staged recruitment through the first full-roster boss.

**Architecture:** Keep immutable archetype definitions distinct from fresh encounter instances and encounter placement. Extend existing content/catalog/Battle/session boundaries. M4 adds authored numerical tiers, identity-based resistance/weakness, persisted reward/search outcomes, and one telegraphed hazard. Enemy action/target selection remains bounded and unchanged. Formations and boss phases are deferred. Do not relocate packages to match an old design sketch.

**Tech stack:** Python content/enemy/combat/runtime, existing RNG injection and validation tooling, semantic clients, saves, pytest/Playwright and pinned runtime qualification.

## Authority, Dependencies, And Delivery Split

- [Enemy design](../../future/enemy-archetypes-scaling-and-capability-progression.md), archetype/rank/tier/capability separation and Defend contracts.
- [Economy](../../future/dungeon-progression-difficulty-and-economy.md), pressure, soft walls, rewards and death; [party design](../../future/party-and-expedition-core-loop.md), roster and convergence.
- [Roadmap](development-roadmap.md), M4 and fixed recruitment; [M2](m2-preparation-trading-escape.md) supplies and escape; [M3](m3-character-advancement.md) damage/potency/discovery contracts; [component names](../weapons/component.md).

**Approved delivery sequence:** **M4A** follows M2/M3: enemy systems plus the bounded Floor II route, D3 recruitment, and Floor II clear. M4A is independently qualified before M5 begins. **M5** follows M4A. **M4B** follows M5: the bounded Floor III route, D4 recruitment, and the first live four-Drifter boss, qualified before M6. M4 is fully closed only after both tranches. M5 depends on M4A, not M4B; this avoids a circular dependency. M8 completes region depth and later content rather than postponing these prerequisite recruitment/boss proofs.

Non-goals: a new combat engine, every illustrative AI/hazard, persistent injuries/durability without approval, campaign-wide balancing, four-person ordinary Floor I battles, granting healing/Super by rank/tier, or expeditions before Floor IV.

## Verified Baseline And Actual Gaps

Five archetypes, rank/role/behavior/capability data, structured moves, XP/gold, and deterministic item drops exist. `EnemySpec.supported_tiers` currently accepts only `(0,)`; `create_definition()` rejects unsupported tiers. Actual creation lives in `root/src/app/content/catalog.py` as `create_enemy_definition()`/`create_enemy_state()`, not in a currently existing `enemies/factory.py` or `enemies/scaling.py`.

`root/src/app/enemies/definition.py`/`state.py` separate definitions and instances. `Battle.select_enemy_move()` chooses uniformly among affordable moves; living party targets are selected randomly. Core Defend/capability support exists, but richer selection policies, typed resistances, meaningful formations, and boss phases do not follow automatically from those fields. The source's deferred "EXP/gold/loot" list is partly stale: extend real rewards rather than rebuilding them.

`RouteSpec` is an ordered route with globally unique nodes, while session/save validation specifically knows Surface/Floor I. Floors II/III and their recruitment scenes are absent. `Battle(..., party=...)` accepts multiple members structurally, but party/session integration and live four-member targets/resources/rewards need proof through M1/M4B. Do not claim that accepting a tuple already qualifies the full boss.

## Fixed Contracts And Ownership

Archetype is identity; rank is descriptive authored complexity; tier is numerical strength; encounter stage is placement. Tier must be an integer, not bool, and nonnegative, then supported by the archetype's authored policy. Tier changes must not add moves, heal, Defend, Super, or alter identity. Tier zero must reproduce current authored statistics and move outputs exactly unless an individual approved content change is separately recorded.

Approved tier assignment: existing Tier 0 outputs remain exact; Floor II uses authored Tier 1 values; Floor III uses authored Tier 2 values. Tier 3 remains later content. Per-archetype numeric scaling and rewards are authored data; rewards are not automatically multiplied by tier. Tier does not grant capabilities or moves.

Enemy definitions own baseline stats/moves/capabilities and approved scaling/behavior identifiers. Encounter placement owns requested tiers and formations. `EnemyState` owns fresh current resources and instance stats; Battle/`CombatState` owns transient policy/phase state. Keep player and enemy Defend distinct; preserve current reductions/caps until an explicitly approved change. Do not apply player level/weapon-grade rules as enemy tiers.

AI continues choosing uniformly among legal affordable moves and randomly among living active Drifters. Healing and Defend remain capability-gated; empty legal sets retain an explicit safe fallback. Approved elemental/alchemical resistance and weakness use identity, not new defense stats: resistance reduces matching component damage by 25%, weakness increases it by 25%, after generic mitigation and before Brace/Defend. There are no immunities and no new elemental defense classes. Physical/magical defense routing remains the existing M3 contract. Formations and boss phases are deferred and are not implementation requirements for M4A or M4B.

One selected environmental pressure must have visible warning and a real preparation counter from M2/M3 in M4A; M5 armor may supply additional counters in M4B. M4A must not depend on unfinished M5 equipment. Recommended levels/soft matchups do not deny entry solely for being underleveled. Story/floor unlocks and required-character conditions remain legitimate entry rules. Hub return still restores full HP/mana; injury/durability examples do not override that contract.

Rewards enter existing unsecured run state and secure only through the chosen exit rules. Resolve any probabilistic loot/search outcome once at an authoritative event boundary; preserve enough per-outing outcome/claim evidence to prevent rerolls or duplicate grants through view rebuilds, repeat inputs, or Rest reloads. Global defeated-encounter history must not suppress legitimate replay rewards. For permanent-discovery searches, only the selected active searcher's existing Intuition discovery bonus modifies the authored base chance. Do not add a quality roll or guarantee rare loot.

## Content And Recruitment Handoffs

Floor II is approved as ten combat encounters, one midway Rest after encounter 5, one pre-boss Rest after encounter 9, and a boss as encounter 10. It includes one telegraphed physical cave-in pressure countered by the existing Brace/Defend systems, at a bounded authored encounter; it adds no status, injury, durability, formation, or boss-phase mechanic. The D3 event is offered at the midway Rest. The Floor III manifest uses the same bounded ten-encounter/two-Rest structure, places D4 before the final four-Drifter boss, and remains M4B work after M5.

Floor II introduces legitimate Grade-II Metal/Fiber/Timber/Core sources and enough material to exercise the already-authored Grade-II improvement recipes across all four slot families. Reuse the sealed generic weapon progression; do not create alternate components or alter the weapon schema. Floor III similarly introduces Grade III in M4B. Earlier floors must not yield later grades. Use existing enemy archetypes where practical; exact encounter compositions and per-archetype values are authored in the bounded floor content, not generalized into a new balance framework.

D3/D4 are recruitment positions among remaining canonical identities, each costing 65 secured shared gold. Recruitment must work for all legal starting/companion choices and never duplicate an owned Drifter. A successful recruitment during a run adds the canonical roster member but cannot change the locked active pair until Hub return. Insufficient funds reject atomically, do not complete the event, and leave it retryable; Floor II remains replayable so the player can return after obtaining enough secured gold. Initialize a recruit with that Drifter's authored baseline Level 1 state, current kit, and base signature weapon; do not fabricate XP, GP, purchases, or weapon progress. The Floor III boss uses all four; earlier ordinary encounters/bosses retain their legal active party.

The Floor III pre-boss event explicitly transitions from the ordinary pair to the four-member encounter, with no substitution during an active battle. M1's ordinary pair-selection restrictions remain intact. Pre-boss XP remains with its earning pair. On boss victory, each of the four Drifters receives the full authored per-member boss XP award, then their own M3 Intuition bonus; do not split that per-member award four ways. No free healing occurs at the party-size transition. The full-party battle targets any living party member under the existing random-target policy; defeat occurs only when all four are down. Save/load and defeat/return preserve the approved mode, payout, and one-time clear evidence. This contract also becomes the M8 reunion-boss integration boundary.

Discovery searches use authored base probabilities and the active Drifter selected to search. Apply that Drifter's existing `discovery_bonus_bps_from_intuition()` as a relative bonus to the authored base chance; never average party Intuition. The first Floor II source starts at 10%; common Grade-II material drops start at 20% per authored entry and Grade-II Core drops at 10%. These are conservative, editable content values, not locked balance. Resolve each search outcome when the search is confirmed and each enemy-drop outcome at encounter victory. Persist outcome identity/results with the run and apply reward changes atomically so reloads, repeated inputs, or view rebuilds cannot reroll or duplicate them. A failed search may be attempted on a later genuine run; a claimed permanent source remains globally one-time. Source reward type/amount remains authored under M3; no separate quality roll is added.

## Integration, Saves, And Clients

Expected areas: `root/src/app/content/enemy_spec.py`, `encounter_spec.py`, `route_spec.py`, `catalog.py`, authored content directories and generation/validation tools; `root/src/app/enemies/definition.py`/`state.py`; `root/src/app/combat/battle.py`, `resolver.py`, `combat_state.py`; current game route/session/story/world/party owners. Add cohesive policy/effect modules only when the selected mechanics need them. All exact APIs/new paths are revalidated at tranche entry.

Persist only source progression, route/recruitment/claim evidence and pending outcomes required at supported checkpoints. Do not introduce arbitrary live-battle saves just to persist boss phases. Extend validators that currently hard-code Surface/Floor I and schema migrations through the existing chain, preserving immutable remote history. Unsupported tier/content, corrupt phase references, or inconsistent roster/floor flags reject before reconstruction rather than silently downgrade.

Terminal/browser must show current actor, party resources, readable threat/phase/formation/resistance information at the approved knowledge level, hazard warnings, actual reward/drop outcomes, and blocked reasons. Both select actions/targets through the same presenter inputs. No browser-side AI, damage, drop rolls, or phase scripts.

## Review Focus

- A numerical tier must not grant moves or capabilities; Gate 1 checks tier-zero equivalence and positive-tier identity.
- Reusing an archetype must not share HP/mana/status across instances; Gate 1 checks independent mutation.
- A view rebuild/Rest reload must not reroll loot, while a genuine replay still earns eligible rewards; Gate 3 checks outcome identity.
- Recruitment and floor flags must not unlock expeditions before the Floor III boss; Gates 3/4/5 check live staged progression.
- A four-member boss must not end when only the original Drifter falls or charge another member's resources; Gate 4 checks live actors and outcomes.

## Gates And Tests

### Gate 0 - Approve The Initial Policies And Floor II Manifest

- [x] Approve and record M4-D1 through D5 for M4A and M4-D6/D7 in advance for M4B. M4B revalidates code interfaces after M5, not product decisions.
- [x] Approve supported tier policies, identity resistance/weakness, unchanged bounded enemy action/target selection, reward/search event boundaries, discovery Intuition, and the single cave-in/Brace/Defend counter.
- [x] Freeze the bounded Floor II route, D3 timing/cost/retry behavior, Grade-II material families, and Floor II clear gate. The full Floor III manifest remains M4B content after M5.

Proof: all M4-D1 through D7 decisions are recorded below; M4A content and implementation boundaries are in [M4A Floor II Implementation Plan](m4-floor-ii-implementation.md). Unselected source examples remain examples.

### Gate 1 - Numerical Tier And Definition Integrity (M4A)

- [ ] Add red/green cases in existing `test_enemy_content.py`, `test_enemy_state.py`, `test_m10_enemy_definitions.py`, and content-tool tests for tier-zero equivalence, supported positive tiers, bool/negative/unsupported rejection, and unchanged move/capability identity.
- [ ] Implement authored policies and encounter tier placement using real catalog creation. Two enemies made from one definition cannot share HP/mana/Super/status mutation.
- [ ] Reject duplicate/unknown policy/content IDs and invalid scaling parameters in content validation, not only at battle entry.

Proof: deterministic same-archetype scaling and instance isolation, with current Surface/Floor I golden cases unchanged.

### Gate 2 - Resistance And Hazard (M4A)

- [ ] Preserve and test the existing random legal-affordable move and random living-active-target behavior; tier does not grant capabilities or moves.
- [ ] Implement and test approved elemental/alchemical identity resistance/weakness at the documented position in the M3 component pipeline; no immunity or new defense stat.
- [ ] Implement the one telegraphed physical cave-in and its existing Brace/Defend counter. Prove warning, response window, mitigation, and no mutation on rejected/blocked actions.
- [x] Defer formations and boss phases; they are not M4A or M4B deliverables.
- [ ] Verify invalid target, missing counter, or blocked action has the approved consequence without partial resource spending; unprepared low-level entry is not denied just for power level.

Proof: a prepared pair can identify and counter the authored Floor II threat; elemental/alchemical identity changes only the approved damage component multiplier.

### Gate 3 - Reward/Discovery And Floor II Loop (M4A)

- [ ] Implement authored reward/drop tables and the discovery search consumer, then the Floor II route, D3 event, Grade-II sources, and Floor II completion gate through existing owners.
- [ ] Test once-only rolls/claims, visible items in pending rewards and secured inventory after return, loss on death, correct exit payouts, and inability to farm Grade II on Floor I. Verify item/recruitment events are safe under duplicate submits and reload.
- [ ] Complete a terminal and built-browser D1+D2 -> Floor II -> D3 -> return/save/reload flow, inspect all three, and select only legal recruited pairs under M1 policy.

Proof: focused flow/persistence/bridge tests, real content validation, browser journey, and shared M4A qualification. M5 may start after M4A is accepted; M4B remains explicitly open.

### Gate 4 - Floor III Readiness And Full-Party Boss (M4B, After M5)

- [ ] After M5, revalidate M1-M5 interfaces and translate the already-approved M4-D6/D7 contracts into the Floor III manifest, D4 scene, and full-party boss integration. Do not reopen their product rules. Use M5 items/effects only through its accepted contract.
- [ ] Author the bounded Floor III path, legitimate Grade-III progression content, and D4 event. Four recruited members do not begin expedition assignments here.
- [ ] Extend party Battle/session/presentation tests for four living/defeated members, exact actor-owned moves/mana/Super/items, individual Dexterity ordering, mid-round reranking, target validity, party-wide mechanics only where authored, and victory/defeat when the original Drifter is down.
- [ ] Prove first four-Drifter boss reward allocation and once-only Floor III clear/story flags. No Rest/load path can duplicate D4 or bypass the boss to unlock expeditions.
- [ ] Test the authored pair-to-four encounter transition with pre-boss pending rewards. Earlier pair-earned XP must retain its approved recipients; wrong-phase transitions, mid-battle substitutions, failed saves and reload cannot change attribution or grant boss rewards twice.

Proof: ordinary semantic terminal and built-browser Floor III recruitment -> four-Drifter boss -> Hub save/reload journey. Structural fixtures alone do not close this gate.

### Gate 5 - Final M4 Qualification And M6 Readiness

- [ ] Extend the real probe for selected tier/policy/reward logic plus D3/D4/first full-party boss and teardown; keep historical route measurement ordering intact.
- [ ] Run shared cumulative qualification on the accepted M4B tree and record separate M4A/M4B evidence/SHA. Verify full roster recruited, Floor III boss complete, no live expedition, and readiness for the Floor IV unlock.

Closure: M4A enemy/Floor II and M4B Floor III proofs both pass; material/recruitment gates are real; first full-party boss is playable; no blanket four-person boss conversion or hidden permanent-injury system was introduced. M8 owns remaining approved region content.

## Approved Product Decisions

All M4-D1 through M4-D7 product decisions are approved. M4B implementation remains deferred until after M5; integration details are revalidated at that time.

| ID | Approved decision |
| --- | --- |
| M4-D1 | Tier 0 remains exactly compatible. Floor II uses authored Tier 1 values; Floor III uses authored Tier 2 values; Tier 3 is deferred. Numeric scaling and rewards are authored per archetype; tier does not automatically scale rewards or add moves/capabilities. Values are initial and tunable. |
| M4-D2 | Keep the current legal-affordable random move selection and random living-active-target policy. Elemental/alchemical identities may be resisted or weakened by 25% after generic mitigation and before Brace/Defend. No immunities, new defense stats, or change to physical/magical mitigation. |
| M4-D3 | Use one visibly telegraphed physical cave-in pressure on Floor II, countered through existing Brace/Defend. Do not add status effects, injuries, durability, formations, or boss phases. Formations and phases remain deferred. |
| M4-D4 | Author conservative discovery base probabilities and apply the selected searching active Drifter's existing Intuition discovery bonus as a relative chance bonus. Do not average party Intuition. Initial tunable values: 10% for the first Floor II discovery source, 20% per authored common Grade-II material drop entry, and 10% per Grade-II Core drop entry. Resolve search on confirmation and drops at encounter victory; persist outcomes to prevent reload/input rerolls or duplicate awards. A later genuine run may retry a failed search; a claimed source stays one-time. Source reward amounts remain authored by M3; no new quality roll or guaranteed rare drop. |
| M4-D5 | Floor II is ten battles with a midway Rest after battle 5, a pre-boss Rest after battle 9, and the boss at battle 10. D3 is offered at the midway event, selected among unrecruited canonical Drifters, costs 65 secured shared gold, and joins the roster without changing the locked active pair. Insufficient gold leaves the event unclaimed/retryable and cannot softlock progression. A recruit starts at its authored Level 1 baseline with the current kit and base signature weapon, without fabricated progression. Floor II introduces Grade-II Metal, Fiber, Timber, and Cores; Floor I remains unchanged. |
| M4-D6 | Floor III follows the bounded ten-battle/two-Rest scaffold, introduces Grade III materials, and recruits the sole remaining D4 for 65 secured shared gold before its final boss. D4 uses the same baseline/retry/active-pair rules as D3. Implement only after M5. |
| M4-D7 | The Floor III final boss uses all four recruited Drifters. Pre-boss XP remains with its earning pair. Each Drifter gets the full authored per-member boss XP award plus their own Intuition bonus. No free healing at transition; enemy targets are random among living members; defeat requires all four down. Only boss clear unlocks Floor IV/expeditions. Implement only after M5. |

Durability/persistent injuries remain unapproved optional M9 dispositions; no decision here silently selects them.

# M4 Enemy Progression And Dungeon Pressure Implementation Plan

> Implementation method: use `superpowers:executing-plans` for native gate-by-gate execution. This is a planning contract, not authorization to select every possible enemy or hazard mechanic.

**Status:** Draft for review, 2026-10-29. Later integration APIs must be revalidated after M2/M3.

**Goal:** Deliver authored enemy scaling, bounded decision policies, reward/discovery integration, and meaningful counterplay, then prove staged recruitment through the first full-roster boss.

**Architecture:** Keep immutable archetype definitions distinct from fresh encounter instances and encounter placement. Extend existing content/factory/Battle/session boundaries; add only the selected numerical, AI, resistance, formation, phase, and hazard contracts. Do not relocate packages to match an old design sketch.

**Tech stack:** Python content/enemy/combat/runtime, existing RNG injection and validation tooling, semantic clients, saves, pytest/Playwright and pinned runtime qualification.

## Authority, Dependencies, And Delivery Split

- [Enemy design](../../future/enemy-archetypes-scaling-and-capability-progression.md), archetype/rank/tier/capability separation and Defend contracts.
- [Economy](../../future/dungeon-progression-difficulty-and-economy.md), pressure, soft walls, rewards and death; [party design](../../future/party-and-expedition-core-loop.md), roster and convergence.
- [Roadmap](development-roadmap.md), M4 and fixed recruitment; [M2](m2-preparation-trading-escape.md) supplies and escape; [M3](m3-character-advancement.md) damage/potency/discovery contracts; [component names](../weapons/component.md).

**Proposed delivery decomposition for review:** **M4A** follows M2/M3: enemy systems plus an approved bounded Floor II path, D3 recruitment, and a Floor II completion gate sufficient to reach the next story stage. It is independently qualified before M5 begins. **M4B** follows M5: a bounded Floor III path, D4 recruitment, and the first live four-Drifter boss, qualified before M6. M4 is fully closed only after both tranches. M5 depends on M4A, not M4B; this avoids a circular dependency. M8 completes region depth and later content rather than postponing these prerequisite recruitment/boss proofs.

Non-goals: a new combat engine, every illustrative AI/hazard, persistent injuries/durability without approval, campaign-wide balancing, four-person ordinary Floor I battles, granting healing/Super by rank/tier, or expeditions before Floor IV.

## Verified Baseline And Actual Gaps

Five archetypes, rank/role/behavior/capability data, structured moves, XP/gold, and deterministic item drops exist. `EnemySpec.supported_tiers` currently accepts only `(0,)`; `create_definition()` rejects unsupported tiers. Actual creation lives in `root/src/app/content/catalog.py` as `create_enemy_definition()`/`create_enemy_state()`, not in a currently existing `enemies/factory.py` or `enemies/scaling.py`.

`root/src/app/enemies/definition.py`/`state.py` separate definitions and instances. `Battle.select_enemy_move()` chooses uniformly among affordable moves; living party targets are selected randomly. Core Defend/capability support exists, but richer selection policies, typed resistances, meaningful formations, and boss phases do not follow automatically from those fields. The source's deferred "EXP/gold/loot" list is partly stale: extend real rewards rather than rebuilding them.

`RouteSpec` is an ordered route with globally unique nodes, while session/save validation specifically knows Surface/Floor I. Floors II/III and their recruitment scenes are absent. `Battle(..., party=...)` accepts multiple members structurally, but party/session integration and live four-member targets/resources/rewards need proof through M1/M4B. Do not claim that accepting a tuple already qualifies the full boss.

## Fixed Contracts And Ownership

Archetype is identity; rank is descriptive authored complexity; tier is numerical strength; encounter stage is placement. Tier must be an integer, not bool, and nonnegative, then supported by the archetype's authored policy. Tier changes must not add moves, heal, Defend, Super, or alter identity. Tier zero must reproduce current authored statistics and move outputs exactly unless an individual approved content change is separately recorded.

Enemy definitions own baseline stats/moves/capabilities and approved scaling/behavior identifiers. Encounter placement owns requested tiers and formations. `EnemyState` owns fresh current resources and instance stats; Battle/`CombatState` owns transient policy/phase state. Keep player and enemy Defend distinct; preserve current reductions/caps until an explicitly approved change. Do not apply player level/weapon-grade rules as enemy tiers.

AI chooses only legal affordable actions, with bounded, seeded/injected randomness and documented fallback. Healing requires the capability and a real supported move/target; Defend requires capability; empty legal sets have an explicit result rather than a loop or illegal free attack. Resistances/weaknesses use M3's component/mitigation order. Formation must affect an approved tactical rule, not just reorder names. An authored boss phase has explicit trigger, once-only transition, effect, and reset policy.

One selected environmental pressure must have visible warning and a real preparation counter from M2/M3 in M4A; M5 armor may supply additional counters in M4B. M4A must not depend on unfinished M5 equipment. Recommended levels/soft matchups do not deny entry solely for being underleveled. Story/floor unlocks and required-character conditions remain legitimate entry rules. Hub return still restores full HP/mana; injury/durability examples do not override that contract.

Rewards enter existing unsecured run state and secure only through the chosen exit rules. Resolve any probabilistic loot/search outcome once at an authoritative, approved event boundary; preserve enough per-outing outcome/claim evidence to prevent rerolls or duplicate grants through view rebuilds, repeat inputs, or Rest reloads. Global defeated-encounter history must not suppress legitimate replay rewards. Intuition affects approved chance/quality, not guaranteed rare loot.

## Content And Recruitment Handoffs

Before M4A coding, approve a finite Floor II manifest: route nodes/Rest and exit rules, at least one pressure/counter, encounter instances/tiers, D3 recruitment event, and completion condition. Before M4B, approve the equivalent bounded Floor III manifest with D4 before its final four-Drifter boss. Neither plan assumes ten battles/two rests for every floor or copies an unapproved recruitment cost.

Floor II introduces legitimate Grade-II Metal/Fiber/Timber/Core sources and sufficient weapon-specific component/recipe content to demonstrate the approved next-grade loop. Floor III similarly introduces Grade III in its readiness tranche. Reuse the sealed generic progression machinery; earlier floors must not yield these later grades. Select finite new enemies/kits only where the slice needs them. Exact encounters, scenes, costs, recruit choice/starting development, boss tuning, and phase/hazard choices are entry content decisions, not invented now.

D3/D4 are recruitment positions among the remaining canonical identities. Recruitment must work for all legal starting/companion choices, never duplicate an owned Drifter, and secure progress under M1's approved event rule. The Floor III boss uses all four; earlier ordinary encounters/bosses retain their legal active party. The meaning of "full boss XP for all four" needs an approved pool/per-member rule before M4B reward implementation.

The Floor III pre-boss event must explicitly transition from the ordinary pair to the four-member encounter, with no substitution during an active battle. M1's ordinary pair-selection restrictions remain intact. Preserve participant attribution for pre-boss rewards through this transition: approve either an appropriate security boundary or sufficient reward-cohort source state before coding, and never simply redivide all previously earned pair XP by four. Save/load and defeat/return must reconstruct the approved mode and payout correctly. This contract also becomes the M8 reunion-boss integration boundary.

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

- [ ] Resolve M4-D1 through D5 for M4A. Compare current archetype outputs and source-design wording; record any proposed change separately.
- [ ] Fix the approved reward/discovery RNG event and rollback model, supported tier policies, and first hazard counter. List required player/enemy action support.
- [ ] Freeze an executable bounded Floor II content manifest and D3 event without deciding the entire campaign.

Proof: every new capability, item/route reference, and formula has one owner and a testable rule; source examples not selected remain examples.

### Gate 1 - Numerical Tier And Definition Integrity (M4A)

- [ ] Add red/green cases in existing `test_enemy_content.py`, `test_enemy_state.py`, `test_m10_enemy_definitions.py`, and content-tool tests for tier-zero equivalence, supported positive tiers, bool/negative/unsupported rejection, and unchanged move/capability identity.
- [ ] Implement authored policies and encounter tier placement using real catalog creation. Two enemies made from one definition cannot share HP/mana/Super/status mutation.
- [ ] Reject duplicate/unknown policy/content IDs and invalid scaling parameters in content validation, not only at battle entry.

Proof: deterministic same-archetype scaling and instance isolation, with current Surface/Floor I golden cases unchanged.

### Gate 2 - Decisions, Resistance, Phase, And Hazard (M4A)

- [ ] Test permitted/forbidden heal/Defend/Super, affordable action sets, legal living targets, policy fallback, deterministic RNG, and no illegal phase-generated action. Use existing Battle/resolver/Defend tests plus focused policy cases.
- [ ] Implement the selected formation and phase contract with a real mechanical assertion, and the one approved hazard/counter. Prove phase transition triggers once and state resets between encounters.
- [ ] If no formation/phase is selected for M4A, record its approved M8 gate or explicit disposition instead of checking an unimplemented mechanic complete. The selected M4A hazard must still have a real M2/M3 counter.
- [ ] Verify invalid target, missing counter, or blocked action has the approved consequence without partial resource spending; unprepared low-level entry is not denied just for power level.

Proof: a prepared pair counters a real authored threat; merely rendering a formation label or phase heading is insufficient.

### Gate 3 - Reward/Discovery And Floor II Loop (M4A)

- [ ] Implement reward tables/discovery consumers, Floor II routing, D3 event, grade sources/recipes, and the approved Floor II completion gate through existing owners.
- [ ] Test once-only rolls/claims, visible items in pending rewards and secured inventory after return, loss on death, correct exit payouts, and inability to farm Grade II on Floor I. Verify item/recruitment events are safe under duplicate submits and reload.
- [ ] Complete a terminal and built-browser D1+D2 -> Floor II -> D3 -> return/save/reload flow, inspect all three, and select only legal recruited pairs under M1 policy.

Proof: focused flow/persistence/bridge tests, real content validation, browser journey, and shared M4A qualification. M5 may start after M4A is accepted; M4B remains explicitly open.

### Gate 4 - Floor III Readiness And Full-Party Boss (M4B, After M5)

- [ ] Revalidate M1-M5 interfaces and approve M4-D6/D7, the Floor III manifest, D4 scene, and full-party boss reward rule. Use M5 items/effects only through its accepted contract.
- [ ] Author the bounded Floor III path, legitimate Grade-III progression content, and D4 event. Four recruited members do not begin expedition assignments here.
- [ ] Extend party Battle/session/presentation tests for four living/defeated members, exact actor-owned moves/mana/Super/items, individual Dexterity ordering, mid-round reranking, target validity, party-wide mechanics only where authored, and victory/defeat when the original Drifter is down.
- [ ] Prove first four-Drifter boss reward allocation and once-only Floor III clear/story flags. No Rest/load path can duplicate D4 or bypass the boss to unlock expeditions.
- [ ] Test the authored pair-to-four encounter transition with pre-boss pending rewards. Earlier pair-earned XP must retain its approved recipients; wrong-phase transitions, mid-battle substitutions, failed saves and reload cannot change attribution or grant boss rewards twice.

Proof: ordinary semantic terminal and built-browser Floor III recruitment -> four-Drifter boss -> Hub save/reload journey. Structural fixtures alone do not close this gate.

### Gate 5 - Final M4 Qualification And M6 Readiness

- [ ] Extend the real probe for selected tier/policy/reward logic plus D3/D4/first full-party boss and teardown; keep historical route measurement ordering intact.
- [ ] Run shared cumulative qualification on the accepted M4B tree and record separate M4A/M4B evidence/SHA. Verify full roster recruited, Floor III boss complete, no live expedition, and readiness for the Floor IV unlock.

Closure: M4A enemy/Floor II and M4B Floor III proofs both pass; material/recruitment gates are real; first full-party boss is playable; no blanket four-person boss conversion or hidden permanent-injury system was introduced. M8 owns remaining approved region content.

## Unresolved Product Decisions

| ID | Decision and blocking gate |
| --- | --- |
| M4-D1 | Initial tier policies, allowed ranges, reward scaling versus tier; Gate 0 |
| M4-D2 | Resistance/weakness rules and bounded AI/target policies; before Gate 2 |
| M4-D3 | First tactical formation, boss phase and hazard/counter selections; before Gate 2 |
| M4-D4 | Discovery chance/quality formula, draw/claim persistence boundary and rare-drop limits; before Gate 3 |
| M4-D5 | Floor II route/exit/recruitment/boss manifest, D3 choice/cost/starting development; before Gate 3 |
| M4-D6 | Floor III manifest and D4 recruitment/starting development; M4B entry |
| M4-D7 | Four-member boss XP, pair-to-four participation boundary and pre-boss reward handling, selected party-wide targeting and defeat/clear rules; M4B entry |

Durability/persistent injuries remain unapproved optional M9 dispositions; no decision here silently selects them.

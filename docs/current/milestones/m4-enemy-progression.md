# M4 Enemy Progression And Dungeon Pressure Implementation Plan

> Implementation method: use `superpowers:executing-plans` for native gate-by-gate execution. This is a planning contract, not authorization to select every possible enemy or hazard mechanic.

**Status:** The original Gate 0 was approved on 2026-11-05. The M4 Floor II/III Boss Party Revision was approved on 2026-11-09 and its initial Floor II implementation was qualified on exact SHA `0aa4ecd5c15013af9c1456db8a53ada50e58357b` ([Actions run 42704099577](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42704099577)). It supersedes the original M4-D5/D6/D7 provisions on recruitment timing/level and boss XP. Three subsequent review corrections gate permanent D3/D4 recruitment on Floor II clear, restrict helper choice to the pre-boss Rest, and require an available D3/D4 helper before a Floor II replay. They are implemented in `10363110a8bf226a88dc871c70880f94f7727c19`, with the browser journey correction in `14286ecf63c8d7f4662271f7e0bc20e1399c1afc`; exact-SHA hosted qualification passed in [Actions run 42721683794](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42721683794). The pinned MicroPython matrix was also rerun on the corrected source tree. M4A is closed under the revised Floor II contract. M4B remains open for the Floor III implementation. See the updated [Floor II plan](m4-floor-ii-implementation.md) for the evidence and governing contract. The reported review baseline was `a64f4461c606dc88698fa45138d5f8a89a231868` on `dungeon`.

**Goal:** Deliver authored enemy scaling, bounded decision policies, reward/discovery integration, and meaningful counterplay, then prove staged recruitment through the first full-roster boss.

**Architecture:** Keep immutable archetype definitions distinct from fresh encounter instances and encounter placement. Extend existing content/catalog/Battle/session boundaries. M4 adds authored numerical tiers, identity-based resistance/weakness, persisted reward/search outcomes, and one telegraphed hazard. Enemy action/target selection remains bounded and unchanged. Formations and boss phases are deferred. Do not relocate packages to match an old design sketch.

**Tech stack:** Python content/enemy/combat/runtime, existing RNG injection and validation tooling, semantic clients, saves, pytest/Playwright and pinned runtime qualification.

## Authority, Dependencies, And Delivery Split

- [Enemy design](../../future/enemy-archetypes-scaling-and-capability-progression.md), archetype/rank/tier/capability separation and Defend contracts.
- [Economy](../../future/dungeon-progression-difficulty-and-economy.md), pressure, soft walls, rewards and death; [party design](../../future/party-and-expedition-core-loop.md), roster and convergence.
- [Roadmap](development-roadmap.md), M4 and fixed recruitment; [M2](m2-preparation-trading-escape.md) supplies and escape; [M3](m3-character-advancement.md) damage/potency/discovery contracts; [component names](../weapons/component.md).

**Approved delivery sequence:** **M4A** delivered enemy systems and the bounded Floor II route. Its approved party correction adds the pre-boss temporary helper, pair-only Floor II XP, and independent Level 1 Hub recruitment for D3/D4; the later recruitment-timing, Rest-only helper, and replay-eligibility corrections are hosted-qualified on the exact SHA recorded above. M4A is closed. M5 follows the original M4A baseline and is complete. **M4B** delivers the bounded Floor III route and first live four-Drifter boss using four permanent roster members, with shared four-way boss XP. M4 is fully closed only after M4B is qualified. M5 depends on the M4A enemy/Floor II baseline, not M4B; this avoids a circular dependency. M8 completes region depth and later content rather than postponing these prerequisite recruitment/boss proofs.

Non-goals: a new combat engine, every illustrative AI/hazard, persistent injuries/durability without approval, campaign-wide balancing, four-person ordinary Floor I battles, granting healing/Super by rank/tier, or expeditions before Floor IV.

## Historical Baseline At M4 Entry (Pre-M4A)

The observations below describe the repository before M4A and are retained for context; they are not claims about current capabilities. M4A is closed. Current remaining work is M4B's bounded Floor III route, Grade-III progression content, four-permanent-Drifter boss, and its cumulative qualification, tracked in Gates 4-5 below.

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

Floor II is ten combat encounters, one midway Rest after encounter 5, one pre-boss Rest after encounter 9, and a boss as encounter 10. It includes one telegraphed physical cave-in countered by existing Brace/Defend. It adds no status, injury, durability, formation, or boss-phase mechanic. The midway Rest does not recruit D3. At the pre-boss Rest, D3 and D4 offer help and the player selects one temporary helper for the Floor II boss only. The Floor III manifest uses the same bounded ten-encounter/two-Rest structure; D3/D4 are permanent Hub recruits rather than Floor III recruitment scenes.

Floor II introduces legitimate Grade-II Metal/Fiber/Timber/Core sources and enough material to exercise the already-authored Grade-II improvement recipes across all four slot families. Reuse the sealed generic weapon progression; do not create alternate components or alter the weapon schema. Floor III similarly introduces Grade III in M4B. Earlier floors must not yield later grades. Use existing enemy archetypes where practical; exact encounter compositions and per-archetype values are authored in the bounded floor content, not generalized into a new balance framework.

D3 and D4 are independently recruitable at the Hub for 65 secured shared gold each, but only after Floor II has been cleared, regardless of which one helped with the Floor II boss. Permanent recruitment starts at Level 1 with authored starting state. Insufficient funds reject atomically and remain retryable; preserve the established gold-earning/replay path so progression cannot softlock. Do not apply the previous permanent-recruit level catch-up rule.

For the Floor II boss, the battle party is the selected active pair plus exactly one temporary D3/D4 helper. The helper must be selected at the pre-boss Rest before continuing; do not offer a new selection at the boss node. Continue is unavailable until the choice is recorded. The helper matches the lower active Drifter's level, receives normal level-derived HP/Mana growth, and has catch-up GP distributed as evenly as possible across all six stats with deterministic remainder handling. Use the helper's authored kit/base signature weapon. Persist the selected helper across supported Rest save/reload, but never add them to the permanent roster or active IDs. The helper receives no XP and no carried-over progression. Floor II secured XP is split between the regular active pair, then each member receives their own M3 Intuition bonus.

For a Floor II replay after its first clear, the active pair must leave at least one of D3 or D4 outside the pair so a temporary helper is available. Block replay entry at the Hub before the outing begins and let the player change their pair there. This is Floor II-specific: D3 and D4 remain a legal active pair for Floor I and other content. Do not allow a two-member Floor II boss fallback.

The Floor III boss uses all four permanent roster members; D3 and D4 must be recruited before the boss, with the existing affordability/retry path preventing a softlock. M1's ordinary pair-selection restrictions remain intact; ordinary encounters continue to use two members. Pre-boss XP remains with its earning pair. On victory, split the authored Floor III boss XP across all four participants, then apply each Drifter's own M3 Intuition bonus independently. No free healing occurs at the party-size transition. The full-party battle targets any living party member under the existing random-target policy; defeat occurs only when all four are down. Save/load and defeat/return preserve the approved mode, payout, and one-time clear evidence. This contract also becomes the M8 reunion-boss integration boundary.

Discovery searches use authored base probabilities and the active Drifter selected to search. Apply that Drifter's existing `discovery_bonus_bps_from_intuition()` as a relative bonus to the authored base chance; never average party Intuition. The first Floor II source starts at 10%; common Grade-II material drops start at 20% per authored entry and Grade-II Core drops at 10%. These are conservative, editable content values, not locked balance. Resolve each search outcome when the search is confirmed and each enemy-drop outcome at encounter victory. Persist outcome identity/results with the run and apply reward changes atomically so reloads, repeated inputs, or view rebuilds cannot reroll or duplicate them. A failed search may be attempted on a later genuine run; a claimed permanent source remains globally one-time. Source reward type/amount remains authored under M3; no separate quality roll is added.

## Integration, Saves, And Clients

Expected areas: `root/src/app/content/enemy_spec.py`, `encounter_spec.py`, `route_spec.py`, `catalog.py`, authored content directories and generation/validation tools; `root/src/app/enemies/definition.py`/`state.py`; `root/src/app/combat/battle.py`, `resolver.py`, `combat_state.py`; current game route/session/story/world/party owners. Add cohesive policy/effect modules only when the selected mechanics need them. All exact APIs/new paths are revalidated at tranche entry.

Persist only source progression, route/recruitment/claim evidence, the selected Floor II helper identity, and pending outcomes required at supported checkpoints. The helper choice must survive Rest save/reload and be cleared or settled consistently at terminal run outcomes; do not persist temporary helper progression. Do not introduce arbitrary live-battle saves just to persist boss phases. Extend validators and schema migrations through the existing chain, preserving immutable remote history. Unsupported tier/content, corrupt references, or inconsistent roster/floor flags reject before reconstruction rather than silently downgrade. Revalidate current schema versions at implementation entry; do not preassign the next version.

Terminal/browser must show current actor, party resources, readable threat/phase/formation/resistance information at the approved knowledge level, hazard warnings, actual reward/drop outcomes, and blocked reasons. Both select actions/targets through the same presenter inputs. No browser-side AI, damage, drop rolls, or phase scripts.

## Review Focus

- A numerical tier must not grant moves or capabilities; Gate 1 checks tier-zero equivalence and positive-tier identity.
- Reusing an archetype must not share HP/mana/status across instances; Gate 1 checks independent mutation.
- A view rebuild/Rest reload must not reroll loot, while a genuine replay still earns eligible rewards; Gate 3 checks outcome identity.
- A selected Floor II helper must not duplicate an active Drifter, mutate the permanent roster/active pair, or receive XP; Gate 3 checks battle composition, save/reload, and pair-only reward attribution.
- D3/D4 Hub recruitment must be independent, Level 1, 65 gold each, and retryable without partial mutation; Gate 3 checks each candidate and insufficient funds.
- Recruitment and floor flags must not unlock the four-member Floor III boss before four permanent members exist or expeditions before the boss; Gates 3/4/5 check staged progression.
- A four-member boss must not end when only the original Drifter falls or misallocate shared XP/resources; Gate 4 checks all live actors and four-way XP plus individual Intuition.

## Gates And Tests

### Gate 0 - Approve The Initial Policies And Floor II Manifest

- [x] Approve and record M4-D1 through D5 for M4A and M4-D6/D7 in advance for M4B. M4B revalidates code interfaces after M5, not product decisions.
- [x] Approve supported tier policies, identity resistance/weakness, unchanged bounded enemy action/target selection, reward/search event boundaries, discovery Intuition, and the single cave-in/Brace/Defend counter.
- [x] Freeze the bounded Floor II route, Grade-II material families, and Floor II clear gate under the original contract.
- [x] Apply and record the 2026-11-09 boss-party revision: pre-boss D3/D4 temporary helper choice, no helper XP/carry-over, 65-gold Level 1 Hub recruitment for each, pair-only Floor II XP, and four-way shared Floor III boss XP.

Proof: original M4-D1 through D7 are recorded below, with D5-D7 updated to the current governing contract. The prior M4A implementation remains historical evidence only for behavior not changed by the revision. Unselected source examples remain examples.

### Gate 1 - Numerical Tier And Definition Integrity (M4A)

- [x] Add red/green cases in existing `test_enemy_content.py`, `test_enemy_state.py`, `test_m10_enemy_definitions.py`, and content-tool tests for tier-zero equivalence, supported positive tiers, bool/negative/unsupported rejection, and unchanged move/capability identity.
- [x] Implement authored policies and encounter tier placement using real catalog creation. Two enemies made from one definition cannot share HP/mana/Super/status mutation.
- [x] Reject duplicate/unknown policy/content IDs and invalid scaling parameters in content validation, not only at battle entry.

Proof: deterministic same-archetype scaling and instance isolation, with current Surface/Floor I golden cases unchanged.

### Gate 2 - Resistance And Hazard (M4A)

- [x] Preserve and test the existing random legal-affordable move and random living-active-target behavior; tier does not grant capabilities or moves.
- [x] Implement and test approved elemental/alchemical identity resistance/weakness at the documented position in the M3 component pipeline; no immunity or new defense stat.
- [x] Implement the one telegraphed physical cave-in and its existing Brace/Defend counter. Prove warning, response window, mitigation, and no mutation on rejected/blocked actions.
- [x] Defer formations and boss phases; they are not M4A or M4B deliverables.
- [x] Verify invalid target, missing counter, or blocked action has the approved consequence without partial resource spending; unprepared low-level entry is not denied just for power level.

Proof: a prepared pair can identify and counter the authored Floor II threat; elemental/alchemical identity changes only the approved damage component multiplier.

### Gate 3 - Reward/Discovery And Floor II Loop (M4A)

- [x] Original authored reward/drop tables, discovery consumer, Floor II route, Grade-II sources, and Floor II clear gate are qualified on the historical M4A baseline.
- [x] Replace the old midway D3 recruitment with the pre-boss temporary helper choice and independent Level 1 Hub recruitment for D3/D4.
- [x] Prove exact three-member Floor II boss composition; helper selection persistence; no duplicate IDs, roster mutation, XP, or progression carry-over; pair-only XP split followed by individual Intuition bonuses; independent recruitment costs/retries; and unchanged two-member ordinary encounters with focused session/terminal tests.
- [x] Re-run the terminal Floor II journey after the correction, alongside the existing search/reward/death/extraction and Grade-II protections.
- [x] Run the built-browser Floor II journey after the correction, including helper save/reload, three-member boss participation, pair-only XP, and Hub recruitment.

Proof: focused flow/persistence/bridge tests, real content validation, revised browser journey, and cumulative qualification for the correction. Do not treat the historical M4A run as qualification for this revision.

### Gate 4 - Floor III Readiness And Full-Party Boss (M4B, After M5)

- [ ] Revalidate M1-M5 interfaces and implement the bounded Floor III path and legitimate Grade-III progression content. D3 and D4 are recruited at the Hub for 65 gold each and start at Level 1; do not add the superseded D4 pre-boss recruitment event or permanent catch-up logic.
- [ ] Ensure four permanent roster members are present before the four-member boss, with the approved affordability/replay path preventing a softlock. Four recruited members do not begin expedition assignments here.
- [ ] Extend party Battle/session/presentation tests for four living/defeated members, exact actor-owned moves/mana/Super/items, individual Dexterity ordering, mid-round reranking, target validity, party-wide mechanics only where authored, and victory/defeat when the original Drifter is down.
- [ ] Prove Floor III boss XP is split across all four members, followed by independent personal Intuition bonuses, and prove once-only Floor III clear/story flags. No Rest/load path can duplicate recruitment or bypass the boss to unlock expeditions.
- [ ] Test the authored pair-to-four encounter transition with pre-boss pending rewards. Earlier pair-earned XP must retain its approved recipients; wrong-phase transitions, mid-battle substitutions, failed saves and reload cannot change attribution or grant boss rewards twice.

Proof: ordinary semantic terminal and built-browser Hub recruitment -> Floor III route -> four-permanent-Drifter boss -> Hub save/reload journey. Structural fixtures alone do not close this gate.

### Gate 5 - Final M4 Qualification And M6 Readiness

- [ ] Extend the real probe for selected tier/policy/reward logic plus D3/D4/first full-party boss and teardown; keep historical route measurement ordering intact.
- [ ] Run shared cumulative qualification on the accepted M4B tree and record separate M4A/M4B evidence/SHA. Verify full roster recruited, Floor III boss complete, no live expedition, and readiness for the Floor IV unlock.

Closure: M4A enemy/Floor II and M4B Floor III proofs both pass; material/recruitment gates are real; first full-party boss is playable; no blanket four-person boss conversion or hidden permanent-injury system was introduced. M8 owns remaining approved region content.

## Approved Product Decisions

All M4-D1 through M4-D4 and the revised M4-D5 through M4-D7 product decisions are approved. The initial Floor II party revision and its subsequent review corrections are hosted-qualified on their recorded exact SHAs; the final corrected tree also passed the pinned MicroPython matrix. M4A is closed. M4B implementation remains sequenced after M4A and M5; integration details are revalidated at entry.

| ID | Approved decision |
| --- | --- |
| M4-D1 | Tier 0 remains exactly compatible. Floor II uses authored Tier 1 values; Floor III uses authored Tier 2 values; Tier 3 is deferred. Numeric scaling and rewards are authored per archetype; tier does not automatically scale rewards or add moves/capabilities. Values are initial and tunable. |
| M4-D2 | Keep the current legal-affordable random move selection and random living-active-target policy. Elemental/alchemical identities may be resisted or weakened by 25% after generic mitigation and before Brace/Defend. No immunities, new defense stats, or change to physical/magical mitigation. |
| M4-D3 | Use one visibly telegraphed physical cave-in pressure on Floor II, countered through existing Brace/Defend. Do not add status effects, injuries, durability, formations, or boss phases. Formations and phases remain deferred. |
| M4-D4 | Author conservative discovery base probabilities and apply the selected searching active Drifter's existing Intuition discovery bonus as a relative chance bonus. Do not average party Intuition. Initial tunable values: 10% for the first Floor II discovery source, 20% per authored common Grade-II material drop entry, and 10% per Grade-II Core drop entry. Resolve search on confirmation and drops at encounter victory; persist outcomes to prevent reload/input rerolls or duplicate awards. A later genuine run may retry a failed search; a claimed source stays one-time. Source reward amounts remain authored by M3; no new quality roll or guaranteed rare drop. |
| M4-D5 (revised 2026-11-09) | Floor II is ten battles with a midway Rest after battle 5, a pre-boss Rest after battle 9, and the boss at battle 10. The midway Rest does not recruit D3. At the pre-boss Rest, the player chooses D3 or D4 as a temporary helper for the Floor II boss only and must record that choice before continuing; never prompt at the boss node. The boss has the regular active pair plus that helper. The helper matches the lower active level, gets normal level-derived HP/Mana growth, and has catch-up GP distributed as evenly as possible across six stats with deterministic remainder handling. Persist the helper choice across supported Rest save/reload; do not mutate the permanent roster/active pair, grant XP, or carry progression. Floor II secured XP is shared by the regular active pair, then each receives their personal Intuition bonus. After returning to the Hub following Floor II clear, D3 and D4 are independently recruitable for 65 secured shared gold each, regardless of helper choice. Each permanent recruit starts at Level 1. Insufficient funds leave state unchanged and retryable; preserve existing progression/gold paths. On Floor II replays only, require an active pair that leaves at least one of D3/D4 available; block entry at the Hub before the outing starts, while preserving D3+D4 pair selection for all other content. Floor II introduces Grade-II Metal, Fiber, Timber, and Cores; Floor I remains unchanged. |
| M4-D6 (revised 2026-11-09) | Floor III follows the bounded ten-battle/two-Rest scaffold and introduces Grade III materials. D3 and D4 are permanent Hub recruits for 65 secured shared gold each and start at Level 1; do not add permanent catch-up progression or a D4 pre-boss recruitment event. The four-member boss requires all four permanent roster members; preserve the affordability/replay path so this cannot softlock progression. Implement after M4A and M5 are closed, and revalidate M1-M5 interfaces at M4B entry. |
| M4-D7 (revised 2026-11-09) | The Floor III final boss uses all four permanent Drifters. Pre-boss XP remains attributed to its earning pair. On boss victory, split the authored boss XP across the four participants, then apply each Drifter's own Intuition bonus independently; do not grant full per-member XP. No free healing at transition; enemy targets are random among living members; defeat requires all four down. Only boss clear unlocks Floor IV/expeditions. |

Durability/persistent injuries remain unapproved optional M9 dispositions; no decision here silently selects them.

The initial 2026-11-09 Floor II revision is implemented and qualified on exact SHA `0aa4ecd5c15013af9c1456db8a53ada50e58357b`; the subsequent review corrections are qualified on exact SHA `14286ecf63c8d7f4662271f7e0bc20e1399c1afc` in [Actions run 42721683794](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42721683794), with the pinned MicroPython matrix rerun on that source tree. M4A is closed. The Floor III portion remains planned, not implemented. The previous M4A midway D3 recruitment, permanent recruitment catch-up, Floor III D4 pre-boss recruitment, and full per-member Floor III boss XP wording are superseded and must not be preserved as current requirements. Historical implementation/CI evidence remains valid only for behavior unaffected by this revision.

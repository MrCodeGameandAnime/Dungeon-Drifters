# M8 Region, Story, And Content Loop Implementation Plan

> Implementation method: use `superpowers:executing-plans` for native gate-by-gate execution. Approve a finite release manifest before authoring content; the source examples do not define a whole campaign automatically.

**Status:** Gate 0 audit and ten-package decomposition proposal; M8-D1 through M8-D6 remain pending review. No M8 gameplay work is authorized by this document or its child plans.

**Audit baseline:** `dungeon` at `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc` (2026-11-18). The worktree was clean at audit start. Runtime and disk save schema are both 25. This entry audit supersedes the October 2026 baseline text retained in older sections of this plan.

**Goal:** Integrate the delivered systems into a complete, finite region progression loop with meaningful information, party restrictions, story/pair outcomes, later-floor rewards, and later full-roster convergence where authored.

**Architecture:** Extend existing authored route/encounter/content and story/world/game source state. Use accepted roster, reward, advancement, equipment and expedition services. Clients render legal story/dungeon choices and results without owning unlocks or generating campaign rewards.

**Tech stack:** Current Python content/runtime/persistence/presentation stack and client/tooling contracts as revalidated at entry; no new backend or graphical engine is implied.

## Authority And Dependencies

- [Roadmap](development-roadmap.md), M8, fixed pacing and common qualification contract.
- [Party design](../../future/party-and-expedition-core-loop.md), dungeon knowledge/restrictions, pair identity, reunion/boss/post-boss loop.
- [Economy](../../future/dungeon-progression-difficulty-and-economy.md), pressure, secure/loss rules, preparation, trader/expedition roles and quest protections.
- [Enemy design](../../future/enemy-archetypes-scaling-and-capability-progression.md), selected formations/phases/visuals and placement versus tier.
- [Character growth](../../future/character-growth-and-stat-scaling.md), permanent discoveries and passive/move prerequisites.
- [Armor](../../future/armor.md), viable owned rewards; [component catalog](../weapons/component.md) and [weapon design](../weapons/signature-weapon-progression.md), Grade I-IV/floor boundaries.
- [M1-M7](development-roadmap.md) and [M6.5](m6-5-hub-vendors.md) are implemented and sealed in the inspected tree. M8 must preserve their current contracts, including M7 Momentum, M6.5 vendor/profession state, and M6's completed-floor/passive-expedition rules. M4 delivers Floor II/III, staged D3/D4 recruitment, and the first four-permanent-Drifter boss; M8 proposes extending those systems rather than treating them as future work.

Non-goals: defining an unlimited campaign, reimplementing systems, redoing canonical first recruitment, forcing four-member parties into every boss, adopting every possible pair/combo/relationship mechanic, full graphical combat, payment integration, `longterm.md`, or executable packaging.

## Entry Baseline And Finite Scope

The October `8099b895` baseline paragraph is historical and incorrect for M8 entry. At the audited baseline, Surface and Floors I-III are live, M1-M7 and M6.5 are present, runtime/disk schema is 25, and the route/content catalog contains 4 routes, 48 route nodes, 11 encounter definitions, 5 enemy archetypes, 4 Drifters, 3 recruitment-event definitions, and 1 active permanent-discovery source. The audited source files and resulting gaps are recorded below. No claim of whole-campaign completion is made.

Gate 0 must approve a finite set of named destinations, routes, encounters, bosses, story events, discoveries, rewards, expedition consumers, component recipes, and assets. The proposal below gives each item a stable proposed ID, prerequisite, owner, effect, unlock path, and proof journey. Names drawn from future-design examples remain proposals until M8-D1 is approved.

The recommendations deliberately bound M8 to the proposed Floors IV-V content below. They do not introduce a Floor VI, an unlimited campaign, a new combat renderer, or speculative APIs/schema numbers. Gate 0 remains open until the user reviews M8-D1 through M8-D6.

**Proposed finite inventory:** 2 destinations, 3 routes, 20 route nodes, 17 encounters (15 ordinary plus 2 bosses), 4 ordinary archetypes plus 2 bosses, 13 story-event/scene IDs, 4 knowledge-fact IDs, 3 permanent-discovery sources, 9 ordinary/first-clear reward sources, 7 expedition consumers, 48 component recipes, and 8 static assets. Counts describe this proposal; any approved reduction must remove dependent rows and graph edges as well.

## Entry Audit At `29bab31`

The following is an inspection of the current tree, cross-checked against the sealed milestone records. It is not a new qualification run for every prior milestone.

### Revalidated Milestone State

| Work | Present in the audited tree | M8 boundary to preserve |
| --- | --- | --- |
| M1 roster | Four permanent Drifter identities, explicit recruited roster and ordered active pair; current roster restrictions and persistence are live. | Ordinary outings remain two-person. Never infer identity from slot order or silently swap a member. |
| M2 preparation/trading/escape | Secured Hub storage, six-unit carried pack, supplies, Alchemy recipes, Smoke Bomb and Return Talisman exits are live. | Preserve death, Rest, boss, talisman and supply-return semantics. No M8 reward may bypass pack or transaction ownership. |
| M3 advancement | Per-Drifter GP, 24-skill authored trees, loadouts, split-damage effects, per-member secured-XP Intuition bonuses, respec, and permanent-discovery claim service are present. | New discovery sources must use the one-time source ID and active-party target contract. Do not modify pricing, unlocks, or reward ordering. |
| M4 | Floors II and III, enemy tiers 0-2, resistance/weakness hooks, discovery/drop event boundaries, the temporary Floor II helper, post-Floor-II Hub recruitment, and the four-permanent-member Floor III boss are live. | Floor II XP belongs to the original pair; Floor III boss XP is split among four then individually Intuition-adjusted. D3/D4 remain Level 1 permanent recruits. |
| M5 | Armor instances, rarity/stat upgrades, modifiers, extraction, affixes, ownership and destructive transactions are live. | M5 explicitly has no ordinary route armor reward source; `resolve_armor_reward()` is a Floor-II-only persisted service, not connected to a live route victory. |
| M6 | 100-energy clock, passive 20-minute assignments, completed-floor destinations I-III, Training/Material assignments and exactly-once reports are live. | Equipment/Recovery are unavailable on I-III; Scouting/Story/Elite are not implemented. Current outing launch permits Floors I-II only and blocks Floor III. |
| M6.5 | Four vendor interfaces, finite stock, future-sale stock, component stacks, Alchemy/Enchanting progression and permanent affix knowledge are live. | Grade-IV Magic Crystal is reserved for Floor IV; Grade-V has no item/source/offer. Vendor floor-clear validation currently treats Floor IV as false. Preserve M6.5 transaction rules. |
| M7 | Shared encounter Momentum, symmetric critical/damage/mitigation bonuses, DoT attribution, and terminal/browser projections are implemented; Momentum is transient and not saved. | Preserve the approved Gate 0 arithmetic and presentation contract. New enemies and split attacks use the same resolver; no per-enemy Momentum state. |

The milestone plans record sealed qualification for these systems. M7's latest implementation SHA is `e0616fe998319c430586ec72cee94dd8db2deb3c`, hosted run [44341214070](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/44341214070). M6.5's sealed implementation SHA is `92b2968e2acf2ba6d4f188ccd2c362fff33059ce`, hosted run [43737762509](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/43737762509). These are historical evidence cited by their owning plans, not new M8 qualification.

### Live Content Inventory

| Area | Current authored content |
| --- | --- |
| Routes | `surface`, `floor_one`, `floor_two`, `floor_three`; each has 12 ordered nodes. The three dungeon floors each have 9 ordinary combat nodes, midpoint Rest, pre-boss Rest, and a 10th boss battle. |
| Encounter catalog | 11 definitions: Goblin solo/pair/trio/quad; Warrior solo/pair; Shaman solo/pair; Elite patrol; Floor-II cave-in; Goblin Lord. Floors II-III mostly reuse these definitions with tier 1/2 stats and drops. |
| Enemy archetypes | `goblin`, `goblin_warrior`, `goblin_shaman`, `goblin_elite`, `goblin_lord`. All currently support tiers 0, 1 and 2; no tier-3 profile or authored resistance/weakness value is present. The Goblin Lord encounter is reused as the boss on Surface and Floors I-III. |
| Reward sources | Floor I dismantling and boss core; Floor II tier-1 material drops and first-clear rewards; Floor III tier-2 drops and first-clear rewards. `vendor_catalog.py` authors Grade-I/II/III Crystal first-clear awards, a Floor-II Mythril Plate award, and no Floor-IV reward yet. No ordinary live armor, Healing Potion, Mana Potion, Smoke Bomb or Return Talisman route drop exists on Floors I-III. |
| Discoveries | `ancient_well_floor2_01` is the only active permanent-discovery source: Ancient Well, +5 max HP, 1,000 bps base search chance at `floor_two_pre_boss_rest`. A retired Floor-I source ID remains recognized for historical evidence. M3 also supports +5/+10 HP, +5/+10 Mana and +3 GP authored sources. |
| Roster and story | Three recruitment definitions exist; the live handler supports the tutorial D2 event and post-Floor-II D3/D4 Hub event. The old `floor_two_d3_recruitment` definition is not a live path. `StoryState` stores generic flags, completed event IDs and decisions; it is not a story-script/requirements engine or relationship-score system. `WorldState` stores generic discovered/opened/consumed evidence. |
| Expeditions | Training and Material are the only available categories. Destinations are hard-coded to completed Floors I-III. The current report shape supports XP and one stackable-item result, not story flags, knowledge facts, or unique equipment instances. |
| Weapon components | Four weapons, four slots each, four starting components and four Grade-I craftable components per weapon. Grade II/III materials drop on Floors II/III, but there are no Grade II/III component recipes or live Grade-IV component sources. M6.5 now owns shared stacks, purchases, sales and replacement recovery; do not revert to the older direct-only ownership model. |
| Client assets | `root/res/` has the four Drifter sprites, logo/hero art, screenshots and UI icons. No region backgrounds or enemy portraits are present. Browser gameplay remains a renderer/input adapter over Python. |

### Reusable Services And Demonstrated Gaps

| Concern | Reusable current owner | Entry gap / implementation implication |
| --- | --- | --- |
| Route content | `RouteSpec`, generated catalog, `OverworldState` immediate-successor checks | Routes are linear; node kinds are Combat, Rest, Boss and Dungeon Entrance. Route starts, floor labels and save validation explicitly enumerate I-III. Branching or new story-node types require a deliberate content/session contract. |
| Clear/unlock state | `PartyState` and `save_document.py` | Authoritative clear flags/run counters exist only for I-III. Current save validators and migrations have no IV/V clear contract; schema change and legacy defaults must be planned, not preassigned. |
| Enemy and drop content | `EnemySpec`, `EncounterSpec`, `EnemyTierSpec`, generated catalog, `RunEventService` | Tier 3 is not present. Tier is numeric strength only; new capabilities/moves need explicit archetype content. M7 applies to all resolved damage. |
| Permanent discoveries | `PermanentDiscoveryService`, `RunEventService.search_discovery`, active searcher Intuition, `WorldState`/party claim evidence | The atomic target/claim service is reusable. Only one active source is authored. New sources must be linked to route nodes and deterministic persisted search outcomes. |
| Expedition lifecycle | `ExpeditionService`, `ExpeditionState`, report claim transaction | Current allowlists and report validation are closed over I-III and Training/Material. New categories need frozen outcomes in reports and atomic exactly-once claim effects. Equipment cannot be represented by current `reward_item_id`/quantity report fields. |
| Armor reward | `ArmorGenerationService`, `EquipmentInstance`, `RunEventService.resolve_armor_reward` | Generation and immutable reward-event evidence exist, but the run-event caller is Floor-II-only and ordinary route victories do not call it. A live M8 source needs an audited floor-general reward boundary and an expedition equipment snapshot contract. |
| Components | `WeaponProgressionService`, M6.5 Blacksmith/component stack transactions | Existing progression and current-slot checks must remain. M8 authors recipes/material sources; it does not add a lifetime craft limit or alter installed effects. |
| Story/knowledge | `StoryState`, `WorldState`, session/presenter and save-document validation | Generic typed containers are reusable, but no authored knowledge catalog, visibility projection, story requirement evaluator, or pair-event content exists. Do not duplicate eligibility logic in JavaScript. |
| Persistence | `GameState`/`PartyState` snapshots, disk schema 25, `SaveCoordinator`, immutable profile history | New clear flags, report evidence, route state or quest-source claims require one canonical owner and a migration from schema 25. Legacy data must default to “not cleared/not discovered”; remote historical payloads remain immutable. |

The future enemy-design document's statement that current archetypes only accept tier 0 is stale relative to M4. The live source and M4 contract above are authoritative; the future design remains useful for the separation of archetype, rank, tier and encounter stage. No unrelated future document is rewritten by this audit.

## Proposed Finite M8 Manifest (Pending M8-D1)

Every row in this section is a proposal, not implemented content or an approved product decision. The IDs are reserved here as stable recommendations so they can be accepted or edited explicitly. Names `Drowned Reliquary` and `Ashen Vault` are examples in the future designs; this proposal selects them only for review.

### Destinations And Routes

| Proposed ID | Prerequisite | Owner | Effect / unlock | Proof journey |
| --- | --- | --- | --- | --- |
| Destination `drowned_reliquary` / floor ID `floor_four` | Floor III clear and all four permanent Drifters recruited; no hard level gate. Any legal active pair. | Destination/content catalog, `PartyState` clear progression, Hub/session projection. | Opens the Floor-IV paired route. On its boss clear, enables Floor-IV expedition destination and reveals `ashen_vault`. | Complete M8 prelude, select each pair in focused eligibility tests, start/return/reload, and verify only the Floor-IV clear unlocks the next destination. |
| Route `floor_four` | `drowned_reliquary` unlocked. | Authored route catalog and existing route/session/save owners. | 12 nodes matching the established floor cadence: 9 ordinary encounters, midpoint Rest, pre-boss Rest, paired boss. Victory records Floor IV clear once. | Full terminal/browser Floor-IV route, Rest checkpoint reload, boss retry/clear idempotency and first-clear reward comparison. |
| Destination `ashen_vault` / floor ID `floor_five` | Floor IV boss clear. | Destination/content catalog and Hub/session projection. | Opens the paired approach route. Floor-V expedition eligibility follows its own completion event, not mere discovery. | Verify blocked before Floor IV clear, available afterward, and remains available through reload. |
| Route `floor_five_approach` | `ashen_vault` discovered; any legal active pair. | Authored route catalog and existing route/session/save owners. | 7 nodes: 6 ordinary encounters and one Rest; the final route outcome reveals the reunion arena and returns the outing through normal settlement. | Complete with and without an active compatible expedition; compare settlement, route evidence and exact unlocked arena state after reload. |
| Route `floor_five_reunion` | Approach outcome `m8_ashen_arena_revealed`; all four permanent Drifters; no active expedition assignment. | Existing four-member `Battle`/M4B participant and reward contracts, with M8 entry orchestration. | One standalone four-member boss encounter launched from Hub; completion records Floor V clear once and returns to Hub/two-plus-two deployment. No mid-run insertion or dual expedition deployment. | Start blocked while any assignment is active; end outing and settle it, then launch all four; test victory, defeat, reload, retry and one-time reward. |

#### Route Node IDs

The following node IDs are proposed and stable within this manifest. Combat node IDs map one-to-one to the encounter rows below; Rest and return nodes have no independent reward roll.

| Route | Ordered node IDs | Prerequisite / effect / proof |
| --- | --- | --- |
| `floor_four` | `floor_four_battle_01`, `floor_four_battle_02`, `floor_four_battle_03`, `floor_four_battle_04`, `floor_four_battle_05`, `floor_four_rest_midpoint`, `floor_four_battle_06`, `floor_four_battle_07`, `floor_four_battle_08`, `floor_four_battle_09`, `floor_four_rest_pre_boss`, `floor_four_battle_10` | Requires `drowned_reliquary` unlocked and a legal active pair. Node owner is the route/session state; victory advances once, Rest uses the existing checkpoint rules. Proof: linear reachability, every Rest reload, stale-node rejection, and boss-clear retry. |
| `floor_five_approach` | `floor_five_battle_01`, `floor_five_battle_02`, `floor_five_battle_03`, `floor_five_rest_midpoint`, `floor_five_battle_04`, `floor_five_battle_05`, `floor_five_battle_06` | Requires `ashen_vault` unlocked and a legal active pair. Final genuine victory records `m8_ashen_arena_revealed`; defeat, extraction, or failed save does not. Proof: each terminal outcome and reload state. |
| `floor_five_reunion` | `floor_five_reunion_battle_01` | Requires arena reveal, all four permanent recruits, and no active expedition assignment. Genuine victory records Floor V completion once. Proof: illegal-entry matrix, four-member win/defeat, failed-write retry, and return to pair selection. |

The two floors are the recommended M8 finite scope. No Floor VI route is included. M8 closure returns the roster to the Hub with Floors IV/V available for the normal two-plus-two loop; any later destination requires its own approved content scope.

### Encounter And Boss IDs

The proposed new archetypes are `reliquary_sentinel`, `brine_oracle`, `drowned_stalker`, and `ashbound_hound`, plus bosses `tidebound_curator` and `ashen_regent`. Their authored values, supported tier-3 profiles, moves, weaknesses, and drops are content work for Gate 2; the IDs do not authorize a new combat mechanic. All ordinary encounters use two combatants on the Drifter side. The Floor-IV boss uses the existing two-member boss contract; only `ashen_regent` uses all four permanent Drifters.

| Archetype ID | First authored use | Owner | Proposed role/effect | Unlock and proof |
| --- | --- | --- | --- | --- |
| `reliquary_sentinel` | Floor-IV battle 1 | Enemy catalog / tier profile | Durable physical frontliner; no new status mechanic. | Floor IV unlock; defeat, mitigation and drop-boundary tests. |
| `brine_oracle` | Floor-IV battle 2 | Enemy catalog / tier profile | Magical ranged pressure; reuses current magical damage/status support only. | Floor IV unlock; authored move and M7 symmetry proof. |
| `drowned_stalker` | Floor-IV battle 1 | Enemy catalog / tier profile | Fast physical pressure; no new turn-order subsystem. | Floor IV unlock; target/turn and independent instance tests. |
| `ashbound_hound` | Floor-IV battle 5 | Enemy catalog / tier profile | Aggressive physical attacker reused in the Ashen approach. | Floor IV unlock; Floor-IV/ V grade provenance tests. |
| `tidebound_curator` | Floor-IV boss | Boss enemy catalog / encounter owner | Paired boss, no phases in this proposal. | Floor IV route end; pair XP, clear and first-reward idempotency. |
| `ashen_regent` | Floor-V reunion boss | Boss enemy catalog / four-member encounter owner | Four-member reunion boss, no phases in this proposal. | Arena reveal and settled assignment; all-four payout/clear proof. |

| Encounter ID | Route node / proposed composition | Prerequisite, owner and effect | Unlock / proof |
| --- | --- | --- | --- |
| `m8_floor_four_encounter_01` | `floor_four_battle_01`: sentinel + stalker | Floor IV open; `EncounterSpec`/enemy catalog; first ordinary combat, Grade-IV source eligibility. | Route order; record actual victory/drop once and verify after Rest reload. |
| `m8_floor_four_encounter_02` | `floor_four_battle_02`: oracle + stalker | Same Floor-IV paired route; introduces the authored magical archetype. | Immediate successor; terminal/browser semantic combat proof. |
| `m8_floor_four_encounter_03` | `floor_four_battle_03`: two sentinels | Same route; repeat archetype instances remain independent. | Immediate successor; prove separate HP/status and no duplicate drop on retry. |
| `m8_floor_four_encounter_04` | `floor_four_battle_04`: oracle + sentinel | Same route; first mixed encounter. | Immediate successor; record M7 Momentum and reward evidence. |
| `m8_floor_four_encounter_05` | `floor_four_battle_05`: hound + stalker | Same route; introduces fast physical threat. | Immediate successor; prove source-grade and client projections. |
| `m8_floor_four_encounter_06` | `floor_four_battle_06`: sentinel + oracle | Same route; common enemy pairing. | Immediate successor; save/reload and deterministic replay proof. |
| `m8_floor_four_encounter_07` | `floor_four_battle_07`: two stalkers + oracle | Same route; three-enemy composition. | Immediate successor; full encounter evidence and pair-only XP. |
| `m8_floor_four_encounter_08` | `floor_four_battle_08`: sentinel + hound + oracle | Same route; eligible armor/recovery source event proposed here. | Immediate successor; prove one source outcome, owned item and replay idempotency. |
| `m8_floor_four_encounter_09` | `floor_four_battle_09`: two oracles + stalker | Same route; final ordinary encounter before Rest/boss. | Immediate successor; save at pre-boss Rest and resume without reroll. |
| `m8_tidebound_curator_boss` | `floor_four_battle_10`: Curator + sentinel | Requires Floor-IV route and existing two-member boss flow; no new phases. | Floor-IV clear unlocks Ashen Vault; prove pair-only payout and clear reward once. |
| `m8_floor_five_encounter_01` | `floor_five_battle_01`: hound + stalker | Floor V open; paired approach route. | Route order; prove ordinary two-member combat and M7 projection. |
| `m8_floor_five_encounter_02` | `floor_five_battle_02`: oracle + hound | Same approach route; reuse authored archetypes without shared mutable state. | Immediate successor; save/reload and independent-instance regression. |
| `m8_floor_five_encounter_03` | `floor_five_battle_03`: two sentinels | Same approach route; eligible search/recovery source proposal. | Immediate successor; source result persists and does not duplicate. |
| `m8_floor_five_encounter_04` | `floor_five_battle_04`: two hounds | Same approach route; fast-pressure composition. | Immediate successor; route and rewards remain deterministic. |
| `m8_floor_five_encounter_05` | `floor_five_battle_05`: sentinel + oracle + stalker | Same approach route; mixed formation. | Immediate successor; client parity and exact drop evidence. |
| `m8_floor_five_encounter_06` | `floor_five_battle_06`: two oracles + hound | Same approach route; arena-reveal trigger occurs after genuine victory. | Route end creates `m8_ashen_arena_revealed`; test non-victory cannot unlock it. |
| `m8_ashen_regent_boss` | `floor_five_reunion_battle_01`: Regent + oracle | Four permanent Drifters; assignment must be settled, not necessarily its report claimed. | Hub-launched reunion route; one clear, one payout, then normal active-pair selection. |

The route/node IDs above are proposed IDs in addition to the encounter IDs. Gate 2 may tune compositions and numerical values, but must not silently add encounter count or alter the selected 2+2-to-four deployment boundary.

### Story, Pair, And Knowledge Events

| Proposed ID | Prerequisite | Owner | Effect / unlock path | Proof journey |
| --- | --- | --- | --- | --- |
| `m8_drowned_reliquary_briefing` | Floor III clear and four recruits | Hub story event + `StoryState`/knowledge facts | Adds a Rumored fact for `drowned_reliquary`; exposes the destination without exposing unlearned enemy/weakness details. | New game and migrated save; verify exact fact visibility and no early recruitment or route start. |
| `m8_pair_scene_branoc_azhvielle`, `m8_pair_scene_branoc_joruun`, `m8_pair_scene_branoc_zhaivra`, `m8_pair_scene_azhvielle_joruun`, `m8_pair_scene_azhvielle_zhaivra`, `m8_pair_scene_joruun_zhaivra` | Pair present at `floor_four_rest_midpoint` | Pair-scene content keyed by sorted permanent Drifter IDs; generic `StoryState` event/decision evidence | One finite dialogue variant for each of six legal pairs; records completion, no numeric relationship meter and no combat bonus in this proposal. | Table-driven test across all six permutations/reversed active order; replay shows no duplicate effect. |
| `m8_azh_archive_memory` | Floor IV reached and Azhvielle is in the active pair at `floor_four_rest_midpoint` | Optional Rest/story interaction | Reveals the proposed `m8_fact_ashen_regent` and a story scene; does not block Floor IV/V access or replace a member automatically. | Reject when Azhvielle is benched; repeat later with her active and verify exact fact/event persistence. |
| `m8_ashen_arena_revealed` | Genuine victory at `floor_five_battle_06` | Route completion/story-state boundary | Makes the standalone reunion route available after return to Hub. It is not granted by a failed/abandoned encounter. | Inject victory-save failure, reload and retry; no premature route availability or duplicate event. |
| `m8_ashen_regent_defeated` | Victory in `m8_ashen_regent_boss` | M4B-style four-member boss settlement and `PartyState` clear evidence | Completes Floor V once, grants approved first-clear rewards, returns all four to Hub. | Win/reload/repeat; preserve pre-boss pair and prior expedition attribution. |
| `m8_future_region_report` | `m8_ashen_regent_defeated` | Story/knowledge event owner | Records a rumor that the wider campaign continues; no Floor VI destination or playable content is promised by this manifest. | Verify narrative marker only; no phantom destination, route, or reward. |
| `m8_story_reliquary_echo` | Claim of `m8_floor_four_story_report` | M6 report claim boundary + `StoryState` | Records the optional echo and enables the approved optional scene; no progression gate or combat benefit. | Claim once, verify scene enabled after reload, duplicate claim has no second effect. |
| `m8_reliquary_echo_scene` | `m8_story_reliquary_echo` recorded; available at Hub | Authored optional story scene + `StoryState` | One finite non-pair-specific scene; records completion only. | Available only after report claim; replay and reload do not repeat one-time effects. |

Knowledge model proposal for M8-D3: explicit Unknown, Rumored, Confirmed facts, each with a stable fact ID, authored reveal source, and truthful projection. A reveal changes only the named fact(s); load/view rebuild never promotes knowledge.

| Fact ID | Initial state and reveal source | Owner / effect | Proof |
| --- | --- | --- | --- |
| `m8_fact_drowned_reliquary` | Unknown; briefing `m8_drowned_reliquary_briefing` changes it to Rumored; entering the destination confirms it. | Knowledge projection; truthful destination summary only. | Reload at both states; hidden enemy details remain hidden until separately revealed. |
| `m8_fact_reliquary_threats` | Unknown; Floor-IV Scouting report changes it to Confirmed. | M6 report claim + knowledge owner; shows authored enemy/weakness hints only. | Claim and reload; compare terminal/browser exact facts and avoid exposing unconfirmed details. |
| `m8_fact_ashen_vault` | Unknown; Floor-IV clear changes it to Rumored; Scouting can confirm it. | Clear progression + knowledge owner; exposes destination only at Rumored, with approved summary. | Verify route is unavailable before Floor-IV clear and available after; knowledge state persists. |
| `m8_fact_ashen_regent` | Unknown; optional Azhvielle archive memory or Scouting report changes it to Confirmed. | Story/report claim + knowledge owner; identifies the reunion threat and preparation hint. | Both reveal paths, reload, and no inferred promotion from viewing the boss route. |

All six pair scenes remain optional content and no pairing is globally disabled.

### Permanent Discoveries And Ordinary Rewards

| Proposed ID | Prerequisite/source | Owner | Effect / unlock | Proof journey |
| --- | --- | --- | --- | --- |
| `ancient_well_floor4_01` | Search at `floor_four_rest_midpoint`; proposed base chance 1,000 bps | Existing `RunEventService` search + `PermanentDiscoveryService` claim | Ancient Well, +5 max HP to one player-selected active Drifter; claim is source-specific and one-time. | Search outcome persists on reload/retry; selected target receives once; death/loss follows approved run/claim rules. |
| `forgotten_altar_floor4_01` | Search at `floor_four_rest_pre_boss`; proposed base chance 1,000 bps | Existing discovery search/claim owners | Forgotten Altar, +5 max Mana to one active Drifter. | Confirm target choice, cap cancel/consume behavior, replay and failed-write atomicity. |
| `spirit_relic_floor5_01` | Search at `floor_five_rest_midpoint`; proposed base chance 1,000 bps | M8.4 discovery definition/claim owner; M8.7 route placement | Spirit Relic, exactly +3 GP to one active Drifter. | Search/save/reload/claim once; verify active-target rejection and no duplicate GP. |
| `m8_floor_four_metal_drop_01` | Genuine victory against a `reliquary_sentinel` on Floor IV | Enemy drop catalog + `RunEventService` + shared material inventory | Eligible Grade-IV Metal; chance/quantity authored at Gate 2, never a guaranteed arbitrary item. | Drop provenance and no Grade-IV source on Floors I-III. |
| `m8_floor_four_fiber_drop_01` | Genuine victory against a `drowned_stalker` on Floor IV | Enemy drop catalog + `RunEventService` + shared material inventory | Eligible Grade-IV Fiber; chance/quantity authored at Gate 2. | Same source, retry and floor-boundary proof. |
| `m8_floor_four_timber_drop_01` | Genuine victory against an `ashbound_hound` on Floor IV | Enemy drop catalog + `RunEventService` + shared material inventory | Eligible Grade-IV Timber; chance/quantity authored at Gate 2. | Same source, retry and floor-boundary proof. |
| `m8_floor_four_core_drop_01` | Genuine victory against `tidebound_curator` | Boss reward catalog + `RunEventService` + shared material inventory | Eligible Grade-IV Core; also supplies the Floor-IV Elite expedition consumer. | Boss victory/settlement retry, no duplication, and provenance validation. |
| `m8_ashen_regent_grade_iv_core_01` | Genuine victory against `ashen_regent` | Reunion boss reward catalog + shared inventory | Grade-IV Core is a legitimate Floor-V material source. | Four-member victory and first-clear/replay evidence; no report can invent a different grade. |
| `m8_floor_four_first_clear_crystal` | First `floor_four` boss clear | M6.5 first-clear reward catalog/party settlement | One Grade-IV Magic Crystal; this fills the catalog's reserved Floor-IV source. | First clear grants once; replay, reload and failed save cannot duplicate. |
| `m8_floor_four_armor_source` | Victory at `floor_four_battle_08` | M5 armor generation + persisted run event | One authored Floor-IV M5 armor instance, unsecured until safe securing; this creates the first legitimate equipment-expedition source. | Actual browser/terminal battle path, Rest secure, save/reload and next victory; no fixture-only grant. |
| `m8_floor_four_recovery_source` | Victory at `floor_four_battle_08` (separate authored deterministic source) | M2 shared/recovery item owner + run event | One Healing Potion in eligible floor reward provenance; enables Floor-IV Recovery assignment. | Verify actual reward, carrying/secured handling, death, extraction and no duplicate on replay. |
| `m8_floor_five_first_clear_reward` | First `m8_ashen_regent_boss` clear | Existing M6.5 shared inventory and first-clear settlement | Proposed one Grade-IV Magic Crystal; no Grade-V crystal or M6.5 Grade-V source is introduced. | Four-member clear/reload/repeat; exactly one shared item reward. |

#### Proposed Grade II-IV Component Coverage

M6.5's shared component inventory/Blacksmith transaction contract remains authoritative. This proposal adds one recipe for each existing weapon component family at Grades II, III and IV: 4 weapons x 4 slots x 3 grades = 48 finite recipes. Exact stable IDs are `m8_<existing_component_id>_grade_ii`, `m8_<existing_component_id>_grade_iii`, and `m8_<existing_component_id>_grade_iv`; the 16 Grade-I base IDs are:

| Weapon | Existing Grade-I component IDs | Proposed additions |
| --- | --- | --- |
| Needle of Plain Iron | `needle_focus_fitted`, `needle_binding_warded`, `needle_haft_ashwood`, `needle_seal_faded` | Each base ID plus the Grade-II, Grade-III and Grade-IV suffixes above. |
| Sky Needle | `sky_needle_head_balanced`, `sky_needle_binding_conductive`, `sky_needle_shaft_flexible`, `sky_needle_focus_stormglass` | Same 3 grade variants per ID. |
| Sathren | `sathren_grip_precision`, `sathren_string_taut`, `sathren_limbs_reinforced`, `sathren_reservoir_alchemical` | Same 3 grade variants per ID. |
| Sunder Spire | `sunder_spire_blade_reinforced`, `sunder_spire_grip_braided`, `sunder_spire_hilt_ashwood`, `sunder_spire_crest_faded` | Same 3 grade variants per ID. |

Prerequisite/unlock: each grade's recipe becomes available at the Blacksmith after the matching floor is cleared (II, III, IV); already-cleared saves qualify after migration. Existing component craft eligibility, material spending, Crafting XP, exact Drifter target, install behavior, M6.5 shared stack consumption/recovery, and no lifetime craft limit remain unchanged. Gate 2 authors conservative component effects and exact material costs. Proof: parameterized exact target/slot/grade tests across all 48 definitions, then representative craft, buy/sell, replace, save/reload and M5 combat projection journeys in both clients.

### Proposed Asset Manifest

No current enemy/region assets exist in `root/res/`. IDs below are proposals for static authored media, not new rendering architecture. Gate 2 records the final file path, dimensions, alt text, license/source provenance, and fallback for each accepted asset; missing required assets fail content/build validation.

| Asset ID | Content association | Owner / use | Proof |
| --- | --- | --- | --- |
| `m8_art_drowned_reliquary` | `drowned_reliquary` | Static region key art in terminal/browser destination inspection. | Both builds resolve the asset and readable fallback; verify intended crop and alt text. |
| `m8_art_ashen_vault` | `ashen_vault` | Static region key art in destination/route selection. | Same asset contract and client parity. |
| `m8_portrait_reliquary_sentinel` | `reliquary_sentinel` | Static enemy portrait in semantic battle and inspection. | Correct catalog reference, dimensions and fallback. |
| `m8_portrait_brine_oracle` | `brine_oracle` | Static enemy portrait in semantic battle and inspection. | Same. |
| `m8_portrait_drowned_stalker` | `drowned_stalker` | Static enemy portrait in semantic battle and inspection. | Same. |
| `m8_portrait_ashbound_hound` | `ashbound_hound` | Static enemy portrait in semantic battle and inspection. | Same. |
| `m8_portrait_tidebound_curator` | `tidebound_curator` | Static Floor-IV boss portrait. | Same, plus paired boss association. |
| `m8_portrait_ashen_regent` | `ashen_regent` | Static four-member reunion boss portrait. | Same, plus route association. |

### Proposed M6 Expedition Consumers

M6's passive timer, energy, completed-destination, report-claim and no-dual-deployment contracts stay fixed. The following rows are new M8 consumers; only completed floors expose their categories. The proposal extends compatible pair-outing assignment launch to Floor IV and the Floor-V approach, but not to Floor III or the standalone four-member reunion route. A missing source means the category remains unavailable with a clear explanation.

| Proposed report/content ID | Destination/category | Prerequisite | Owner | Deterministic report effect / unlock | Proof journey |
| --- | --- | --- | --- | --- | --- |
| `m8_floor_four_material_report` | Floor IV / Material | Floor IV completed; a Grade-IV Metal drop is authored | M6 report settlement + shared inventory | One Grade-IV Metal, using the existing fixed one-item-per-assignment pattern. | Timer completion, exact item claim once, reload/retry no duplicate. |
| `m8_floor_four_equipment_report` | Floor IV / Equipment | `m8_floor_four_armor_source` is a legitimate Floor-IV reward | M6 report + M5 `EquipmentInstance` ownership | One frozen authored Floor-IV armor instance; report schema must carry or reference the complete instance, not only item ID/quantity. | Claim, equip, save/reload, retry; no instance duplication or source reroll. |
| `m8_floor_four_recovery_report` | Floor IV / Recovery | `m8_floor_four_recovery_source` is live | M6 report + M2 shared item inventory | One Healing Potion stack unit. | Claim once; carried/secured treatment and reload match the ordinary source. |
| `m8_floor_four_scouting_report` | Floor IV / Scouting | Floor IV completed | New frozen report result + knowledge owner | Confirms `m8_fact_ashen_vault` and `m8_fact_ashen_regent`; helps pair/equipment selection but is not required to enter Floor V. | Claim report, observe actionable facts in both clients, reload and repeat input without a second reveal. |
| `m8_floor_four_story_report` | Floor IV / Story | Floor IV completed | New report result + `StoryState` | Records `m8_story_reliquary_echo`; unlocks an optional story/pair scene, not a mandatory progression lock. | Claim once, scene availability changes, reload, no repeat flag/reward. |
| `m8_floor_four_elite_report` | Floor IV / Elite | Floor IV completed and an authored eligible Grade-IV Core source exists | New report result + shared material inventory | One Grade-IV Core, also legitimately obtainable from a named Floor-IV elite/boss source. | Claim exactly once and compare with authored source catalog; no invented reward. |
| `m8_floor_five_material_report` | Floor V / Material | Floor V completed and Grade-IV material drops are authored there | M6 report + shared inventory | Proposed one Grade-IV Core from the completed floor's eligible source. | Complete reunion boss, settle/claim report once, reload, verify eligible source and item. |

Floor I-III Equipment/Recovery remain unavailable. Floor V Equipment/Recovery/Scouting/Story/Elite remain unavailable in this proposal unless an additional legitimate source/consumer is explicitly added to the approved manifest. Scouting/Story/Elite outcomes are immutable report data and take effect only through the existing exactly-once Hub claim boundary; they do not simulate expedition gameplay.

## Proposed Route And Unlock Graph

```text
Existing: Surface -> Floor I clear -> Floor II
         -> Floor II helper + boss -> Hub recruitment D3/D4 (65g each)
         -> Floor III (pair encounters; all-four boss)
         -> four permanent Drifters -> M6 unlock

M8 proposal:
Floor III clear + roster of four
  -> Hub briefing: Drowned Reliquary = Rumored
  -> Floor IV paired route (any legal pair)
  -> Floor IV boss clear
       -> Floor IV marked complete; first-clear Grade-IV reward once
       -> Floor IV becomes an eligible M6 destination
       -> Ashen Vault becomes available
  -> optional Floor-IV Scouting/Story/Elite/Equipment/Recovery reports
       -> settle/claim once; reports can reveal facts, story flag, or eligible source rewards
  -> Floor V paired approach route (any legal pair)
  -> return to Hub; any active assignment settles by existing M6 rules
  -> arena reveal event
  -> Floor V Reunion route (all four, no active assignment)
  -> Ashen Regent victory; Floor V completion/reward once
  -> Hub, all four reunited, normal two-plus-two loop remains available
```

No branch makes an expedition assignment a hard prerequisite for story completion. The proposed Scouting report changes knowledge and preparation, not basic destination eligibility. No expedition member is used in a boss while assigned; a completed but unclaimed report does not make a permanent Drifter unavailable.

## Canonical Gameplay Contracts

### Selection, Knowledge, And Restrictions

Dungeon selection shows only approved known/rumored information: level guidance, enemies, hazard/resistance/weakness/material hints, story relevance, required members, boss progress and meaningful expedition progress information. Unknown is distinct from absent or false. Reports/NPCs/documents/previous attempts/scouting reveal authored facts through stable discovery identities, not by revealing the full underlying definition by default.

The proposed Floor-IV/V paired routes accept any legal recruited pair. The optional archive scene requires Azhvielle to be in the active pair; no proposed destination locks a specific pair. The reunion event requires all four and its explicit availability gate. No required identity is manufactured or auto-recruited to satisfy entry. Soft power recommendations are not hard level locks. Preserve M1 narrative-lead policy without using active-slot order as character identity.

### Pair And Story Outcomes

All six pairings remain legally usable once all four are recruited. This proposal authors finite optional dialogue and durable event evidence only. Numeric relationship progression, combat synergy, combination attacks, trust/conflict systems, or mechanical environmental solutions require separate explicit approval; dialogue alone is not a mechanical synergy.

Event completion, one-time rewards, requirements and decisions must remain consistent through repeated interaction, return, death and reload. This finite proposal introduces no portable quest/story item: destination and story progression use durable event/knowledge evidence. If a later approved content row needs an item, its M2 secured/unsecured, death-loss, source-reacquisition, and atomic-consumption behavior must be named before implementation. Do not make every discovered item permanently secured to protect a hypothetical key.

### Boss And Region Loop

Reuse the four-member combat contract first qualified at the end of Floor III. Later major dungeon/region reunion bosses may require all four where authored; existing Floor I and earlier ordinary floor-boss parties stay unchanged. Settle/resolve availability of any outstanding expedition before all four deploy, according to M6/M8 entry policy; no member fights and remains assigned simultaneously.

Reuse M4B's four-member battle, defeat, and participant-attributed reward contracts. The recommended M8 reunion is a separate Hub-launched event after the paired outing has ended and any active assignment is settled; it is not a mid-run party swap. Earlier pair-earned XP and expedition participants never change retroactively.

Boss entrance conditions may use approved story/knowledge/preparation events, not every illustrative gate. This manifest uses no portable key item. Clear grants actual approved rewards, story/floor/region unlocks and stock/expedition opportunities once, then returns to the Hub/normal two-plus-two loop where applicable. The first Floor III boss precedes expeditions; do not rewrite that sequence to justify the later reunion model.

### Content Progression And Reward Sources

Grade II first appears on Floor II, III on III, IV on IV. Complete the approved later-floor weapon component/source/recipe content alongside the playable floors, using sealed craft-and-install/slot/Tier V machinery. Earlier floors cannot bypass grades. M6.5 now authorizes shared stacks for uninstalled components, so use its approved purchase/sale/install/replacement recovery contract; do not revive random replacement weapon rewards or add lifetime crafting limits.

The proposed manifest selects no new learnable weapon-technique source. Existing learned techniques and their persistence remain unchanged; do not invent rare-core sources for checklist coverage. Any later technique source needs an explicit manifest row and supported move/effect consumer.

Complete Scouting/Story/Elite expedition assignments and real information/story/reward consumers left by M6. Provide actual gameplay paths for M3's permanent discoveries and M4's search/discovery rules; keep optional awards optional for baseline survival. Trader supply reliability must complement dungeon exceptional rewards. Authored armor rewards obey M5's early-item viability rule rather than later-floor automatic obsolescence.

## State, Persistence, And Integration

Authored content owns destinations, facts, requirements, event/reward IDs, route graph and actual text/assets. StoryState owns completed events and approved decisions; WorldState owns discovered/consumed source evidence; route/run state owns cursor/outcomes/unsecured rewards; roster/advancement/equipment/expedition owners remain authoritative for their own fields. Numeric relationship progression is not in this proposal. Add focused new state only if existing typed owners cannot express the approved contract safely.

The original route spec is linear with global node IDs and specific node kinds. If selected content needs branches, encounters triggered by choices or a floor selector, extend that authored/session contract deliberately; do not run a parallel campaign engine in the browser. Revalidate concrete modules from accepted M1-M7 and M6.5 before planning file edits. Expected integration includes `root/src/app/content/`, game story/world/overworld/party state, session orchestration, presenters/inputs, content tooling and built browser adapters.

Persist source progression/claim IDs and knowledge separately from derived visible text/eligibility. Old saves must migrate without claiming unseen discoveries, granting recruits, losing active checkpoints or changing earlier story decisions. Unknown required content/reference combinations fail validation with a recoverable load error, not invented replacement content. Preserve historical remote revisions/digests; validate current rewards/claims/roster/story coherence before reconstruction.

Failed required writes, duplicate event submissions, stale entry offers and illegal party assignments cannot partially settle an expedition, grant a boss reward or unlock a destination. Prepare an independent accepted outcome before committing multi-owner progression; verify restart consistency at the boundaries. Maintain the existing no-rewind outcome/save model rather than enabling live-battle snapshots to handle narrative gates.

## Client And Asset Requirements

Terminal/browser expose equivalent destination facts, restrictions, roster choices, story options, loot/equipment inspection and outcome reports. Clients do not infer completion from the absence of a route button or roll discoveries. Keep phase-specific phone views/navigation and clear desktop comparison; show which exact Drifter receives a permanent award or has a required role.

Provide the selected release's enemy/region assets with stable IDs, dimensions, readable fallbacks and actual content associations; preserve source artwork. Enemy portraits do not authorize a new graphical combat renderer, animation engine, transmog or 3D dependency. Missing required assets/references are build/content validation failures or explicitly approved fallbacks, not silently blank primary media.

## M8.1-M8.10 Proposed Work Packages

The following ten documents define independently reviewable work packages. They are proposals derived from the audited manifest, not implementation authorization. The parent remains authoritative for the finite inventory, shared contracts, route graph and M8-D1 through D6 decisions; child documents own their package-specific planning, tests and closure record.

| Package | Plan | Scope boundary | Proposed dependencies | Status |
| --- | --- | --- | --- | --- |
| M8.1 | [Region progression, selection and knowledge](m8-01-region-progression.md) | Clear state, destination eligibility, knowledge facts, migrations and client projections. | Gate 0 approval. | Draft; pending review. |
| M8.2 | [Signature weapon grade expansion](m8-02-weapon-grade-expansion.md) | 48 Grade II-IV recipes and Blacksmith integration; preserve M3/M6.5 crafting. | M8.1 clear-state contract. | Draft; pending review. |
| M8.3 | [Drowned Reliquary, Floor IV](m8-03-floor-four.md) | Twelve-node paired route, nine ordinary encounters, Curator boss, material sources and first clear. | M8.1; M8.2 package boundary. | Draft; pending review. |
| M8.4 | [Permanent discoveries, armor and recovery rewards](m8-04-discoveries-and-rewards.md) | Generalize reward boundaries; register three discovery rewards; connect live Floor-IV armor/recovery sources. | M8.3 route and source nodes. | Draft; pending review. |
| M8.5 | [Expedition expansion](m8-05-expedition-expansion.md) | Completed-floor eligibility and frozen Material/Equipment/Recovery/Scouting/Story/Elite reports where sourced. | M8.1, M8.3, M8.4; D5. | Draft; pending review. |
| M8.6 | [Character stories and pair interactions](m8-06-character-stories.md) | Six pair scenes, optional Azhvielle archive, optional expedition-story consumer. | M8.1 knowledge; M8.5 Story report; D2. | Draft; pending review. |
| M8.7 | [Ashen Vault, Floor V approach](m8-07-floor-five-approach.md) | Seven-node paired approach, Spirit Relic placement, durable arena reveal. | M8.1, M8.4, M8.5; Floor-IV clear. | Draft; pending review. |
| M8.8 | [Ashen Regent and full-party reunion](m8-08-reunion-boss.md) | Separate four-member Hub boss, settlement, Floor-V clear and return to pair play. | M8.1, M8.5, M8.7; D5. | Draft; pending review. |
| M8.9 | [Region and enemy visual presentation](m8-09-visual-presentation.md) | Two region illustrations and six static enemy/boss portraits; no new combat renderer. | Stable IDs; D1 and D6. Can run alongside M8.2-M8.8. | Draft; pending review. |
| M8.10 | [Integrated campaign qualification](m8-10-integrated-qualification.md) | Cumulative progression journeys, cross-client/persistence checks and M8 closure evidence. | M8.1-M8.9 accepted; D1-D6 resolved. | Draft; pending review. |

**Dependency graph:** `M8.1 -> M8.2 -> M8.3 -> M8.4 -> M8.5 -> M8.6 -> M8.7 -> M8.8 -> M8.10`; M8.9 may proceed in parallel after the manifest IDs and visual scope are approved and must integrate before M8.10. M8.7 specifically consumes M8.4's Spirit Relic definition/claim behavior and M8.5's approved expedition coexistence contract; it owns only the Floor-V route placement. M8.3 does not expose armor/recovery/discovery rewards before M8.4. M8.5 may define later-floor report support before Floor V completes, but the Floor-V Material report remains unavailable until M8.8 records the genuine clear.

Each child package must complete its own planning approval, implementation, focused/regression tests, independent review, exact-SHA hosted CI, and closure record. Applicable cumulative suites and pinned MicroPython evidence are required when shared Python runtime/save state is changed. A failing package reopens only its owning scope unless the review demonstrates a cross-package contract defect. No package can close by inheriting another package's green run.

Gate 0 remains open until the user reviews the decomposition and explicitly resolves M8-D1 through D6. The prior source audit and finite manifest above remain the planning authority; the child documents do not independently redefine them.

## M8-D1 Through M8-D6: Approval Required

All six rows below are **proposals for review**, not approved decisions. Recommendations use the audited repository and the future designs without silently promoting every example into scope.

### M8-D1: Finite Content Scope

**Recommend:** approve only proposed Floors IV-V, 3 routes, 17 encounter definitions (including 2 bosses), the 4 proposed ordinary archetypes, 2 bosses, the 48 Grade II-IV component recipes, three permanent discoveries, the first-clear/recovery/armor/material rewards, and the listed report consumers. Do not add Floor VI, formations, phases, additional recruitment, or unlimited pair synergies in M8. All IDs/compositions/source rows are in the manifest above. This is a substantial but finite content package; declining either proposed floor requires removing its dependent IDs and route rows before Gate 0 closes.

### M8-D2: Pair Story And Mechanics

**Recommend:** approve six short, one-time pair-scene variants at the Floor-IV midpoint Rest plus the optional Azhvielle archive scene. Persist event/decision IDs only. Do not add numeric relationship levels, mandatory pair locks, combo attacks or mechanical bonuses in this release. If a synergy mechanic is desired, select its exact pair, input, effect, costs and proof contract before Gate 3.

### M8-D3: Knowledge And Permanent Discovery

**Recommend:** approve Unknown/Rumored/Confirmed fact visibility with the four proposed stable fact IDs and named reveal sources. Reuse M3's source-specific one-time permanent awards, active-party-only target, no new per-Drifter cap, and the existing Intuition search bonus. Use the M4 conservative 1,000 bps authored base chance for the three proposed searches; resolve each outcome at the authoritative search event and persist it before presenting the result. Scouting reveals useful facts but is not required for core progression.

### M8-D4: Story-Critical Items And Death

**Recommend:** approve no portable quest/story item in this finite M8 manifest; all proposed gates use durable event and knowledge facts. If later approved scope adds an item, preserve M2 unsecured/death-loss behavior unless a separately named exception is approved, make the source legitimately reacquirable where required, and atomically record consumption into durable story/world evidence. Do not create a broad inventory exemption or permanently secure an unmanifested key.

### M8-D5: Four-Party Boss And Outstanding Expedition

**Recommend:** the reunion boss is a separate Hub-launched route requiring all four permanent Drifters and no active assignment. The player must end the active outing normally; M6 settlement then marks the assignment complete or incomplete under its existing 20-minute rule. A settled, completed but unclaimed report does not block reunion. Never pull assigned members into combat or auto-cancel/refund the assignment. Permit an assignment alongside M8's pair-only Floor-IV/Floor-V approach outings; retain the Floor-III and four-member reunion restrictions. Use the existing M4B shared boss XP pool split four ways, then each member's own Intuition bonus; pair-earned pre-boss XP remains with its original pair. This differs from a broader future-design sentence suggesting full per-member boss XP, so the explicit M8 reward rule needs approval.

### M8-D6: Hazards, Enemy Visuals And Combat Presentation

**Recommend:** select no new hazard mechanic, formation system, boss phase or graphical combat renderer. Use authored archetypes, existing M4 resistance/weakness hooks if any values are deliberately selected, and M7 Momentum unchanged. Require static region key art for both proposed destinations and readable portraits for the four new ordinary archetypes and two bosses; include stable IDs, dimensions, alt text and a documented readable fallback. Battle remains the current text/semantic interface.

## Gate 0 Decision Record

| Decision | Status at audit | Blocks |
| --- | --- | --- |
| M8-D1 finite scope/manifest | Proposed; approval required | All implementation packages |
| M8-D2 pair story/synergy | Proposed; approval required | M8.6 |
| M8-D3 knowledge/discoveries | Proposed; approval required | M8.1, M8.4, M8.5 and M8.7 |
| M8-D4 quest-item loss/security | Proposed; approval required | M8.4 and any future item-gated scope; current manifest proposes no portable key |
| M8-D5 reunion/expedition/XP | Proposed; approval required | M8.5, M8.7 and M8.8 |
| M8-D6 hazards/assets/renderer | Proposed; approval required | M8.3 and M8.9 |

Exact future signatures are deliberately left for repository revalidation, not replaced with fabricated APIs in this plan.

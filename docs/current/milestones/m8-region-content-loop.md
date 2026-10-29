# M8 Region, Story, And Content Loop Implementation Plan

> Implementation method: use `superpowers:executing-plans` for native gate-by-gate execution. Approve a finite release manifest before authoring content; the source examples do not define a whole campaign automatically.

**Status:** Draft for review, 2026-10-29. Semantic implementation contract; concrete files/APIs must be revalidated after M1-M6 and M7 if selected.

**Goal:** Integrate the delivered systems into a complete, finite region progression loop with meaningful information, party restrictions, story/pair outcomes, later-floor rewards, and later full-roster convergence where authored.

**Architecture:** Extend existing authored route/encounter/content and story/world/game source state. Use accepted roster, reward, advancement, equipment and expedition services. Clients render legal story/dungeon choices and results without owning unlocks or generating campaign rewards.

**Tech stack:** Current Python content/runtime/persistence/presentation stack and client/tooling contracts as revalidated at entry; no new backend or graphical engine is implied.

## Authority And Dependencies

- [Roadmap](../development-roadmap.md), M8, fixed pacing and common qualification contract.
- [Party design](../../future/party-and-expedition-core-loop.md), dungeon knowledge/restrictions, pair identity, reunion/boss/post-boss loop.
- [Economy](../../future/dungeon-progression-difficulty-and-economy.md), pressure, secure/loss rules, preparation, trader/expedition roles and quest protections.
- [Enemy design](../../future/enemy-archetypes-scaling-and-capability-progression.md), selected formations/phases/visuals and placement versus tier.
- [Character growth](../../future/character-growth-and-stat-scaling.md), permanent discoveries and passive/move prerequisites.
- [Armor](../../future/armor.md), viable owned rewards; [component catalog](../weapons/component.md) and [weapon design](../weapons/signature-weapon-progression.md), Grade I-IV/floor boundaries.
- [M4](m4-enemy-progression.md) already delivers D3/Floor II and D4/Floor III/four-party-boss readiness; [M6](m6-expeditions.md) already delivers a minimal playable Floor IV two-plus-two loop. M8 expands and integrates them, not postpones prerequisites needed by earlier milestones.

Non-goals: defining an unlimited campaign, reimplementing systems, redoing canonical first recruitment, forcing four-member parties into every boss, adopting every possible pair/combo/relationship mechanic, full graphical combat, payment integration, `longterm.md`, or executable packaging.

## Entry Baseline And Finite Scope

At the inspected `8099b895` baseline, only Surface and Floor I routes exist. StoryState supports flags/completed events/decisions; WorldState supports discoveries/opened/consumed objects and dungeon changes. These containers do not by themselves implement branching campaign progression, knowledge, relationship events, quest protection, scouting consumers, or region selection.

At actual entry, M1-M6 should have supplied later recruitment/boss readiness, exact roster ownership, supplies/trading, character growth, equipment, enemies and expedition state. Build an implementation inventory from accepted milestone evidence, not these plans' unchecked boxes. Identify real reusable interfaces and any remaining controlled-only outputs such as Scouting/Story/Elite category contracts or permanent discoveries without locations.

Gate 0 must approve a finite manifest of named playable destinations/floors, routes/exits, encounters, bosses, recruitment/story beats, pair restrictions, dialogue/synergy selections, equipment/weapon component recipes, selected learned-technique sources, material/reward sources, discoveries, quest items, expedition assignments, trader stock and required assets. Give each row a stable content ID, prerequisites, owning source requirement, effect/consumer, proof journey, and implementation gate. Named example locations such as the Drowned Reliquary and Ashen Vault are not automatically required campaign locations.

No final release-floor count, battle count, difficulty formula or exact future module signature is known from the sources. Fix those choices at entry; do not leave a claim of "complete campaign" attached to an unbounded list.

## Canonical Gameplay Contracts

### Selection, Knowledge, And Restrictions

Dungeon selection shows only approved known/rumored information: level guidance, enemies, hazard/resistance/weakness/material hints, story relevance, required members, boss progress and meaningful expedition progress information. Unknown is distinct from absent or false. Reports/NPCs/documents/previous attempts/scouting reveal authored facts through stable discovery identities, not by revealing the full underlying definition by default.

Free-choice destinations accept any legal recruited pair. Character-story destinations require one named recruited member and allow a legal partner; locked-pair destinations require the authored pair. Full-party events require all four and the explicit availability/story gate. No required identity is manufactured or auto-recruited to satisfy entry. Soft power recommendations are not hard level locks. Preserve M1 narrative-lead policy without using active-slot order as character identity.

### Pair And Story Outcomes

All six pairings remain legally usable once all four are recruited; a selected dungeon can favor or require a pair without making the others invalid globally. Author the finite selected dialogue, relationship flags and useful mechanical interactions. Possible combination attacks, trust/conflict systems or environmental solutions require actual approved mechanics; a line of dialogue does not count as a functioning synergy system.

Event completion, one-time rewards, requirements and decisions must remain consistent through repeated interaction, return, death and reload. Quest/story-critical item loss exemptions need an explicit policy; ordinary death must not silently erase story-critical progress because it uses the same stack shape as Goblin Scrap. Do not make every discovered item permanently secured merely to protect one quest key.

### Boss And Region Loop

Reuse the four-member combat contract first qualified at the end of Floor III. Later major dungeon/region reunion bosses may require all four where authored; existing Floor I and earlier ordinary floor-boss parties stay unchanged. Settle/resolve availability of any outstanding expedition before all four deploy, according to M6/M8 entry policy; no member fights and remains assigned simultaneously.

Use M4B's explicit pair-to-four encounter boundary and participant-attributed reward contract. Expanding for a boss must not redistribute earlier pair-earned XP to the newly present members or retroactively change expedition participants. This is an authored event transition, not an ordinary mid-run party-swap affordance.

Boss entrance conditions may use approved keys/story/knowledge/preparation events, not every illustrative gate. Clear grants actual approved rewards, story/floor/region unlocks and stock/expedition opportunities once, then returns to the Hub/normal two-plus-two loop where applicable. The first Floor III boss precedes expeditions; do not rewrite that sequence to justify the later reunion model.

### Content Progression And Reward Sources

Grade II first appears on Floor II, III on III, IV on IV. Complete the approved later-floor weapon component/source/recipe content alongside the playable floors, using sealed craft-and-install/slot/Tier V machinery. Earlier floors cannot bypass grades. Do not create inventory stacks of signature parts or revive random replacement signature weapon rewards.

Where the release manifest introduces a learnable weapon technique, author its actual source, eligibility and supported move/effect consumer. Prove learning persists after component replacement and remains separate from GP-purchased/refunded moves. Controlled lifecycle tests from the earlier weapon system do not count as a real technique acquisition source; if none is selected, record that content disposition explicitly rather than inventing rare cores for checklist coverage.

Complete Scouting/Story/Elite expedition assignments and real information/story/reward consumers left by M6. Provide actual gameplay paths for M3's permanent discoveries and M4's search/discovery rules; keep optional awards optional for baseline survival. Trader supply reliability must complement dungeon exceptional rewards. Authored armor rewards obey M5's early-item viability rule rather than later-floor automatic obsolescence.

## State, Persistence, And Integration

Authored content owns destinations, facts, requirements, event/reward IDs, route graph and actual text/assets. StoryState owns completed events/decisions/relationships where appropriate; WorldState owns discovered/consumed source evidence; route/run state owns cursor/outcomes/unsecured rewards; roster/advancement/equipment/expedition owners remain authoritative for their own fields. Add focused new state only if existing typed owners cannot express the approved contract safely.

The original route spec is linear with global node IDs and specific node kinds. If selected content needs branches, encounters triggered by choices or a floor selector, extend that authored/session contract deliberately; do not run a parallel campaign engine in the browser. Revalidate concrete modules from accepted M1-M6 before planning file edits. Expected integration includes `root/src/app/content/`, game story/world/overworld/party state, session orchestration, presenters/inputs, content tooling and built browser adapters.

Persist source progression/claim IDs and knowledge separately from derived visible text/eligibility. Old saves must migrate without claiming unseen discoveries, granting recruits, losing active checkpoints or changing earlier story decisions. Unknown required content/reference combinations fail validation with a recoverable load error, not invented replacement content. Preserve historical remote revisions/digests; validate current rewards/claims/roster/story coherence before reconstruction.

Failed required writes, duplicate event submissions, stale entry offers, missing quest inputs and illegal party assignments cannot partially consume keys, settle an expedition, grant a boss reward or unlock a destination. Prepare an independent accepted outcome before committing multi-owner progression; verify restart consistency at the boundaries. Maintain the existing no-rewind outcome/save model rather than enabling live-battle snapshots to handle narrative gates.

## Client And Asset Requirements

Terminal/browser expose equivalent destination facts, restrictions, roster choices, story options, loot/equipment inspection and outcome reports. Clients do not infer completion from the absence of a route button or roll discoveries. Keep phase-specific phone views/navigation and clear desktop comparison; show which exact Drifter receives a permanent award or has a required role.

Provide the selected release's enemy/region assets with stable IDs, dimensions, readable fallbacks and actual content associations; preserve source artwork. Enemy portraits do not authorize a new graphical combat renderer, animation engine, transmog or 3D dependency. Missing required assets/references are build/content validation failures or explicitly approved fallbacks, not silently blank primary media.

## Review Focus

- Unknown/rumored knowledge must not become a confirmed spoiler on load; Gate 1 checks exact reveal state.
- Required characters must not be auto-recruited or swapped in during a run; Gate 1 rejects illegal deployment.
- Quest keys and permanent discovery claims must not disappear or duplicate across failure/reload; Gate 2 checks approved protection and security.
- A reunion boss must not use members simultaneously assigned to an expedition; Gate 4 tests settlement and availability.
- Later-floor source/component integration must not yield higher grades early or revive stacked signature parts; Gate 2 checks content and actual rewards.

## Gates And Tests

### Gate 0 - Approve The Manifest And Outstanding Product Choices

- [ ] Revalidate accepted M1-M6/M7 evidence, then approve M8-D1 through D6. Resolve the explicit difference between required behavior, chosen illustrative content and deferred optional systems.
- [ ] Complete the finite content/requirements/proof matrix and route/unlock graph. Ensure no destination depends on an expedition that cannot unlock until after that same destination.
- [ ] Define story-critical protection, knowledge reveals, pair/combination mechanics and late reunion settlement before coding their events.

Proof: every manifest row has a legal acquisition/entry/consumer/return path and a named owner; no unknown campaign-size promise remains.

### Gate 1 - Destination Knowledge And Restriction Flow

- [ ] Red/green tests for unknown/rumored/confirmed facts, selected reveal sources, locked destination versus soft recommendation, one-required/two-required/free pair validation, and stale offers with no mutation.
- [ ] Implement selection/knowledge through accepted content/session/presenter boundaries. Round-trip discoveries without rerolling or revealing hidden content on load.
- [ ] Prove terminal and browser make the same exact-ID eligibility decisions, including a missing required unrecruited member.

Proof: a real approved reveal changes an actionable destination decision; placeholder hint text is not knowledge progression.

### Gate 2 - Floor/Region Content And Permanent Discovery

- [ ] Author the approved incremental encounter/hazard/reward/weapon/equipment content, completing Grade II-IV coverage without duplicating M4/M6 content IDs or moving sources to earlier floors.
- [ ] Connect actual treasure/search/altar locations to M3/M4 award/claim services; test duplicate use, selected target, failed commit, death/extraction provenance and quest protection.
- [ ] Validate catalogs, route reachability, references, unsupported move/effect forms, grade/source boundaries and required media at build time.

Proof: each approved floor/content row is playable and observable, not merely accepted by a data constructor.

### Gate 3 - Pair Story And Remaining Expedition Consumers

- [ ] Author selected conversations/relationships/synergies with specific eligibility, result and repeat policy. Test exact character identity regardless of active order and no repeat GP/item/story rewards.
- [ ] Complete real Scouting/Story/Elite assignments and reports using M6's engine; show their information/story/resources changing a later legitimate player choice.
- [ ] Test saved assignment results, unlock chains, cancellation/return interactions and immunity to repeated report claims. No commercial purchase is required for story completion.

Proof: selected pair/expedition content has real downstream consumers in both clients; record unselected illustrative mechanics explicitly.

### Gate 4 - Later Full-Party Convergence And Post-Boss Return

- [ ] Use the approved outstanding-expedition settlement rule, entry requirements, full-party targets/effects and reward pool from accepted earlier work; no dual deployment.
- [ ] Test gate/key consumption, four-member victory/defeat, once-only boss/reunion rewards, new region/stock/expedition unlocks and return to normal pair selection. Check the starting Drifter can be defeated without premature party defeat.
- [ ] Verify pre-boss pair rewards retain their participants across reunion, including an outstanding expedition settled by the approved policy. No enlarged-party calculation may rewrite earlier reward recipients.
- [ ] Inject failed required writes at entry/claim/clear/reunion transitions and reload from disk/browser storage to prove restart consistency and no reward/expedition duplication.

Proof: an actual later reunion encounter where selected, distinct from the already-proven Floor III boss and not imposed on Floor I.

### Gate 5 - Finite Release Loop And Qualification

- [ ] Terminal and built-browser proof covers preparation -> knowledge -> legal pair -> dungeon/expedition -> return/reward -> selected full-party boss -> next region/unlock -> normal split, with save/reload at supported checkpoints.
- [ ] Reconfirm all six pairings for legal play and selected story restrictions. Use focused pairing tests and bounded journeys, not six identical full campaign smokes.
- [ ] Extend the real pinned probe to new ownership/state transitions and the bounded final content loop, then run shared cumulative qualification and exact-SHA hosted checks. Complete the content traceability ledger for M9.

Closure: every approved manifest row has actual gameplay and acceptance evidence; content-only placeholders are not shipped behavior. The finite region loop works, no early recruitment or extraction regression exists, and every excluded example has an explicit downstream/approved disposition rather than being silently deleted.

## Unresolved Product Decisions

| ID | Decision and blocking gate |
| --- | --- |
| M8-D1 | Finite release destinations/floors, route counts/exits, bosses, required assets/content; Gate 0 |
| M8-D2 | Story scripts/requirements, pair dialogue/relationships and selected actual synergy mechanics; before Gate 3 |
| M8-D3 | Knowledge granularity/reveal sources, discovery locations, permanent award limits and target scope; before Gates 1/2 |
| M8-D4 | Quest/story item security and loss exceptions; before Gate 2 |
| M8-D5 | Later region boss party rules and outstanding-expedition settlement; before Gate 4 |
| M8-D6 | Which optional hazards, enemy visuals and full graphical-combat scope are selected; Gate 0; visual asset work alone does not select a new renderer |

Exact future signatures are deliberately left for repository revalidation, not replaced with fabricated APIs in this plan.

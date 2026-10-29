# Future Systems Delivery Roadmap

**Status:** Proposed sequence for review, 2026-10-29. This is a roadmap, not authorization to implement every speculative example in the source documents.

**Baseline inspected:** `hub` at `8099b895f0d6f2e7d0415909d3d98e83216a2f0f`, plus the local closure-note edits and untracked armor design. Source documents are unchanged by this review.

**Goal:** Finish the remaining documented gameplay systems in playable, independently reviewable milestones, then qualify a bounded content release and improve website delivery.

**Architecture:** Extend the existing Python-authoritative domain, session/presenter, content catalog, and persistence boundaries. Terminal and browser consume the same legal actions. Do not replace the package architecture, save architecture, or signature-weapon ownership model.

## Scope And Sources

Explicit exclusions: `docs/future/longterm.md` and everything under `docs/future/exe/`. No executable distribution work belongs to this roadmap.

| Included source | Delivery owner in this roadmap |
| --- | --- |
| [Party and Expedition Core Loop](../../future/party-and-expedition-core-loop.md) | M1 roster architecture and staged recruitment, M6 expeditions, M8 regions/story/later full-party bosses |
| [Dungeon Progression, Difficulty, and Economy](../../future/dungeon-progression-difficulty-and-economy.md) | M2 supplies/extraction, M4 pressure, M5 equipment, M6 energy, M8 content, M9 economy/optional services |
| [Character Growth and Stat Scaling](../../future/character-growth-and-stat-scaling.md) | M3 advancement, M7 Momentum interaction, M8 permanent discoveries, M9 tuning |
| [Enemy Archetypes, Scaling, and Capability Progression](../../future/enemy-archetypes-scaling-and-capability-progression.md) | M4 enemy systems, M8 encounters/bosses/visual content |
| [Momentum](../../future/momentum.md) | M7 temporary combat mechanic |
| [Armor](../../future/armor.md) | M5 armor/accessories/ownership/upgrade loop |
| [Website Profile Report](../../future/website-profile-report.md) | W1 independent website delivery and measurement lane |

The website report is a September measurement, not a current performance result. Armor is included because it is present locally, regardless of its current Git tracking status.

## Existing Work To Reuse

These observations come from source inspection, not a fresh full regression run.

| Area | Already present | Remaining distinction |
| --- | --- | --- |
| Character progression | Six stats, stat caps, levels, XP curve, three Growth Points per level, stat spending, automatic HP/mana growth | Do not reimplement these as future tasks. Current code caps level at 250; changing that requires a deliberate decision. |
| Scaling | Piecewise HP/mana and output curves in `player/scaling.py`; resolver uses Strength/Dexterity/Intelligence output, Strength negation, Dexterity accuracy/dodge, Intuition critical/Super bonuses | Special-potency, discovery, and secured-XP helpers exist without gameplay callers found. Separate damage components are not equivalent to the current single move power and averaged scaling bonuses. |
| Hub and dungeon | First companion recruitment, two-person combat, tutorial extraction, Floor I, rests, reward banking, replay XP reduction, death return | `PartyState` still explicitly requires the tutorial pair. It is not a permanent selectable four-person roster yet. |
| Weapons | Craft-and-install, per-Drifter slot progress, quality gates, Tier V machinery, shared materials/Crafting, salvage and persistence | Later-floor component content is not yet authored; do not rebuild the generic system. |
| Enemies | Authored rank/role/behavior/capabilities, five archetypes, structured moves, XP/gold and item drops | Authored enemy tiers currently accept only `(0,)`. Move selection is uniform among affordable moves; party targeting chooses a living Drifter randomly. |
| Inventory | Shared item stacks and inspection; character-owned ingredient preparation/infusion recipes | This is not a full shop, general Alchemy system, or persistent armor-instance inventory. |
| Saves and clients | Established snapshots, validated save documents, profile storage/sync, terminal/browser presentation | New state needs deliberate migrations and adapter parity, not another save representation. |

Relevant existing files include:

- `root/src/app/game/party_state.py`, `overworld_state.py`, and `overworld_session.py`.
- `root/src/app/player/player_state.py`, `progression.py`, `scaling.py`, `run_items.py`, and `inventory_action.py`.
- `root/src/app/combat/battle.py`, `resolver.py`, `move.py`, and `combat_state.py`.
- `root/src/app/content/enemy_spec.py`, authored enemies/routes, and the generated catalog.
- `root/src/app/game/weapon_progression.py` and the existing signature-weapon state/content contracts.
- `root/src/app/presentation/overworld_models.py`, `overworld_presenter.py`, terminal UI, and `root/web/`.

## Sequencing Recommendation

Build playable systems in dependency order, using Floor I as the initial proving ground:

```text
M0 baseline/decisions
  -> M1 permanent roster architecture and staged recruitment support
  -> M2 preparation, supplies, and escape tools
  -> M3 remaining character advancement
  -> M4 enemy progression and dungeon pressure
  -> M5 persistent armor and accessories
  -> Floor 3 full-roster boss gate
  -> M6 expeditions and the Floor 4 two-plus-two loop
  -> M7 Momentum
  -> M8 complete region loop and staged later-floor content
  -> M9 integrated balance and release qualification

W1 website improvements: independent lane, scheduled between gameplay milestones
Commercial/optional extension decisions: tracked under M9, not hidden prerequisites
```

This favors a functioning game after every milestone. Building every generic subsystem first would delay playable feedback; finishing one entire design document at a time would duplicate shared inventory, rewards, and roster work. Neither is recommended.

Do not wait until M8 to play new encounters: M4 should prove its systems with a small authored next-floor slice. M8 completes the integrated content rather than inventing every environment and story before the systems are exercised.


## Canonical Recruitment And Expedition Unlock Sequence

This roadmap must preserve the intended roster pacing:

```text
Game start
  -> D1

Floor 1
  -> recruit D2
  -> roster size 2

Floor 2
  -> recruit D3
  -> roster size 3

Floor 3
  -> recruit D4
  -> roster size 4
  -> first full four-Drifter boss battle

Floor 4
  -> expeditions unlock
  -> two Drifters enter the dungeon
  -> two Drifters take expedition assignments
  -> all six pair combinations are now available for legal-play qualification
```

M1 owns the roster architecture that makes this staged growth possible. It does not grant the full roster early. The Floor 3 full-party boss proves four-combatant party behavior before M6 introduces the normal two-plus-two expedition split on Floor 4.


## M0 - Establish The Remaining Contract

**Deliverable:** A short accepted backlog distinguishing implemented behavior, missing behavior, prototypes, and optional examples.

- Preserve the sealed Hub/Floor I/weapon behavior as the regression baseline.
- Preserve the canonical roster pacing: D1 starts; D2 joins on Floor 1; D3 on Floor 2; D4 on Floor 3; Floor 3 culminates in the first full four-Drifter boss battle; Floor 4 is the first expedition-enabled floor.
- Reconcile only explicitly stale statements when their owning milestone starts. Do not bulk-rewrite or delete future designs.
- Record these conflicts for resolution before their owning milestone, rather than changing behavior implicitly:
  - Existing rest extraction keeps 50% XP/gold and all items; the broad economy doc describes full normal extraction. Preserve the explicit Floor I rest rule unless separately changed (M2).
  - Ordinary floor encounters and earlier floor bosses use the currently legal active party. Floor 3 is the first planned full four-Drifter boss battle; later major dungeon/region bosses may reconverge all four. Do not turn every floor boss into a four-person fight (M4/M8).
  - Current full move kits versus future two-move starts, bought moves, and delayed Super. Decide new-game and existing-save behavior before locking moves (M3).
  - Future equipment-expedition weapon rewards and component installation/removal services must not reintroduce random replacement signature weapons or stackable signature parts (M2/M6).
  - Hub return currently restores HP/mana. Persistent injuries, durability, and treatment are optional new systems, not permission to remove that recovery (M4/M8).
  - Armor ring/amulet language versus economy ring/pendant language needs one accessory-slot vocabulary (M5).
  - Expedition completion is gameplay-event-based; energy regeneration is time-based. These are separate clocks/contracts (M6).
  - Website-report accessible-name recommendations conflict with an earlier user preference; obtain approval for that semantic change rather than silently treating the report as authorization (W1).

**Done when:** Each remaining requirement has a milestone and unresolved product choices are visible. No gameplay implementation is required for this gate.

## M1 - Permanent Roster And Hub Party Selection

**Depends on:** M0. **Recommended next implementation milestone.**

1. Preserve the existing Floor 1 recruitment of D2.
2. Build the permanent roster model so recruited and unrecruited Drifters are explicit. The system must support the fixed staged progression: D2 on Floor 1, D3 on Floor 2, D4 on Floor 3. M1 does not grant the full roster early.
3. Represent the permanent recruited roster separately from the active party, preserving exact Drifter identities, XP, equipment, weapon progress, and run-specific state.
4. Allow Hub selection only from currently recruited Drifters. Before four Drifters exist, permit only pairings that are actually possible from the recruited roster. Prevent duplicate assignments and mid-run roster substitution unless explicitly designed.
5. Make inspection, stat spending, weapon progression, and future equipment actions target any exact recruited roster member. Do not rely on lead/companion position as identity.
6. Migrate existing two-Drifter saves without losing progression, changing the current tutorial pair, or silently granting D3/D4.

**Proof:** Preserve the Floor 1 D1+D2 flow; prove recruited versus unrecruited state; save/reload without granting future Drifters; add later recruits through their approved floor events as that content is authored; verify exact Drifter state and participant-only rewards across all currently legal pairings. Full all-six-pair qualification waits until D4 has joined on Floor 3. Terminal and browser must offer the same legal choices.

**Decide at entry:** Recruitment-event representation, lead identity versus active-slot identity, and whether any non-expedition Hub restrictions apply. Recruitment floors are fixed: D2 on Floor 1, D3 on Floor 2, D4 on Floor 3. Exact story scenes/costs remain authored content decisions where not already defined.

## M2 - Hub Preparation, Trading, And Escape Tools

**Depends on:** M1 roster architecture and exact-Drifter ownership; existing reward banking and shared inventory. This milestone must not assume D3 or D4 are already recruited before their canonical floors.

1. Add authored buy/sell stock, prices, stock-unlock conditions, and atomic shared-gold transactions to the merchant. Reuse existing materials and progression services.
2. Distinguish secured Hub storage, carried supplies, and newly found unsecured loot. Preserve spent-supply outcomes through return, death, save, and load.
3. Add a narrow healing-potion loop with a carrying limit and explicit use/target rules.
4. Implement smoke-bomb encounter escape without falsely completing the encounter or duplicating rewards. Implement return-talisman extraction with the specified XP-only reward retention.
5. Keep authorized rest/boss exits and their existing payouts distinct from these escape methods. Run-ending transitions must respect existing no-rewind save invalidation.
6. Expand Alchemy as its own recipe/progression contract, building on existing infusion preparation rather than duplicating it. Author a small useful set of potions, arrow preparations, and intermediate ingredients before expanding the catalog.

**Proof:** Buy supplies -> allocate/use -> find loot -> rest/recover -> choose continue or extract -> bank the correct rewards -> sell/dismantle eligible items. Exercise death, smoke escape, talisman use, insufficient funds, full capacity, and reload with no duplicate spending or rewards.

**Decide at entry:** Shared versus per-Drifter carry capacity, supply-loss policy, item action costs/targets, smoke-bomb boss restrictions and post-escape location, talisman combat legality, and the first Alchemy contract. Prices/yields can use explicitly provisional authored defaults.

## M3 - Complete Character Advancement

**Depends on:** M1; existing scaling and secured-XP pipeline.

1. Audit existing curves/callers against the design and preserve working formulas. Add independently scaled physical/magical/elemental/alchemical damage components where actually needed, with explicit mitigation and rounding order.
2. Complete Intuition special potency, secured-XP handling, and discovery integration. A helper function alone is not a finished mechanic; discovery waits for a real reward/search consumer in M4/M8.
3. Add authored passive nodes/ranks, move purchases, prerequisites, and exact-Drifter spending: one point per stat, two per passive/rank, three per move as currently designed.
4. Author an initial progression path for each Drifter, respecting the four-normal-move plus Super design. Distinguish bought moves from permanently learned weapon techniques.
5. Add the approved respec service, with explicit refund/prerequisite rules and no refunds or resets to weapon investment.
6. Support permanent resource discoveries with unique award identity and repeat-claim prevention; author their actual locations in M8.

**Proof:** Build each Drifter through stat, passive, and move choices; reject unmet prerequisites without spending; save/reload; respec legally without duplicating points or leaving invalid equipped moves. Verify mixed damage, caps, secured-XP application exactly once, and unchanged legacy characters under the approved migration policy.

**Decide at entry:** Initial/unlocked moves and existing-save policy, first passive trees/prerequisites, respec contract, damage-component composition, personal versus party Intuition XP bonus. Preserve documented prototype numbers unless a numerical change is explicitly approved.

## M4 - Enemy Progression And Meaningful Dungeon Pressure

**Depends on:** M3 combat contracts; M2 supplies for preparation counters.

1. Implement authored numerical tier policies while preserving archetype identity and capability budgets. Enemy tier is not weapon quality or material grade.
2. Add explicit resistances/weaknesses and bounded behavior policies for attack, heal, Defend, targeting, and resource use. Tier changes must not automatically grant moves or capabilities.
3. Author additional specialized enemy kits only where encounters need them; reuse existing archetypes rather than rebuilding the catalog.
4. Extend existing XP/gold/item drops into the required reward tables. Connect discovery bonuses to an approved probability/quality rule, without guaranteed rare rewards or reroll-on-reload exploits.
5. Prove formation behavior and a boss phase transition where selected for the first content slice. Do not mistake existing target order for tactical formations.
6. Add one authored environmental pressure and its preparation/counterplay loop. Durability and persistent injuries need separate approval if selected.
7. Build a small next-floor slice using these systems and legitimate next-grade material sources. It need not wait for the entire later campaign.

**Proof:** The same archetype scales without gaining unauthorized capability; enemy instances remain independent; illegal actions cannot be selected; a prepared pair can counter the new threat; rewards enter unsecured state and bank only under the correct return rule.

**Decide at entry:** Initial scaling policies, resistance rules, readable AI behavior, selected formation/phase/hazard mechanics, and which next-floor content to author first. Use editable first-pass values, not an exhaustive balance exercise.

## M5 - Persistent Armor And Accessories

**Depends on:** M1 ownership, M2 item economy, M3 stat/effect composition, M4 reward sources. Respect armor's instruction not to interrupt unfinished foundational work.

1. Define owned equipment instances and equipped references per Drifter; identical-looking pieces with different upgrades must not collapse into one material stack.
2. First prove the armor document's narrow slice: one slot, two pieces, equip, swap, upgrade, sell, dismantle, save/reload.
3. Expand to Helm, Chest, Gloves, and Boots after the slice is accepted.
4. Add the approved accessory slots and specialized effects separately; do not assume accessories share armor's upgrade formula.
5. Integrate enemy/chest/merchant rewards, upgrade previews, inventory management, and safe sell/dismantle behavior for equipped items.
6. Prove an early piece can reach the same supported progression ceiling as later pieces. Rarity changes identity/acquisition/economics, not permission to remain viable.

**Proof:** Keep and upgrade an early helm, swap to an alternative and back with investment intact, transfer equipment under approved ownership rules, and persist exact instances. No duplication, cross-Drifter mis-equipping, or resurrection of sold/dismantled items.

**Decide at entry:** Ownership/transfer eligibility, armor progression ceiling/formula, effect stacking, accessory slots/upgrades, equipped-item disposal, and unsecured-equipment use. Do not invent set bonuses or cosmetic systems merely because they appear as possibilities.

## M6 - Expeditions And The Two-Plus-Two Loop

**Depends on:** M1 roster architecture, M2 rewards/supplies, M3 XP allocation, M4 reward definitions, M5 for real equipment expedition rewards, and completion of the Floor 3 full-roster boss gate. Expeditions do not begin until Floor 4.

1. Unlock expeditions only after the Floor 3 story/recruitment sequence is complete, D4 has joined, and the first full four-Drifter boss battle has been completed. Floor 4 is the first expedition-enabled floor.
2. Separate the four-person permanent roster into an active dungeon pair and an expedition pair, validating availability and exclusivity.
3. Implement energy as a launch resource, with bounded regeneration and refill accounting. It must never block dungeon entry.
4. Advance assignments by explicitly selected gameplay events, not an expedition countdown. Persist assignment identity, progress, and claim state.
5. Begin with Training and Material assignments. Then author Equipment, Scouting, Recovery, Story, and Elite categories once their reward consumers exist.
6. Apply reduced expedition XP with an explicit pool/split rule, rather than assuming a provisional 70-85% is final or granting it to all four members.
7. Resolve rewards/reports once at reunion; support selected character/pair effects and complications. Add scouting information and story unlock consumers in M8.

**Proof:** Complete the Floor 3 full-roster boss -> enter the Floor 4 expedition-enabled state -> choose an active pair -> launch an expedition for the other pair -> play/return -> resolve once -> distribute -> rotate -> repeat. Prove all six legal pair combinations now that all four Drifters exist. Also prove save/load, no-energy dungeon play, death/early-extraction outcomes, and no duplicate expedition rewards.

**Decide at entry:** Energy capacity/regeneration clock and offline rules, qualifying progress events, XP accounting, launch cancellation, and resolution after death/early extraction. Payments are not a prerequisite for this playable milestone.

## M7 - Momentum

**Depends on:** Stable M3 critical/scaling rules and M4 mitigation/AI. Can be scheduled before M6 if a combat-focused milestone is preferred.

1. Resolve the small numerical contract: maximum, successful-action gain, meaningful-damage loss, preservation, critical conversion/cap, and limited Intuition interaction.
2. Store Momentum only in encounter combat state, reset on entry/exit, and keep it out of permanent PlayerState, save progression, and ResourceType.
3. Apply gain once per successful damaging action, not once per hit. Misses do not remove existing Momentum; Defend and sufficient mitigation preserve it under the agreed rules.
4. Add visible combat feedback and explicitly authored enemy access only if approved.

**Proof:** Deterministic gain/loss/preservation, multi-hit behavior, cap interaction, party-member isolation, and reset after every encounter. No permanent save-state or mana-cost changes.

**Decide at entry:** The unresolved formulas and enemy access. Natural decay, thresholds required by moves, and character-specific exceptions are optional choices, not implied requirements.

## M8 - Finish The Region, Story, And Content Loop

**Depends on:** M1-M6; integrate M7 if it is accepted into the release.

1. Agree a finite content manifest: floors/regions, enemies, encounters, bosses, recruitment beats, required pairings, expeditions, equipment, techniques, discoveries, and narrative events. The future docs do not specify enough content to claim an entire campaign is finished.
2. Add dungeon selection, known/rumored information, free-choice/required-character/locked-pair restrictions, and discoveries from scouting, NPCs, documents, and prior attempts.
3. Author pair dialogue/relationship outcomes and selected synergy/combination mechanics. Do not require every listed possible mechanic on every pair or boss.
4. Reuse the four-Drifter combat capability first proven by the Floor 3 boss for later major dungeon/region reunion bosses, with explicit targets/resources/initiative, party-wide effects where authored, and no simultaneous expedition assignment. Preserve the existing two-person Floor I boss unless changed by design.
5. Connect later boss conditions, story progress, new destinations, trader stock, expedition/story unlocks, and return to normal two-plus-two play after reunion encounters.
6. Complete later floors incrementally: author their material sources and weapon components when the floor is playable; prove earlier floors cannot bypass progression gates. Add selected hazards, treasure/search locations, permanent discoveries, and quest-item protections.
7. Supply enemy visual assets and clear client presentation for the chosen release content. Full graphical combat is a separate scope decision, not an accidental dependency of an enemy portrait.

**Proof:** A complete approved region loop from preparation through dungeon/expedition play, knowledge acquisition, a later four-Drifter reunion boss where authored, next-region unlock, and persisted return to the normal two-plus-two loop. Reconfirm all six pairs for legal play and required story combinations; the first all-six-pair qualification occurs once D4 joins and expeditions unlock for Floor 4.

**Decide at entry:** Release content count, floor versus region boss rules, recruitment/story scripts, hazard selections, relationship mechanics, and quest-item exemptions. Named example dungeons in the design are examples until selected for the manifest.

## M9 - Integrated Economy, Optional Services, And Release Closure

**Depends on:** The preceding playable loops, not merely isolated unit tests.

1. Tune progression with real runs: leveling, passive/move opportunity cost, Crafting speed, material scarcity, gold sinks, sell versus dismantle, supply capacity, equipment investment, and expedition efficiency.
2. Test rotation, favored-pair specialization, catch-up, early-floor farming, soft progression walls, and eventual overpowered returns. Preserve free access to dungeon gameplay and the ability to progress without payment.
3. Audit every source requirement against the delivered release manifest and mark it implemented, explicitly deferred by approval, or still open. A prototype function or empty content category does not count as delivered gameplay.
4. Run cumulative client/service/browser/content/migration qualification and the real pinned MicroPython matrix on the final runtime/probe tree. Record exact SHA evidence and real heap observations; do not impose the previous probe heap as a product memory ceiling.

### Commercial And Optional Extension Decisions

The economy document includes real-money acceleration and numerous optional examples. They remain visible work, not silently dropped, but require their own product decisions before implementation:

- Energy purchases/capacity upgrades, reward bonuses, convenience bundles, passes, cosmetics, skins, decorations, and visual effects: approve a concrete offer list. Real purchases require authoritative account entitlements, receipt verification, idempotent grants, refund/revocation handling, secure provider adapters, and an offline/free-play policy. Never trust a browser-provided payment flag. Reuse the existing profile/identity boundary; do not redesign core saves around a vendor.
- Daily/login rewards, achievements, milestone refills, and Hub/account capacity upgrades: choose actual earn rules and persist one-time claims. The source lists possibilities, not an approved implementation for each.
- Rotating/seasonal challenges, prestige, score modes, restricted-party challenges, endless modes, and account cosmetics: decide which are in the finite release, later work, or rejected. Do not declare them complete because the base dungeon loop exists.
- Equipment degradation, persistent injuries, set bonuses, special accessory progression, and cosmetic/transmog systems require explicit selection and their own acceptance contracts where adopted.

**Done when:** The agreed finite gameplay scope is playable and qualified, and every optional item has an explicit disposition. This roadmap does not promise all illustrative endgame/live-service systems without that scope decision.

## W1 - Website Delivery And Discoverability

**Independent of gameplay milestones.** Can ship as bounded maintenance work between them.

1. Reprofile the current built and published pages before relying on the September timing/byte counts. Record cold/warm desktop and actual mobile results, console errors, image transfer, runtime-ready time, and overflow.
2. Generate optimized responsive artwork variants without editing original source artwork. Add intrinsic dimensions and responsive image markup; prioritize visible art and defer below-fold images.
3. Add sitemap/robots, canonical/social metadata, and page descriptions; decide Play indexing explicitly. Add structured game/site data only for facts actually represented on the pages.
4. Correct duplicate page-level headings and inactive-state semantics while preserving the existing visual design. Resolve the icon-button naming preference before adopting that report recommendation.
5. Evaluate versioned asset caching within the deployed host's actual capabilities. Do not promise custom cache headers without verifying hosting support or add an offline/service-worker architecture merely to improve a cache score.
6. Recheck size/startup budgets against measured devices and preserve screenshot parity. The report's 4 MB desktop/2 MB mobile home targets, 100 KB Play shell, and warm-cache six-second startup are proposed budgets, not existing guarantees.
7. Document first-visit runtime cost; decide whether privacy-conscious real-user timing collection is wanted before adding telemetry.

**Proof:** A reproducible before/after report, valid built-site URLs/metadata, visually intact responsive art, no new layout overflow or console failures, and no regression to Play startup/save/reload. Website performance work must not replace the normal homepage with the game.

## How Each Milestone Is Executed

- The implementation documents below expand M1-M9 now. Only the next accepted milestone is entry-ready: revalidate its concrete files, APIs, tests, migrations, and authored content against the repository before execution. Later plans fix semantic contracts, dependencies, gates, and acceptance behavior, not hypothetical future signatures.
- Settle behavioral ambiguities at that milestone's entry. Use labeled configurable defaults for ordinary balance numbers rather than months of up-front tuning.
- Implement one complete player flow, then expand within the milestone. Include terminal/browser projection and save/load in the feature, not as a final catch-up project.
- Run focused regressions per change. Broaden to the full suites at milestone closure or when shared contracts change; avoid duplicative tests whose only purpose is to inflate coverage counts.
- Test invalid actions for zero partial mutation, exact Drifter targeting, reward/transaction idempotency, and legacy save preservation wherever relevant.
- Requalify the real pinned runtime when gameplay/import/probe changes affect it. Record scope honestly when a check is reused or not rerun.
- Review and obtain approval before merging/publishing a milestone. This planning pass performs no commits, pushes, branch creation, or gameplay changes.

## Implementation Documents

These are planning drafts for review, not authorization to implement M1-M9 continuously. M0 remains the entry/decision contract above rather than a separate gameplay implementation milestone.

| Milestone | Implementation document | Entry dependency |
| --- | --- | --- |
| M1 | [Permanent roster](m1-permanent-roster.md) | Accepted M0 boundary and M1 entry decisions |
| M2 | [Preparation, trading, and escape](m2-preparation-trading-escape.md) | M1 |
| M3 | [Character advancement](m3-character-advancement.md) | M1; integrate M2 reward/supply contracts |
| M4 | [Enemy progression](m4-enemy-progression.md) | M2/M3 for M4A; M5 for the M4B Floor III readiness proof |
| M5 | [Armor and accessories](m5-armor-accessories.md) | M1-M3 and accepted M4A |
| M6 | [Expeditions](m6-expeditions.md) | M5 and accepted M4B, including the first four-Drifter boss |
| M7 | [Momentum](m7-momentum.md) | Stable M3/M4 combat contracts; may precede M6 |
| M8 | [Region and content loop](m8-region-content-loop.md) | M1-M6; M7 only if selected for the release |
| M9 | [Release qualification](m9-release-qualification.md) | Accepted finite release manifest and preceding playable loops |

**Proposed Floor III delivery handoff:** M4A proves enemy systems with a playable Floor II slice and D3 recruitment. After M5, M4B supplies the bounded Floor III path, D4 recruitment, and first full-party boss proof needed by M6. This planning decomposition is for review: it is a delivery split of M4, not a new recruitment rule or a dependency on completing all M8 content. M6 supplies a minimal playable Floor IV expedition loop; M8 completes the approved region manifest.

## Shared Implementation And Qualification Contract

Every linked plan inherits this section. Baseline observations refer to `8099b895`, runtime schema 11, disk schema 12, profile envelope 1, and API `/v1`; re-read the actual constants and interfaces at milestone entry. The historical passing counts in `docs/probe.md` are not a fresh run or a target test count for these plans.

- Fixed requirements come from the roadmap and owning design. An example, possible mechanic, or provisional number does not become fixed merely because a plan mentions it. Record contradictions and secure approval at the affected gate before changing behavior.
- Preserve the Surface opening, 65-gold D2 recruitment, safe tutorial/reset exception, individual Dexterity turns, immediate reordering of unacted combatants, Floor I's ten battles/two rests, Recover staying at Rest, checkpoint no-rewind behavior, and Hub-return full HP/mana.
- Preserve Floor I rest extraction: half adjusted XP/gold, equal participant XP shares rounded down, fractional gold rounded up, all items kept. Preserve boss full banking and replay XP rates 50/40/30/20. These rules do not automatically define every later floor's exits or full-party boss XP.
- Preserve signature-weapon craft-and-install, exact Drifter IDs, separate slot improvement, 25/50/75/100 gates, Tier V state, identity recomputation, shared Crafting/materials, and no stackable signature-part ownership. No replacement weapon loot or alternate-part collection is introduced implicitly.
- One authoritative state object per recruited Drifter; persistent source state in existing snapshots/save documents; transient combat state in `CombatState`/Battle. Never persist duplicated derived stats or client-owned eligibility/reward rules.
- Extend schemas deliberately when source state changes. Validate before reconstruction, migrate defensive copies, verify historical envelope digests before migration, and leave historical remote revisions/digests immutable. Exercise current remote revision advancement. Do not preassign later schema numbers or change the envelope/API/database/provider architecture for convenience.
- Reject forged/stale inputs with no partial mutation. For operations involving required durable checkpoints, prove failed writes cannot spend twice, grant twice, change location, or restore a forfeited run. Use existing SavePort/coordinator boundaries; local saves remain independent of cloud availability.
- Each implementation gate follows a focused red/green test cycle, verifies its deliverable and client projection, and stops at its own scope. Test risk classes, not duplicate presentation details to inflate counts. Update the gate evidence before the next gate.
- Keep generated runtime/build/test outputs inside `root/` and existing ignored locations. Do not move source assets or restructure the package to make a milestone easier. Regenerate content/dataclass manifests through their tools rather than hand-editing them.

### Closure Checks

Run focused tests per gate. At milestone closure, from `root/`, run the following with the project's configured Python environment:

```text
python -m tools.validate_content
python tools/generate_content_catalog.py --check
python tools/generate_dataclass_manifest.py --check
python -m pytest
python -m pytest web_tests
python -m compileall src tests web_tests tools
python tools/build_browser_site.py --output web/dist
```

Install the existing locked browser test dependencies in `root/web_tests/` when needed, serve the built `root/web/dist/` using the existing smoke setup, then run `node web_tests/browser_smoke.mjs <local-built-site-url>` from `root/`. Do not count mocked bridge tests as the real reload/persistence proof. Use current terminal semantic inputs and a built-browser journey for the new flow, including valid/invalid exact-target actions and real save/reload; retain desktop and phone portrait/landscape usability. Do not put an entire campaign in every smoke case.

Run `python -m pytest tests` from `root/services/profile_api/` against a dedicated PostgreSQL database with the repository's test DB variables configured. Use a separate disposable migration database for `python -m alembic upgrade head` and `python -m alembic check`; never point destructive test fixtures at real player data. Follow `.github/workflows/tests.yml` for the current environment contract. Include schema advancement, immutable history, and relevant concurrency tests when shared persistence changes.

Run the actual pinned MicroPython qualification on the final gameplay/import/probe tree:

```text
python tools/runtime_qualification_matrix.py --python <configured-cpython> --micropython <verified-pinned-executable>
```

Use the recorded executable identity in `docs/probe.md`, not a similarly named stock binary. Cover the new semantic path in the real probe, default/native/overlay modes and semantic parity, plus three-run passing-pressure and lower-frontier observations. The present harness checks 608K/576K; neither is a product memory ceiling nor an immutable budget for later features. If the frontier changes, diagnose it and review the harness expectations with observed evidence; do not weaken assertions to manufacture a pass. Preserve marker protocols and historical measurements. A skipped runtime check must remain explicitly open.

Finish with `git diff --check`, content/manifest drift checks, a scoped cumulative review, and exact totals/SHA/CI links. Require green applicable hosted workflows for the pushed implementation SHA before sealing; a local test result or a prior SHA's green run is not final hosted evidence. Keep doc-only follow-ups distinguishable from runtime changes. These planning documents do not themselves execute any qualification or certify future behavior.

## Immediate Next Step

Review the nine plans, resolve M1's entry decisions, then authorize M1 alone. The original starting Drifter's narrative role versus active-slot identity remains a product decision; the planning pass does not decide it. Later decisions are scheduled at their owning gates rather than blocking all implementation up front.

# M3 Character Advancement Implementation Plan

> Implementation authorization: M3 work is approved on the existing `dungeon` branch. Execute gate by gate; preserve all behavior and save policy outside the explicit M3 contracts below.

**Status:** Gates 0-4 are implemented on the existing `dungeon` branch. M3-D1 through M3-D6 are resolved. Gate 4 passed exact-SHA hosted qualification, including hosted browser smoke and PostgreSQL/migration checks. Gate 5 implementation and local cumulative qualification are complete in the current working tree; exact-SHA hosted qualification remains pending. The pinned MicroPython matrix passed on this working tree.

**Goal:** Complete passive/move advancement, remaining Intuition consumers, split-damage capability, respecs, and permanent-discovery awards without rebuilding working stats or losing secured progress.

**Architecture:** Keep authored advancement requirements immutable, permanent purchase/source state on the exact Drifter, shared claim evidence at the appropriate game owner, and derived combat projections outside saves. Extend existing scaling/resolver/reward boundaries and M1 roster targeting.

**Tech stack:** Existing Python content/player/combat/session layers, semantic clients, validated save migration, pytest/Playwright and pinned runtime qualification.

## Authority, Dependencies, And Non-Goals

- [Roadmap](development-roadmap.md), M3 and shared constraints; [M1](m1-permanent-roster.md) exact roster identity; [M2](m2-preparation-trading-escape.md) supply/payout contracts where implemented.
- [Character growth](../../future/character-growth-and-stat-scaling.md), sole authority for individual advancement, prototype curves, and unresolved formulas.
- [M3 advancement blueprint](m3-advancement-blueprint.md), shared mechanical purpose for all 24 skill slots and character-specific authoring rules.
- [M3 Drifter skill content](m3-drifter-skill-content.md), authored names and conceptual purposes for all four 24-skill trees.
- [Economy](../../future/dungeon-progression-difficulty-and-economy.md), sole authority for securing/losing XP; [weapon design](../weapons/signature-weapon-progression.md), independent weapon investment/learned-technique contract.

Do not reimplement six stats, the Level 1 60-point budget, permanent caps, automatic HP/mana growth, levels, Growth Points, or stat spending. Non-goals: a new leveling architecture, resetting legacy builds, armor, Momentum, arbitrary campaign discovery placement, or weapon respec/refunds. The source's old milestone language does not authorize stripping existing kits.

## Verified Baseline And Missing Consumers

`root/src/app/player/progression.py` already defines three Growth Points per level, a 250 level cap, and a deterministic XP curve. `player/scaling.py` implements piecewise Constitution/Spirit resource curves, primary output, physical negation, accuracy/dodge, and Intuition helper curves. `PlayerState.gain_experience()` awards points and recalculates maxima; `increase_permanent_stat()` spends one point. Preserve these existing behaviors pending an approved change.

The resolver uses existing Strength/Dexterity/Intelligence output and Intuition critical/Super bonuses. Secured-XP bonuses are consumed at secured reward boundaries, and Gate 3 now has a controlled permanent-discovery claim service. Moves currently have independently resolved damage components under the Gate 2 contract. All authored kits are currently available, including Super. Weapon component effects are projected onto moves, and learned technique state exists in the signature-weapon model.

Gate 1 authors all 96 character-specific skill names/purposes and owns per-Drifter passive/active purchases plus four normal-move slots. Gate 2 projects the authored passive and move effects into combat. The Skills UI and terminal/browser advancement actions remain for Gate 5; Gate 3 owns secured-XP awards and permanent-discovery claims, while respec remains open.

## Fixed Contracts And Required State

Secured levels continue to grant three Growth Points per level; +1 permanent stat continues to cost one point. Do not change the existing level/stat systems. Each single-purchase passive costs 2 GP; all new active skills cost 3 GP. These prices are flat across tiers and skill types: capstones, mana techniques, and the additional Super have no premium.

Each Drifter receives 24 new GP-purchased skills: 18 single-purchase passive skills and six active skills (four mana techniques, one free/non-mana normal move, and one additional Super). "Free/non-mana" describes the move's combat resource cost; it is still purchased with GP. The new additional Super unlocks at Level 50 and remains in the Super system, outside the four normal-move slots. The character-specific concepts are authored in the linked skill-content document; effect details remain subject to Gate 2.

| Tier | Minimum character level | Passive skills | Active skills |
| --- | ---: | ---: | --- |
| I | 1 | 5 | 1 free/non-mana normal move |
| II | 25 | 4 | Mana Technique 1 |
| III | 50 | 4 | Mana Technique 2 and additional Super |
| IV | 75 | 4 | Mana Technique 3 |
| V | 100 | 1 capstone | Mana Technique 4 |

After a tier opens, its skills may generally be purchased in any order. Tier membership alone does not create prerequisite chains; add a specific prerequisite only when required by an authored skill. Mutually exclusive branches are not the default. Author skills using the primary/secondary identities defined from each Drifter's highest and second-highest authored Level 1 permanent stats in the Character Growth authority; effects should primarily scale from or enhance those stats, with other stats supporting specific mechanics where justified by the existing kit.

Each Drifter's normal-move loadout has four equipped slots. A GP-purchased normal or mana skill is permanently unlocked into that Drifter's available move pool and may then be equipped in one of those slots. The additional Super is separately tracked by the Super system. Keep permanently learned weapon techniques distinct from GP-purchased skills.

Legacy saves retain their current kits and continue normally. Migration must not remove existing move access, retroactively restrict a character, reset an equipped kit, or invent refunds/purchases because M3 begins tracking new advancement. Preserve existing access without fabricating purchase history.

Each selected Drifter owns permanent stats, unspent GP, purchased passive IDs, newly purchased active-skill IDs, and the equipped normal-move IDs. The initial M3 content has no multi-rank nodes or skill prerequisites. Authored skills own costs, level gates, any later justified prerequisites, and effect definitions. Catalog validation must reject unknown references, invalid costs/levels/kinds, impossible branches, and unsupported effects before gameplay.

Derive effects and available moves from validated source state plus authored content; never persist both a final modified stat and the same bonus as a passive. Affordability and eligibility are separate validations. Do not make every prerequisite category mandatory simply because it appears as an example in the design.

A mixed move resolves only the authored components that exist: physical staff/arrow components use Dexterity, heavy/blade use Strength, magical/elemental/alchemical components use their approved Intelligence/Intuition rules. Specify hit/crit/resource-charge timing, mitigation/Defend per component, status application, and integer rounding before implementation. One action cannot charge mana, consume a payload, grant Super, or apply a weapon modifier twice because it has multiple damage components. Unchanged legacy moves retain their outputs under the approved compatibility mapping.

Apply secured-XP bonuses once at the security boundary, after the approved payout/recipient calculation. Do not award levels from unsecured dungeon XP or apply the helper on every save/load. M3-D4 resolves personal Intuition and rounding order below. Surface encounter rewards are already secured and use their existing recipient policy; M3 does not force the Surface into a dungeon extraction ledger.

Permanent-discovery contract (M3-D6 resolved): an authored source has a unique source ID distinct from its type. Ancient Wells award authored +5 or +10 permanent max HP; Forgotten Altars award authored +5 or +10 permanent max Mana; Spirit Relics award exactly +3 GP. The player selects and confirms exactly one currently active Drifter. Cancellation changes nothing; a confirmed reward and durable source claim are saved together, and a repeated claim/reload cannot award again. No new HP, Mana, or GP cap is introduced. If a separately approved cap exists in the future, the player may cancel or consume-and-waste the source, never redirect it. M3 uses controlled source fixtures only; M8 owns actual release locations. Discovery probability consumption in real loot/search belongs to M4/M8, not a new RNG call in the scaling helper.

Respec operates only under the approved Hub eligibility/cost/refund rules. Validate the resulting prerequisite graph, available kit, GP accounting, and resource maxima before any debit/refund. Preserve levels, XP, weapons/components/material investment, permanent discovery awards, and already-learned weapon techniques unless a separately approved contract explicitly says otherwise.

## Integration And Persistence

Revalidate these current edit areas: `root/src/app/player/player_state.py`, `character.py`, `progression.py`, `scaling.py`, `root/src/app/combat/move.py`, `resolver.py`, `result.py`, and `root/src/app/game/party_state.py` reward banking. Add focused authored advancement/effect definitions and player-owned advancement state using existing content patterns; filenames/signatures are entry-time implementation choices.

Extend `OverworldSession`, Skills/Character presenter models, terminal inputs, and the browser bridge/renderer for exact-ID purchases, eligibility explanations, cost/effect previews, and respec confirmation. Clients never recalculate GP refunds or formulas. M2 Alchemy effects, signature component projections, and future M5 bonuses must share a documented effect composition order without making M3 depend on unreleased armor.

Use a deliberate forward save migration. Preserve every old Drifter's stats, unspent points, level, XP, resources, full-kit access under the approved policy, slot progress, Tier V, and learned techniques. Old saves lack a detailed purchase history; do not invent refundable spending or silently refund all stats to a newly authored starting distribution. Update trusted payload validation for prerequisites and IDs and prove legacy remote revision advancement without rewriting history. Gate 4 adds the per-Drifter purchased-stat ledger and respec count additively: current runtime schema is 16 and disk schema is 17. The profile API, envelope version, and database schema remain unchanged. Schema-16 saves migrate with zero tracked stat purchases and zero prior respecs; this records no invented purchase history.

## Review Focus

- Existing saves must not lose full-kit access or receive invented refunds; Gates 0/4 check the approved legacy policy and source immutability.
- Multi-component attacks must not debit resources or award Super twice; Gate 2 checks per-action accounting and old-move golden results.
- Unsecured XP, repeated extraction or reload must not apply Intuition bonuses twice; Gate 3 checks each payout path.
- Respec must not leave invalid prerequisites, negative GP or a nonfunctional kit; Gate 4 checks conservation and eligibility.
- Component-learned techniques and weapon investment must survive purchases/respec; Gates 1/4 check independent source ownership.

## Gates And Tests

### Gate 0 - Approve Arithmetic, Purchase, And Legacy Policies

- [x] Inventory existing curve callers and baseline fixtures; record where source prototypes match implementation and where adding a consumer changes outcomes.
- [x] Record the approved M3-D1 move-progression and M3-D2 tree-structure decisions, including preservation of legacy kits.
- [x] Record flat M3 prices: permanent stat 1 GP, single-purchase passive skill 2 GP, active skill 3 GP, with no tier, capstone, mana-technique, or additional-Super premium.
- [x] Record the universal P1-P18/A1-A6 slot blueprint; keep individual effects conceptual until the Gate 2 arithmetic contract is resolved.
- [x] Author all four character-specific skill trees in [M3 Drifter Skill Content](m3-drifter-skill-content.md). Names and tactical purposes are set; Gate 2 still owns numerical effects and unsupported mechanics.
- [x] Record the current-versus-M3 behavior baseline and additive migration examples below. Schema numbers for the advancement payload remain an implementation-entry choice.
- [x] Preserve existing approved progression formulas and do not reopen unrelated balance.

Gate 0 evidence: curve consumers are `Character` resource-maximum recalculation, `CombatResolver` output/negation/accuracy/dodge/crit/Super generation, and save-document canonical resource validation. The secured-XP, discovery, and special-potency helper functions currently have no production gameplay consumer. The focused baseline command `python -m pytest -q tests/test_player_scaling.py tests/test_player_state.py tests/test_overworld_session.py` from `root/` passed **89 tests**.

| Behavior | Current M1/M2 contract | M3 addition | Compatibility rule |
| --- | --- | --- | --- |
| Level and GP | Secured level awards 3 GP; level cap is 250. | Skill purchases spend the approved flat GP costs. | Preserve curve, level, current GP, and all past outcomes. |
| Permanent stats | Six permanent stats; +1 costs 1 GP; existing stat/resource curves apply. | Passives project effects separately from permanent stats. | No stat reset, formula replacement, or fabricated stat-spending history. |
| Starting moves | Each authored Drifter kit supplies its current normal moves and Super. | New normal/mana moves enter a permanent per-Drifter pool; four normal moves are equipped. | Existing kit and Super access remain available; initial equipment is the existing four normal moves. |
| Purchased advancement | No M3 passive or active purchase ledger exists. | Add exact-Drifter passive/active purchase state and equipped normal move IDs. | Old saves migrate with no purchased M3 IDs; no GP is charged or refunded. |
| Intuition consumers | Crit and Super generation are used in combat; secured-XP, discovery, and special-potency helpers have no production consumers. | Add only the consumers defined by their owning M3 gates. | Existing outputs and rewards stay unchanged until the relevant consumer is explicitly approved and tested. |
| Weapon state | Signature weapon, component, slot progress, Tier V, and learned techniques are independently persisted. | M3 skill state is separate. | No weapon progress, materials, component, or technique changes. |

The runtime snapshot was schema 13 and the disk save schema 14 at M3 entry.
Gate 1 selected runtime schema 14 and disk schema 15 for the additive
advancement state. The forward migration must not rewrite an old remote revision
or its digest. Its default advancement state has empty M3 passive/active
purchase lists and no spending history. The four already-authored normal moves
seed the four equipped slots; the original Super stays available outside those
slots. Existing stats, level, XP, unspent GP, current resources, shared/run
inventory, party roster, and signature-weapon state are copied without
adjustment.

**Gate 1 implementation checkpoint (complete):** `root/src/app/content/advancement_spec.py` authors all 96 approved names/purposes and shared tier/cost schedule; `root/src/app/player/advancement_state.py` and `PlayerState` own exact-Drifter purchases, unlocked move pools, and four-slot loadouts; disk schema 15 migrates schema-14 saves additively while retaining schema-14 profile history unchanged. Validation passed 1,918 root tests, 63 web tests, content validation, and Python compilation. The focused advancement/save-state set passed 90 tests. The web checks covered static packaging/contracts, not a Playwright gameplay journey. Real pinned MicroPython qualification remains for final M3 qualification. No combat effect projection, Skills UI, terminal/browser actions, secured-XP consumer, discovery claims, or respec has been implemented yet.

| Legacy Drifter example | Existing invested state to preserve | Additive M3 default |
| --- | --- | --- |
| Branoc | Level 137; STR 91, CON 97; 2 unspent GP; current Sunder-Spire state and full kit. | No purchased M3 nodes; current four normal moves equipped; Third Gate Obsequy remains available. |
| Azhvielle | Level 118; INT 99, SPI 88; 5 unspent GP; current weapon and full kit. | No purchased M3 nodes; current four normal moves equipped; Causality Nullwake remains available. |
| Zhaivra | Level 102; DEX 100, INTU 93; 0 unspent GP; current Sathren/payload state and full kit. | No purchased M3 nodes; current four normal moves equipped; Starless Meridian Obsequy remains available. |
| Joruun | Level 79; INT 88, DEX 91; 11 unspent GP; current Sky-Needle state and full kit. | No purchased M3 nodes; current four normal moves equipped; Coagulated Torrent remains available. |

These are migration fixtures, not grant examples. They demonstrate that high
stats, spent points (which are not reconstructed), unspent GP, current kits,
resources, and independent weapon investment survive without inferred purchases
or refunds.

### Gate 1 - Authored Advancement And Atomic Purchases

- [x] Prove permanent stat/passive/active costs of 1/2/3 GP, respectively, with no tier/type premium; prove level gates, ownership, duplicate purchase, unknown target, and insufficient points reject without mutation. The initial content intentionally has no ranks or skill prerequisites, so neither is implemented as an invented rule.
- [x] Implement and validate the complete 24-slot tree for each Drifter, exact-Drifter purchase state, permanent normal/Super unlock pools, and four-slot normal loadouts. Preserve the existing kit on migration and do not finalize Gate 2 effect numbers early.
- [x] Round-trip purchases and unlocked/equipped move IDs for active and bench members under M1 roster ownership without changing another Drifter.

Proof: `tests/test_advancement.py`, `tests/test_save_state.py`, and existing permanent-stat tests; 1,918 root tests, 63 web tests, content validation, compilation, and `git diff --check` passed. Web verification covered build packaging/contracts only; no browser gameplay flow or real pinned MicroPython run is claimed for Gate 1.

### Gate 2 - Damage Components And Remaining Potency

- [x] Add resolver golden cases for unchanged legacy moves and approved physical/magical/elemental/alchemical components, power-share mitigation, Defend, hit/critical outcomes, minimum damage, and exact rounding boundaries.
- [x] Implement only supported component/effect forms. Connect Intuition special potency to actual approved mechanics rather than applying it indiscriminately to all damage or healing.
- [x] Prove one resource debit, one payload use, one per-action Super award, one passive projection, and stable weapon component effects. Preserve Dexterity initiative and current ordinary hit/crit caps unless explicitly changed.

#### Gate 2 Damage Contract (Approved)

- A damage component has an authored identity, a physical or magical defense
  class, scaling attributes, and a positive base-power contribution. Identity
  is descriptive and future-facing; it does not introduce elemental or
  alchemical resistance in M3.
- Resolve each component through its applicable scaling and move/skill
  modifiers, then generic mitigation, applicable physical-only Strength
  negation, existing combat-state modifiers, Brace, and Defend, in that order.
  Brace and Defend apply independently to each component; Brace remains
  physical-only and Defend uses the component's defense class.
- Allocate generic mitigation by each component's share of the move's authored
  base power. First calculate the existing full class mitigation using its
  current integer rules (Constitution or Spirit divided by four, including
  existing Arcane Break adjustment); then multiply by that component's authored
  base-power share and floor. This preserves the mixed move's total mitigation
  budget instead of charging full physical and magical mitigation to both
  halves. The 50/50 legacy conversions may differ from the old averaged
  HYBRID result by at most one point from integer rounding.
- Floor each existing percentage operation at its current stage for each
  component. Components may resolve to zero, never negative damage. Sum the
  resolved integer component damages, apply the move's minimum of one once to
  that sum, then apply the existing critical multiplier once. Roll hit and
  critical once per move, not once per component.
- Rejected moves do not mutate resources, payloads, statuses, or combat state.
  Accepted moves retain the current action timing: resource spend and existing
  attempt-consumed setup occur before the hit roll; hit-dependent effects apply
  only after a hit and while their target remains alive. Preserve the existing
  Gravemantle miss behavior. Resource, setup, status, and Super effects resolve
  at most once per action, regardless of component count.
- Reuse current output curves: Strength/Dexterity physical output and
  Intelligence magical output. Intuition special potency is used only by an
  explicitly authored special/status effect, never as a generic damage or
  healing multiplier. Clamp inputs to scaling helpers at 100; direct mitigation
  continues to use the actual effective stat, including equipment bonuses.
- For the clearly mixed legacy attacks, preserve the existing total base power
  and split it evenly: Branoc's Third Gate Obsequy 12 physical + 12 magical;
  Joruun's Lightning Palm 12 physical + 12 elemental/lightning (magical
  defense); Goblin Lord's Tyrant's Ruin 13 physical + 13 magical. Retain
  legacy HYBRID handling for moves without a clearly authored second source,
  including Zhaivra's Starless Meridian Obsequy and Azhvielle's Gravemantle
  Rupture.
- Component identity does not itself apply a status. Existing and new
  secondary effects require an authored mechanic and use the action timing
  above. New skill coefficients remain conservative and are derived from the
  Gate 1 authored purposes; do not add resistance, redesign tree structure, or
  change GP, tier, purchase, loadout, or schema-15 ownership rules.

Proof: local qualification on the Gate 2 working tree passed 1,932 root tests, 63 web tests, content validation, compileall, the 132-entry dataclass manifest check, a 153-file browser build, and browser smoke. Hosted Gate 2 CI passed on base SHA `9d9c892fefdd8b91a3969938dbfb984fafbf3e96`; the current Gate 3 changes were not part of that run. At this Gate 2 checkpoint, Gate 5's advancement journey and pinned MicroPython requalification remained future work; see Gate 5 for the cumulative follow-through.

### Gate 3 - Secured XP And Permanent Awards

- [x] Extend reward tests for normal split, independent personal Intuition, partial extraction, replay multiplier, boss/full bank, Return Talisman, death, save/reload, and retry. Verify zero-bonus awards preserve prior totals.
- [x] Implement the secured-XP consumer after payout adjustment and recipient split. Apply it per eligible Drifter on dungeon banking and already-secured Surface encounter rewards; never award unsecured XP.
- [x] Resolve M3-D6 and implement authored permanent-discovery sources, active-party target selection, explicit confirmation/cancellation, one-time claim evidence, and atomic reward-plus-save behavior. Do not add new permanent HP/Mana/GP caps or world placements.
- [x] Verify each authored reward (HP/Mana +5/+10 and Spirit Relic +3 GP), both active targets, rejection of benched targets and malformed/unknown source IDs, cancellation, repeat/reload behavior, and unchanged state when persistence fails.
- [x] Record the M4/M8 handoff: M4/M8 owns discovery probability and resolves an outcome once; M8 owns source placement and authored source IDs. Presentation only offers an already-resolved source to the claim service and never rerolls. M3 adds no locations, search probabilities, or loot placement.

Gate 3 local verification at that checkpoint: **1,960 root tests** and **63 web tests** passed; content validation passed (5 enemies, 4 weapons, 4 Drifters, 10 encounters, 2 routes, 1 recruitment event), Python compilation passed, and `git diff --check` passed. The discovery service uses injected authored definitions and controlled fixtures; no release locations or search/drop probabilities are implemented in M3. Web tests then covered static packaging/contracts, not a browser gameplay journey. Hosted PostgreSQL and pinned MicroPython were not run for that checkpoint; see Gate 5 for cumulative qualification status.

### Gate 4 - Respec And Persistence Trust Boundary

- [x] Implement a full respec for exactly one selected recruited Drifter at `DungeonPhase.HUB`. Each Drifter has an independent first free use; each later confirmed use consumes exactly one `revision_parchment`. Merchant price, acquisition, and drop rules are not defined here.
- [x] Preview exact GP refund, removed stat/passive/active purchases, resulting stats/GP, and parchment cost before explicit confirmation. Cancellation, invalid target/phase, insufficient parchment, and failed save preserve the original game state.
- [x] Refund only ledgered M3 purchases at 1 GP per permanent stat point, 2 GP per passive, and 3 GP per active. Preserve unspent and discovery-awarded GP. Legacy saves receive no fabricated purchase or respec history.
- [x] Remove purchased passive/active ownership and any equipped move made unavailable by the respec; preserve legacy/independent move access and maintain the four-slot legal kit. Preserve level, XP, automatic growth, weapons, components, materials, weapon XP, learned techniques, discovery bonuses/claims, and all other Drifters.
- [x] Recalculate resource maxima from resulting permanent stats and clamp current HP/Mana to the new maxima without healing/refilling. Persist per-Drifter stat-purchase history and respec count under runtime schema 16 / disk schema 17; keep profile API, envelope, and database schemas unchanged.
- [x] Test exact refund and parchment accounting, independent free uses, cancellation/failure atomicity, invalid target/phase, save/reload/profile-sync no-duplicate behavior, preserved independent progression, resource clamping, and strict save validation.
- [x] Complete exact-SHA hosted qualification: PostgreSQL integration, migration-from-zero, Alembic parity, Python 3.14 full root suite, and hosted browser smoke. Gate 5 remains responsible for the playable terminal/browser respec journey.

**Gate 4 local evidence (working tree based on `d9d068f99a85ddcb6668726f537c1707184d605f`):** a fresh focused schema/respec bundle passed **136 tests** under Python 3.14.6, and web pytest passed **63 tests**. The full root suite reported **1,937 passed and 39 failed**; each failure occurred while a test attempted to spawn a child process and Windows returned `WinError 6` for an invalid handle, before that child-process behavior could be exercised. The repository's hosted workflow also uses Python 3.14, but this local runner result is not counted as a green full suite.


**Gate 4 hosted qualification (exact commit `410ed240f284d79ab37daf7211f9b0d60e409d45`; [Actions run 41969940820](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/41969940820)):** both hosted jobs passed. The hosted Python 3.14 suite passed **1,976 root tests** and **63 web tests**; the PostgreSQL service suite passed **37 tests**. Content validation, compilation, the 156-file browser build, Chromium smoke, migration from zero, and Alembic model parity passed. Gate 4 is hosted-qualified. The local Windows child-process `WinError 6`, unavailable local Chromium executable, and incompatible local `pydantic_core` wheel are historical environment diagnostics, not outstanding Gate 4 blockers. Pinned MicroPython was not run and remains part of cumulative qualification.

No production behavior outside the approved respec/state/migration contract was changed.

### Gate 5 - Playable Advancement And Qualification

- [x] Prove the terminal journey through its real input/render adapter: target a Drifter, purchase passive/active skills, equip the move, save/load, and confirm Hub respec with preserved weapon state. The built-browser journey additionally proves the equipped move's real combat effect, save/reload, and respec conservation.
- [x] Retain compact mobile Skills/Character navigation and desktop information; extend the pinned probe with a bounded purchase/effect/round-trip path.
- [x] Run local cumulative qualification: 1,983 root tests, 65 web tests, content validation, compileall, 156-file browser build, full Playwright smoke, and the pinned MicroPython matrix (816K stable pass 3/3; 784K expected memory limit 3/3).
- [ ] Run exact-SHA hosted checks, including PostgreSQL integration, migration-from-zero, Alembic parity, and hosted browser smoke. Record discoveries as controlled system fixtures pending M8; no real discovery locations are claimed.

Gate 5 local evidence is recorded in [Probe Notes](../../probe.md). The current tree is based on `410ed240f284d79ab37daf7211f9b0d60e409d45` and remains uncommitted. Docker was unavailable in the local environment, so PostgreSQL/migration checks were not rerun locally. M3 is not sealed until the exact pushed revision passes hosted CI.

Closure: all four Drifters have the approved functioning initial advancement path, real potency/secured-XP consumers, safe respec, and trusted persistence. M4/M8 remain responsible for real search/loot placement; M7 is separate temporary Momentum.

## Unresolved Product Decisions

| ID | Decision and blocking gate |
| --- | --- |
| M3-D1 | Resolved structure: new normal/mana skills are GP-purchased and permanently unlocked per Drifter; four equipped normal-move slots; additional Super remains outside those slots and unlocks at Level 50; preserve legacy kits. |
| M3-D2 | Resolved structure, pricing, shared slot purposes, and character-specific concept list in the [M3 blueprint](m3-advancement-blueprint.md) and [M3 Drifter Skill Content](m3-drifter-skill-content.md): 24 skills per Drifter (18 single-purchase passives, six actives), tiers/counts at Levels 1/25/50/75/100, permanent stat 1 GP, passive 2 GP, active 3 GP, no premiums. Conservative initial mechanics are authored for Gate 2; later balance review may tune their coefficients. The initial trees have no skill prerequisites. |
| M3-D3 | Resolved for Gate 2 by the approved [damage contract](#gate-2-damage-contract-approved): component floor/rounding, action-level hit/critical and resource timing, power-share mitigation, scaling-helper cap, and conservative migration of clearly mixed legacy moves. |
| M3-D4 | **Resolved:** calculate the secured pool after existing replay/extraction/talisman/boss rules; split it among eligible Drifters; then apply each Drifter's own `secured_xp_bonus_bps_from_intuition()` to their share. Floor each bonus independently. Never average party Intuition, apply the bonus before splitting, or recalculate it on reload/retry. Zero-bonus totals remain unchanged. Any later expedition handoff follows this same per-Drifter secured-award rule. |
| M3-D5 | **Resolved:** full rebuild for one selected recruited Drifter at the Hub; first respec free per Drifter, later respecs cost one Revision Parchment each; exact refunds for ledgered stats/passives/actives at 1/2/3 GP; preserve unspent/discovery GP and all independent/legacy progression; no partial respecs or fabricated legacy purchase history; explicit preview/confirmation; candidate-state save atomicity; clamp current HP/Mana after recalculation without refill. Merchant price and item acquisition remain undefined; see Gate 4 implementation record. |
| M3-D6 | **Resolved:** Ancient Well +5/+10 permanent max HP; Forgotten Altar +5/+10 permanent max Mana; Spirit Relic +3 GP. One player-selected currently active Drifter per unique authored source ID; explicit confirm; cancellation leaves the source; reward and claim persist atomically; repeated claims never award again. No new resource or GP cap. If a separately approved cap is added later, the player may cancel or consume-and-waste without redirect. Controlled fixtures only; M8 owns placements and M4/M8 own discovery probabilities. |
| M3-D7 | Any change to level 250, current XP/HP/mana/output curves or caps; explicit review only, otherwise preserve current code |

Actual file/API details will be revalidated at M3 entry; fixed GP costs and secured-versus-unsecured boundaries do not become provisional during that check.

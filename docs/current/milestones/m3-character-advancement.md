# M3 Character Advancement Implementation Plan

> Implementation method: use `superpowers:executing-plans` for native gate-by-gate execution. Planning only; no progression or existing-save policy changes are authorized here.

**Status:** Draft for review, 2026-10-29. Revalidate exact APIs after M1/M2; do not mistake the historical word "future" for evidence a system is missing.

**Goal:** Complete passive/move advancement, remaining Intuition consumers, split-damage capability, respecs, and permanent-discovery awards without rebuilding working stats or losing secured progress.

**Architecture:** Keep authored advancement requirements immutable, permanent purchase/source state on the exact Drifter, shared claim evidence at the appropriate game owner, and derived combat projections outside saves. Extend existing scaling/resolver/reward boundaries and M1 roster targeting.

**Tech stack:** Existing Python content/player/combat/session layers, semantic clients, validated save migration, pytest/Playwright and pinned runtime qualification.

## Authority, Dependencies, And Non-Goals

- [Roadmap](development-roadmap.md), M3 and shared constraints; [M1](m1-permanent-roster.md) exact roster identity; [M2](m2-preparation-trading-escape.md) supply/payout contracts where implemented.
- [Character growth](../../future/character-growth-and-stat-scaling.md), sole authority for individual advancement, prototype curves, and unresolved formulas.
- [Economy](../../future/dungeon-progression-difficulty-and-economy.md), sole authority for securing/losing XP; [weapon design](../weapons/signature-weapon-progression.md), independent weapon investment/learned-technique contract.

Do not reimplement six stats, the Level 1 60-point budget, permanent caps, automatic HP/mana growth, levels, Growth Points, or stat spending. Non-goals: a new leveling architecture, resetting legacy builds, armor, Momentum, arbitrary campaign discovery placement, or weapon respec/refunds. The source's old milestone language does not authorize stripping existing kits.

## Verified Baseline And Missing Consumers

`root/src/app/player/progression.py` already defines three Growth Points per level, a 250 level cap, and a deterministic XP curve. `player/scaling.py` implements piecewise Constitution/Spirit resource curves, primary output, physical negation, accuracy/dodge, and Intuition helper curves. `PlayerState.gain_experience()` awards points and recalculates maxima; `increase_permanent_stat()` spends one point. Preserve these existing behaviors pending an approved change.

The resolver uses existing Strength/Dexterity/Intelligence output and Intuition critical/Super bonuses. Special-potency, secured-XP, and discovery helper functions exist; code inspection found no gameplay consumers for those helpers. Moves currently have one power/damage type and scaling attributes, not independently resolved damage packets. All authored kits are currently available, including Super. Weapon component effects are projected onto moves, and learned technique state exists in the signature-weapon model.

No authored passive tree, paid move-unlock flow, GP purchase ledger/respec policy, or real permanent-resource discovery flow is implemented. A helper or serialization field alone is not a delivered consumer.

## Fixed Contracts And Required State

Secured levels grant three points; +1 permanent stat costs one, a passive node/rank costs two, and a move costs three. Affordability and eligibility are separate validations. A kit's intended shape is four normal moves plus one Super; starting moves/unlock order and existing-save policy must be approved before restricting moves.

Each selected Drifter owns permanent stats, unspent GP, purchased passive node/rank IDs, purchased/unlocked move IDs, and any approved spending/refund evidence. Authored nodes own costs, max ranks, prerequisites, mutually exclusive branches if selected, and effect definitions. Catalog validation rejects cycles, unknown references, invalid ranks/costs, impossible branches, and unsupported effects before gameplay.

Derive effects and available moves from validated source state plus authored content; never persist both a final modified stat and the same bonus as a passive. Keep permanently learned weapon techniques distinct from GP-purchased moves and their refund ledger. Do not make every prerequisite category mandatory simply because it appears as an example in the design.

A mixed move resolves only the authored components that exist: physical staff/arrow components use Dexterity, heavy/blade use Strength, magical/elemental/alchemical components use their approved Intelligence/Intuition rules. Specify hit/crit/resource-charge timing, mitigation/Defend per component, status application, and integer rounding before implementation. One action cannot charge mana, consume a payload, grant Super, or apply a weapon modifier twice because it has multiple damage components. Unchanged legacy moves retain their outputs under the approved compatibility mapping.

Apply secured-XP bonuses once at the security boundary, after the approved payout/recipient calculation. Do not award levels from unsecured dungeon XP or apply the helper on every save/load. Personal versus party Intuition and rounding order are product decisions. Surface rewards currently awarded directly are already secured; M3 must not force the Surface into a dungeon extraction ledger.

Permanent discoveries need an authored source ID, eligible target/scope, award value/cap, and durable claim evidence paired with the award. Implement the claim service with controlled content in M3; M8 owns actual release locations. A repeated claim/reload cannot award again. Discovery probability consumption in real loot/search belongs to M4/M8, not a new RNG call in the scaling helper.

Respec operates only under the approved Hub eligibility/cost/refund rules. Validate the resulting prerequisite graph, available kit, GP accounting, and resource maxima before any debit/refund. Preserve levels, XP, weapons/components/material investment, permanent discovery awards, and already-learned weapon techniques unless a separately approved contract explicitly says otherwise.

## Integration And Persistence

Revalidate these current edit areas: `root/src/app/player/player_state.py`, `character.py`, `progression.py`, `scaling.py`, `root/src/app/combat/move.py`, `resolver.py`, `result.py`, and `root/src/app/game/party_state.py` reward banking. Add focused authored advancement/effect definitions and player-owned advancement state using existing content patterns; filenames/signatures are entry-time implementation choices.

Extend `OverworldSession`, Skills/Character presenter models, terminal inputs, and the browser bridge/renderer for exact-ID purchases, eligibility explanations, cost/effect previews, and respec confirmation. Clients never recalculate GP refunds or formulas. M2 Alchemy effects, signature component projections, and future M5 bonuses must share a documented effect composition order without making M3 depend on unreleased armor.

Use a deliberate forward save migration. Preserve every old Drifter's stats, unspent points, level, XP, resources, full-kit access under the approved policy, slot progress, Tier V, and learned techniques. Old saves lack a detailed purchase history; do not invent refundable spending or silently refund all stats to a newly authored starting distribution. Update trusted payload validation for prerequisites/ranks/IDs and prove legacy remote revision advancement without rewriting history. New schema numbers are chosen from the entry tree, not assigned now.

## Review Focus

- Existing saves must not lose full-kit access or receive invented refunds; Gates 0/4 check the approved legacy policy and source immutability.
- Multi-component attacks must not debit resources or award Super twice; Gate 2 checks per-action accounting and old-move golden results.
- Unsecured XP, repeated extraction or reload must not apply Intuition bonuses twice; Gate 3 checks each payout path.
- Respec must not leave invalid prerequisites, negative GP or a nonfunctional kit; Gate 4 checks conservation and eligibility.
- Component-learned techniques and weapon investment must survive purchases/respec; Gates 1/4 check independent source ownership.

## Gates And Tests

### Gate 0 - Approve Arithmetic, Purchase, And Legacy Policies

- [ ] Inventory existing curve callers and baseline fixtures; record where source prototypes match implementation and where adding a consumer changes outcomes.
- [ ] Resolve M3-D1/D2 and the legacy compatibility boundary for the first slice. Schedule D3-D6 at their owning gates; freeze damage/award composition, rounding and respec rules before implementing those behaviors, not through invented defaults.
- [ ] Keep approved prototype numbers editable and unchanged unless a specific numerical revision is approved; do not reopen all balance simultaneously.

Proof: a current-versus-new behavior table and versioned migration examples for all four authored Drifters, including heavily invested legacy builds.

### Gate 1 - Authored Advancement And Atomic Purchases

- [ ] Add failing tests for one stat costing 1, passive/rank costing 2, and move costing 3; unmet level/stat/story/node prerequisites, invalid rank, duplicate purchase, unknown target, and insufficient points must leave state identical.
- [ ] Implement definitions, validation, player source state, and domain purchase actions. Author one useful bounded progression path per Drifter after approval; no empty trees counted as content.
- [ ] Round-trip purchases and derived legal moves/effects using M1 exact targets, including a bench member and an active member without changing the other.

Proof: focused additions to existing progression/player/Skills tests plus a small proposed advancement-content module test file; run applicable content/catalog/manifest checks.

### Gate 2 - Damage Components And Remaining Potency

- [ ] Add resolver golden cases for unchanged legacy moves and approved new physical+magic/elemental/alchemical composition, independent mitigation, Defend, hit/critical outcomes, min/max values, and exact rounding boundaries.
- [ ] Implement only supported component/effect forms. Connect Intuition special potency to actual approved mechanics rather than applying it indiscriminately to all damage or healing.
- [ ] Prove one resource debit, one payload use, one per-action Super award, one passive projection, and stable weapon component effects. Preserve Dexterity initiative and current ordinary hit/crit caps unless explicitly changed.

Proof: existing resolver/character-mechanic/Battle regressions plus focused component tests pass; costs and outcomes are observable in terminal and bridge projections.

### Gate 3 - Secured XP And Permanent Awards

- [ ] Extend Floor I reward tests for death, partial extraction, replay multiplier, boss, and talisman ordering. Pin exact approved personal/party Intuition rounding; retries/load do not multiply bonuses.
- [ ] Implement the secured-XP consumer at its single owner and permanent-discovery award/claim pairing with controlled authored sources. Test repeated claim, wrong target, cap, malformed save, and failed required write.
- [ ] Specify the M4 loot-discovery hook and M8 placement contract semantically: probabilities/outcomes are resolved once by the owner, not rerolled on presentation.

Proof: original zero-bonus rewards remain unchanged; a real approved nonzero bonus/claim changes only the intended Drifter/source once.

### Gate 4 - Respec And Persistence Trust Boundary

- [ ] Test refund/cost conservation, dependency cascades, minimum functional move kit, legacy purchase evidence, equipped move validity, and HP/mana maximum changes under the approved current-resource rule.
- [ ] Implement the service only after its policy is approved. Reject a respec that would leave invalid prerequisites or exceed the refund budget before spending/refunding anything.
- [ ] Round-trip all advancement state, reject invalid purchased IDs/ranks/claims at profile validation, and prove current remote progression advances while old schema/digest history stays immutable.

Proof: exact per-Drifter save/reload and real service coverage; no weapon material, progress, Tier V, or technique reset/refund.

### Gate 5 - Playable Advancement And Qualification

- [ ] Terminal/built-browser journey: gain secured GP -> buy passive/move -> inspect changed legal kit -> use its real effect -> save/reload -> approved Hub respec -> verify conservation and weapon preservation.
- [ ] Retain compact mobile Skills/Character navigation and desktop information; extend the real probe with a bounded purchase/effect/round-trip path.
- [ ] Run shared cumulative qualification and exact-SHA hosted checks. Record which discoveries are system-only controlled fixtures pending M8; do not claim real location content exists yet.

Closure: all four Drifters have the approved functioning initial advancement path, real potency/secured-XP consumers, safe respec, and trusted persistence. M4/M8 remain responsible for real search/loot placement; M7 is separate temporary Momentum.

## Unresolved Product Decisions

| ID | Decision and blocking gate |
| --- | --- |
| M3-D1 | Starting moves, Super unlock, move equip/selection rules, and new-game versus existing-save access; Gate 0 |
| M3-D2 | Initial passive trees/ranks, exclusivity and prerequisites, actual move purchase list; before Gate 1 |
| M3-D3 | Component composition, mixed mitigation, rounding, effect ordering, and effective-stat cap treatment beyond permanent 100; before Gate 2 |
| M3-D4 | Personal/party Intuition XP, bonus basis and rounding, including expedition handoff; before Gate 3 |
| M3-D5 | Respec existence/eligibility/cost/refunds and legacy spending evidence policy; before Gate 4; recommendation is not historical approval |
| M3-D6 | Permanent award scope/limits, resource changes, and claim security point; before Gate 3 |
| M3-D7 | Any change to level 250, current XP/HP/mana/output curves or caps; explicit review only, otherwise preserve current code |

Actual file/API details will be revalidated at M3 entry; fixed GP costs and secured-versus-unsecured boundaries do not become provisional during that check.

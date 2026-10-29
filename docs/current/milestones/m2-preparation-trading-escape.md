# M2 Hub Preparation, Trading, And Escape Tools Implementation Plan

> Implementation method: use `superpowers:executing-plans` for native gate-by-gate execution. Planning only; no gameplay change or publishing is authorized here.

**Status:** Draft for review, 2026-10-29. Semantic contracts are specified now; revalidate repository details after M1.

**Goal:** Make preparation, carried supplies, merchant transactions, and emergency escape a complete playable economy loop without weakening extraction risk.

**Architecture:** Extend the existing party inventory/reward owners and session/Battle action boundaries. Shared secured gold funds preparation; Python owns stock, costs, carrying rules, consumption, outcome preparation, and commits. Alchemy stays separate from weapon Crafting.

**Tech stack:** Existing Python content/runtime, semantic terminal/browser adapters, versioned saves, pytest/Playwright and the qualification stack in the roadmap.

## Authority, Dependencies, And Scope

- [Roadmap](../development-roadmap.md), M2 and the shared implementation/qualification contract.
- [Economy design](../../future/dungeon-progression-difficulty-and-economy.md), Extraction Methods, Hub Trader, Healing Potions, Gold, and unresolved rules.
- [Party design](../../future/party-and-expedition-core-loop.md), preparation and participant ownership.
- [M1](m1-permanent-roster.md) supplies recruited/active IDs and exact-target actions; [M3](m3-character-advancement.md) later consumes secured XP and potency hooks; [M5](m5-armor-accessories.md) adds actual equippable inventory, not M2.

Goals: authored buy/sell stock, secured-versus-carried-versus-found accounting, one potion loop, smoke bombs, return talismans, and a small separate Alchemy recipe loop. Non-goals: armor, energy, payments, unlimited recipe authoring, removing existing Heal, changing weapon ownership, or implementing every illustrative trader service. No full roster is granted by this work.

## Current Implementation And Missing Work

At `8099b895`, `PartyState` has secured shared gold/item stacks and `OutingRewards`; `WeaponProgressionService` spends secured materials at the Hub. There is no general buy/sell stock model, carry-capacity accounting, potion inventory use, or smoke/talisman resolution. `InventoryActionResolver`, `run_items.py`, and `CharacterRunState` already implement character-owned ingredient preparation and infused payloads; they are not a general Alchemy profession.

`OverworldSession._persist_floor_one_rest_fallback()` and related outcome helpers prevent loading a Rest save to resurrect a forfeited run. `Battle` has semantic inventory inputs and rejected actions do not consume a turn. The normal Escape affordance is not a finished smoke-bomb system. Extend these boundaries rather than faking victory or adding JavaScript inventory state.

## Canonical Behavior And Ownership

| Owner | Required source state/behavior |
| --- | --- |
| Party/Hub storage | Secured gold, stored supply quantities, stock state if finite, separately identified Alchemy progress if approved |
| Deployment/run | Loaded supply counts and provenance, consumption, newly found unsecured loot, approved carry limits; no double ownership between storage and carried bags |
| Selected Drifter | Exact item target and character-specific prepared payloads; target must be recruited and eligible under the approved action rules |
| Authored content | Stable item/recipe/stock IDs, prices, availability predicates, max counts, effects, source/yield/consumption policy |
| Battle/session | Valid action window, turn cost, escape versus victory, current route after escape, and prepared durable run-ending outcome |

A purchase validates current stock, unlock, positive integer quantity, total cost, funds, and capacity before changing anything. Sale validates actual eligible ownership and provenance before removing items or granting gold. No negative prices, boolean quantities, invented items, or unsecured-to-secured laundering. Whether carried secured supplies are at risk is M2-D1, not a deduction from the death rule for newly found loot.

Potion use consumes once, applies the approved healing amount to the exact legal target, and respects the carrying limit. Resolve use at full HP, use on a defeated member, and in/out-of-combat turn costs at Gate 0; do not quietly turn a potion into revival or a free action. Existing Heal and its cooldown remain distinct.

Smoke bombs guarantee escape from an eligible current encounter, consume one, preserve the run, and do not count as a kill or award encounter loot/XP. Decide boss exclusions and post-escape location before integration. A return talisman consumes one and ends the run: bank eligible unsecured XP, abandon unsecured gold/loot/materials, return to the fully restored Hub. Its payout is not the Floor I Rest half-payout; preserve replay XP adjustments and later M3 bonus ordering exactly once. Combat legality is unresolved until approved.

Floor I authorized Rest extraction still pays half adjusted XP/gold and keeps items; boss completion banks full eligible rewards. General economy prose about normal extraction does not override that sealed rule. Do not apply the Floor I partial rule to all future exit types without content/design approval.

Alchemy recipes use actual ingredients and explicit outputs/awards; infusion preparation remains character-correct. Alchemy awards never increment weapon Crafting merely because both consume materials. Ingredient/payload consumption and shared versus personal Alchemy progression must be approved, not inferred from the weapon system.

## Repository Integration And Persistence

Expected edit areas, revalidated at entry: `root/src/app/game/party_state.py`, `overworld_session.py`, `root/src/app/player/character_run_state.py`, `run_items.py`, `inventory_action.py`, `root/src/app/combat/battle.py`, content/catalog and validation tooling. Add narrowly scoped transaction/recipe definitions alongside existing game/content modules if needed; exact new filenames/APIs are entry decisions, not existing dependencies.

Extend overworld/battle input models, presenters, `terminal_overworld_ui.py`/`terminal_battle_ui.py`, `root/web/python/dd_bridge.py`, and `root/web/play/js/pyd4.js`. Both clients must show stored/carried/newly found quantities, selected target, buy/sell totals, consumption, blocked reasons, and escape consequences before confirmation. Backend revalidates submitted IDs/quantities even if a button was offered earlier.

Persist new source state through the normal migration chain; old saves receive empty/new-system defaults without taking their secured items or retroactively consuming supplies. Preserve immutable remote history and update current profile validation. Do not serialize content prices as player authority or add stock to account entitlements.

Before a required run-ending outcome becomes visible, durably replace the prior rewindable checkpoint using the established safe-outcome approach. If a required write fails, do not consume a talisman while remaining in a live run or bank XP while leaving loot available. Validate/precompute outcomes before spending; test storage failure and retries across reconstruction. Do not promise arbitrary crash-time exactly-once behavior without a specified committed state transition.

## Review Focus

- Loading must not restore already spent carried supplies into secured storage; Gates 1/3 check conservation and restart outcomes.
- A smoke escape must not trigger victory rewards or complete a route node by accident; Gate 3 checks the approved transition.
- A talisman must not become a full-loot extraction or consume itself without an accepted outcome; Gate 3 checks payout and failed writes.
- Forged/stale quotes and exact-target item requests must not spend gold or heal the wrong Drifter; Gates 1/2 check zero mutation.
- Alchemy must not award weapon Crafting or duplicate prepared payloads; Gate 2 checks the actual recipe consumer and round-trip.

## Gates And Proof

### Gate 0 - Approve Outcome And Content Tables

- [ ] Resolve entry-blocking M2-D1/D6 for trading/carrying; schedule the remaining decisions before their named gates. Record approved legal contexts/targets, turn costs, capacities, and the transition/payout matrix as each item is selected.
- [ ] Select a small authored stock/recipe list and configurable provisional prices/yields. Map recipe outputs to real item consumers. Review supply debit/return and save-failure sequencing before coding.

Proof: no ambiguous item outcome reaches implementation. Ordinary numeric tuning remains configurable, not an exhaustive balance exercise.

### Gate 1 - Storage, Carrying, And Merchant Transactions

- [ ] Red/green domain tests, proposed `root/tests/test_hub_trading.py`/`test_run_supplies.py`: exact purchase/sale, insufficient funds, full capacity, invalid quantities, unavailable stock, stale quotes, and no partial inventory/gold mutation.
- [ ] Implement provenance/carry preparation through the M1 roster boundary. Verify secured storage and the loaded bag cannot both contain the same debited supply.
- [ ] Add snapshot validation and migration tests as part of the feature, including carry quantities exceeding approved limits and invalid item references.

Proof: buy -> pack -> save -> reload -> unpack/sell yields exact conserved quantities/gold. No new Drifter is recruited.

### Gate 2 - Potion Use And First Alchemy Recipes

- [ ] Extend inventory/Battle tests with the approved exact target, healing cap, full-HP/dead-target rules, turn cost, and stale repeated input behavior; verify actor resources/prepared payloads are not taken from the original lead.
- [ ] Implement the small approved Alchemy contract and real potion/arrow/intermediate recipes with ingredient validation and atomic outputs. Keep legacy infusion behavior covered in `test_inventory_action_resolver.py` and relevant existing run-state tests after verifying their filenames at entry.
- [ ] Round-trip Alchemy source state and consumed supplies; prove no weapon Crafting XP is awarded by an Alchemy-only action.

Proof: craft -> carry -> use with visible effect in terminal and Python bridge; unsupported recipes/items reject without spending.

### Gate 3 - Escape And Durable Run Outcomes

- [ ] Add a transition matrix in existing Floor I/Battle tests plus focused escape tests: smoke does not award victory, normal encounter outcomes remain unchanged, talisman keeps only eligible XP, and spent items are not returned through outcome retry.
- [ ] Implement approved escape legality/route behavior without calling the ordinary victory reward path. Extend required checkpoint writes to include correct supply consumption and source state.
- [ ] Inject failed writes before/during outcome installation, reconstruct a fresh coordinator/session, and prove no duplicate XP, free talisman, resurrected loot, or defeated-run rewind. Death/rest/boss behavior remains unchanged.

Proof: earned loot -> emergency exit -> fresh load returns exactly the accepted Hub/run outcome. Include a post-smoke next encounter under the approved route rule.

### Gate 4 - Client Parity And Qualification

- [ ] Terminal and bridge tests compare legal buy/sell/craft/use/escape offers and exact target/outcome projections; disabled reasons reflect authoritative state.
- [ ] Built Playwright journey: prepare supplies at Hub, consume in battle, reach Rest, Recover and still Extract, save/reload, and verify quantities/gold/XP. Exercise smoke and talisman in bounded additional journeys; do not replay the entire campaign for each item edge case.
- [ ] Check mobile and desktop overflow/navigation. Extend the real probe with a bounded transaction/use/outcome round-trip, then run shared cumulative qualification, PostgreSQL/migrations, review, and exact-SHA hosted checks.

Closure: a real preparation -> play -> loss/extraction -> restock loop is available in both clients, with atomic spending and no-rewind outcomes. Armor, payments, expansive recipe catalogs, and later floor content remain outside M2.

## Unresolved Product Decisions

| ID | Decision and blocking gate |
| --- | --- |
| M2-D1 | Shared/per-Drifter capacity, loading/unloading, brought-in supply and carried-gold loss policy; Gate 0 |
| M2-D2 | Potion healing/targets, full-HP/dead-member behavior, combat turn cost and use locations; Gate 0 |
| M2-D3 | Smoke boss restrictions, use window, and post-escape route state; before Gate 3 |
| M2-D4 | Return-talisman name and combat legality; before Gate 3; XP-only retention itself is fixed |
| M2-D5 | Alchemy ownership/progression, initial recipes and compound consumption; before Gate 2 |
| M2-D6 | Finite versus replenished stock and unlock rules; Gate 0. Prices are explicitly provisional content values |
| M2-D7 | Future-floor extraction/quest-item exceptions; M8 entry, not permission to change Floor I now |

Later APIs and schema numbers must be revalidated at M2 entry. No unapproved answer in this table is silently selected by the plan.

# M2 Hub Preparation, Trading, And Escape Tools Implementation Plan

> Implementation method: execute the approved gates on the existing `dungeon` branch. This plan does not authorize branch creation, commits, or publishing.

**Status:** Gate 0 approved, 2026-10-31. M2 implementation and local qualification are complete on the uncommitted `dungeon` working tree based on `4324b35ae21233ddc03901e5376aebd0dc32d831`. Runtime save schema is 13 and disk schema is 14. PostgreSQL/migration and exact-SHA hosted qualification remain pending; Docker is currently unavailable in this environment. Content quantities and prices below are provisional and configurable.

**Goal:** Make preparation, carried supplies, merchant transactions, and emergency escape a complete playable economy loop without weakening extraction risk.

**Architecture:** Extend the existing party inventory/reward owners and session/Battle action boundaries. Shared secured gold funds preparation; Python owns stock, costs, carrying rules, consumption, outcome preparation, and commits. Alchemy stays separate from weapon Crafting.

**Tech stack:** Existing Python content/runtime, semantic terminal/browser adapters, versioned saves, pytest/Playwright and the qualification stack in the roadmap.

## Authority, Dependencies, And Scope

- [Roadmap](development-roadmap.md), M2 and the shared implementation/qualification contract.
- [Economy design](../../future/dungeon-progression-difficulty-and-economy.md), Extraction Methods, Hub Trader, Healing Potions, Gold, and unresolved rules.
- [Party design](../../future/party-and-expedition-core-loop.md), preparation and participant ownership.
- [M1](m1-permanent-roster.md) supplies recruited/active IDs and exact-target actions; [M3](m3-character-advancement.md) later consumes secured XP and potency hooks; [M5](m5-armor-accessories.md) adds actual equippable inventory, not M2.

Goals: authored buy/sell stock, secured-versus-carried-versus-found accounting, one potion loop, smoke bombs, return talismans, and a small separate Alchemy recipe loop. Non-goals: armor, energy, payments, unlimited recipe authoring, removing existing Heal, changing weapon ownership, or implementing every illustrative trader service. No full roster is granted by this work.

## Current Implementation And Missing Work

At M2 entry, `PartyState` has secured shared gold/item stacks and `OutingRewards`; `WeaponProgressionService` spends secured materials at the Hub. There is no general buy/sell stock model, carry-capacity accounting, potion inventory use, or smoke/talisman resolution. `InventoryActionResolver`, `run_items.py`, and `CharacterRunState` already implement character-owned ingredient preparation and infused payloads; they are not a general Alchemy profession.

`OverworldSession._persist_floor_one_rest_fallback()` and related outcome helpers prevent loading a Rest save to resurrect a forfeited run. `Battle` has semantic inventory inputs and rejected actions do not consume a turn. The normal Escape affordance is not a finished smoke-bomb system. Extend these boundaries rather than faking victory or adding JavaScript inventory state.

## Canonical Behavior And Ownership

| Owner | Required source state/behavior |
| --- | --- |
| Party/Hub storage | Secured gold and stored item quantities; no M2 stock depletion or Alchemy level/XP |
| Deployment/run | One shared active-party pack with capacity six individual units; loading debits Hub storage, use debits pack, safe return deposits unused supplies, and death destroys remaining carried supplies. Unsecured encounter rewards are separate from pack capacity. |
| Selected Drifter | Exact item target and character-specific prepared payloads; target must be recruited and eligible under the approved action rules |
| Authored content | Stable item/recipe/stock IDs, prices, availability predicates, max counts, effects, source/yield/consumption policy |
| Battle/session | Valid action window, turn cost, escape versus victory, current route after escape, and prepared durable run-ending outcome |

A static authored merchant offers unlimited stock in M2. Buying and selling use secured Hub storage only: purchases enter storage, never the pack; sales debit storage and accept only explicitly sellable item IDs. Sell value is `floor(base_price / 2)`. Validate positive integer quantities, total cost, funds, and ownership before changing anything. No negative prices, boolean quantities, invented items, or unsecured-to-secured laundering. Carried supplies are at risk on death; unsecured encounter rewards remain separate from pack capacity.

Healing Potion restores `floor(target.max_hp * 0.40)`, capped at missing HP. It targets a living deployed Drifter, cannot be used at full HP, and cannot revive. Outside combat it is free; in combat it consumes the acting Drifter's turn. It consumes exactly one carried potion. Existing Heal and its cooldown remain distinct.

Smoke Bomb is usable during non-boss combat. Successful use consumes the bomb and the acting Drifter's turn, ends that encounter immediately without an enemy response, and awards no encounter rewards or defeat evidence. The route remains at the same uncleared encounter; re-entry creates fresh enemies. Party HP, Mana, and Super remain unchanged. Smoke does not return the party to a Rest or Hub, so the player may prepare and retry or use a Return Talisman from the out-of-combat state.

Return Talisman is usable outside combat, including after a Smoke Bomb. It consumes one talisman and returns to the fully restored Hub, banks 100% of already-adjusted run XP only, banks no unsecured gold/items/materials, and returns every other unused carried supply. Do not apply replay adjustment twice. This is distinct from Floor I Rest's existing 50% adjusted XP/gold and all-items payout; boss completion continues to bank full eligible rewards.

Floor I Rest behavior remains unchanged: Recover restores party HP/Mana and presents both Continue and Extract; extraction pays half adjusted XP/gold and keeps all unsecured items. Continue preserves the carried pack. Death returns the party to Hub fully restored, destroys carried supplies and all unsecured run rewards, and invalidates the run checkpoint so it cannot be rewound. Boss completion banks full eligible rewards and returns unused supplies.

Alchemy is a separate shared-inventory recipe system, distinct from weapon Crafting and existing character-owned fire/poison infusion preparation. M2 adds no Alchemy level or XP. Recipe inputs are consumed and outputs credited atomically; generic transaction/recipe machinery may be reused where it is genuinely generic. Initial provisional recipes: Healing Potion = Medicinal Herb + Clean Water; Smoke Powder = Goblin Scrap + Charcoal Dust; Smoke Bomb = Smoke Powder + Cord; Return Talisman = Faded Core + Cord. Prices, recipe quantities, and yields remain data-driven and easy to tune.

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

- [x] Approve shared six-unit pack, secured Hub storage/shop boundary, sellability and sale rounding, potion effect/target/action rules, smoke/talisman transitions and payout, unchanged Rest/death/boss outcomes, and separate no-XP Alchemy.
- [x] Select a small provisional, data-driven Floor I recipe list and configurable prices/yields. Preserve existing personal fire/poison infusion behavior without duplicating it as Alchemy.

Proof: no ambiguous item outcome reaches implementation. Ordinary numeric tuning remains configurable, not an exhaustive balance exercise.

### Gate 1 - Storage, Carrying, And Merchant Transactions

- [x] Red/green domain tests: exact purchase/sale, insufficient funds, six-unit capacity, invalid quantities, stale quotes, sellability, and no partial inventory/gold mutation.
- [x] Implement provenance/carry preparation through the M1 roster boundary. Verify secured storage and the loaded bag cannot both contain the same debited supply.
- [x] Add snapshot validation and migration tests as part of the feature, including carry quantities exceeding approved limits and invalid item references.

Proof: buy -> pack -> save -> reload -> unpack/sell yields exact conserved quantities/gold. No new Drifter is recruited.

### Gate 2 - Potion Use And First Alchemy Recipes

- [x] Extend inventory/Battle tests with exact deployed target, floor-rounded healing/cap, full-HP/dead-target rules, free-vs-turn cost, and stale repeated input behavior; verify actor resources/prepared payloads are not taken from the original lead.
- [x] Implement the approved Alchemy recipes (Healing Potion, Smoke Powder, Smoke Bomb, and Return Talisman) with ingredient validation and atomic outputs. Keep legacy infusion behavior covered in `test_inventory_action_resolver.py` and relevant existing run-state tests.
- [x] Round-trip Alchemy source state and consumed supplies; prove no weapon Crafting XP is awarded by an Alchemy-only action.

Proof: craft -> carry -> use with visible effect in terminal and Python bridge; unsupported recipes/items reject without spending.

### Gate 3 - Escape And Durable Run Outcomes

- [x] Add a transition matrix in existing Floor I/Battle tests plus focused escape tests: smoke ends only the current battle, preserves HP/Mana/Super, leaves the route uncleared for fresh-enemy retry, and awards no victory; talisman then keeps only already-adjusted XP, and spent items are not returned through outcome retry.
- [x] Implement approved escape legality/route behavior without calling the ordinary victory reward path. Extend required checkpoint writes to include correct supply consumption and source state.
- [x] Inject failed writes before/during outcome installation, reconstruct a fresh coordinator/session, and prove no duplicate XP, free talisman, resurrected loot, or defeated-run rewind. Death/rest/boss behavior remains unchanged.

Proof: earned loot -> emergency exit -> fresh load returns exactly the accepted Hub/run outcome. Include a post-smoke next encounter under the approved route rule.

### Gate 4 - Client Parity And Qualification

- [x] Terminal and bridge tests compare legal buy/sell/craft/use/escape offers and exact target/outcome projections; disabled reasons reflect authoritative state.
- [x] Playwright journeys cover Hub preparation and save/reload, smoke use and fresh retry, XP-only talisman return, and the existing Floor I Rest flow where Recover retains Extract. They stay bounded rather than replaying the campaign for every item edge case.
- [x] Desktop/mobile browser checks, the pinned runtime probe, shared local cumulative qualification, content validation, compilation, and browser build passed. Probe markers include M2 preparation/Alchemy, healing, smoke retry, and talisman return.
- [ ] Run the PostgreSQL service/migration qualification and exact-SHA hosted checks. Docker is inaccessible locally; hosted checks require the eventual committed/pushed SHA.

Closure: a real preparation -> play -> loss/extraction -> restock loop is available in both clients, with atomic spending and no-rewind outcomes. Armor, payments, expansive recipe catalogs, and later floor content remain outside M2.

## Unresolved Product Decisions

| ID | Decision and blocking gate |
| --- | --- |
| M2-D1 | Resolved: one shared six-individual-unit pack; secured Hub storage; no carried gold; unused supplies return on safe exits and are lost on death. |
| M2-D2 | Resolved: potion restores floor(40% max HP), living deployed target only, no full-HP use/revival; free outside combat and consumes actor turn in combat. |
| M2-D3 | Resolved: non-boss combat only; ends encounter without enemy response/rewards, preserves party resources, leaves route node uncleared for fresh-enemy retry. |
| M2-D4 | Resolved: Return Talisman, outside combat only; banks 100% of already-adjusted run XP and no unsecured gold/items/materials; returns other unused supplies. |
| M2-D5 | Resolved: separate shared-inventory Alchemy, no level/XP in M2; initial recipe list is provisional and data-driven; existing personal infusions remain unchanged. |
| M2-D6 | Resolved: unlimited static authored merchant stock; purchases/sales affect secured Hub storage only; only explicitly sellable IDs accepted; sale is floor(base price / 2). Prices are provisional content values. |
| M2-D7 | Future-floor extraction/quest-item exceptions; M8 entry, not permission to change Floor I now |

All product decisions are resolved. Runtime and disk schema versions are recorded above. M2 implementation and local qualification are complete; final closure remains pending the PostgreSQL/migration and exact-SHA hosted checks.

### Local Qualification Record (2026-10-31)

Working-tree evidence is based on `4324b35ae21233ddc03901e5376aebd0dc32d831` on `dungeon`; the M2 changes are not committed or pushed. The full root suite passed **1,895 tests** and the web contract suite passed **63 tests**. Content validation, Python compilation, `git diff --check`, a **149-file browser build**, and the full Playwright smoke passed. The Playwright output included `M2_BROWSER|PREP_ALCHEMY_PACK_SAVE_RELOAD|PASS`, `M2_BROWSER|SMOKE_ESCAPE_PRESERVES_AND_RETRIES|PASS`, and `M2_BROWSER|TALISMAN_XP_ONLY|PASS`.

The exact pinned MicroPython v1.29.0 Windows executable was used (488,960 bytes; SHA-256 `6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA`). CPython native/forced-overlay, default MicroPython, 688K MicroPython, and semantic parity passed. The 688K heap point passed 3/3; 672K was classified as the expected memory limit 3/3; final marker: `MYP20|RESULT|CLOSURE_COMPLETE`. The probe traversed the Hub, Floor I, weapon progression, and the new M2 supply/Alchemy/healing/smoke/talisman stages.

The PostgreSQL service suite, migration-from-zero, and Alembic check were not rerun: Docker returned a permission error for the engine pipe. No profile-service/API/database implementation files changed in M2. Hosted checks remain pending the eventual exact commit SHA. Do not treat local working-tree evidence as hosted or Postgres qualification.

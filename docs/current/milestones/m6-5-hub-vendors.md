# M6.5 Hub Vendor Specialization

**Status:** Planning draft. Product direction is approved; numerical economy tuning and the Gate 0 audit remain open. No gameplay implementation is authorized by this document.

**Baseline:** v0.7 merge commit `8a76bf6b857c6b4302b5a013f08e208e2f823a28`. Revalidate the current branch, service owners, persistence versions, and client actions at Gate 0.

**Goal:** Give the Hub four clear service identities by reorganizing access to existing commerce, weapon, armor, modifier, and Alchemy operations. Preserve their current authoritative owners, transaction semantics, inventory ownership, and save behavior.

## Authority

- [M2 Preparation, Trading, And Escape](m2-preparation-trading-escape.md) owns secured commerce, item sale rules, shared-inventory Alchemy, and its atomic recipe contract.
- [M5 Armor And Accessories](m5-armor-accessories.md) owns equipment instance ownership, armor services, modifier operations, destructive disposal, and fixed Ring/Pendant behavior.
- [M6 Expeditions](m6-expeditions.md) and the [Development Roadmap](development-roadmap.md) establish the v0.7 baseline and side-mission sequencing.
- The current v0.7 repository is implementation authority. The source paths below are an entry audit, not a promise that exact APIs will remain unchanged before M6.5 begins.

## Scope

M6.5 is an optional Hub quality-of-life side mission after M6. It does not add combat, floors, loot sources, equipment systems, or progression dependencies for M7-M9.

In scope:

- Separate Merchant, Blacksmith, Enchanter, and Alchemist service entry points in the terminal and browser.
- Route each existing Hub action to its approved vendor while retaining Python-side validation and the current domain transaction boundaries.
- Give the Alchemist both an authored price advantage on eligible alchemical goods and deterministic crafting-efficiency advantages.
- Preserve Character -> Equipment as the place to inspect, equip, and swap already-owned gear.

Out of scope:

- New equipment, modifiers, magical effect types, consumables, recipes, loot sources, or vendor-only reward items.
- New equipment ownership, Alchemy levels/XP, weapon progression, or alternate-part inventories.
- Changes to combat, M2 carrying/escape rules, M5 equipment ownership/destructive outcomes, or expedition behavior.
- Schema changes unless the Gate 0 audit demonstrates a required persistent source of truth; any such change needs explicit review before implementation.

## Approved Vendor Roles

| Vendor | Owns access to | Preserved boundary |
| --- | --- | --- |
| Merchant | Ordinary buying and selling, common-material trade, traveling supplies, and general inventory commerce | Retain M2 secured-storage, sellability, authored price, and integer sale-value rules. No weapon or armor upgrade service. |
| Blacksmith | Signature-weapon component crafting/installing and slot improvement; armor stat upgrades and rarity advancement; material dismantling | Component crafting still installs directly on the exact Drifter. Improvement remains separate. Armor operations retain M5 confirmation, eligibility, cost, and atomicity rules. |
| Enchanter | Applying stored modifiers, replacing compatible modifiers, and extracting/disenchanting armor modifiers | Preserve M5 compatibility and grade checks. Replacement explicitly confirms permanent loss of the displaced modifier. Extraction destroys the donor armor and is the only way to recover its installed modifiers. |
| Alchemist | Consumable Alchemy recipes and eligible alchemical-goods commerce | Must provide both approved pricing and crafting-efficiency advantages. No weapon Crafting XP or changes to personal fire/poison infusion preparation. |

Character -> Equipment remains independent of vendor services. A player can inspect, equip, or swap owned gear there without visiting a Blacksmith or Enchanter. Vendor visits are required only for the services assigned above.

## M6.5-D1: Alchemist Pricing And Efficiency

**Approved direction:** The Alchemist provides both benefits:

- Better purchase prices than the Merchant for eligible potions, ingredients, and other authored alchemical supplies.
- Better crafting efficiency for shared-inventory Alchemy recipes through reduced ingredient requirements, improved output quantities, or a reviewed combination.

The current M2 recipes have no gold crafting fee. M6.5 must not invent one as part of this benefit. Exact discounts, eligible goods, recipe-specific costs/yields, and the efficiency mechanism remain to be authored and approved during M6.5 balancing. Do not choose numbers or apply a global multiplier during implementation.

Efficiency must be explicit, deterministic, and authored per recipe. A recipe transaction consumes its approved inputs and credits its approved outputs atomically. Failed or stale actions must not partially consume ingredients, duplicate output, or award weapon Crafting XP. The existing separation between Alchemy and weapon Crafting remains unchanged.

## v0.7 Implementation Audit

The current v0.7 source already contains the underlying operations:

- `HubEconomyService` in `root/src/app/game/hub_economy.py` handles shared-item purchases/sales, supply loading/unloading, and shared-inventory Alchemy recipes.
- `WeaponProgressionService` in `root/src/app/game/weapon_progression.py` owns signature-weapon component and slot progression operations.
- `ArmorProgressionService` in `root/src/app/game/armor_progression.py` owns deterministic armor upgrades and rarity advancement.
- `AlchemistService` in `root/src/app/game/alchemist.py` currently handles equipment sale, dismantling, modifier extraction, affixing, and replacement. M6.5 moves their player-facing service access to the Merchant, Blacksmith, or Enchanter as specified above; it does not redesign M5 ownership or transaction rules.
- `EquipmentService` in `root/src/app/game/equipment.py` and the Character equipment view continue to own equipment inspection, transfer, and equipping.
- `OverworldSession`, `OverworldPresenter`, terminal UI, and the browser client provide the shared semantic action and presentation boundary. The current Hub does not yet expose four specialist vendor identities.

The M6 plan records runtime and disk schema 24 at v0.7. Vendor navigation should be transient UI/session state, not player progression. Gate 0 must verify current save contracts and confirm that the reorganization needs no persistent vendor state or schema migration.

## M6.5A: Vendor Audit And Contracts

This planning stage makes no gameplay changes. Produce the final action-ownership matrix and record any corrections before authorizing M6.5B.

- Inventory every currently exposed Hub action, preview, confirmation, and cancellation path in both clients.
- Map commerce, weapon progression, armor upgrades/rarity, armor sale/dismantling, modifier affixing/replacement/extraction, Alchemy, and equipment management to exactly one owning vendor or to Character -> Equipment.
- Reconcile the existing M5 disposal operations with the new roles: eligible equipment sale belongs to general commerce; material dismantling belongs to the Blacksmith; modifier extraction/affixing/replacement belongs to the Enchanter. Preserve M5 item eligibility, authored yields/costs, explicit destructive confirmations, and rollback behavior. Flag any content definition that does not fit this mapping rather than silently changing it.
- Inventory M2 stock, prices, sale rules, recipes, ingredient costs, outputs, and existing atomicity tests. Identify the Merchant comparison price and eligible alchemical-goods set for the Alchemist benefit.
- Select an explicitly authored, deterministic crafting-efficiency policy and numerical values for the eligible Alchemy recipes. Keep these values reviewable and tunable; do not infer them from illustrative examples.
- Verify exact-target behavior, Hub-only restrictions, stale-input rejection, save-failure rollback, terminal/browser parity, and the current M2/M5 schema contracts.
- Record Gate 0 evidence and unresolved decisions in this plan before beginning vendor separation.

**M6.5A exit:** Every existing action has one approved owner; sale and destructive equipment paths are reconciled; discount eligibility and comparison basis are explicit; each affected recipe has approved efficiency values; no hidden persistence or gameplay change is required.

## M6.5B: Vendor Separation

- Add four vendor entry points and vendor-specific service views in both terminal and browser presentations.
- Move existing semantic actions to their assigned vendors without changing operation calculations, item ownership, recipes, authored costs, confirmation language, or save semantics.
- Keep Character -> Equipment fully available for inspection, equip, and swap operations without a vendor visit.
- Enforce vendor/action ownership in Python session handling as well as presenter availability. Forged, stale, wrong-vendor, or wrong-target submissions reject without mutation.
- Preserve M2 and M5 confirmation/cancellation flows. In particular, do not expose modifier extraction for Ring/Pendant or non-armor equipment, do not permit modifier loss to be hidden, and do not make vendor navigation a persistence requirement.

**Proof:** Each legal operation is available from exactly its assigned vendor in both clients; direct wrong-vendor submissions are rejected; equipment management remains independent; representative buy/sell, crafting, upgrade, dismantling, affix/replacement, and extraction journeys preserve their current exact costs, outputs, and rollback behavior.

## M6.5C: Economy Refinement And Qualification

- Implement the Gate 0-approved discounted prices for eligible alchemical goods and per-recipe crafting-efficiency values.
- Keep Merchant prices and all non-alchemical merchandise unchanged.
- Preserve atomic ingredient spending/output credit, save-failure rollback, no duplicate outputs, no Alchemy XP, and no weapon Crafting XP.
- Compare the tuned costs and yields against the existing M2 economy and authored supply availability. Record the balance rationale; do not expand into a general economy rebalance.
- Qualify semantic parity and save/reload behavior through both terminal and built-browser journeys.

## Acceptance And Qualification

M6.5 is complete when:

- All existing Hub operations have clear, single-vendor ownership in Python, terminal, and browser.
- The four vendor identities are distinct without making routine equipment management cumbersome.
- The Alchemist has both approved, authored benefits and only affects eligible alchemical merchandise/recipes.
- M2 transaction rules and M5 equipment, modifier, disposal, and destructive-confirmation contracts remain unchanged.
- No player progression or save schema changes were introduced without separate approval.
- Focused service/action tests, relevant root and web suites, authored-content validation, compile/build checks, and browser smoke pass on the exact pushed SHA. Run PostgreSQL/migration and pinned MicroPython qualification when affected by the implementation tree, following the shared roadmap contract.
- The plan records exact-SHA hosted evidence and any remaining economy limits.

## Deferred

New magical effects, resistance systems, Alchemy progression/XP, larger item catalogs, new dungeon drops, additional vendor services, and broad economy rebalance remain outside M6.5. Existing Ring/Pendant equipment remains fixed and non-procedural under M5.

# M6.5 Hub Vendor Specialization

**Status:** Gate 0-1 source/action audit is complete and Gate 0-1 is closed at the product-decision level. Subdecisions 0-1A through 0-1D are closed; same-Hub-visit vendor buyback is approved as a separate M6.5 requirement. Gates 0-2 through 0-5 remain open. This update is documentation-only; no gameplay implementation, schema work, or client changes are authorized.

**Planning baseline:** v0.7 merge commit `8a76bf6b857c6b4302b5a013f08e208e2f823a28`. Revalidate the current branch, service owners, persistence versions, content, and client actions at Gate 0.

**Goal:** Organize Hub commerce and services around four specialists while preserving the existing Python-authoritative gameplay, inventory, equipment, transaction, and client boundaries. M6.5 now includes planned persistent Alchemy and Enchanting professions, permanent affix discovery, finite vendor stock, and approved shared-stack ownership for uninstalled tradeable weapon components; it is not merely a navigation or presentation reorganization.

## Authority And Scope

- [M2 Preparation, Trading, And Escape](m2-preparation-trading-escape.md) owns the current secured inventory, purchase/sale transaction, item eligibility, supply preparation, and consumable Alchemy contracts. M6.5 explicitly revises M2's unlimited-stock policy and no-Alchemy-XP rule as described under [Contract reconciliation](#contract-reconciliation-m2-and-m5).
- [M5 Armor And Accessories](m5-armor-accessories.md) owns armor/equipment identity, ownership, security, upgrades, rarity, modifier compatibility, destructive outcomes, confirmation, and atomicity. M6.5 changes which vendor offers several M5 services, not their established gameplay semantics.
- [M6 Expeditions](m6-expeditions.md) and the [Development Roadmap](development-roadmap.md) establish the v0.7 baseline and milestone sequence.
- The current repository remains implementation authority for existing behavior. Source/action ownership and persistence seams must be revalidated before implementation; this plan does not lock new APIs, schemas, data formats, or migration mechanics.

M6.5 is a Hub systems side mission after the sealed v0.7 M1-M6 scope. It remains independent of M7-M9 progression, but its expanded persistent-state scope must be designed and qualified before implementation.

### In Scope

- Distinct Merchant, Blacksmith, Enchanter, and Alchemist service identities in terminal and browser clients.
- Reassignment of existing service access according to the ownership contracts below.
- Finite stock for every vendor that sells merchandise, with stock replenishment tied to Hub returns. Exact stock behavior remains open.
- Persistent Alchemy and Enchanting skill progression, a separate permanent discovered-affix collection, and persistent vendor stock/player-influenced inventory as approved product direction.
- Limited same-Hub-visit buyback for eligible sold property, separate from future vendor stock and unable to undo committed crafting or destructive conversions.
- Planned shared-inventory component stacks, quantity-based trading, and return of displaced installed components to inventory under approved Gate 0-1A.
- Four authored material families: `alch`, `smith`, `enchant`, and `gen`; Grade I through V Magic Crystals are `enchant` materials required for Enchanting. Their exact costs and acquisition sources remain to be defined.
- Both Alchemist economic advantages: discounted eligible alchemical merchandise and improved recipe efficiency. Their exact values and mechanisms remain open.
- Character -> Equipment remains the independent interface for inspecting and equipping already-owned gear.

### Out Of Scope For This Documentation Pass

- Gameplay, content, UI, save-schema, migration, or test implementation.
- Choosing discount percentages, stock counts, refresh policy, anti-arbitrage formulas, Alchemy/Enchanting XP, level thresholds, skill benefits, recipe efficiencies, or recipe-specific costs and yields.
- Adding field-crafting interfaces, new magical effects, new loot sources, new equipment catalogs, or a general economy rebalance.
- Changing combat effects, signature weapon identity/effects, M2 supply rules, M5 equipment ownership, or M5 destructive-operation outcomes.

## Gate 0-1: Approved Product Direction

The vendor and action ownership below is the approved product contract. The completed source/action audit is recorded here as implementation evidence, including current entry points, typed and browser inputs, targets, resource effects, confirmations, persistence boundaries, and non-vendor Hub workflows.

| Vendor or view | Approved responsibility | Ownership boundary |
| --- | --- | --- |
| Merchant | General commerce and broad, finite merchandise inventory | May sell eligible goods from several categories, including items also stocked by specialists. It is not the weapon/armor crafting or enchanting specialist. Preserve M2 purchase/sale validation and secured-inventory boundaries except for the explicit finite-stock and specialist-pricing changes. Owns buyback only for goods it originally purchased. |
| Blacksmith | Signature weapon improvement; component crafting/installation; armor stat upgrades and rarity advancement; eligible material dismantling; sale of armor, weapon components, and eligible crafting materials; purchase of eligible equipment, components, and crafting materials | Preserve existing craft-and-install eligibility, material spending, target/slot checks, installation, and Crafting XP. The current `already_installed` check only rejects a component currently occupying that slot; M6.5 adds no historical/lifetime crafting restriction. Uninstalled tradeable components use shared quantity stacks, and displaced parts return to shared stock. Owns buyback only for goods it originally purchased. |
| Enchanter | Armor disenchantment/modifier extraction; applying known compatible affixes; replacing affixes under explicit confirmation; management of the permanent discovered-affix collection | Service-only: no merchandise inventory. Preserve M5 extraction rewards and add permanent affix knowledge as a distinct result; retain M5 armor-only restrictions, grade compatibility, donor destruction, displaced-modifier loss, confirmations, and transaction atomicity. |
| Alchemist | Alchemical merchandise and ingredients; consumable recipes; Alchemy skill progression; purchase of eligible player-owned ingredients | May sell eligible alchemical goods at a discount and provide authored recipe-efficiency advantages. Alchemy progression is separate from weapon Crafting. Limited stock applies. Owns buyback only for goods it originally purchased. |
| Character -> Equipment | Inspect, equip, unequip, and swap compatible owned equipment among eligible Drifters | These actions remain available without visiting a vendor. They do not become Blacksmith or Enchanter services merely because those vendors can modify equipment. |
| Hub -> Inventory | Shared storage and supply packing/unpacking | Approved owner for supply preparation and ordinary inventory management. Preserve M2 capacity, carryability, secured-storage, exact quantities, and atomicity; this is not Merchant commerce and does not create a second item authority. |

Merchant inventory may include healing and Mana Potions, Return Talismans, Smoke Bombs, arrows and other ordinary consumables, armor/equipment, alchemical ingredients, weapon components, and other eligible general goods. Its quantities and prices may differ from specialist vendors. An item being available for sale through Merchant does not make Merchant the owner of that item's specialist service or player-sale path.

Player-sale ownership approved at this level:

- Eligible armor and weapon components are sold to the Blacksmith.
- Eligible weapon/armor crafting materials sold to the Blacksmith become eligible Blacksmith stock for purchase on a future Hub return.
- Eligible alchemical ingredients sold to the Alchemist become eligible Alchemist stock for purchase on a future Hub return.
- The Merchant owns general commerce for other eligible goods, subject to the existing authored sellability rules. It may also sell eligible armor/equipment as merchandise; Blacksmith and Merchant can offer overlapping goods without duplicating transaction authority.
- Components sold to the Blacksmith also become eligible for future Blacksmith purchase. Exactly how player-sold materials/components/ingredients combine with ordinary stock is unresolved; existing item eligibility still governs whether an item can be sold.

Eligible ordinary sales may also create a buyback opportunity through the vendor that purchased the goods, but only for the current Hub visit. This buyback is distinct from specialist future stock and follows the requirements below.

### Material Families And Magic Crystals

Materials are organized into four authored families: `alch` (Alchemy), `smith` (smithing/physical crafting), `enchant` (Enchanting), and `gen` (general). These family labels classify material use; by themselves they do not establish sale eligibility, vendor stock, price, or acquisition source.

Magic Crystals are `enchant`-family materials with Grades I through V. They are required inputs for Enchanting. The specific Enchanter operations that consume them, the grade and quantity required by each operation, and any interaction with Enchanting progression remain to be defined. Do not infer crystal costs for extraction/disenchantment or other operations beyond the approved requirement that Enchanting requires crystals.

The existing player-sale contracts remain in force for eligible `smith` crafting materials sold to the Blacksmith and eligible `alch` ingredients sold to the Alchemist; those sales become purchase-eligible stock on a future Hub return. No seller, stock source, or player-sale destination is approved for `enchant` materials. In particular, the Enchanter remains service-only and does not gain merchandise stock by implication. `gen` material sale and stock routing remains subject to authored item eligibility and later vendor-stock decisions.

Crystal prices, quantities, stock, vendor availability, and dungeon/content acquisition sources are unresolved. No new drop table or crystal source is established by this plan; Gate 0 must identify a legitimate acquisition path before Enchanting costs are implemented.

## Approved Persistent Systems

These are product requirements, not implementation decisions. Gate 0-4 must establish their source of truth, ownership, validation, save migration, backward compatibility, and transaction boundaries before implementation.

### Alchemy Skill

Alchemy activities advance a persistent Alchemy skill/progression bar. This is distinct from signature-weapon Crafting progression. M2 currently awards no Alchemy XP; M6.5 explicitly expands that contract, but the qualifying activities, awards, thresholds, benefits, and any unlock requirements are not decided here.

### Enchanting Skill

Eligible enchanting and disenchantment activities advance a persistent Enchanting skill/progression bar. It is separate from Alchemy and from the discovered-affix collection. Eligible actions, XP awards, thresholds, benefits, and skill-gating rules remain undecided.

### Discovered Affix Collection

The Enchanter maintains a permanent collection of discovered affix recipes. Disenchanting eligible armor registers its discovered affixes for future use. Knowledge is persistent and independent of Enchanting skill progression. The collection is not the same as ordinary stored modifier instances or consumable modifier inventory.

The approved M6.5 disenchant operation preserves the existing M5 extracted-modifier payout and additionally registers each affix in the permanent recipe collection. Stored modifier instances and learned recipes remain separate concepts. Previously discovered recipes remain known without duplicate collection entries; repeat disenchantment continues to preserve the existing modifier-instance payout. No learned recipe silently creates or duplicates a consumable modifier instance. Exact Enchanting awards, crystal quantities, and learned-recipe application costs remain assigned to later Gate 0 work.

Rings and Pendants remain fixed authored equipment and are not eligible for modifier extraction or disenchantment.

### Vendor Stock And Player-Influenced Inventory

All vendors selling merchandise have finite stock. The Enchanter is service-only and has no merchandise inventory. Replenishment is associated with returning to the Hub rather than enabling unlimited purchases during one visit. Player sales feed future specialist availability: eligible `smith` materials and components sold to the Blacksmith, and eligible `alch` ingredients sold to the Alchemist, become purchase-eligible stock on a future Hub return.

The following are deliberately unresolved: exact quantities; full, partial, or rotating replenishment; how player-sold goods merge with ordinary stock; purchase/resale pricing and anti-arbitrage; behavior through save/load, death, extraction, and repeated Hub visits; and whether every return or only qualifying completed outings refresh stock. Gate 0 must answer these before implementation. Do not choose defaults here.

### Hub Buyback (Approved Product Direction)

Buyback is a limited recovery option for eligible items sold to a vendor during the current Hub visit. It is not a general undo system.

- The player may navigate among vendors and Hub menus without ending buyback eligibility. Leaving the Hub ends that visit's opportunities; a later return does not restore expired entries.
- Buyback is offered through the vendor that purchased the item. Eligible ordinary merchandise includes crafting materials, alchemical ingredients, general goods, armor, accessories, and other explicitly eligible goods. Independently owned weapon components are not automatically included; their eligibility must be resolved under Gate 0-5.
- Buying back stackable goods restores only the selected quantity to the correct shared inventory and reduces the associated buyback quantity. The player cannot recover more than was sold.
- Buying back unique armor/accessories restores the exact sold instance and its original identity and authored/generated state, including rarity, upgrades, modifiers, and other saved properties. Do not generate a substitute.
- Buyback price and its relationship to the original sale proceeds remain open for Gate 0-5. Save/load behavior, visit identity, and interaction with future vendor stock belong to Gate 0-4. Repeated or stale claims must not duplicate gold, items, equipment, or modifiers.
- Future stock is separate: eligible smithing materials/components sold to the Blacksmith and alchemical ingredients sold to the Alchemist may become available on a qualifying future Hub return. That does not extend buyback eligibility. Gate 0-4 must define how an item bought back during the visit is excluded from later stock and how expired buyback items enter any approved future stock without duplication.

Buyback does not reverse crafting or destructive conversions. Successfully committed alchemical crafting, component crafting/installation, weapon improvement, armor upgrade/rarity advancement, material/equipment/component dismantling, enchanting, disenchanting, or modifier extraction/consumption remains irreversible under the applicable gameplay contract. Technical rollback of a failed or uncommitted operation remains required.

### Weapon Component Ownership (Gate 0-1A Approved)

Uninstalled tradeable signature-weapon components will be shared inventory quantities keyed by authored `component_id`. Identical components stack regardless of source, and players can buy/sell chosen quantities. Individual component UUIDs, per-instance provenance, and the unique armor/equipment-instance model are **not** used for these stacks.

Installed weapon slots continue to store component definition IDs on the exact Drifter. Installing one owned component consumes one unit from the corresponding shared stack; the outgoing installed component is returned to shared inventory as one unit of its definition, not destroyed. Existing craft-and-install remains the baseline, but its displaced installed component must likewise return to shared inventory. Crafting/improvement materials are not refunded. These resource, slot, and inventory changes must be atomic and checked against exact target/compatibility rules.

**All components may be sold once uninstalled, including recovered starter components.** Installed parts cannot be sold directly. Blacksmith owns player component sales and finite specialist stock; the Merchant may offer eligible component merchandise without taking over Blacksmith crafting/install services. Player-sold components become available on a subsequent qualifying Hub return, with stock/refill/price values still open.

**Existing crafting contract (preserve unchanged):** `WeaponProgressionService.craft_component()` validates the exact Drifter, authored component, signature weapon and slot; rejects a component already installed in that slot; validates and consumes its authored materials; installs directly; and awards the existing party Crafting XP. The installed-component check is not a lifetime history: once a component is no longer installed, the existing service has no historical restriction against crafting it again. M6.5 must not add a one-per-weapon/Drifter or other lifetime crafting lock, and shared-stack ownership does not change the established crafting eligibility or progression.

The exact representation of starter/default components when displaced, any separately approved removal action, and stale replacement validation need technical qualification. Preserve the current rejection when the incoming definition is already installed, with no stack consumption or partial mutation.

This expressly supersedes the old no-stackable-signature-parts restriction **for uninstalled tradeable components only**. Installed signature-weapon identities and compatibility remain based on existing component definitions. Gate 0-4 must specify persistent stack ownership, current/legacy save migration, validation, atomic buy/sell/install/craft-and-replace behavior, and terminal/browser parity.

## M6.5-D1: Alchemist Pricing And Crafting Efficiency

**Approved direction:** Both benefits are required.

- Discounted purchase prices for eligible alchemical goods and ingredients compared with the Merchant's applicable offer.
- Improved crafting efficiency through reduced ingredient requirements, increased output quantities, or an approved combination.

The intended specialist advantage is substantial. The illustration that field costs could be approximately twice the Alchemist's resource cost is a direction for later design, not approval for a universal 50% multiplier. Discounts, eligible goods, comparison prices, per-recipe requirements, output quantities, and the efficiency mechanism remain open for Gate 0-2 and 0-3.

M2 recipes currently have no gold crafting fee. Do not invent one. Any later approved efficiency must be explicit, deterministic, authored, and atomic. Failed or stale operations must not partially consume ingredients, duplicate output, or award weapon Crafting XP. Alchemy profession progression must follow the Gate 0-3 earning contract; no activity award is inferred here.

## Contract Reconciliation: M2 And M5

M6.5 changes the following named access/economy/progression provisions. Other M2 and M5 behavior remains authoritative unless explicitly revised here.

| Existing contract | M6.5 direction | Preserved behavior / unresolved boundary |
| --- | --- | --- |
| M2-D6 specifies unlimited static Merchant stock. | Superseded: merchandise vendors have finite stock, with replenishment tied to Hub returns. | M2 purchase/sale validation, secured inventory, eligible-item rules, transaction atomicity, authored purchase prices, and the existing floor(base price / 2) sale rule remain unless separately approved. Refresh, resale, and anti-arbitrage details are open. |
| M2-D5 specifies shared-inventory Alchemy with no Alchemy level or XP. | Superseded: Alchemy activities advance a persistent Alchemy profession. | Recipes remain distinct from weapon Crafting; exact activities, XP, thresholds, benefits, and efficiency values are open. Existing recipe transaction guarantees remain. |
| M2 provides the Preparation/Inventory workflow for carrying supplies. | Hub -> Inventory owns supply packing/unpacking. | Preserve M2 six-unit capacity, carryability, secured storage, exact quantities, atomic load/unload, and dungeon preparation/extraction rules. This changes navigation ownership, not item authority. |
| M5 presents equipment sale/dismantling and modifier extraction/affixing/replacement through Alchemist-owned Hub services. | Service access is reassigned: armor/component commerce and physical equipment services to Blacksmith; modifier/disenchantment/affix services to Enchanter. | Preserve M5 eligibility, instance identity, secured-gear requirements, destructive consequences, explicit confirmations, grade compatibility, and atomic rollback. |
| M5 extraction destroys donor armor and stores its eligible installed modifiers; replacement destroys the displaced modifier. | Enchanter owns these services; each successful eligible disenchantment also adds its affix definitions to permanent recipe knowledge. | Preserve every existing extracted modifier instance as a consumable payout. Recipe knowledge is separate, persists without duplicate entries, and does not replace or duplicate the M5 payout. Numerical progression and later application costs remain open. |
| M5 Rings/Pendants are static and cannot be extracted/disenchanted. | No change. | Accessories remain ineligible for disenchantment and modifier extraction. |
| M5 equipment sale destroys attached modifiers and awards only authored gold. | M6.5 same-visit buyback can restore an eligible sold armor/accessory instance with its exact original properties. | Narrow explicit supersession while a sale has active buyback: retain the exact instance and attached state for recovery, while preserving M5's existing destructive-sale confirmation. Final disposition after buyback expires must be reconciled with stock rules at Gate 0-4/0-5. Equipment dismantling remains destructive under M5 confirmation rules. |
| M2 supply packing/unpacking is presented on the Merchant screen. | Hub -> Inventory owns supply preparation. | Navigation moves away from Merchant; M2 six-unit capacity, carryability, secured-storage ownership, exact quantities, atomic load/unload, and outing rules remain unchanged. |
| M2 shared-stack sale and dismantling are immediate, without a confirmation screen. | Keep eligible ordinary quantity-based sales and shared-stack material dismantling immediate. | No added confirmation for these routine transactions. Material dismantling is irreversible. M5 armor/accessory dismantling and destructive Enchanter services retain their existing confirmations. |
| M5 signature weapon parts are crafted and installed directly; no part inventory exists. | Gate 0-1A approves tradeable shared component stacks and returns each displaced installed component to inventory, including starters. | Keep installed weapon-slot definition IDs, exact target/slot compatibility, and current Crafting XP. Preserve existing `craft_component()` eligibility and its current-slot `already_installed` check; introduce no lifetime crafting-history restriction. No unique instances or crafting-material refunds. |

These are intentional M6.5 revisions to the named provisions, not permission to rewrite the owning M2/M5 documents or unrelated gameplay contracts during this documentation pass.

## Gate 0-1 Source And Action Audit (Completed)

This is the completed source-traced audit of the v0.7 implementation at the planning baseline. It records current behavior and approved ownership; it does not authorize implementation. The single current `MERCHANT` screen exposes shared-item trade, supply packing, Alchemy recipes, signature-weapon progression, and stack-item dismantling together. Armor services are exposed from `Character -> Equipment`. There are no separate Blacksmith, Enchanter, or Alchemist screens or vendor IDs today.

### Existing Vendor And Equipment Actions

| Existing semantic input / wire ID | Current entry and Python owner | Target and resources | Confirmation and persistence | M6.5 owner; classification |
| --- | --- | --- | --- | --- |
| `action:merchant` | Hub -> Merchant; `OverworldSession._dispatch_overworld_navigation` opens `OverworldScreen.MERCHANT`; presenter combines `MerchantView` and `HubEconomyView` | No target or resource | Navigation only; screen state is transient | Keep Merchant entry for general commerce and add specialist entries; **modify navigation/presentation** |
| `merchant_target` / `ChooseMerchantTarget(drifter_id)` | Merchant screen -> `_select_merchant_target`; `OverworldPresenter._merchant_view` lists available recruited targets | Exact Drifter; no resource | Selection only, not persisted | Move exact-Drifter weapon-target selection to Blacksmith; **relocation** |
| `hub_supply`, operation `buy` / `ChooseHubSupplyAction(BUY, item_id)` | Merchant screen -> `_perform_hub_economy_action` -> `HubEconomyService.buy` | Exact authored `item_id`; spends shared gold and adds shared `shared_items`; current price is `base_price * quantity`; UI submits quantity 1 | No preview/confirmation. Mutates current session state; not saved by the service. Explicit `action:save` persists later. Current `shop_stocked` is a boolean and stock does not decrement. | Merchant for general goods; Alchemist may offer eligible overlapping alchemical goods at its approved discount. One authoritative purchase transaction must receive/validate the selected vendor offer; **modify for vendor pricing and finite stock** |
| `hub_supply`, operation `sell` / `ChooseHubSupplyAction(SELL, item_id)` | Merchant screen -> `_perform_hub_economy_action` -> `HubEconomyService.sell` | Exact item stack in secured shared storage; consumes quantity and adds `(base_price // 2) * quantity` shared gold | Ordinary shared-stack sale is immediate, without confirmation; in-memory until explicit Save. Only authored `sellable` items qualify. | Merchant for other eligible goods; Blacksmith buys eligible weapon/armor crafting materials; Alchemist buys eligible alchemical ingredients. Eligible sales may create same-visit buyback entries at the purchasing vendor and specialist goods may separately become future stock. Existing M2 sale value remains unless separately revised; **relocate by item category and add buyback** |
| `hub_supply`, operation `load` / `ChooseHubSupplyAction(LOAD, item_id)` | Merchant screen -> `_perform_hub_economy_action` -> `HubEconomyService.load` | Exact carryable item; transfers secured storage to carried supplies; six-unit cap | No confirmation; in-memory until explicit Save | Hub -> Inventory; **navigation relocation**, preserve M2 eligibility and transaction behavior |
| `hub_supply`, operation `unload` / `ChooseHubSupplyAction(UNLOAD, item_id)` | Merchant screen -> `_perform_hub_economy_action` -> `HubEconomyService.unload` | Exact carried item; transfers to secured storage | No confirmation; in-memory until explicit Save | Hub -> Inventory; **navigation relocation**, preserve M2 eligibility and transaction behavior |
| `alchemy_recipe` / `ChooseAlchemyRecipe(recipe_id)` | Merchant screen -> `_perform_hub_economy_action` -> `HubEconomyService.craft_alchemy` | Exact authored recipe; consumes shared ingredients and credits shared outputs; no gold fee | No preview/confirmation. Atomic against insufficient inputs in memory; service does not save. No Alchemy XP or weapon Crafting XP today. | Alchemist; **modify** recipe efficiency and award approved Alchemy progression while preserving atomicity and no weapon Crafting XP |
| `merchant_craft_component` / `ChooseMerchantCraftComponent(target_drifter_id, component_id)` | Merchant screen -> `_perform_merchant_action` -> `WeaponProgressionService.craft_component` | Exact recruited Drifter and authored component; consumes recipe material; installs directly and awards shared Crafting XP | No confirmation. Mutates the target's `SignatureWeaponState` and party Crafting XP in memory; explicit Save required | Blacksmith; **relocation plus inventory integration**: preserve all current eligibility, material, install, and XP behavior; return the displaced part to a shared component stack. Preserve the existing rejection only when that component is currently installed; add no historical crafting restriction. |
| `merchant_improve` / `ChooseMerchantImprove(target_drifter_id, slot_id)` | Merchant screen -> `_perform_merchant_action` -> `WeaponProgressionService.improve_slot` | Exact Drifter and slot; grade-appropriate shared material; random bounded progress and shared Crafting XP | Availability/cost is projected, but no confirmation. Mutates in memory; explicit Save required | Blacksmith; **relocation only** for existing improvement math |
| `merchant_tier_v` / `ChooseMerchantTierV(target_drifter_id)` | Merchant screen -> `_perform_merchant_action` -> `WeaponProgressionService.attempt_tier_v` | Exact Drifter; Grade-IV shared materials; RNG decides success, materials spent on either outcome; success records Tier V state | No confirmation. Mutates in memory; explicit Save required. Completed state rejects another attempt. | Blacksmith; **relocation only** for existing Tier V contract |
| `merchant_dismantle` / `ChooseMerchantDismantle(target_drifter_id, item_id, quantity)` | Merchant screen -> `_perform_merchant_action` -> `WeaponProgressionService.dismantle` | Current input requires an exact recruited Drifter, though output is shared; consumes a shared stack, RNG selects authored salvage and may double yield; no XP | Immediate, without preview or confirmation; irreversible after successful commit. Mutates in memory; explicit Save required. Repeating with stock is another operation. The Drifter target has no effect on salvage ownership. | Blacksmith; **relocation**, with an audit note that this legacy target parameter is an authorization/UI coupling, not per-Drifter ownership |
| `action:weapon`, `weapon_target` / `ChooseWeaponTarget(drifter_id)` | Character -> Weapon; `_weapon_view` inspects the selected Drifter's installed signature components and effects | Exact Drifter; no resource | Read-only, transient selection | Remains Character inspection; **unchanged independent function** |
| `action:equipment`, `character_target`, `equipment_instance` | Character -> Equipment; `_equipment_view` shows equipped references, party-owned equipment and modifier instances | Exact recruited Drifter and unique equipment `instance_id` | Selection/inspection only; transient | Remains Character -> Equipment; **unchanged independent function** |
| `equipment_action`, operation `equip` | Character -> Equipment -> `_perform_equipment_action` -> `EquipmentService.equip` | Exact target Drifter and owned equipment instance; transfers the slot reference, no item cost | No confirmation. Candidate-state save; save failure returns original state. | Remains Character -> Equipment; **unchanged** |
| `equipment_action`, operation `upgrade` | Character -> Equipment -> `ArmorProgressionService.upgrade_stat` | Exact secured armor instance; authored shared gold and material cost; deterministic stat investment | Cost/result preview is shown, but action is immediate without confirmation. Candidate-state save; save failure rolls back. | Blacksmith; **relocation only** for the existing M5 upgrade transaction |
| `equipment_action`, operation `advance_rarity` | Character -> Equipment -> `ArmorProgressionService.advance_rarity` | Exact secured armor instance; authored shared gold and material cost; deterministic rarity/capacity change | Preview but no confirmation. Candidate-state save; save failure rolls back. | Blacksmith; **relocation only** |
| `equipment_action`, operation `sell` | Character -> Equipment -> preview and `_confirm_equipment_action` -> `AlchemistService.sell` | Exact secured, unequipped equipment instance with authored `sale_value_gold`; M5 sale normally destroys attached modifiers and yields only authored gold | Preserve M5 explicit preview and Confirm/Cancel; stale confirmation rejected. Candidate-state save; save failure rolls back. If eligible for buyback, retain the exact sold instance and attached state during the active Hub visit. | Blacksmith buys eligible player equipment under the approved physical-equipment remit; Merchant may separately sell armor/equipment merchandise. **Relocate service access and add same-visit buyback**, with post-expiration disposition assigned to Gate 0-4/0-5 |
| `equipment_action`, operation `dismantle` | Character -> Equipment -> preview and `_confirm_equipment_action` -> `AlchemistService.dismantle` | Exact secured, unequipped instance with authored dismantle yields; destroys attached modifiers and yields only salvage | Explicit preview and Confirm/Cancel; stale confirmation rejected. Candidate-state save; save failure rolls back. | Blacksmith under the approved physical/material service remit; **relocate service access**, preserve M5 consequences. Keep distinct from `merchant_dismantle`, which dismantles shared stack items immediately |
| `equipment_action`, operation `extract` | Character -> Equipment -> preview and `_confirm_equipment_action` -> `AlchemistService.extract` | Exact secured, unequipped armor with modifiers; spends authored gold/material costs; consumes donor armor and creates one secured modifier instance per installed grade | Explicit preview names donor destruction and extracted modifiers; Confirm/Cancel; stale confirmation rejected. Candidate-state save; save failure rolls back. | Enchanter; **relocate service access**. No permanent affix recipe is learned today |
| `equipment_action`, operation `affix` | Character -> Equipment -> preview and `_confirm_equipment_action` -> `AlchemistService.affix` | Exact armor and exact secured modifier `instance_id`; requires slot/grade compatibility; spends authored gold/materials; consumes incoming instance; a displaced same-grade modifier is permanently destroyed | Explicit preview and Confirm/Cancel; confirms loss; stale confirmation rejected. Candidate-state save; save failure rolls back. There is no separate `replace` operation; replacement is `affix` with a displaced modifier. | Enchanter; **relocate service access**. Applying from a learned recipe instead of a stored instance is a new, unresolved action |
| `equipment_confirmation` / `ChooseEquipmentConfirmation(confirmed)` | Generic Equipment Confirmation screen; dispatches to the pending operation | Pending exact item/modifier/action; no independent resources | Confirm executes; Cancel clears the preview without mutation | Keep confirmation semantics for destructive equipment actions at their new vendor; **relocate presentation, preserve transaction boundary** |

Service-level phase boundaries are not identical today: `HubEconomyService` and `WeaponProgressionService` accept Hub/Party Ready; `ArmorProgressionService` previews only secured armor in those phases; `AlchemistService` requires the strict Hub phase; `EquipmentService` has separate Hub, safe-Rest, and Floor II rules. Vendor navigation must not accidentally broaden these rules. Direct session input is gated by the current screen and offered view, while domain services independently check their own phase, target, ownership, and resource constraints.

### Other Hub And Character Actions That Remain Independent

These are currently exposed from the Hub or from its Character, Items, Map, Options, party, and expedition subviews. They are not transferred to a vendor by M6.5. The client command `kind` values below are the browser bridge inputs; `action:<value>` is the `OverworldAction` value.

| Existing semantic input / wire ID | Current owner, target, and resources | Confirmation and persistence | M6.5 disposition |
| --- | --- | --- | --- |
| `action:character`, `character_target`, `action:skills`, `action:back` | `OverworldSession` navigation and character/skills presenter; exact recruited Drifter target | Selection is transient; Back only changes the current screen. | Keep as independent Character/Skills navigation. |
| `stat_increase`, `advancement_purchase`, `advancement_equip` | `OverworldSession._increase_permanent_stat` / `_perform_advancement_action` and the selected `PlayerState`; target is the selected Drifter/stat or skill/move. Spends that Drifter's GP for permanent stats/skills; equipping an unlocked move changes that Drifter's four-slot loadout. | No confirmation or save-port transaction for these inputs; state is persisted through explicit Save. | Preserve existing M3 ownership and rules. |
| `action:respec`, `action:confirm`, `action:cancel` | `OverworldSession._open_respec_confirmation` / `_confirm_respec` -> `RespecService`; exact selected Drifter, eligible Revision Parchment for repeat respec. | Full preview, explicit Confirm/Cancel, candidate save; failed save leaves state unchanged. | Preserve existing Character advancement service; not a vendor action. |
| `action:items`, `overworld_item`, `action:craft`, `action:inspect`, `action:use`, `overworld_healing_target`, `action:back` | `OverworldSession._select_item` / `_use_overworld_healing_potion` and `PartyState`; exact carried item and eligible deployed Drifter target, consumes one carried potion. `action:craft` is currently presented disabled. | No confirmation; use effect and item removal mutate current session state, persisted by explicit Save. Inspect/Back are read/navigation only. | Keep carried-item use in Items/Preparation. Hub supply packing/unpacking belongs in the separate Hub -> Inventory view; do not duplicate item authority. |
| `action:map`, `action:inspect`, `action:back` | Map presenter and route/world state; inspection targets the currently selected inspectable route node and does not spend resources. | Read-only/transient. | Keep independent. |
| `action:options`, `action:save`, `action:load`, `action:quit`, `action:confirm`, `action:cancel`, `action:back` | `OverworldSession._save_current_session`, `_load_saved_session`, and menu dispatch; Save/Load operate on the whole game profile, Quit leaves the current session. | Save persists a candidate; Load and Quit use confirmation screens; cancel changes no game state. | Keep independent; vendor transactions must not replace or bypass profile Save/Load. |
| `action:select_party`, `active_pair` | `OverworldSession._select_active_pair` -> `PartyState.select_active_pair`; exact ordered pair selected from recruited Drifters. | No confirmation/save-port call; updates active IDs in memory and is persisted by explicit Save. Existing Floor II replay eligibility is checked at outing start. | Keep M1 party ownership and restrictions unchanged. |
| `action:recruit_companion`, `companion` | Recruitment event/session flow -> `Recruitment` / `PartyState`; exact authored event and selected Drifter, spends shared gold (D3/D4 Hub recruitment is 65 gold after Floor II clear). | Hub D3/D4 recruitment saves a candidate before replacing session state; earlier recruitment paths retain their existing event-specific flow. | Keep independent Hub recruitment; do not classify as vendor commerce. |
| `action:start_floor_one`, `action:start_floor_two`, `action:start_floor_three`, `action:ready`, `action:set_out`, `action:choose_floor_two_helper`, `floor_two_boss_helper`, `action:extract`, `action:return_to_hub`, `action:return_with_talisman`, `action:finalize_floor_two_clear`, `action:finalize_floor_three_clear` | `OverworldSession` outing transitions and `PartyState`; validates clear state, exact active pair/full roster, carried supplies and (for Floor II) authored temporary helper choice. Return/settlement actions resolve the outing, secured rewards, and roster return. | Some transitions use persisted candidate/checkpoint or terminal-settlement save boundaries; death settlement is an encounter outcome rather than a player command. These are not vendor transactions. | Preserve M1/M2/M4 dungeon entry, preparation, helper, and settlement contracts. These return boundaries are relevant to future stock refresh but do not themselves define it. |
| `action:expeditions`, `action:prepare_expedition_floor_one`, `action:prepare_expedition_floor_two`, `expedition_plan`, `action:start_expedition`, `action:confirm`, `action:cancel`, `expedition_report` | `ExpeditionService` and expedition state; targets the selected eligible floor/category and report ID, spends energy at confirmed launch, later claims a report. | Launch uses explicit confirmation/cancel and a persisted service transaction; report claim is direct, persisted, and duplicate-checked. | Preserve M6 expedition ownership and its persistence/settlement contract; not a vendor service. |

The rows above cover the non-vendor actions offered from the Hub and its related management views. The `load`/`unload` supply operations remain the current packing controls; their approved M6.5 navigation owner is Hub -> Inventory.

### Current Data, Ownership, And Persistence Seams

Source references inspected:

- Routing and authority: `root/src/app/game/overworld_session.py::submit`, `_dispatch_overworld_navigation`, `_perform_hub_economy_action`, `_perform_merchant_action`, `_perform_equipment_action`, `_confirm_equipment_action`, `_return_to_hub`, `_return_with_talisman`, `_save_current_session`.
- Presentation model and action offers: `root/src/app/presentation/overworld_models.py::OverworldScreen`, `OverworldAction`, `MerchantView`, `HubEconomyView`, `EquipmentView`; `root/src/app/presentation/overworld_presenter.py::_options`, `_merchant_view`, `_hub_economy_view`, `_equipment_view`.
- Typed commands and clients: `root/src/app/ui/overworld_ui.py::ChooseHubSupplyAction`, `ChooseAlchemyRecipe`, `ChooseMerchant*`, `ChooseEquipmentAction`, `ChooseEquipmentConfirmation`; `root/src/app/ui/terminal_overworld_ui.py::_merchant_lines`, `_equipment_lines`, input translation; `root/web/python/dd_bridge.py::_command_to_input`; `root/web/play/js/pyd4.js::renderMerchant`, `renderHubEconomy`, `renderEquipment` and their command payloads.
- Service owners: `root/src/app/game/hub_economy.py::HubEconomyService`; `weapon_progression.py::WeaponProgressionService`; `armor_progression.py::ArmorProgressionService`; `alchemist.py::AlchemistService`; `equipment.py::EquipmentService` and `can_manage_equipment_target`.
- Authored data: `root/src/app/content/hub_economy.py::SupplyItemSpec`, `AlchemyRecipeSpec`, `SUPPLY_ITEMS`, `ALCHEMY_RECIPES`; `weapon_progression_spec.py::WeaponComponentSpec`, `DismantleSpec`, `WeaponImprovementRecipeSpec`, `TIER_V_ATTEMPT_SPEC` and `root/src/app/content/weapons/*/weapon.py`; `equipment_spec.py::EquipmentTemplateSpec`, `EQUIPMENT_TEMPLATES`; `armor_spec.py::ArmorModifierSpec`, `ArmorRaritySpec`, `MODIFIER_DEFINITIONS`; `root/src/app/content/catalog.py` registrations/lookups.
- Persistent ownership: `root/src/app/game/party_state.py::snapshot` stores shared gold/items, carried items, party Crafting XP, equipment instances, and modifier instances. `root/src/app/player/player_state.py::snapshot` stores per-Drifter signature weapon slot component IDs. `root/src/app/items/equipment.py::EquipmentInstance` stores a unique equipment ID, definition/source IDs, security, rarity/upgrades, and grade-to-modifier-definition mapping; `root/src/app/items/armor_modifier.py::ArmorModifierInstance` stores a unique modifier ID, definition/source IDs, and security.
- Save contracts: `root/src/app/snapshot.py::STATE_SCHEMA_VERSION` is 24; `root/src/app/persistence/save_document.py::DISK_SCHEMA_VERSION` is 24 and validates/reconstructs the party, equipment, and modifier inventory; `root/src/app/persistence/migration.py::migrate_legacy_save` performs forward migration. No Alchemy profession, Enchanting profession, learned-affix collection, vendor stock, vendor-return identity, or component-instance state currently exists in `root/src/app` or its tests.

`SupplyItemSpec.shop_stocked` is only a boolean. `HubEconomyService.buy` checks that flag, charges the static authored base price, and never decrements stock. `sell` uses the authored `sellable` flag and `(base_price // 2)` per unit. `EquipmentTemplateSpec` has authored sale value and dismantle yields but no purchase price or vendor quantity. `WeaponComponentSpec` has recipe material and Crafting XP values but no merchandise price, stock, independent instance, or provenance. Shared item quantities exist only as player-owned `PartyState.shared_items`; unique armor and modifiers have separate instance inventories, but there is no vendor-owned inventory.

Current general purchases/sales and Alchemy/weapon operations mutate the live session state and rely on the explicit Save action; their service methods do not invoke a save port. Armor progression, equipment changes, and Alchemist disposal/affixing instead build a candidate state and commit through the save port, returning the original state on persistence failure. This difference matters: finite stock must change atomically with gold/item ownership, and its durable save boundary must be defined rather than assumed to be supplied by M2's current service.

`OverworldSession._return_to_hub` and other settlement paths set the party back to Hub, settle/recover the outing, and return the route to its surface entrance. The relevant current semantic actions include `extract`, `return_to_hub`, `return_with_talisman`, and Floor II/III clear finalization; death settlement is driven by the battle outcome. Extraction, Talisman, death, and boss settlement have their own authoritative settlement paths. The saved model has phase, route, run/event IDs, and expedition state, but no stable Hub-visit or Hub-return sequence ID and no stock-refresh event. Re-rendering/navigation is not a Hub return. A durable, once-only replenishment boundary must be designed at Gate 0-4. Current Hub transactions also have no general transaction nonce: a repeated affordable purchase/sale is another valid transaction. Existing service validation and stale M5 confirmation protect their own boundaries, not finite-stock refresh idempotency.

### New M6.5 Actions And State

| Planned operation/state | Current support | Change classification and unresolved contract |
| --- | --- | --- |
| Separate Merchant, Blacksmith, Enchanter, and Alchemist entries/views | One `action:merchant` / `MERCHANT` screen only | New navigation and presentation models; vendor identity must be Python-authoritative, not client-only |
| Vendor-qualified merchandise offers and finite stock | Existing `hub_supply` item actions and static `shop_stocked` flag | Modify purchase projection/validation, add finite remaining quantities and vendor offers; define persisted stock and return refresh in Gate 0-4 |
| Buy armor/equipment merchandise | No equipment buy action or template purchase price/stock field | New authored merchandise and purchase operation; prices/stock/eligible template list remain open |
| Buy/sell component merchandise | No independent component inventory, merchandise price, stock, or component `buy`/`sell` input | **0-1A approved:** shared stack counts keyed by `component_id`, quantity-based buy/sell, including recovered starters; stock/price and persistence mechanics remain open |
| Alchemy discounts and recipe efficiency | Current `buy` uses one base price; current recipes use fixed authored costs/outputs | Modify authoritative pricing/recipe calculation in Gates 0-2/0-3; overlapping goods must not duplicate transaction logic |
| Alchemy profession progression | No Alchemy XP, level, or bar; current `craft_alchemy` awards no XP | New persistent state and award hook on approved activities; values/actions remain Gate 0-3 |
| Enchanting profession progression | No Enchanting XP, level, or bar | New persistent state and award hooks for approved Enchanter actions; values remain Gate 0-3 |
| Learned-affix collection and use | No known-recipe collection; current affix requires a stored `modifier_instance_id` | Add permanent knowledge alongside the unchanged M5 modifier-instance payout; repeated discovery does not duplicate the collection entry. Applying learned recipes remains a new action with costs and eligibility to define. |
| Vendor stock, refresh, and player-sold future stock | No vendor inventory, stock quantity, Hub-return ID, or stock event | New persistent state plus idempotent return and sale integration; exact life cycle remains Gate 0-4 |
| Same-visit vendor buyback | No buyback record, Hub-visit identity, or item escrow | New limited recovery operation for eligible sold property. Gate 0-4 defines visit identity, persistence and stock interaction; Gate 0-5 defines eligibility, price, expiry consequences and transaction protection. |

All future browser commands must continue through `dd_bridge` to typed inputs and the shared session/domain services. A second client-side catalog, price calculator, profession tracker, stock inventory, or affix collection would violate the existing architecture.

## Gate 0-1A: Shared Component Stacks And Replacement (Approved)

**Existing implementation evidence (v0.7):** `WeaponComponentSpec` definitions use `component_id` and `slot_id`. A Drifter's `SignatureWeaponState.components` currently maps weapon slots to definition IDs in `PlayerState`. `WeaponProgressionService.craft_component` spends shared materials, installs on the exact Drifter, awards party Crafting XP, and discards the previous installed definition. There is currently no uninstalled component stock, sale price, purchase input, quantity transfer, unequip action, or separately owned part.

**Approved new contract:**

1. **Shared stacks:** Track uninstalled tradeable components by `component_id` and nonnegative quantity in player shared inventory. Identical definitions merge into a stack. No per-component UUIDs or source/provenance objects.
2. **Install from inventory:** Require an owned unit, exact recruited Drifter, correct slot and weapon compatibility; spend one unit and install the corresponding definition ID.
3. **Replace:** Return the outgoing installed component definition as one unit in the shared inventory, including starter/default parts. A replacement with an owned part consumes the incoming unit and credits the outgoing unit in the same validated transaction.
4. **Craft-and-install:** Preserve the existing direct craft/install pathway, including exact-target/weapon/slot validation, current `already_installed` rejection, authored material spending, and Crafting XP awards. Credit the outgoing installed component to shared inventory. No spent crafting materials are refunded. The market's quantity controls do not alter the existing craft action.
5. **No new crafting history:** The existing `already_installed` check applies only while the same definition occupies that slot. Do not add lifetime, per-Drifter, per-weapon, or other historical crafting restrictions. Crafting may be performed again under the existing rules after the prior definition is no longer installed.
6. **Trade:** Sell any owned, uninstalled component, including recovered starter components, to the Blacksmith in a chosen quantity. Never sell a part directly from an installed slot. Purchases through eligible vendor offers add the chosen quantity to the shared stack; the Blacksmith has finite stock and previously sold parts enter future purchase availability under a later-approved Hub-return rule.
7. **Authority and atomicity:** Exact-target and compatibility checks, sufficient inventory/stock, gold and resource spending, displaced-part return, and persisted state updates must not partially succeed or duplicate items on stale, repeated, rejected, or failed-save submissions. Pricing, stock quantities/refresh, and persistence implementation await their assigned Gate 0 contracts.

The earlier alternatives of unique instances and deferring component trading are **rejected** for M6.5. The historical no-stackable-signature-parts contract is superseded only for uninstalled tradeable component stacks; installed weapon slots remain definition-based.

**Implementation questions to resolve without changing the crafting contract:** identify starter/default component definitions and how their returned stack units are represented; determine the location and validation of shared component counts; define migration defaults for older saves; and provide quantity-based terminal/browser purchase and sale with atomicity tests. If the incoming component is already installed, retain the existing rejection without consuming inventory. New optional component removal, prices, and anti-arbitrage values are not approved here.

## Enchanter Modifier And Recipe Ownership (Gate 0-1B Approved)

The current lifecycle is:

1. Generated armor stores modifier definitions by grade in `EquipmentInstance.modifier_slots`; the installed value is a definition ID, not a modifier-instance ID.
2. `AlchemistService.preview_extraction` accepts secured, unequipped armor only, requires at least one modifier, and aggregates each modifier's authored gold/material extraction costs.
3. Confirmed extraction destroys the donor armor and creates one new secured `ArmorModifierInstance` per installed grade. Each instance stores a unique UUID, `definition_id`, `source_id`, and `secured`; grade, compatibility, and effects resolve from the immutable authored `ArmorModifierSpec`.
4. Affixing requires an exact owned, secured modifier instance and secured armor, enforces compatible armor slot and rarity-supported grade, spends authored gold/material costs, consumes the incoming instance, and installs its definition ID. Replacing a same-grade modifier permanently destroys the displaced definition; it is not returned to inventory.
5. Under M5, sale/dismantling destroy attached modifiers; Ring/Pendant items are not modifier-bearing and are excluded from extraction/disenchantment. M6.5 buyback narrowly supersedes immediate modifier destruction for eligible equipment sales during the active Hub visit so the exact item can be restored; equipment dismantling remains destructive and is not reversible through buyback. Preserve all applicable confirmations and candidate-state rollback.

There is no permanent recipe-learning state today. The approved additive contract is:

- A successful eligible disenchantment preserves the M5 result: destroy the eligible donor armor and create the existing secured consumable `ArmorModifierInstance` payout for each installed grade.
- The same operation permanently registers the armor's affix definitions in the Enchanter's known-recipe collection. Already-known definitions remain known without duplicate collection entries.
- Repeated disenchantment continues to grant the existing M5 modifier-instance payout. Permanent knowledge never silently creates or duplicates a consumable instance.
- Modifier instances remain consumable inputs for the existing affix operation. Applying a learned recipe without a stored instance is a distinct new action, with costs and eligibility still to be defined.
- Enchanting skill is a separate persistent progression system. Exact XP awards, repeat-discovery progression, crystal quantities, and learned-recipe application costs remain assigned to Gates 0-3/0-5 as appropriate.

Preserve M5's armor-only extraction, donor destruction, secured/unequipped requirements, grade compatibility, replacement consequences, explicit confirmations, and atomic rollback. Rings and Pendants remain ineligible.

## Profession And Persistence Audit

The existing Crafting system is the only profession-like progression reference. `PartyState` owns one shared `crafting_experience`; `crafting_level` is derived from `CRAFTING_LEVEL_THRESHOLDS` in `weapon_progression_spec.py`. The current curve starts at Level 1 with 0 XP, advances one level per 10 cumulative XP, and caps at Level 100 / 990 XP. Authored component recipes currently award 10 XP; improvement awards are authored by material grade: Grade I 20, Grade II 30, Grade III 40, and Grade IV 50 XP. Successful component craft/install and slot improvement award XP after their resource transaction; stack dismantling and Tier V attempts award none. It is party-level, persisted in the `party.crafting_experience` snapshot field, and validated against `MAX_CRAFTING_EXPERIENCE`.

This provides an implementation reference for a persistent experience value, derived level, authored threshold curve, and award at a successful domain transaction boundary. It is not a reusable profession framework: there is no generic profession object or shared XP API. M6.5 must keep Alchemy and Enchanting as independent progressions with separate sources/curves/state. Reusing a small persistence/validation pattern may be appropriate; reusing Crafting XP, awarding weapon Crafting XP from Alchemy, coupling professions, or changing weapon Crafting behavior is not.

The current save baseline is runtime schema 24 and disk schema 24. `PartyState` already persists shared stock, party Crafting XP, equipment instances, and modifier instances; each `PlayerState` persists signature-weapon component IDs and advancement. No vendor/profession/known-affix fields exist. Any adopted M6.5 state therefore needs an explicit owner, validation and legacy default, a forward-only runtime/disk migration, current and historical profile coverage, and save/reload tests. The exact schema version and field placement are not decided. Profile envelope/API/database changes are not implied; verify them at Gate 0-4 rather than assuming.

## Vendor Stock And Hub-Return Audit

Current facts:

- M2-D6 explicitly specifies unlimited static authored Merchant stock. `SupplyItemSpec.shop_stocked` is eligibility only; no remaining quantity is read or written.
- Purchases use `SupplyItemSpec.base_price`, spend shared gold, and add to secured `PartyState.shared_items`. Sales consume only authored sellable shared items and pay `floor(base_price / 2)` per unit. Both live in `HubEconomyService`; the presenter hardcodes one unit per UI action although the service accepts a positive quantity.
- `PartyState.shared_items` is player-owned stock, not a vendor inventory. Equipment and modifier instances are separate unique party-owned collections. No vendor stock count, player-sold future stock, sale receipt, or vendor offer record exists.
- `EquipmentTemplateSpec` has optional sale value and salvage yields, but no vendor buy price or stock. `WeaponComponentSpec` has recipe material costs and Crafting award, but no buy/sale price or stock. Equipment/service sale and stack-item sale are different transactions.
- Hub phase changes and returns are handled by session/party/overworld outcome methods. Extraction, Talisman, death, and boss settlement have their own authoritative settlement paths. The state records route/run/event details, but no stable Hub-visit counter or return event exists; merely opening Merchant or re-rendering a Hub does not represent a return. The approved future-stock categories are Blacksmith-accepted crafting materials/components and Alchemist-accepted ingredients.
- Existing inputs are validated against current views and services recheck phase, resources, item ownership, and IDs. There is no general idempotency key for repeated buy/sell commands. A repeated valid command is a new transaction. Current M5 preview equality protects against stale destructive confirmations; it does not identify a Hub return or prevent duplicate stock refresh.

The M6.5 finite-stock requirement is an intentional revision of only M2's unlimited-stock availability rule. It does not replace M2's secured-storage, authored sellability, sale rounding, or transaction rules. Future state must represent vendor-owned finite stock separately from player-owned shared stacks and atomically account for purchases, player sales, and replenishment. The refresh trigger and handling of sold items across returns, reload, extraction, death, and repeated actions remain open for Gate 0-4.

## Existing Test Coverage And Gaps

| Boundary | Existing coverage inspected | Coverage still missing for M6.5 |
| --- | --- | --- |
| M2 shared purchase/sale, carrying, Alchemy | `root/tests/test_hub_economy.py`: purchase storage, invalid quantity, affordability/unknown item, sellability and half-price floor, six-unit load/unload, phase rejection, atomic recipe input/output, no Crafting XP. `test_save_document_boundary.py` covers stored/carried round trips. | Vendor-specific price/stock authority; stock decrement, replenishment and rollback; Alchemy XP; vendor overlap; sale-driven future stock; purchase/save failure boundary. |
| Weapon improvement/component/Tier V/material dismantling | `root/tests/test_weapon_progression.py`: grades/gates, RNG, exact target, component craft-and-install, already-installed/wrong component, replacement effects, dismantle output/atomic rejection, Tier V costs and retry prevention. `root/tests/test_hub_flow.py` and `test_overworld_session.py` cover merchant orchestration and exact target. `test_save_document_boundary.py` covers installed components and Tier V round trips. | Component merchandise or ownership, bought component compatibility, sale/removal, vendor stock, new Blacksmith-only authorization, and persisted transaction rollback for these in-memory service calls. |
| Armor upgrades and rarity | `root/tests/test_armor_progression.py`: authored costs/projections, rarity path, resource rejection, save-failure rollback, accessory exclusion. | Blacksmith-only service routing and any equipment purchase/stock path. |
| Equipment transfer and M5 disposal/modifiers | `root/tests/test_equipment_service.py`: exact Drifter, ownership transfer, safe Rest, phase limits, save failure. `root/tests/test_alchemist.py`: sale/dismantle/extract/affix, armor/accessory eligibility, compatibility, exact instance, destructive confirmations, cancel, stale preview, repeat submission, resource rejection, and save rollback. `test_overworld_session.py` covers equipment confirmation orchestration. | Enchanter-only routing; additive instance payout plus permanent knowledge; repeat-known handling; learned-recipe application; same-visit buyback preserving exact equipment identity/state; expiry and transaction boundaries. |
| Terminal/browser parity | `root/tests/test_terminal_overworld_ui.py`: Merchant shared supply/Alchemy, target IDs, weapon recipes/Tier V, equipment selection and destructive confirmation. `root/web_tests/test_browser_bridge_contract.py`: merchant commands, exact target component craft, equipment commands and target. `root/web_tests/browser_smoke.mjs` includes M5 upgrade/equip/save-reload/transfer/modifier replacement/extraction/sale/dismantle journeys. | Four distinct vendor flows; Hub Inventory preparation; wrong-vendor rejection; finite stock display/transactions; buyback return/cancel/expiry; Alchemist price/efficiency/profession; Enchanter profession/library; player-sold goods availability after return. |
| Persistence/migration | `root/tests/test_save_state.py` covers current schema 24, schemas 18-23, unsupported future schema rejection, modifier inventory migration, equipment/weapon round trips, and immutable legacy history; `root/tests/test_save_document_boundary.py` covers current equipment and component state. | New vendor stock, profession, collection, component ownership, Hub-visit and buyback state; schema defaults, malformed-state rejection, exact-instance round trips, expiry, and current remote/profile advancement. |

The current tests provide substantial protection for existing service semantics, but they do not qualify the new persistence sources or vendor ownership boundary. Existing M2 purchase/sale/Alchemy operations do not use a save-port candidate commit; tests cover their in-memory atomic mutation, not storage failure rollback. Any stock/resource transaction design must add focused protection rather than relying on M5's different commit path.

## Gate 0-1 Closure And Remaining Implementation Work

The source/action mapping is complete for the exposed commerce, weapon progression, armor/equipment, modifier, supply-preparation, and other Hub actions. Gate 0-1 is **closed at the product-decision level**. No Gate 0-1 product decision remains open; the following approved contracts are binding for M6.5:

- **0-1A, weapon components:** uninstalled tradeable components use shared quantity stacks; installation/craft-and-install returns displaced parts, including starters; recovered components may be sold; current crafting eligibility, material costs, compatibility, and Crafting XP remain unchanged. No lifetime crafting restriction or crafting-material refund.
- **0-1B, Enchanter:** successful eligible disenchantment preserves the M5 modifier-instance payout and additively records permanent affix knowledge without duplicate collection entries. The learned collection and consumable instances remain separate.
- **0-1C, supply preparation:** Hub -> Inventory owns packing/unpacking. M2 carrying and secured-storage semantics remain unchanged.
- **0-1D, immediate shared-stack transactions:** eligible ordinary quantity-based material/item sales and shared-stack dismantling execute immediately without an additional confirmation screen. Armor/accessory dismantling and destructive Enchanter operations retain their existing M5 confirmations. Equipment sale retains its existing M5 confirmation where applicable.
- **Buyback direction:** an eligible item sale may be reversed only through its purchasing vendor during the same Hub visit. Buyback is separate from future vendor stock and cannot reverse a committed crafting or destructive conversion.

The audit findings remain useful implementation evidence, not pending product decisions. Starter-component representation, persistence/migrations, vendor and Hub-visit identity, finite stock, buyback record lifecycle, prices, exact crystal costs/acquisition, profession values, and transaction implementations are assigned to Gates 0-2 through 0-5 below. No gameplay or schema work is authorized by this documentation update.

## Gate 0 Tracking

| Gate item | Status | Required outcome |
| --- | --- | --- |
| 0-1: Vendor ownership and product direction | **Closed: approved** | Source/action audit complete; 0-1A through 0-1D are closed at the product-decision level. |
| 0-1A: Component ownership/replacement | **Closed: approved** | Uninstalled components are shared stacks keyed by `component_id`; replacement/craft-and-install credits the outgoing component; all recovered parts including starter components may be sold. Preserve existing crafting rules; no lifetime restriction. |
| 0-1B: Enchanter extraction and recipe knowledge | **Closed: approved** | Preserve M5's extracted modifier-instance payout and additionally add permanent affix knowledge, without duplicate collection entries. Exact progression and costs remain assigned to later gates. |
| 0-1C: Supply preparation ownership | **Closed: approved** | Hub -> Inventory owns packing/unpacking; all M2 capacity, carryability, secured-storage, quantity, and atomicity rules remain. |
| 0-1D: Immediate shared-stack transactions | **Closed: approved** | Ordinary quantity-based sales and shared-stack dismantling need no additional confirmation; M5 equipment and Enchanter destructive confirmations remain. |
| Hub buyback direction | **Approved** | Eligible sold property may be bought back from its original vendor during the same Hub visit; eligibility, pricing, persistence, and stock interaction remain assigned to Gates 0-4/0-5. |
| 0-2: Alchemist merchandise and discounts | Open | Identify eligible goods, Merchant comparison offers, and explicit discount prices. |
| 0-3: Recipe efficiency and profession values | Open | Define Alchemy recipe inputs/outputs/efficiency, Alchemy/Enchanting progression values including repeat-discovery rewards, and authored operation-specific Magic Crystal costs. |
| 0-4: Navigation and persistence | Open | Specify vendor/Hub Inventory navigation, state ownership, schema/migration/backward compatibility, client parity, Hub-visit identity, finite stock, buyback lifetime, and legitimate seller/acquisition availability for `enchant` materials. |
| 0-5: Destructive, sale, and buyback paths | Open | Finalize buyback eligibility/pricing, post-expiration disposition and stock interaction, rollback/stale-action behavior, and confirmation/destructive protections against M5. |

No numeric values or technical architecture are inferred beyond the approved product contracts. Gates 0-2 through 0-5 remain open; this documentation update does not authorize gameplay implementation.

## Future Implementation Stages

These stages remain planning structure only; no gameplay implementation is authorized by this Gate 0-1 closure update.

### M6.5A: Remaining Vendor Contracts

Complete Gates 0-2 through 0-5 using the source/action audit and closed Gate 0-1 contracts already recorded here. Define pricing, recipe efficiency, profession progression, stock and buyback lifecycle, and persistence. Do not repeat the completed audit or fill unresolved choices in during implementation.

### M6.5B: Vendor Separation And Persistent Systems

After approval, introduce the vendor identities and route semantic operations to their owners. Implement only the approved persistent sources of truth for Alchemy/Enchanting progression, discovered affixes, finite stock/player-influenced inventory, visit-scoped buyback, and approved transferable component ownership. Preserve the single authoritative Python domain and shared save architecture; terminal and browser remain projections of Python legality, prices, outcomes, and transaction results.

### M6.5C: Economy Refinement And Qualification

Apply approved merchandise and recipe values, check affordability and anti-arbitrage against the existing economy, and qualify ownership, atomicity, save/reload, terminal/browser parity, migrations, and supported runtime behavior. No broad economy rebalance is implied.

## Acceptance And Qualification

M6.5 implementation closure will require, at minimum:

- Every relevant action has one clear owner and equivalent legal behavior in Python, terminal, and browser.
- Merchant, Blacksmith, and Alchemist stock is finite under the approved replenishment contract; Enchanter remains service-only.
- Alchemy skill, Enchanting skill, learned-affix knowledge, and vendor stock/player-influenced inventory have distinct, validated persistent ownership as approved.
- Buyback is limited to eligible sales from the purchasing vendor during the current Hub visit; stack quantities and exact unique-item state are restored without duplication, and committed crafting/destructive conversions remain irreversible.
- Weapon components use approved shared stack counts when uninstalled; exact compatible installs and craft-and-install return displaced definitions without duplicate/refund exploits. Installed slots remain definition-based. All recovered components, including starter parts, are eligible for sale.
- Character -> Equipment remains independent; Hub -> Inventory owns supply preparation while preserving M2 rules and item authority.
- M2 transaction and carrying guarantees and M5 equipment/modifier/destructive-operation guarantees remain intact except for the explicit stock, Alchemy progression, and vendor ownership revisions recorded above.
- Relevant focused tests, full applicable Python/web suites, content validation, compile/build, browser journeys, migration/profile-service qualification, and pinned runtime checks pass on the exact implementation SHA, with evidence recorded in this plan.

## Deferred

Gates 0-2 through 0-5 remain open: exact prices, stock amounts/refresh, profession progression, recipe values, Magic Crystal operation costs/acquisition, learned-affix application costs, buyback eligibility/prices/lifetime interactions, starter/default-part representation, and technical schema/migration choices. No component crafting-limit decision is open. New magical effect types, Ring/Pendant disenchantment, new dungeon loot sources, new field-crafting interfaces, and broad economy rebalance are not approved by this plan.

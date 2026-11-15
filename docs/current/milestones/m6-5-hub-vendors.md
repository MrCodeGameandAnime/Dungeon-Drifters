# M6.5 Hub Vendor Specialization

**Status:** Gate 0 and implementation Slices A-E are implemented. Slice D adds finite vendor commerce, shared component stacks, buyback escrow, future-stock routing, and their transaction/persistence boundaries. Slice E adds Alchemy and Enchanting progression, recipe mastery, Mana Potions, rare Return Talisman crafting, permanent affix knowledge, and learned-affix application. Local Slice E qualification passed: 2,421 root tests, 78 web tests, authored-content validation, compileall, the 180-file browser build, and the full Playwright browser smoke. Exact-SHA hosted qualification and the pinned MicroPython executable qualification remain for Slice F; Docker was unavailable locally, so PostgreSQL and migration checks are pending hosted CI.

**Planning baseline:** v0.7 merge commit `8a76bf6b857c6b4302b5a013f08e208e2f823a28`; final readiness audit at `e66a4f066d2dc7083b1c76075239ba7ab392a76f` on `dungeon`.

**Gate 0-4 source audit baseline:** `bf830a63bb01edd710506ba753abeea8d6b50d64`.

**Goal:** Organize Hub commerce and services around four specialists while preserving the existing Python-authoritative gameplay, inventory, equipment, transaction, and client boundaries. M6.5 now includes planned persistent Alchemy and Enchanting professions, permanent affix discovery, finite vendor stock, and approved shared-stack ownership for uninstalled tradeable weapon components; it is not merely a navigation or presentation reorganization.

## Slice A Implementation Evidence

- `root/src/app/content/hub_economy.py` now defines the approved item prices, Mana Potion data, canonical Charcoal Powder display name, and unsellability for Healing Potions, Mana Potions, and Smoke Bombs. Existing recipe inputs and outputs remain unchanged.
- `root/src/app/content/vendor_catalog.py` defines validated merchandise offers, finite stock caps/initial/refill quantities, progression unlocks, deterministic equipment policies, Grade I-IV Crystal offers, Grade I-III first-clear rewards, and the reserved Grade V boundary. No service consumes these definitions yet.
- `root/tools/validate_content.py` includes vendor-catalog validation while preserving normal diagnostics when existing authored content is malformed.
- Focused catalog/economy/content tests cover IDs, prices, resale eligibility, stock schedules, unlock/source references, compatibility, and validation failures. The generated MicroPython dataclass manifest and existing M2 price-probe expectation were updated for the added content definitions.
- Hosted run `43635075062` passed the Python, web, content, build, PostgreSQL, and migration checks; its browser smoke used the superseded `Charcoal Dust` label. The smoke now expects the approved `Charcoal Powder` label, and the complete browser smoke passes locally.
- Slice A added no vendor service or screen. Slice B now adds the persistent state and outing lifecycle foundation; it still adds no vendor navigation or commerce UI.

## Slice B Implementation Evidence

- `PartyState` now owns the initial M6.5 economy state: Alchemy and Enchanting XP, known-affix IDs, component stacks, vendor stock, Hub/outing identity, progress and settlement evidence, and transaction sequencing. Runtime and disk schema advance from 24 to 25. Historical schema-24 data migrates forward with authored stock, first-clear reward backfill, active-outing evidence, and the approved 1:1 Smoke Powder-to-Charcoal Powder conversion.
- Outing starts, Floor I encounter outcomes, and terminal returns use candidate-save-before-publish behavior. A failed local write leaves the prior route, party, reward, carried-supply, and M6.5 state intact. Floors II and III use the same outing ledger while retaining their existing run-event and settlement contracts.
- Encounter progress is recorded only after the reward payload has been constructed successfully. Duplicate settlement cannot create another outing or Hub visit. Current-schema validation binds outing floor/progress to the active route and rejects malformed or inconsistent vendor state.
- Regression coverage includes current and schema-24 round trips, invalid-ledger rejection, first-clear backfill, Smoke Powder conversion, all-floor outing start/progress/settlement, idempotency, save-failure rollback, and Floor I save/reload continuation. The full local root suite passed **2,361 tests**; web contracts passed **75 tests**; content validation, compileall, the **178-file** browser build, and full Playwright smoke also passed.
- Local PostgreSQL/migration checks could not run because the Docker engine endpoint was unavailable. Exact-SHA hosted qualification remains pending. No Slice C vendor screens or commerce transactions are included here.

## Slice C Implementation Evidence

- `OverworldSession` now owns vendor-directory entry, separate Merchant/Blacksmith/Enchanter/Alchemist navigation, independent Hub Inventory entry, and vendor-aware Back routing. Direct service submissions outside the valid Hub state reject without mutating game state.
- The presenter assigns each existing operation to its approved service: general trade to Merchant; weapon and physical armor services to Blacksmith; modifier extraction and affixing to Enchanter; consumable recipes to Alchemist. Character Equipment remains equip/inspection only, and Hub Inventory remains the supply preparation surface.
- Terminal and browser clients render the same semantic routes and continue submitting Python-owned actions. No pricing, stock, profession, inventory, schema, or transaction behavior was added in this slice.
- Tests cover route ownership and Back behavior, wrong-phase rejection, terminal options, bridge payloads, browser screen projections, and semantic navigation. The cumulative browser smoke now follows the M6.5 ownership split through Character Equipment, Blacksmith, and Enchanter. The obsolete `Charcoal Dust` smoke labels were already corrected to `Charcoal Powder`.
- Local qualification on the Slice C worktree: root pytest **2,365 passed**; web pytest **76 passed**; authored-content validation passed; Python compileall passed; browser build packaged **178 files**; full Playwright smoke passed. Docker was unreachable locally, so PostgreSQL/migration checks were not run locally. Push this slice to obtain exact-SHA hosted qualification.

## Slice D Implementation Evidence

- `HubVendorService` now applies finite purchases and sales, same-visit buyback escrow, queued future stock, specialist-first replenishment, and quantity-based component ownership. Component purchases/installations preserve the existing weapon eligibility and Crafting XP contracts; replacing an installed part returns the displaced part to its shared stack.
- Browser smoke now buys the two approved Charcoal Powder units from the Alchemist at 3g each and verifies its finite stock falls from two to zero. The remaining smoke purchases were checked against their authored limits; the single Healing Potion purchase stays with the Merchant, and equipment buyback remains tied to an exact preceding sale.
- The same hosted smoke exposed a stale M5 sale-confirmation assertion. It now verifies the actual same-visit buyback and Hub-departure discard warning rather than requiring the modifier's name in the warning.
- Exact-SHA qualification passed on `1223e453e501cd0b7fa84da730200857ecafb9e9`, [Actions run 43693830256](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/43693830256): root pytest **2,390 passed**; web pytest **77 passed**; PostgreSQL **51 passed**; content validation, compile, 179-file browser build, full browser smoke, migration-from-zero, and Alembic parity all passed. The local Windows browser process could not launch under this runner, so the full smoke evidence is hosted.

## Slice E Implementation Evidence

- The Alchemist now owns persistent Alchemy XP, deterministic mastery output, approved Healing Potion/Smoke Bomb/Mana Potion recipes, and the confirmed rare Return Talisman craft. The Enchanter now awards independent Enchanting XP, permanently learns eligible affixes during armor extraction while preserving the existing consumable modifier payout, and applies learned affixes using the approved grade-matched Crystal and gold costs.
- Mana Potions restore the authored 30% maximum Mana to one eligible living active Drifter, consume exactly one carried unit, and use the same target-specific flow in overworld and combat. Terminal and browser views show the relevant resource and the profession/affix progression state.
- Regression coverage proves recipe/mastery thresholds, stale/repeated craft rejection, candidate-save rollback, Talisman confirmation and exclusions, independent Enchanting progression, first/repeated affix discovery, learned-affix cost bands/replacement/rollback, and exact Mana Potion targeting. The full browser smoke includes M6.5 recipe, save/reload, Enchanter, and Mana targeting journeys.
- Local qualification on the Slice E worktree: root pytest **2,421 passed**; web pytest **78 passed**; authored-content validation, compileall, 180-file browser build, and full Playwright smoke passed. `git diff --check` passed. Docker was unreachable locally, so PostgreSQL/migration checks await exact-SHA hosted qualification. The exact pinned MicroPython artifact was not available at its recorded path; a different local v1.29.0 binary was not substituted or counted as pinned evidence.

## Authority And Scope

- [M2 Preparation, Trading, And Escape](m2-preparation-trading-escape.md) owns the current secured inventory, purchase/sale transaction, item eligibility, supply preparation, and consumable Alchemy contracts. M6.5 explicitly revises M2's unlimited-stock policy and no-Alchemy-XP rule as described under [Contract reconciliation](#contract-reconciliation-m2-and-m5).
- [M5 Armor And Accessories](m5-armor-accessories.md) owns armor/equipment identity, ownership, security, upgrades, rarity, modifier compatibility, destructive outcomes, confirmation, and atomicity. M6.5 changes which vendor offers several M5 services, not their established gameplay semantics.
- [M6 Expeditions](m6-expeditions.md) and the [Development Roadmap](development-roadmap.md) establish the v0.7 baseline and milestone sequence.
- The current repository remains implementation authority for existing behavior. Source/action ownership and persistence seams must be revalidated before implementation; this plan does not lock new APIs, schemas, data formats, or migration mechanics.

M6.5 is a Hub systems side mission after the sealed v0.7 M1-M6 scope. It remains independent of M7-M9 progression, but its expanded persistent-state scope must be designed and qualified before implementation.

### In Scope

- Distinct Merchant, Blacksmith, Enchanter, and Alchemist service identities in terminal and browser clients.
- Reassignment of existing service access according to the ownership contracts below.
- Finite stock for every vendor that sells merchandise, replenished by top-up to authored limits on each qualifying, encounter-progressing Hub return. Slice A authors the approved capacities, initial quantities, and refill amounts; persistent stock and replenishment remain later-slice behavior.
- Persistent Alchemy and Enchanting skill progression, a separate permanent discovered-affix collection, and persistent vendor stock/player-influenced inventory as approved product direction.
- Same-Hub-visit buyback for approved eligible sales, at the exact original sale payout, separate from future vendor stock and unable to undo committed crafting or destructive conversions.
- Planned shared-inventory component stacks, quantity-based trading, and return of displaced installed components to inventory under approved Gate 0-1A.
- Four authored material families: `alch`, `smith`, `enchant`, and `gen`; Grade I through V Magic Crystals are `enchant` materials. Gate 0-3 defines matching-grade learned-affix costs. Slice A defines the approved Grade I-III first-clear rewards and Grade I-IV Merchant offers; Grade IV reward sourcing and Grade V remain future-floor content.
- Both Alchemist economic advantages: a flat 25% discount on eligible alchemical merchandise and deterministic mastery-based output bonuses. The approved merchandise schedule is recorded below; Gate 0-3 fixes recipe quantities, output milestones, and XP.
- Character -> Equipment remains the independent interface for inspecting and equipping already-owned gear.

### Out Of Scope For Slice A

- Services, UI, save-schema, migration, or gameplay implementation of the approved profession, recipe, stock, and learned-affix contracts.
- Reopening or changing approved Gate 0 decisions. The consolidated readiness package is approved; only Slice A content definitions and their validation are authorized now.
- No new magical effect behavior, field-crafting interface, or general economy rebalance. First-clear rewards are definitions only; delivery and historical backfill remain Slice B work.
- Changing combat effects, signature weapon identity/effects, M2 supply rules, M5 equipment ownership, or M5 destructive-operation outcomes.

## Gate 0-1: Approved Product Direction

The vendor and action ownership below is the approved product contract. The completed source/action audit is recorded here as implementation evidence, including current entry points, typed and browser inputs, targets, resource effects, confirmations, persistence boundaries, and non-vendor Hub workflows.

| Vendor or view | Approved responsibility | Ownership boundary |
| --- | --- | --- |
| Merchant | General commerce and broad, finite merchandise inventory | May sell eligible goods from several categories, including items also stocked by specialists. It is not the weapon/armor crafting or enchanting specialist. Preserve M2 purchase/sale validation and secured-inventory boundaries except for the explicit finite-stock and specialist-pricing changes. Owns buyback only for goods it originally purchased. |
| Blacksmith | Signature weapon improvement; component crafting/installation; armor stat upgrades and rarity advancement; eligible material dismantling; sale of armor, weapon components, and eligible crafting materials; purchase of eligible equipment, components, and crafting materials | Preserve existing craft-and-install eligibility, material spending, target/slot checks, installation, and Crafting XP. The current `already_installed` check only rejects a component currently occupying that slot; M6.5 adds no historical/lifetime crafting restriction. Uninstalled tradeable components use shared quantity stacks, and displaced parts return to shared stock. Owns buyback only for goods it originally purchased. |
| Enchanter | Armor disenchantment/modifier extraction; applying known compatible affixes; replacing affixes under explicit confirmation; management of the permanent discovered-affix collection | Service-only: no merchandise inventory. Preserve M5 extraction rewards and add permanent affix knowledge as a distinct result; retain M5 armor-only restrictions, grade compatibility, donor destruction, displaced-modifier loss, confirmations, and transaction atomicity. |
| Alchemist | Alchemical merchandise and ingredients; ordinary consumable recipes; the rare Return Talisman crafting service; Alchemy skill progression; purchase of eligible player-owned ingredients | May sell eligible alchemical goods at a discount and provide authored recipe-efficiency advantages. The Alchemist crafts but does not sell Return Talismans; Merchant remains their exclusive merchandise seller. The rare Talisman craft receives no Alchemy XP, output bonus, ingredient reduction, or discount. Alchemy progression is separate from weapon Crafting. Limited stock applies to merchandise. Owns buyback only for merchandise it originally purchased. |
| Character -> Equipment | Inspect, equip, unequip, and swap compatible owned equipment among eligible Drifters | These actions remain available without visiting a vendor. They do not become Blacksmith or Enchanter services merely because those vendors can modify equipment. |
| Hub -> Inventory | Shared storage and supply packing/unpacking | Approved owner for supply preparation and ordinary inventory management. Preserve M2 capacity, carryability, secured-storage, exact quantities, and atomicity; this is not Merchant commerce and does not create a second item authority. |

Merchant's generalist remit allows eligible ordinary consumables, armor/equipment, alchemical ingredients, weapon components, and other general goods. Return Talismans are Merchant-exclusive merchandise and are never Alchemist stock. Eligible merchandise is allocated from shared Hub stock with specialist priority and Merchant overflow as specified under Gate 0-2; this is not an unlimited independent Merchant supply. An item being available for sale through Merchant does not make Merchant the owner of that item's specialist service or player-sale path.

Player-sale ownership approved at this level:

- Eligible armor and weapon components are sold to the Blacksmith.
- Eligible weapon/armor crafting materials sold to the Blacksmith become eligible Blacksmith stock for purchase on a future Hub return.
- Eligible alchemical ingredients sold to the Alchemist become eligible Alchemist stock for purchase on a future Hub return.
- The Merchant owns general commerce for other eligible goods, subject to the existing authored sellability rules. It may also sell eligible armor/equipment as merchandise; Blacksmith and Merchant can offer overlapping goods without duplicating transaction authority.
- Eligible components/materials/ingredients sold to a specialist follow the approved buyback-then-queue lifecycle in Gate 0-5: active-visit escrow is not future stock; after expiry, eligible remaining stack quantities enter a persistent queue and are allocated on qualifying returns under the Gate 0-4 capacity and vendor-priority rules. Existing authored item eligibility still governs whether an item can be sold or routed to Merchant overflow.

Eligible completed player-to-vendor sales create buyback eligibility through the originating vendor for the current Hub visit. This buyback is distinct from specialist future stock: an eligible stack unit is in only one place at a time, and its remaining future-stock entitlement is resolved when the buyback window expires.

### Material Families And Magic Crystals

Materials are organized into four authored families: `alch` (Alchemy), `smith` (smithing/physical crafting), `enchant` (Enchanting), and `gen` (general). These family labels classify material use; by themselves they do not establish sale eligibility, vendor stock, price, or acquisition source.

Magic Crystals are `enchant`-family materials with Grades I through V. Under the approved Gate 0-3 contract, only the new learned-affix recipe application consumes grade-matched crystals, in the quantities specified below. Existing M5 disenchantment/extraction and stored-modifier application do not require crystals. Grades I-IV enter the economy through progression-appropriate dungeon rewards and limited Merchant merchandise; exact floors, quantities, drop probabilities, prices, and stock limits are content-authoring dependencies. The Enchanter does not sell crystals. Grade V learned-application remains reserved for future content.

The newly planned Magic Reagent, Aether Dust, Sulfur, and Charcoal Powder are `alch` materials. Preserve `charcoal_dust` as the canonical item ID and display it as Charcoal Powder. During the approved legacy migration, convert each saved `smoke_powder` quantity into the same `charcoal_dust` stack at 1:1, merging any existing quantity; remove the obsolete intermediate only after successful conversion and prevent conversion on later loads. Do not create a competing Charcoal Powder ID or alter unrelated materials. Mythril Plate is a rare `smith` material associated with advanced content; its exact acquisition remains an authoring dependency. Boss Cores retain their existing gameplay identity until broader material classification and recipe eligibility are reviewed. These profession families do not replace the weapon-progression material families `metal`, `fiber`, `timber`, and `cores`.

The existing player-sale contracts remain in force for eligible `smith` crafting materials sold to the Blacksmith and eligible `alch` ingredients sold to the Alchemist; those sales become purchase-eligible stock on a subsequent qualifying Hub return. Grade I-IV Magic Crystal sources are limited to progression-appropriate dungeon rewards and Merchant stock; do not infer Enchanter sale or player-sale eligibility. `gen` material sale and stock routing remains subject to authored item eligibility and the approved vendor ownership rules.

Crystal quantities and learned-application gold costs are fixed below. The source categories are approved, while exact authored floor sources, reward quantities, probabilities, Merchant prices, and stock limits must be established before implementation. Do not invent sources, drop tables, or unlimited supply. Persistent crystal ownership follows the existing shared inventory authority.

## Approved Persistent Systems

These are product requirements, not implementation decisions. Gate 0-4 records the party-owned source of truth and forward-migration direction; implementation must establish exact snapshot fields, validation, and legacy defaults. Gate 0-5 now fixes transaction behavior; the implementation must prove the contract through the qualification obligations below.

### Alchemy Skill

Approved Alchemy activities, XP awards, thresholds, and deterministic output benefits are fixed in the closed Gate 0-3 tables below. Alchemy is distinct from signature-weapon Crafting; M2's no-Alchemy-XP rule is superseded only for the explicitly authored M6.5 recipe crafts.

### Enchanting Skill

The approved Enchanting actions, XP awards, thresholds, discovery bonuses, and learned-recipe cost reductions are fixed in the closed Gate 0-3 tables below. Enchanting remains separate from Alchemy and from the permanent discovered-affix collection; no additional skill gates are implied.

### Discovered Affix Collection

The Enchanter maintains a permanent collection of discovered affix recipes. Disenchanting eligible armor registers its discovered affixes for future use. Knowledge is persistent and independent of Enchanting skill progression. The collection is not the same as ordinary stored modifier instances or consumable modifier inventory.

The approved M6.5 disenchant operation preserves the existing M5 extracted-modifier payout and additionally registers each affix in the permanent recipe collection. Stored modifier instances and learned recipes remain separate concepts. Previously discovered recipes remain known without duplicate collection entries; repeat disenchantment continues to preserve the existing modifier-instance payout. No learned recipe silently creates or duplicates a consumable modifier instance. Gate 0-3 fixes Enchanting awards, crystal quantities, and learned-recipe costs below; Gate 0-5 fixes their preview, confirmation, commit, and retry behavior.

Rings and Pendants remain fixed authored equipment and are not eligible for modifier extraction or disenchantment.

### Vendor Stock And Player-Influenced Inventory

All vendors selling merchandise have finite stock. The Enchanter is service-only and has no merchandise inventory. On a qualifying Hub return after encounter progress, stock is topped up to authored per-item limits: unsold units remain, and replenishment adds only the amount needed to reach the limit. Eligible player-sold `smith` materials/components and `alch` ingredients remain in same-visit buyback escrow until that visit expires. Unrecovered eligible stack quantities then enter a persistent future-stock queue; on subsequent qualifying returns, allocate to the specialist first, eligible Merchant overflow second, and retain unallocated excess in the queue. A unit cannot be buyback property, queued stock, or vendor stock simultaneously.

Approved stock mechanics are fixed; exact authored capacities and per-return stock-generation quantities, source allocations, and any overflow eligibility remain implementation authoring dependencies. A qualifying return does not require a full floor clear, but requires a legitimate dungeon outing with encounter progress. Menu navigation, save/load, restart/refresh, waiting/resting without encounter advancement, immediate no-progress entry/exit, repeated completed interaction, or replaying an already-applied return cannot refresh stock. Specialist stock is allocated first, eligible overflow goes to Merchant, unallocated player-sold eligible stacks remain queued across returns, and an item allocation is never duplicated across vendors.

### Hub Buyback (Approved Product Contract)

Buyback is available only for eligible completed player-to-vendor sales during the current Hub visit; it is not a general undo system. Detailed eligibility, original-payout pricing, expiration, and stock-queue rules are fixed under Gate 0-5 below.

- The player may navigate among vendors and Hub menus without ending buyback eligibility. Leaving the Hub ends that visit's opportunities; a later return does not restore expired entries.
- The originating vendor owns the buyback offer. Eligible sales include authored-eligible general stack goods, alchemical ingredients, smithing materials, uninstalled component stacks, and eligible armor/accessories. Installed components cannot be sold directly. Dismantling, disenchanting, crafting, upgrades, modifier consumption, and other conversions do not create buyback claims.
- Stack buyback restores only the selected outstanding quantity to shared inventory. Component stacks remain keyed by `component_id`; no component UUID is introduced. Partial recovery cannot exceed the original sold quantity.
- Unique armor/accessories are retained with their exact identity, definition, rarity, upgrades, affixes, and other persistent properties while buyback is active. Expiration finalizes the destructive sale: the instance and attached affixes are discarded and never enter future vendor stock.
- The buyback price is exactly the original gold payout for the selected quantity or unique item. Do not recalculate it from current merchandise prices, discounts, or a new valuation.
- Future stock is separate: eligible smithing materials/components sold to the Blacksmith and alchemical ingredients sold to the Alchemist may become available on a subsequent qualifying Hub return. That does not extend buyback eligibility. Gate 0-4 requires bought-back items to be excluded from future stock and defines the expiry event boundary; Gate 0-5 decides post-expiry disposition and qualifies no-duplication transactions.

Buyback does not reverse crafting or destructive conversions. Successfully committed alchemical crafting, component crafting/installation, weapon improvement, armor upgrade/rarity advancement, material/equipment/component dismantling, enchanting, disenchanting, or modifier extraction/consumption remains irreversible under the applicable gameplay contract. Technical rollback of a failed or uncommitted operation remains required.

### Weapon Component Ownership (Gate 0-1A Approved)

Uninstalled tradeable signature-weapon components will be shared inventory quantities keyed by authored `component_id`. Identical components stack regardless of source, and players can buy/sell chosen quantities. Individual component UUIDs, per-instance provenance, and the unique armor/equipment-instance model are **not** used for these stacks.

Installed weapon slots continue to store component definition IDs on the exact Drifter. Installing one owned component consumes one unit from the corresponding shared stack; the outgoing installed component is returned to shared inventory as one unit of its definition, not destroyed. Existing craft-and-install remains the baseline, but its displaced installed component must likewise return to shared inventory. Crafting/improvement materials are not refunded. These resource, slot, and inventory changes must be atomic and checked against exact target/compatibility rules.

**All components may be sold once uninstalled, including recovered starter components.** Installed parts cannot be sold directly. Blacksmith owns player component sales and finite specialist stock; the Merchant may offer eligible component merchandise without taking over Blacksmith crafting/install services. Components qualify for same-visit Blacksmith buyback at their original per-unit sale payout. Unrecovered eligible quantities move to the persistent future-stock queue after expiration and become available only through the subsequent qualifying-return allocation rules. Slice A authors the approved 8g/20g purchase prices, half-price resale, and one-unit per-vendor stock caps.

**Existing crafting contract (preserve unchanged):** `WeaponProgressionService.craft_component()` validates the exact Drifter, authored component, signature weapon and slot; rejects a component already installed in that slot; validates and consumes its authored materials; installs directly; and awards the existing party Crafting XP. The installed-component check is not a lifetime history: once a component is no longer installed, the existing service has no historical restriction against crafting it again. M6.5 must not add a one-per-weapon/Drifter or other lifetime crafting lock, and shared-stack ownership does not change the established crafting eligibility or progression.

The exact representation of starter/default components when displaced, any separately approved removal action, and stale replacement validation need technical qualification. Preserve the current rejection when the incoming definition is already installed, with no stack consumption or partial mutation.

This expressly supersedes the old no-stackable-signature-parts restriction **for uninstalled tradeable components only**. Installed signature-weapon identities and compatibility remain based on existing component definitions. Gate 0-4 must specify persistent stack ownership, current/legacy save migration, validation, atomic buy/sell/install/craft-and-replace behavior, and terminal/browser parity.

## M6.5-D1: Alchemist Pricing And Crafting Efficiency

**Approved direction:** Both benefits are required. Eligible Alchemist merchandise receives a flat 25% purchase discount under Gate 0-2; Gate 0-3 approves deterministic mastery-based output bonuses without reducing recipe inputs.

- A flat 25% purchase discount on eligible Alchemist merchandise, calculated from its authored base price as specified under Gate 0-2.
- Deterministic mastery-based additional output at the approved Alchemy levels below; base ingredient requirements do not decrease.

The intended specialist advantage combines discounted purchases and increased crafting yield, not ingredient reduction. The prior illustration that field costs could be approximately twice the Alchemist's resource cost does not establish an ingredient-efficiency multiplier. Gate 0-3's exact recipes, XP, and output milestones are specified below.

M2 recipes currently have no gold crafting fee; the approved M6.5 recipes add none. Successful recipe crafts award only their authored Alchemy XP, never weapon Crafting XP. Crafting consumes all base ingredients and atomically applies the approved bonus output and one XP award; rejected or failed crafts award no XP or output.

## Gate 0-2: Merchandise Prices And Specialist-First Stock (Closed At Product-Decision Level)

The Alchemist specializes in alchemical ingredients and finished alchemical consumables. Its approved initial merchandise direction is:

| Merchandise class | Eligible goods | Status |
| --- | --- | --- |
| Finished alchemical consumables | Healing Potions, standard Mana Potions, Smoke Bombs | Alchemist priority; standard Mana Potion restores 30% of targeted Drifter's maximum Mana, capped at maximum. Eligible overflow may go to Merchant at its normal price. |
| Alchemical ingredients/materials | Medicinal Herbs, Clean Water, Charcoal Powder, Magic Reagent, Aether Dust, Sulfur | Alchemist priority; eligible overflow may go to Merchant at normal prices. `charcoal_dust` remains the canonical Charcoal Powder ID; legacy `smoke_powder` migrates into it 1:1. |
| Return Talismans | Merchant merchandise only | No Alchemist stock, sale, or discount. The Alchemist separately owns the rare crafting service described under Gate 0-4. |

### Flat Alchemist Discount

The approved discount is flat at 25% for eligible alchemical merchandise, applying equally to ingredients, alchemical crafting materials, and finished consumables. Return Talismans receive no Alchemist discount and remain Merchant-exclusive.

`Alchemist price = base price * 3 / 4`

Every discounted base price must be divisible by four so the resulting price is a whole number of gold. No rounding, fractional currency, or quantity-dependent discount formula is used. Total purchase cost is discounted unit price multiplied by quantity. Merchant overflow uses the normal undiscounted price. Discounts do not alter player resale values unless separately approved. Python remains authoritative for price calculation.

### Approved Merchandise Price Schedule

This exact schedule is approved. The base prices support the flat 25% discount; do not introduce alternate prices, tiers, or rounding.

| Item | Base price | Alchemist price |
| --- | ---: | ---: |
| Medicinal Herb | 4g | 3g |
| Clean Water | 4g | 3g |
| Charcoal Powder | 4g | 3g |
| Sulfur | 4g | 3g |
| Magic Reagent | 8g | 6g |
| Aether Dust | 8g | 6g |
| Healing Potion | 12g | 9g |
| Mana Potion | 20g | 15g |
| Smoke Bomb | 12g | 9g |

The prior lower provisional prices are superseded by this approved schedule. At these prices, one Healing Potion's 3g Medicinal Herb plus 3g Clean Water costs 6g in ingredients versus a 9g finished item. Gate 0-3 separately defines recipe efficiency, quantities, and profession benefits; do not add unapproved fees or XP.

### Specialist-First Shared Merchandise Allocation

Approved direction: vendors draw from a shared Hub merchandise allocation, with each specialist receiving priority for its category and the Merchant acting as overflow. Merchandise is allocated, not duplicated across vendors. For example, if the Hub receives three Healing Potions and the Alchemist's available allocation is two, the Alchemist receives two at its discounted price and the Merchant may receive the remaining one at the normal price.

- Alchemist priority: eligible alchemical ingredients/materials, Healing Potions, standard Mana Potions, Smoke Bombs, and other approved alchemical merchandise.
- Blacksmith priority: weapon components, eligible smithing materials, armor, and other approved physical equipment merchandise.
- Merchant overflow: remaining eligible merchandise after specialist allocation limits are reached; Merchant prices remain undiscounted. Limited Grade I-IV Magic Crystals are Merchant merchandise, supplied only from their approved dungeon reward/Hub stock allocations.
- Merchant-exclusive/general goods, including Return Talismans, are assigned to Merchant from the same shared finite allocation; this does not create duplicate stock. The Alchemist's separate Return Talisman crafting service does not make Talismans Alchemist merchandise.
- Purchases decrement the actual finite stock of the vendor used. Allocation is Python-authoritative and applies when stock is generated or replenished.
- Player-sold materials and components remain eligible for future stock under the already approved vendor-sale contracts.

Exact per-item capacities and stock-generation quantities are fixed in the approved readiness schedule below; runtime stock generation remains later-slice work. The example quantity is illustrative, not a universal limit. This Gate 0-2 update does not change buyback rules.

Gate 0-2 is closed at the product-decision level: the Alchemist discount, approved Alchemist schedule, specialist-first shared stock with Merchant overflow, Return Talisman price, and per-item stock values are recorded below.

## Gate 0-3: Profession, Recipe, And Learned-Affix Contracts (Closed)

Gate 0-3 is closed at the product-decision level. The numerical contracts below are approved and must not be treated as provisional or rebalanced during implementation. Gate 0-4 records the product contract for persistence, migration, stock, and legitimate source categories; exact snapshot fields/schema versions remain technical implementation details. Gate 0-5 adds transaction contracts without reopening these values; implementation qualification must prove those contracts.

### Profession Ownership And XP Thresholds

Alchemy and Enchanting are independent, party-wide professions. Each starts at Level 1, caps at Level 100, persists cumulative XP, derives its level from its own threshold curve, and has a separate progression bar. Neither shares XP with the other or changes weapon Crafting XP.

| Property | Alchemy | Enchanting |
| --- | ---: | ---: |
| Starting level | 1 | 1 |
| Maximum level | 100 | 100 |
| XP per level | 50 | 25 |
| Level 25 cumulative threshold | 1,200 | 600 |
| Level 50 cumulative threshold | 2,450 | 1,225 |
| Level 75 cumulative threshold | 3,700 | 1,850 |
| Level 100 cumulative threshold | 4,950 | 2,475 |

The cumulative threshold formulas are `Alchemy XP for Level N = (N - 1) * 50` and `Enchanting XP for Level N = (N - 1) * 25`. Do not reuse `crafting_experience` or alter the weapon Crafting curve.

### Alchemy Recipes And Mastery Output

| Recipe | Base ingredients | Base output | Alchemy XP per successful craft |
| --- | --- | ---: | ---: |
| Healing Potion | 1 Medicinal Herb + 1 Clean Water | 1 | 10 |
| Smoke Bomb | 1 Charcoal Powder + 1 Sulfur | 1 | 15 |
| Mana Potion | 1 Magic Reagent + 1 Aether Dust | 1 | 20 |

Alchemy level changes output only; it never reduces ingredients:

| Alchemy level | Total output per craft | Bonus output |
| --- | ---: | ---: |
| 1-24 | 1 | 0 |
| 25-59 | 2 | +1 |
| 60-99 | 3 | +2 |
| 100 | 4 | +3 |

These milestones apply to all three recipes. Every operation consumes the complete base recipe and awards its recipe XP exactly once, regardless of bonus output. Multiple operations each consume the full recipe. Output bonuses are deterministic, do not multiply XP, and enter secured shared inventory without changing the existing six-unit carried-supply limit. No crafting fee, random bonus, fractional output, ingredient discount, or weapon Crafting XP is introduced. Failed, rejected, or canceled crafts award no XP or output; spending, output, and XP commit atomically.

Healing Potion behavior remains unchanged. A standard Mana Potion restores 30% of the targeted Drifter's maximum Mana, capped at that Drifter's maximum Mana. This approved effect does not change the recipe, Alchemy XP, output milestones, or merchandise pricing recorded above.

### Smoke Bomb Recipe And Legacy Identifiers

The approved M6.5 recipe replaces the former Smoke Powder intermediate:

`1 Charcoal Powder + 1 Sulfur -> 1 Smoke Bomb`

The v0.7 runtime chain (`Goblin Scrap + Charcoal Dust -> Smoke Powder`, then `Smoke Powder + Grade-I Fiber -> Smoke Bomb`) remains untouched during this documentation update. M6.5's approved new recipe no longer requires Smoke Powder. Preserve `charcoal_dust` as the canonical ID and display name Charcoal Powder; migrate saved `smoke_powder` quantities into `charcoal_dust` at 1:1, merging existing counts. Remove the legacy intermediate from canonical inventory only after successful conversion, and ensure later loads do not migrate it again. Do not create a competing Charcoal Powder ID or alter unrelated materials. The migration must be validated at the existing save-document boundary.

### Return Talisman Exclusion

Return Talismans remain Merchant-exclusive merchandise under the approved 25% markup and finite-stock rules. The approved authored base price is 80g and Merchant purchase price is 100g; the legacy 16g value is superseded.

The separate rare recipe is exactly `2 Boss Cores + 1 Mythril Plate -> 1 Return Talisman`. The Alchemist owns this rare crafting service but does not sell Return Talismans. It yields exactly one item, remains separate from ordinary Alchemy mastery, grants no Alchemy XP or bonus output, uses no ingredient reduction, and receives no Alchemist merchandise discount. Merchant remains the exclusive merchandise seller. The craft requires an ingredient/output preview and explicit confirmation, revalidation, and one durable local commit; cancellation or failed commit changes nothing. It creates no buyback entitlement. Qualifying Boss Core definitions, legitimate/repeatable acquisition, Mythril Plate sourcing/rarity, and exact purchase price remain implementation authoring dependencies; do not add farming systems or loot sources here.

### Enchanting XP And Permanent Affix Discovery

Successful disenchantment and affix application award Enchanting XP by affix grade:

| Affix grade | Disenchant XP | Affix application XP | First-discovery bonus |
| --- | ---: | ---: | ---: |
| I | 10 | 10 | +5 |
| II | 20 | 20 | +10 |
| III | 30 | 30 | +15 |
| IV | 40 | 40 | +20 |
| V | 50 | 50 | +25 |

One successful disenchantment awards base XP for the highest-grade affix extracted from the donor armor. It also awards the discovery bonus separately for each affix definition newly added to permanent knowledge. For example, armor with Grade I and Grade III affixes awards 30 base XP; if both recipes are new, it adds 5 + 15 discovery XP for 50 total. Repeated extraction still awards its grade-based operation XP and the existing M5 consumable modifier-instance payout, but never duplicates a known recipe or repeats its discovery bonus.

A successful application awards XP for the applied affix grade, whether using an existing M5 stored modifier instance or the new learned-recipe operation. Replacing an affix grants no XP for the displaced modifier. Failed, rejected, canceled, or unchanged applications award no XP. Experience must commit atomically with the successful equipment operation.

### Preserve Existing M5 Extraction And Stored-Instance Affixing

M5 remains authoritative for eligible armor extraction, consumable modifier-instance creation, stored-instance application, replacement, compatibility, grade restrictions, donor/displaced-modifier destruction, confirmations, stale-action rejection, and rollback. Existing M5 extraction and stored-instance application keep their authored gold/material costs and confirmation behavior. **They do not gain Magic Crystal costs or Gate 0-3 level discounts.** Gate 0-3 adds Enchanting XP to successful operations and permanent knowledge to eligible disenchanting; it does not replace or duplicate M5 modifier instances. Permanent knowledge never creates an `ArmorModifierInstance`.

Rings and Pendants remain ineligible for disenchantment or modifier extraction.

### Learned-Affix Recipe Application

The Enchanter gains a separate operation to apply a permanently learned affix without consuming a stored modifier instance. It requires known affix knowledge, compatible armor, authored gold, and grade-matched Magic Crystals. Existing M5 compatibility and rarity restrictions still apply; replaced affixes are destroyed as before. Enchanting level changes only the costs, never affix strength. Every attempt presents the target armor, selected affix/grade, compatibility, required crystal/gold costs after mastery, resource sufficiency, and any outgoing affix. An empty-slot application needs no additional destructive confirmation after preview; replacing an installed affix requires explicit confirmation naming its permanent loss. Revalidate the preview against current state before committing.

Let `G` be the applied affix grade (`I=1`, `II=2`, `III=3`, `IV=4`, `V=5`):

| Enchanting level | Matching-grade Magic Crystals | Gold cost |
| --- | ---: | ---: |
| 1-24 | 2 | 8 * G |
| 25-49 | 2 | 7 * G |
| 50-74 | 2 | 6 * G |
| 75-99 | 1 | 5 * G |
| 100 | 1 | 4 * G |

Crystals must match the affix grade exactly; higher-grade substitution is not allowed. At least one crystal is always consumed. Gold remains whole with no rounding. Level 100 costs half the Level 1 gold requirement and one crystal instead of two. These reductions apply only to this new learned-recipe operation, never to M5 extraction or stored-instance affixing.

| Enchanting level | Grade III crystals | Gold |
| --- | ---: | ---: |
| 1 | 2 | 24 |
| 25 | 2 | 21 |
| 50 | 2 | 18 |
| 75 | 1 | 15 |
| 100 | 1 | 12 |

### Magic Crystal Grade V Boundary

| Material | Application grade | Gate 0-3 status |
| --- | --- | --- |
| Grade I Magic Crystal | I | Planned |
| Grade II Magic Crystal | II | Planned |
| Grade III Magic Crystal | III | Planned |
| Grade IV Magic Crystal | IV | Planned |
| Grade V Magic Crystal | V | Reserved for appropriate future content |

Grade V affix definitions already exist under M5. The new Grade V crystal-dependent learned-recipe application remains unavailable until appropriate future content supports it. This does not disable or alter existing Grade V extraction or stored-instance application. Grades I-IV use the approved progression-appropriate dungeon reward and limited Merchant source categories; exact authored sources, price, drop rates, quantities, and stock limits remain dependencies. Grade V has no current source or vendor offer. No grade conversion is allowed. The Enchanter remains service-only.

### Persistence And Transaction Boundaries

Alchemy XP, Enchanting XP, and permanent affix knowledge remain independent party-owned persistent state in the existing save architecture. Gate 0-4 records this ownership direction and requires forward-only runtime/disk migration with legacy defaults and validation; exact field placement and schema versions are selected during implementation. Runtime calculations remain Python-authoritative. Gate 0-5 requires a complete candidate state to commit durably to the local save before the new state is published; failed local writes leave the original gameplay state unchanged. Local success does not wait for or depend on optional remote synchronization. Retry/reload must not duplicate output, modifier rewards, recipe knowledge, or XP; the detailed idempotency and qualification contract is below. These requirements do not reopen the approved numerical contracts above.

## Contract Reconciliation: M2 And M5

M6.5 changes the following named access/economy/progression provisions. Other M2 and M5 behavior remains authoritative unless explicitly revised here.

| Existing contract | M6.5 direction | Preserved behavior / unresolved boundary |
| --- | --- | --- |
| M2-D6 specifies unlimited static Merchant stock. | Superseded: merchandise vendors have finite stock, topped up to authored limits on qualifying encounter-progress returns, with specialist-first allocation and Merchant overflow. | Preserve M2 purchase/sale validation, secured inventory, eligible-item rules, transaction atomicity, authored prices, and half-base resale for eligible goods. The three finished Alchemy outputs are explicitly unsellable; stock values are authored below and runtime replenishment remains later-slice work. |
| M2-D5 specifies shared-inventory Alchemy with no Alchemy level or XP. | Superseded: approved Alchemy recipe crafts award persistent Alchemy XP and deterministic mastery output. | Exact recipe XP and level/output thresholds are specified under Gate 0-3 below. Recipes remain distinct from weapon Crafting; no gold fee or weapon Crafting XP is added. Existing recipe transaction guarantees remain. |
| M2 provides the Preparation/Inventory workflow for carrying supplies. | Hub -> Inventory owns supply packing/unpacking. | Preserve M2 six-unit capacity, carryability, secured storage, exact quantities, atomic load/unload, and dungeon preparation/extraction rules. This changes navigation ownership, not item authority. |
| M5 presents equipment sale/dismantling and modifier extraction/affixing/replacement through Alchemist-owned Hub services. | Service access is reassigned: armor/component commerce and physical equipment services to Blacksmith; modifier/disenchantment/affix services to Enchanter. | Preserve M5 eligibility, instance identity, secured-gear requirements, destructive consequences, explicit confirmations, grade compatibility, and atomic rollback. |
| M5 extraction destroys donor armor and stores its eligible installed modifiers; replacement destroys the displaced modifier. | Enchanter owns these services; successful disenchantment also records permanent affix knowledge and awards approved Enchanting XP. | Preserve every existing extracted modifier instance as a consumable payout. Recipe knowledge is separate and does not replace or duplicate the M5 payout. Gate 0-3 adds XP and a first-discovery bonus without changing M5 extraction costs or behavior; learned-recipe costs are specified below. |
| M5 Rings/Pendants are static and cannot be extracted/disenchanted. | No change. | Accessories remain ineligible for disenchantment and modifier extraction. |
| M5 equipment sale destroys attached modifiers and awards only authored gold. | M6.5 same-visit buyback can restore an eligible sold armor/accessory instance with its exact original properties. | Narrow explicit supersession while a sale has active buyback: retain the exact instance and attached state in escrow, preserving M5's existing destructive-sale confirmation. On Hub-visit expiry, finalize the M5 destructive sale by discarding the instance and affixes; never move it to future stock. Equipment dismantling remains destructive and has no buyback. |
| M2 supply packing/unpacking is presented on the Merchant screen. | Hub -> Inventory owns supply preparation. | Navigation moves away from Merchant; M2 six-unit capacity, carryability, secured-storage ownership, exact quantities, atomic load/unload, and outing rules remain unchanged. |
| M2 shared-stack sale and dismantling are immediate, without a confirmation screen. | Keep eligible ordinary quantity-based sales and shared-stack material dismantling immediate, with M6.5's durable local commit boundary. | No added confirmation for these routine transactions. Material dismantling is irreversible. M5 armor/accessory dismantling and destructive Enchanter services retain their existing confirmations. |
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

`OverworldSession._return_to_hub` and other settlement paths set the party back to Hub, settle/recover the outing, and return the route to its surface entrance. The relevant current semantic actions include `extract`, `return_to_hub`, `return_with_talisman`, and Floor II/III clear finalization; death settlement is driven by the battle outcome. Extraction, Talisman, death, and boss settlement have their own authoritative settlement paths. No stable Hub-visit or Hub-return sequence ID or stock-refresh event currently exists. Re-rendering/navigation is not a Hub return. Gate 0-4 now fixes the requirement for one durable, once-only qualifying-return boundary and persisted visit identity; implementation still needs to connect that boundary to the existing floor-specific evidence. Current Hub transactions also have no general transaction nonce: a repeated affordable purchase/sale is another valid transaction. Existing service validation and stale M5 confirmation protect their own boundaries, not finite-stock refresh idempotency.

### New M6.5 Actions And State

| Planned operation/state | Current support | Change classification and unresolved contract |
| --- | --- | --- |
| Separate Merchant, Blacksmith, Enchanter, and Alchemist entries/views | One `action:merchant` / `MERCHANT` screen only | New navigation and presentation models; vendor identity must be Python-authoritative, not client-only |
| Vendor-qualified merchandise offers and finite stock | Existing `hub_supply` item actions and static `shop_stocked` flag | Modify purchase projection/validation and add finite remaining quantities/vendor offers; implement Gate 0-4 top-up, allocation, persistence, and return evidence |
| Buy armor/equipment merchandise | No equipment buy action or template purchase price/stock field | New authored merchandise and purchase operation; prices/stock/eligible template list remain open |
| Buy/sell component merchandise | No independent component inventory, merchandise price, stock, or component `buy`/`sell` input | **0-1A/0-4 approved:** shared stack counts keyed by `component_id`, quantity-based buy/sell, including recovered starters; implement the party-owned stack and approved future-stock lifecycle. Exact authored component price/capacity remains a dependency. |
| Alchemy discounts and recipe mastery | Current `buy` uses one base price; current recipes use fixed authored costs/outputs | Implement the approved Gate 0-2 price formula and Gate 0-3 recipe XP/output milestones in Python; overlapping goods must not duplicate transaction logic |
| Alchemy profession progression | No Alchemy XP, level, or bar; current `craft_alchemy` awards no XP | Add party-owned persistent state and an award hook to successful approved recipe crafts; numerical XP, thresholds, and output milestones are fixed by Gate 0-3; implement the Gate 0-4 migration contract |
| Enchanting profession progression | No Enchanting XP, level, or bar | Add separate party-owned persistent state and XP hooks to successful approved Enchanter actions; numerical awards/thresholds are fixed by Gate 0-3; implement the Gate 0-4 migration contract |
| Learned-affix collection and use | No known-recipe collection; current affix requires a stored `modifier_instance_id` | Add permanent knowledge alongside the unchanged M5 modifier-instance payout; first-discovery XP and learned-recipe costs/eligibility are fixed by Gate 0-3. Persist/validate per Gate 0-4 and qualify atomic actions under Gate 0-5. |
| Vendor stock, refresh, and player-sold future stock | No vendor inventory, stock quantity, Hub-return ID, or stock event | New persistent state and idempotent return/sale integration under the approved Gate 0-4 top-up, specialist-first, subsequent-return contract; exact authored capacities and allocations remain implementation values |
| Same-visit vendor buyback | No buyback record, Hub-visit identity, or item escrow | Add visit-scoped records and stock separation per Gate 0-4; implement the closed Gate 0-5 eligibility, exact original-payout pricing, expiry disposition, confirmation, durable-commit, and idempotency contract. |
| Legacy Smoke Powder migration | Existing `smoke_powder` intermediate and `charcoal_dust` item ID | Convert saved `smoke_powder` quantities 1:1 into canonical `charcoal_dust` (displayed as Charcoal Powder), merge counts, and migrate once at the validated save-document boundary |
| Rare Return Talisman crafting | No such service | New Alchemist-owned rare craft service; Merchant remains the only merchandise seller. Preserve the fixed recipe and all Gate 0-3 exclusions from Alchemy XP/efficiency. |

All future browser commands must continue through `dd_bridge` to typed inputs and the shared session/domain services. A second client-side catalog, price calculator, profession tracker, stock inventory, or affix collection would violate the existing architecture.

## Gate 0-1A: Shared Component Stacks And Replacement (Approved)

**Existing implementation evidence (v0.7):** `WeaponComponentSpec` definitions use `component_id` and `slot_id`. A Drifter's `SignatureWeaponState.components` currently maps weapon slots to definition IDs in `PlayerState`. `WeaponProgressionService.craft_component` spends shared materials, installs on the exact Drifter, awards party Crafting XP, and discards the previous installed definition. There is currently no uninstalled component stock, sale price, purchase input, quantity transfer, unequip action, or separately owned part.

**Approved new contract:**

1. **Shared stacks:** Track uninstalled tradeable components by `component_id` and nonnegative quantity in player shared inventory. Identical definitions merge into a stack. No per-component UUIDs or source/provenance objects.
2. **Install from inventory:** Require an owned unit, exact recruited Drifter, correct slot and weapon compatibility; spend one unit and install the corresponding definition ID.
3. **Replace:** Return the outgoing installed component definition as one unit in the shared inventory, including starter/default parts. A replacement with an owned part consumes the incoming unit and credits the outgoing unit in the same validated transaction.
4. **Craft-and-install:** Preserve the existing direct craft/install pathway, including exact-target/weapon/slot validation, current `already_installed` rejection, authored material spending, and Crafting XP awards. Credit the outgoing installed component to shared inventory. No spent crafting materials are refunded. The market's quantity controls do not alter the existing craft action.
5. **No new crafting history:** The existing `already_installed` check applies only while the same definition occupies that slot. Do not add lifetime, per-Drifter, per-weapon, or other historical crafting restrictions. Crafting may be performed again under the existing rules after the prior definition is no longer installed.
6. **Trade:** Sell any owned, uninstalled component, including recovered starter components, to the Blacksmith in a chosen quantity. Never sell a part directly from an installed slot. Purchases through eligible vendor offers add the chosen quantity to the shared stack; the Blacksmith has finite stock and player-sold parts become purchase-eligible only on a subsequent qualifying Hub return.
7. **Authority and atomicity:** Exact-target and compatibility checks, sufficient inventory/stock, gold and resource spending, displaced-part return, and persisted state updates must not partially succeed or duplicate items on stale, repeated, rejected, or failed-save submissions. Gate 0-4 fixes the stock/return lifecycle; Gate 0-5 fixes durable local commit and duplicate/stale behavior. Exact authored prices/capacities and implementation details remain dependencies; qualify the approved behavior with the test obligations below.

The earlier alternatives of unique instances and deferring component trading are **rejected** for M6.5. The historical no-stackable-signature-parts contract is superseded only for uninstalled tradeable component stacks; installed weapon slots remain definition-based.

**Implementation details to resolve without changing the crafting contract:** identify starter/default component definitions and their returned stack units; implement and validate shared component counts; define migration defaults for older saves; and provide quantity-based terminal/browser purchase and sale. If the incoming component is already installed, retain the existing rejection without consuming inventory. New optional component removal is not approved. Exact component merchandise prices and stock remain authored dependencies; same-visit buyback uses the exact original sale payout under Gate 0-5.

## Enchanter Modifier And Recipe Ownership (Gate 0-1B Approved)

The current lifecycle is:

1. Generated armor stores modifier definitions by grade in `EquipmentInstance.modifier_slots`; the installed value is a definition ID, not a modifier-instance ID.
2. `AlchemistService.preview_extraction` accepts secured, unequipped armor only, requires at least one modifier, and aggregates each modifier's authored gold/material extraction costs.
3. Confirmed extraction destroys the donor armor and creates one new secured `ArmorModifierInstance` per installed grade. Each instance stores a unique UUID, `definition_id`, `source_id`, and `secured`; grade, compatibility, and effects resolve from the immutable authored `ArmorModifierSpec`.
4. Affixing requires an exact owned, secured modifier instance and secured armor, enforces compatible armor slot and rarity-supported grade, spends authored gold/material costs, consumes the incoming instance, and installs its definition ID. Replacing a same-grade modifier permanently destroys the displaced definition; it is not returned to inventory.
5. Under M5, sale/dismantling destroy attached modifiers; Ring/Pendant items are not modifier-bearing and are excluded from extraction/disenchantment. M6.5 buyback narrowly supersedes immediate modifier destruction for eligible equipment sales during the active Hub visit so the exact item can be restored; on expiry, discard the item and attached modifiers to finalize the destructive sale. Equipment dismantling remains destructive and is not reversible through buyback. Preserve all applicable confirmations and candidate-state rollback.

There is no permanent recipe-learning state today. The approved additive contract is:

- A successful eligible disenchantment preserves the M5 result: destroy the eligible donor armor and create the existing secured consumable `ArmorModifierInstance` payout for each installed grade.
- The same operation permanently registers the armor's affix definitions in the Enchanter's known-recipe collection. Already-known definitions remain known without duplicate collection entries.
- Repeated disenchantment continues to grant the existing M5 modifier-instance payout. Permanent knowledge never silently creates or duplicates a consumable instance.
- Modifier instances remain consumable inputs for the existing affix operation. Applying a learned recipe without a stored instance is a distinct new action, with costs and eligibility still to be defined.
- Enchanting skill is a separate persistent progression system. Gate 0-3 fixes the XP awards, repeat-discovery progression, crystal quantities, and learned-recipe application costs; Gate 0-5 fixes preview, confirmation, durable commit, and retry behavior.

Preserve M5's armor-only extraction, donor destruction, secured/unequipped requirements, grade compatibility, replacement consequences, explicit confirmations, and atomic rollback. Rings and Pendants remain ineligible.

## Profession And Persistence Audit

The existing Crafting system is the only profession-like progression reference. `PartyState` owns one shared `crafting_experience`; `crafting_level` is derived from `CRAFTING_LEVEL_THRESHOLDS` in `weapon_progression_spec.py`. The current curve starts at Level 1 with 0 XP, advances one level per 10 cumulative XP, and caps at Level 100 / 990 XP. Authored component recipes currently award 10 XP; improvement awards are authored by material grade: Grade I 20, Grade II 30, Grade III 40, and Grade IV 50 XP. Successful component craft/install and slot improvement award XP after their resource transaction; stack dismantling and Tier V attempts award none. It is party-level, persisted in the `party.crafting_experience` snapshot field, and validated against `MAX_CRAFTING_EXPERIENCE`.

This provides an implementation reference for a persistent experience value, derived level, authored threshold curve, and award at a successful domain transaction boundary. It is not a reusable profession framework: there is no generic profession object or shared XP API. Gate 0-3 fixes the independent Alchemy and Enchanting curves and award rules below; Gate 0-4 approves distinct party-owned persistence and forward migration. Reusing a small persistence/validation pattern may be appropriate; reusing Crafting XP, awarding weapon Crafting XP from Alchemy, coupling professions, or changing weapon Crafting behavior is not.

At the audited v0.7 baseline, runtime and disk save schemas were both 24. `GameState.snapshot()` remains the root boundary; `PartyState.snapshot()` owns shared gold/items, Crafting XP, equipment/modifier instances, party/outing state, and Floor II/III run evidence, while `PlayerState` owns per-Drifter advancement and installed weapon slots. Slice B adds the initial party-owned `hub_economy` field and advances runtime/disk schema to 25 with validation and forward migration from schema 24. Slice D will populate the currently empty future-stock and buyback collections. Profile envelope/API/database schemas remain unchanged.

## Gate 0-4: Navigation, Stock, And Persistence (Closed At Product-Decision Level)

Gate 0-4 fixes the behavior below. It does not authorize gameplay implementation, choose exact schema fields or version numbers, or fill the remaining content-authoring values. The closed Gate 0-5 contract below fixes transaction eligibility, pricing, confirmation, expiry disposition, rollback, and duplicate-action semantics; later implementation must qualify them.

### Navigation And Visit Boundaries

- The Hub exposes one `Vendors` entry. That submenu contains Merchant, Blacksmith, Alchemist, and Enchanter. `Inventory` and other existing Hub actions remain separate; Character -> Equipment remains unchanged.
- Switching vendor/Hub menus, saving/loading, restarting/refreshing, or re-rendering never generates stock. Vendor transitions only change the current view.
- A Hub visit is an identity-bearing period at the Hub. Leaving for a dungeon outing ends the current visit's buyback window. A return begins a new visit identity, but it replenishes stock only when the outing was legitimate and made encounter progress.
- A qualifying return does not require clearing a floor. No-progress entry/exit, waiting/resting without encounter advancement, a repeated completed interaction, or replaying an already-processed return grants no additional replenishment.
- Gate 0-4 owns the visit identity, outing association, qualifying-progress proof, applied-return marker, and the expiration event boundary for same-visit buyback. Gate 0-5 fixes which sold property is recoverable, its exact original-payout price, what happens at expiry, confirmation/commit rules, and duplicate/stale-operation behavior.

### Finite Stock And Player-Sold Merchandise

- All merchandise vendors have finite quantities; Enchanter remains service-only. Purchases decrement the selected vendor's actual remaining stock.
- On each qualifying return, retain unsold units and top up eligible stock only to its authored cap; do not replace inventory wholesale. Specialist categories are allocated to the relevant specialist first, then eligible overflow may go to Merchant. A single allocated unit cannot appear at two vendors.
- Components sold to Blacksmith and eligible `smith` materials sold to Blacksmith, plus eligible `alch` ingredients sold to Alchemist, become future purchasable stock only after a subsequent qualifying return. They do not produce an immediate duplicate on the same return. Current-visit buyback escrow is separate and cannot also exist as future stock.
- Save/load preserves the remaining per-vendor quantities, ownership/allocation, pending future stock, current visit, applied-return evidence, and active buyback records. A reload cannot restore purchased units, replenish twice, duplicate a sale, extend an expired buyback, or create gold/items.
- Exact per-item capacities, authored stock-generation amounts, concrete source allocation, and any overflow-specific catalog remain content/implementation dependencies. The top-up and allocation rules themselves are settled.

### Approved Persistent Owners And Migration Boundaries

| Persistent concept | Authoritative owner and existing save boundary | Gate 0-4 requirement |
| --- | --- | --- |
| Alchemy XP, Enchanting XP, known affix definition IDs | Party-wide `PartyState` in the existing `party` snapshot | Persist as separate progress/knowledge; derive levels from their own approved XP curves; reject malformed/duplicate knowledge; provide legacy defaults. |
| Uninstalled component quantities | Shared party inventory in `PartyState`; installed slot definitions remain on each Drifter's `PlayerState` | Persist quantity stacks by `component_id`; preserve installed state and recovered starter parts; migrate old saves with empty uninstalled stacks. |
| Vendor remaining stock and sale-fed future stock | Party-owned economy state in the existing `party` snapshot | Persist vendor ownership, quantities, allocation, and event/return dedupe evidence; keep player shared inventory distinct from vendor-owned stock. |
| Hub visit, outing progress, replenishment application, buyback escrow | Party-owned Hub-economy state in the existing `party` snapshot, correlated with existing route/world/party outing evidence | Persist a unique visit/outing association and exactly-once processing evidence. Preserve exact equipment identity/state while in escrow; keep it distinct from ordinary stock. |
| Legacy Smoke Powder | Existing shared item stacks, normalized at the save-document migration boundary | Convert `smoke_powder` to canonical `charcoal_dust` 1:1, merge existing quantities, remove the old key only on successful migration, and prove subsequent loads do not reconvert. |

Runtime and disk schemas advance forward-only with defensive-copy migrations and historical-save validation. Existing profile envelope, API, and database structures remain unchanged unless implementation demonstrates a concrete need. Save-document validation remains the boundary for migrated canonical state. Old valid saves receive empty/default M6.5-owned state; optional sync/network failure must not retroactively invalidate them.

### Floor Progress Evidence: Source Audit

The product rule requires an authoritative per-outing proof that at least one encounter advanced and that its Hub return has not already replenished stock. The v0.7 model does not yet provide one common durable proof across all floors:

- Floor I has no per-outing run ID in `PartyState`. `OverworldState` stores the current route/cursor, while `WorldState.defeated_encounters` is durable but route-global rather than scoped to a particular outing. `PartyState` holds the current unsecured outing rewards and replay count; these are not a durable return receipt.
- Floor II and III have run IDs and `PartyState.resolved_run_events` scoped to the active run and floor. The settlement methods clear that event history when the run completes, extracts, or fails, so it is not retained as a post-return replenishment receipt.
- `GameState.snapshot()` already separates `world`, `overworld`, and `party` state, but no current `hub_visit_id`, qualifying-return event, or stock-refresh marker exists.

Therefore, M6.5 implementation must add durable outing/progress/return correlation at the approved party-owned save boundary and update it atomically with settlement and replenishment. Reuse existing authoritative encounter/reward outcomes as inputs; do not infer progress from wall time, route display, menu visits, reloads, or repeat commands. The exact field/API and how existing Floor I versus Floor II/III evidence feeds it are implementation details to design and test; no product behavior remains undecided.

### Magic Crystals, Return Talismans, And Consumables

- Grade I-IV Magic Crystals are acquired only through progression-appropriate dungeon rewards and limited Merchant merchandise. Enchanter remains service-only. Grade V remains reserved for future content. Exact eligible floors, rewards/quantities/probabilities, stock caps, prices, and progression gates are authored dependencies. Higher grades never substitute for lower grades. Existing M5 extraction and stored-instance affixing remain crystal-free.
- Merchant is the exclusive Return Talisman merchandise seller; its exact purchase price remains an authored value dependency under the approved 25% markup. The Alchemist owns the separate rare craft service: `2 Boss Cores + 1 Mythril Plate -> 1 Return Talisman`. It grants exactly one item, no Alchemy XP or mastery output, no ingredient reduction, and no Alchemist merchandise discount. Define eligible Boss Core IDs and legitimate advanced Mythril acquisition before implementation; do not invent a farming loop or drops.
- A standard Mana Potion restores 30% of the targeted Drifter's maximum Mana, capped at that maximum. Existing ownership, targeting, consumption, recipe, pricing, Alchemy XP, and output milestones stay as approved.

### Legacy Identifier Migration

Preserve `charcoal_dust` as the canonical item identifier and display it as Charcoal Powder. Convert each saved `smoke_powder` quantity into that stack at 1:1, merge counts, and remove `smoke_powder` from canonical inventory only after successful conversion. Migration must be defensive-copy, forward-only, idempotent across subsequent loads, and covered by historical and current save-document validation. The old Smoke Powder recipe is not used for new crafting; the approved M6.5 Smoke Bomb recipe is `1 Charcoal Powder + 1 Sulfur -> 1 Smoke Bomb`.

### Implementation Qualification Obligations

These are required tests for the later implementation, not tests to add or run during this documentation-only Gate 0-4 update:

- Qualifying return after encounter progress on Floor I, II, and III, including return before a complete floor clear; no-progress entry/exit, menu navigation, save/load, rest/wait, repeated interaction, and duplicate settlement must not replenish.
- Each legitimate return path that may end an outing (extraction, Return Talisman, death, and floor clear) applies at most one replenishment. Test save/reload immediately before and after settlement and prove the same return cannot refresh twice.
- Existing unsold quantity remains; top-up reaches, but never exceeds, each authored cap. Specialist stock receives its allocation first, only eligible overflow reaches Merchant, and total allocation is not duplicated.
- Blacksmith-sold components/materials and Alchemist-sold ingredients enter stock only on a subsequent qualifying return. Same-visit buyback and future vendor stock remain mutually exclusive; moving between vendors or saving/loading preserves the active buyback record and its expiry boundary.
- A save round-trips vendor stock, pending sold stock, visit identity, applied-return evidence, buyback escrow including exact equipment/modifier state, profession XP, affix knowledge, and component stacks. Invalid quantities, IDs, references, or duplicate markers fail validation before reconstruction.
- Legacy v0.7 and other supported historical saves migrate without source mutation. `smoke_powder` plus an existing `charcoal_dust` count merges 1:1; repeat load does not increase the result; failed migration leaves the source and persisted profile unchanged.
- Merchant/Blacksmith/Alchemist/Enchanter navigation and legal actions remain semantically aligned in terminal and browser, while Python alone owns offers, stock, prices, rewards, and eligibility.

## Vendor Stock And Hub-Return Source Audit

Current facts:

- M2-D6 explicitly specifies unlimited static authored Merchant stock. `SupplyItemSpec.shop_stocked` is eligibility only; no remaining quantity is read or written.
- Purchases use `SupplyItemSpec.base_price`, spend shared gold, and add to secured `PartyState.shared_items`. Sales consume only authored sellable shared items and pay `floor(base_price / 2)` per unit. Both live in `HubEconomyService`; the presenter hardcodes one unit per UI action although the service accepts a positive quantity.
- `PartyState.shared_items` is player-owned stock, not a vendor inventory. Equipment and modifier instances are separate unique party-owned collections. No vendor stock count, player-sold future stock, sale receipt, or vendor offer record exists.
- `EquipmentTemplateSpec` has optional sale value and salvage yields, but no vendor buy price or stock. `WeaponComponentSpec` has recipe material costs and Crafting award, but no buy/sale price or stock. Equipment/service sale and stack-item sale are different transactions.
- Hub phase changes and returns are handled by session/party/overworld outcome methods. Extraction, Talisman, death, and boss settlement have their own authoritative settlement paths. The state records route/run/event details, but no stable Hub-visit counter or return event exists. Floor I lacks a per-outing ID and has route-global defeated encounter evidence; Floor II/III run events are scoped while active and cleared on settlement. The approved future-stock categories are Blacksmith-accepted materials/components and Alchemist-accepted ingredients.
- Existing inputs are validated against current views and services recheck phase, resources, item ownership, and IDs. There is no general idempotency key for repeated buy/sell commands. A repeated valid command is a new transaction. Current M5 preview equality protects against stale destructive confirmations; it does not identify a Hub return or prevent duplicate stock refresh.

The M6.5 finite-stock requirement is an intentional revision of only M2's unlimited-stock availability rule. It does not replace M2's secured-storage, authored sellability, sale rounding, or transaction rules. Future state must represent vendor-owned finite stock separately from player-owned shared stacks and atomically account for purchases, player sales, and replenishment. The qualifying-return, top-up, specialist-first, visit identity, and saved-state behaviors are fixed under Gate 0-4; Gate 0-5 fixes buyback/queue and transaction rules. Implementation must qualify local-save rollback and stale/repeated submissions under the test obligations below.

## Existing Test Coverage And Gaps

| Boundary | Existing coverage inspected | Coverage still missing for M6.5 |
| --- | --- | --- |
| M2 shared purchase/sale, carrying, Alchemy | `root/tests/test_hub_economy.py`: purchase storage, invalid quantity, affordability/unknown item, sellability and half-price floor, six-unit load/unload, phase rejection, atomic recipe input/output, no Crafting XP. `test_save_document_boundary.py` covers stored/carried round trips. | Vendor-specific price/stock authority; stock decrement, replenishment and rollback; Alchemy XP; vendor overlap; sale-driven future stock; purchase/save failure boundary. |
| Weapon improvement/component/Tier V/material dismantling | `root/tests/test_weapon_progression.py`: grades/gates, RNG, exact target, component craft-and-install, already-installed/wrong component, replacement effects, dismantle output/atomic rejection, Tier V costs and retry prevention. `root/tests/test_hub_flow.py` and `test_overworld_session.py` cover merchant orchestration and exact target. `test_save_document_boundary.py` covers installed components and Tier V round trips. | Component merchandise or ownership, bought component compatibility, sale/removal, vendor stock, new Blacksmith-only authorization, and persisted transaction rollback for these in-memory service calls. |
| Armor upgrades and rarity | `root/tests/test_armor_progression.py`: authored costs/projections, rarity path, resource rejection, save-failure rollback, accessory exclusion. | Blacksmith-only service routing and any equipment purchase/stock path. |
| Equipment transfer and M5 disposal/modifiers | `root/tests/test_equipment_service.py`: exact Drifter, ownership transfer, safe Rest, phase limits, save failure. `root/tests/test_alchemist.py`: sale/dismantle/extract/affix, armor/accessory eligibility, compatibility, exact instance, destructive confirmations, cancel, stale preview, repeat submission, resource rejection, and save rollback. `test_overworld_session.py` covers equipment confirmation orchestration. | Enchanter-only routing; additive instance payout plus permanent knowledge; repeat-known handling; learned-recipe application; same-visit buyback preserving exact equipment identity/state; expiry and transaction boundaries. |
| Terminal/browser parity | `root/tests/test_terminal_overworld_ui.py`: Merchant shared supply/Alchemy, target IDs, weapon recipes/Tier V, equipment selection and destructive confirmation. `root/web_tests/test_browser_bridge_contract.py`: merchant commands, exact target component craft, equipment commands and target. `root/web_tests/browser_smoke.mjs` includes M5 upgrade/equip/save-reload/transfer/modifier replacement/extraction/sale/dismantle journeys. | Four distinct vendor flows; Hub Inventory preparation; wrong-vendor rejection; finite stock display/transactions; buyback return/cancel/expiry; Alchemist price/efficiency/profession; Enchanter profession/library; player-sold goods availability after return. |
| Persistence/migration | At the audited v0.7 baseline, `root/tests/test_save_state.py` covered current schema 24, schemas 18-23, unsupported future schema rejection, modifier inventory migration, equipment/weapon round trips, and immutable legacy history; `root/tests/test_save_document_boundary.py` covered current equipment and component state. Slice B adds `root/tests/test_hub_economy_state.py`, schema-25 round trips and malformed-state checks, schema-24 migration/backfill coverage, and profile-history fixtures that advance immutable schema-24 records to schema 25. | Vendor transaction updates, profession awards, component ownership changes, stock replenishment, buyback lifecycle, and their transaction-level rollback/idempotency remain for Slices D-E; these use the party state and schema boundary established in Slice B. |

The current tests provide substantial protection for existing service semantics, but they do not qualify the new persistence sources or vendor ownership boundary. Existing M2 purchase/sale/Alchemy operations do not use a save-port candidate commit; tests cover their in-memory atomic mutation, not storage failure rollback. M5 has candidate-state rollback for its confirmed equipment operations. Gate 0-5 therefore requires new or modified M6.5 transactions to commit a complete candidate through the existing local durable-save boundary before publishing state, with focused failure tests; it does not require a general rewrite of unrelated M2/M5 transactions.

## Gate 0-5: Transaction, Confirmation, And Buyback Contracts (Closed At Product-Decision Level)

Gate 0-5 closes the final M6.5 product decisions. It does not authorize gameplay implementation or select schema fields, stock capacities, or authored content values. Gates 0-1 through 0-4 remain unchanged. The following rules are binding implementation contracts.

### Buyback Eligibility, Price, And Expiration

| Sold property or operation | Same-visit buyback | After expiration |
| --- | --- | --- |
| Eligible general shared-stack goods sold to Merchant | Yes, up to the outstanding quantity | Follow only an approved future-stock route; otherwise no new resale path is created. |
| Eligible alchemical ingredients sold to Alchemist | Yes, up to the outstanding quantity | Remaining eligible quantity enters the Alchemist future-stock queue. |
| Eligible smithing materials sold to Blacksmith | Yes, up to the outstanding quantity | Remaining eligible quantity enters the Blacksmith future-stock queue. |
| Uninstalled weapon components, including recovered starter parts, sold to Blacksmith | Yes, up to the outstanding quantity; stacks remain keyed by `component_id` | Remaining eligible quantity enters the Blacksmith future-stock queue. |
| Eligible armor/accessories sold to a vendor | Yes, exact original instance | Buyback expires and the M5 destructive sale is finalized; instance and attached affixes are permanently discarded, not future stock. |
| Installed component, dismantled property, disenchanted donor, consumed modifier, craft/upgrade result, or learned-affix application | No | No buyback entitlement is created. |
| Rare Return Talisman craft | No | Crafting is not a sale and cannot be reversed through buyback. |

The originating purchasing vendor owns the active buyback record. Navigation and save/load within the same Hub visit preserve it; leaving the Hub ends eligibility. Partial stack recovery reduces both the sale entitlement and any future-stock quantity attributable to that sale. Recovery cannot exceed the original sale quantity.

Buyback costs exactly the gold originally paid to the player for the selected property. For stack sales, preserve the original per-unit payout or an equivalent exact transaction record; different sale transactions retain their own payout values. For unique equipment, use the original gold awarded for that instance. Do not recalculate using current prices, discounts, stock, or a new valuation. Existing M2 sale pricing remains authoritative unless a separately approved item contract specifies otherwise.

During the active visit, sold unique equipment remains in buyback escrow with its exact identity, definition, rarity, upgrades, affixes, and other persistent properties. On expiration, finalize the destructive sale: discard the instance and attached affixes, and never transfer it into vendor stock or the future-stock queue. Existing explicit M5 sale confirmation remains required. Dismantling and disenchanting are distinct destructive operations and create no buyback.

### Player-Sold Future-Stock Queue

An eligible sale is first represented by its active same-visit buyback entitlement. Once that window expires, only its unrecovered eligible stack quantity transfers to the persistent future-stock queue. Expired unique equipment is destroyed as above. At a subsequent qualifying return, allocate queued units to the owning specialist up to available authored capacity, then allocate only otherwise-eligible surplus to Merchant capacity. Persist any unallocated excess for later qualifying returns. Existing unsold vendor units remain and stock is topped up to its approved authored limit; never duplicate a unit across escrow, queue, player inventory, or vendor stock. No category gains future resale eligibility by implication.

The approved player-sale queue sources remain limited to eligible `smith` materials and uninstalled components sold to the Blacksmith, plus eligible `alch` ingredients sold to the Alchemist. Other sold goods gain no future-stock route unless an existing explicit offer rule authorizes it.

### Explicit Previews And Confirmations

- **Rare Return Talisman craft:** The Alchemist previews the recipe, both required quantities, available resources, exactly one output, and irreversible ingredient consumption. The player must explicitly confirm. Revalidate recipe, ingredients, and current state; cancellation is inert. A successful craft consumes `2 Boss Cores + 1 Mythril Plate`, creates exactly one Talisman, grants no Alchemy XP/output bonus/ingredient reduction/discount, and is not buyback-reversible.
- **Learned-affix application:** Every application previews target armor identity, known affix and grade, compatibility/rarity eligibility, matching-grade crystal quantity, gold after the approved mastery reduction, resource sufficiency, and any outgoing affix. An empty compatible slot proceeds from preview without an additional destructive-confirmation step. If an installed affix would be displaced, explicitly identify its permanent destruction and require confirmation. Revalidate target identity, costs, compatibility, and current affix state; stale or mismatched confirmation is rejected without mutation.
- **Existing M5 operations:** Preserve M5 confirmation requirements, including stored-modifier affixing, extraction, sale, dismantling, and destructive replacement. The learned-recipe empty-slot rule does not relax the existing M5 stored-instance confirmation contract.

### Durable Local Commit And Rollback

For every new or modified M6.5 transaction, authoritative Python validates and constructs the complete candidate state, attempts the existing local durable save boundary, and publishes the resulting gameplay state only after that local commit succeeds. A failed local write leaves the original state and resources unchanged and must not report success. Covered operations include merchandise purchase/sale, buyback, vendor stock and queued-stock changes, qualifying-return replenishment, component install/replacement, Alchemy crafts and XP, rare Talisman crafting, Enchanting/disenchanting XP and discovery, and learned-affix application. Any new M6.5 state coupled to an existing M5 service commits with that operation.

This is a targeted revision for new or modified M6.5 transactions: existing M2 commerce commonly mutates live state before a later explicit Save, and the new vendor actions must not rely on that behavior for success. Do not redesign unrelated M2/M5 transactions or the sealed persistence architecture. A successful local gameplay save remains successful if optional remote synchronization, networking, or later conflict bookkeeping fails; remote success is not a prerequisite and cannot undo or reapply the locally committed action.

### Duplicate, Stale, And Fresh Operations

The same submitted operation is applied at most once. A retry, duplicate delivery/callback, or resubmission after a lost success response must not spend twice, award twice, duplicate property, repeat replenishment, or reclaim an already-used buyback. Reject stale requests whose target, stock, ownership, resources, visit, entitlement, recipe, or preview no longer matches authoritative state, with no mutation or XP award.

A new deliberate, valid submission remains repeatable: players may buy separate quantities, sell more owned materials, craft the same eligible recipe again, recover another outstanding quantity, or apply another valid affix. Do not introduce a permanent action restriction. Where required, operation identity and completion evidence survive the relevant save/reload boundary. Use the minimum compatible mechanism in the existing authoritative Python/save architecture; clients do not own a second transaction ledger.

### Required Implementation Qualification

These are later implementation test obligations, not tests to add or run during this documentation-only update:

- Buyback: vendor ownership; exact original payout; full/partial stacks and components; recovered starter components; exact unique equipment/affix restoration; visit expiry; save/load; stale/duplicate claim rejection; reducing future-stock entitlement on recovery.
- Future stock: specialist capacity, eligible Merchant overflow, persistent excess queue, later allocation, top-up without replacing unsold stock, mutual exclusion among buyback/queue/vendor inventory, and no future stock for expired unique gear.
- Confirmation: rare Talisman preview/confirm/cancel/stale resources; learned-affix empty-slot preview; explicit destructive replacement confirmation; stale/mismatched preview; preserve existing M5 confirmation behavior after equipment/resource changes.
- Atomicity: local-save failure for each covered operation leaves gold, inventory, components, equipment, modifiers, XP, knowledge, stock, queue, and records unchanged; same-operation retry applies once; fresh valid operations remain repeatable; optional remote failure after local commit does not revert the action.
- Persistence and clients: current/historical save migration, save/load during active Hub visits and around return/expiry, exact transaction evidence, terminal/browser semantic parity, and Python-authoritative prices, eligibility, outcomes, and stock.

## Gate 0-1 Closure And Remaining Implementation Work

The source/action mapping is complete for the exposed commerce, weapon progression, armor/equipment, modifier, supply-preparation, and other Hub actions. Gate 0-1 is **closed at the product-decision level**. No Gate 0-1 product decision remains open; the following approved contracts are binding for M6.5:

- **0-1A, weapon components:** uninstalled tradeable components use shared quantity stacks; installation/craft-and-install returns displaced parts, including starters; recovered components may be sold; current crafting eligibility, material costs, compatibility, and Crafting XP remain unchanged. No lifetime crafting restriction or crafting-material refund.
- **0-1B, Enchanter:** successful eligible disenchantment preserves the M5 modifier-instance payout and additively records permanent affix knowledge without duplicate collection entries. The learned collection and consumable instances remain separate.
- **0-1C, supply preparation:** Hub -> Inventory owns packing/unpacking. M2 carrying and secured-storage semantics remain unchanged.
- **0-1D, immediate shared-stack transactions:** eligible ordinary quantity-based material/item sales and shared-stack dismantling execute immediately without an additional confirmation screen. Armor/accessory dismantling and destructive Enchanter operations retain their existing M5 confirmations. Equipment sale retains its existing M5 confirmation where applicable.
- **Buyback contract:** approved eligible sales may be reversed only through the originating vendor during the same Hub visit, for exactly the original sale payout. Buyback is separate from future stock and cannot reverse a committed crafting or destructive conversion; see Gate 0-5 for component, unique-equipment expiry, and queue rules.

The audit findings remain implementation evidence, not pending product decisions. Gates 0-1 through 0-5 are closed at the product-decision level. Gate 0-4 establishes the approved navigation, visit/return qualification, top-up stock lifecycle, party-owned persistence direction, migration rules, crystal source categories, Talisman crafting ownership, and Mana Potion effect. Gate 0-5 fixes buyback pricing/eligibility/disposition, destructive confirmations, durable local commits, rollback, and stale/repeated-operation behavior. Exact schema fields/version and transaction mechanisms remain technical implementation details; authored stock/source values, eligible Boss Core IDs, Mythril acquisition, and the Return Talisman price are resolved below. The full M6.5 implementation is authorized and is being delivered in bounded slices; Slice B currently implements the state and durable-outing foundation.

## Gate 0 Tracking

| Gate item | Status | Required outcome |
| --- | --- | --- |
| 0-1: Vendor ownership and product direction | **Closed: approved** | Source/action audit complete; 0-1A through 0-1D are closed at the product-decision level. |
| 0-1A: Component ownership/replacement | **Closed: approved** | Uninstalled components are shared stacks keyed by `component_id`; replacement/craft-and-install credits the outgoing component; all recovered parts including starter components may be sold. Preserve existing crafting rules; no lifetime restriction. |
| 0-1B: Enchanter extraction and recipe knowledge | **Closed: approved** | Preserve M5's extracted modifier-instance payout and additionally add permanent affix knowledge, without duplicate collection entries. Gate 0-3 fixes the Enchanting XP/discovery awards and learned-recipe costs; Gate 0-4 owns their persistence. |
| 0-1C: Supply preparation ownership | **Closed: approved** | Hub -> Inventory owns packing/unpacking; all M2 capacity, carryability, secured-storage, quantity, and atomicity rules remain. |
| 0-1D: Immediate shared-stack transactions | **Closed: approved** | Ordinary quantity-based sales and shared-stack dismantling need no additional confirmation; M5 equipment and Enchanter destructive confirmations remain. |
| Hub buyback direction | **Closed: approved** | The originating vendor offers approved eligible sales during the current Hub visit; Gate 0-4 owns visit identity/persistence and Gate 0-5 fixes eligibility, exact original-payout pricing, expiry, and future-stock interaction. |
| 0-2: Merchandise and discounts | **Closed at product-decision level** | Flat 25% Alchemist discount, approved merchandise schedule, specialist-first shared stock with Merchant overflow, and the 80g base / 100g Merchant Return Talisman price are recorded. |
| 0-3: Recipe efficiency and profession progression | **Closed at product-decision level** | Profession thresholds, recipe inputs/outputs/XP, mastery output milestones, Enchanting XP/discovery awards, learned-recipe crystal/gold costs, and standard Mana Potion restoration at 30% maximum Mana are fixed above. |
| 0-4: Navigation, stock lifecycle, and persistence | **Closed at product-decision level** | One Vendors submenu; encounter-progress qualifying return; finite stock top-up, specialist-first/Merchant-overflow allocation; visit and replenishment identity; party-owned persisted vendor/profession/component/affix/buyback state; Grade I-IV crystals from eligible dungeon rewards and limited Merchant stock; Alchemist rare Talisman crafting; 1:1 Smoke Powder migration. Authored source/stock values are fixed below; exact fields/schema versions remain technical implementation details. |
| 0-5: Transactions, confirmations, and buyback | **Closed at product-decision level** | Eight contracts fix: (1) uninstalled-component buyback; (2) exact original-payout pricing; (3) destructive expiry of unique gear; (4) persistent future-stock queues; (5) rare Talisman preview/confirmation; (6) learned-affix preview and destructive replacement confirmation; (7) atomic local durable commits; and (8) same-operation idempotency with fresh-action repeatability. |

Gates 0-1 through 0-5 are closed at the product-decision level. **Overall Gate 0 progress: 5 of 5 gates complete.** Exact fields/schema versions, per-outing evidence, and transaction/idempotency mechanisms remain technical implementation details. Qualification obligations record how to prove the approved contracts; they are not open Gate 0 product decisions. The full M6.5 implementation is authorized; Slice B is the current implementation slice.

## M6.5 Implementation Readiness (Consolidated Review Package)

Gate 0's five decision gates remain closed. This approved readiness package resolves the authored price, stock, source, schema, and transaction contracts using the current `dungeon` repository. The full M6.5 implementation is authorized and is being delivered in the bounded slices below.

### Verified Baseline And Source Owners

- Runtime and disk save schemas are both **24**. `GameState.snapshot()` and `PartyState.snapshot()` are the current root and party boundaries. `PartyState` owns shared items/gold, Crafting XP, equipment/modifier instances, and Floor II/III run events; each `PlayerState` owns installed weapon component IDs. No M6.5 vendor/profession/affix/component-stack state exists.
- `OverworldSession` owns floor starts, encounter results, Rest, extraction, Talisman return, defeat, and floor-clear settlement. Floor I has route-global encounter evidence but no outing ID. Floors II/III have scoped run events which are cleared during settlement. There is no Hub-visit identity or stock-refresh receipt.
- `HubEconomyService` owns current shared-item buy/sell/load/unload and recipe crafting; current stock is unlimited and `shop_stocked` is only an eligibility flag. `WeaponProgressionService` owns component craft-and-install, improvement, Tier V, and Crafting XP. Preserve its current exact-target/current-slot eligibility and do not add a lifetime craft limit.
- `ArmorProgressionService`, `EquipmentService`, and the current `AlchemistService` own armor upgrades, equipment ownership, and confirmed sale/dismantle/extraction/affix transactions. M6.5 changes service routing, not those M5 semantics. `OverworldPresenter`, terminal overworld UI, `root/web/python/dd_bridge.py`, and `root/web/play/js/pyd4.js` are projections/dispatch boundaries; Python remains authoritative.
- Content owners verified: `root/src/app/content/hub_economy.py`, `equipment_spec.py`, `weapon_progression_spec.py`, the four `root/src/app/content/weapons/*/weapon.py` catalogs, enemy tier/item-drop specs, and `root/src/app/content/routes/floor_{one,two,three}/route.py`.

### Proposed Authored Price And Stock Schedule

All prices are whole gold. Merchant uses base price; Blacksmith uses base price; Alchemist uses only the already-approved `3/4` price. Resale uses the existing `floor(base_price / 2)` rule for eligible shared stacks. Armor keeps its existing direct `sale_value_gold`. A dash means not eligible for vendor resale. Stock is authored per item ID; initial stock equals the stated caps for currently unlocked offers. A qualifying return first allocates eligible player-sold queue units to the specialist, then Merchant overflow, then fills remaining authored stock gaps. The maximum new units for one item on one return is the combined vacant capacity shown by its caps; never exceed either cap or duplicate a unit.

| Alchemical ID | Base / Alchemist | Resale and sale owner | Alchemist / Merchant cap | Initial A / M | Max refill | Availability |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| `medicinal_herb` | 4g / 3g | 2g / Alchemist; future queue | 2 / 1 | 2 / 1 | 3 | Start |
| `clean_water` | 4g / 3g | 2g / Alchemist; future queue | 2 / 1 | 2 / 1 | 3 | Start |
| `charcoal_dust` (Charcoal Powder) | 4g / 3g | 2g / Alchemist; future queue | 2 / 1 | 2 / 1 | 3 | Start |
| `sulfur` | 4g / 3g | 2g / Alchemist; future queue | 2 / 1 | 2 / 1 | 3 | Start |
| `magic_reagent` | 8g / 6g | 4g / Alchemist; future queue | 2 / 1 | 2 / 1 | 3 | Start |
| `aether_dust` | 8g / 6g | 4g / Alchemist; future queue | 2 / 1 | 2 / 1 | 3 | Start |
| `healing_potion` | 12g / 9g | Not sellable, regardless of origin | 1 / 1 | 1 / 1 | 2 | Start |
| `mana_potion` | 20g / 15g | Not sellable, regardless of origin | 1 / 1 | 1 / 1 | 2 | Start |
| `smoke_bomb` | 12g / 9g | Not sellable, regardless of origin | 1 / 1 | 1 / 1 | 2 | Start |

The Alchemist schedule and exact 25% discount are approved. Finished consumables remain purchasable and craftable but cannot be sold back; ingredient sale and future-stock rules remain unchanged.

| Smith/general ID group | Base buy price | Resale | Blacksmith / Merchant cap | Initial B / M | Max refill | Sale route and unlock |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `grade_i_metal`, `grade_i_fiber`, `grade_i_timber`, `grade_i_cores` (Scrap metal, Cord, Softwood, Faded Core) | 4g each | 2g each | 2 / 1 each | 2 / 1 | 3 each | Sell to Blacksmith; queue eligible; start |
| `grade_ii_metal`, `grade_ii_fiber`, `grade_ii_timber`, `grade_ii_cores` (Iron, Cotton, Hardwood, Elemental core) | 8g each | 4g each | 1 / 1 each | 1 / 1 | 2 each | Sell to Blacksmith; queue eligible; after Floor I clear |
| `grade_iii_metal`, `grade_iii_fiber`, `grade_iii_timber`, `grade_iii_cores` (Steel, Silk, Ironwood, Overcharged core) | 16g each | 8g each | 1 / 1 each | 1 / 1 | 2 each | Sell to Blacksmith; queue eligible; after Floor II clear |
| `grade_iv_metal`, `grade_iv_fiber`, `grade_iv_timber`, `grade_iv_cores` (Etheral Alloy, Carbon, Elderwood, Singularity Core) | 32g each | 16g each | 1 / 1 each | 1 / 1 | 2 each | Sell to Blacksmith; queue eligible; after Floor III clear |
| `goblin_scrap` | 3g | 1g | Merchant 1 | 1 | 1 | Merchant general stock; player sale remains Merchant-only; no future queue |
| `mythril_plate` | 80g | 40g | Blacksmith 1; Merchant 0 | 0 | 0 authored / 1 sale-fed | Blacksmith may buy; only player-sold units queue; no generated stock |
| `goblin_lord_core` | Not sold | — | 0 / 0 | 0 / 0 | 0 | Boss reward only; no sale or shop stock |

All 16 weapon-progression material IDs become Blacksmith merchandise. This explicitly authors a 4g/sellable value for existing `grade_i_fiber` (currently 2g) and `grade_i_cores` (currently zero and not sellable); those are M6.5 item-catalog revisions, not changes to weapon costs or progression. Keep the `metal`, `fiber`, `timber`, and `cores` families distinct from the broader profession families.

| Magic Crystal ID | Merchant price | Merchant cap / initial | Max refill | Availability and source |
| --- | ---: | ---: | ---: | --- |
| `grade_i_magic_crystal` | 12g | 1 / 1 after unlock | 1 | One deterministic Grade-I crystal on Floor I first clear; Merchant stock unlocks after Floor I clear |
| `grade_ii_magic_crystal` | 24g | 1 / 1 after unlock | 1 | One deterministic Grade-II crystal on Floor II first clear; Merchant stock unlocks after Floor II clear |
| `grade_iii_magic_crystal` | 48g | 1 / 1 after unlock | 1 | One deterministic Grade-III crystal on Floor III first clear; Merchant stock unlocks after Floor III clear |
| `grade_iv_magic_crystal` | 96g | 1 / 0 until unlock | 1 after unlock | Reserved for Floor IV first-clear content; no current source or stock before Floor IV exists |

Magic Crystals are not player-sellable and are Merchant-only; higher grades never substitute. Each current-floor reward is a guaranteed one-time first-clear settlement award (100% on first clear, zero on replay), not a random drop table. Grade V remains reserved and has no price, source, or offer.

| Component group (exact IDs) | Buy price / resale | Blacksmith / Merchant cap | Initial stock | Max refill per ID | Availability |
| --- | ---: | ---: | --- | ---: | --- |
| Sunder-Spire starters: `sunder_spire_blade`, `sunder_spire_grip`, `sunder_spire_hilt`, `sunder_spire_crest`; recipes: `sunder_spire_blade_reinforced`, `sunder_spire_grip_braided`, `sunder_spire_hilt_ashwood`, `sunder_spire_crest_faded` | Starter 8g / 4g; recipe 20g / 10g | 1 / 1 | 1 / 1 per ID | 2 | Once matching Drifter is recruited |
| Sky-Needle starters: `sky_needle_head`, `sky_needle_binding`, `sky_needle_shaft`, `sky_needle_focus`; recipes: `sky_needle_head_balanced`, `sky_needle_binding_conductive`, `sky_needle_shaft_flexible`, `sky_needle_focus_stormglass` | Starter 8g / 4g; recipe 20g / 10g | 1 / 1 | 1 / 1 per ID | 2 | Once matching Drifter is recruited |
| Sathren starters: `sathren_grip`, `sathren_string`, `sathren_limbs`, `sathren_reservoir`; recipes: `sathren_grip_precision`, `sathren_string_taut`, `sathren_limbs_reinforced`, `sathren_reservoir_alchemical` | Starter 8g / 4g; recipe 20g / 10g | 1 / 1 | 1 / 1 per ID | 2 | Once matching Drifter is recruited |
| Needle of Plain Iron starters: `needle_focus`, `needle_binding`, `needle_haft`, `needle_seal`; recipes: `needle_focus_fitted`, `needle_binding_warded`, `needle_haft_ashwood`, `needle_seal_faded` | Starter 8g / 4g; recipe 20g / 10g | 1 / 1 | 1 / 1 per ID | 2 | Once matching Drifter is recruited |

Every sale is to Blacksmith, receives same-visit buyback at its exact 4g/10g per-unit payout, and enters its future-stock queue only after buyback expiry. Merchant may sell its separately allocated overflow at the same purchase price. Purchase creates uninstalled shared stacks; install remains exact-weapon/slot validated, consumes one unit, and returns the displaced component, including a starter, without refunding recipe materials or changing Crafting XP.

| Equipment ID | Purchase price | Player sale payout | Vendor stock cap / initial | Max refill | Authored offer |
| --- | ---: | ---: | ---: | ---: | --- |
| `field_helm` | 24g | 6g to Blacksmith | Blacksmith 1 / Merchant 1; 1 / 1 | 2 | Common, no modifiers, minimum authored stat roll (Constitution +1) |
| `field_chest` | 40g | 10g to Blacksmith | Blacksmith 1 / Merchant 1; 1 / 1 | 2 | Common, no modifiers, minimum authored stat roll (Constitution +1, Spirit +0) |
| `field_gloves` | 24g | 6g to Blacksmith | Blacksmith 1 / Merchant 1; 1 / 1 | 2 | Common, no modifiers, minimum authored stat roll (Strength +1, Dexterity +0) |
| `field_boots` | 24g | 6g to Blacksmith | Blacksmith 1 / Merchant 1; 1 / 1 | 2 | Common, no modifiers, minimum authored stat roll (Dexterity +1, Intuition +0) |
| `iron_ring` | 20g | — | Merchant 1 / 1 | 1 | Fixed authored +1 Intuition; no upgrade, dismantle, or disenchant |
| `wayfinder_pendant` | 20g | — | Merchant 1 / 1 | 1 | Fixed authored +1 Spirit; no upgrade, dismantle, or disenchant |

Purchased armor creates a normal unique secured equipment instance using the fixed common offer above; it does not roll procedural stats or modifiers. Rings and Pendants remain fixed authored items, never procedural and never eligible for disenchantment. Their current templates have no sale value, so they remain non-sellable. Armor sale retains existing M5 sale-value payouts, confirmation, and exact-instance same-visit escrow; expired equipment and affixes are destroyed, not queued.

| General merchandise | Price | Sale payout | Cap / initial | Max refill | Owner |
| --- | ---: | ---: | ---: | ---: | --- |
| `return_talisman` | Base 80g; Merchant 100g (exact 25% markup) | — | Merchant 1 / 1 | 1 | Merchant-exclusive merchandise; no Alchemist price, sale, or discount |

Merchant is the only offer for Talismans. The separate Alchemist recipe remains exactly `2 goblin_lord_core + 1 mythril_plate -> 1 return_talisman`, one output, confirmed, no Alchemy XP or efficiency. The Talisman value of 100g is intentionally a substantial purchase relative to ordinary consumables, while one first-clear Mythril Plate limits the currently authored rare recipe to one craft.

### Acquisition Sources And Balance Notes

- The existing Goblin Lord definition drops two `goblin_scrap` and one `goblin_lord_core` on a normal victory, and the same authored boss archetype appears on Floors I-III. Only `goblin_lord_core` qualifies for the Talisman recipe; two identical cores may be combined. A normal Floor I clear and Floor II clear supply the two cores without requiring replay farming. Existing replay drops and restrictions remain unchanged.
- Add one `mythril_plate` to the Floor II boss's first-clear settlement only. This is a single deterministic M6.5 reward, not a new random table; replay never awards another. It is not normally vendor-generated or Merchant stock. The source makes the recipe attainable in currently playable content after Floor II completion; if this one-time authored reward is not accepted, the recipe has no legitimate Mythril source in current content.
- Grade I/II/III crystals use the corresponding first-clear boss settlement as listed above. Grade IV requires Floor IV first-clear content and is an explicit future-floor dependency, not an early-floor drop. Limited Merchant stock for an unlocked grade is one; each qualifying return tops it up by at most one.
- On schema-24-to-25 migration, grant the corresponding one-time crystal to an existing save for each of `floor_one_cleared`, `floor_two_cleared`, and `floor_three_cleared`; also grant its one Mythril Plate when `floor_two_cleared` is already true. This is a migration backfill of the newly authored first-clear awards, not a replay reward. The schema bump commits the backfill exactly once. New clears award them in the same atomic first-clear settlement that records the floor clear. Test each legacy-clear combination, repeat migration/reload, and confirm replay cannot duplicate these items.
- The fixed armor-shop offers are sourced from the four existing armor templates at their minimum authored stats. This is a new deterministic vendor offer, not a claim that M5's generated Floor II armor reward is already wired into ordinary battle rewards.
- Existing authored enemy gold is 3g/5g/7g/9g for the ordinary Goblin/Warrior/Shaman/Elite tiers and 10g for the Goblin Lord. The 24-40g armor, 20g component merchandise, and 100g Talisman offers are intentionally not trivial one-encounter purchases. These approved authored values do not rebalance enemy rewards.

### Crafted Consumable Sale Eligibility (Resolved)

`healing_potion`, `mana_potion`, and `smoke_bomb` are unsellable regardless of whether they were purchased, crafted, or looted. This explicitly supersedes M2 sellability for those three item IDs and avoids provenance tracking. Their approved purchase/crafting rules remain otherwise unchanged; Slice A disables legacy sale eligibility without adding a new vendor transaction path.

### Proposed Party State, Migration, And Validation

Add one `PartyState`-owned `hub_economy` snapshot object, with the following canonical fields:

| Field | Shape and owner |
| --- | --- |
| `alchemy_xp`, `enchanting_xp` | Nonnegative cumulative integers; independent party-wide tracks, levels derived from the approved curves |
| `known_affix_ids` | Sorted unique authored modifier-definition IDs; distinct from consumable modifier instances |
| `component_stacks` | `{component_id: positive quantity}` for uninstalled shared parts; installed slot IDs remain on `PlayerState` |
| `vendor_stock` | `{vendor_id: {item_id: nonnegative quantity}}` for Merchant, Blacksmith, Alchemist only; Enchanter omitted |
| `future_stock_queue` | Ordered sale-source records `{sale_id, specialist_id, item_id, remaining_quantity}`; player property cannot also be escrow or vendor stock |
| `buyback_records` | `{sale_id, vendor_id, visit_id, item_id, remaining_quantity, original_unit_payout}`; unique equipment stores the exact serialized instance and modifier state instead of quantity |
| `hub_visit_sequence`, `current_hub_visit_id` | Monotonic saved visit identity; a return creates the next identity, vendor navigation does not |
| `outing_sequence`, `active_outing` | Active record `{outing_id, floor_id, has_encounter_progress}`; created on floor launch and marked only with an authoritative encounter victory/progression commit |
| `last_settled_outing_id`, `last_replenished_outing_id` | Durable return/refresh evidence; the same outing ID cannot be settled or replenished twice |
| `transaction_sequence` | Monotonic operation identity; each M6.5 action submits the current expected sequence, and successful local commit advances it once |

Use one forward schema bump: runtime `STATE_SCHEMA_VERSION` **24 -> 25** and disk `DISK_SCHEMA_VERSION` **24 -> 25**, with `migrate_schema24()` following the existing migration chain. Do not change the profile envelope, web/API contract version, or PostgreSQL schema absent a demonstrated need. Historical saves receive zero profession XP, empty knowledge/component queues, valid initial vendor stock for offers unlocked by existing floor-clear flags, the one-time crystal/Mythril backfill for already-cleared Floors I-III as defined above, and empty outing/buyback evidence; existing PlayerState weapon slots, inventory ownership, equipment, and remote history remain untouched. Migration tests must prove the first-clear backfill and 1:1 Smoke Powder conversion each occur exactly once, while preserving existing saved quantities and prior remote revisions.

The same schema-24-to-25 migration converts `shared_items.smoke_powder` into `shared_items.charcoal_dust` at 1:1, merges any existing Charcoal Powder count, and removes the legacy key exactly once. Validate IDs against authored catalogs; enforce integer/nonnegative XP and quantities, stock caps and unlocks, unique known-affix IDs and sale/visit/outing IDs, valid component definition IDs, valid equipment escrow snapshots, and mutually exclusive ownership across shared items, component stacks, buyback escrow, future queues, and vendor stock. Reject malformed current saves before reconstruction.

### Outing Progress And Exactly-Once Refresh

Create a monotonic `outing_id` when `OverworldSession` starts Floor I, II, or III. Expire the previous Hub visit's buyback when the player actually leaves the Hub, move only eligible expired stack sales into the pending queue, and commit the new outing/visit transition locally before publishing it. At each authoritative successful encounter reward/progression commit, set that outing's `has_encounter_progress = true` in the same candidate transaction. This is a single durable eligibility bit, not a second combat/encounter tracker; existing route cursor, defeated encounter state, and Floor II/III run events remain authoritative for battle progress.

Route every legitimate outing end (extraction, Return Talisman, defeat, or floor completion) through one party-state settlement helper. It closes that outing, starts a new Hub visit, and if-and-only-if encounter progress is true and `last_replenished_outing_id` differs, allocates eligible queued sales specialist-first then Merchant, tops remaining unlocked stock to caps, and records the outing ID as replenished in the same local commit. Rest alone, smoke escape, no-progress entry/exit, menu/save/load, and repeated settlement do not qualify. A later outing has a new ID, so deliberate new qualifying returns replenish normally.

### Gate 0-5 Transaction Ownership And Evidence

| Contract | Python owner and state | Focused proof |
| --- | --- | --- |
| 1. Uninstalled component buyback | New `HubVendorService`, backed by `component_stacks` and `buyback_records`; `WeaponProgressionService` still owns install legality | Exact quantity/target, including recovered starters; partial/full recovery; component ownership conservation |
| 2. Exact original payout | `HubVendorService` stores original per-unit payout on each sale receipt; no repricing at buyback | Different sale receipts, price change/discount, partial quantity, round-trip gold |
| 3. Unique-equipment expiry | Existing equipment sale preview/service routed to Blacksmith; escrow keeps exact instance until visit expiry, then destroys it and affixes | Confirm/cancel, exact instance restore, expiry destruction, never queued |
| 4. Specialist-first queue and Merchant overflow | `HubVendorService` plus outing-settlement helper; queue record retains sale source until allocation | Specialist capacity, overflow, excess retention, no duplicate across escrow/queue/stock |
| 5. Rare Talisman craft confirmation | Alchemist-owned explicit preview/confirm service; consumes 2 cores + 1 plate for exactly one | Missing resource, cancel/stale preview, repeat, save failure, no Alchemy XP/output benefit |
| 6. Learned-affix preview/replacement | Enchanter-facing service reuses existing M5 compatibility and candidate-state patterns; known IDs and crystals in party state | Unknown/known, grade/cost, compatible target, empty/replacement slot, destructive confirm, rollback |
| 7. Atomic local durable commit | Every new/modified service builds a complete `GameState` candidate and calls the existing `SavePort`; publish only on success | Injected local save failure leaves gold/items/stock/equipment/XP/visit unchanged; remote sync failure after local save does not undo |
| 8. Same-operation idempotency | `transaction_sequence` is part of party-owned vendor state and every mutation input; stale sequence is rejected, successful local commit advances once | Same sequence retry/reload cannot apply twice; fresh sequence can intentionally repeat; failed save does not consume sequence |

Service routing: `HubVendorService` owns buy/sell/stock/buyback/queue; `WeaponProgressionService` owns craft-and-install/improve/Tier V with component-stack integration; `ArmorProgressionService`/`EquipmentService` retain armor and gear rules under Blacksmith routing; Alchemy recipes and mastery stay in the existing Python economy boundary or one extracted `AlchemyService`; the rare Talisman recipe is an explicit Alchemist operation; existing `AlchemistService` logic is routed through Enchanter ownership and extended only for its separate XP/library/learned-recipe behavior. `OverworldSession` owns visit/outing lifecycle. Terminal/browser expose semantic actions and confirmations only; they do not calculate prices, stock, XP, or legality. Optional remote sync remains outside the local gameplay commit.

### Bounded Implementation Slices

| Slice | Prerequisites | Responsibility and primary seams | Schema | Acceptance and stop condition |
| --- | --- | --- | --- | --- |
| A. Authored catalogs | None | Define validated IDs, prices, caps, unlocks, initial stock, floor rewards, and deterministic shop equipment in `content/hub_economy.py`, `equipment_spec.py`, `weapon_progression_spec.py`, weapon catalogs, and focused new vendor/catalog specs. | No | All IDs resolve; discount/markup/resale arithmetic and cap/unlock validation pass. Stop before changing services or UI. |
| B. State and durable outing foundation | A | Add `PartyState.hub_economy`, `snapshot.py`/`save_document.py` runtime and disk migration 24->25, smoke-powder conversion, visit/outing/return evidence, local candidate-save helpers. | Yes, 25 | Current and historical save round-trips, invalid state rejection, migration once-only, encounter-progress qualification on all floors/return paths, duplicate settlement and injected-write rollback pass. Stop before vendor screens. |
| C. Vendor navigation | A-B | Add the Vendors submenu and separate Merchant/Blacksmith/Enchanter/Alchemist views through `OverworldSession`, presenter, terminal UI, `dd_bridge.py`, and `pyd4.js`; keep Hub Inventory and Character Equipment separate. | No additional | Every semantic command has one owner; wrong-vendor/invalid-phase actions reject; terminal/browser routing parity passes. Stop before new economic calculations in clients. |
| D. Finite commerce and components | A-C | Implement stock decrement/top-up, seller queues, buyback escrow, quantity commerce, armor/equipment offers, and component stack purchases/sales/install recovery through `HubVendorService`, `HubEconomyService`, `WeaponProgressionService`, and existing equipment services. | Uses B | Gold, item/component conservation, exact sale payout, expiry, specialist priority, queue overflow, unique-instance escrow, stale sequence, and local-save rollback pass. Stop before professions/recipe effects. |
| E. Alchemy and Enchanting | A-D and the approved consumable-sale policy | Implement approved new goods/recipes, mastery output/XP, Mana Potions, Talisman craft, crystals/source awards, Enchanting XP/discovery and learned-affix application using the existing services and M5 compatibility checks. | Uses B | Gate 0-3 values exact; recipe and crystal sources/costs, confirmation, replacement, duplicate learning, rollback, and M5 extraction/stored-modifier regression pass. |
| F. Cumulative qualification | A-E | End-to-end Hub-to-dungeon-to-Hub stock journeys; terminal/browser semantic parity; historical migration, save/reload, transaction failure, supported runtime, content/build, root/web/service and exact-SHA hosted CI. | No new unless a demonstrated defect | All M6.5 acceptance bullets below pass on the same implementation SHA; record runtime evidence and residual risks. Stop on unrelated baseline browser failures rather than refactoring broadly. |

Slice A adds `root/tests/test_vendor_catalog.py`, extends `root/tests/test_hub_economy.py` for unsellable outputs, and adds a vendor-catalog boundary check to `root/tests/test_content_tooling.py`. Slice B adds `root/src/app/game/hub_economy_state.py` and `root/tests/test_hub_economy_state.py`, extends save/migration and all-floor outing tests, and updates browser/runtime qualification to verify durable checkpoints. Slice C adds vendor routing and terminal/browser projections with wrong-phase and ownership tests. Slices D-F retain the planned finite commerce, profession, and cumulative qualification work.

### Qualification Baseline And Remaining Boundary

The exact Gate 0 baseline `e66a4f066d2dc7083b1c76075239ba7ab392a76f` has [a failing hosted Actions run](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/43612861248). Root/web tests, content validation, compile, browser build, and the PostgreSQL/migration job passed; the main Tests job timed out late in the existing M5 equipment browser journey while waiting for an overworld option. This documentation-only SHA does not demonstrate an M6.5 gameplay regression. Re-run the established smoke on implementation slices; do not undertake broad browser refactoring unless this failure reproduces and blocks the new semantic flow.

Grade IV Crystal sourcing remains a future Floor IV content dependency. The consolidated readiness package and all Gate 0 product decisions are approved. Slices A-E are implemented, with Slice E locally qualified as recorded above. Slice D's exact-SHA hosted qualification is recorded above and is green. Slice E's exact-SHA hosted qualification remains pending. Slice F remains the cumulative qualification and pinned MicroPython executable gate.

Implementation closure still requires the sealed M2 carrying/economy guarantees, M5 equipment/modifier confirmations, all Gate 0-5 transaction invariants, terminal/browser parity, schema/migration compatibility, content/build validation, relevant root/web/profile/PostgreSQL suites, browser journeys, and pinned MicroPython qualification on the exact final implementation SHA. No unrelated M7-M9 work, broad balance pass, Grade V crystal source, procedural jewelry, new combat effect, or general economy redesign is included.

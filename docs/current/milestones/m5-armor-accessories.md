# M5 Persistent Armor And Accessories Implementation Plan

> Implementation method: use `superpowers:executing-plans` for native gate-by-gate execution. This is planning, not permission to interrupt earlier foundational work.

**Status:** Draft for review, 2026-10-29. Revalidate repository details after M1-M3 and accepted M4A.

**Goal:** Add persistent, swappable armor and accessories whose original pieces retain investment and can reach the supported progression ceiling regardless of acquisition floor.

**Architecture:** Authored equipment definitions are separate from owned item instances and exact-Drifter equipped references. Integrate the existing loot, trade, stat/effect composition and save boundaries; do not make armor an extension of stackable materials or replace signature weapons.

**Tech stack:** Existing Python content/player/game/presentation layers, merchant/inventory actions, validated saves, terminal/Pyodide adapters and the shared qualification stack.

## Authority And Dependencies

- [Armor design](../../future/armor.md), controlling ownership, permanent viability, equipment separation, and narrow first implementation scope.
- [Economy](../../future/dungeon-progression-difficulty-and-economy.md), accessories, secured/unsecured equipment and trader/drop roles.
- [Roadmap](../development-roadmap.md), M5/shared constraints; [M1](m1-permanent-roster.md) roster ownership, [M2](m2-preparation-trading-escape.md) trade/salvage and provenance, [M3](m3-character-advancement.md) effect composition, [M4A](m4-enemy-progression.md) reward sources.

M5 can start after accepted M4A; it does not depend on M4B's four-member boss. M4B uses M5's accepted equipment contract afterward. The armor source says not to interrupt unfinished foundations: this entry dependency satisfies that instruction rather than overriding it.

Non-goals: randomized replacement signature weapons, transmog required for viability, all armor sets/rarity rolls, cosmetics, equipment degradation, PvP normalization, or assuming accessory upgrades equal armor upgrades. Later drop location is not an automatic power ceiling.

## Verified Baseline And Missing Contracts

At `8099b895`, `PlayerState` has equipment slots `weapon`, `off_hand`, `head`, `body`, `accessory` and basic inventory/equip/unequip methods. These placeholders do not implement the proposed Helm/Chest/Gloves/Boots plus accessory system. Disk reconstruction accepts known authored weapon payloads or null, not arbitrary persistent armor instances. The equipment presenter is not a complete armor ownership/loadout flow.

Shared loot/material stacks, dismantling, signature-weapon source state, and projected weapon bonuses exist. M1/M2/M3/M4A will change surrounding contracts. Inventory objects or a new display card alone cannot satisfy persistent instance identity, upgrades, authoritative effects, or provenance. Re-audit at entry before choosing new files.

## Canonical Equipment Contract

Every owned piece has a stable instance identity, an authored definition ID, source/provenance, and only its actual persistent investment/rolled source fields. Equipped state references a valid owned instance in a legal slot on an exact recruited Drifter. Two identical-looking pieces with different investment remain distinct. One instance cannot be equipped twice, owned in two inventories, sold and still referenced, or recreated after disposal.

Choose ownership/transfer policy at Gate 0: per-Drifter ownership versus shared storage with exact equipped references is not settled by the word "owned." Either approved model must support safe inspection, transfer where allowed, swap, upgrade, sale, dismantle, and save/reload without implicit lead targeting. Preserve canonical signature-weapon ownership and its craft-and-install model.

Primary armor slots are Helm, Chest, Gloves, Boots. Accessory vocabulary/slot count must be resolved against the economy's ring/pendant and armor's ring/amulet suggestions. Do not infer extra slots from the current `off_hand` placeholder or silently migrate a generic accessory into an arbitrary new slot.

Every supported early/late armor piece can reach the same supported maximum progression. Authored profiles/effects may differ; rarity may change identity, acquisition, frequency or upgrade economics, not disqualify a common early piece from reaching the ceiling. Approve the actual upgrade formula/cap and effect stacking order before deriving statistics; do not invent a set system to prove viability.

Swapping retains the unequipped item's instance and upgrade source state. Equipping, upgrading, selling, or dismantling validates exact ownership, target, slot, eligibility, quantities/cost, provenance and current references before any mutation. Equipped-item disposal must reject or atomically unequip under the approved policy; never leave a dangling reference. Rewards found during the outing remain unsecured under the approved equip/use policy; equipping them must not launder them into permanent secured equipment on death.

## Owners, Persistence, And Client Projection

Authored definitions own family, slots, eligibility, base profile/effects, upgrade curve/cost references, sale value and salvage rules. Runtime ownership/inventory owns instance IDs and investment. The Drifter owns equipped references; M3 composes derived effective stats/moves/resources. Game/run state owns acquisition security and pending equipment rewards. Do not persist derived armor totals that will be applied again on load.

Expected integration areas: current item/content definitions and catalog tooling, `root/src/app/player/player_state.py`, `inventory.py`, `root/src/app/game/party_state.py`, trade/action services introduced by M2, effect composition from M3, rewards from M4A, session/presenter models, and existing save/profile validation. Exact new modules, source fields and APIs are revalidated and mapped at Gate 0.

Migrate old equipment slot keys and known weapon data deliberately, preserving all signature weapon/component/Tier V state and any valid existing objects. Old saves gain no free armor or random rolls. Validate instance-ID uniqueness, definitions, upgrade bounds, permitted effects, security provenance and references before reconstruction. A missing definition is a load error, not a replacement from current loot tables. Keep immutable historical remote revisions and use ordinary current-revision advancement; no envelope/API/database redesign is required by owning equipment.

Terminal and browser expose the same owned/loadout views, exact target selector, upgrade/equip preview, costs, effect changes, and sale/dismantle confirmation. They submit IDs/actions, not final stats or gold. Recompute maxima according to M3's approved current-HP/mana rule, not a free heal on every equip. Keep compact phone navigation and readable desktop comparison; visual armor rendering is not required.

## Review Focus

- Identical definitions must not collapse distinct invested pieces; Gate 1 checks instance identities and swap/reload.
- One instance must not be equipped twice or disposed while a dangling reference remains; Gates 1/2 check ownership and disposal.
- Equipping an unsecured drop must not protect it from death; Gate 3 checks provenance and every approved return method.
- Recomputing effects must not double bonuses or create free healing; Gate 2 checks repeated equip/load projections.
- Early armor must reach the same supported ceiling as later armor; Gates 0/2 require actual formula and investment proof.

## Gates And Tests

### Gate 0 - Approve Slot, Instance, And Upgrade Policy

- [ ] Resolve M5-D1 through D5 for the narrow slice. Record slot migration, owner/reference representation, instance-ID generation, permitted persistent fields, and M3 stacking order.
- [ ] Author two distinct pieces for one primary slot (recommended Helm) with one approved upgrade path; choose simple, real effects that the accepted resolver/stat contract can represent.
- [ ] Define evidence showing both pieces reach the supported ceiling, including the early one. Freeze inputs/formulas, not final balance.

Proof: finite content/field/transaction tables and migration examples; the narrow slice has a real effect and a real acquisition source.

### Gate 1 - Instance Ownership, Equip, And Swap

- [ ] Red/green proposed ownership/equipment tests: two identical definitions yield distinct instances; wrong slot/target/unowned/duplicate-reference attempts leave state unchanged.
- [ ] Implement canonical instance storage and exact equipped references. Equip and swap transfer references/ownership according to policy, retaining the replaced piece and its investment.
- [ ] Add save/reload and trusted payload rejection in the same gate. Use existing `root/tests/test_player_state.py`, inventory/save tests, plus narrowly scoped new armor tests rather than duplicating all equipment checks per piece.

Proof: own two pieces -> equip A -> swap to B -> back to A -> reload preserves IDs, investment, target and effective state.

### Gate 2 - Upgrade, Sale, And Dismantle Vertical Slice

- [ ] Test upgrade previews against actual effect/cost, insufficient inputs, max cap, RNG failure if approved, and no partial spend. Prove an early piece reaches the same ceiling as the later one.
- [ ] Integrate M2 buy/sell and authored salvage for one owned instance; apply equipped-item disposal policy, consume/remove exactly once, and reject stale repeated disposal.
- [ ] Test that sold/dismantled IDs never reappear on load, failed required persistence cannot duplicate a transaction, and changing equipment does not duplicate passive/weapon bonuses or heal for free.

Proof: the complete one-slot/two-piece flow in real terminal and built browser, with inspection, upgrade, sale, dismantle and exact persistence. Review/accept this slice before expansion.

### Gate 3 - Four Primary Slots, Accessories, And Reward Provenance

- [ ] Extend definitions/eligibility to Helm/Chest/Gloves/Boots and the approved accessory slots. Add only the selected accessory effect/upgrading rules; do not reuse armor curves by assumption.
- [ ] Connect finite enemy/merchant/chest sources available at entry and M6 equipment rewards via the same acquisition service, not separate constructors with different ownership rules.
- [ ] Test cross-slot effects, exact-Drifter transfer where permitted, capped/effective-stat composition, alive/dead targets, and newly found equipment through rest extraction, talisman, death, and boss return. Quest-item exemptions remain M8 decisions.

Proof: secured gear survives ordinary death; unsecured gear does not become permanent just by equipping; all current slots survive reconstruction and profile validation.

### Gate 4 - Client Parity And Milestone Qualification

- [ ] Semantic terminal/bridge tests cover selection, instance inspection, previews, equip/swap/upgrade/dispose rejection and success with matching legal offers.
- [ ] Built-browser journey obtains two pieces, upgrades the early one, changes the selected Drifter, saves/reloads fresh runtime, swaps back, then disposes of an unequipped alternative; compare exact instance/effect/source state.
- [ ] Extend the real probe with a bounded equip/swap/upgrade/snapshot/teardown path. Run shared cumulative tests, browser proof, PostgreSQL/migrations, runtime matrix and exact-SHA hosted checks.

Closure: four primary armor slots and the approved accessory system are real persistent gameplay, the early-piece viability rule is proven, clients match, and signature weapons remain independent. Hand the accepted equipment API/content requirements to M4B and M6; defer unselected set/cosmetic/durability systems explicitly rather than implying they shipped.

## Unresolved Product Decisions

| ID | Decision and blocking gate |
| --- | --- |
| M5-D1 | Ownership/storage/transfer eligibility and armor restrictions; Gate 0 |
| M5-D2 | Armor ceiling, upgrade formula/costs, rarity identity and allowed effect fields; Gate 0; balance numbers remain editable |
| M5-D3 | Ring/pendant versus ring/amulet vocabulary, count and accessory upgrades; before Gate 3 |
| M5-D4 | Equipped-item sale/dismantle policy and confirmation; before Gate 2 |
| M5-D5 | Equipping newly found unsecured gear, its loss/return behavior and stat/resource changes; before Gates 1/3 as applicable |

Unselected examples such as sets, transmog, biome exclusivity or PvP normalization remain for explicit M9 disposition, not hidden M5 closure requirements.

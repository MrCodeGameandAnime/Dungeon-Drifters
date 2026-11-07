# M5 Armor, Procedural Loot, And Modifier Progression Plan

> Implementation method: native, gate-by-gate execution on the existing `dungeon` branch. This plan is planning only; it does not authorize production implementation until the user reviews the revised scope. M4B and Floor III content remain out of scope.

**Status:** M5-D1 through D5 remain approved, with the accessory/disenchant clarification below. The expanded procedural-armor direction was supplied 2026-11-07. Planning is being revised; implementation has not started.

**Goal:** Build persistent armor instances with reproducible authored generation, deterministic investment, grade-aware modifiers, and a distinct Alchemist service, while preserving exact ownership, extraction risk, and fixed accessories.

**Architecture:** Authored armor templates, modifier definitions, and floor rarity tables feed an injected-RNG generator at an authoritative reward boundary. Generated outcomes become unique persisted equipment instances; equipped references remain per Drifter. Armor upgrades, rarity advancement, and modifier extraction/affixing are separate authoritative transactions using existing inventory, resource, save, and combat-effect boundaries.

**Tech Stack:** Existing Python domain/content/persistence layers, current shared inventory and run-event services, terminal/Pyodide clients, pytest/Playwright, PostgreSQL profile service, and pinned MicroPython qualification.

## Scope And Authority

- This plan expands the former bounded authored-equipment slice. It retains the approved ownership, transfer, security, and deterministic-upgrade contracts except where the new rarity direction explicitly refines the old assumption that early and late pieces must have identical total endgame power.
- [Armor design](../../future/armor.md) supplies the permanent-viability and equipment-identity principles. This M5 plan is the more specific implementation contract for procedural armor, rarity, modifiers, and static accessories.
- [Dungeon economy](../../future/dungeon-progression-difficulty-and-economy.md) remains authoritative for secured/unsecured rewards, exits, and the Ring/Pendant slots. This plan narrows its generic accessory-dismantling direction: accessories cannot be modifier-extracted/disenchanted.
- [Roadmap](development-roadmap.md) owns milestone order. M5 consumes M1-M4A ownership, trade, progression, and event contracts. It does not implement M4B, Floor III, or later floor encounters.
- M5 defines a ten-floor rarity-policy/data contract and tests it across floors 1-10. Actual future-floor enemy/source placements remain owned by the milestones that author those floors.

Non-goals: signature-weapon redesign, armor sets, transmog, cosmetics, degradation, PvP normalization, new damage/resistance systems, broad balance tuning, and authoring future-floor encounter content.

## Revalidated Entry Baseline

The current branch is `dungeon` at `421189c0d608ce5d21644534428dde1fc90c47c2`, a documentation-only M5/M4A-review commit on top of the accepted M4A implementation baseline `614586e615e456d2facb778828582c6e9bddbff1`. Production code has not advanced beyond that M4A baseline. Revalidate these versions and owners again when implementation starts.

- Runtime game-state schema is 17; disk schema is 18; profile envelope version is 1. The M5 model needs a forward game/disk migration using the existing migration architecture. Do not assume a profile API, envelope, or database version change is needed.
- `PlayerState` has generic slots (`weapon`, `off_hand`, `head`, `body`, `accessory`) and persists the existing weapon, but there is no armor/modifier instance inventory. Signature-weapon progression remains separate and unchanged.
- `PlayerState.effective_stat()` composes permanent stats with weapon bonuses. M3 combat/passive effects have their own existing projection. M5 must use those boundaries, not add a parallel combat-effect or resistance framework.
- Maximum HP/Mana currently derive from permanent Constitution/Spirit, level, and discovery bonuses. Equipment changes never heal/refill. If an allowed equipment effect later changes a maximum, recalculate and clamp current resources only when the maximum decreases.
- `PartyState` owns shared stack items, carried supplies, gold, and `OutingRewards`; the six-unit limit applies to carried supplies only. `HubEconomyService` handles shop and consumable alchemy recipes. Armor modifier services must be a distinct responsibility and must not change weapon Crafting XP or ordinary consumable alchemy.
- `RunEventService` resolves Floor II drops at the victory boundary and stores event results in `resolved_run_events`; current drops are stack item IDs and quantities. M5 must add equipment-instance evidence to this existing authoritative boundary so load/retry cannot reroll or duplicate a drop.
- Existing death, Return Talisman, Rest extraction, and boss-return owners are `PartyState` and `OverworldSession`. Preserve their reward semantics and extend their candidate-state transactions to equipment instances and equipped references.

Current code/test entry map (revalidate exact APIs on implementation entry): `root/src/app/player/player_state.py`; `root/src/app/game/party_state.py`, `overworld_session.py`, `run_events.py`, and `hub_economy.py`; `root/src/app/content/catalog.py` and content validators; `root/src/app/presentation/overworld_presenter.py` and `overworld_models.py`; `root/src/app/snapshot.py` and `root/src/app/persistence/save_document.py` / `envelope.py`.

Existing test owners to extend before adding new modules: `root/tests/test_player_state.py`, `test_party_state.py`, `test_floor_two_run_events.py`, `test_hub_economy.py`, `test_overworld_session.py`, `test_overworld_presenter.py`, `test_save_document_boundary.py`, and `test_legacy_save_migration.py`. Browser boundaries include `root/web_tests/test_browser_bridge_contract.py`, `test_browser_smoke_contract.py`, and `browser_smoke.mjs`.

## Approved Equipment Contract

### Ownership And Security

- The party owns a shared equipment inventory of unique instances. Every instance has a stable instance ID, authored definition/template identity, source provenance, secured/unsecured status, and persistent progression/generated state. Drifters persist slot-to-instance references.
- Equipment can transfer among recruited Drifters. Equip, swap, inspect, and other per-Drifter actions require the exact target ID. At Hub or a safe Rest, any recruited Drifter may be managed; during an outing only the active pair may change loadouts.
- One instance cannot be duplicated, equipped in multiple slots/owners, or disposed while referenced. All failed/stale operations reject without partial mutation.
- Equipping unsecured gear never secures it. Safe Rest/extraction/boss returns bank it under the existing rules. Death and Return Talisman remove lost unsecured instances and clear only references to those IDs atomically. Secured gear, other equipment, character progression/resources, and signature-weapon investments remain unchanged. Attached modifiers on lost unsecured armor are part of that lost instance; separately stored secured modifiers survive.

### Armor, Rarity, And Modifiers

- Only **armor** is procedural and modifier-bearing in M5. Armor slots are Helm, Chest, Gloves, and Boots.
- Armor instances combine authored slot/family/template/material, rarity, base-stat profile, generated modifier results, unique identity, and investment. Use an injected RNG at the authoritative generation event; persist the actual result so load, retry, view rebuild, and repeated input never reroll it.
- Rarity grades are Common, Uncommon, Rare, Epic, and Legendary. Modifier capacity is respectively 1, 2, 3, 4, and 5. A capacity slot corresponds to its grade: a Legendary item can hold one modifier of each grade, not five arbitrary modifiers. Armor rarity is separate from weapon material grade.
- Modifier definitions are authored and validated with grade, supported effect values, and compatibility. Generated or extracted modifier instances retain exact authored identity/effect values and compatibility when stored or attached.
- Armor stat upgrades and rarity advancement are distinct deterministic operations with separately authored costs. Every armor piece uses the same configurable stat-upgrade cap; early armor can receive full stat investment. Rarity advancement preserves the armor instance identity, its investment, and compatible installed modifiers while increasing rarity/capacity. It is not a random success roll and does not reroll the item.
- Rarity offers more customization, not an automatic universal power multiplier. An early item can remain viable through investment and modifiers, but need not equal every later item's raw profile. Higher rarity appears progressively by dungeon depth; Legendary is unavailable at the opening and is a meaningful normal reward possibility on the final floors. Exact weights, costs, stat ranges, and effect magnitudes are authored/tunable rather than balance locks.
- Use M3-supported stats and combat effects only. M5 does not add elemental, alchemical, status, or other resistance calculations or a second effect engine.

### Static Accessories And Disposal

- Each Drifter has one Ring and one Pendant/Necklace slot. Accessories are fixed authored equipment: they are not procedurally generated, upgraded, rarity-advanced, or given modifier slots in M5.
- Rings and Pendants/Necklaces **cannot be modifier-extracted or disenchanted**. Modifier extraction is armor-only. This does not by itself prohibit an accessory sale or material dismantle; those remain available only if its authored definition explicitly permits them, and neither can produce a modifier.
- Merchant and Alchemist services operate at the Hub on secured gear; disposal requires an unreferenced instance and explicit confirmation. Sell, dismantle, and modifier extraction are different actions with authored outcomes. Extraction destroys one secured armor donor and stores its eligible modifiers; it is never an accessory operation. Sale/salvage availability and proceeds remain definition data.
- Any operation consuming an instance, modifier, gold, or materials is atomic. Never duplicate or partially lose gear, modifiers, or resources on failure.

## Save, Event, And Client Boundaries

- Persist exact generated armor outcomes, modifier instances and attachment, rarity, stat-upgrade investment, ownership, provenance/security, and equipped references. Do not reconstruct random outcomes during loading or store derived effective stats.
- Use the normal forward-only runtime/disk save migration. Legacy saves gain no armor, modifiers, rarity, or random rolls; preserve all valid existing equipment/weapon state. Do not guess-map the generic legacy `accessory` into Ring or Pendant/Necklace. Preserve immutable remote revisions and profile-envelope semantics.
- Validate unique IDs, known definitions, generated value bounds, rarity/capacity/grade compatibility, source/security, resource accounting, and one-owner/one-reference consistency. Missing definitions and malformed saved outcomes fail closed.
- Resolve generated equipment at the persisted reward event. Persist enough event/result evidence to prevent rerolls or duplicate drops across retry, reload, and repeated inputs.
- Candidate-state transactions cover equip/swap, upgrade, rarity advancement, sale, dismantle, extract, affix/replace, reward generation, safe banking, death, and Talisman settlement.
- Terminal and browser clients request semantic actions with exact IDs and display authoritative item/effect/cost previews. Both expose equivalent ownership, loadout, inspection, upgrades, rarity advancement, alchemist actions, disposal, and rejection feedback. Clients do not implement RNG, legality, prices, or derived-stat calculations.

## Implementation Defaults

These are tunable implementation defaults, not additional balance approvals:

- Keep armor rarity, modifier grade, and weapon material grade as distinct data dimensions.
- Keep generation's RNG injectable; author one canonical floor-to-rarity policy for floors 1-10 and persist generated results, not a recipe for rerolling them.
- Start with four deterministic armor stat-upgrade steps (rank 0 through rank 4) and one configurable shared cap. This is a tunable implementation default, not a permanent balance law. Keep rarity advancement separate and deterministic.
- Use the existing shared gold/material inventory and existing atomic transaction patterns. Do not add new currencies, random upgrade failure, or Alchemy XP.
- Keep ordinary consumable alchemy and weapon Crafting XP unchanged. The new Alchemist owns only armor modifier extraction/affixing and any explicitly scoped equipment operations.
- If an armor has no eligible installed modifiers, extraction should be unavailable rather than destroy it for no modifier result. This is a conservative implementation default, not a broader alchemy rule.
- Exact armor templates, modifier values, costs, weights, and sale/salvage outputs stay in authored data and remain tunable.

## Gates

### Gate 0 - Planning And Contract Reconciliation

- [x] Record the inherited M5-D1 through D5 ownership/equip/security approvals and the user's static Ring/Pendant/Necklace, armor-only disenchant clarification.
- [x] Revalidate the current M4A code baseline, migration versions, reward boundary, exits, and test/client owners.
- [ ] Resolve the open modifier replacement/recovery and disposal-of-attached-modifier contracts below before starting the Alchemist gate.

Proof: this plan distinguishes inherited rules, revised scope, tunable authored data, and remaining product decisions. No production implementation starts until this revised plan is reviewed.

### Gate 1 - Persistent Instance Ownership And Equip

- [ ] Define validated armor-template, static-accessory, and instance records; define party-owned equipment storage and per-Drifter slot references.
- [ ] Prove exact targeting, ownership transfer, compatible slots, no duplicate references, active-pair restrictions during outings, and no security change on equip/swap.
- [ ] Add a forward runtime/disk schema migration from the actual entry version. Legacy saves receive no equipment; preserve current weapon, M3, and M4A state. Keep envelope/API/database unchanged unless implementation review establishes a necessary change.
- [ ] Prove save/reload preserves exact IDs, provenance/security, ownership, and equipped references. Reject malformed references and unknown definitions without partial reconstruction.
- [ ] Implement supported equipment-stat composition through existing M3 boundaries. Equipping never heals; when an effect decreases a maximum resource, clamp current value only as required.

Proof: two distinct armor instances can be transferred and swapped between exact recruited Drifters, then save/reload with no duplication, loss, or security promotion.

### Gate 2 - Authored Templates, Modifiers, And Reproducible Generation

- [ ] Define content schemas/validators for armor templates, families, rarity, stat ranges, modifier pools, modifier grades, effect compatibility, and generation policy.
- [ ] Author a small usable catalog that exercises Helm, Chest, Gloves, and Boots; all five modifier grades; and one static Ring plus one static Pendant/Necklace. Use controlled fixtures for rare edge cases; do not author future-floor encounter placements here.
- [ ] Implement injected-RNG generation that returns one fully materialized unique armor instance. Identical authored input plus identical RNG stream gives identical results; generated values remain bounded and compatible.
- [ ] Implement rarity capacity/grade rules: Common 1, Uncommon 2, Rare 3, Epic 4, Legendary 5; each item has at most one modifier of each eligible grade.
- [ ] Persist and reconstruct exact generated stats/modifiers without another random draw. Test duplicate calls/reloads against event evidence and prove one reward event creates at most one instance.
- [ ] Add content validation for duplicate IDs, invalid ranges/grades, unsupported effects, bad slot/family references, impossible capacities, and malformed RNG result data.

Proof: seeded generation is reproducible; the saved instance round-trips byte-for-byte in gameplay-relevant identity/effects; invalid content fails validation.

### Gate 3 - Deterministic Armor Upgrades And Rarity Advancement

- [ ] Implement Hub stat upgrades as a deterministic authored rank track, separate from rarity. One configurable shared maximum applies to all armor; early armor can reach it.
- [ ] Implement Hub rarity advancement as a separate deterministic transaction with authored gold/material costs, preserving instance identity, stat investment, and compatible modifiers while unlocking the new grade capacity.
- [ ] Prove upgrade/advancement preview matches commit, exact resource spending, insufficient-resource rejection, rank/rarity caps, retries, failed-write rollback, and no random outcome on load/retry.
- [ ] Verify stat/effect projection changes once, never writes permanent character stats, never heals/refills, and cannot alter signature-weapon progression.

Proof: one early armor instance advances through its authored stat track and rarity path without replacement, reroll, investment loss, or partial resource spend.

### Gate 4 - Alchemist: Armor Modifier Extraction, Affixing, And Replacement

- [ ] Add a distinct equipment-modifier service; keep `HubEconomyService` consumable recipes and weapon Crafting XP unchanged.
- [ ] Implement separate Hub sale and material-dismantle actions for secured, unreferenced instances, with authored per-item eligibility/results, preview, explicit confirmation, and atomic gold/material accounting. These actions never extract modifiers; static accessories participate only when their authored definitions permit that action.
- [ ] Extraction accepts secured, unequipped armor only, consumes authored gold/alchemical materials, destroys exactly one donor, and creates persistent modifier instances for its eligible installed modifiers. Accessories reject extraction regardless of caller/client.
- [ ] Affixing accepts a compatible modifier instance and armor grade slot, consumes the modifier exactly once plus authored costs, and commits atomically.
- [ ] Implement the approved replacement/recovery behavior only after the open decisions below are answered. Do not guess whether a displaced modifier returns, is destroyed, or can be extracted again.
- [ ] Prove extraction/affix/replacement save/reload, ownership/provenance, sufficient and insufficient gold/materials, invalid compatibility, repeated submission, failed persistence, and no partial mutation.
- [ ] Prove sale/dismantle rejects unsecured, equipped, unknown, stale, and unauthorized instances without mutation; a confirmed action consumes only one instance and grants only its authored result.

Proof: only armor can be disenchanted; sale, dismantle, extraction, and affixing remain distinct; successful transactions consume exact inputs and preserve the defined output; every rejection is mutation-free.

### Gate 5 - Ten-Floor Rarity Policy And M4A Reward Integration

- [ ] Author one tunable floor 1-10 eligibility/weight policy. Legendary is ineligible at the opening and becomes progressively available; final-floor policy makes it a meaningful normal reward possibility. Keep precise percentages provisional.
- [ ] Test every floor's allowed rarity set, progression direction, valid weight totals, modifier pools, and generated stat-quality ranges using deterministic RNG fixtures. Do not require unbuilt floor encounter content.
- [ ] Integrate the generated armor result with `RunEventService` at its authoritative event boundary and persist event/result/instance evidence.
- [ ] Extend existing exits: safe Rest/extraction/boss return banks eligible gear; death and Return Talisman remove unsecured gear plus attached modifiers and clear only affected equipped references atomically. Secured gear/modifiers and unrelated Drifter investment survive.
- [ ] Verify gear remains unsecured when equipped and that carrying capacity still counts consumable supply units only.

Proof: a seeded reward is stable across event retry/load, extraction banks it, death/Talisman removes the unsecured item and attached modifiers with no dangling ref, and secured items remain intact.

### Gate 6 - Terminal/Browser Parity And Cumulative Qualification

- [ ] Add terminal/browser projections and semantic controls for equipment, exact Drifter selection, item inspection, upgrades, rarity advancement, alchemist extraction/affix/replacement, sale, and dismantling. Keep static accessories free of upgrade/modifier/disenchant controls.
- [ ] Add representative browser journey: generate/receive armor -> equip -> upgrade/advance -> save/reload -> inspect/swap -> extract/affix -> safe return; prove the key failed/atomic cases at domain/service boundaries rather than duplicating the full matrix in Playwright.
- [ ] Extend the actual pinned MicroPython probe with bounded equipment/modifier/generation/reconstruction operations and record measured memory results; do not claim qualification without running the pinned binary.
- [ ] Run focused tests, full root/web suites, content validation, compile/build, browser smoke, save migration/profile validation, PostgreSQL service tests, migration-from-zero, Alembic parity, pinned MicroPython matrix, and exact-SHA hosted CI.
- [ ] Review unchanged M1-M4A behavior: party targeting, secured/unsecured exits, M3 effect semantics, weapon progression, and historical save compatibility.

Closure: armor instances and modifiers are persistent and reproducible; fixed accessories remain fixed; armor upgrades and rarity advancement are deterministic; extraction/affixing/disposal are atomic; ten-floor rarity policy is validated; terminal/browser agree; old saves and M1-M4A behavior remain intact; all applicable qualifications pass on the exact accepted SHA.

## Approved Decisions And Scope Changes

| ID | Decision | Status |
| --- | --- | --- |
| M5-D1 | Shared party equipment inventory with unique instances and exact Drifter equipped references; transfers among recruited Drifters; Hub/safe Rest management and active-pair-only changes during outings. | Approved, retained |
| M5-D2 | Armor stat upgrades remain deterministic, finite, authored, tunable, and share one configurable maximum. Add a separate deterministic rarity-advancement path. Early armor remains viable through investment/customization but is not promised identical raw power to every later item. | Approved, refined by expansion |
| M5-D3 | One Ring and one Pendant/Necklace per Drifter. Fixed authored/static equipment: no procedural generation, upgrades, rarity advancement, modifier slots, or disenchanting. | Approved, clarified |
| M5-D4 | Hub sale/dismantle/extraction are distinct authored, confirmed, atomic actions on secured unreferenced items. Modifier extraction/disenchant is armor-only; accessory sale/material dismantle remains definition-gated and never yields modifiers. | Approved, clarified |
| M5-D5 | Equipping never secures outing gear. Existing safe exits bank it; death/Talisman atomically remove unsecured gear and clear only its refs, preserving secured gear and all unrelated character/weapon investment. Attached modifiers follow their armor instance. | Approved, retained |

## Open Product Contracts

These affect ownership or gameplay and must be resolved before Gate 4, not guessed by the implementer:

1. **Replacing an installed modifier:** what happens to the displaced modifier: returned to stored inventory, destroyed, or another explicit recovery path? What costs, if any, apply to replacement?
2. **Selling/dismantling armor with installed modifiers:** are attached modifiers destroyed with the armor, or is any recovery allowed? Modifier extraction is a separate armor-only action, but the interaction with sale/material dismantle needs an explicit rule.

Other numeric content (prices, material quantities, stat values, rarity weights, modifier effects, salvage yields) remains authored and tunable and does not block the architecture gates. The existing plan does not introduce a new resistance system or an Alchemy XP/level system.

## Deferred Beyond M5

M4B/Floor III encounter authoring and actual later-floor source placement, accessory upgrades/modifiers/procedural generation, armor sets, transmog, cosmetics, degradation, PvP normalization, resistance mechanics, and broad balance tuning remain deferred. M5 may define and validate the ten-floor rarity policy but does not author future-floor encounters.

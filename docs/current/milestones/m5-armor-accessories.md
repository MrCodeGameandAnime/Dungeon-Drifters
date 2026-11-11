# M5 Armor, Procedural Loot, And Modifier Progression Plan

> Implementation method: native, gate-by-gate execution on the existing `dungeon` branch. M4B and Floor III content remain out of scope.

**Status:** M5-D1 through D7 approved. M5 is sealed on code SHA `f9bf1ae1af34d0d0402553db60d1391c62f8a826`: hosted CI passed and the exact pinned MicroPython v1.29.0 matrix completed with semantic parity, 1152K stable 3/3, and the expected 1024K memory limit 3/3. The ordinary Floor II route has no authored armor-drop source; live placement remains deferred. The revised procedural-armor scope and destructive Alchemist contracts were approved 2026-11-07.

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

The current branch is `dungeon` at `ab1988b0a534beaef2c574c46d661a6ed507b3e3`, a documentation-only M5 contract update on top of the accepted M4A implementation baseline `614586e615e456d2facb778828582c6e9bddbff1`. Production code has not advanced beyond that M4A baseline. Revalidate these versions and owners at each gate entry.

- M5 entry: runtime game-state schema 17; disk schema 18; profile envelope version 1. Gate 1 advanced runtime/disk schemas to 18/19 using the existing migration architecture. Do not assume a profile API, envelope, or database version change is needed.
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
- Floor I's existing persistence contract accepts outing saves only at an unresolved Rest, so its equipment mutations are offered only at those saveable checkpoints. Floor II permits active-pair equipment changes between rests because its outing snapshots are persistable there. A safe Rest still permits managing any recruited Drifter.
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
- Initial stat-upgrade costs by resulting rank are 10/20/40/80 gold and 1/2/3/4 units of the armor template's Grade-I material. Each armor template authors the stat bonus gained per rank; the current catalog grants +1 to its designated stat.
- Initial rarity-advancement costs are 25/50/100/200 gold plus one Grade-I/II/III/IV core for Common-to-Uncommon through Epic-to-Legendary. These are authored tuning values, not balance locks.
- Use the existing shared gold/material inventory and existing atomic transaction patterns. Do not add new currencies, random upgrade failure, or Alchemy XP.
- Keep ordinary consumable alchemy and weapon Crafting XP unchanged. The new Alchemist owns only armor modifier extraction/affixing and any explicitly scoped equipment operations.
- If an armor has no eligible installed modifiers, extraction should be unavailable rather than destroy it for no modifier result. This is a conservative implementation default, not a broader alchemy rule.
- Exact armor templates, modifier values, costs, weights, and sale/salvage outputs stay in authored data and remain tunable.

## Gates

### Gate 0 - Planning And Contract Reconciliation

- [x] Record M5-D1 through D7, including static Ring/Pendant/Necklace rules and armor-only modifier extraction.
- [x] Revalidate the current M4A code baseline, migration versions, reward boundary, exits, and test/client owners.
- [x] Resolve modifier replacement, sale, and dismantle behavior for installed modifiers.

Proof: the approved scope, destructive-operation confirmations, and transaction outcomes are explicit. No product decisions remain open for these operations.

### Gate 1 - Persistent Instance Ownership And Equip

- [x] Define validated armor-template, static-accessory, and instance records; define party-owned equipment storage and per-Drifter slot references.
- [x] Prove exact targeting, ownership transfer, compatible slots, no duplicate references, active-pair restrictions during outings, and no security change on equip/swap.
- [x] Add a forward runtime/disk schema migration from the actual entry version. Legacy saves receive no equipment; preserve current weapon, M3, and M4A state. Keep envelope/API/database unchanged unless implementation review establishes a necessary change.
- [x] Prove save/reload preserves exact IDs, provenance/security, ownership, and equipped references. Reject malformed references and unknown definitions without partial reconstruction.
- [x] Implement supported equipment-stat composition through existing M3 boundaries. Equipping never heals; when an effect decreases a maximum resource, clamp current value only as required.

Proof: two distinct armor instances can be transferred and swapped between exact recruited Drifters, then save/reload with no duplication, loss, or security promotion. Runtime schema 18 and disk schema 19 are covered; schema-18 migration adds empty equipment ownership without changing historical state. Focused persistence/ownership suite: 279 passed before the final swap case; final full root suite: 2,129 passed. MicroPython portability tests pass against the updated 149-record dataclass manifest; cumulative pinned-binary evidence is recorded in Gate 6.

### Gate 2 - Authored Templates, Modifiers, And Reproducible Generation

- [x] Define content schemas/validators for armor templates, families, rarity, stat ranges, modifier pools, modifier grades, effect compatibility, and generation policy.
- [x] Author a small usable catalog that exercises Helm, Chest, Gloves, and Boots; all five modifier grades; and one static Ring plus one static Pendant/Necklace. Use controlled fixtures for rare edge cases; do not author future-floor encounter placements here.
- [x] Implement injected-RNG generation that returns one fully materialized unique armor instance. Identical authored input plus identical RNG stream gives identical results; generated values remain bounded and compatible.
- [x] Implement rarity capacity/grade rules: Common 1, Uncommon 2, Rare 3, Epic 4, Legendary 5; each item has at most one modifier of each eligible grade.
- [x] Persist and reconstruct exact generated stats/modifiers without another random draw. Test duplicate calls/reloads against event evidence and prove one reward event creates at most one instance.
- [x] Add content validation for duplicate IDs, invalid ranges/grades, unsupported effects, bad slot/family references, impossible capacities, and malformed RNG result data.

Proof: seeded generation is reproducible; the saved instance round-trips byte-for-byte in gameplay-relevant identity/effects; event replay returns the same owned instance without consuming RNG; malformed catalog and RNG values fail closed. Focused armor/equipment/event/persistence set: 191 passed; content validation passed. Gate 6 records cumulative pinned MicroPython evidence and owns the remaining hosted qualification.

### Gate 3 - Deterministic Armor Upgrades And Rarity Advancement

- [x] Implement Hub stat upgrades as a deterministic authored rank track, separate from rarity. One configurable shared maximum applies to all armor; early armor can reach it.
- [x] Implement Hub rarity advancement as a separate deterministic transaction with authored gold/material costs, preserving instance identity, stat investment, and compatible modifiers while unlocking the new grade capacity.
- [x] Prove upgrade/advancement preview matches commit, exact resource spending, insufficient-resource rejection, rank/rarity caps, retries, failed-write rollback, and no random outcome on load/retry.
- [x] Verify stat/effect projection changes once, never writes permanent character stats, never heals/refills, and cannot alter signature-weapon progression.

Proof: one early armor instance advances through its authored stat track and rarity path without replacement, reroll, investment loss, or partial resource spend. Focused progression/equipment/portability set: 63 passed; content validation passed. Final cumulative qualification remains in Gate 6.

### Gate 4 - Alchemist: Armor Modifier Extraction, Affixing, And Replacement

- [x] Add a distinct equipment-modifier service; keep `HubEconomyService` consumable recipes and weapon Crafting XP unchanged.
- [x] Implement separate Hub sale and material-dismantle actions for secured, unreferenced instances, with authored per-item eligibility/results, preview, explicit confirmation, and atomic gold/material accounting. These actions never extract modifiers; static accessories participate only when their authored definitions permit that action.
- [x] Extraction accepts secured, unequipped armor only, consumes authored gold/alchemical materials, destroys exactly one donor, and creates persistent modifier instances for its eligible installed modifiers. Accessories reject extraction regardless of caller/client.
- [x] Affixing accepts a compatible modifier instance and armor grade slot, consumes the modifier exactly once plus authored costs, and commits atomically.
- [x] Replacing an installed modifier requires explicit confirmation naming the incoming modifier, displaced modifier, and permanent loss. On confirmation, destroy the displaced modifier, consume the incoming modifier and authored gold/material costs, and commit atomically. Recovering an installed modifier otherwise requires extraction that destroys its donor armor.
- [x] Selling modified armor destroys all attached modifiers and awards only its authored gold value. Dismantling modified armor destroys all attached modifiers and awards only its authored salvage materials. Neither operation returns modifiers; the player must choose armor extraction to preserve them.
- [x] Sale, dismantle, extraction, affix, and replacement confirmation states state their destructive consequences. Cancellation and failed writes leave armor, modifiers, gold, and materials unchanged.
- [x] Prove extraction/affix/replacement save/reload, ownership/provenance, sufficient and insufficient gold/materials, invalid compatibility, repeated submission, failed persistence, and no partial mutation.
- [x] Prove sale/dismantle rejects unsecured, equipped, unknown, stale, and unauthorized instances without mutation; a confirmed action consumes only one instance and grants only its authored result.

Proof: only armor can be disenchanted; sale, dismantle, extraction, and affixing remain distinct; successful transactions consume exact inputs and preserve the defined output; every rejection is mutation-free.

Proof: Alchemist previews explicitly identify destroyed armor/modifiers and extracted modifier IDs. Confirmation is required for sale, dismantle, extraction, and affixing; stale quotes and cancellation are inert. Replacement consumes the exact incoming modifier and authored resources while permanently losing the displaced definition. Save failure rolls back every operation. Secured gear can be affixed while worn; disposal/extraction remains limited to unreferenced donors. Sale, dismantling, extraction, and replacement round-trip through save/load. Focused Alchemist tests: 34 passed; cumulative M5/equipment/save suites and content validation are recorded below after the gate verification run. No profile API or envelope bump; disk schema 21 adds party-owned modifier instances.

### Gate 5 - Ten-Floor Rarity Policy And Reward Event Support

- [x] Author one tunable floor 1-10 eligibility/weight policy. Legendary is ineligible at the opening and becomes progressively available; final-floor policy makes it a meaningful normal reward possibility. Keep precise percentages provisional.
- [x] Test every floor's rarity ceiling, progression direction, valid weight totals, modifier compatibility, and generated stat-quality ranges using deterministic RNG fixtures. Do not require unbuilt floor encounter content.
- [x] Implement `RunEventService.resolve_armor_reward` as a persisted, replay-safe reward boundary for an authored caller-supplied Floor II source. No ordinary encounter handler or route node invokes this service yet; generated armor is therefore not currently awarded by normal Floor II battle victories.
- [x] Extend existing exits: safe Rest/extraction/boss return banks eligible gear; death and Return Talisman remove unsecured gear plus attached modifiers and clear only affected equipped references. Secured gear/modifiers and unrelated Drifter investment survive.
- [x] Verify gear remains unsecured when equipped and that carrying capacity still counts consumable supply units only.

Proof: deterministic generation checks cover all ten floor policies and their eligible rarity ceilings; the service replay/load contract returns the same materialized instance without rerolling; safe Rest/extraction/boss settlement secures eligible armor; defeat/Talisman discard unsecured armor and clear references across active and benched Drifters while preserving secured gear; equipping does not secure armor or consume supply capacity. The current browser armor-reward journey uses a controlled save fixture, not a live Floor II drop. Related progression/equipment/run-event/persistence suites: 361 passed. Content validation passed (5 enemies, 4 weapons, 4 Drifters, 11 encounters, 3 routes, 2 recruitment events). Hosted profile-service, migration, and CI qualification passed on the original M5 implementation SHA; post-review hosted evidence is recorded below.

### Gate 6 - Terminal/Browser Parity And Cumulative Qualification

- [x] Add terminal/browser projections and semantic controls for equipment, exact Drifter selection, item inspection, upgrades, rarity advancement, alchemist extraction/affix/replacement, sale, and dismantling. Keep static accessories free of upgrade/modifier/disenchant controls.
- [x] Add representative browser journey using a controlled generated-armor save fixture: equip -> upgrade/advance -> save/reload -> inspect/swap -> extract/affix -> safe return; prove the key failed/atomic cases at domain/service boundaries rather than duplicating the full matrix in Playwright.
- [x] Extend the actual pinned MicroPython probe with bounded equipment/modifier/generation/reconstruction operations and record measured memory results; do not claim qualification without running the pinned binary.
- [x] Run focused tests, full root/web suites, content validation, compile/build, browser smoke, and local save migration/profile validation.
- [x] Run PostgreSQL profile-service tests, migration-from-zero, and Alembic parity locally against a dedicated PostgreSQL 17 test container.
- [x] Run hosted CI against the exact pushed M5 SHA.
- [x] Review unchanged M1-M4A behavior: party targeting, secured/unsecured exits, M3 effect semantics, weapon progression, and historical save compatibility.

Gate 6 qualification evidence: root pytest **2,225 passed**; web pytest **70 passed**; profile-service suite **45 passed** against PostgreSQL 17; content validation and compileall passed; browser build produced **170 files**; full Playwright smoke passed through M1-M5, including `M5_BROWSER|ARMOR_PROGRESS_TRANSFER_RELOAD_ALCHEMIST_STATIC_ACCESSORIES|PASS` and `M5_BROWSER|GENERATED_ARMOR_SAFE_RETURN|PASS`. Historical profile fixtures match their schema-era equipment shape; current schema 21 advances are covered from schemas 8, 9, 11, 12, and 15-20.

Hosted qualification: implementation SHA `195049845cbfd09b5ef3cdf5e3927cb339efb4c9`; [GitHub Actions run 42379807072](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42379807072) completed successfully. The Tests job passed root/web tests, content validation, compile, the 170-file browser build, and full browser smoke. The Profile Service (PostgreSQL) job passed all 45 service tests, migration-from-zero, and Alembic model parity (`No new upgrade operations detected`).

Pinned MicroPython evidence: executable SHA-256 `6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA` (v1.29.0, Windows). Native CPython, forced overlay, and pinned MicroPython semantic parity passed. The complete M1-M5 probe passed at **1152K, 3/3**; **1024K** produced the expected memory limit **3/3**. Frontier observations were non-monotonic near the limit: 1048K passed 3/3, 1032K memory-limited 3/3, and 1040K was a transition (2/3 pass). The qualification profile therefore remains the conservative 1152K setting; no sharper heap cutoff is claimed.

The pinned MicroPython evidence above applies to original implementation SHA `195049845cbfd09b5ef3cdf5e3927cb339efb4c9`; it has not been rerun on post-review code SHA `9c7ca7a0a729a317bd802f0f471c4248d82691b6`. The exact recorded executable path was unavailable during review, and a nearby executable had a different SHA-256, so it was not substituted.

Post-review correction: commit `9c7ca7a0a729a317bd802f0f471c4248d82691b6` fixes Rest security changing a live armor instance while its immutable generation event remains unsecured. Its regression covers Floor II victories, Rest recovery, save/reload, replay without reroll, continuing to another encounter, and persisting that victory. Exact-SHA hosted CI passed root pytest **2,226**, web pytest **70**, PostgreSQL service tests **45**, content validation, compile, 170-file browser build and full smoke, migration-from-zero, and Alembic parity: [Actions run 42410870669](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42410870669). At that checkpoint the pinned MicroPython matrix remained pending; it was later completed on the review-fix SHA recorded below.

Additional review corrections: the equipment presenter exposes benched recruited Drifters at safe Rest without leaking equipment selection into Character selection; Floor I equip actions are unavailable away from saveable Rest checkpoints; Floor II map completion follows persisted route progress; and displayed bonuses aggregate repeated stats across equipped pieces. Focused service, presenter, session, and browser-bridge tests passed **137 cases**.

Final qualification for review-fix code SHA `f9bf1ae1af34d0d0402553db60d1391c62f8a826`: [hosted Actions run 42453945121](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/42453945121) passed 2,233 root tests, 71 web tests, all 45 PostgreSQL service tests, content validation, compile, the 170-file browser build and full browser smoke, migration-from-zero, and Alembic parity. The exact pinned MicroPython matrix also passed on this code SHA; details are recorded in [probe.md](../../probe.md). Live Floor II armor-drop placement remains deferred: no ordinary battle currently awards generated armor, and the browser reward journey is fixture-backed. Future placement must add an authored source and connect it to the authoritative reward transaction.

## Approved Decisions And Scope Changes

| ID | Decision | Status |
| --- | --- | --- |
| M5-D1 | Shared party equipment inventory with unique instances and exact Drifter equipped references; transfers among recruited Drifters; Hub/safe Rest management and active-pair-only changes during outings. | Approved, retained |
| M5-D2 | Armor stat upgrades remain deterministic, finite, authored, tunable, and share one configurable maximum. Add a separate deterministic rarity-advancement path. Early armor remains viable through investment/customization but is not promised identical raw power to every later item. | Approved, refined by expansion |
| M5-D3 | One Ring and one Pendant/Necklace per Drifter. Fixed authored/static equipment: no procedural generation, upgrades, rarity advancement, modifier slots, or disenchanting. | Approved, clarified |
| M5-D4 | Hub sale/dismantle/extraction are distinct authored, confirmed, atomic actions on secured unreferenced items. Modifier extraction/disenchant is armor-only; accessory sale/material dismantle remains definition-gated and never yields modifiers. | Approved, clarified |
| M5-D5 | Equipping never secures outing gear. Existing safe exits bank it; death/Talisman atomically remove unsecured gear and clear only its refs, preserving secured gear and all unrelated character/weapon investment. Attached modifiers follow their armor instance. | Approved, retained |
| M5-D6 | Replacing an installed modifier permanently destroys the displaced modifier. Explicit confirmation is required; the transaction consumes the incoming modifier and authored gold/material costs atomically. Installed modifiers can otherwise be recovered only by extracting and destroying the donor armor. | Approved |
| M5-D7 | Selling modified armor destroys its attached modifiers and yields only authored gold. Dismantling modified armor destroys its attached modifiers and yields only authored salvage materials. Neither returns modifiers; preserving them requires Alchemist extraction. Confirm destructive consequences; roll back completely on failure. | Approved |

All remaining numeric content (prices, material quantities, stat values, rarity weights, modifier effects, salvage yields) remains authored and tunable. The existing plan does not introduce a new resistance system or an Alchemy XP/level system.

## Deferred Beyond M5

M4B/Floor III encounter authoring, live generated-armor source placement (including ordinary Floor II encounter drops), accessory upgrades/modifiers/procedural generation, armor sets, transmog, cosmetics, degradation, PvP normalization, resistance mechanics, and broad balance tuning remain deferred. M5 defines and validates the ten-floor rarity policy but does not author live armor-drop sources or future-floor encounters.

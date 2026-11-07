# M5 Persistent Armor And Accessories Implementation Plan

> Implementation method: native, gate-by-gate execution on the existing `dungeon` branch. This plan does not authorize starting M4B, creating a branch, or changing production behavior before implementation is approved.

**Status:** M5-D1 through D5 approved 2026-11-07. Entry baseline revalidated at `614586e615e456d2facb778828582c6e9bddbff1`. Implementation has not started.

**Goal:** Add persistent, swappable armor and accessories whose individual investment survives swaps and whose early pieces can reach the same maximum progression as later pieces.

**Architecture:** Authored equipment definitions are separate from unique owned instances. The party owns one shared equipment inventory; each recruited Drifter equips instance IDs in legal slots. Instance provenance remains authoritative through Hub, outing, extraction, death, and Return Talisman settlement. Equipment effects use M3's effective-stat/combat-effect boundaries; no derived bonuses are saved.

**Tech Stack:** Existing Python content, player/game/presentation layers, shared-item economy, validated saves, terminal/Pyodide clients, pytest/Playwright, and the pinned MicroPython qualification.

## Authority And Dependencies

- [Armor design](../../future/armor.md) owns permanent viability, equipment separation, and the narrow first slice.
- [Dungeon economy](../../future/dungeon-progression-difficulty-and-economy.md) owns secured/unsecured rewards, exits, and accessory context.
- [Roadmap](development-roadmap.md) owns milestone order and shared constraints. M1 roster, M2 trade/exit rules, M3 stat/effect composition, and accepted M4A reward/event behavior are prerequisites.
- M5 follows accepted M4A and does not depend on M4B. M4B consumes the accepted M5 equipment contract afterward. Do not implement M4B or Floor III content as part of M5.

Non-goals: replacing signature weapons, sets, transmog, cosmetics, degradation, PvP normalization, accessory upgrades, new resistance mechanics, broad balance work, or visual armor rendering. M5 authors only the content needed to prove its contracts; later-floor catalogs remain with their owning milestones.

## Revalidated M4A Baseline

The current branch is `dungeon`, tracking `origin/dungeon`, at `614586e615e456d2facb778828582c6e9bddbff1`. Its M4A code includes the post-review Floor II fixes; the latest M4A code correction in its history is `a0aaa53`. The existing untracked `.codex-remote-attachments/` directory is unrelated and is not part of this plan.

- `PlayerState.EQUIPMENT_SLOTS` is still the generic `weapon`, `off_hand`, `head`, `body`, `accessory` tuple. Equipment is stored per Drifter; there is no armor/accessory instance catalog or shared equipment inventory. The signature weapon has its own separately persisted progression state and must remain untouched.
- `PlayerState.effective_stat()` currently composes permanent stats with the equipped weapon's bonuses. M3 passive effects are a separate combat-effect projection. M5 equipment stat bonuses are additive through the effective-stat path, not writes to permanent stats. Scaling helpers retain their M3 cap behavior; direct mitigation continues to read the actual effective stat.
- Current max HP/Mana are derived from permanent Constitution/Spirit, level, and permanent discovery bonuses. Ordinary equipment stat bonuses do not change those maxima. Equip/swap therefore must not heal or refill resources; any later direct max-resource equipment effect is outside this initial M5 effect set.
- `PartyState` owns shared stackable items, carried supply stacks, shared gold, and `OutingRewards` item stacks. The six-unit limit applies to carried supplies, not equipment or found loot. M2's `HubEconomyService` buys/sells stack items at the Hub; weapon progression consumes shared materials.
- M4A Floor II run events resolve encounter drops at the victory boundary and persist the run/event result in `resolved_run_events`. Current event drops and pending rewards are stack item IDs and quantities, not equipment instances.
- Current exit owners are `PartyState` and `OverworldSession`: death discards unsecured rewards and carried supplies, restores the recruited party, and returns to Hub; Return Talisman banks adjusted XP only, loses run gold/items, and returns unused carried supplies; safe Rest extraction and boss settlement bank items under their existing M2/M4A rules. M5 must extend these same transitions for equipment without changing their existing payout semantics.
- Current in-memory game-state schema is 17, disk game-state schema is 18, and profile-envelope version is 1. M5's persisted equipment state requires a forward runtime/disk schema increment (planned 18/19); keep the profile API, envelope version, and database schema unchanged. Revalidate exact migration hooks at implementation entry.

There is no persistent equipment-instance ownership, provenance, upgrade rank, equipment-specific drop result, or exact instance reference in the current M4A save model. M5 must add those contracts rather than treating armor as a stack item or serializing derived stats.

Entry implementation/test map (revalidate exact APIs at each gate): `PlayerState` and per-Drifter equipment in `root/src/app/player/player_state.py`; party inventory/provenance and exit settlement in `root/src/app/game/party_state.py` and `overworld_session.py`; event-boundary drops in `root/src/app/game/run_events.py`; merchant actions in `root/src/app/game/hub_economy.py`; current content in `root/src/app/content/catalog.py` and the authored content/validation tools; presenter models in `root/src/app/presentation/overworld_presenter.py` and `overworld_models.py`; runtime/disk validation in `root/src/app/snapshot.py`, `root/src/app/persistence/save_document.py`, and `root/src/app/persistence/envelope.py`.

Existing test owners to extend before adding new modules: `root/tests/test_player_state.py`, `test_party_state.py`, `test_floor_two_run_events.py`, `test_hub_economy.py`, `test_overworld_session.py`, `test_overworld_presenter.py`, `test_save_document_boundary.py`, and `test_legacy_save_migration.py`. Browser boundaries are `root/web_tests/test_browser_bridge_contract.py`, `test_browser_smoke_contract.py`, and `root/web_tests/browser_smoke.mjs`.

## Approved Equipment Contract

Every item instance has a stable unique instance ID, an authored definition ID, authored acquisition/source provenance, security state, and its persistent upgrade rank. A definition describes legal slot(s), stat/effect profile, upgrade costs/changes, sale value, and salvage output. Derived effective stats are recomputed, never persisted.

The party owns one shared equipment inventory. Each recruited Drifter can equip any compatible authored item; no Drifter-specific restriction is introduced unless a later authored definition explicitly requires one. Equipment may be managed at the Hub or a safe Rest. During an outing, only the active pair may change loadouts. One instance cannot be equipped twice, duplicated, transferred into two owners, or disposed while referenced.

Primary armor slots are **Helm, Chest, Gloves, Boots**. Accessory slots are **one Ring and one Pendant per Drifter**. The existing signature-weapon slot/state is independent; do not reinterpret `off_hand` or migrate a generic legacy `accessory` into Ring or Pendant without an unambiguous authored mapping.

Armor uses a finite deterministic upgrade track with one shared maximum for every armor piece. The initial implementation default is four authored upgrade steps (rank 0 through rank 4), recorded as a tunable system setting rather than a permanent balance law. Each step consumes its authored shared-material costs and applies its authored stat/effect change; no RNG, rarity lockout, or floor-origin ceiling. Item prices, material quantities, salvage yields, and effect magnitudes stay in authored data and are tunable. Accessories are equipable/persistent in M5 but are not upgradeable in this milestone.

The first content slice uses two Helm definitions with distinct, M3-supported stat bonuses and at least one real authored acquisition source. No new resistance channel or passive-effect engine is added. Equipment bonuses join the existing effective-stat composition once; M3 scaling and mitigation semantics remain authoritative. Weapon progression behavior is unchanged.

Hub disposal accepts secured items only. An equipped item must first be unequipped or replaced; sale/dismantle requires explicit confirmation and removes exactly that instance. Sale and salvage availability/output are authored per definition. Failed or stale transactions make no partial changes.

Equipment found during an outing is an individual unsecured instance. Equipping it never changes its security state. Safe extraction, Rest extraction, and boss return apply existing item-banking rules. Death and Return Talisman remove unsecured gear and clear only equipped references to those removed instance IDs in the same state transition. All secured instances, unrelated equipped references, signature weapons/components/progression, and all other Drifter investment remain unchanged. If a secured item was displaced by the lost item, it remains owned and secured; the loss operation does not silently destroy or duplicate it.

## State, Save, And Client Boundaries

- The party is the canonical owner of equipment instances and their secured/unsecured provenance. Drifters hold slot-to-instance references. Run-event settlement owns the creation of dropped unsecured instances; party return/death/Talisman settlement owns banking or removal.
- Exact target IDs are required for equip, swap, inspect, and all other per-Drifter actions. Clients send IDs/actions and display authoritative previews; they do not compute prices, derived stats, or final upgrade outcomes.
- Use candidate-state transactions for multi-owner changes. Applying an equipment drop, upgrading, disposing, extracting, dying, or using a Return Talisman must not leave costs/rewards and item references out of sync if validation or required persistence fails.
- Add a forward-only game-state migration from runtime schema 17 / disk schema 18 to runtime 18 / disk 19. Preserve current weapon state and every valid existing object; old saves gain no free armor or rolls. Map only unambiguous legacy equipment fields, leave new slots empty, and reject malformed/unknown references rather than inventing replacements. Preserve immutable remote revisions; profile envelope/API/database versions remain unchanged.
- Strictly validate instance-ID uniqueness, definition and slot validity, rank bounds, authored effect fields, source/security state, one-owner/one-reference rules, and the rule that an unsecured reference cannot be made secured by equip/swap. A missing definition is a load error, not a loot-table replacement.
- Terminal and browser expose the same inventory/loadout, exact Drifter selection, item inspection, equip/swap, upgrade preview, merchant sale/salvage confirmation, and rejection reasons. Visual rendering is not required.

## Gate 0 - Approved Policy And Entry Map

- [x] Record M5-D1 through D5 below.
- [x] Revalidate the current M4A baseline and record owners, state/schema versions, exit behavior, client/test locations, and migration boundaries.

Proof: all five product decisions and the current `614586e` entry baseline are recorded; no additional product decisions are required.

## Implementation Defaults

These are first-pass, data-driven implementation choices, not additional locked balance decisions:

- Use four deterministic armor upgrade steps (rank 0 through rank 4) for the initial system. Keep the shared cap configurable so later tuning can change it without changing save ownership semantics.
- Use the existing shared-material inventory for upgrade costs; do not add a new currency or upgrade RNG.
- Keep the initial effects to authored bonuses supported by the current M3 effective-stat/combat paths. Exact names, amounts, prices, costs, and salvage outputs remain content data and may be tuned later.
- Use authored fixed salvage outputs for the initial armor items. Do not introduce another random reward roll for dismantling equipment.

## Gate 1 - Instance Ownership, Equip, Swap, And Save

- [ ] Author two distinct Helm definitions with supported M3 stat bonuses, rank 0-4 effect/cost data, authored values, and a real acquisition source. Record the exact sample data in the content spec; values are tunable.
- [ ] Map existing save fixtures and valid equipment payloads so the forward migration preserves current data and creates no armor for legacy players.
- [ ] Add focused model/content tests for authored definitions, unique instances, legal slots, compatibility, upgrade rank bounds, source/provenance, and strict invalid-ID rejection.
- [ ] Add red/green ownership tests: same definition creates distinct instances; exact recruited Drifter targeting; wrong-slot, unowned, unknown, duplicate-reference, and inactive-during-outing actions reject with zero mutation.
- [ ] Implement shared equipment storage and Drifter slot references. Equip/swap retains the displaced instance and its upgrade rank; no action changes security state.
- [ ] Add runtime 17 -> 18 and disk 18 -> 19 forward migration, strict current-schema validation, save/reload, and remote-payload rejection/advance coverage. Existing signatures, weapons, Tier V, learned techniques, M3 advancement, and legacy state remain unchanged.
- [ ] Verify old saves create no armor and preserve all valid prior data; do not map the old generic `accessory` placeholder to Ring/Pendant by guess.

Proof: own two distinct Helms -> equip A -> swap to B -> equip A on another recruited Drifter -> save/reload -> exact IDs, rank, provenance, and legal references remain correct.

## Gate 2 - Deterministic Upgrade And Merchant Disposal

- [ ] Add focused upgrade tests for each authored rank, preview-versus-commit equality, exact material spend, insufficient material, maximum rank, repeated input, and zero partial mutation on rejection/failure.
- [ ] Implement Hub-only deterministic armor upgrades using the shared-material economy and authored rank data. The early and later Helm both reach rank 4; no floor or rarity condition prevents the early piece from reaching the cap.
- [ ] Integrate authored sale and salvage for secured equipment instances. Equipped items reject disposal until unequipped/replaced; confirm once, remove one instance, grant only authored proceeds/output, and reject stale repeated disposal.
- [ ] Verify upgrades and disposal do not duplicate effects, alter permanent stats, grant HP/Mana, or affect weapon progression.
- [ ] Add terminal/browser merchant views for item inspection, upgrade preview, costs/effects, and explicit sale/salvage confirmation for the one-slot slice.

Proof: both Helms traverse the complete deterministic progression; cancellation/rejection is mutation-free; a disposed instance never returns after save/reload.

## Gate 3 - Full Slots, Accessories, And Outing Provenance

- [ ] Extend authored definitions and legal equipped references to Helm/Chest/Gloves/Boots plus one Ring and one Pendant. Add only the content needed to prove each slot and the shared stat-effect path; accessory upgrades remain absent.
- [ ] Extend the M4A run-event reward boundary to create an equipment instance exactly once at the authored drop event. Persist event/result/instance evidence so view rebuild, repeated input, save/reload, and retry cannot reroll or duplicate gear.
- [ ] Implement security transitions using existing exit owners: safe extraction/Rest/boss returns bank equipment according to current rules; death and Return Talisman atomically remove unsecured instances and clear only their equipped references.
- [ ] Test equipped unsecured gear on death and Talisman; secured equipped and unequipped gear survives; the displaced secured item remains intact; unrelated characters' stats, resources, advancement, weapon/component state, and equipment remain unchanged.
- [ ] Test gear acquired before/at Rest, after continuing from Rest, at boss settlement, after load, and through all applicable Floor II exit methods. Floor I route, rewards, and difficulty remain unchanged.

Proof: a run drop remains unsecured after equip and reload; extraction banks it; death/Talisman lose it with no dangling reference or mutation to secured equipment.

## Gate 4 - Client Parity And Cumulative Qualification

- [ ] Align terminal and browser action availability, exact target selection, previews, inventory/loadout projection, and failure feedback. The bridge submits semantic IDs/actions only.
- [ ] Add one built-browser journey: acquire two Helms -> equip/upgrade -> inspect the other active Drifter -> save/reload -> swap -> equip a Floor II drop -> use an approved safe return and verify banking. Add focused death/Talisman browser proof only where it remains deterministic and does not duplicate the domain matrix.
- [ ] Extend the real pinned MicroPython probe with bounded definition/instance, equip/swap, upgrade, snapshot/reload, and teardown coverage; record the actual memory frontier and do not claim a runtime result that was not run.
- [ ] Run focused tests, full root pytest, web pytest, content validation, compile/build, browser smoke, save/migration/profile validation, PostgreSQL service tests, migration-from-zero, Alembic parity, pinned MicroPython matrix, and exact-SHA hosted CI.
- [ ] Re-review every removed or replaced behavior assumption against M2 exits, M3 effect/resource rules, and M4A Floor II run-event settlement. Record exact SHA and observed results before marking M5 complete.

Closure: all four armor slots and Ring/Pendant are persistent and usable; exact item investment survives swaps; early armor reaches the shared cap; disposal and run-loss behavior are atomic; terminal/browser agree; saves migrate without free gear; signature weapons and M4A behavior remain intact; all required qualification is green.

## Approved Product Decisions

| ID | Approved decision |
| --- | --- |
| M5-D1 | One shared equipment inventory with unique persistent instances and exact Drifter equipped references. Any recruited Drifter may equip a compatible item. Loadouts change at Hub or safe Rest; during an outing only the active pair may change gear. |
| M5-D2 | Armor upgrades are deterministic, finite, authored, and tunable. Every armor piece shares the same maximum; an early piece can reach it. Prices, costs, bonuses, and effects remain authored data. There are no random upgrade rolls or rarity/floor lockouts; use M3-supported stat/effect behavior only. No accessory upgrade curve is assumed. The initial four-step rank count is a tunable implementation default, not a separate product decision. |
| M5-D3 | Each Drifter has one Ring and one Pendant slot. They are persistent and swappable; accessory upgrades are deferred for M5. |
| M5-D4 | Sell/dismantle only secured items at the Hub merchant. Equipped items must first be unequipped or replaced. Disposal is explicitly confirmed, authored per item, and atomic. |
| M5-D5 | Outing equipment stays unsecured when equipped. Existing Rest/extraction/boss rules bank it; death and Return Talisman lose it. Loss removes unsecured instances and clears only their equipped references atomically, preserving secured equipment and all other character investment. |

## Deferred Beyond M5

M4B Floor III, later-floor equipment catalogs and drop tables, accessory upgrades, sets, transmog, cosmetics, degradation, PvP normalization, new resistance systems, and broad balance tuning remain with their owning milestones or future decisions. The four-step cap is an editable initial default, not a locked long-term balance law.

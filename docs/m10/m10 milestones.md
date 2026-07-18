# Dungeon Drifters M10 — Overworld Route and Multi-Enemy Combat

## Contract Authority

Implementation and orchestration must use the dedicated M10 contracts below as
the authority for locked product decisions. Earlier question lists and planning
language do not override these files.

| Milestone | Authoritative contract files |
|---|---|
| M10A | `docs/m10/m10 overworld session contract.md` |
| M10B | `docs/m10/m10 encounter route manifest.md`; `docs/m10/m10 enemy definitions.md` |
| M10C | `docs/m10/m10 multi enemy battle contract.md` |
| M10D | `docs/m10/m10 equipment.md` |
| M10E | `docs/m10/m10 leveling.md`; `docs/m10/m10 gold.md`; `docs/m10/m10 encounter route manifest.md` |
| M10F | `docs/m10/m10 rest contract.md` |
| M10G | `docs/m10/m10 save load.md` |

---

# M10A — Session and Overworld Shell

## Purpose

Replace the current one-battle ending with a persistent non-combat session loop that can return from Battle, preserve the selected Drifter, and continue toward the next authored encounter.

The complete Session and Overworld contract is recorded in
`docs/m10/m10 overworld session contract.md`.

## Repository seams

Current implementation already provides:

- `main_loop.py` for composition and game flow
- `GameState` as the persistent session root
- `PlayerState` as the selected Drifter’s persistent runtime state
- `StoryState` and `WorldState` for persistent narrative and world progress
- `CharacterProfile` and character selection
- `Battle` returning a victory result

The roadmap explicitly introduces `OverworldState` between `GameState` and `Battle`.

## Required player-visible behavior

After character selection, the player can enter the surface route rather than a one-fight ending.

After a victory, the player returns to an overworld menu that can expose:

- Continue to next encounter
- Rest
- Equipment
- Inventory
- Character status
- Save
- Return or exit where appropriate

The first playable checkpoint is:

```text
one Drifter
→ 1 Goblin
→ overworld transition
→ rest or inspect
→ 2 Goblins
→ exact target selection
→ defeat one Goblin without ending combat
→ defeat both Goblins
```

The same selected Drifter and persistent resources must carry into the next encounter.

## Required tests

- `GameState` still owns the selected `PlayerState`
- the session gains one overworld-state owner without duplicating player resources
- victory returns control to the overworld loop
- defeat does not advance to the next encounter
- current route position is persistent and serializable
- two separate sessions do not share overworld state
- terminal input remains outside session mechanics
- the first Goblin-to-overworld transition works end to end

## Decision Authority

Menu wording, semantic navigation, victory and defeat return behavior, state
ownership, disabled and hidden controls, and exit behavior are locked by
`docs/m10/m10 overworld session contract.md`.

## Completion gate

A selected Drifter can defeat the first Goblin, return to a functioning overworld menu, inspect persistent state, and continue into the two-Goblin encounter without recreating `PlayerState`.

---

# M10B — Encounter Route

## Purpose

Represent the fixed Goblin surface route as authored, deterministic encounter data and add the enemy archetypes required by that route.

## Repository seams

Current implementation already provides:

- immutable enemy definitions
- `EnemyState` for mutable encounter instances
- enemy registration and factory lookup
- rank, role, behavior, and capability metadata
- tier validation
- structured enemy moves
- one registered ordinary Goblin

The complete M10 enemy-definition lock is recorded in
`docs/m10/m10 enemy definitions.md`. It covers the four new archetypes,
their authored moves and metadata, tier 0 support, the shared affordable-move
policy, and the final Goblin Lord composition.

The complete route order, stable node IDs, encounter compositions, rewards,
Rest-node placement, boss designation, completion behavior, and next
destinations are recorded in `docs/m10/m10 encounter route manifest.md`.

The roadmap requires encounters to define composition, identifier, reward values, rest boundary, next destination, boss status, and completion state.

## Required player-visible behavior

The fixed escalating route is:

```text
1. 1 Goblin
2. 2 Goblins
3. 1 Goblin Warrior
4. 2 Goblin Warriors
5. 1 Goblin Shaman
6. 2 Goblin Shamans
7. 1 Goblin Elite + 1 Goblin
8. 1 Goblin Lord + 1 Goblin + 1 Goblin Warrior
9. Dungeon entrance
```

The player sees the correct enemies in the correct order.

Duplicate enemies are distinguishable during combat.

The ordinary Goblin retains its current production balance unless a separate approved balance change is made.

## Required tests

- Goblin Warrior, Goblin Shaman, Goblin Elite, and Goblin Lord can be created through the existing enemy factory
- each factory call creates independent runtime state
- the Goblin Shaman is present in both the single-Shaman and two-Shaman encounters
- encounter identifiers are unique
- all eight combat encounters have the exact approved composition and next destination
- the route contains exactly one Goblin Lord encounter
- duplicate Goblins, Warriors, and Shamans have independent HP, Mana, actions, and temporary state
- the eight-encounter route order is deterministic
- completed encounters are represented persistently
- authored enemy definitions are not mutated by combat

## Decision Authority

Route identifiers, rewards, Rest boundaries, boss flags, and completion
semantics come from `docs/m10/m10 encounter route manifest.md`. Duplicate-enemy
labels and runtime target identity come from
`docs/m10/m10 multi enemy battle contract.md`.

## Completion gate

Every required enemy archetype exists through the current registry/factory pattern, and the exact eight-encounter route plus dungeon entrance can be instantiated and inspected as deterministic authored encounter data.

---

# M10C — Multi-Enemy Combat

## Purpose

Expand the current one-player-versus-one-enemy Battle to support one player against multiple independent enemies without rewriting the established combat, presentation, or UI ownership boundaries.

The complete Multi-Enemy Battle contract is recorded in
`docs/m10/m10 multi enemy battle contract.md`.

## Repository seams

Current implementation already provides:

- `Battle` as orchestration
- `CombatResolver` for action mechanics
- `CombatState` for encounter-local state
- identity-based status ownership
- `BattlePresenter`
- immutable `BattleView`
- semantic battle input values
- stateless terminal rendering
- `Battle.run()` returning `"player"` or `"enemy"`

Current single-enemy assumptions exist in `Battle`, `BattlePresenter`, `BattleView`, and `TerminalBattleUI`.

## Required player-visible behavior

The first architecture gate is:

```text
one player character
→ two Goblins
→ select either target
→ both enemies can act
→ defeating one does not end combat
→ defeating both ends combat
```

The final M10 route must also support the two-Goblin encounter, single Warrior, Warrior pair, single Shaman, Shaman pair, Elite-plus-Goblin encounter, and Goblin Lord-plus-Goblin-plus-Warrior finale.

Every action and status applies to the exact intended enemy.

Presentation shows each enemy’s independent HP and temporary states.

Defeated enemies take no further actions.

Mutual player/enemy death remains defeat.

## Required tests

- two enemies can coexist in one Battle
- the two-Goblin, two-Warrior, two-Shaman, Elite-plus-Goblin, and three-enemy Goblin Lord compositions are supported
- target selection resolves the exact chosen enemy
- enemy HP and temporary state remain independent
- both living enemies can receive action opportunities
- one enemy can die while combat continues
- victory occurs only after all required enemies are defeated
- defeated enemies do not act
- Frozen and Stun suppress only the affected enemy
- Burn, Poison, and Frostbite ordering remains deterministic
- Gravemantle Break never affects another enemy
- Frost, Conductive, Turbulence, and other source-target mechanics remain exact
- Overcharge can follow its existing different-target behavior without status leakage
- invalid target input does not spend resources or advance combat
- current single-enemy Battle behavior and winner return values do not regress
- presentation and terminal input remain renderer-neutral and semantic

## Locked M10C Decisions

- Battle accepts an authored-order enemy collection directly.
- Initiative remains one side-level roll.
- Every living enemy receives one opportunity per enemy phase in authored order.
- One living enemy is auto-targeted; multiple living enemies require semantic
  target selection after move selection.
- Enemy target IDs are stable encounter-local IDs independent of display names.
- Duplicate display names are numbered in authored order.
- Defeated enemies remain visible, untargetable, and unable to act.
- Back from target selection returns to the originating move phase.
- `Battle.enemies` and `BattleView.enemies` are canonical.
- Single-enemy compatibility accessors may remain only when they fail explicitly
  for multi-enemy encounters.

## Completion gate

The two-Goblin architecture gate passes manually and automatically: the player can choose either target, both enemies behave independently, one can die without ending combat, and defeating both returns the existing player-victory result.

---

# M10D — Equipment Integration

## Purpose

Connect the existing signature-weapon equipment system to effective combat
values and make the current weapon inspectable from the overworld.

The complete M10 equipment boundary is recorded in
`docs/m10/m10 equipment.md`.

## Repository seams

Current implementation already provides:

- equipment slots on `PlayerState`
- inventory ownership checks
- equip, replace, and unequip behavior
- four equipped signature weapons
- weapon stat bonuses
- `PlayerState.effective_stat()`
- resolver use of effective stats
- equipment data in snapshots
- tests for item conservation and session isolation

## Required player-visible behavior

From the overworld, the player can inspect the currently equipped signature
weapon through a read-only Weapon tab.

Equipping an item changes the effective values that item is intended to modify.

Existing equip, replace, and unequip APIs continue to preserve the correct
effective values, but M10 does not add a broader equipment-management screen.

Permanent base attributes remain unchanged.

Equipment persists into later encounters and appears in persistent state.

## Required tests

- equipped modifiers affect the intended effective combat values
- permanent stats are not mutated
- inventory-only equipment grants no effect
- replacing and unequipping update effective values exactly once
- item conservation remains correct
- equipment belongs to the correct `PlayerState`
- two sessions do not share equipment mutations
- equipment remains present across encounters
- equipment appears in snapshots and later save/load data
- temporary combat state never becomes equipment state
- the read-only Weapon tab cannot mutate state through presentation objects

## Decision Authority

Supported signature weapons, stable identifiers, effective bonuses, and the
read-only Weapon tab come from `docs/m10/m10 equipment.md`.

## Completion gate

The player can inspect the equipped signature weapon from the overworld,
observe the approved effective-value changes in combat, and move between
encounters without mutating permanent attributes or losing equipment state.

---

# M10E — Progression and Rewards

## Purpose

Connect encounter victory to persistent EXP, level state, gold or other already-supported persistent rewards, and controlled permanent growth.

The M10 progression curve and level cap are recorded in
`docs/m10/m10 leveling.md`. Exact encounter EXP and gold rewards, atomic reward
rules, and the expected dungeon-entrance totals are recorded in
`docs/m10/m10 gold.md` and `docs/m10/m10 encounter route manifest.md`.

## Repository seams

Current implementation already provides:

- `Level`
- `Exp.gain()` with carryover and multiple-level support
- permanent stats with controlled mutation
- HP and Mana scaling from permanent stats and level
- resource-maximum recalculation on `Character`
- gold on `PlayerState`
- snapshot coverage for level, EXP, resources, and gold
- an unused Intuition secured-XP scaling helper

The current repository has no encounter reward model or controlled `PlayerState` progression entry point.

## Required player-visible behavior

After a complete encounter victory, the player sees the approved reward and retains it after leaving combat.

EXP, level, HP, Mana, gold, equipment, and other persistent state remain correct when the next encounter begins.

A multi-enemy encounter grants its reward once, after all required enemies are defeated.

The first Goblin does not automatically grant a level unless the approved progression curve says it should.

## Required tests

- victory applies the encounter reward once
- partial defeat of a multi-enemy group grants nothing
- defeat grants nothing
- completed encounters cannot grant rewards twice
- EXP thresholds and carryover remain correct
- multiple-level gains remain correct
- approved maximum-resource growth is applied safely
- controlled permanent growth validates stat names, values, and bounds
- failed permanent growth leaves state unchanged
- gold rewards persist when used
- progression remains present in the next encounter
- snapshots and save/load data represent the resulting progression
- the approved route reaches the approved level points

## Decision Authority

M10 uses the exact progression curve, Growth Point economy, encounter rewards,
and route totals in the linked progression documents. Orchestration must not
substitute alternate rewards, random variance, per-enemy immediate rewards, or
Intuition-based reward scaling.

## Completion gate

A full encounter victory applies one approved persistent reward, progression survives the overworld transition, and the next encounter begins with the correct level, EXP, resources, gold, and equipment.

---

# M10F — Resting

## Purpose

Provide the simple deterministic between-encounter recovery action required by a route with persistent HP and Mana.

The complete Rest contract is recorded in
`docs/m10/m10 rest contract.md`.

## Repository seams

Current implementation already provides:

- persistent HP and Mana on the selected character
- persistent Super on `PlayerState`
- persistent run inventory and prepared Infusion state
- encounter-local temporary state inside `CombatState`
- the M10A overworld menu and route state
- completed encounter tracking

No rest operation currently exists.

## Required player-visible behavior

At an authored overworld Rest node, the player can choose Rest, Save, Quit, or
Menu, or continue without resting.

Rest fully restores HP and Mana, leaves Super unchanged, consumes the single-use
Rest node, and advances to the next authored route node.

Rest does not occur during combat.

Rest never duplicates rewards, resets equipment, resets prepared run inventory, refills consumables unexpectedly, or alters authored character data.

The player can continue without resting whenever the approved contract allows it.

## Required tests

- rest is available only at approved route boundaries
- rest applies the approved HP and Mana recovery
- rest cannot affect an active Battle
- temporary combat state is not restored
- EXP, level, equipment, and completed encounters remain unchanged
- prepared run inventory remains correct
- consumables are not unexpectedly refilled
- repeated-rest behavior matches the approved contract
- rest availability persists through save/load
- resting does not advance or repeat encounter rewards

## Locked M10 Rest Decisions

- Rest occurs only at authored map Rest nodes.
- The three M10 Rest nodes are single-use.
- Rest fully restores HP and Mana.
- Rest does not reset or increase Super.
- Rest has no gold, time, item, or resource cost.
- Continue Without Rest is available and consumes the node without recovery.
- Save and Quit do not consume the node.
- Menu returns to the normal Main Overworld Menu.
- Rest does not alter persistent state unrelated to HP and Mana.

## Completion gate

At an approved post-encounter boundary, the player can rest, receive exactly the approved recovery, preserve every unaffected persistent value, and enter the next encounter with the resulting state.

---

# M10G — Save and Load

## Purpose

Persist the meaningful M10 session state outside active combat and restore it into a playable session.

The complete M10 Save/Load contract is recorded in
`docs/m10/m10 save load.md`.

## Repository seams

Current implementation already provides:

- schema-versioned plain snapshots
- `GameState.snapshot()`
- `PlayerState.snapshot()`
- `StoryState.snapshot()`
- `WorldState.snapshot()`
- run-inventory and prepared-payload snapshots
- character profiles and canonical character factories
- equipment snapshot data
- strict plain-value validation

There is no disk save/load service or reconstruction path.

The current in-memory inspection snapshot remains schema `7`. M10 disk saves
use schema `8`, with deterministic migration from schema 7.

## Required player-visible behavior

From an approved overworld boundary, the player can save one game.

From the opening flow, the player can load that saved game.

Loading restores the selected Drifter, progression, current resources, equipment, inventories, prepared Infusion state, route position, completed encounters, rest state where relevant, and story/world progress.

The loaded session can continue into the next encounter.

No active combat, open menu, presenter model, RNG object, enemy runtime object, or temporary status is saved.

## Required tests

- a saved overworld session round-trips into an equivalent playable state
- selected character identity restores through the canonical profile/factory path
- HP, Mana, Super, level, EXP, gold, equipment, inventory, run inventory, and prepared state restore correctly
- route position and completed encounters restore correctly
- rest state restores where required
- story and world progress restore correctly
- loaded completed encounters cannot grant rewards again
- unsupported or malformed data fails clearly
- unknown character, equipment, route, or inventory identifiers are rejected
- runtime-only combat and presentation objects never appear in save data
- failed saves do not destroy a prior valid save
- loading does not create shared mutable state with another session
- the restored game can continue into the next encounter

## Decision Authority

Save boundaries, schema behavior, missing and invalid save behavior, and
persistence ownership come from `docs/m10/m10 save load.md`. Canonical item
identifiers come from their approved item contracts and authored registries.

## Completion gate

The player can save at an approved overworld boundary, exit the process, restart, load the game, verify all approved persistent state, and continue the fixed route without duplicated rewards or temporary combat state.

---

# M10 Completion

M10 is complete when one selected Drifter can:

```text
complete the first Goblin
return to a real overworld loop
continue through all eight fixed authored encounters
fight the exact approved multi-enemy compositions
receive persistent rewards
manage approved equipment
rest under the approved contract
save and load
defeat the Goblin Lord + Goblin + Goblin Warrior encounter
reach the dungeon entrance
```

Required final verification:

- focused tests for M10A through M10G pass
- the complete existing test suite passes
- Python compilation passes
- `git diff --check` passes
- the current one-Goblin balance baseline has no unexplained regression
- one complete M10 route passes manually
- the first Goblin → overworld → two-Goblin gate is proven with every Drifter
- exact-commit CI is green
- the working tree is clean

Do not begin second-character or party work inside M10.

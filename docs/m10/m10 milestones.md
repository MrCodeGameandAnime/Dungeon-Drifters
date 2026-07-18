# Dungeon Drifters M10 — Overworld Route and Multi-Enemy Combat

---

# M10A — Session and Overworld Shell

## Purpose

Replace the current one-battle ending with a persistent non-combat session loop that can return from Battle, preserve the selected Drifter, and continue toward the next authored encounter.

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

## Unresolved product decisions

- exact overworld menu wording and navigation
- exact meaning of “Return or exit where appropriate”
- what the player can do after defeat
- whether unavailable M10 features appear disabled before their section lands
- which existing `StoryState` and `WorldState` fields own each route fact
- whether leaving the game before M10G simply exits without persistence

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

## Unresolved product decisions

- exact enemy stats, moves, capabilities, and tiers
- exact encounter identifiers
- exact reward values
- exact rest boundaries
- exact boss flags and completion semantics
- exact display labels for duplicate enemies

## Completion gate

Every required enemy archetype exists through the current registry/factory pattern, and the exact eight-encounter route plus dungeon entrance can be instantiated and inspected as deterministic authored encounter data.

---

# M10C — Multi-Enemy Combat

## Purpose

Expand the current one-player-versus-one-enemy Battle to support one player against multiple independent enemies without rewriting the established combat, presentation, or UI ownership boundaries.

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

## Unresolved product decisions

- exact enemy turn sequencing when several enemies are alive
- how initiative interacts with multiple enemy actions
- whether one remaining enemy is auto-targeted or still selected
- how defeated enemies remain visible in presentation
- exact duplicate-enemy labels and numbering
- how target selection returns to move selection
- whether Battle accepts a collection directly or an encounter runtime object
- whether any existing compatibility accessor remains temporarily

## Completion gate

The two-Goblin architecture gate passes manually and automatically: the player can choose either target, both enemies behave independently, one can die without ending combat, and defeating both returns the existing player-victory result.

---

# M10D — Equipment Integration

## Purpose

Connect the existing equipment system to effective combat values and make equipment inspectable and manageable from the overworld.

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

From the overworld, the player can inspect current equipment and manage supported owned equipment.

Equipping an item changes the effective values that item is intended to modify.

Unequipping or replacing it restores the correct effective values.

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
- overworld equipment input cannot mutate state through presentation objects

## Unresolved product decisions

- which equipment slots and item types are supported during M10
- whether M10 requires any new equipment content beyond the current signature weapons
- which derived values count as “supported” for equipment integration
- whether Constitution or Spirit equipment changes maximum HP or Mana in M10
- how current HP or Mana should react if a maximum changes
- exact equipment menu behavior
- stable item identity required for save/load
- whether intended-wielder restrictions are enforced

## Completion gate

The player can inspect and manage supported equipment from the overworld, observe the approved effective-value changes in combat, and move between encounters without mutating permanent attributes or losing equipment state.

---

# M10E — Progression and Rewards

## Purpose

Connect encounter victory to persistent EXP, level state, gold or other already-supported persistent rewards, and controlled permanent growth.

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

## Unresolved product decisions

- exact EXP and gold rewards for every encounter
- whether M10 uses permanent-stat rewards
- when the first level should occur
- expected level before the Goblin Lord encounter and at the dungeon entrance
- whether current HP and Mana increase when their maxima increase
- whether the Intuition secured-XP helper is active in M10
- whether any reward other than EXP, gold, or controlled growth is required
- exact reward presentation

## Completion gate

A full encounter victory applies one approved persistent reward, progression survives the overworld transition, and the next encounter begins with the correct level, EXP, resources, gold, and equipment.

---

# M10F — Resting

## Purpose

Provide the simple deterministic between-encounter recovery action required by a route with persistent HP and Mana.

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

At approved overworld boundaries, the player can choose Rest.

Rest applies the approved recovery contract and returns the player to the overworld.

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

## Unresolved product decisions

- full or partial HP/Mana recovery
- whether rest has a gold, time, item, or no cost
- whether rest is always available or boundary-specific
- whether rest is optional at every available boundary
- whether a boundary can be used more than once
- whether rest is available after the final Goblin Lord encounter
- whether Super changes during rest
- exact treatment of prepared Infusion state
- whether resting affects story progression
- exact player-facing text

## Completion gate

At an approved post-encounter boundary, the player can rest, receive exactly the approved recovery, preserve every unaffected persistent value, and enter the next encounter with the resulting state.

---

# M10G — Save and Load

## Purpose

Persist the meaningful M10 session state outside active combat and restore it into a playable session.

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

Current schema version is `7`.

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

## Unresolved product decisions

- whether save/load reuses the inspection snapshot shape or has a separate persistence shape
- whether the schema version changes during M10
- exact save-file location and filename
- exact safe save boundaries
- whether saving is manual only
- opening-menu behavior when no save exists
- invalid-save handling and player-facing message
- whether defeated player state may be saved
- whether saving is allowed immediately before or after the final Goblin Lord encounter
- exact canonical item identifiers
- whether backward compatibility with schema 7 is required

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

This is the complete section 4 contract, built from the finalized overworld menu wireframes.

# M10 Overworld Session Contract

## Purpose

M10 replaces the current one-battle ending with a persistent overworld session.

The session flow is:

```text
character selection
→ overworld
→ authored route node
→ battle or rest
→ overworld
→ next authored route node
→ dungeon entrance
```

The selected Drifter, progression, resources, equipment, inventory, route
position, and completed encounters persist throughout the session.

The overworld is a real non-combat gameplay state. It is not merely transitional
text printed between battles.

---

# Overworld Screen Hierarchy

```text
Main Menu
├── Character
│   ├── Skills
│   ├── Weapon
│   ├── Equipment
│   └── Back
├── Items
│   ├── Craft
│   ├── Inspect
│   ├── Use
│   └── Back
├── Map
│   ├── Inspect
│   └── Back
└── Options
    ├── Save
    ├── Load
    ├── Quit
    └── Back
```

The main menu and every submenu are available only at safe overworld
boundaries.

No overworld menu is available during active Battle resolution.

---

# Global Navigation Rules

All menu input is semantic.

Examples include:

```text
character
items
map
options
skills
weapon
equipment
inspect
use
craft
save
load
quit
back
continue
retry
rest
skip_rest
confirm
cancel
```

The session and gameplay layers do not depend on:

* terminal coordinates
* mouse coordinates
* colors
* raw button text
* renderer-specific input values

## Back

Back returns exactly one menu level.

Examples:

```text
Skills → Character
Weapon → Character
Equipment → Character
Character → Main Menu
Items → Main Menu
Map → Main Menu
Options → Main Menu
```

Back does not:

* advance the route
* consume a Rest node
* alter inventory
* spend Growth Points
* save or load
* recreate PlayerState
* alter completed encounters

## Invalid Input

Invalid input:

* keeps the current screen open
* changes no persistent state
* spends no resource
* does not advance the route
* does not begin Battle

---

# Main Overworld Menu

The main menu contains:

```text
Location

Adventure Text

Character    Items
Map          Options
```

## Location

Location displays the current authored route node.

The displayed location comes from the current route position.

Opening or closing a submenu does not change the current location.

## Adventure Text

Adventure Text displays:

* current route context
* the outcome of the previous battle or action
* the upcoming encounter
* Rest-node information
* defeat information
* route-completion information
* the currently available contextual route action

Contextual route actions are presented through the Adventure Text area rather
than permanent menu tiles.

Possible contextual actions include:

```text
Enter Encounter
Continue
Retry
Rest
Continue Without Rest
```

Only actions valid for the current node are shown.

---

# Character Menu

The Character menu contains:

```text
Skills                  Character Emblem
Weapon                  Stats
Equipment               XP Bar
```

The Character Emblem, Stats, and XP Bar are display regions.

The selectable character submenus are:

```text
Skills
Weapon
Equipment
Back
```

## Character Emblem

The emblem represents the currently selected Drifter.

Opening the Character menu never recreates or replaces the selected Drifter.

## Stats

The Stats panel displays the actual Dungeon Drifters attributes:

```text
Strength
Constitution
Intelligence
Spirit
Dexterity
Intuition
```

It may also display:

* Level
* current and maximum HP
* current and maximum Mana
* available Growth Points
* other already-approved persistent character values

Gold is not a character stat.

## XP Bar

The XP Bar displays:

```text
current level
current EXP
EXP required for the next level
visual progress toward the next level
```

At the absolute level cap, the display shows that the character is at maximum
level rather than presenting another threshold.

---

# Skills Menu

The Skills menu contains two sections.

## Level-Up Section

The upper section displays:

```text
Growth Points Available

Strength        current value    +
Constitution    current value    +
Intelligence    current value    +
Spirit          current value    +
Dexterity       current value    +
Intuition       current value    +
```

The six displayed attributes must match the real Dungeon Drifters stat model.

M10 displays the level-up structure and available Growth Points.

Growth Point spending is not active during M10.

Therefore, during M10:

* Growth Points are displayed.
* Current permanent stats are displayed.
* The stat-increase controls remain visible.
* The stat-increase controls are disabled.
* Selecting a disabled control changes no state.
* A concise explanation states that stat spending is not yet available.

The controls may become active in a later milestone when the authored growth
system is implemented.

## Attacks Section

The lower section displays the selected Drifter’s actual authored moves.

For Branoc, the displayed list includes the currently authored Branoc moves,
such as:

```text
Brace
Ironwake Dismemberment
Third Gate Obsequy
```

Each Drifter displays their own real move list.

The Attacks section is read-only during M10.

The Skills menu does not:

* purchase moves
* unlock moves
* equip or unequip moves
* modify move data
* spend Growth Points
* create a growth tree

Back returns to the Character menu.

---

# Weapon Menu

The Weapon menu displays the currently equipped signature weapon.

The layout contains:

```text
Weapon

Weapon Name
Weapon Type

Bonuses
- authored stat bonuses

Description
- authored weapon description

Back
```

Example structure:

```text
Sunder-Spire
Great Flamberge

Bonuses
Strength +3
Constitution +1

Description
[authored weapon description]
```

The displayed values come from the real equipped weapon data.

The menu must not invent weapon descriptions, bonuses, types, or wielder
restrictions.

The Weapon menu is read-only during M10.

It does not provide:

* equip
* unequip
* replace
* refine
* dismantle
* upgrade
* craft
* reroll
* component installation

Back returns to the Character menu.

---

# Equipment Menu

The Equipment menu displays two accessory slots:

```text
Necklace
Ring
```

Below the slots, the Benefits section displays the effects provided by the
currently equipped Necklace and Ring.

Example structure:

```text
Benefits

Necklace: [benefit or Empty]
Ring: [benefit or Empty]
```

The example wireframe benefits are layout examples only.

Actual item names and benefits must come from approved equipment data.

During M10:

* the Necklace slot remains visible
* the Ring slot remains visible
* an empty slot displays `Empty`
* an empty slot provides no benefit
* the Benefits section displays `None` when no accessory benefit exists
* accessory swapping is not implemented unless separately approved
* the screen remains read-only

The signature weapon does not appear in these two accessory slots.

The signature weapon is inspected through the separate Weapon menu.

Back returns to the Character menu.

---

# Items Menu

The Items menu contains:

```text
Item list

Craft      Inspect
Use        Back
```

The item list displays the current persistent inventory.

Selecting an item changes only the current menu selection.

## Inspect

Inspect displays the selected item’s authored information.

Inspect is enabled only when an item is selected.

Inspecting an item does not consume or modify it.

## Use

Use is enabled only when:

* an item is selected
* that item has an approved overworld-use action
* its use is legal at the current overworld boundary

Using an item follows the item’s existing gameplay contract.

Use is disabled when the selected item cannot legally be used from the
overworld.

## Craft

Craft remains visible but disabled throughout M10.

M10 does not implement crafting.

Selecting Craft during M10:

* changes no inventory
* spends no resource
* opens no crafting workflow
* displays a concise unavailable message

## Back

Back returns to the Main Menu.

---

# Map Menu

The Map menu displays the complete authored M10 surface route.

It contains:

```text
Location
Route Map
Inspect
Back
```

## Location

Location identifies the player’s current route node.

The current node must be distinguishable without relying only on color.

## Route Display

The route map shows:

* regular enemy nodes
* all three Rest nodes
* the Elite encounter
* the Goblin Lord encounter
* the dungeon entrance
* the current node
* completed nodes
* remaining nodes

The player cannot use the map to:

* fast travel
* skip encounters
* revisit cleared encounters
* jump to a Rest node
* select a future destination
* enter the dungeon

## Inspect

Inspect displays the next unresolved combat encounter.

At a combat node, Inspect displays that encounter’s composition.

At a Rest node, Inspect displays the next combat encounter after the Rest node.

Examples include:

```text
2 Goblins
2 Goblin Warriors
Goblin Elite + Goblin
Goblin Lord + Goblin + Goblin Warrior
```

Inspect does not create enemy runtime objects or begin Battle.

Inspect is disabled at the dungeon entrance because no later M10 encounter
exists.

## Back

Back returns to the Main Menu.

---

# Options Menu

The Options menu contains:

```text
Save      Quit
Load      Back
```

## Save

Save is enabled only at a safe overworld boundary.

Saving follows the separate M10 Save and Load Contract.

Save is never available during Battle or during an unresolved state
transition.

## Load

Load is enabled only when a valid supported save exists.

Selecting Load while a session is active requires confirmation because the
loaded session replaces the current session.

If no save exists, Load remains visible but disabled.

If a save is invalid, loading follows the invalid-save behavior defined by the
M10 Save and Load Contract.

## Quit

Quit requires confirmation.

Confirming Quit:

* exits the active game session
* does not automatically save
* does not alter the save file
* does not advance the route

Cancel returns to the Options menu.

## Back

Back returns to the Main Menu.

---

# Contextual Route Actions

Route progression is controlled through contextual actions shown in the
Adventure Text area.

These actions are separate from the four permanent main-menu commands.

## Combat Node

At an uncleared combat node:

```text
Enter Encounter
```

or, after returning from a previous node:

```text
Continue
```

begins the authored encounter for the current node.

## Defeated Combat Node

After defeat:

```text
Retry
```

begins a fresh instance of the same authored encounter.

## Rest Node

At a Rest node:

```text
Rest
Continue Without Rest
```

are available.

The exact recovery, cost, Super behavior, Infusion behavior, and one-use rules
come from the separate M10 Rest Contract.

## Dungeon Entrance

At the dungeon entrance:

```text
Enter Dungeon
Continue Route
Next Encounter
```

are unavailable.

M10 ends at the dungeon entrance.

---

# Availability by Node Type

## Combat Nodes

The following are available before entering Battle:

```text
Enter Encounter or Continue
Character
Items
Map
Options
```

The current encounter may be inspected through Map.

Rest is unavailable unless the current node is an authored Rest node.

## Rest Nodes

The following are available:

```text
Rest
Continue Without Rest
Character
Items
Map
Options
```

The next combat encounter may be inspected through Map.

## Goblin Lord Node

The Goblin Lord node behaves like another combat node for menu availability:

```text
Enter Encounter
Character
Items
Map
Options
```

It remains clearly identified as the boss encounter.

## Dungeon Entrance

The following remain available:

```text
Character
Items
Map
Options
```

The route is complete.

There is no M10 combat continuation or dungeon-entry action.

## Active Battle

The overworld menu is unavailable.

The following cannot be opened during Battle:

```text
Character
Items
Map
Options
Save
Load
Rest
```

Combat uses its own battle-specific interaction flow.

---

# Victory Return Behavior

After full encounter victory:

```text
Battle returns victory
→ verify every required enemy is defeated
→ apply approved EXP once
→ apply approved gold once
→ process level gains
→ update HP and Mana maxima under the progression contract
→ award Growth Points
→ mark the encounter completed
→ advance to the authored next route node
→ discard Battle runtime state
→ return to the Main Overworld Menu
```

The same PlayerState continues after victory.

Victory must not:

* recreate the selected Drifter
* reset current HP or Mana
* reset Super
* reset inventory
* reset equipment
* duplicate rewards
* preserve enemy runtime objects
* preserve temporary combat statuses
* leave the completed encounter replayable for rewards

Adventure Text reports the victory and introduces the newly reached route node.

---

# Defeat Return Behavior

Before entering Battle, the session creates a transient pre-battle checkpoint
of the persistent player state.

After defeat:

```text
Battle returns defeat
→ grant no EXP
→ grant no gold
→ award no Growth Points
→ mark no encounter completion
→ do not advance the route
→ discard enemy runtime state
→ discard temporary combat state
→ restore the player from the pre-battle checkpoint
→ return to the same combat node
→ return to the Main Overworld Menu
```

Adventure Text reports the defeat.

The contextual route action becomes:

```text
Retry
```

Retry creates new independent enemy runtime objects.

Defeat does not consume a Rest node.

Defeat does not alter previously completed encounters or previously secured
progression.

The pre-battle checkpoint is transient session data and is not written into the
save file.

---

# State Ownership

The persistent session ownership is:

```text
GameState
├── PlayerState
├── StoryState
├── WorldState
└── OverworldState
```

## GameState Owns

GameState remains the root object for one active game session.

It owns exactly one instance of each persistent state object.

## PlayerState Owns

PlayerState owns:

* selected Drifter identity
* Level
* EXP
* Growth Points
* current and maximum HP
* current and maximum Mana
* permanent stats
* Super
* signature weapon
* approved equipment
* inventory
* run inventory
* prepared Infusion state
* other persistent character resources

No menu owns or duplicates these values.

## OverworldState Owns

OverworldState owns route-session facts:

* current route node ID
* whether the surface route has begun
* whether the dungeon entrance has been reached
* whether the M10 route is complete
* authored Rest-node resolution state
* current contextual route phase

OverworldState does not own a second copy of PlayerState resources.

## WorldState Owns

WorldState remains authoritative for durable world facts:

* discovered locations
* completed or defeated encounter IDs
* other persistent world changes

Completed encounter IDs are not duplicated inside OverworldState.

OverworldState uses WorldState completion data when determining whether the
current encounter is cleared.

## StoryState Owns

StoryState owns:

* current chapter
* current scene
* narrative location
* story flags
* completed narrative events
* player decisions

Adventure Text may be generated from StoryState, OverworldState, and authored
route data.

The rendered Adventure Text itself is not persistent gameplay state.

## Menu and Presentation State

The following are temporary presentation state:

* currently open menu
* highlighted item
* highlighted stat
* highlighted route node
* confirmation prompt
* scroll position
* rendered text
* button focus

Presentation state is not saved.

Loading always returns the player to the safe Main Overworld Menu rather than
restoring an open submenu.

---

# Hidden and Disabled Features

M10 uses the following rule:

## Persistent Menu Features

Permanent authored menu entries remain visible.

When unavailable, they are disabled rather than removed.

Disabled entries:

* use a visibly inactive presentation
* cannot mutate state
* cannot advance navigation into an unfinished workflow
* display a concise reason when selected

Examples:

```text
Craft
Growth Point stat-increase controls
Load when no save exists
Use when the selected item cannot be used
Inspect when nothing is selected
Map Inspect at the dungeon entrance
```

## Contextual Route Features

Contextual route actions are shown only when valid for the current node.

Invalid contextual actions are hidden.

Examples:

* Rest appears only at a Rest node.
* Retry appears only after defeat.
* Enter Encounter appears only at an uncleared combat node.
* Continue Without Rest appears only at a Rest node.
* Enter Dungeon does not appear during M10.

This distinction preserves the fixed menu layouts while preventing the
Adventure Text area from displaying irrelevant route actions.

---

# Required Tests

* GameState owns exactly one OverworldState.
* PlayerState is not recreated during menu navigation.
* Opening and closing every submenu changes no persistent state.
* Back returns exactly one menu level.
* Invalid menu input changes no state.
* Location reflects the current authored node.
* Adventure Text exposes only valid contextual route actions.
* Combat nodes expose Enter Encounter or Retry as appropriate.
* Rest actions appear only at the three authored Rest nodes.
* The map cannot alter route position.
* Map Inspect displays the correct upcoming encounter.
* Map Inspect is disabled at the dungeon entrance.
* Character Stats use the six real Dungeon Drifters attributes.
* Skills displays the correct Drifter move list.
* Growth Points display correctly.
* M10 stat-increase controls are visible but disabled.
* Weapon inspection cannot mutate equipment.
* Weapon values come from the equipped signature weapon.
* Necklace and Ring slots display Empty when unoccupied.
* Craft remains visible but disabled during M10.
* Item Inspect does not consume an item.
* Item Use is disabled when use is not legal.
* Save is available only at safe overworld boundaries.
* Load is disabled when no valid save exists.
* Quit does not autosave.
* Victory advances exactly one authored route node.
* Victory rewards are granted exactly once.
* Defeat grants no rewards.
* Defeat does not advance the route.
* Defeat restores the pre-battle persistent player checkpoint.
* Retry creates fresh enemy runtime state.
* Completed encounters cannot be replayed for rewards.
* Reaching the dungeon entrance completes M10.
* Dungeon entry is not offered during M10.
* Open menus and presentation state do not appear in save data.

---

# Completion Gate

The Overworld Session Contract is satisfied when one selected Drifter can:

```text
enter the surface route
→ complete an encounter
→ return to the Main Overworld Menu
→ inspect Character, Items, Map, and Options
→ navigate every submenu safely
→ continue to the next authored node
→ lose and retry without route advancement
→ use authored Rest-node navigation
→ save and load at safe boundaries
→ reach the dungeon entrance
```

The same persistent PlayerState must survive the entire session without
duplication, unintended reset, or temporary combat-state leakage.

# Dungeon Extraction Economy

This note records future authored design direction for Dungeon Drifters'
extraction economy. It is not authorized for implementation during Milestone 3.

## Core Purpose

The trader, gold economy, consumables, accessories, and extraction rules complete
the main Dungeon Drifters gameplay loop.

The intended loop is:

```text
Prepare at the hub
-> enter the dungeon
-> fight and explore
-> earn unsecured experience, gold, and loot
-> decide whether to continue or extract
-> successfully return and secure the run
-> spend, refine, equip, and prepare
-> enter again
```

The dungeon should create increasing tension because rewards earned during the
active run remain at risk until the party successfully leaves.

## Secured And Unsecured Progress

The game should distinguish between progress already secured at the hub and
rewards currently carried inside the dungeon.

## Secured Progress

Secured progress includes things already returned to the hub or permanently
applied:

- previously secured character levels
- previously banked experience, depending on the final leveling model
- signature-weapon refinement
- installed weapon components
- equipped accessories
- stored items
- banked gold
- completed story progress
- permanent unlocks

Secured progress is not lost when the party dies during a later dungeon run.

## Unsecured Progress

Unsecured progress includes rewards earned during the current dungeon run:

- experience
- gold
- weapon components
- refinement materials
- alchemical ingredients
- consumables found inside
- rings
- pendants
- rare loot
- other dungeon rewards

Unsecured rewards become secured only after a successful extraction.

## Death Rule

If the active party dies inside the dungeon:

- all unsecured experience is lost
- all unsecured gold is lost
- all unsecured loot is lost
- all unsecured components and materials are lost
- the party returns to the hub
- previously secured progression remains intact

The player loses the current run, not the entire save file.

The player should not lose:

- previously secured levels
- the Drifters themselves
- signature weapons
- previously installed weapon components
- previously equipped accessories
- banked gold
- stored items
- completed story progress

No corpse-retrieval system is currently intended.

The important risk decision occurs before death:

> Continue deeper for greater rewards, or leave while the current run can still
> be secured?

## Extraction Methods

## Normal Extraction

The party reaches an authorized exit, dungeon completion point, or other valid
extraction location.

Result:

- keep unsecured experience
- keep unsecured gold
- keep unsecured loot
- convert the run's rewards into secured progress
- no special item cost

This is the ideal outcome.

## Smoke Bomb

A smoke bomb provides a guaranteed escape from the current combat encounter.

Intended result:

- immediately end or escape the active encounter
- preserve the active dungeon run
- remain inside the dungeon
- consume the smoke bomb
- require the player to still reach an extraction point or use another escape
  method

A smoke bomb is not a full dungeon extraction item. It prevents one dangerous
battle from automatically destroying the run.

Exact restrictions remain unresolved, including:

- whether bosses prevent its use
- whether certain enemies can counter it
- whether it has a carrying limit
- whether it consumes a full turn
- whether it works automatically or must be selected before defeat

## Return Talisman

A return talisman immediately removes the party from the dungeon.

Intended result:

- preserve unsecured experience
- abandon unsecured gold
- abandon unsecured loot
- abandon unsecured materials and components
- consume the talisman
- return directly to the hub

This creates an emergency decision:

> Preserve the experience earned during the run, or risk everything while trying
> to leave normally?

The talisman should not function as a free perfect extraction.

Its exact name remains unresolved.

## Trader

The trader is the central preparation and recovery service at the hub.

The trader should provide reliable access to useful, story-appropriate supplies
without selling the strongest rewards in the game.

## Regular Stock

Possible regular stock includes:

- healing potions
- smoke bombs
- return talismans
- common alchemical ingredients
- common weapon-refinement materials
- basic weapon components
- simple resistance items
- ordinary utility consumables
- preparation supplies

The trader should ensure that core character mechanics remain usable without
depending entirely on random drops.

## Story And Dungeon Progression

Trader inventory should expand according to:

- story progression
- dungeon depth
- defeated bosses
- discovered regions
- unlocked trade routes
- rescued or encountered NPCs
- recovered crafting knowledge

The trader may sell equipment appropriate to the current stage of the game.

The trader should provide reliable adequacy.

The dungeon should provide exceptional power.

## Zhaivra And Alchemical Supplies

Zhaivra's core compound mechanics should not depend completely on random dungeon
drops.

The trader should sell common ingredients required for basic preparations, such
as:

- common fire compounds
- common poison compounds
- smoke-producing ingredients
- basic reaction agents
- reservoir-filling materials

Rare, transformative, or unusually powerful reagents should still come from:

- dungeon exploration
- elite enemies
- bosses
- rare gathering points
- dismantled equipment
- hidden rooms
- story rewards

The intended split is:

```text
Trader
-> dependable access to the basic kit

Dungeon
-> rare ingredients and build-defining discoveries
```

Exact compound-consumption rules remain unresolved.

## Healing Potions

Healing potions should be:

- purchasable from the trader
- discoverable inside the dungeon
- obtainable through rewards
- subject to a carrying limit

A carrying limit is important so that buying an excessive stockpile does not
become the dominant solution to dungeon difficulty.

Preparation should require meaningful choices between:

- more healing
- an emergency smoke bomb
- a return talisman
- alchemical supplies
- weapon-refinement materials
- accessories
- saving gold for later progression

Exact healing values, prices, carrying capacity, and potion tiers remain
unresolved.

## Gold

Gold becomes the primary hub-economy currency.

Intended gold sinks include:

- healing potions
- smoke bombs
- return talismans
- alchemical ingredients
- common refinement materials
- common weapon components
- rings
- pendants
- component-installation services
- component-removal services
- other future crafting or preparation costs

Gold found during a dungeon run remains unsecured until successful extraction.

The final rules for gold already carried into the dungeon remain unresolved. The
likely direction is that banked hub gold remains secured while gold found during
the active run is at risk.

## Accessories

Each Drifter should have a small accessory system separate from their permanent
signature weapon.

Proposed slots:

- one ring
- one pendant

Two slots provide meaningful build customization without turning the characters
into generic armor mannequins or undermining their signature equipment.

## Trader Accessories

The trader may sell useful accessories appropriate to the current story and
dungeon tier.

Possible effects include:

- increased maximum HP
- increased maximum mana
- improved potion effectiveness
- elemental resistance
- poison resistance
- improved accuracy
- improved dodge
- modest critical bonuses
- improved searching
- faster super-meter generation
- reduced consumable costs
- modest stat bonuses

Trader accessories should be useful and dependable, but generally not the
strongest available items.

## Dungeon Accessories

The strongest, strangest, and most build-defining rings and pendants should come
from:

- exploration
- bosses
- elite enemies
- hidden rooms
- rare events
- story choices
- major discoveries

The player may buy a competent accessory.

The player should usually discover a legendary one.

## Equipment Retention

Previously equipped rings and pendants are secured equipment.

They are not lost when the party dies during a later dungeon run.

A ring or pendant found during the current run remains unsecured until
extraction.

Exact rules for equipping newly found accessories inside the dungeon remain
unresolved.

## Risk And Preparation

The system should create a recurring choice between spending secured resources
now and saving them for later.

Before entering the dungeon, the player may decide to:

- buy additional healing
- buy an escape tool
- purchase basic alchemical supplies
- buy common weapon materials
- purchase a story-appropriate accessory
- save gold for future refinement
- enter underprepared to preserve resources

Inside the dungeon, the player repeatedly decides whether to:

- continue deeper
- search another room
- fight an optional encounter
- retreat toward an exit
- use a smoke bomb
- sacrifice loot with a return talisman
- risk losing the entire unsecured run

## Relationship To Expeditions

The active dungeon run and the expedition system should remain distinct.

Dungeon runs:

- are directly played
- create extraction risk
- produce unsecured experience and loot
- may be entered whenever permitted by story rules

Expeditions:

- are passive or semi-passive assignments
- use expedition energy
- gather supporting resources
- help underused Drifters remain viable
- may provide common supplies, ingredients, or materials

Exact overlap between expedition rewards and trader stock remains unresolved.

## Completed Gameplay Loop

```text
Select and prepare the active Drifter or party
-> equip ring and pendant
-> purchase consumables and supplies
-> enter the dungeon
-> fight, explore, and gather
-> accumulate unsecured experience, gold, and loot
-> encounter increasing danger
-> decide whether to continue, retreat, smoke-bomb, or use a talisman
-> extract successfully or lose the run
-> bank rewards
-> level characters
-> refine signature weapons
-> install components
-> adjust accessories
-> restock supplies
-> begin the next run
```

## Design Principle

The trader does not replace dungeon exploration.

The trader provides:

- preparation
- reliability
- recovery
- basic supplies
- common progression materials
- level-appropriate equipment

The dungeon provides:

- danger
- experience
- rare components
- powerful accessories
- exceptional reagents
- major weapon development
- the highest-value rewards

The death system gives those rewards meaning by placing the current run at risk.

## Explicitly Unresolved

Do not freeze these yet:

- trader identity and lore
- trader inventory interface
- exact prices
- exact potion values
- carrying limits
- inventory limits
- whether banked experience exists before leveling
- exact leveling location
- exact return-talisman name
- whether talismans work during combat
- whether smoke bombs work against bosses
- exact accessory effects
- accessory rarity system
- whether accessories can be upgraded
- gold drop quantities
- reward scaling
- storage rules
- whether some loot is automatically secured
- whether story items can ever be lost
- whether quest items are exempt from death loss
- exact expedition and trader overlap
- balancing formulas

Story-critical items and permanent unlocks should not be lost through ordinary
dungeon death unless explicitly designed otherwise.

## Milestone Boundary

This is future design authority only.

Milestone 3 must continue separating definitions from runtime state while
preserving current behavior.

Do not implement during Milestone 3:

- trader systems
- gold banking
- unsecured run inventories
- death-loss rules
- extraction logic
- smoke bombs
- return talismans
- potion limits
- accessory slots
- alchemical purchasing
- weapon-upgrade purchasing

These systems should be implemented only after the underlying architecture can
clearly represent:

- session state
- persistent player state
- dungeon-run state
- inventory ownership
- consumables
- experience ownership
- gold ownership
- equipment slots
- extraction outcomes
- death outcomes

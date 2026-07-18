The current repository confirms the exact gap M9 identified: the playable flow is still one selected Drifter against one Goblin; `main_loop.py`, `Battle`, `BattlePresenter`, and `BattleView` all assume one enemy.

The useful foundations already exist: `GameState`, `StoryState`, `WorldState`, persistent player resources, equipment, snapshots, structured combat, and the separated presentation boundary. Story and world state already expose suitable ownership seams for route position, completed events, discovered locations, and defeated encounters.

The registry currently contains only the basic Goblin, and the snapshot schema is version 7. Those are deliberate M10 expansion points.

I cannot independently fetch tonight’s live GitHub Project README edit through the repository connector. I am therefore treating M9’s quoted campaign finish line, encounter compositions, and corrective review as the controlling amendment to the previously retrieved roadmap—not pretending the obsolete progression-only M10 section remains authoritative.

````md
# Dungeon Drifters M10 — Playable v0.3 Campaign and Build Week Release

## Status

Draft controlling plan for product approval and X plan-mode review.

This document replaces the rejected progression-and-equipment-only M10 plan.

The rejected plan may be consulted only for its useful progression contracts:

- `PlayerState.gain_exp()`
- controlled permanent growth
- deficit-preserving resource maximum growth
- secured-EXP integration
- existing-equipment persistence

The following rejected work is fully deferred:

- `DefensiveItem`
- damage-type armor mitigation
- mitigation stacking
- armor interaction with Gravemantle Break
- generic mitigation protocol expansion
- defensive-equipment snapshot formats

---

# Baseline

Expected starting point:

```text
Repository: MrCodeGameandAnime/Dungeon-Drifters
Branch: master
HEAD: b3a0f2fc4999a0b4a102a5fcfb56a03d00880bad
Checkpoint: v0.2.9 / completed M9
````

Before M10 implementation, X must independently verify:

```text
current branch
current HEAD
origin/master synchronization
clean working tree
full pytest green
compileall green
git diff --check green
manual balance probe runnable
current vertical slice playable
```

Create the approved M10 branch only after baseline verification.

Recommended branch:

```text
m10-playable-v0.3-campaign
```

---

# Mission

Ship the complete playable v0.3 campaign for OpenAI Build Week.

The required player journey is:

```text
select a Drifter
→ begin the fixed surface route
→ fight multiple authored Goblin encounters
→ select exact enemies during multi-enemy combat
→ preserve HP, Mana, Super, inventory, equipment, and progression
→ receive persistent encounter rewards
→ use the fixed rest point
→ perform the approved equipment interaction
→ save and load at safe campaign boundaries
→ defeat the Goblin Lord finale
→ enter the dungeon
→ recruit the fixed second Drifter
```

This campaign path is the product.

Progression, equipment, rest, encounters, save/load, and recruitment are supporting systems beneath it.

---

# Release Priority

The priority order is:

```text
1. Complete playable route
2. Multi-enemy combat
3. Persistent encounter-to-encounter state
4. Rewards and progression
5. Rest and equipment interaction
6. One-slot save/load
7. Goblin Lord finale and recruitment
8. Regression, polish, documentation, submission
9. Stretch work only after the release gate is green
```

A technically interesting subsystem must not displace a required campaign step.

---

# Source of Truth

Use this order when information conflicts:

```text
1. Current product decisions from M
2. Current GitHub Project v0.3 README
3. Explicit corrections in M9’s review
4. Current repository behavior and architecture
5. Approved M10 plan
6. Older milestone documents and prior conversations
```

A difference is not automatically a defect.

Determine whether it represents:

```text
an approved evolution
an unfinished migration
an obsolete document
or a real contradiction
```

Stop rather than silently reconciling a material contradiction.

---

# Architectural Locks

## Lock 1 — One GameState per campaign run

The selected campaign must continue using one authoritative `GameState`.

Do not recreate or copy persistent state between route nodes.

`GameState` owns:

```text
party / active Drifter state
story position
world progression
campaign metadata
```

## Lock 2 — Use existing story and world ownership

Use existing ownership wherever practical:

```text
StoryState
→ current chapter
→ current scene / route node
→ current location
→ story flags
→ completed events
→ player decisions

WorldState
→ discovered locations
→ defeated encounters
→ opened or consumed route objects
→ persistent dungeon changes
```

Do not duplicate route completion in several unrelated containers.

## Lock 3 — Authored route definitions are immutable

The fixed campaign route must be represented as authored data.

Runtime state stores identifiers and completion state, not duplicate copies of encounter definitions.

Do not build:

```text
procedural maps
random route generation
branching quest graphs
random encounter tables
```

## Lock 4 — Encounter is the campaign reward boundary

An encounter may contain one or more enemies.

Rewards belong to the encounter, not to repeated per-enemy callbacks.

Recommended contract:

```text
EncounterDefinition
→ encounter ID
→ ordered enemy spawn definitions
→ authored reward
→ route metadata

EncounterState
→ runtime enemy instances
→ completion state
→ encounter-local identifiers
```

Recommended reward decision:

```text
Each authored encounter owns one total reward.
The reward is granted exactly once when every required enemy is defeated.
```

Do not call a reward service once per enemy.

## Lock 5 — Battle remains combat orchestration

Battle owns:

```text
encounter combat flow
turn scheduling
target selection
resolver calls
accepted-action completion
victory and defeat detection
semantic battle events
```

Battle does not own:

```text
route advancement
EXP tables
reward authoring
save files
rest
recruitment
world completion
```

The campaign/session layer handles those after Battle returns.

## Lock 6 — Preserve the UI/engine separation

Battle continues to receive semantic input through the battle UI port.

The presenter remains pure.

The terminal UI remains stateless.

Multi-enemy support must extend the existing boundary rather than moving terminal logic back into Battle.

## Lock 7 — Multi-enemy is player-versus-many only

Required v0.3 combat shape:

```text
one active player-controlled Drifter
versus
one or more enemies
```

Required recruitment does not automatically require two-player party combat.

Two-Drifter combat remains stretch work.

## Lock 8 — Exact target identity cannot depend on display names

Duplicate enemy types must remain independently targetable.

Each enemy instance requires a stable encounter-local target identifier separate from:

```text
display name
class name
archetype name
list position that changes after death
```

Status and targeting tests must distinguish duplicate Warriors or Elites.

## Lock 9 — Persistent resources survive encounters

Unless changed by an approved route action:

```text
current HP persists
current Mana persists
Super persists according to the approved Super rule
inventory persists
prepared payloads persist
equipment persists
EXP and level persist
gold persists
```

CombatState and presentation history never persist beyond one encounter.

## Lock 10 — Rest is the recovery mechanism

Do not automatically refill the player after every victory.

The fixed authored rest node performs the approved deterministic restoration.

Rest cannot be repeatedly farmed unless the route explicitly permits it.

## Lock 11 — Save only at safe campaign boundaries

Required save shape:

```text
one slot
out of combat
fixed safe route boundaries
strict schema validation
no CombatState
no BattlePresentationSession
no active input phase
```

No mid-turn or mid-encounter save.

## Lock 12 — Evolve persistence once

The current snapshot schema is version 7.

M10 must first freeze the complete campaign persistence shape, including:

```text
party
active Drifter
route position
story state
world state
player resources
progression
inventory
equipment
character run state
recruitment
```

Then perform one deliberate schema evolution:

```text
STATE_SCHEMA_VERSION = 8
```

Do not increment the schema independently for each M10 feature.

## Lock 13 — Reconstruct authored definitions on load

Loading must reconstruct canonical authored data from stable identifiers.

Do not deserialize arbitrary Python objects or treat saved move definitions as runtime authority.

Recommended shape:

```text
saved profile ID
→ canonical CharacterProfile
→ canonical character factory
→ fresh authored loadout
→ apply validated mutable saved state
```

## Lock 14 — No forced first-Goblin level

EXP pacing must be authored against the complete surface campaign.

Do not inflate the first Goblin’s reward merely to demonstrate leveling.

The route must answer:

```text
Where does level 2 normally occur?
How many levels are expected before the Goblin Lord?
What resource growth is expected before the finale?
```

## Lock 15 — No unapproved enemy or equipment lore

X may implement approved contracts and authored values.

X must not invent:

```text
canonical enemy names
Goblin Lord abilities
equipment names
equipment lore
reward values
recruited Drifter identity
story dialogue
route order
```

unless the approved README or M provides them.

---

# Product Decisions Required

The following decisions must be resolved before their owning section executes.

## Before M10-B

```text
Exact fixed route-node order
Exact encounter order
Exact location of rest
Exact location of equipment interaction
Exact safe save boundaries
Exact boss encounter composition sequence
```

The route must be transcribed from the approved README without reinterpretation.

## Before M10-C

```text
Multi-enemy turn schedule
```

Recommended minimal rule:

```text
Player phase
→ each living enemy acts once in authored order
→ repeat
```

Initiative may determine whether the first round begins with the player phase or enemy phase.

X must not choose a different scheduler without approval.

Also decide:

```text
When one enemy remains, auto-target or still show target selection?
```

Recommended:

```text
one living enemy → auto-target
multiple living enemies → explicit target phase
```

## Before M10-D

```text
Encounter-total reward values
Expected first level location
Expected pre-boss level
Whether secured-EXP Intuition scaling is active
Gold rewards, if any
Whether permanent stat growth is awarded during this route
```

Recommended:

```text
authored encounter-total EXP
secured-EXP scaling active
no player-facing stat-allocation menu
```

## Before M10-F

```text
Rest restores:
- HP?
- Mana?
- Super?
- prepared payloads?
- run inventory?
```

Recommended minimum:

```text
HP → full
Mana → full
Super → preserve
prepared payloads → preserve
run inventory → preserve
```

The approved product rule overrides this recommendation.

## Before M10-E

```text
Fixed equipment reward
Equipment slot
Stat bonuses
Who may equip it
Whether it replaces a signature weapon
```

Recommended direction:

```text
Use one stat-bonus accessory or other non-weapon item
so every Drifter keeps their signature weapon.
```

No damage-type mitigation mechanic is introduced.

## Before M10-G

```text
Production save-file path
Manual save, automatic checkpoint save, or both
Load option location
Behavior when no save exists
Behavior when save data is invalid
Defeat recovery behavior
```

Recommended minimum:

```text
one fixed save path
explicit Save at approved safe nodes
Load Game on the opening menu
clear non-destructive failure on invalid data
```

## Before M10-H

```text
Fixed recruited Drifter
Recruit starting level
Recruit starting EXP
Recruit current HP/Mana/Super
Recruit starting equipment and run state
Whether the recruit becomes active immediately
```

No random recruit selection.

---

# M10-A — Campaign Session Shell and Persistent Route State

## Purpose

Replace the one-battle main-loop shape with a campaign session capable of advancing through authored route nodes while preserving one authoritative object graph.

## What Already Exists

```text
GameState
PlayerState
StoryState
WorldState
CharacterProfile roster
character selection
single-battle main loop
strict plain-value snapshots
```

## Integrate

Preserve:

```text
CharacterProfile
→ Character
→ PlayerState
→ GameState
```

The same selected `PlayerState` must remain active throughout the surface route.

## Build

Add the smallest campaign orchestration layer required to:

```text
start new campaign
read current route node
present route content
launch encounter
process victory or defeat
advance to the next node
perform rest
open equipment interaction
save
load
transition location
recruit
finish the v0.3 route
```

Recommended separation:

```text
authored route definition
runtime route/session controller
existing StoryState
existing WorldState
```

Introduce a minimal party/roster state capable of owning:

```text
ordered PlayerState members
active member identifier
initial selected Drifter
later fixed recruit
```

Compatibility requirement:

```text
game_state.player_state
```

must continue exposing the active Drifter unless a deliberate repository-wide migration is approved.

Freeze the complete schema-8 persistent shape here, even when some fields begin empty.

## Required Tests

Prove:

```text
one GameState is created per new run
selected Drifter becomes the first party member
active PlayerState remains the same object
campaign begins at the approved first node
StoryState contains the current route position
WorldState begins with no defeated campaign encounters
invalid route transitions are rejected
completed route nodes cannot regress accidentally
party members cannot be duplicated
snapshot remains strict plain data
schema version is exactly 8
```

## Manual Gate

```text
launch game
select each of the four Drifters
confirm campaign begins at the first authored route node
confirm no combat behavior changed
```

## Scope Cuts

Do not add:

```text
branching routes
map navigation
quest log
random travel events
party combat
character switching during battle
```

## Commit

```text
M10-A - Add campaign session shell and route state
```

## Stop Conditions

Stop if:

```text
the approved route cannot be represented without duplicating StoryState/WorldState
party ownership requires replacing PlayerState rather than wrapping it compatibly
schema-8 shape is not yet complete enough to freeze
current character selection would regress
```

---

# M10-B — Authored Encounter Definitions and Route Progression

## Purpose

Represent the complete fixed surface route as authored encounter data.

## What Already Exists

```text
Enemy definition/runtime separation
EnemyState
enemy registration
enemy factory
Goblin definition
Goblin structured moves
enemy tier support
WorldState defeated-encounter tracking
```

## Integrate

Use the existing enemy registration and factory system.

Do not bypass it with campaign-specific inline enemy objects.

## Build

Add the approved enemy archetypes needed by the campaign:

```text
Goblin
Goblin Warrior
Goblin Elite
Goblin Lord
```

Names here are descriptive placeholders unless they exactly match the approved authored names.

Add encounter definitions for the approved compositions, including:

```text
two Warriors
two Elites
Goblin Lord + Goblin
Goblin Lord + Goblin + Warrior
```

Include the existing introductory Goblin encounter where required by the route.

Each encounter definition must own:

```text
stable encounter ID
ordered spawn specifications
stable enemy-instance target keys
authored reward reference
route-node association
```

Each encounter launch creates fresh `EnemyState` instances.

Defeated encounters are recorded only after full encounter victory.

## Enemy Authoring Constraints

Use the smallest combat kits needed to establish hierarchy.

Do not build:

```text
advanced tactical AI
summoning
phase transitions
procedural move generation
generic boss scripting engine
large new status systems
```

Enemy move definitions must remain structured and resolver-compatible.

## Required Tests

Prove:

```text
every approved enemy archetype is registered
factory creates independent runtime instances
duplicate archetypes do not share resources or status identity
every route encounter has a unique ID
every enemy instance has a unique stable target key
all approved compositions are exact
unknown encounter IDs fail clearly
route cannot skip an uncleared required encounter
full encounter completion advances exactly one route node
```

Every authored enemy move must pass resolver compatibility tests.

## Manual Gate

Render or inspect every authored encounter roster and confirm:

```text
correct encounter ID
correct enemy count
correct enemy order
correct display labels
correct route position
```

No multi-enemy battle is required yet.

## Scope Cuts

Do not add:

```text
random encounter generation
enemy loot drops
dynamic difficulty scaling
new elements or statuses unless required by approved enemy kits
optional route encounters
```

## Commit

```text
M10-B - Add authored Goblin route encounters
```

## Stop Conditions

Stop if:

```text
enemy stats, moves, or rewards are not approved
the README encounter order is ambiguous
a new generic combat mechanic would be required
the existing registry cannot support authored variants without architectural conflict
```

---

# M10-C — Multi-Enemy Battle, Exact Targeting, and Victory

## Purpose

Upgrade the current one-player-versus-one-enemy battle to one-player-versus-many while preserving every M9 combat and presentation contract.

This is the highest-risk implementation section.

## What Already Exists

```text
Battle orchestration
CombatResolver
CombatState keyed by combatant identity
accepted-action lifecycle
pure BattlePresenter
immutable BattleView
stateless TerminalBattleUI
typed semantic BattleInput
structured battle log
single-enemy HUD
```

## Integrate

Replace the single-foe assumption with an encounter runtime containing an ordered collection of enemies.

Do not move formulas or status mechanics into Battle.

## Build

### Encounter Runtime

Battle receives one encounter runtime rather than assuming one `foe`.

It must expose:

```text
all enemy instances
living enemies
defeated enemies
lookup by stable target key
all-enemies-defeated state
```

### Presentation Models

Extend the immutable view contract to expose:

```text
tuple of enemy CombatantView values
stable target options
selected/pending move context where required
```

Do not expose mutable `EnemyState` objects.

### Semantic Target Input

Add a typed input such as:

```python
ChooseTarget(target_key)
```

Add a target-selection interaction phase.

Required flow:

```text
choose Attack or Super
→ choose move
→ if self-targeted: resolve
→ if one enemy target is available: approved auto-target rule
→ if multiple enemy targets are available: choose exact target
→ validate target against the exact offered view
→ resolve canonical actor-owned move
```

Invalid target input:

```text
does not spend resources
does not consume a turn
does not mutate CombatState
does not lose the chosen move unexpectedly
```

### Enemy Turns

Implement the approved deterministic turn scheduler.

Dead enemies:

```text
cannot act
cannot be targeted
remain available for encounter result/audit data
```

### Status Isolation

Prove independently for duplicate enemy types:

```text
Burn on Warrior A does not affect Warrior B
Poison on Elite A does not affect Elite B
Frost charges remain source-target specific
Gravemantle Break remains tied to the exact target
Conductive and Turbulence remain source-target specific
Stun/Frozen suppress only the affected enemy
```

### Lifecycle

An accepted action must complete exactly once.

When the player acts, pass the approved living opposing set into lifecycle completion.

When one enemy acts, the player is the opposing combatant.

Do not advance accepted-action lifecycle for suppressed opportunities.

### Victory and Defeat

Victory requires:

```text
player alive
and
all required enemies defeated
```

Defeat includes:

```text
player defeated
mutual death
```

Defeating one enemy must not end the encounter while another enemy remains alive.

Return a structured encounter result or equivalent verified encounter-completion contract suitable for campaign rewards.

## Required Tests

### Targeting

```text
duplicate enemies receive distinct target keys
only living enemies are offered
unoffered target is rejected
self-target moves skip enemy target selection
one-enemy behavior follows approved auto-target rule
resource cost is charged only after valid target selection
```

### Turn Scheduling

```text
each living enemy receives the approved action opportunity
dead enemy is skipped
suppressed enemy loses only its own opportunity
initiative rule is deterministic under injected RNG
turn order remains stable
```

### Lifecycle and Statuses

```text
accepted player action completes once
accepted enemy action completes once
rejected input completes zero times
defend/brace behavior remains correct
status ticks remain actor-specific
lethal status cleanup remains correct
temporary state is destroyed after encounter
```

### Victory

```text
first enemy death does not end battle
last enemy death ends battle
mutual death is defeat
battle result identifies exact encounter
all defeated target keys are available for audit
```

### Presentation

```text
all living enemies render
HP/status data belongs to correct enemy
target menu renders stable numbered options
duplicate names remain distinguishable
60/80/120-column layouts remain readable
ASCII fallback retains all target meaning
```

Run the complete existing M9 combat suite after every meaningful patch.

## Manual Gate

Complete at least:

```text
one two-Warrior encounter
one two-Elite encounter
one Goblin Lord composition
```

Confirm manually:

```text
choose exact target
damage correct target
status remains isolated
kill one enemy
battle continues
remaining enemy acts
kill final enemy
victory occurs
```

## Scope Cuts

Do not implement:

```text
area-of-effect moves
multi-target player moves
party targeting
ally turns
formation systems
initiative stats
advanced enemy AI
enemy coordination mechanics
```

## Commit Shape

This section may require bounded internal commits:

```text
M10-C1 - Add encounter runtime and multi-enemy models
M10-C2 - Add semantic enemy targeting
M10-C3 - Add multi-enemy turn and victory flow
M10-C4 - Harden statuses and multi-enemy presentation
```

Push after every green commit.

## Mandatory Review Stop

Stop after M10-C.

Do not automatically proceed into progression until:

```text
focused tests green
full suite green
compileall green
balance probe has no unexplained single-Goblin regressions
manual multi-enemy gate passes
all commits pushed
CI green
M reviews the multi-enemy diff
```

---

# M10-D — Encounter Rewards and Persistent Progression

## Purpose

Award one authored reward after complete encounter victory and carry progression through the campaign.

## What Already Exists

```text
Level
Exp
threshold carryover
multiple-level support
PermanentStats
resource maximum recalculation
Intuition secured-EXP scaling helper
PlayerState gold
persistent resources
```

## Integrate

Add controlled progression entry points on `PlayerState`.

Do not duplicate threshold logic outside `Exp.gain()`.

## Build

### Encounter Reward Contract

Recommended immutable shape:

```text
EncounterReward
→ total EXP
→ gold, when approved
→ fixed item reward ID, when approved
→ fixed permanent growth, when approved
```

The campaign grants this once after verified encounter victory.

### PlayerState EXP API

Add:

```python
player_state.gain_exp(amount)
```

Return an inspectable immutable result containing:

```text
EXP awarded
EXP before/after
level before/after
levels gained
HP maximum before/after
Mana maximum before/after
```

### Resource Growth

When level increases:

```text
recalculate maximum HP
recalculate maximum Mana
increase current HP by positive maximum delta
increase current Mana by positive maximum delta
preserve the amount missing
```

Do not full-heal on level-up.

### Permanent Growth API

Add:

```python
player_state.increase_permanent_stat(name, amount)
```

It must:

```text
validate before mutation
enforce stat bounds
remain atomic on failure
recalculate HP for Constitution growth
recalculate Mana for Spirit growth
preserve resource deficits
```

No allocation menu is required.

### Secured EXP

Recommended:

```text
apply secured-EXP scaling from the active Drifter’s effective Intuition
to the authored encounter-total EXP reward
```

Use integer basis-point arithmetic.

Do not apply the reward once per defeated enemy.

### Exactly-Once Completion

Reward application and encounter completion must be coordinated so:

```text
victory reward grants once
save/load cannot replay the reward
re-entering an already cleared node cannot grant it again
defeat grants nothing
partial enemy kills grant nothing
```

## Required Tests

```text
one encounter with multiple enemies grants one reward
first enemy kill grants nothing
final enemy kill permits one reward
calling completion twice does not duplicate reward
defeat grants nothing
mutual death grants nothing
EXP carryover remains correct
multiple level gains remain correct
resource deficits remain correct
secured-EXP rounding is exact
gold persists when present
permanent growth is atomic
snapshot reflects progression
```

Add route pacing tests using the approved reward table:

```text
level after each encounter
EXP remainder after each encounter
expected level before Goblin Lord
```

These tests protect the campaign curve.

## Manual Gate

Complete the approved early route and confirm:

```text
reward appears only after full encounter clear
EXP persists into next encounter
level occurs at the approved route point
HP/Mana deficits persist
no automatic post-victory refill occurs
```

## Scope Cuts

Do not add:

```text
random loot
per-enemy reward callbacks
skill trees
level-up selection UI
move purchasing
passive selection
class changes
```

## Commit

```text
M10-D - Add encounter rewards and persistent progression
```

## Stop Conditions

Stop if:

```text
route reward values are unapproved
first-level timing differs from the approved curve
reward application requires Battle to own progression
existing scaling would make a Drifter exceed the intended route curve
```

---

# M10-E — Minimal Equipment Interaction and Persistence

## Purpose

Make existing equipment visibly matter during the campaign without creating a new armor system.

## What Already Exists

```text
equipment slots
inventory transfer
equip
unequip
starting signature weapons
weapon stat bonuses
PlayerState.effective_stat()
equipment snapshot data
```

## Integrate

Preserve the four starting signature weapons and their current combat effects.

Prove their bonuses continue through:

```text
multiple encounters
rest
save
load
boss battle
```

## Build

Add one minimal out-of-combat equipment interaction at the approved route node.

Required flow:

```text
receive or discover approved fixed equipment
→ inspect current equipment
→ inspect eligible inventory equipment
→ choose slot/item
→ equip
→ previous item returns to inventory when applicable
→ continue route
```

### Conditional Item Model

If the approved reward is a `Weapon`:

```text
reuse the existing Weapon contract
```

If the approved reward occupies a non-weapon slot:

```text
add the smallest validated stat-bonus equipment contract
generalize PlayerState.effective_stat() across equipped stat-bonus items
```

Do not add:

```text
damage-type mitigation
armor ratings
resistances
Break interaction
durability
rarity
set bonuses
```

### UI Boundary

This is a campaign/out-of-combat interaction.

Do not force equipment management into `Battle`.

A small terminal equipment screen is sufficient.

## Required Tests

```text
starting weapons still affect actual combat
equipment survives encounter transition
approved reward enters inventory exactly once
eligible item equips into correct slot
invalid slot/item leaves state unchanged
replacement conserves both items
effective stat changes once
permanent stat does not change
next encounter uses changed effective stat
save/load preserves inventory and equipment
```

## Manual Gate

```text
earn approved item
open equipment interaction
equip item
inspect changed effective value
enter next encounter
observe intended combat effect
save and load
confirm item remains equipped
```

## Scope Cuts

Do not add:

```text
shops
loot tables
random items
equipment comparison automation
drag-and-drop UI
defensive mitigation
crafting
```

## Commit

```text
M10-E - Add campaign equipment interaction
```

## Stop Conditions

Stop if:

```text
equipment reward or bonuses are unapproved
implementation would replace signature weapons contrary to product direction
a new resolver formula would be required
snapshot shape would need another schema change
```

---

# M10-F — Fixed Deterministic Rest

## Purpose

Provide the authored recovery point that makes persistent resources playable across the route.

## What Already Exists

```text
mutable Health
mutable Mana
persistent Super
persistent character run state
route state
```

## Integrate

Rest operates on the active `PlayerState` through the campaign layer.

It does not create a new player or reset progression.

## Build

At the approved rest node:

```text
present rest
apply approved deterministic recovery
record the rest event
advance route
```

Recommended default:

```text
HP → restore to maximum
Mana → restore to maximum
Super → preserve
prepared payloads → preserve
run inventory → preserve
equipment → preserve
EXP/level → preserve
```

The rest event must be one-time unless the route explicitly says otherwise.

## Required Tests

```text
rest changes only approved resources
rest preserves level and EXP
rest preserves equipment
rest preserves inventory
rest preserves route completion
rest cannot be farmed repeatedly
rest survives save/load
skipping rest follows approved behavior, when skipping is allowed
```

## Manual Gate

Reach rest while damaged and low on Mana.

Confirm:

```text
before/after values display correctly
approved resources restore
unapproved resources do not reset
route advances
next encounter uses restored state
```

## Scope Cuts

Do not add:

```text
camp crafting
random rest events
party conversations
rest bonuses
status cures beyond approved behavior
repeatable farming
```

## Commit

```text
M10-F - Add fixed campaign rest
```

## Stop Conditions

Stop if the persistent-resource or Super rule is not approved.

---

# M10-G — One-Slot Save and Load

## Purpose

Persist the complete campaign state at safe boundaries and reconstruct it without trusting saved authored definitions.

## What Already Exists

```text
strict plain-value validation
GameState snapshot
PlayerState snapshot
schema versioning
canonical CharacterProfile factories
equipment snapshots
story and world snapshots
```

## Integrate

Use the schema-8 shape frozen in M10-A.

Do not create a second competing campaign persistence model.

## Save Payload

Must include:

```text
schema version
party members
active member
profile IDs
mutable permanent stats
current/max HP
current/max Mana
Super
level
EXP
gold
inventory
equipment
character run state
route node
chapter/scene/location
story flags/events/decisions
defeated encounters
discovered locations
persistent route/dungeon state
recruitment state
```

Must not include:

```text
CombatState
status objects
BattlePresentationSession
BattleView
pending input
terminal formatting
resolver
RNG object
arbitrary Python classes
```

## Loading

Recommended sequence:

```text
read JSON
→ validate top-level shape
→ validate schema version
→ resolve profile IDs
→ create canonical characters
→ create PlayerState members
→ apply validated mutable values
→ restore party
→ restore StoryState
→ restore WorldState
→ create GameState
→ verify invariants
```

Reject unsupported or corrupted data clearly.

No schema migration framework is required for v0.3.

## File Safety

Use:

```text
one production save path
temporary write
successful JSON validation
atomic replace where supported
```

Tests inject temporary paths.

Do not overwrite a known-good save with invalid payload generation.

## Safe Boundaries

Saving is allowed only when the campaign controller is outside Battle.

Examples:

```text
after encounter completion and reward
at rest
at equipment node
before or after dungeon transition
after recruitment
```

## Opening Flow

Add the approved minimal choice:

```text
New Game
Load Game
```

When no save exists, Load is unavailable or reports clearly without crashing.

## Required Tests

### Round Trip

```text
new campaign
after multi-enemy victory
after rewards/level
after equipment interaction
after rest
after synthetic two-member party state
```

For each:

```text
save
destroy in-memory object
load
compare authoritative state
continue route
```

### Validation

```text
missing file
malformed JSON
wrong schema
unknown profile ID
unknown equipment ID
invalid resource ranges
invalid route node
duplicate party member
invalid active-member ID
```

### Safety

```text
cannot save active CombatState
failed write does not destroy old save
loaded equipment affects combat
loaded defeated encounter cannot reward again
```

## Manual Gate

```text
play to approved checkpoint
save
exit process
restart
load
confirm exact route node
confirm HP/Mana/Super
confirm EXP/level
confirm inventory/equipment
continue into next encounter
```

## Scope Cuts

Do not add:

```text
multiple save slots
cloud saves
autosave history
mid-battle saves
schema migrations
save thumbnails
save-selection UI
```

## Commit Shape

```text
M10-G1 - Freeze schema-8 campaign persistence
M10-G2 - Add one-slot save and load
M10-G3 - Add opening load flow and round-trip gates
```

## Mandatory Review Stop

Stop after M10-G.

Require:

```text
all save/load tests green
full suite green
compileall green
manual process-restart round trip passes
schema remains exactly 8
CI green
M reviews persistence diff
```

---

# M10-H — Goblin Lord Finale, Dungeon Transition, and Recruitment

## Purpose

Complete the authored surface campaign and establish the first dungeon-party state.

## What Already Exists

```text
route state
multi-enemy combat
authored encounters
persistent rewards
rest
equipment
save/load
CharacterProfile roster
party foundation
```

## Integrate

Use the approved Goblin Lord encounter definitions and fixed route order.

Do not create a separate boss combat engine.

The Goblin Lord remains an authored enemy using the shared resolver and multi-enemy Battle.

## Build

### Finale

Launch the approved final composition:

```text
Goblin Lord
plus approved supporting Goblins/Warriors
```

Victory requires every required enemy to be defeated.

Award the final authored surface reward exactly once.

### Transition

After victory:

```text
mark surface route complete
mark Goblin Lord encounter defeated
discover dungeon entrance
change current location to the approved dungeon location
advance current scene
```

### Recruitment

Create the approved fixed second Drifter through the canonical `CharacterProfile`.

Add one new `PlayerState` to the party.

Do not duplicate the chosen lead.

Record recruitment in authoritative state.

The recruit must survive save/load.

No required two-Drifter battle follows recruitment.

### Ending

Render the approved v0.3 completion state:

```text
Goblin route complete
dungeon reached
second Drifter recruited
future descent established
```

## Required Tests

```text
boss encounter uses shared Battle
supporting enemies remain targetable
boss death alone does not win while support remains
support deaths alone do not win while boss remains
full clear grants final reward once
surface route marks complete
dungeon location becomes current
fixed recruit is canonical
party contains exactly two distinct members
active lead follows approved rule
save/load preserves both members
reloading finale completion cannot duplicate recruit or reward
```

## Manual Gate

Complete the entire route with one Drifter from New Game through:

```text
Goblin Lord victory
dungeon transition
recruitment
save
exit
load
two-member party confirmation
```

## Scope Cuts

Do not add:

```text
recruit selection
party dialogue system
relationship system
party equipment sharing
party formation
two-Drifter required combat
dungeon procedural generation
```

## Commit Shape

```text
M10-H1 - Add Goblin Lord finale
M10-H2 - Add dungeon transition and fixed recruitment
M10-H3 - Harden finale persistence
```

## Stop Conditions

Stop if:

```text
Goblin Lord authored data is unapproved
fixed recruit is unapproved
recruit state would require another schema bump
boss mechanics require a new generic combat engine
```

---

# M10-I — Full Regression, Release Hardening, and Submission

## Purpose

Prove that the complete v0.3 campaign works for all four starting Drifters, harden the release, and prepare the Build Week submission.

## Automated Campaign Gates

Create deterministic full-route coverage for:

```text
Ser Branoc
Azhvielle
Zhaivra
Joruun
```

Each route must prove:

```text
selection
first encounter
multi-enemy targeting
enemy turn scheduling
status isolation
persistent HP/Mana/Super
encounter reward
approved leveling curve
equipment interaction
rest
save/load
Goblin Lord finale
dungeon transition
fixed recruitment
strict final snapshot
```

## Character-Specific Regression

Protect:

```text
Branoc Brace and Ironwake lifecycle
Azhvielle Overcharge/Break/Instability/Frost behavior
Zhaivra preparation, Burn, and Poison persistence rules
Joruun current switching, Conductive, Turbulence, and Stun
all four Supers
```

## Balance Probe Expansion

Preserve the canonical M9 single-enemy snapshot.

Add separate campaign-era probes for:

```text
two Warriors
two Elites
approved Goblin Lord compositions
full fixed route where deterministic policy support is practical
```

Do not rewrite M9 history.

Record:

```text
commit SHA
route version
encounter values
reward table
seeds
win/loss
turn count
remaining resources
level progression
Super usage
```

Balance changes require evidence.

Do not weaken an enemy merely because one scripted route policy is poor.

## Manual Playthroughs

Required:

```text
one complete route with every starting Drifter
one defeat path
one invalid-save path
one save/load process restart
one narrow-terminal run
one ASCII-disabled/redirected-output check
```

## Terminal Polish

Ensure:

```text
multi-enemy HUD is readable
target selection is clear
duplicate enemies are distinguishable
route transitions are clear
rewards are concise
rest results are clear
equipment choices are clear
save/load results are clear
final recruitment is clear
```

No large visual redesign.

## Documentation

Update:

```text
README
play instructions
current playable campaign
enemy/encounter architecture
multi-enemy targeting
progression and rest
equipment interaction
save path and load instructions
known limitations
v0.3 completion summary
```

Document explicitly:

```text
what was built during Build Week
what existed before Build Week
what Codex/GPT-5.6 contributed
what remains deferred
```

## Submission Package

Prepare:

```text
clean public repository
green CI
release commit
v0.3 tag
screenshots
short demonstration video
judge play instructions
Build Week development evidence
commit/PR/CI references
Devpost description
submission before deadline
```

## Final Release Gate

```text
All required M10 sections complete.
All four Drifters complete the route.
Multi-enemy target selection works.
Every living enemy receives correct turns.
Statuses remain isolated.
HP/Mana/Super follow approved persistence rules.
Encounter rewards grant exactly once.
Level pacing matches approved route.
Equipment matters and persists.
Rest works exactly once where authored.
One-slot save/load survives process restart.
Goblin Lord finale completes.
Dungeon transition completes.
Fixed recruitment persists.
Snapshots and saves use schema 8.
Full pytest passes.
Compileall passes.
git diff --check passes.
Balance probes contain no unexplained regressions.
Manual gates pass.
CI is green.
Working tree is clean.
README and submission materials are current.
v0.3 is tagged and shipped.
```

## Commit Shape

Recommended:

```text
M10-I1 - Add full-route regression coverage
M10-I2 - Harden terminal campaign presentation
M10-I3 - Update v0.3 documentation and release assets
M10-I4 - Finalize Build Week release
```

---

# Stretch Only — First Two-Drifter Dungeon Encounter

Do not begin until the complete required release gate is green.

Stretch scope:

```text
one fixed dungeon encounter
two recruited PlayerState members
controlled ally turn order
exact ally and enemy targeting
no party swapping outside the encounter
no advanced formation or AI
```

Stretch work must not delay:

```text
release hardening
demo recording
submission
```

---

# Autonomous Execution Strategy

## Wave 1 — Campaign Foundation

```text
M10-A
M10-B
```

Execution:

```text
one autonomous Codex run
separate commit and push per milestone
continue only while tests and CI remain green
```

Stop before M10-C if any product data remains unresolved.

## Wave 2 — Multi-Enemy Foundation

```text
M10-C1
M10-C2
M10-C3
M10-C4
```

Execution:

```text
controlled autonomous run
commit and push each patch
mandatory review after completion
```

This is the highest architectural-risk wave.

## Wave 3 — Campaign Systems

```text
M10-D
M10-E
M10-F
```

Execution:

```text
one autonomous run after approved product values are supplied
separate commit and push per milestone
```

Stop on reward, equipment, rest, or balance ambiguity.

## Wave 4 — Persistence

```text
M10-G1
M10-G2
M10-G3
```

Execution:

```text
controlled run
mandatory review afterward
```

## Wave 5 — Finish and Ship

```text
M10-H
M10-I
```

Execution:

```text
autonomous through green subcommits
stop immediately on campaign regression
do not begin stretch work automatically
```

---

# Global Verification Contract

Before every commit:

```powershell
.\.venv\Scripts\python.exe -m pytest <focused tests>
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall src tests
git diff --check
git status --short
```

For relevant sections also run:

```text
manual route gate
manual terminal gate
save/load process restart
balance probe
```

After every commit:

```text
push
record full SHA
verify exact-commit CI
continue only when green
```

---

# Global Stop Conditions

X must stop immediately if:

```text
tests fail
CI fails
working tree contains unexplained changes
approved route order is unclear
product values are missing
implementation requires unapproved lore
Battle would need to own campaign progression
presentation would need to mutate mechanics
multi-enemy support changes M9 combat rules unexpectedly
save/load requires a second schema bump
single-Goblin balance changes unexpectedly
scope expands into party combat before required release completion
a required release feature would be deferred to preserve a side feature
```

---

# Explicit M10 Non-Goals

Do not implement before release:

```text
procedural dungeon generation
random encounters
advanced enemy AI
area-of-effect combat
required two-Drifter combat
party formations
party relationship systems
random loot tables
shops
crafting
rarity
durability
damage-type armor mitigation
generic resistance systems
skill trees
move purchasing
class changes
multiple save slots
mid-battle saving
cloud saves
schema migration framework
advanced quest system
large story branching
Android UI
browser UI
```

---

# Final Line to Protect

> M10 succeeds only when Dungeon Drifters is a complete playable v0.3 campaign. Every supporting system must serve that route, and no supporting system may replace it as the milestone.

```
```

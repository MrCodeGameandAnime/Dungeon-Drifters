# Dungeon Drifters Long-Term Architecture, Portability, and Dungeoneering Plan

## Status

Long-term product and architecture direction.

This work is intentionally tabled until the current Dungeon Drifters engine, primary extraction loop, and major gameplay systems are substantially complete and proven in Python.

Do not interrupt active milestone development to begin this work prematurely.

This plan establishes the eventual direction for:

- codebase streamlining
- engine and presentation separation
- procedural dungeon generation
- Story Mode and Dungeoneering
- isolated world economies
- Drifter recruitment and account ownership
- Android, PC, and possible console clients
- a future portable C++ engine core
- automated Python-to-C++ change assistance
- competitive modes such as leaderboards and PvP

---

# Product Vision

Dungeon Drifters should begin as a mechanically complete Python game and eventually mature into a platform-independent game system capable of supporting multiple clients.

The long-term structure is:

```text
Dungeon Drifters Engine
-> receives validated commands
-> applies authoritative game rules
-> produces deterministic state transitions
-> emits semantic outcomes
-> exposes structured presentation data

Clients
-> translate player input into engine commands
-> display engine results
-> never own authoritative game rules
```

Potential clients include:

```text
Python terminal client
Android client
PC graphical client
possible future console clients
automated simulation tools
balance-analysis tools
competitive verification services
```

The core single-player game must remain locally playable.

Android, PC, and console gameplay must not require a remote server merely to run the game, resolve combat, generate dungeons, load saves, or display results.

A server may eventually support optional online features such as:

- leaderboards
- cloud saves
- shared challenge seeds
- live PvP
- asynchronous PvP
- account ownership verification
- tournaments
- replay verification

The normal game must remain functional without those services.

---

# Current Architectural Assessment

Dungeon Drifters is not a spaghetti codebase.

It is well organized, layered, tested, and explicit about ownership. The high-level package structure tells a coherent story.

The current difficulty is cognitive complexity.

A developer can understand the major folders quickly while still needing substantial time to trace how one feature moves through the entire system.

A normal feature can involve:

```text
authored content
-> registration
-> canonical factory
-> runtime state
-> encounter definition
-> session orchestration
-> presenter
-> terminal view
-> persistence
-> reconstruction
-> integration tests
```

Each individual layer may be correct and well designed. The total journey is still expensive to understand.

The long-term goal is therefore not to flatten the architecture into one undifferentiated pile.

The goal is:

```text
Flatten the developer experience.
Preserve strong internal ownership.
Create one obvious supported path for every common task.
```

---

# Guiding Principles

## 1. Python Remains the Prototype and Discovery Language

Python is the correct language for discovering the complete Dungeon Drifters engine.

It allows the project to move rapidly through:

```text
design
-> implementation
-> testing
-> revision
-> architectural discovery
```

The game still needs major systems, including the primary extraction loop. Converting to C++ before those systems exist would lock unstable assumptions into a more expensive development environment.

Python should remain authoritative while the game is still discovering:

- dungeon exploration
- extraction
- run failure
- loot acquisition
- equipment growth
- persistent settlement
- recruitment
- dungeon generation
- world generation
- endgame progression
- competitive rules
- final combat architecture

Python is not disposable work.

Even after a future C++ conversion, Python can remain valuable for:

- the reference engine
- rapid feature prototyping
- balance probes
- validators
- save inspectors
- migration tools
- content scaffolders
- dungeon-generation analysis
- simulation
- parity testing
- automated port assistance

## 2. Complete the Engine Before Porting It

A future C++ conversion must not begin merely because the current vertical slice is stable.

The engine should first contain and prove the actual Dungeon Drifters identity:

```text
enter dungeon
-> explore
-> choose routes
-> fight
-> gather loot and resources
-> recruit Drifters
-> decide whether to continue
-> risk losing run-specific gains
-> extract
-> settle the run
-> convert successful gains into persistent progression
-> prepare for another descent
```

The current route to the Dungeon Entrance is foundational work.

It is not yet the complete game loop.

## 3. The Engine Should Behave Like an API, Not Require a Server

API means a clear programming interface.

It does not automatically mean a remote web service.

The desired local flow is:

```text
player input
-> platform adapter
-> local engine command
-> local state transition
-> semantic result
-> platform display
```

For Android:

```text
Android application
├── local Dungeon Drifters engine
├── local authored content
├── Android presentation layer
└── local save storage
```

No internet connection should be required for ordinary gameplay.

## 4. Content Should Be Input, Not Architecture

Adding ordinary content should not require creating new orchestration paths.

The engine should consume validated specifications for:

- Drifters
- enemies
- moves
- weapons
- equipment
- items
- encounters
- room events
- bosses
- dungeon rules
- routes
- rewards

New mechanics remain engine work.

New content using existing mechanics should be a straightforward authoring task.

## 5. Platform Clients Must Not Own Game Rules

The engine owns:

- validation
- combat rules
- damage
- resources
- progression
- rewards
- loot resolution
- recruitment
- route transitions
- dungeon generation
- extraction
- run settlement
- save semantics
- available actions
- semantic outcomes

Clients own:

- layout
- text rendering
- buttons
- controller input
- touch input
- animation
- sound
- music
- visual effects
- accessibility
- screen navigation
- platform storage integration
- platform achievements

The Android client must not calculate damage.

The PC client must not decide whether Rest is available.

The terminal client must not determine rewards.

All clients ask the engine what is true, what happened, and what actions are currently legal.

---

# Phase 0: Complete Dungeon Drifters in Python

## Objective

Complete and prove the actual game before attempting a native-engine conversion.

## Required Major Systems

The exact milestone structure will be planned later, but the Python engine should eventually prove:

- complete primary extraction loop
- dungeon entry and exit
- room progression
- route choice
- branching dungeon graphs
- loot generation
- loot ownership
- run inventory
- persistent inventory
- extraction settlement
- loss and failure rules
- equipment acquisition
- shops or preparation systems
- Drifter recruitment
- team management
- dungeon difficulty progression
- biome structure
- elite encounters
- bosses
- growth trees
- long-term character development
- world progression
- replayable endgame
- complete Save/Load coverage
- deterministic testing seams

## Exit Condition

Do not consider C++ until Dungeon Drifters has a complete, playable, mechanically representative engine.

The goal is not necessarily to finish every piece of content first.

The goal is to know the final categories of behavior the engine must support.

---

# Phase 1: Architecture Streamlining and Portable Content Foundation

## Objective

Reduce the amount of architectural knowledge required for ordinary development without weakening ownership or validation.

The target experience is:

```text
Copy a template.
Edit one clear definition.
Run one validator.
Run focused tests.
Done.
```

## Desired Public Workflows

A contributor should immediately know:

```text
Add an enemy
-> use this path

Add a Drifter
-> use this path

Add an encounter
-> use this path

Add an item
-> use this path

Add a move
-> use this path

Add a route node
-> use this path

Add persistent state
-> follow this reconstruction contract

Add a screen
-> follow this presentation contract
```

## Proposed Content Organization

Conceptually:

```text
content/
├── drifters/
├── enemies/
├── moves/
├── weapons/
├── equipment/
├── items/
├── encounters/
├── events/
├── bosses/
├── biomes/
└── dungeon_rules/
```

The exact physical structure should be decided only after auditing the completed Python engine.

## Content Specifications

Ordinary built-in content should use declarative, immutable, validated specifications.

Conceptually:

```python
DRIFTER = DrifterSpec(
    drifter_id="branoc",
    profile=...,
    stats=...,
    moves=...,
    mechanic=...,
    equipment=...,
)
```

```python
ENEMY = EnemySpec(
    archetype_id="goblin_warrior",
    stats=...,
    moves=...,
    rewards=...,
    behavior=...,
)
```

```python
ENCOUNTER = EncounterSpec(
    encounter_id="surface_warrior_pair",
    composition=...,
    rules=...,
)
```

The engine validates and consumes these specifications.

Content authors should not manipulate private state, construct sessions, edit persistence internals, or duplicate canonical information.

## Generic Runtime Construction

Where practical, explicit content-specific subclasses should be replaced by generic runtime objects created from validated specifications.

Examples:

```text
DrifterSpec
-> PlayableCharacter

EnemySpec
-> EnemyDefinition
-> EnemyState

EncounterSpec
-> EncounterManifest
```

Special mechanics may still require engine implementations.

The content definition should reference those mechanics through stable identifiers or controlled factories rather than creating new architectural pathways.

## Deterministic Discovery

The project may use convention-based content discovery, but discovery must remain deterministic and testable.

Requirements:

- stable sorted loading
- duplicate ID rejection
- duplicate choice rejection
- unknown reference rejection
- no import-order dependence
- no filesystem-order dependence
- clear validation errors
- explicit content-version awareness

A generated and validated index may be preferable to unrestricted magical scanning.

## Validators and Scaffolders

Future developer commands may include:

```text
python -m tools.scaffold_enemy skeleton_knight
python -m tools.scaffold_drifter new_drifter
python -m tools.scaffold_encounter forgotten_crypt
python -m tools.validate_content
python -m tools.validate_dungeon_grammar
```

The validator should detect:

- duplicate IDs
- invalid stats
- invalid rewards
- unknown moves
- invalid mechanics
- invalid weapons
- impossible equipment
- broken encounter references
- invalid dungeon rules
- persistence identity conflicts
- unsupported platform content
- nondeterministic definitions

## Streamlining Rule

Every normal content addition should aim for:

```text
one primary definition
zero private-field manipulation
zero duplicated authored data
zero manual persistence registration
zero platform-specific game rules
one validation command
one focused proof path
```

## Migration Strategy

Do not rewrite the entire codebase at once.

Use controlled vertical migrations:

```text
define new public path
-> migrate one content family
-> prove identical behavior
-> migrate remaining built-ins
-> remove old path only after full parity
```

Every migration must preserve sealed behavior.

---

# Phase 2: Formal Engine Command and Result Boundary

## Objective

Make the Python engine behave like a headless, embeddable game API.

## Command Model

Clients submit structured commands such as:

```text
UseMove
ChooseTarget
UseItem
Rest
SkipRest
SelectRoute
EnterDungeon
AttemptExtraction
RecruitDrifter
EquipItem
SpendGrowthPoint
SaveGame
LoadGame
```

Commands must be validated by the engine.

Clients must not mutate engine state directly.

## Result Model

The engine returns structured outcomes:

```text
updated authoritative state
semantic events
available actions
validation failures
presentation-ready facts
saveable state
```

Conceptually:

```text
dispatch(command)
-> ActionResult
```

Possible semantic events include:

```text
ManaSpent
DamageDealt
StatusApplied
EnemyDefeated
LootDiscovered
DrifterRecruited
ExtractionSucceeded
ExtractionFailed
LevelGained
RewardGranted
DungeonCompleted
```

The terminal client may render those events as text.

Android may render them as animations, bars, icons, and sounds.

A PC client may render them through a graphical scene.

The engine result remains the same.

## Presentation Data

The application-facing layer should expose structured views instead of requiring clients to inspect domain internals.

Examples:

```text
CharacterView
CombatView
InventoryView
DungeonMapView
ExtractionView
RestView
RecruitmentView
RewardView
```

Presenters should receive typed domain facts and return stable view data.

Platform renderers should not reverse-engineer state ownership.

## Determinism

Where randomness exists, it must come from explicit deterministic seed authorities.

A complete result should be reproducible from:

```text
engine version
content version
generation version
initial state
seed state
ordered command log
```

This foundation supports:

- replay
- debugging
- parity testing
- leaderboard verification
- daily challenges
- cross-platform consistency
- automated C++ conversion validation

---

# Phase 3: Procedural Dungeon Generation

## Objective

Do not manually author hundreds of complete dungeons.

Teach the engine what makes a valid Dungeon Drifters dungeon.

## Core Principle

```text
Do not build 100 dungeons.

Build a generation system capable of producing
large numbers of valid and meaningful dungeons.
```

The project should author reusable components:

- room types
- encounter formations
- events
- treasure outcomes
- Rest variants
- elite scenarios
- boss approaches
- bosses
- extraction conditions
- biome rules
- environmental modifiers
- narrative fragments
- loot budgets
- difficulty curves

The generator combines those components within controlled rules.

## Authored Dungeon Grammar

Procedural generation must not mean unrestricted randomness.

The generator should operate through an authored grammar.

Example invariants:

- every dungeon has an entrance
- every required objective is reachable
- every generated node has valid transitions
- extraction remains reachable when intended
- bosses have valid approach structures
- Rest cannot appear in forbidden sequences
- difficulty rises within controlled depth bands
- branch rewards reflect branch risk
- elite placement respects encounter budgets
- loot follows controlled scarcity rules
- no route creates duplicate rewards
- no generated ID collides
- no room requires unavailable mechanics
- every generated dungeon can save and load
- every completed route can settle correctly

## Generated Dungeon Graph

The generator should produce a validated dungeon instance using the same route and encounter concepts used by authored content.

Conceptually:

```text
Dungeon Rules
+
Seed
+
Biome
+
Depth
+
World State
+
Content Version
=
Validated Dungeon Graph
```

The session should not care whether the graph was manually authored or procedurally generated.

## Seed Hierarchy

The generation structure should support:

```text
Mode Seed
-> World or Campaign State
-> Dungeon Seed
-> Run or Attempt Seed
-> Room, Encounter, Loot, and Event outcomes
```

Derived seeds must be stable and deterministic.

Do not rely on accidental runtime RNG order.

## Generator Testing

The project should validate large seed ranges automatically.

Conceptually:

```python
for seed in seed_range:
    dungeon = generate(seed)
    validate(dungeon)
```

Required proofs include:

- same seed produces the same dungeon
- different seeds produce meaningful variation
- all mandatory nodes are reachable
- extraction rules remain valid
- bosses remain reachable
- rewards cannot duplicate
- generated content uses valid IDs
- save and load preserve the generated instance
- loading does not regenerate a different dungeon
- generation remains isolated across sessions
- malformed generation fails before gameplay begins

---

# Phase 4: Two Game Modes

Dungeon Drifters should ultimately have two major modes powered by the same engine.

---

# Story Mode

## Seed Authority

Story Mode uses the Main Seed.

The Main Seed represents the canonical Dungeon Drifters campaign.

```text
Main Seed
+
story chapter
+
campaign state
+
content version
+
generation version
=
canonical campaign experience
```

## Purpose

Story Mode provides:

- the official narrative
- canonical world progression
- Drifter introductions
- major discoveries
- authored bosses
- mechanic onboarding
- controlled difficulty progression
- extraction-system teaching
- team-building foundations
- the path to unlocking Dungeoneering

## Procedural Use

Story Mode may still use procedural generation, but within narrow authored boundaries.

It can vary:

- minor room arrangement
- ordinary encounter composition
- optional branches
- treasure placement
- noncritical room events
- descriptive presentation

It must preserve:

- required story events
- major bosses
- key discoveries
- canonical chapter order
- required character moments
- narrative continuity
- intended progression gates

The Main Seed is not random chaos.

It is controlled procedural authorship.

## Completion Reward

Completing Story Mode unlocks Dungeoneering.

This establishes a natural progression:

```text
Story Mode
-> learn the world
-> learn the systems
-> complete the canonical journey
-> unlock the long-term mode
```

---

# Dungeoneering

## Seed Authority

Dungeoneering uses a World Seed.

The World Seed should generate more than a single disconnected dungeon.

It should define a deterministic Dungeoneering world.

```text
World Seed
+
world progression
+
generation version
+
content version
=
generated Dungeoneering world
```

The world may contain:

- multiple dungeons
- biome order
- dungeon identities
- boss distribution
- encounter tendencies
- loot tendencies
- extraction structures
- rare events
- world modifiers
- progression pathways

Individual dungeon seeds derive from the World Seed.

Conceptually:

```text
dungeon_seed = derive(
    world_seed,
    dungeon_index,
    dungeon_depth,
    world_state
)
```

Run-specific outcomes may derive from the dungeon seed and attempt context.

## Purpose

Dungeoneering provides the long-term replayable game:

```text
generate a world
-> enter dungeons
-> recruit Drifters
-> gather loot
-> develop the team
-> push deeper
-> extract
-> expand world progression
-> compete
-> repeat
```

It supports:

- shareable worlds
- community seeds
- daily seeds
- weekly seeds
- race-to-Level-100 categories
- extraction records
- hardcore worlds
- Drifter-specific rankings
- build experimentation
- long-term mastery

## Unlock Rule

Dungeoneering unlocks after Story Mode completion.

It is an endgame reward and long-term mode rather than an overwhelming option presented immediately to a new player.

---

# Phase 5: Dungeoneering Entry Paths

After unlocking Dungeoneering, the player should be able to choose how a new World Seed begins.

## Option 1: Carry Forward the Story Team

The player may bring the completed Story team into a new Dungeoneering world.

This preserves continuity and rewards the completed campaign.

Potential imported state may include:

- recruited Story Drifters
- Drifter levels
- permanent stat development
- growth-tree progression
- account-owned Drifter eligibility
- selected persistent character identity

The exact equipment rule should be decided after the complete item and extraction economies exist.

Story gold must not become Dungeoneering gold.

Story consumables and unrelated Story route state should not enter the new world unless explicitly designed to do so.

A carried team enters a fresh World Seed economy.

## Option 2: Start Over at the Dungeon Entrance

The player may choose a true fresh Dungeoneering start.

The world begins at the Dungeon Entrance.

The player receives one random eligible Drifter.

The remaining team must be discovered and recruited within the generated world.

Conceptually:

```text
generate World Seed
-> roll one eligible starting Drifter
-> enter at Dungeon Entrance
-> earn local gold
-> discover recruitable Drifters
-> buy team members inside that world
-> build the team organically
```

This creates a stronger replay and challenge structure than selecting a complete team from a menu.

## Competitive Separation

Legacy and fresh-start runs should not share one undifferentiated leaderboard.

Potential categories include:

- Legacy Team
- Fresh Random Start
- Fixed World Seed
- Unseeded World
- Drifter-specific Fresh Start
- Hardcore
- No Failed Extraction
- Fastest Level 100
- Fastest World Completion
- Deepest Descent

---

# Phase 6: Economy Ownership

Dungeon Drifters should separate account ownership, world-instance progression, and active-run resources.

## Account State

Account state may contain:

- Story completion
- Dungeoneering unlock
- permanently owned Drifters
- cosmetics
- achievements
- account settings
- leaderboard records
- entitlement records
- completed challenges

Account state must not become a universal wallet that trivializes new worlds.

## Story Instance State

Story state may contain:

- campaign progression
- Story team
- Story gold
- Story inventory
- Story equipment
- Story choices
- Story route state

Story gold remains inside the Story instance.

## Dungeoneering World State

Each World Seed owns an isolated economy.

World state may contain:

- World Seed
- generation version
- recruited team
- local levels and progression
- local gold
- local stash
- local equipment
- discovered dungeons
- completed dungeons
- extracted resources
- world modifiers
- active dungeon
- world-specific unlocks

World Seed A cannot transfer gold into World Seed B.

A player cannot farm an easy world indefinitely and use that wealth to trivialize every future world.

## Active Run State

The active run owns temporary risk-bearing state such as:

- run inventory
- unextracted loot
- prepared consumables
- temporary buffs
- current dungeon graph
- current dungeon position
- active objectives
- current run resources
- extraction availability
- run-specific penalties

The extraction system decides which run gains become world-persistent gains.

## Economy Principle

```text
Account:
what the player permanently owns

World:
what the player has earned in this generated world

Run:
what the player is currently risking
```

---

# Phase 7: Drifter Ownership, Recruitment, and Optional Purchases

## Account Ownership

The account may permanently own Drifters.

Ownership means the Drifter is eligible for supported game systems.

Depending on the mode, an owned Drifter may:

- enter the random starting pool
- appear as a recruit inside a generated world
- become available in direct-selection modes
- appear in PvP team construction
- remain eligible across future World Seeds

## World Recruitment

Account ownership does not automatically mean the Drifter has joined every world.

Inside normal Dungeoneering:

```text
Account ownership
-> Drifter may appear

World recruitment
-> local gold is paid
-> Drifter joins that specific world team
```

This preserves the world economy and recruitment loop.

## Real-Money Drifter Purchases

A future commercial model may allow players to permanently buy additional Drifters with real money.

This must be implemented carefully.

The clean rule is:

```text
Cash controls account eligibility.

Instance gold controls world recruitment.
```

Buying a Drifter should not:

- grant universal gold
- bypass all world recruitment
- provide a fully leveled character
- provide superior equipment
- automatically insert the Drifter into every team
- create competitive statistical superiority
- invalidate the extraction economy

Paid Drifters should be mechanical sidegrades with:

- distinct identities
- different combat roles
- different resource loops
- different team interactions
- different build possibilities
- equivalent competitive legitimacy

The player purchases access to a character, not direct victory.

Final monetization decisions should occur only after the base game, economy, progression, and competitive structure are fully understood.

---

# Phase 8: Competitive Systems

Competitive systems are optional layers above the complete offline game.

They should not determine the architecture of ordinary single-player gameplay.

## Leaderboards

Potential leaderboard categories include:

- fastest Level 100
- fastest Story completion
- fastest Dungeoneering world completion
- fastest fixed-seed completion
- deepest extraction
- highest-value extraction
- least-turn completion
- Drifter-specific records
- Legacy Team records
- Fresh Random Start records
- hardcore records
- no-failure records

## Seeded Competition

Seeded competition provides controlled fairness.

```text
same engine version
+
same content version
+
same generation version
+
same seed
=
same underlying challenge
```

Daily and weekly challenges may define:

- fixed World Seed
- fixed starting Drifter
- fixed entry rules
- fixed difficulty modifiers
- limited attempts
- global rankings

## Run Verification

A trustworthy leaderboard should not simply accept a number from the client.

A submission may include:

- engine version
- content version
- generation version
- seed
- initial-state identity
- ordered command log
- timing data
- final state
- result signature

A verification service can replay the deterministic run and confirm the outcome.

This also enables:

- run replays
- ghost comparisons
- turn-by-turn analysis
- tournament review
- anti-cheat verification

## PvP

Possible future PvP forms include:

### Asynchronous PvP

Players submit:

- Drifter team
- builds
- equipment
- tactical behavior settings

Other players challenge a locally reconstructed or server-verified team.

Advantages:

- lower server cost
- no live disconnect pressure
- mobile-friendly sessions
- replayable defenses
- easier scheduling

### Live Turn-Based PvP

Players directly command Drifter teams against one another.

This has a higher competitive ceiling but requires:

- authoritative networking
- matchmaking
- reconnect handling
- turn timers
- version control
- rating systems
- anti-cheat
- balance governance

Live PvP should be considered only after the single-player engine and deterministic command model are mature.

---

# Phase 9: Future C++ Native Engine Core

## Objective

After the Python engine is complete, streamlined, and behaviorally locked, evaluate a portable C++ production core.

## Reason for C++

Performance alone is not the main reason.

Dungeon Drifters is turn-based, and Python is likely fast enough for ordinary gameplay.

The primary benefits would be:

- one portable native engine
- local Android execution
- PC support
- possible console support
- native packaging
- strong cross-platform boundaries
- long-term production stability
- reduced dependence on embedded Python runtimes
- compatibility with multiple graphical technologies

## Proposed Structure

```text
Dungeon Drifters C++ Core
├── commands
├── state
├── combat
├── progression
├── loot
├── recruitment
├── dungeon generation
├── extraction
├── world progression
├── persistence
├── validation
└── semantic results
```

Clients:

```text
Python Terminal Client
-> Python bindings to C++ core

Android Client
-> Kotlin interface to local C++ core

PC Client
-> native or engine-specific adapter to C++ core

Possible Console Client
-> platform adapter to C++ core
```

## Android Structure

The preferred Android structure is:

```text
Kotlin and Jetpack Compose
-> screens, input, animation, accessibility, Android integration

C++ core
-> game rules, state, generation, persistence semantics
```

The C++ engine is bundled inside the application.

Android gameplay does not require a remote server.

## PC and Console Potential

A portable C++ core could support graphical clients built through technologies such as:

- SDL
- Unreal integration
- Godot native extensions
- a custom native desktop client
- platform-specific console shells

C++ does not automatically guarantee console release.

Console development still requires platform agreements, SDK access, certification, platform integration, and production resources.

The C++ core would make the engine technically portable enough for those clients to become realistic options.

## Narrow Interoperability Boundary

Do not expose hundreds of C++ classes directly across Kotlin, Python, or platform boundaries.

Prefer a narrow interface:

```text
create engine
dispatch command
query structured view
create save document
load save document
destroy engine
```

Cross-language calls should happen at meaningful transaction boundaries.

A turn-based game can afford structured serialization at this boundary.

Clarity and testability matter more than micro-optimizing every call.

## Conversion Order

Do not translate the current Python repository file by file.

That would preserve current complexity in a more expensive language.

The correct sequence is:

```text
1. Complete the Python engine.

2. Streamline content and public workflows.

3. Establish the command, result, event, view, and persistence contracts.

4. Lock deterministic behavioral fixtures.

5. Implement one narrow C++ vertical slice.

6. Run Python and C++ against identical fixtures.

7. Expand C++ incrementally.

8. Replace Python engine responsibilities only after exact parity.

9. Preserve Python tooling and reference behavior where useful.
```

## First C++ Proof

The first proof should be intentionally small.

Example:

```text
create one Drifter
create one enemy
resolve one encounter
award deterministic rewards
produce structured events
serialize state
reconstruct state
match Python output exactly
```

Only after that vertical slice succeeds should the C++ scope expand.

---

# Phase 10: Shared Portable Contracts and Content

The strongest long-term design avoids duplicating ordinary content across Python, C++, and Kotlin.

Where practical, portable definitions should be language neutral or generated from one source.

Potential shared contracts include:

- commands
- semantic events
- view records
- save schemas
- content schemas
- validation rules
- engine error codes
- generation records
- replay records

Conceptually:

```text
one authoritative contract
-> generate Python representation
-> generate C++ representation
-> generate Kotlin representation
-> generate serialization support
-> generate fixture skeletons
```

Built-in game content may remain authored through typed Python specifications during early development.

Before C++ conversion, the project should evaluate whether finalized content is best represented through:

- generated portable documents
- compiled content bundles
- schema-validated JSON
- another deterministic shared format

Do not create a general modding or plugin framework unless the product explicitly requires one.

The immediate goal is internal portability and reliable authoring.

---

# Phase 11: Automated Diff-Driven Port Assistance

## Objective

Build a Dungeon Drifters-aware tool that assists with synchronizing Python engine changes into the C++ engine.

This should not be marketed internally as a universal Python-to-C++ transpiler.

The tool understands Dungeon Drifters contracts, content formats, state rules, and testing expectations.

## Core Principle

```text
Do not translate changed lines mechanically.

Interpret the semantic change represented by the diff.
```

## Proposed Workflow

```text
Python engine commit
-> Git diff
-> changed-symbol analysis
-> semantic classification
-> shared-contract regeneration
-> C++ patch candidate
-> C++ compilation
-> cross-engine parity fixtures
-> human review
```

## Analysis Layers

The tool should use:

```text
Git diff
-> defines the change boundary

Python AST
-> identifies changed functions, classes, fields, and expressions

Portable contracts
-> identify schema and content changes

C++ syntax model
-> identifies corresponding native symbols

Behavioral fixtures
-> prove whether the result is actually correct
```

The Git diff is the trigger.

It is not sufficient evidence by itself.

## Change Categories

Every changed area should be classified into categories such as:

```text
SHARED_CONTENT
ENGINE_CONTRACT
ENGINE_LOGIC
PERSISTENCE_SCHEMA
GENERATION_RULE
TEST_FIXTURE
PYTHON_PRESENTATION
PYTHON_TOOLING
PLATFORM_SPECIFIC
UNSUPPORTED
```

## Automated Policies

```text
SHARED_CONTENT
-> validate or regenerate
-> no manual C++ translation when both engines consume the same content

ENGINE_CONTRACT
-> regenerate Python, C++, and Kotlin records where supported

ENGINE_LOGIC
-> produce a reviewed C++ patch candidate

PERSISTENCE_SCHEMA
-> regenerate structures and produce a migration checklist

GENERATION_RULE
-> generate native rule changes only when the pattern is supported
-> rerun deterministic seed fixtures

TEST_FIXTURE
-> execute against both engines

PYTHON_PRESENTATION
-> no C++ engine change

PYTHON_TOOLING
-> no production-engine change unless explicitly mapped

PLATFORM_SPECIFIC
-> route to the relevant client

UNSUPPORTED
-> stop and require manual implementation
```

## Highly Automatable Changes

Likely high-confidence areas:

- ordinary content additions
- reward value changes
- stat changes
- new validated records
- command definitions
- event definitions
- view-model definitions
- serialization field generation
- simple schema structure
- deterministic fixture generation
- stable enum additions

## Assisted Changes

Potentially automatable with mandatory review:

- simple formulas
- deterministic conditional logic
- resource-cost changes
- threshold changes
- small state transitions
- simple validation additions
- known generation-rule patterns

## Manual Stop Conditions

The tool should refuse to silently translate:

- ownership redesigns
- lifecycle changes
- concurrency
- memory-management changes
- major polymorphism changes
- new resource architectures
- new targeting models
- major combat-resolution redesigns
- JNI or platform integration
- new networking models
- unsupported persistence migrations

A clear refusal is better than a convincing incorrect patch.

## Parity as Acceptance Authority

A generated C++ patch is not accepted because it compiles.

It is accepted because Python and C++ produce the same observable behavior.

Parity comparison should include:

- resulting state
- semantic events
- available actions
- validation failures
- resource changes
- damage and rounding
- rewards
- route progression
- generated dungeon output
- save output
- reconstruction
- extraction settlement
- session isolation

## Python as Reference Laboratory

The long-term workflow may become:

```text
prototype feature in Python
-> prove it with tests and fixtures
-> classify the semantic diff
-> regenerate shared contracts
-> generate or assist with C++ implementation
-> run both engines against identical fixtures
-> reject behavioral drift
-> review and merge
```

This preserves Python's development speed while allowing C++ to become the production engine.

---

# Phase 12: Client Expansion

## Android

Android should be the first major graphical portability target if product priorities remain the same.

It should provide:

- fully local gameplay
- touch-first controls
- graphical combat presentation
- local saves
- controller support where practical
- offline Story Mode
- offline Dungeoneering
- optional online leaderboards and account services

## PC

A PC client could expand presentation through:

- keyboard and controller support
- richer visuals
- larger battlefield presentation
- higher-resolution artwork
- deeper UI density
- Steam integration
- challenge leaderboards
- replay viewing
- mod support only if deliberately planned later

## Console

Console becomes a possible future business direction after:

- the native engine is stable
- the PC or Android graphical client proves the presentation
- controls are fully gamepad-compatible
- save and suspend behavior are reliable
- certification requirements are understood
- platform access is secured

Console support is a ceiling enabled by the architecture, not an immediate commitment.

---

# Long-Term Milestone Sequence

The eventual work should follow this dependency order.

## Stage 1: Complete the Python Game

```text
Primary extraction loop
Dungeon exploration
Loot
Recruitment
Run settlement
Persistent progression
World progression
Complete Save/Load
Major content systems
```

## Stage 2: Streamline the Python Architecture

```text
Audit extension seams
Define public authoring paths
Flatten common content workflows
Add validators and scaffolders
Migrate existing content
Prove zero behavioral drift
```

## Stage 3: Build Procedural Dungeon Generation

```text
Dungeon grammar
Dungeon graph
Seed hierarchy
Generator validation
Save persistence
Large-seed simulation
```

## Stage 4: Establish Story and Dungeoneering

```text
Main Seed campaign authority
Story completion unlock
World Seed generation
Legacy-team entry
Fresh random-Drifter entry
Isolated world economy
Local recruitment
```

## Stage 5: Formalize the Engine API

```text
Commands
Results
Semantic events
View records
Deterministic replay
Platform boundaries
```

## Stage 6: Lock Portable Behavioral Fixtures

```text
Combat
Progression
Loot
Recruitment
Dungeon generation
Extraction
Persistence
World settlement
Complete representative runs
```

## Stage 7: Evaluate and Prove C++

```text
Small C++ vertical slice
Python bindings
Android interoperability proof
Cross-engine parity
Build and packaging proof
```

## Stage 8: Build Diff-Driven Port Assistance

```text
Diff classifier
AST analysis
Contract generation
C++ patch generation
Parity runner
Manual stop conditions
```

## Stage 9: Expand the Native Core

```text
Incremental system migration
Continuous parity
No file-by-file blind translation
Python reference retained
```

## Stage 10: Build Production Clients

```text
Android
PC
possible console
optional online competitive services
```

---

# Required Architectural Acceptance Rules

The long-term effort succeeds only if the following remain true.

## Local Gameplay

- Story Mode works offline.
- Dungeoneering works offline.
- combat resolves locally.
- dungeon generation works locally.
- saves work locally.
- presentation does not require a remote response.

## Authority

- the engine owns rules.
- clients own presentation.
- authored content does not own runtime state.
- saves do not own authored definitions.
- seeds do not bypass validation.
- servers do not become mandatory for ordinary play.

## Determinism

- identical versioned inputs produce identical outcomes.
- seed derivation is explicit.
- generated dungeons remain stable after save and load.
- competitive submissions can be replayed.
- Python and C++ can be compared through shared fixtures.

## Economy Isolation

- Story gold remains in Story.
- each Dungeoneering world owns its gold.
- active-run loot remains at risk until extraction.
- account ownership does not become universal instance wealth.
- paid Drifters do not bypass core progression or create direct competitive superiority.

## Streamlining

- common development tasks have one obvious path.
- public extension contracts are documented.
- validators fail clearly.
- old paths are removed only after migration.
- architecture remains layered without forcing ordinary contributors to trace every layer.

---

# Final Direction

Dungeon Drifters should continue using Python to discover and complete the game.

The immediate mission is still to build the actual Dungeon Drifters engine, especially the primary extraction loop.

The long-term evolution is:

```text
complete Python engine
-> streamlined content and architecture
-> procedural dungeon grammar
-> Main Seed Story Mode
-> World Seed Dungeoneering
-> isolated world economies
-> local recruitment and extraction
-> formal engine command API
-> portable behavioral fixtures
-> optional C++ production core
-> automated diff-driven port assistance
-> Android, PC, and possible console clients
```

The central product structure is:

```text
Story Mode gives Dungeon Drifters its canon.

Dungeoneering gives Dungeon Drifters its longevity.

Python discovers the complete engine.

C++ may eventually carry that engine across platforms.

The clients display the game.

The engine remains the game.
```
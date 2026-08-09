# Dungeon Drifters Change Log

## v0.3

v0.3 completes and hardens the single-Drifter surface campaign:

- verified all four Drifters through the complete authored Goblin route
- proved persistent ownership across combat, overworld menus, Rest, and retry
- proved encounter-local cleanup and exact multi-enemy identity isolation
- proved complete progression to Level 9, 68 EXP, 24 Growth Points, and 75 gold
- proved save, exit, load, and continuation through the remaining route
- preserved canonical equipment, inventory, run state, and prepared payloads
- verified inactive final Battle views and truthful overworld presentation
- ends after the Goblin Lord at the passive Dungeon Entrance endpoint
- does not enter the dungeon or introduce companions or party state

## v0.2.10

v0.2.10 completes the M10 surface-route session:

- added the persistent overworld session and authored twelve-node route shell
- added eight authored encounters and deterministic enemy compositions
- added one-to-four enemy Battle orchestration with stable target identity,
  ordered enemy phases, exact targeting, suppression, cleanup, and inactive
  final views
- added route-aware Map encounter inspection without creating runtime enemies
- added signature-weapon inspection and narrow equipment presentation
- added atomic encounter EXP and gold rewards, nonlinear progression to the
  Level 250 cap, carryover EXP, and controlled permanent-stat growth
- added three authored Rest nodes with full HP/Mana recovery or route skip
- added schema-8 atomic disk save/load with schema-7 migration, validation,
  invalid-save recovery, and startup Load/New Game selection
- preserved schema-7 inspection snapshots and excluded Battle/UI runtime state
  from disk persistence

## v0.2.9

v0.2.9 completes the M9 UI/engine separation milestone:

- added a controlling UI/engine separation plan in
  `docs/m9-ui-engine-separation.md`
- added immutable renderer-neutral battle presentation models
- added a pure `BattlePresenter` and bounded structured battle log session
- replaced raw Battle menu input with typed semantic action, move, and Back
  intents
- moved terminal rendering and input handling into a stateless
  `TerminalBattleUI`
- kept Battle responsible for orchestration, resolver calls, accepted-action
  completion, and victory/defeat flow
- added the persistent Super meter and five-option ordinary action hierarchy
  with disabled Items and Escape states
- restored universal Heal as a resolver-backed self-heal with a three-action
  cooldown, without adding healing moves to character loadouts
- added structured move roles, affinities, summaries, and dynamic Brace and
  Ironwake presentation without consuming combat state
- verified all four Drifters through resolver compatibility tests and
  deterministic Goblin vertical slices
- removed the obsolete private Battle menu bridge after the UI migration
- completed the four Drifter identity pass with encounter-local mechanics for
  Brace, Gravemantle, Frost, Infused Barb, Burn, Poison, Conductive,
  Turbulence, Lightning Storm, Stun, and universal Heal
- added the deterministic M9 balance snapshot tool with fixed 25-seed Goblin,
  100-seed stress, eight-route, and natural Super-usage coverage

## v0.2.8.5

v0.2.8.5 adds the first post-M8 stat-scaling pass and targeted hardening:

- added the central `app.player.scaling` contract for all six permanent stats
- moved authored starting Level 1 stat distributions into player loadout modules
- derived player HP from Constitution and player Mana from Spirit, including
  level-based resource growth through explicit recalculation
- replaced raw additive damage scaling with basis-point output scaling for
  Strength, Dexterity, and Intelligence
- wired Strength physical negation into incoming physical damage
- wired Dexterity accuracy and dodge into ordinary hit chance
- wired Intuition Super gain scaling into landed non-Super damage hits
- wired Intuition crit chance into landed damage moves and surfaced crit state
  through `MoveResult`
- updated Battle rendering to visibly show critical hits
- added resolver compatibility coverage proving all four authored Drifter
  structured move rosters enter the resolver path successfully
- completed an M8 hardening audit across combat, player, enemy, snapshot, and
  progression boundaries without changing move data, enemy data, or Battle flow

## v0.2.8

v0.2.8 completes the Milestone 8 structured Goblin Battle integration:

- rewired player-selected structured moves through `CombatResolver`
- rewired ordinary Goblin enemy actions through authored structured moves
- added structured Attack and Super submenus to the terminal Battle flow
- integrated Defend as a core resolver-backed action
- routed accepted action completion through `CombatState`
- rendered Battle output from `MoveResult` values
- expanded the terminal HUD to show HP, Mana, Super, Defend, and relevant
  temporary combat state
- removed legacy Battle-owned attack, recovery, miss, damage, and universal
  enemy-healing helpers
- verified the Goblin vertical slice from character selection through victory
  using structured moves and resolver-backed combat

## v0.2.7

v0.2.7 adds the standalone Milestone 7 combat resolver and related pre-M8
contracts:

- added `CombatResolver` for canonical actor-owned structured moves
- added deterministic accuracy, scaling, mitigation, damage, and healing rules
- added Mana and persistent Super spending/generation in resolver flow
- added enemy archetype, rank, role, behavior, capability, and tier metadata
- corrected the ordinary Goblin to a two-move common `BASIC_ATTACKS` roster
  with 0 Mana
- moved enemy definitions, runtime state, registration, factory, scaling, and
  authored Goblin content into `app.enemies`
- added the core Defend contract for resolver-level damage reduction and
  temporary encounter-owned defending state
- completed the current structured Branoc, Azhvielle, and Zhaivra active
  rosters as four standard attacks plus one Super each
- preserved unsupported character-specific effects as deferred comments instead
  of active mechanic tags
- kept the interactive `Battle` loop on the legacy path for Milestone 8
- documented that complete structured Battle playability still depends on M8
  integration and remaining character-kit/mechanic work

## v0.2.5

v0.2.5 is the architecture checkpoint currently merged through Milestone 6:

- added canonical Drifter profiles and profile-attached character identity
- added compact character selection and profile confirmation flow
- added console screen transitions
- added `GameState`, `StoryState`, and `WorldState`
- added serializable `PlayerState` and `GameState` snapshots
- separated character loadout definitions from runtime state
- migrated to six permanent stats
- added validated resource and stat mutation boundaries
- added shared `Combatant` protocol
- added `EnemyState` and moved enemy runtime HP out of Battle-owned integers
- normalized enemy moves as structured `Move` definitions
- added validated `Move` and `MoveResult` contracts
- clarified active move resources as `None`, `Mana`, and `Super`
- preserved the v0.1 vertical slice while preparing for later resolver work

## v0.2

v0.2 added the first persistent state foundation:

- refactored the project into domain packages
- added structured move data for playable classes
- implemented `Health`, `Mana`, `Level`, `Exp`, and stat objects
- preserved legacy `Character` attributes through compatibility properties
- added `PlayerState` for selected character, gold, inventory, and equipment
- created `PlayerState` in the main flow
- changed `Battle` to receive player runtime state
- moved player HP mutation into persistent `PlayerState.health`
- added `CombatState` as temporary per-battle state

## v0.1

v0.1 established the first complete playable slice:

- restored a clean root launcher
- fixed character selection
- fixed story execution order
- connected story choices to battle or escape
- added deterministic smoke coverage for attack and flee paths
- kept the first playable loop focused on one Goblin encounter

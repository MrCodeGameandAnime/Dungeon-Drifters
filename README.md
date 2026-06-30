# Dungeon Drifters

Dungeon Drifters is a text-based Python RPG prototype set in the land of Ketlyv.

The current repository checkpoint is **v0.2.5**. This is an architecture
checkpoint between **v0.2** and the unfinished **v0.3** release. The small
**v0.1 vertical slice** remains the playable baseline while the project builds
the state, move, enemy, and combat contracts needed for later gameplay work.

## Current Playable State

The playable flow is intentionally small:

```text
title screen
  -> Drifter selection
  -> opening story
  -> attack or flee
  -> Goblin encounter or escape
  -> victory or defeat ending
```

Current Drifter selection uses canonical profile identity layered over the
existing mechanical archetypes:

- Ser Branoc, the Unbroken Crest - Brawler
- Azhvielle, the Unconfessed - Black Mage
- Zhaivra Kelyth, the Uncontrolled Reagent - Rogue Archer
- Joruun Veyr, the Bloody Storm Monk - Monk

Battle is still on the legacy playable path. It presents:

- quick move
- power move
- Recover

Structured move definitions exist, but the current battle loop has not been
rewired to a full structured resolver yet.

## Play Instructions

From the project root, run:

```powershell
.\.venv\Scripts\python.exe run_game.py
```

You can also run `run_game.py` directly from PyCharm.

During play:

1. Press Enter past the title screen.
2. Choose a Drifter.
3. Confirm or return to selection.
4. Read the opening story.
5. Choose to attack or flee.
6. If combat starts, choose a quick move, power move, or Recover.

## Implemented Architecture

The repository now includes these active foundations:

- `GameState` as the session root for one active run.
- `PlayerState`, `StoryState`, and `WorldState` ownership boundaries.
- Separated character runtime state, loadout definitions, and profile identity.
- Canonical character profiles for the four current Drifters.
- Per-character loadout modules for legacy move names, structured moves, and
  identity metadata.
- Health, mana, level, EXP, permanent stats, and effective stat access.
- Inventory, gold, and equipment slot state on `PlayerState`.
- Immutable validated `Move` definitions.
- Immutable validated `MoveResult` as the future resolution-result contract.
- Shared `Combatant` protocol for player and enemy runtime state.
- Runtime `EnemyState` with independent health, mana, stats, and structured
  enemy moves.
- Battle using combat-facing player and enemy runtime state while preserving
  the current legacy menu flow.
- Serializable `PlayerState` and `GameState` snapshots.
- Defensive copies or immutable views for state collections where currently
  implemented.

These systems are architecture and contract foundations. They are not all fully
wired into final gameplay yet.

## Resource Terminology

The active `Move` resource categories are:

- `None`
- `Mana`
- `Super`

Momentum is deferred shared encounter state. It is not an active move resource.

Ki may appear as Joruun identity or technique flavor. It is not an active
resource state.

Focus, ammunition, compounds, prepared charges, Momentum, Ki meters, and other
character-specific resource systems are not implemented as active resources.

## Test Instructions

Install development dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Run the full pytest suite:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Run a compile check:

```powershell
.\.venv\Scripts\python.exe -m compileall app tests run_game.py
```

## Project Structure

```text
app/
  game/
    main_loop.py       Current game flow
    game_state.py      Session root
    story_state.py     Persistent story state
    world_state.py     Persistent world state
    console.py         Console pause/clear helpers

  player/
    character.py       Runtime character composition and archetype constructors
    player_state.py    Persistent player aggregate
    resources.py       Health and mana resource objects
    progression.py     Level and EXP objects
    stats.py           Permanent and effective stat layers
    inventory.py       Player-owned item container
    loadouts/          Drifter move and mechanic definitions

  combat/
    battle.py          Current legacy battle loop
    combatant.py       Shared combat-facing protocol
    combat_state.py    Temporary per-battle state
    enemy.py           Enemy definitions
    enemy_state.py     Runtime enemy state
    move.py            Validated structured Move contract
    result.py          Validated MoveResult contract

  world/
    story.py           Title, story text, and endings
    event.py           Character selection and event rolls
    character_profiles/
      profile.py       Profile data and rendering
      roster.py        Canonical Drifter roster

  items/
    weapon.py          Weapon classes

  snapshot.py          Strict plain-value snapshot helpers

tests/
  Direct-run regression tests for state, profiles, loadouts, combat contracts,
  snapshots, Battle behavior, and the vertical slice.

docs/
  v0.3-combat-design-reference.md
  character-growth-progression.md
  dungeon-extraction-economy.md
  signature-weapon-progression.md
  momentum.md

run_game.py            Project-root launcher
```

## Change Summary

### v0.1

v0.1 established the first complete playable slice:

- restored a clean root launcher
- fixed character selection
- fixed story execution order
- connected story choices to battle or escape
- added deterministic smoke coverage for attack and flee paths
- kept the first playable loop focused on one Goblin encounter

### v0.2

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

### v0.2.5

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

## Known Limitations

- Structured move resolver integration is not implemented.
- Battle still uses the legacy quick move, power move, and Recover flow.
- Final character kits are not complete.
- Exact combat formulas and balance are provisional.
- Super behavior and generation are not implemented.
- Momentum implementation is deferred.
- Ammunition, compounds, and prepared-charge systems are not implemented.
- Status effects and elemental interactions are not active.
- Equipment exists as state but does not provide bonuses.
- Broader encounters, progression gameplay, shops, extraction, and save/load are
  future work.

## Development Notes

- Use the project virtual environment at `.venv`.
- Use `.\.venv\Scripts\python.exe` for commands.
- Pytest is the canonical test runner.

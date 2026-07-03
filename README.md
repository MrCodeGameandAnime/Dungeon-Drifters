# Dungeon Drifters

Dungeon Drifters is a text-based Python RPG prototype set in the land of Ketlyv.

The current repository checkpoint is **v0.2.7**. This is an architecture
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
.\.venv\Scripts\python.exe src\run_game.py
```

You can also run `src/run_game.py` directly from PyCharm.

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
- Enemy archetype metadata for rank, role, behavior, capabilities, and tier.
- `app.combat` contains reusable combat rules and contracts; `app.enemies`
  contains enemy definitions, runtime state, registration, scaling, factory, and
  authored enemy content.
- Core Defend contract in the standalone resolver and encounter-owned
  `CombatState`, with Battle integration deferred.
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
.\.venv\Scripts\python.exe -m compileall src tests
```

## Project Structure

```text
Dungeon-Drifters/
+-- .github/
|   +-- workflows/
|       +-- tests.yml
+-- src/
|   +-- app/
|   |   +-- combat/
|   |   +-- enemies/
|   |   +-- game/
|   |   +-- items/
|   |   +-- player/
|   |   +-- world/
|   +-- run_game.py
+-- tests/
+-- docs/
+-- README.md
+-- .gitignore
+-- pytest.ini
+-- requirements-dev.txt
```

The complete runnable game is contained under `src/`. Tests, documentation,
GitHub Actions, and development configuration remain outside the distributable
game directory.

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

### v0.2.7

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

## Known Limitations

- Structured move resolver integration into Battle is not implemented.
- Battle still uses the legacy quick move, power move, and Recover flow.
- Battle still has temporary universal enemy low-HP healing; authored enemy
  healing capability should replace this in Milestone 8.
- Defend exists only in the standalone resolver/CombatState contract until
  Battle is rewired in Milestone 8.
- Joruun's full structured combat identity and specialized mechanics remain
  deferred.
- Exact combat formulas and balance are provisional.
- Super behavior and generation are implemented only in the standalone resolver.
- Momentum implementation is deferred.
- Ammunition, compounds, and prepared-charge systems are not implemented.
- Status effects and elemental interactions are not active.
- Equipment contributes through `effective_stat()` where implemented.
- Broader encounters, progression gameplay, shops, extraction, and save/load are
  future work.

## Development Notes

- Use the project virtual environment at `.venv`.
- Use `.\.venv\Scripts\python.exe` for commands.
- Pytest is the canonical test runner.

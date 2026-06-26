# Dungeon Drifters

Dungeon Drifters is a text-based Python RPG prototype set in the land of Ketlyv.

The current project version is **v0.2**. The game still preserves the **v0.1
vertical slice** as its playable baseline, while the underlying architecture now
has persistent player state and temporary combat-state boundaries ready for later
class mechanics and richer combat.

## Current Playable State

The playable flow is still intentionally small:

```text
title screen
  -> choose a character
  -> opening story
  -> attack or flee
  -> goblin battle or escape ending
  -> victory/defeat ending
```

Current gameplay includes:

- four playable classes: Brawler, Black Mage, Rogue Archer, and Monk
- structured class move data and class mechanic metadata
- one active story encounter
- flee chance
- turn-based goblin combat
- persistent player health during battle
- victory, defeat, and escape endings

Some systems exist architecturally but are not fully wired into gameplay yet:

- inventory
- gold
- equipment slots
- mana spending
- structured move resolution
- class mechanics
- temporary combat effects

## Play Instructions

From the project root, run:

```powershell
.\.venv\Scripts\python.exe run_game.py
```

You can also run `run_game.py` directly from PyCharm.

During play:

1. Choose one of the four classes.
2. Read the opening story.
3. Choose to attack or flee.
4. If combat starts, choose a steady attack, heavy attack, or Recover.

## Test Instructions

Run the vertical-slice smoke test:

```powershell
.\.venv\Scripts\python.exe tests\smoke_test_vertical_slice.py
```

Expected output:

```text
Vertical slice smoke test passed.
```

Run the current direct-run test suite:

```powershell
.\.venv\Scripts\python.exe tests\test_inventory.py
.\.venv\Scripts\python.exe tests\test_player_state.py
.\.venv\Scripts\python.exe tests\test_main_flow_player_state.py
.\.venv\Scripts\python.exe tests\test_battle_player_state.py
.\.venv\Scripts\python.exe tests\test_combat_state.py
.\.venv\Scripts\python.exe tests\test_character_move_data.py
.\.venv\Scripts\python.exe tests\test_character_state.py
```

Run a compile check:

```powershell
.\.venv\Scripts\python.exe -m compileall app tests run_game.py
```

## Project Structure

```text
app/
  game/
    main_loop.py      Main game flow
    game_state.py     Placeholder for future game-level state

  player/
    character.py      Playable classes, moves, resources, stats, EXP/level
    player_state.py   Persistent playthrough player state
    inventory.py      Player-owned item container

  combat/
    battle.py         Turn-based combat
    enemy.py          Enemy classes
    combat_state.py   Temporary per-battle state

  world/
    story.py          Title, story text, and endings
    event.py          Character selection and event rolls
    npc.py            Placeholder NPC module

  items/
    weapon.py         Weapon classes

tests/
  smoke_test_vertical_slice.py
  test_battle_player_state.py
  test_character_move_data.py
  test_character_state.py
  test_combat_state.py
  test_inventory.py
  test_main_flow_player_state.py
  test_player_state.py

run_game.py           Project-root launcher
```

## v0.1 To v0.2 Change Log Summary

v0.1 established the first complete playable slice:

- restored a clean root launcher
- fixed character selection
- fixed story execution order
- connected story choices to battle or escape
- added deterministic smoke coverage for attack and flee paths
- kept the first playable loop focused on one goblin encounter

v0.2 adds the foundation for persistent player state:

- refactored the project into domain packages
- added structured immutable move data for playable classes
- added class mechanic metadata for each class
- implemented `Health`, `Mana`, `Level`, `Exp`, and `Stats`
- preserved legacy `Character` attributes through compatibility properties
- added `PlayerState` for selected character, gold, inventory, and equipment
- added `Inventory` with safe per-instance item storage
- created `PlayerState` in the main flow
- changed `Battle` to accept `PlayerState`
- moved player HP mutation into persistent `PlayerState.health`
- added `CombatState` as temporary per-battle state
- added direct-run tests for player state, inventory, combat state, battle state,
  character state, move data, and the playable vertical slice

## Known Limitations

- Combat still uses generic steady/heavy attacks instead of full structured move
  resolution.
- Mana exists but is not spent during battle yet.
- Class mechanics exist as metadata but are not active combat systems yet.
- Equipment exists as state but does not grant bonuses or enforce item slots yet.
- Enemy HP is still battle-local.
- `CombatState` tracks turn count and placeholder containers, but statuses,
  buffs, debuffs, and defending are not active gameplay yet.
- GitHub Issue #2 for the cosmetic healing-display bug remains intentionally
  separate.

## Development Notes

- Use the project virtual environment at `.venv`.
- Use `.\.venv\Scripts\python.exe` for commands.

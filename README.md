# Dungeon Drifters

Dungeon Drifters is a text-based Python RPG prototype set in the land of Ketlyv.
The current build is a playable vertical slice: title screen, character selection,
opening story, flee/attack choice, goblin battle, and ending.

## Current Playable Flow

```text
title screen
  -> choose a character
  -> opening story
  -> attack or flee
  -> goblin battle or escape ending
  -> victory/defeat ending
```

## Run The Game

From the project root:

```powershell
.\.venv\Scripts\python.exe run_game.py
```

You can also run `run_game.py` directly from PyCharm.

## Run The Smoke Test

The smoke test verifies the current vertical slice, including the attack path and
the flee path.

```powershell
.\.venv\Scripts\python.exe tests\smoke_test_vertical_slice.py
```

Expected output:

```text
Vertical slice smoke test passed.
```

## Project Structure

```text
app/
  battle.py       Turn-based combat
  character.py    Playable character classes
  enemy.py        Enemy classes
  event.py        Character selection and event rolls
  main_loop.py    Main game flow
  story.py        Title, story text, and endings
  weapon.py       Weapon classes

tests/
  smoke_test_vertical_slice.py

run_game.py       Project-root launcher
```

## Development Notes

- Use the project virtual environment at `.venv`.
- Keep playable source code in `app/`.
- `backup/`, IDE files, caches, and generated output are ignored by Git.
- The next major improvement should connect stats, mana, weapons, and class
  moves more deeply into combat.

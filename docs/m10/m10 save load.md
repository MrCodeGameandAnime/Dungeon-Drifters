# M10 Save and Load Contract

## Save Location

M10 uses one manual save file:

```text
src/saves/dungeon_drifters.json
```

The `saves` directory is next to `src/run_game.py`. The directory is created
when the first save is requested. M10 does not provide save slots, cloud
saves, autosave, or configurable save locations.

## Safe Save Boundary

Saving is allowed only between battles at an overworld node. A save cannot be
created during:

- an active Battle
- enemy or player action resolution
- an open combat menu
- a transition between actions

The save captures the persistent session after the current encounter has
completed and before the next encounter begins.

Writes must be atomic: write the complete JSON document to a temporary file in
the same `saves` directory, then replace the target save file only after the
write and validation succeed. A failed write must not destroy the previous
valid save.

## Missing Save

If the save file does not exist, Load behaves like there is no saved session:

```text
opening flow
-> normal character/session creation
```

Missing-save handling is not an error and does not create a placeholder save.

## Invalid Save

If the save file exists but cannot be read, parsed, validated, or reconstructed:

1. Preserve the invalid file unchanged.
2. Report a concise player-facing load error.
3. Do not partially mutate the current session.
4. Return to the normal new-game opening flow.

An invalid save must never silently become a partially loaded session and must
not crash the process.

## Disk Schema

The current in-memory inspection snapshot remains schema `7`.

M10 disk saves use schema `8` because they add the persistent route boundary,
completed encounter identifiers, rest state, and other session fields needed
to resume the overworld campaign.

Schema 7 saves remain loadable through a deterministic migration. Missing M10
fields receive safe initial values:

- route position starts at the opening route node
- completed encounters are empty
- rest state is unset
- existing player, story, world, equipment, inventory, and resource fields are
  preserved

The migrated session is represented and written back as schema `8` only after
the user successfully saves it again. Unsupported future schema versions are
rejected as invalid saves.

## Persistence Boundary

The save includes only serializable persistent session state:

- selected character/profile identity
- PlayerState progression and current resources
- equipment and inventory
- run inventory and prepared Infusion state
- gold
- route position
- completed encounter identifiers
- rest state
- StoryState and WorldState

The save excludes:

- active Battle objects
- CombatState and temporary statuses
- resolver objects
- Battle UI and presenter models
- open menu phases
- RNG objects
- runtime enemy objects
- object identity references

## M10 Gate

The Save/Load gate passes when a player can:

```text
reach an overworld boundary
-> save
-> exit
-> start the game
-> load
-> restore persistent state
-> continue into the next encounter
```

The loaded session must not duplicate rewards, restore temporary combat state,
or share mutable state with another session.

# Future Plan: Browser-Based Playtesting

Dungeon Drifters should eventually receive a browser-based version for early cross-platform playtesting.

## Goal

Allow players to test the game through a web link on:

* Android
* iPhone
* Windows
* Mac
* Linux
* Tablets
* Chromebooks

This avoids maintaining separate Android, iOS, and desktop builds during early development.

## Proposed Architecture

```text
Dungeon Drifters Engine
├── Combat
├── Characters
├── Enemies
├── Inventory
├── Encounters
├── GameState
├── WorldState
└── StoryState
        ↑
   Browser Interface
        ↑
 HTML, CSS, JavaScript
        ↑
      Pyodide
```

Pyodide would run the existing Python game code directly inside the player's browser.

## Hosting

The browser version can be hosted for free through GitHub Pages.

Example:

```text
mrcodegameandanime.github.io/Dungeon-Drifters/
```

The GitHub Pages deployment would contain:

```text
index.html
styles.css
game_ui.js
game/
    Python game files
```

No separate Python server would be required for the initial version.

## Development Approach

The existing terminal interface should remain available for development, debugging, and automated testing.

```text
Dungeon Drifters Engine
        ├── Terminal UI
        └── Browser UI
```

The browser interface should remain thin and only handle:

1. Displaying the current game state.
2. Presenting available actions.
3. Sending the selected action to the Python engine.
4. Displaying the updated result.

The game engine should not contain browser-specific logic.

## Initial Browser Features

The first browser version only needs:

* Battle text
* Player and enemy health
* Numbered action buttons
* Attack submenu
* Item submenu
* Super submenu
* Return button
* Encounter results
* Dungeon progression
* Restart option

The interface should be designed mobile-first.

## Saving

Early saves can be stored locally in the player's browser.

Possible options:

* Browser local storage
* Downloadable save file
* Copyable save code

Accounts and cloud saves are not required for the first playtest version.

## Limitations

A GitHub Pages version would not initially support:

* User accounts
* Cross-device cloud saves
* Online multiplayer
* Global leaderboards
* Protected server-side logic

These features would require a hosted backend later.

## Recommended Development Order

```text
1. Complete the core Python game engine
2. Complete the terminal combat interface
3. Separate terminal input/output from game logic
4. Add a browser-facing Python interface
5. Build the mobile browser UI
6. Load the Python engine through Pyodide
7. Deploy automatically through GitHub Pages
8. Run private cross-platform playtests
9. Add local saving
10. Consider a hosted backend only when needed
```

## Long-Term Direction

The browser version can later become a Progressive Web App so players can add Dungeon Drifters to their phone home screen and launch it more like a normal application.

Native Android and iPhone builds should only become a priority after the game systems, interface, and player experience have been validated through browser-based playtesting.

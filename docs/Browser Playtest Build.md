# Future Plan: Browser Playtest Build

Dungeon Drifters is currently being developed in Python to establish the core game systems, combat, progression, characters, enemies, and overall gameplay loop.

The long-term goal is still to rebuild the game properly for mobile once the core design is stable and proven.

Before that rebuild begins, a lightweight browser version can be created so friends and early players can try the game through a simple link.

The browser version is not intended to become the final platform. It is a temporary playtest, feedback, and promotional build.

## Purpose

The browser version would allow players to:

* Open the game through a link
* Play on Android, iPhone, tablets, or computers
* Test the current gameplay systems
* Provide early feedback
* Share the project with friends
* Play a short public demo from Reddit or other communities
* Experience Dungeon Drifters without installing Python

The browser build should remain small and easy to maintain.

## Development Direction

```text
Current Python Version
        ↓
Establish the core game
        ↓
Create a simple browser playtest
        ↓
Gather feedback and build interest
        ↓
Complete the Python prototype
        ↓
Rebuild the proven game for mobile
        ↓
Consider additional platform ports later
```

## Proposed Architecture

The existing Python game systems should remain the foundation.

```text
Dungeon Drifters Core Engine
├── Combat
├── Characters
├── Enemies
├── Inventory
├── Encounters
├── Dungeon Progression
├── GameState
├── WorldState
└── StoryState
        ↑
   Flask or FastAPI
        ↑
 Minimal JSON Endpoints
        ↑
 HTML / CSS / JavaScript
```

The browser interface should only display the game state and return player choices.

It should not contain combat calculations, progression rules, enemy logic, or other core systems.

## Example Server Endpoints

The browser build may only need a few routes.

```http
GET /game/state
POST /game/action
POST /game/restart
```

An action request could look like:

```json
{
  "action": "attack",
  "option": "slash"
}
```

The Python engine would process the action and return the updated state.

```json
{
  "player_hp": 82,
  "enemy_hp": 31,
  "message": "Branoc used Slash for 14 damage.",
  "available_actions": [
    "attack",
    "defend",
    "items",
    "super"
  ]
}
```

The JavaScript interface would then redraw the battle screen.

## Interface Requirements

The browser version should be designed to feel like a mobile game rather than a normal website.

It should:

* Play horizontally
* Use the full available screen
* Avoid scrolling
* Use large touch controls
* Hide unnecessary browser-style elements
* Support phones, tablets, and desktop browsers
* Display a rotate-device message when opened vertically
* Request fullscreen after the player enters the game
* Use safe-area spacing for devices with notches or rounded corners

## Opening Flow

```text
Open Game Link
      ↓
Dungeon Drifters Title Screen
      ↓
Tap to Enter Dungeon
      ↓
Request Fullscreen
      ↓
Request Landscape Orientation
      ↓
Load the Game Interface
```

Browsers generally require the player to tap before fullscreen can be activated.

The title screen gives the game a natural place to request fullscreen and begin loading the current game state.

## Title Screen

```text
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│                    DUNGEON DRIFTERS                          │
│                                                              │
│              Enter the dungeon. Survive the drift.           │
│                                                              │
│                    [ ENTER DUNGEON ]                         │
│                                                              │
│                 Best played in landscape                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

The player taps **Enter Dungeon**, the browser requests fullscreen, and the game begins.

## Portrait Orientation Screen

If the player opens the game vertically, the normal interface should be hidden.

```text
┌──────────────────────────────┐
│                              │
│       Rotate Your Device     │
│              ↻               │
│                              │
│ Dungeon Drifters is played   │
│       in landscape mode.     │
│                              │
└──────────────────────────────┘
```

Once the phone is rotated, the game screen becomes visible automatically.

## Main Battle Interface

```text
┌──────────────────────────────────────────────────────────────┐
│ Branoc  HP ███████░░      Dungeon Chamber      Goblin ███░░ │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                 CHARACTER / ENEMY VISUALS                    │
│                                                              │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Branoc strikes the Goblin for 14 damage.                     │
├──────────────────────────────────────────────────────────────┤
│  [ Attack ]    [ Defend ]    [ Items ]    [ Super ]         │
└──────────────────────────────────────────────────────────────┘
```

The screen should be divided into four basic sections:

1. Player and enemy status
2. Character and enemy visuals
3. Battle log
4. Action controls

The entire interface should remain visible without scrolling.

## Attack Menu

Selecting Attack should replace the main action buttons with the available moves.

```text
┌──────────────────────────────────────────────────────────────┐
│ Branoc  HP ███████░░      Dungeon Chamber      Goblin ███░░ │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                 CHARACTER / ENEMY VISUALS                    │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Choose an attack.                                            │
├──────────────────────────────────────────────────────────────┤
│ [ Slash ]  [ Jumping Slash ]  [ Heavy Strike ]  [ Back ]    │
└──────────────────────────────────────────────────────────────┘
```

The Back button returns the player to the main action menu.

## Item Menu

```text
┌──────────────────────────────────────────────────────────────┐
│                           ITEMS                              │
├──────────────────────────────────────────────────────────────┤
│ Healing Flask x2        Restores health                      │
│ Iron Tonic x1           Temporarily increases defense        │
│ Fire Bomb x1            Damages one enemy                     │
├──────────────────────────────────────────────────────────────┤
│ [ Flask ]      [ Tonic ]      [ Fire Bomb ]      [ Back ]    │
└──────────────────────────────────────────────────────────────┘
```

The item screen should only display items currently available to the player.

## Super Menu

```text
┌──────────────────────────────────────────────────────────────┐
│ Branoc  HP ███████░░      SUPER ██████████      Goblin ███░ │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                      SUNDER-SPIRE                            │
│                                                              │
│     Branoc unleashes the full weight of his Great-Flamberge. │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                    [ USE SUPER ]    [ BACK ]                 │
└──────────────────────────────────────────────────────────────┘
```

If the Super meter is not ready, the button should remain visible but disabled.

## Encounter Result Screen

```text
┌──────────────────────────────────────────────────────────────┐
│                         VICTORY                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                   Goblin defeated                            │
│                                                              │
│                   Experience gained: 25                      │
│                   Gold recovered: 14                         │
│                   Item found: Iron Tonic                     │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                    [ CONTINUE DUNGEON ]                      │
└──────────────────────────────────────────────────────────────┘
```

## Demo Completion Screen

The browser playtest should have a clear stopping point.

```text
┌──────────────────────────────────────────────────────────────┐
│                 PLAYTEST COMPLETE                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│            You survived the first dungeon.                   │
│                                                              │
│       Thank you for playing Dungeon Drifters.                │
│                                                              │
│      This is an early prototype of the core game.            │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ [ PLAY AGAIN ]   [ LEAVE FEEDBACK ]   [ FOLLOW DEVELOPMENT ]│
└──────────────────────────────────────────────────────────────┘
```

This gives players somewhere to provide feedback or follow future development.

## Fullscreen Behavior

The game should request fullscreen after the player presses the title-screen button.

```javascript
async function enterGame() {
    const game = document.getElementById("game");

    if (game.requestFullscreen) {
        await game.requestFullscreen();
    }

    if (screen.orientation?.lock) {
        try {
            await screen.orientation.lock("landscape");
        } catch {
            // The player can still rotate the device manually.
        }
    }

    startGame();
}
```

Orientation locking may not work identically across every mobile browser, so the interface should still support manual device rotation.

## Full-Screen Layout

```css
html,
body {
    width: 100%;
    height: 100%;
    margin: 0;
    overflow: hidden;
    background: #000;
}

#game {
    width: 100dvw;
    height: 100dvh;
    box-sizing: border-box;

    padding:
        env(safe-area-inset-top)
        env(safe-area-inset-right)
        env(safe-area-inset-bottom)
        env(safe-area-inset-left);
}
```

The interface should use dynamic viewport units so it adjusts properly when mobile browser controls appear or disappear.

## Portrait Blocking

```css
#rotate-message {
    display: none;
}

@media (orientation: portrait) {
    #game {
        display: none;
    }

    #rotate-message {
        display: flex;
    }
}
```

The portrait screen should fill the display and clearly tell the player to rotate the device.

## Optional Progressive Web App Support

The browser version could later include a small web-app manifest.

```json
{
  "name": "Dungeon Drifters",
  "short_name": "Drifters",
  "start_url": "/",
  "display": "fullscreen",
  "orientation": "landscape",
  "background_color": "#000000"
}
```

This would allow players to add the demo to their phone home screen and launch it in a more app-like window.

This is optional and should not delay the initial browser build.

## Demo Scope

The first public browser demo should remain small.

Possible content:

* One short introduction
* One playable character
* A small set of attacks
* Several normal encounters
* One elite enemy
* One boss
* One small dungeon
* Ten to twenty minutes of gameplay
* One feedback screen

The browser version does not need:

* Accounts
* Cloud saves
* Multiplayer
* Global leaderboards
* Complex web animations
* A full graphical overhaul
* Every character
* Every dungeon
* The entire planned game

## Public Sharing

The browser build can be shared with:

* Friends
* Private testers
* Reddit communities
* Discord communities
* GitHub followers
* Early supporters
* Potential mobile testers

A player should be able to see a post, tap the link, rotate their phone, press **Enter Dungeon**, and begin playing.

```text
Gameplay Clip or Screenshot
             ↓
      Browser Demo Link
             ↓
        Play Immediately
             ↓
     Feedback or Follow
             ↓
 Future Mobile Announcement
```

## Recommended Development Order

```text
1. Complete the core Python game systems
2. Keep the terminal interface for development and testing
3. Separate terminal input and output from game logic
4. Add a minimal Flask or FastAPI server
5. Create basic game-state and action endpoints
6. Build the landscape browser interface
7. Add fullscreen and rotate-device behavior
8. Add the title screen
9. Add battle and submenu interfaces
10. Add the demo completion screen
11. Deploy the playtest build
12. Share it privately
13. Fix major playtest issues
14. Share the demo publicly
15. Continue development toward the eventual mobile rebuild
```

## Long-Term Direction

The browser build should remain a lightweight presentation layer around the Python prototype.

```text
Dungeon Drifters Core Engine
        ├── Terminal Interface
        ├── Browser Playtest Interface
        └── Future Mobile Rebuild
```

Its purpose is to make the current game easy to experience while the real development work continues.

The browser version provides the illusion of a small mobile game, gives players something tangible to try, and creates an easy way to gather feedback and build interest without changing the long-term mobile direction.

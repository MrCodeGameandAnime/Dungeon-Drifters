# Dungeon Drifters: Pyodide + GitHub Pages Browser Playtest Plan

## Status

This plan supersedes the older browser-playtest plans that assumed either a Flask/FastAPI backend or a disposable Python prototype that would later be rewritten for mobile.

Those assumptions no longer match Dungeon Drifters.

DD now has one authoritative Python gameplay implementation, renderer-neutral semantic views and inputs, `Battle.current_view()` / `Battle.submit(...)`, `OverworldSession.current_view()` / `OverworldSession.submit(...)`, canonical new-game construction through `create_new_game(drifter_id)`, a qualified headless surface route, and a closed MPY0-MPY20 portability campaign.

The browser build is therefore a **static GitHub Pages host around the existing Python runtime**, executed in-browser with Pyodide.

---

# 1. Controlling Goal

```text
GitHub Pages
    ↓
HTML / CSS / JavaScript
    ↓
Pinned Pyodide
    ↓
Authoritative DD Python runtime
    ↓
OverworldSession / Battle
    ↓
SessionView / BattleView
    ↓
thin browser projection
    ↓
player choice
    ↓
existing SessionInput / BattleInput
    ↓
submit(...)
    ↓
next authoritative view
```

No Flask. No FastAPI. No gameplay server. No duplicate combat engine. No JavaScript-owned progression rules. No separate browser game state.

---

# 2. Current Baseline

```text
branch: mpy
current head at plan creation:
e31c77e3ccd0628130286d722a270d98deaf4bed
```

MPY20 closure:

```text
44d31c95db9d43c2fe8e5a17dbfbc32edc4100f3
MPY20 - Seal Cross-Runtime Qualification
```

The currently qualified route proves:

```text
8 encounters
3 Rests
8 Battles
14 fresh enemies
Goblin Lord
Dungeon Entrance

final:
Level 9
EXP 68
Growth Points 24
Gold 75
```

Canonical headless browser construction should use the existing runtime directly:

```python
game = create_new_game("branoc")

session = OverworldSession(
    game,
    ui=None,
    battle_factory=Battle,
    enemy_factory=create_enemy_state,
    battle_ui_factory=None,
    save_repository=None,
)
```

---

# 3. Branch / Integration Precondition

Preferred sequence:

```text
mpy
  ↓
merge into master
  ↓
verify master contains post-MPY runtime
  ↓
create pyodide branch from updated master
```

Recommended browser branch:

```text
pyodide
```

If browser work starts before `mpy` is merged, create `pyodide` from the exact current `mpy` head.

Do not branch from the older stale `master` and recreate portability history.

---

# 4. Architecture

```text
root/src/app/
    owns gameplay/runtime
        ↑
root/web/python/
    owns browser-only adapter/projection
        ↑
root/web/js/
    owns rendering/input/fullscreen
        ↑
GitHub Pages
```

The browser adapter may translate immutable presentation models into browser-friendly data.

It may **not** decide:

- whether an action is legal,
- how damage is calculated,
- which move can be used,
- whether rewards are granted,
- how the route advances,
- whether a Rest is available,
- whether Super is ready,
- or any other gameplay rule already owned by Python.

---

# 5. Pyodide Rules

Pyodide is a CPython/WebAssembly target, not MicroPython.

The first browser qualification should run the normal DD source.

Do not automatically load MPY compatibility overlays.

Rules:

```text
pin an explicit Pyodide release
record its Python version
never use "latest" in production
do not add compatibility code before an observed failure
do not fork gameplay for Pyodide
do not convert gameplay to JavaScript
```

If Pyodide exposes a new incompatibility, stop at that exact frontier and derive the narrowest evidence-backed repair.

---

# 6. Static GitHub Pages Model

The final site must be fully static.

Conceptual deployment artifact:

```text
site/
├── index.html
├── styles.css
├── js/
│   ├── app.js
│   ├── pyodide_runtime.js
│   ├── renderer.js
│   ├── input.js
│   └── fullscreen.js
├── game/
│   └── dd_runtime.zip
├── assets/
└── build metadata
```

`dd_runtime.zip` should be generated from the authoritative source tree during the Pages build.

Do not maintain a copied browser edition of `root/src/app`.

---

# 7. Proposed Repository Boundaries

```text
root/
├── src/
│   └── app/
│       └── authoritative gameplay/runtime
├── web/
│   ├── index.html
│   ├── styles.css
│   ├── js/
│   ├── python/
│   │   ├── browser_host.py
│   │   └── browser_projection.py
│   ├── assets/
│   └── dist/
├── tools/
│   └── build_web.py
└── tests/
    ├── test_browser_bridge_contract.py
    └── test_web_build_contract.py
```

Exact filenames can change if live implementation evidence shows a cleaner boundary.

Ownership may not:

```text
root/src/app = gameplay
root/web     = browser host/presentation
root/tools   = build tooling
```

---

# 8. Browser Host Contract

The host API should stay deliberately small:

```text
start_game(drifter_id="branoc")
current_view()
submit(command)
restart_game()
```

For the first public build:

```text
Drifter: Branoc
Persistence: none
Content: current authored surface route
```

The host must construct the real `GameState`, `OverworldSession`, `Battle`, and `EnemyState`.

No parallel browser-owned state.

---

# 9. Browser Projection Contract

JavaScript should receive a plain presentation projection rather than reach through arbitrary Python object internals.

Preferred first boundary:

```text
Python dict/list/scalars
        ↓
json.dumps(...)
        ↓
JSON.parse(...) in JavaScript
```

The projection may include:

```text
screen / phase
display text
player status
enemy status
battle log
offered actions
offered moves
offered targets
offered inventory operations
enabled / disabled state
selection keys
target IDs
route action
completion/result information
```

It must not derive legality.

If the authoritative view does not offer an action, JavaScript must not invent it.

---

# 10. Browser Input Contract

Browser commands must map directly onto existing semantic input classes:

```text
ChooseOverworldAction(...)
ChooseAction(...)
ChooseMove(selection_key)
ChooseTarget(target_id)
ChooseInventoryItem(...)
ChooseInventoryCommand(...)
ConfirmInventoryUse(...)
GoBack()
```

A compact browser command may exist, for example:

```json
{
  "kind": "move",
  "key": "selection-key-from-current-view"
}
```

but its key must come from the current authoritative view.

Do not create a second REST-like gameplay protocol.

---

# 11. First Demo Scope

## Included

```text
Branoc
current authored surface route
normal encounters
elite encounter
Goblin Lord
Rests
current progression/reward loop
battle menus
inventory interactions required by current views
Super interactions
restart
demo completion screen
feedback/follow links
```

Natural stopping point:

```text
surface_dungeon_entrance
```

Completion copy should match reality:

```text
You reached the Dungeon Entrance.
```

## Deferred

```text
accounts
cloud saves
server backend
multiplayer
leaderboards
native packaging
PWA installation
offline mode
full art overhaul
all future characters/content
```

---

# 12. Persistence

Do not make saving a prerequisite for browser v0.

```text
refresh / close tab
→ session is lost
```

That is acceptable for the current short route.

`SAVE-ARCH` remains separate.

Do not force the desktop `SaveRepository` into Pyodide.

Later browser storage can be designed against the authoritative save contract:

```text
localStorage
IndexedDB
downloadable save
copyable save code
```

---

# 13. UI Direction

The browser should feel like a small landscape game, not a normal webpage.

Requirements:

```text
mobile-first
landscape-first
full viewport
no page scrolling during play
large touch targets
safe-area support
desktop mouse/keyboard compatibility
clear disabled states
responsive phone/tablet/desktop layout
```

Core regions:

```text
status
visual/game area
battle/adventure log
context-sensitive controls
```

Art is not a blocker. The first build may use styled panels, text, icons, simple backgrounds, and placeholder visuals.

---

# 14. Fullscreen and Orientation

```text
Open GitHub Pages link
        ↓
Title screen
        ↓
ENTER DUNGEON
        ↓
attempt fullscreen
        ↓
attempt landscape orientation lock
        ↓
start game
```

Fullscreen and orientation lock are progressive enhancement.

If unsupported:

```text
show rotate guidance
allow manual rotation
continue functioning
```

Use safe-area insets and dynamic viewport units where supported.

---

# 15. Performance Policy

DD is turn-based.

Pyodide may run on the main thread initially.

Do not introduce a Web Worker before evidence shows unacceptable input/render blocking.

If needed later:

```text
measure
→ identify blocking phase
→ move Pyodide host to Worker
```

---

# 16. Gate Plan

## PYD0 - Prove Raw Pyodide Runtime Boot

### Purpose

Find the first real Pyodide compatibility frontier before browser UI work.

### Work

Create the smallest static harness that:

```text
loads pinned Pyodide
records Pyodide version
records Python version
loads DD runtime package
adds it to sys.path
imports:
  app.game.new_game
  app.game.overworld_session
  app.combat.battle
  app.content.catalog
```

Then:

```python
game = create_new_game("branoc")
```

### Required result

```text
Pyodide loads
DD imports
Branoc GameState constructs
```

### Stop rule

Any import/construction failure stops the gate. Record the exact exception and derive the next repair from evidence.

### Suggested commit

```text
PYD0 - Prove Pyodide Runtime Boot
```

---

## PYD1 - Qualify Canonical Headless Session

### Purpose

Prove the real semantic session boundary under Pyodide.

### Work

Construct the real headless `OverworldSession` with `Battle`, `create_enemy_state`, and no persistence.

Require:

```text
current_view() → valid OverworldView
route node → surface_goblin_solo
offered action → ENTER_ENCOUNTER
```

Enter the first real Battle and drive real semantic input using only choices offered by `BattleView`.

### Required result

```text
real OverworldSession
real Battle
real default CombatResolver
real default RNG path
semantic view/input loop
PASS
```

### Suggested commit

```text
PYD1 - Qualify Pyodide Semantic Session
```

---

## PYD2 - Qualify Full Surface Route Under Pyodide

### Purpose

Re-run the canonical deterministic route oracle inside Pyodide before browser UI work.

### Expected route

```text
surface_goblin_solo
surface_goblin_pair
surface_warrior_solo
surface_rest_after_warrior_solo
surface_warrior_pair
surface_shaman_solo
surface_shaman_pair
surface_rest_after_shaman_pair
surface_elite_patrol
surface_rest_before_goblin_lord
surface_goblin_lord
surface_dungeon_entrance
```

Require:

```text
8 encounters
3 Rests
8 Battles
14 fresh enemies
route_complete == True
dungeon_entrance_reached == True
active_battle is None

Level 9
EXP 68
GP 24
Gold 75
```

Use deterministic qualification combat for the route oracle, while preserving PYD1 evidence that the real default path works.

### Stop rule

Any semantic mismatch blocks UI work.

### Suggested commit

```text
PYD2 - Qualify Full Surface Route In Pyodide
```

---

## PYD3 - Seal Browser Bridge Contract

### Purpose

Create the thin browser-only Python adapter.

### Required operations

```text
start_game
current_view
submit
restart
```

### Tests

Prove:

```text
host creates canonical runtime
projection does not mutate runtime
offered keys come from authoritative views
commands create existing semantic input objects
invalid command kinds are rejected
bridge contains no combat/progression calculations
```

The bridge should be testable under normal CPython.

### Suggested commit

```text
PYD3 - Seal Browser Runtime Bridge
```

---

## PYD4 - Build Minimal Playable Browser Shell

### Purpose

Make the entire current route manually playable with intentionally simple presentation.

### Implement

```text
title/loading screen
overworld/action screen
battle status
battle log
action controls
move controls
target controls
inventory controls needed by current views
Super controls
Rest flow
victory/result transitions
Dungeon Entrance completion screen
restart
```

The page renders only from Python projection output.

### Required result

A player can complete the current route manually in a desktop browser.

### Suggested commit

```text
PYD4 - Add Playable Browser Shell
```

---

## PYD5 - Harden Mobile Landscape Play

### Add

```text
landscape-first layout
portrait rotate screen
touch sizing
safe areas
dynamic viewport sizing
fullscreen request after user gesture
orientation lock attempt
manual-rotation fallback
responsive desktop support
loading/error/retry states
```

### Device/browser qualification

At minimum:

```text
Android Chrome-class browser
iPhone Safari-class browser
desktop Chromium
desktop Firefox
```

Fullscreen/orientation API differences must not block gameplay.

### Suggested commit

```text
PYD5 - Harden Mobile Browser Playtest
```

---

## PYD6 - GitHub Pages Build And Deployment

### Build tooling

Create a deterministic host build that:

```text
takes root/src/app
takes browser host Python
creates runtime archive
stages HTML/CSS/JS/assets
writes final static site
```

No hand-maintained copied `app` tree.

### GitHub Pages

Use GitHub Actions Pages deployment.

The workflow should:

```text
checkout exact SHA
run required Python verification
build browser artifact
run browser contract checks
upload Pages artifact
deploy Pages artifact
```

All paths must work under:

```text
/Dungeon-Drifters/
```

Avoid assumptions that the site is hosted at `/`.

Everything sent to Pages is public. No secrets may be required.

### Required result

```text
https://mrcodegameandanime.github.io/Dungeon-Drifters/
```

loads and plays without an application backend.

### Suggested commit

```text
PYD6 - Deploy Browser Playtest To GitHub Pages
```

---

## PYD7 - Browser CI Qualification

### Purpose

Make Pyodide/browser execution a permanent regression target.

Use a real headless browser against the built static site, for example Playwright plus a local static server.

Prove:

```text
page loads
Pyodide initializes
DD initializes
initial SessionView renders
one semantic action round-trip works
deterministic route qualification completes
completion signal is emitted
```

Do not use screenshot matching as the gameplay oracle.

Existing Python CI remains authoritative for Python regression tests.

Browser CI adds:

```text
static build
headless browser smoke
Pyodide semantic qualification
```

### Suggested commit

```text
PYD7 - Add Pyodide Browser Qualification CI
```

---

## PYD8 - Playtest Release

GitHub Pages is public, so an early "private" Pages test is really an unadvertised public URL.

Before broad sharing:

```text
real Android run
real iPhone run
desktop run
manual full-route completion
restart verification
readable refresh/no-save behavior
readable loading failures
no dead-end menus
feedback link
follow-development link
```

Public loop:

```text
post / screenshot / clip
        ↓
GitHub Pages link
        ↓
title
        ↓
Pyodide load
        ↓
surface route
        ↓
Goblin Lord
        ↓
Dungeon Entrance
        ↓
completion
        ↓
feedback / follow
```

### Suggested commit

```text
PYD8 - Release Browser Playtest
```

---

# 17. Verification

Before release preserve normal repo verification:

```text
full Python suite
content validation
compileall
dataclass manifest freshness
git diff --check
```

Add browser verification:

```text
web build succeeds
runtime archive contains intended app package
tests/docs/private junk are not packaged unintentionally
Pyodide boot passes
new-game construction passes
semantic session passes
full route passes
bridge contract passes
headless browser smoke passes
Pages deployment passes
```

Record actual test totals rather than predicting them.

---

# 18. GitHub Pages Workflow Policy

Recommended public deployment trigger once stable:

```text
push to master
workflow_dispatch
```

During development, branch CI should build/test the static artifact without automatically replacing the public Pages deployment.

Preferred flow:

```text
pyodide
  ↓
PR
  ↓
CI
  ↓
merge master
  ↓
Pages deploy
```

If a pre-merge Pages deployment is needed, make it an explicit manual action.

---

# 19. Architecture Failures To Avoid

```text
JavaScript damage calculation
JavaScript reward calculation
JavaScript route advancement
JavaScript enemy AI
JavaScript legality logic duplicated from Python
separate browser GameState
browser-specific combat engine
Flask/FastAPI solely to host gameplay
manual copied browser edition of root/src/app
rewriting DD in JavaScript
changing gameplay for UI convenience
forcing SaveRepository into browser v0
using MPY overlays in Pyodide without evidence
```

Presentation adaptation is allowed.

Gameplay authority migration is not.

---

# 20. Stop Conditions

Stop and derive a focused repair if:

```text
Pyodide cannot import authoritative runtime
canonical new game fails
default Battle/session semantics differ
full route final state differs
bridge requires gameplay knowledge
projection requires GameState mutation
JavaScript must infer legal actions not present in view
Pages appears to require backend behavior for current demo
save work contaminates deferred SAVE-ARCH
compatibility repair introduces second gameplay path
```

Do not treat fullscreen/orientation/CSS differences as runtime failures.

---

# 21. Initial Product Decisions

```text
Playable Drifter: Branoc
Gameplay authority: Python only
Browser Python runtime: Pyodide
Hosting: GitHub Pages
Backend: none
Accounts: none
Cloud saves: none
Local saves: deferred
PWA: deferred
Art overhaul: deferred
Demo ending: Dungeon Entrance
Purpose: playtesting + feedback + frictionless sharing
```

---

# 22. Deferred Work

After PYD8, evidence may justify:

```text
browser persistence adapter
PWA/install mode
offline caching
Web Worker Pyodide host
other Drifters
more content
audio
animation polish
controller/keyboard shortcuts
accessibility improvements
telemetry
structured feedback
```

None is required to prove the initial architecture.

---

# 23. Requalification Triggers

Re-run Pyodide semantic qualification when:

```text
Pyodide version changes
Pyodide Python version changes
SessionView/SessionInput changes
BattleView/BattleInput changes
browser bridge protocol changes
route oracle changes
new runtime dependency enters root/src/app
browser packaging changes
```

Pyodide should become a regression target, not the center of gameplay architecture.

---

# 24. Final Acceptance Criteria

The browser-playtest milestone is complete when:

```text
one authoritative Python gameplay runtime remains
normal Python regression suite passes
DD imports in pinned Pyodide
create_new_game("branoc") works in Pyodide
real headless OverworldSession works in Pyodide
real default Battle/input path works in Pyodide
deterministic full surface route qualifies in Pyodide
browser bridge uses existing semantic views/inputs
JavaScript contains no gameplay rules
Branoc can complete the current route manually in browser
mobile landscape experience is usable
fullscreen/orientation failures degrade gracefully
static build requires no backend
GitHub Pages deploy succeeds
public URL loads and plays
Goblin Lord can be defeated
Dungeon Entrance can be reached
completion screen offers feedback/follow actions
no persistence is required for v0
no duplicate browser gameplay implementation exists
```

---

# 25. End-State Architecture

```text
                         Dungeon Drifters
                    Authoritative Python Runtime
                              │
            ┌─────────────────┼──────────────────┐
            │                 │                  │
         CPython           Pyodide          MicroPython
      development /      GitHub Pages       qualified
        desktop          browser host       constrained
            │                 │
      terminal host      thin web host
                              │
                        HTML / CSS / JS
```

Future Android or other hosts should consume the same gameplay authority rather than inherit browser implementation details.

---

# 26. Immediate Next Action

After the post-MPY branch is landed, or after `pyodide` is created directly from its exact head:

```text
begin PYD0
```

The first implementation task is deliberately tiny:

```text
static local page
→ load pinned Pyodide
→ package/load root/src/app
→ import DD
→ create Branoc
→ emit PASS
```

Do not build the real browser UI until that succeeds.

The campaign should preserve the same evidence-first discipline that worked for MPY:

```text
prove runtime
→ qualify semantics
→ qualify full route
→ seal bridge
→ build presentation
→ deploy
```

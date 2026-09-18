# Dungeon Drifters: Pyodide + GitHub Pages Browser Playtest Plan

## Status
This is the active browser-playtest implementation plan. It supersedes older browser plans that assumed a Flask/FastAPI gameplay backend or a disposable Python prototype that would later be rewritten.

Dungeon Drifters now has one authoritative Python gameplay implementation with semantic views/inputs, step-driven `Battle` and `OverworldSession` APIs, canonical new-game construction, a qualified headless route, and a completed MPY0-MPY20 portability campaign.

The browser build is a static GitHub Pages host around the existing Python runtime, executed in-browser with Pyodide.

# 1. Goal And Invariants
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
existing SessionInput / BattleInput
    ↓
submit(...)
```

Hard rules:
```text
Python owns gameplay.
JavaScript owns browser presentation and input collection.

No Flask/FastAPI gameplay backend.
No duplicate combat engine.
No browser-owned GameState.
No JavaScript damage/reward/route/legality logic.
No copied browser edition of root/src/app.
No gameplay rewrite for Pyodide.
No persistence requirement for the first browser build.
```

Presentation adaptation is allowed. Gameplay authority migration is not.

# 2. Current Baseline And Scope
Browser work starts from current `master` after the completed MPY merge.

Historical portability archive:
```text
tag: mpy-archive
SHA: 74eb4ae82c31ad259fdaa52294794c27030e1cdd
```

Recommended browser branch:
```text
pyodide
```

Create it from current `master`.

Existing deterministic route qualification proves:
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

Canonical construction:
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

First browser scope:
```text
Branoc
current authored surface route
normal encounters
elite encounter
Goblin Lord
Rests
current progression/reward loop
battle menus
required inventory interactions
Super interactions
restart
completion at Dungeon Entrance
feedback/follow links
```

Natural stopping point:
```text
surface_dungeon_entrance
```

Completion copy:
```text
You reached the Dungeon Entrance.
```

Saving, accounts, backend services, PWA work, native packaging, and future gameplay/content are outside this milestone.

# 3. Browser Boundary
Ownership:
```text
root/src/app/
    authoritative gameplay/runtime

root/web/python/
    browser host and presentation projection

root/web/js/
    rendering, input collection, fullscreen/orientation

root/tools/
    deterministic browser build tooling
```

Exact filenames may change. Ownership may not.

Browser-facing Python API:
```text
start_game(drifter_id="branoc")
current_view()
submit(command)
restart_game()
```

The host constructs the real `GameState`, `OverworldSession`, `Battle`, and `EnemyState`. There is no parallel browser-owned gameplay state.

Preferred projection boundary:
```text
Python dict/list/scalars
    ↓
json.dumps(...)
    ↓
JSON.parse(...) in JavaScript
```

Projection may expose:
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

It must not derive gameplay legality. If an authoritative view does not offer an action, JavaScript must not invent it.

Browser commands map onto the existing semantic input types, including the current equivalents of:
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

A compact command envelope is allowed:
```json
{
  "kind": "move",
  "key": "selection-key-from-current-view"
}
```

The command must resolve to the existing Python semantic input object. Selection keys and target IDs must come from the current authoritative view. Do not create a second gameplay protocol.

# 4. Pyodide, Presentation, And Deployment Constraints
Pyodide is a CPython/WebAssembly target, not MicroPython.

Start with the normal DD source:
```text
pin an explicit Pyodide release
record its Python version
never use "latest" in production
do not load MPY overlays without an observed need
do not add compatibility code before an observed failure
```

If Pyodide exposes an incompatibility, stop at that exact frontier and derive the narrowest evidence-backed repair.

The playtest must be fully static and deployable through GitHub Pages.

Conceptual deployment artifact:
```text
site/
├── index.html
├── styles.css
├── js/
├── game/
│   └── dd_runtime.zip
├── assets/
└── build metadata
```

`dd_runtime.zip` must be generated from `root/src/app`. Do not maintain a copied browser edition of the application tree.

All deployment paths must work under:
```text
/Dungeon-Drifters/
```

No secrets or application backend may be required.

Presentation constraints:
```text
mobile-first
landscape-first
full viewport
no page scrolling during play
large touch targets
safe-area support
responsive desktop support
clear disabled states
loading/error/retry states
```

Art is not a blocker. Styled panels, text, icons, simple backgrounds, and placeholder visuals are acceptable.

Fullscreen and orientation lock are progressive enhancement. Unsupported APIs must degrade to manual rotation guidance without blocking gameplay.

DD is turn-based. Run Pyodide on the main thread first. Add a Web Worker only if measured browser behavior proves it necessary.

# 5. Gate Plan

## PYD0 - Prove Raw Pyodide Runtime Boot
Purpose: find the first real Pyodide compatibility frontier before browser UI work.

Work:
```text
load pinned Pyodide
record Pyodide version
record Python version
load DD runtime package
add it to sys.path
import:
  app.game.new_game
  app.game.overworld_session
  app.combat.battle
  app.content.catalog
create Branoc with create_new_game("branoc")
```

Pass:
```text
Pyodide loads
DD imports
Branoc GameState constructs
```

Stop on any import/construction failure and repair only the observed frontier.

Suggested commit:
```text
PYD0 - Prove Pyodide Runtime Boot
```

## PYD1 - Qualify Canonical Headless Session
Purpose: prove the real semantic session boundary under Pyodide.

Construct the real headless `OverworldSession` using the existing Battle, enemy construction, resolver path, RNG path, and no persistence.

Require:
```text
current_view() returns valid OverworldView
initial route node is surface_goblin_solo
ENTER_ENCOUNTER is offered by the authoritative view
first real Battle can be driven using choices from BattleView
```

Pass:
```text
real OverworldSession
real Battle
real default CombatResolver
real default RNG path
semantic view/input loop
```

Stop on semantic mismatch or any need for browser-specific gameplay behavior.

Suggested commit:
```text
PYD1 - Qualify Pyodide Semantic Session
```

## PYD2 - Qualify Full Surface Route Under Pyodide
Purpose: re-run the canonical deterministic route oracle in Pyodide before browser presentation work.

Expected route:
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

Required result:
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

Use deterministic qualification combat for the route oracle while preserving PYD1 evidence that the real default path works. Any route, semantic, or final-state mismatch blocks UI work.

Suggested commit:
```text
PYD2 - Qualify Full Surface Route In Pyodide
```

## PYD3 - Seal Browser Bridge Contract
Purpose: create the thin browser-only Python adapter.

Required operations:
```text
start_game
current_view
submit
restart
```

Prove:
```text
host creates canonical runtime
projection does not mutate runtime
offered keys come from authoritative views
commands create existing semantic input objects
invalid command kinds are rejected
bridge contains no combat/progression/route calculations
```

The bridge must also be testable under normal CPython. If the bridge needs gameplay knowledge rather than translation/presentation knowledge, stop and repair the boundary.

Suggested commit:
```text
PYD3 - Seal Browser Runtime Bridge
```

## PYD4 - Build Minimal Playable Browser Shell
Purpose: make the current route manually playable with intentionally simple presentation.

Implement:
```text
title/loading screen
overworld/action screen
battle status
battle log
action controls
move controls
target controls
required inventory controls
Super controls
Rest flow
victory/result transitions
Dungeon Entrance completion screen
restart
```

The page renders from Python projection output.

Pass when a player can complete the route manually in a desktop browser without JavaScript owning gameplay decisions.

Suggested commit:
```text
PYD4 - Add Playable Browser Shell
```

## PYD5 - Harden Mobile Landscape Play
Add:
```text
landscape-first layout
portrait rotate guidance
touch sizing
safe areas
dynamic viewport sizing
fullscreen request after user gesture
orientation lock attempt
manual-rotation fallback
responsive desktop support
loading/error/retry states
```

Qualify at minimum:
```text
Android Chrome-class browser
iPhone Safari-class browser
desktop Chromium
desktop Firefox
```

Fullscreen/orientation differences must not block gameplay.

Suggested commit:
```text
PYD5 - Harden Mobile Browser Playtest
```

## PYD6 - Build And Deploy Through GitHub Pages
Create a deterministic build that:
```text
takes root/src/app
takes browser host Python
creates runtime archive
stages HTML/CSS/JS/assets
writes final static site
```

No hand-maintained copied `app` tree.

GitHub Actions Pages workflow:
```text
checkout exact SHA
run required Python verification
build browser artifact
run browser contract checks
upload Pages artifact
deploy Pages artifact
```

Development flow:
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

Pass when the public Pages URL loads and plays without an application backend.

Suggested commit:
```text
PYD6 - Deploy Browser Playtest To GitHub Pages
```

## PYD7 - Add Browser CI Qualification
Purpose: make Pyodide/browser execution a permanent regression target.

Use a real headless browser against the built static site, for example Playwright with a local static server.

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

Do not use screenshot matching as the gameplay oracle. Existing Python CI remains authoritative for Python regression tests.

Browser CI adds:
```text
static build
headless browser smoke
Pyodide semantic qualification
```

Suggested commit:
```text
PYD7 - Add Pyodide Browser Qualification CI
```

## PYD8 - Release Browser Playtest
Before broad sharing verify:
```text
real Android run
real iPhone run
desktop run
manual full-route completion
restart
clear refresh/no-save behavior
readable loading failures
no dead-end menus
feedback link
follow-development link
```

GitHub Pages is public, so an early Pages test is an unadvertised public build rather than a private deployment.

Pass when the browser playtest is suitable to share directly through the Pages URL.

Suggested commit:
```text
PYD8 - Release Browser Playtest
```

# 6. Verification And Stop Conditions
Preserve normal repository verification:
```text
full Python suite
content validation
compileall
dataclass manifest freshness
git diff --check
```

Record actual test totals rather than predicting them.

Browser qualification adds:
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

Stop and derive a focused repair if:
```text
Pyodide cannot import authoritative runtime
canonical new game fails
default Battle/session semantics differ
full-route final state differs
bridge requires gameplay knowledge
projection requires gameplay-state mutation
JavaScript must infer legal actions not present in the view
Pages requires backend gameplay behavior
browser work contaminates the separate save architecture
compatibility repair introduces a second gameplay path
```

CSS, fullscreen, orientation, and presentation differences are not gameplay-runtime failures.

# 7. Requalification Triggers
Re-run Pyodide semantic qualification when these change materially:
```text
Pyodide version
Pyodide Python version
SessionView / SessionInput
BattleView / BattleInput
browser bridge protocol
route oracle
runtime dependencies under root/src/app
browser runtime packaging
```

Pyodide is a regression target, not the center of gameplay architecture.

# 8. Final Acceptance Criteria
The browser-playtest milestone is complete when:
```text
one authoritative Python gameplay runtime remains
normal Python verification passes
DD boots and constructs Branoc in pinned Pyodide
real OverworldSession and default Battle path work in Pyodide
deterministic full surface route qualifies in Pyodide
browser bridge uses existing semantic views and inputs
JavaScript contains no gameplay rules
Branoc can complete the route manually in browser
mobile landscape play is usable and degrades safely
static GitHub Pages build requires no backend
browser CI covers boot, semantic round-trip, and route qualification
public Pages URL loads and reaches Dungeon Entrance
restart works
no persistence is required for this milestone
```

Begin with **PYD0**. Do not build the real browser UI until raw Pyodide runtime boot and canonical game construction are proven.

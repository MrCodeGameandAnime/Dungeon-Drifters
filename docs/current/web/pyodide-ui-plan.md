# PD|UI Browser Phase Parity Implementation Plan

**Goal:** Make the browser playtest preserve Dungeon Drifters' canonical phase-driven interaction flow, information hierarchy, transitions, and authored detail while retaining responsive browser presentation.

**Architecture:** Keep `root/src/app` and `root/web/python/dd_bridge.py` authoritative for game state, offered actions, and transitions. Refactor the existing `root/web/pyd4` shell into a faithful browser renderer of the current `SessionView` or `BattleView`. The browser adapts geometry for the viewport but does not redesign DD's interaction model. Keep every browser-specific test under `root/web_tests`.

**Tech Stack:** Pinned Pyodide 314.0.7, HTML, CSS, vanilla JavaScript, the existing Python browser bridge, Python web contracts, and Playwright browser smoke tests.

**Spec:** [Pyodide + GitHub Pages Browser Playtest Plan](../../current/web/pyodide-plan.md), with the user-approved clarification in this task: browser parity preserves canonical phases, information priority, transitions, grouping, and available detail; responsive reflow may not redefine the interaction model.

## Presentation Authority

The existing DD terminal presentation is the canonical interaction and information-hierarchy reference for every surface already wired into the browser playtest.

Authority is divided as follows:

- `SessionView`, `BattleView`, and the existing bridge projection are authoritative for state, legality, labels, values, enabled/disabled state, offered commands, and transitions.
- The terminal renderer is authoritative for phase structure, information priority, grouping, sequencing, and the detail shown to the player for currently supported surfaces.
- The browser may adapt layout geometry, spacing, typography, control shape, and responsive reflow for desktop/mobile constraints.
- The browser may not redesign DD into persistent dashboard panels, expose inactive-phase controls, regroup unrelated phases, omit authored detail available from the authoritative projection, or invent browser-specific gameplay concepts.
- Features not yet wired into the browser, including Map, Equipment, broader Character surfaces, Drifter selection, or persistence, remain absent rather than being simulated or replaced.
- Host-only utilities such as Fullscreen and Restart may remain compact browser controls, but they are not gameplay surfaces.

The browser target is therefore **1:1 interaction parity for currently wired gameplay**, not pixel-identical terminal styling.

## Canonical Phase Structure

### Overworld

Render, in canonical information order:

1. Location / current phase header.
2. Adventure or route narrative.
3. Contextual action currently offered by the session, such as entering an encounter or using a rest.
4. General actions currently offered by `view.options`.

Do not render Battle controls, empty Battle placeholders, target controls, move controls, or persistent panels for inactive phases.

### Battle - Actions

Render, in canonical information order:

1. Player and enemy status.
2. Encounter / combat log.
3. Current Battle action choices.
4. Persistent combat resource information such as Super.

The Battle screen does not retain an Overworld route card or "road ahead" panel. Once Battle is active, the visible surface is Battle.

### Battle - Move Selection

Selecting Attack transitions the active interaction area from Actions to Move Selection.

Render:

1. Existing player/enemy Battle context.
2. Existing Battle log.
3. Each authoritative offered move with:
   - move name
   - type / tags
   - resource cost / `resource_label`
   - authored description / `rules_summary`
   - enabled/disabled state and reason
4. Explicit Back control when `GoBack` is offered.
5. Persistent combat resource information.

Do not continue showing the generic Actions list beside the move list.

### Battle - Target Selection

When a move requires a target, replace the active Move Selection controls with the authoritative target choices.

Render:

1. Existing player/enemy Battle context.
2. Existing Battle log.
3. Each authoritative target with:
   - current label
   - HP/state detail exposed by the view
   - enabled/disabled state
   - authoritative `target_id`
4. Explicit Back control when offered.
5. Persistent combat resource information.

### Battle - Inventory / Nested Interaction

When Items or another nested Battle interaction is active, render only the controls for the currently authoritative interaction phase while retaining Battle context.

Preserve item, combination, confirmation, cancellation, and Back transitions exactly as currently offered by the bridge.

### Resolution and Return to Overworld

After an encounter resolves:

1. Preserve the authoritative result, reward, notice, or narrative returned by the session.
2. Return to the Overworld projection through the existing runtime transition.
3. Render the next Overworld state independently.
4. Do not automatically fold the next encounter into the completed Battle.
5. Entering the next encounter remains a separate contextual action.

## Global Constraints

- Python remains the sole owner of gameplay, legality, route, combat, and progression state.
- JavaScript renders authoritative projections and submits existing semantic inputs; it must not infer or invent offered actions.
- Do not modify `root/src/app`, compatibility overlays, the bridge protocol, or gameplay behavior for presentation convenience.
- Do not create a second gameplay implementation, browser-owned game state, or persistent dashboard of unrelated phases.
- Do not introduce browser-only test hooks into gameplay code.
- Keep all tests specifically for the web in `root/web_tests`; do not add them to the regular `root/tests` suite.
- Preserve the pinned Pyodide version, static GitHub Pages deployment, Branoc quick start, and no-save playtest scope.
- Unsupported browser surfaces remain absent unless the authoritative browser view already offers them.
- Do not simulate absent Map, Equipment, Character, Drifter-selection, persistence, or other gameplay surfaces in JavaScript.
- Preserve authored detail already available from the authoritative browser projection rather than replacing it with generic browser labels.
- After each of the three gates: run its checks, commit on `pyodide`, push, wait for exact-SHA CI/Pages checks, report the commit and result, then stop for the user's direction before starting the next gate.

## Review Focus

- Overworld projection with no contextual encounter/rest action: render only options the current view offers and no empty Battle controls; pin in Gate 1 browser smoke.
- Battle entry: remove all persistent Overworld route/dashboard content once the authoritative view enters Battle.
- Battle actions or moves marked disabled: preserve disabled state and reason without allowing submission; pin in Gate 2 browser smoke.
- Attack with several offered moves: show names, tags/type, resource labels, and rules summaries only after entering Move Selection; pin in Gate 2 browser smoke.
- Multi-enemy target selection: preserve each authoritative target label, HP, enabled state, and target ID; pin in Gate 2 semantic round-trip.
- Back behavior: every phase that authoritatively offers `GoBack` must expose a clear Back control and return to the correct prior phase.
- Encounter completion: browser rendering must consume the authoritative result and subsequent Overworld projection rather than synthesizing its own completion state.
- Long move descriptions or many controls on short landscape/mobile viewports: keep every choice reachable without clipping or unintended page-level scrolling; pin in Gate 3 responsive browser checks.
- Visual hierarchy: automated DOM correctness is insufficient on its own; Gate 3 must capture screenshots proving the browser still reads like DD rather than a generic dashboard.

---

## Gate PD|UI 1 - Focus The Overworld Phase

**Files:**

- Modify: `root/web/pyd4/index.html`
- Modify: `root/web/pyd4/js/pyd4.js`
- Modify: `root/web/pyd4/styles.css`
- Modify: `root/web_tests/test_pyodide_shell_contract.py`
- Modify: `root/web_tests/browser_smoke.mjs`

**Interfaces:**

- Consumes: the existing JSON projection returned by `current_view_json()` and `submit_json(...)` in `root/web/python/dd_bridge.py`.
- Produces: one visible phase surface at a time.
- The Overworld surface follows the canonical DD order: location/header, adventure narrative, contextual route action when present, then only the general options in `view.options`.
- Fullscreen and Restart remain compact host utilities rather than gameplay content panels.

- [ ] **Step 1: Pin the current Overworld failure in web tests.** Add browser-smoke assertions that the initial main view shows its location/route narrative and offered contextual/general options, hides Battle-only content, and does not show an empty "Choose your next move" panel or other inactive Battle controls.
- [ ] **Step 2: Pin canonical Overworld ordering.** Assert that location/header and narrative precede contextual/general controls and that unrelated dashboard cards are absent.
- [ ] **Step 3: Verify the tests fail against the current dashboard shell.** Run `& .\.venv\Scripts\python.exe -m pytest root\web_tests\test_pyodide_shell_contract.py -q` and the browser smoke against the locally built site; confirm the failures describe the currently visible empty/persistent phase panels or incorrect hierarchy.
- [ ] **Step 4: Establish a focused Overworld surface.** Restructure the existing shell and renderer so main/Overworld state is one focused screen matching the canonical terminal information hierarchy. Render contextual and general controls only from the current projection.
- [ ] **Step 5: Remove inactive-phase presentation.** Ensure no Battle status, move controls, target controls, Battle input card, or empty placeholders persist while the authoritative view is Overworld.
- [ ] **Step 6: Verify the Overworld-to-Battle transition.** Extend the Playwright smoke to enter the first encounter and confirm the resulting view replaces the Overworld surface with a focused Battle surface. No Overworld "Current Route," "The road ahead," narrative card, or persistent dashboard panel remains visible in Battle. Detailed move/target parity remains Gate 2.
- [ ] **Step 7: Run Gate 1 checks.** Run `& .\.venv\Scripts\python.exe -m pytest root\web_tests\test_pyodide_shell_contract.py -q`; build with `& .\.venv\Scripts\python.exe root\tools\build_browser_site.py --output root\web\dist`; serve `root\web\dist` locally; run `npm --prefix root/web_tests run browser-smoke -- http://127.0.0.1:8765`; and run `git diff --check`.
- [ ] **Step 8: Release Gate 1 and stop.** Commit as `PD|UI 1 - Focus Overworld Phase`, push `pyodide`, wait for the exact-SHA Python CI and Pages workflow, then report the commit, run links/results, and changed behavior. Do not start Gate 2 until the user says continue.

**Gate 1 acceptance:** The initial Overworld view follows DD's canonical phase hierarchy rather than a dashboard; only current Overworld information and offered controls are visible; no Battle-only empty panel exists; submitted contextual action replaces Overworld with the authoritative Battle; no production or bridge files changed.

---

## Gate PD|UI 2 - Preserve Battle Interaction Flow

**Files:**

- Modify: `root/web/pyd4/index.html` only if the focused Battle surface needs semantic regions.
- Modify: `root/web/pyd4/js/pyd4.js`
- Modify: `root/web/pyd4/styles.css`
- Modify: `root/web_tests/test_pyodide_shell_contract.py`
- Modify: `root/web_tests/browser_smoke.mjs`
- Modify or create: focused Battle-flow contracts under `root/web_tests/`

**Interfaces:**

- Consumes: authoritative `BattleView` fields including `interaction_phase`, `player`, `enemies`, `log_entries`, `action_options`, `move_options`, `target_options`, inventory options, and their enabled/disabled metadata.
- Produces: a Battle renderer following the canonical DD order of player/enemy status, Battle log, current interaction controls, and persistent combat resources.
- Submits only the existing action, move, target, inventory, confirmation, Back, and related commands already translated by `dd_bridge.py`.

- [ ] **Step 1: Pin canonical Battle Actions presentation.** Assert that entering Battle displays player/enemy state, Battle log/context, the currently offered Actions, and persistent combat resources in the canonical DD hierarchy. Assert that Overworld route/dashboard content is absent.
- [ ] **Step 2: Pin canonical phase transitions.** Assert that Actions initially exposes only the action choices; selecting Attack changes the authoritative interaction phase to Move Selection; selecting a move uses its current `selection_key`; target choices use the current `target_id`; and Back returns through the existing command path.
- [ ] **Step 3: Pin authored move detail.** For every offered move, assert the browser renders the authoritative name, tags/type, `resource_label`, `rules_summary`, enabled/disabled state, and disabled reason when present. Assert move detail appears only during Move Selection.
- [ ] **Step 4: Pin multi-enemy target detail.** Assert Target Selection preserves each authoritative target label, HP/state detail exposed by the view, enabled state, and `target_id`.
- [ ] **Step 5: Verify those assertions fail against the generic dashboard/action-card presentation.** Run the focused web tests and existing Playwright smoke before changing the Battle renderer.
- [ ] **Step 6: Render one focused Battle phase.** Present player/enemy status, relevant combat log, current interaction controls, and Super/resource state in the canonical terminal-derived hierarchy. Do not keep multiple interaction phases visible simultaneously.
- [ ] **Step 7: Restore Move Selection detail.** Selecting Attack replaces the Actions controls with the currently offered move list. Render the full authoritative move detail and Back when offered. Do not leave generic Attack/Defend/Heal/Items controls beside the move list.
- [ ] **Step 8: Restore Target Selection detail.** When a selected move requires a target, replace the Move Selection controls with authoritative targets and Back. Preserve labels, current HP/state, availability, and target identity.
- [ ] **Step 9: Preserve outcomes and nested inventory flow.** Keep the authoritative Battle context visible while rendering the currently active item, combination, confirmation, cancellation, or Back phase. After encounter completion, consume the authoritative session result/notice and subsequent Overworld projection. Do not invent a browser-only result or inventory state.
- [ ] **Step 10: Verify bounded semantic round-trips in Playwright.** Enter an encounter, choose Attack, inspect the move surface, submit a move, select a target when offered, exercise Back where offered, and verify every visible next phase comes from the bridge response.
- [ ] **Step 11: Qualify encounter completion without introducing testability hacks.** Complete an encounter through Playwright only if the existing runtime/browser surface provides a deterministic path without gameplay changes, browser-only state, or special test hooks. If deterministic Playwright completion is not available, do not modify gameplay to manufacture it. Instead:
  - use Playwright for bounded real semantic round-trips;
  - retain the existing deterministic full-route qualification page for authoritative encounter completion;
  - pin result-to-Overworld browser rendering through a focused web-layer contract using an authoritative projection.
- [ ] **Step 12: Keep existing qualification surfaces unchanged.** The deterministic full-route browser qualification page remains unchanged and green unless a genuine compatibility fix is required by this gate.
- [ ] **Step 13: Run Gate 2 checks.** Run `& .\.venv\Scripts\python.exe -m pytest root\web_tests`; rebuild and serve `root\web\dist`; run `npm --prefix root/web_tests run browser-smoke -- http://127.0.0.1:8765`; and run `git diff --check`.
- [ ] **Step 14: Release Gate 2 and stop.** Commit as `PD|UI 2 - Preserve Battle Interaction Flow`, push `pyodide`, wait for exact-SHA CI/Pages success, report the commit and run links/results, then stop for the user's direction.

**Gate 2 acceptance:** The player sees DD's canonical Battle hierarchy and actual Actions -> Move Selection -> Target/Inventory -> result -> Overworld interaction flow. The active phase replaces the prior controls rather than accumulating beside them. Authored move/target detail and availability remain intact. No Overworld route card persists during Battle. No JS combat rules, second gameplay state, new command protocol, gameplay test hook, or production convenience change was added.

---

## Gate PD|UI 3 - Qualify Responsive Phase Presentation

**Files:**

- Modify: `root/web/pyd4/styles.css`
- Modify: `root/web/pyd4/index.html` and `root/web/pyd4/js/pyd4.js` only for accessibility or rendering fixes exposed by responsive qualification.
- Modify: `root/web_tests/test_pyodide_mobile_contract.py`
- Modify: `root/web_tests/browser_smoke.mjs`

**Interfaces:**

- Consumes: the canonical phase surface established by Gates 1 and 2, including variable-length authoritative text and option lists.
- Produces: responsive desktop, landscape-phone, and portrait-guidance layouts without changing game phases, grouping, ordering, authored detail, or offered choices.
- Responsive presentation may reflow geometry but may not introduce a separate mobile/desktop interaction model.

- [ ] **Step 1: Pin responsive failure cases.** Add Playwright checks for a desktop viewport, a short landscape phone viewport, and portrait guidance. Assert the current phase and required controls remain visible/reachable, text is not clipped, and the document does not acquire unintended page-level scrolling during play.
- [ ] **Step 2: Pin hierarchy across viewport sizes.** Assert that responsive changes preserve the same canonical phase order and do not reintroduce dashboard panels, persistent inactive controls, or different desktop/mobile gameplay grouping.
- [ ] **Step 3: Verify responsive checks expose the current layout problems.** Run the focused web/mobile contract tests against the current styles before editing.
- [ ] **Step 4: Reflow the focused phase surface.** Remove dashboard grid sizing. Use responsive constraints for player/enemy context, log, phase choices, Super/resource display, safe areas, and dynamic viewport height. Keep long option lists reachable through a deliberate contained region without hiding Back or active controls.
- [ ] **Step 5: Preserve desktop density.** Desktop must not inflate ordinary Battle controls into oversized dashboard cards. Use the available screen area to keep the canonical Battle presentation compact, readable, and focused.
- [ ] **Step 6: Preserve mobile usability.** Landscape mobile may use larger touch targets and tighter stacking/reflow, but it must preserve the same interaction sequence, authored detail, phase boundaries, and control availability as desktop.
- [ ] **Step 7: Verify functional parity at each viewport.** Run the same phase-driven browser smoke at desktop and landscape-phone dimensions; verify portrait guidance remains advisory and does not block input. Check keyboard focus, disabled controls, touch target sizing, long move text, Back, and Restart.
- [ ] **Step 8: Capture visual parity evidence.** Capture browser screenshots after the responsive pass for at least:
  - desktop Overworld;
  - desktop Battle Actions;
  - desktop Move Selection;
  - desktop Target Selection when reachable;
  - landscape-mobile Battle Actions;
  - landscape-mobile Move Selection.
- [ ] **Step 9: Review screenshots against the canonical terminal flow.** Confirm visually that the browser preserves the same phase hierarchy and reads as Dungeon Drifters rather than a generic web dashboard. DOM assertions alone are not sufficient evidence for this gate.
- [ ] **Step 10: Run final Gate 3 verification.** Run `& .\.venv\Scripts\python.exe -m pytest root\web_tests`, rebuild and run the Playwright smoke, run the repository's full Python suite with `& .\.venv\Scripts\python.exe -m pytest`, and run `git diff --check`.
- [ ] **Step 11: Request physical-device verification.** Request/record a real Android browser check on the deployed `pyodide` Pages site. Do not report physical-device verification until the user confirms it. Record whether desktop and the tested Android orientation both preserve the canonical phase flow and all reachable controls.
- [ ] **Step 12: Release Gate 3 and stop.** Commit as `PD|UI 3 - Qualify Responsive Browser UI`, push `pyodide`, wait for exact-SHA CI and Pages deployment, and report the commit, run links, test totals, deployed URL, screenshot evidence, and any device-check limitation.

**Gate 3 acceptance:** Desktop and automated mobile viewport checks preserve the same DD phase flow, hierarchy, grouping, authored detail, and reachable choices. Responsive geometry changes do not create a separate interaction model. The interface is not a persistent dashboard. Screenshot evidence confirms the browser presentation remains recognizably faithful to the canonical terminal experience. Deployment and normal Python CI remain green.

---

## Completion Boundary

The three UI gates do not add missing gameplay screens, select a Drifter, add persistence, wire Map or Equipment, or claim iPhone/Android certification.

They make the already-wired Branoc browser playtest render DD's existing Overworld/Battle interaction model faithfully.

Missing browser features are acceptable within this milestone when the underlying browser surface has not been wired yet.

Replacing, simplifying, regrouping, or redesigning already-wired DD interaction merely because the host is a browser is not acceptable.

**Completion means: same Dungeon Drifters experience, different renderer.**
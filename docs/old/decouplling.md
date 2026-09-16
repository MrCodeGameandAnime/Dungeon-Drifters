DD Runtime Decoupling

Summary

Refactor the runtime so semantic state transitions are publicly driveable without terminal input, while preserving the existing terminal game, combat rules, save format, content catalog, presenters, and semantic input objects.

Actual baseline:

Branch: master
HEAD: ea1e79adf9118aae309cad4e14af25fa1009f4de
Working tree: clean
Remote: synchronized

The existing semantic seams are real:

BattleUI and OverworldUI already define render(view) and read_input(view).

M11 already drives full routes with custom non-terminal UI objects.

Battle and OverworldSession currently own blocking loops.

main_loop still owns terminal startup and character selection.

Public Runtime Contract

Battle

Add:

battle.current_view() -> BattleView
battle.submit(input: BattleInput) -> BattleView
battle.is_complete -> bool
battle.winner -> str | None

Behavior:

Battle accepts ui=None; UI is required only by compatibility methods such as run() and player_action().

Battle initialization, including encounter logging and initiative, occurs exactly once before the first externally observable view is produced. current_view() itself must be observational: it must not mutate battle state, consume RNG, reroll initiative, or replay actions.

If the enemy side wins initiative, its automatic phase runs before the first player decision is returned.

Repeated current_view() calls do not reroll RNG, replay actions, or mutate state.

submit() processes exactly one already-semantic input and never calls read_input(), input(), print(), or terminal code.

Navigation and invalid-input behavior remain unchanged, but one invalid submission returns the current view instead of internally waiting for another input.

Accepted player actions run existing lifecycle logic, automatic enemy phases, winner checks, and suppression exactly as today.

Move selection and target selection stop at the next required player decision.

A completed submission returns the final inactive BattleView once.

current_view() after completion returns that same inactive final view.

Submissions after completion are harmless no-ops returning the final view.

Existing run(), player_action(), enemy_phase(), and enemy_action() remain as compatibility helpers. They must depend on shared transition logic, while the new step API never depends on them.

The existing CombatResolver, RNG injection, presenters, lifecycle ordering, target validation, inventory behavior, and combat mechanics remain authoritative.

OverworldSession

Add:

session.current_view() -> OverworldView | BattleView
session.submit(input: OverworldInput | BattleInput) -> OverworldView | BattleView

Use public aliases:

SessionView = OverworldView | BattleView
SessionInput = OverworldInput | BattleInput

Behavior:

ui and battle_ui_factory become optional for step-driven use.

run() requires those compatibility UI dependencies and raises clearly if they are absent.

The session owns an optional active Battle internally.

Submitting ENTER_ENCOUNTER or RETRY creates the active Battle and returns its first BattleView.

While a Battle is active, session submissions route only Battle semantic inputs to it.

When Battle completes, the session immediately owns victory/defeat finalization:

verify all enemies are defeated;

apply or reject rewards using existing rules;

restore checkpoint on defeat;

mark encounters and advance route on victory;

open Rest where required;

preserve Dungeon Entrance completion behavior.

A completing submission returns the final BattleView once. The next current_view() returns the resulting OverworldView.

The active Battle is discarded after finalization.

Rest, Skills, inventory, Map, Options, Save, Load, Retry, and Quit behavior remain unchanged.

SaveRepository remains a concrete dependency and is not redesigned.

The old nested _run_current_encounter() -> Battle.run() ownership is split into active-Battle creation and finalization helpers.

Canonical New Game

Add a small pure construction function:

create_new_game(drifter_id) -> GameState

It must use only:

catalog DrifterSpec
-> DrifterSpec.create_character()
-> PlayerState
-> GameState

Terminal character selection remains presentation/input glue and must yield the confirmed canonical Drifter ID to the new-game construction path rather than owning authoritative game construction. Prefer a new or renamed selection-only helper if changing Events.pick_character() would break existing callers or tests; retain a compatibility wrapper if necessary. Existing roster, profile, confirmation, and terminal output remain intact.

Gates

Gate 0 - Baseline Audit

No code changes.

From root/, run:

..\.venv\Scripts\python.exe -m pytest
..\.venv\Scripts\python.exe -m pytest tests/test_m11_session_ownership.py tests/test_m11_cross_encounter.py tests/test_m11_surface_routes.py tests/test_m11_save_continue.py
..\.venv\Scripts\python.exe -m pytest tests/test_battle_player_state.py tests/test_overworld_session.py
..\.venv\Scripts\python.exe -m compileall src tests tools
git diff --check

Record the exact HEAD and identify these existing proofs:

semantic Battle driving: test_m10c_hardening.py, test_battle_player_state.py, test_m11_surface_routes.py;

semantic Overworld driving: test_overworld_session.py, test_m11_cross_encounter.py, test_m11_surface_routes.py;

complete route: test_m11_surface_routes.py;

real CombatResolver: test_combat_resolver.py and mechanic integration tests;

victory, defeat, Retry: test_m10c_route_integration.py, test_m11_cross_encounter.py;

Rest progression: test_overworld_session.py, test_m11_surface_routes.py;

rewards: test_m10e_enemy_rewards.py, test_m10e_progression.py;

Dungeon Entrance completion: test_m10c_route_integration.py, test_m11_surface_routes.py.

Gate 1 - Step-Driven Battle

Commit:

DD-RD1 - Add Step-Driven Battle Boundary

Implement the Battle contract without changing CombatResolver or gameplay.

Focused tests must drive real Battles only through:

battle = Battle(..., ui=None, rng=deterministic_rng)
view = battle.current_view()
view = battle.submit(ChooseAction(...))
view = battle.submit(ChooseMove(...))
view = battle.submit(ChooseTarget(...))

Cover:

single-enemy construction;

multi-enemy target selection;

automatic enemy turns;

invalid and stale inputs;

Back and submenu navigation;

inventory flow where live;

victory and defeat;

final inactive view;

RNG ownership and no extra RNG consumption;

at least one real CombatResolver mechanic for each existing Drifter family;

no BattleUI, input(), print(), or terminal adapter.

Keep existing direct player_action() and run() tests green.

Gate 2 - Step-Driven Overworld Session

Commit:

DD-RD2 - Add Step-Driven Overworld Session

Implement active Battle ownership inside OverworldSession.

Focused tests must prove:

current_view() returns Overworld or Battle views correctly;

session submissions never acquire input;

Battle choices persist across calls;

final Battle views are returned once;

victory finalization remains session-owned;

defeat restores the checkpoint and exposes Retry;

Retry creates fresh enemies;

rewards are paid once;

Rest resolution remains session-owned;

route advancement and Dungeon Entrance completion remain exact;

active Battle and runtime enemy objects are discarded after completion;

invalid cross-mode inputs mutate nothing;

no Battle.run() is called by the step-driven session path.

Add no persistence fields and make no SaveRepository changes.

Gate 3 - Canonical New Game and Terminal Compatibility

Commit:

DD-RD3 - Separate New Game Construction from Terminal Input

Add create_new_game(drifter_id) and route terminal character confirmation through it.

Make the compatibility drivers use the new boundary:

Terminal UI:
render current view
read human input
translate to semantic input
submit semantic input
repeat

Battle.run() and OverworldSession.run() remain available for the existing terminal application, but their loops become convenience drivers over current_view() and submit().

Tests must prove:

all four Drifters construct through the canonical path;

profile identity and PlayerState ownership remain unchanged;

terminal startup still displays and confirms the same choices;

terminal Battle and Overworld flows still operate;

compatibility wrappers do not duplicate rewards, turns, or lifecycle work;

legacy story output remains unchanged;

no terminal strings become runtime commands.

Gate 4 - Headless Runtime Qualification

Commit:

DD-RD4 - Qualify the Semantic Runtime Boundary

Add a dedicated headless acceptance test using:

create_new_game();

canonical catalog factories;

real GameState, PlayerState, OverworldSession, and Battle;

semantic input objects only;

no TerminalBattleUI;

no TerminalOverworldUI;

no input();

no print() as control flow;

no console clearing;

no Battle.run();

no OverworldSession.run().

The qualification must drive:

new game
-> Drifter selection/construction
-> all eight encounters
-> all three Rests
-> progression
-> rewards
-> multi-enemy encounters
-> Goblin Lord
-> Dungeon Entrance

Assert:

exact encounter and Rest completion;

route completion;

final progression and reward totals;

fresh enemies per encounter;

no duplicate rewards;

defeat/Retry behavior where exercised;

no active Battle or runtime enemies at Dungeon Entrance;

no persistence or save-file access.

The full-route qualification may reuse the existing deterministic resolver strategy for route-duration control. Separate Gate 1 tests must continue to exercise real CombatResolver behavior.

Verification Protocol

For every gate:

Run focused tests.

Run the complete pytest suite.

Run:

..\.venv\Scripts\python.exe -m compileall src tests tools
git diff --check

Review the exact diff for:

gameplay drift;

CombatResolver changes;

duplicated progression or reward logic;

save-schema changes;

platform-specific abstractions;

async code;

browser, Android, Pyodide, or C++ concepts;

weakened existing tests.

Commit with the exact gate message.

Push the current branch.

Verify local and remote SHA equality.

Wait for green CI whose headSha exactly matches.

Report the SHA, focused/full totals, CI run, clean-tree state, and synchronization.

Stop for gate review before continuing.

Final Architecture Proof

The accepted dependency direction will be:

Terminal
Browser someday
Android someday
Headless tests
Future native frontend
        |
        v
semantic input/view boundary
        |
        v
OverworldSession / Battle
        |
        v
GameState / PlayerState / CombatResolver / content catalog

Intentionally deferred coupling:

terminal startup/save selection in main_loop;

legacy story/event presentation;

concrete SaveRepository dependency;

terminal compatibility loops retained by run() and player_action().

These are documented compatibility boundaries, not new gameplay authorities.

No SAVE-ARCH, content architecture, resolver, save-schema, platform, asynchronous, or gameplay changes are included.

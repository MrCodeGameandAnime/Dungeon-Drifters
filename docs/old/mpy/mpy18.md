# MPY18 - Qualify Full Surface Route Under MicroPython

**Goal:** Extend the sealed MicroPython runtime qualification from one completed session encounter to the entire authored v0.3 surface route, proving that the same authoritative `OverworldSession` / `Battle` runtime can traverse all eight encounters, resolve all three Rests, defeat the Goblin Lord, apply progression/rewards, and arrive at Dungeon Entrance under pinned MicroPython `v1.29.0`.

MPY18 is a **qualification gate**, not a compatibility-repair gate. No production behavior is expected to change.

## Baseline

```text
branch: mpy
SHA: 4ac69098c173d7fecbd590eb329c3222af00876b

MicroPython: v1.29.0
source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
platform: win32
```

Sealed MPY17 qualification:

```text
BATTLE_CONSTRUCTION         PASS
BATTLE_VIEW                 PASS
BATTLE_INPUT                PASS
BATTLE_COMPLETE             PASS
SESSION_IMPORT              PASS
SESSION_CONSTRUCTION        PASS
SESSION_VIEW                PASS
SESSION_ENCOUNTER_ENTRY     PASS
SESSION_ENCOUNTER_COMPLETE  PASS
RAW_PROBE_STAGES_COMPLETE
```

Final MPY17 memory:

```text
FREE:  669536
ALLOC: 354976
```

Dataclass census:

```text
EXPECTED:    74
DECORATED:   73
CONSTRUCTED: 33
```

MPY17 therefore establishes that a real headless `OverworldSession` can enter and complete its first encounter under pinned MicroPython.

MPY18 expands the qualification horizon to the entire authored surface route.

---

## Controlling Route Contract

Before editing, verify the live authored route and the existing CPython qualification test still agree on the exact sequence:

```text
1  surface_goblin_solo
2  surface_goblin_pair
3  surface_warrior_solo
4  surface_rest_after_warrior_solo
5  surface_warrior_pair
6  surface_shaman_solo
7  surface_shaman_pair
8  surface_rest_after_shaman_pair
9  surface_elite_patrol
10 surface_rest_before_goblin_lord
11 surface_goblin_lord
12 surface_dungeon_entrance
```

Require exactly:

```text
encounters: 8
rests:      3
bosses:     1
terminal route node: surface_dungeon_entrance
```

Expected encounter IDs:

```python
(
    "surface_goblin_solo",
    "surface_goblin_pair",
    "surface_warrior_solo",
    "surface_warrior_pair",
    "surface_shaman_solo",
    "surface_shaman_pair",
    "surface_elite_patrol",
    "surface_goblin_lord",
)
```

Expected Rest IDs:

```python
(
    "surface_rest_after_warrior_solo",
    "surface_rest_after_shaman_pair",
    "surface_rest_before_goblin_lord",
)
```

Expected compositions:

```python
(
    ("goblin",),
    ("goblin", "goblin"),
    ("goblin_warrior",),
    ("goblin_warrior", "goblin_warrior"),
    ("goblin_shaman",),
    ("goblin_shaman", "goblin_shaman"),
    ("goblin_elite", "goblin"),
    ("goblin_lord", "goblin", "goblin_warrior"),
)
```

Stop before implementation if the live route or `test_runtime_qualification.py` differs from this contract.

Do not rewrite the probe around stale assumptions.

---

# Qualification Strategy

Do **not** create a second gameplay runtime and do not duplicate route progression logic.

Extend the existing:

```text
root/tools/micropython_probe.py
```

so that its currently sealed stages remain intact and run first.

After:

```text
SESSION_ENCOUNTER_COMPLETE
```

construct a **fresh** Branoc game and fresh headless session specifically for full-route qualification.

Do not reuse the first probe game because that game has already participated in standalone Battle and first-session qualification.

The route qualification therefore begins from:

```python
create_new_game("branoc")
```

again.

The existing bootstrap remains authoritative:

```text
root/tools/micropython_probe_bootstrap.py
```

and must not change.

This means the same expanded probe runs under:

```text
native CPython
forced-overlay CPython
pinned MicroPython
```

with the same route assertions.

---

# Deterministic Qualification Harness

The full-route probe is intended to qualify:

```text
session orchestration
battle lifecycle
enemy construction
semantic input flow
encounter finalization
reward application
rest resolution
route advancement
persistent in-memory state
terminal route state
```

It is **not** a stochastic combat-balance test.

MPY17 already proved the default production RNG/CombatResolver path through a real session encounter.

For MPY18, use a deterministic qualification Battle factory equivalent to the already-sealed CPython runtime qualification test.

## Deterministic RNG

Reuse or extend the existing probe `_DeterministicRng`:

```python
class _DeterministicRng:
    def randint(self, start, _end):
        return start

    def choice(self, options):
        return tuple(options)[0]
```

Do not change the production random adapter.

## Deterministic resolver

Add a probe-only resolver equivalent to the existing `test_runtime_qualification.py` oracle.

Its contract:

```text
accepted: True
hit: True
resource spent: 0
healing: 0
statuses: ()
```

When the target is a living enemy:

```text
damage = target.health.current
```

so each selected enemy is defeated immediately.

When the target is not a living enemy:

```text
damage = 0
```

Use the production:

```text
app.combat.result.MoveResult
```

Do not create a fake result type.

## Route Battle factory

Add a probe-only factory that constructs the real:

```text
app.combat.battle.Battle
```

with:

```text
ui=None
deterministic resolver
deterministic RNG
real PlayerState
real EnemyState instances
real BattlePresenter
real BattlePresentationSession
real OverworldSession integration
```

Record every constructed Battle.

## Enemy factory

Use the authoritative catalog:

```python
create_enemy_state(archetype_id, tier=0)
```

Record every produced enemy object.

Do not stub enemy state.

---

# Preserve the Existing Raw Probe

The existing stages through MPY17 are sealed.

Do not weaken, replace, or shortcut:

```text
SOURCE_PATH
CATALOG_IMPORT
DRIFTER_SPEC
NEW_GAME
FIRST_ENCOUNTER
ENEMY_STATE
BATTLE_CONSTRUCTION
BATTLE_VIEW
BATTLE_INPUT
BATTLE_COMPLETE
SESSION_IMPORT
SESSION_CONSTRUCTION
SESSION_VIEW
SESSION_ENCOUNTER_ENTRY
SESSION_ENCOUNTER_COMPLETE
```

In particular, do not replace the current real session Battle construction with the deterministic full-route factory merely to make the later route easier.

The full-route qualification is **additional evidence**.

---

# Full Route Driver

After the current `SESSION_ENCOUNTER_COMPLETE` stage, add a fresh route qualification stage.

Recommended structure:

```text
ROUTE_CONSTRUCTION
ROUTE_INITIAL_VIEW
SURFACE_ROUTE_COMPLETE
ROUTE_FINAL_STATE
```

Inside `SURFACE_ROUTE_COMPLETE`, emit explicit node markers before and after every authored route node.

For example:

```text
MPY|ROUTE|surface_goblin_solo|BEGIN
MPY|ROUTE|surface_goblin_solo|PASS

MPY|ROUTE|surface_goblin_pair|BEGIN
MPY|ROUTE|surface_goblin_pair|PASS
...
```

If a node fails, emit:

```text
MPY|ROUTE|<node_id>|FAIL|<ExceptionType>|<message>
```

before propagating the exception.

This gives MPY19 and any future compatibility gate an exact route frontier rather than merely:

```text
SURFACE_ROUTE_COMPLETE failed somewhere
```

---

# Encounter Driver

For each combat or boss node:

1. Require:

```text
session.current_view().screen == OverworldScreen.MAIN
```

2. Require the current route node ID to equal the expected hardcoded node.

3. Require:

```text
contextual_route_option.action is OverworldAction.ENTER_ENCOUNTER
```

4. Record the encounter ID.

5. Submit:

```python
ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
```

6. Drive the resulting Battle semantically using only offered view state:

```text
ACTIONS
→ ChooseAction("attack")

REGULAR_MOVES
→ first enabled move option
→ ChooseMove(selection_key)

TARGETS
→ first enabled target
→ ChooseTarget(target_id)
```

7. Continue until:

```text
InteractionPhase.COMPLETE
```

Use a finite safety bound.

Recommended:

```text
100 semantic inputs maximum per encounter
```

If exceeded:

```text
AssertionError
```

Do not inspect Battle internals to choose moves or targets.

8. Call:

```python
session.current_view()
```

to ensure finalization has occurred.

9. Require that the completed encounter is appended exactly once to:

```text
game.world_state.defeated_encounters
```

10. Require:

```text
session.active_battle is None
```

before advancing to the next route node.

---

# Rest Driver

For every authored Rest:

```text
surface_rest_after_warrior_solo
surface_rest_after_shaman_pair
surface_rest_before_goblin_lord
```

Require:

```text
current route node ID == expected Rest ID
screen == OverworldScreen.REST
```

The resulting Rest view must retain the currently authored semantics.

Do not rewrite Rest behavior into probe-only shortcuts.

Resolve the Rest through the semantic session input:

```python
ChooseOverworldAction(OverworldAction.REST)
```

Then require:

```text
the Rest ID was recorded exactly once
screen returns to MAIN
route advances to the immediate authored successor
```

The route probe should exercise actual HP/Mana Rest restoration even though the deterministic combat resolver is unlikely to damage the player.

Do not use `SKIP_REST` for this qualification.

The gate is specifically proving all three normal Rest-resolution paths.

---

# Prefix Invariants During Traversal

Do not wait until Dungeon Entrance to verify everything.

After each completed encounter, require:

```text
world_state.defeated_encounters
==
expected encounter prefix
```

For example, after Warrior Solo:

```python
(
    "surface_goblin_solo",
    "surface_goblin_pair",
    "surface_warrior_solo",
)
```

After each resolved Rest, require:

```text
overworld_state.resolved_rest_node_ids
==
expected Rest prefix
```

This catches route corruption at its actual source.

Also require every advancement to be the immediate authored successor.

Do not allow the probe to “eventually reach” the expected node after an incorrect intermediate transition.

---

# Enemy And Battle Ownership Qualification

At route completion require exactly:

```text
8 Battle instances
14 EnemyState instances
```

Require the Battle compositions to equal:

```python
(
    ("goblin",),
    ("goblin", "goblin"),
    ("goblin_warrior",),
    ("goblin_warrior", "goblin_warrior"),
    ("goblin_shaman",),
    ("goblin_shaman", "goblin_shaman"),
    ("goblin_elite", "goblin"),
    ("goblin_lord", "goblin", "goblin_warrior"),
)
```

Prove all fourteen enemy objects are distinct.

Do this portably with identity comparison rather than relying on implementation-specific `id()` behavior:

```python
for index, enemy in enumerate(enemies):
    for previous in enemies[:index]:
        if enemy is previous:
            raise AssertionError("route reused an EnemyState instance")
```

Require every recorded Battle to finish at:

```text
InteractionPhase.COMPLETE
```

and require:

```text
session.active_battle is None
```

at Dungeon Entrance.

---

# Final Route State

At completion require exactly:

```text
current_route_node_id == "surface_dungeon_entrance"
route_complete is True
dungeon_entrance_reached is True
```

World state:

```python
defeated_encounters == (
    "surface_goblin_solo",
    "surface_goblin_pair",
    "surface_warrior_solo",
    "surface_warrior_pair",
    "surface_shaman_solo",
    "surface_shaman_pair",
    "surface_elite_patrol",
    "surface_goblin_lord",
)
```

Rest state:

```python
resolved_rest_node_ids == (
    "surface_rest_after_warrior_solo",
    "surface_rest_after_shaman_pair",
    "surface_rest_before_goblin_lord",
)
```

Final player progression must equal the existing CPython qualification oracle:

```text
Level:         9
EXP:           68
Growth Points: 24
Gold:          75
```

Final view must satisfy:

```text
screen == OverworldScreen.MAIN
contextual_route_option is None
```

No post-route encounter or Rest action may remain available.

---

# Persistence Boundary

MPY18 must remain entirely in-memory.

Construct the route session with:

```text
save_repository=None
```

Do not import or instantiate:

```text
SaveRepository
tempfile
pathlib
shutil
```

during the route qualification.

At the end require the route session has not materialized its lazy disk repository.

The probe may assert:

```python
STATE["route_session"]._save_repository is None
```

because this is qualification tooling, not production API code.

Do not visit the Options/save/load screens.

The existing CPython `test_runtime_qualification.py` remains authoritative for the filesystem-side assertion that no save file is created during normal headless route traversal.

---

# Memory Evidence

MPY18 is not yet the memory-pressure gate, but collect evidence while the complete route is running.

For every route node emit:

```text
memory BEFORE
memory AFTER
```

using the existing probe `_emit_memory()`.

At minimum preserve measurements for:

```text
ROUTE_CONSTRUCTION
each of 8 encounters
each of 3 Rests
Dungeon Entrance
ROUTE_FINAL_STATE
```

Do **not** introduce pass/fail memory thresholds in MPY18.

That belongs to MPY19.

MPY18 fails only if the runtime actually cannot complete due to memory/runtime failure.

---

# Dataclass Evidence

Continue using the existing bootstrap census.

Do not predict the final constructed count.

Require only:

```text
EXPECTED == 74
manifest remains current
```

Report the actual final:

```text
DECORATED
CONSTRUCTED
```

after full-route qualification.

If full-route traversal causes additional dataclass types to be constructed, that is evidence, not a problem.

---

# Probe Contract Test

Create:

```text
root/tests/test_micropython_route_probe_contract.py
```

This is a tooling-contract test, not a duplicate runtime test.

It should parse:

```text
root/tools/micropython_probe.py
```

and permanently require:

1. The sealed MPY17 stage sequence remains the exact prefix through:

```text
SESSION_ENCOUNTER_COMPLETE
```

2. Full-route qualification occurs only **after** that prefix.

3. The hardcoded expected route node sequence contains exactly the twelve authored nodes in order.

4. Expected encounter count is 8.

5. Expected Rest count is 3.

6. Expected enemy count is 14.

7. Expected final node is:

```text
surface_dungeon_entrance
```

8. Expected final progression constants remain:

```text
level 9
exp 68
growth points 24
gold 75
```

9. The raw probe does not import:

```text
pytest
tempfile
pathlib
shutil
SaveRepository
```

10. No filesystem scanning, save-file creation, or test-framework dependency is added.

Synthetic AST cases are not necessary unless a reusable classifier is introduced.

Keep this test focused on the qualification artifact itself.

---

# Existing CPython Authority

Do not change the expectations in:

```text
root/tests/test_runtime_qualification.py
```

unless the live authoritative game behavior has already changed independently of MPY18.

That test remains the CPython semantic oracle for:

```text
8 encounters
3 Rests
14 fresh enemies
Dungeon Entrance
Level 9
EXP 68
GP 24
Gold 75
no persistence
```

Also retain the route/state regression coverage in:

```text
tests/test_m11_surface_routes.py
tests/test_m10c_route_integration.py
tests/test_overworld_session.py
tests/test_overworld_state.py
```

MPY18 should prove the MicroPython runtime reaches the same outcome, not redefine the outcome.

---

# Verification

Run the full suite from `root`.

Then run the exact sealed MPY17 cumulative suite plus MPY18 route qualification coverage:

```powershell
Push-Location root

& ..\.venv\Scripts\python.exe -m pytest `
  tests\test_dataclass_contract.py `
  tests\test_portable_dataclasses.py `
  tests\test_enum_contract.py `
  tests\test_portable_enum.py `
  tests\test_keyword_contract.py `
  tests\test_portable_keyword.py `
  tests\test_regex_contract.py `
  tests\test_portable_regex.py `
  tests\test_collections_contract.py `
  tests\test_portable_collections_abc.py `
  tests\test_string_contract.py `
  tests\test_portable_string_validation.py `
  tests\test_portable_counter_removal.py `
  tests\test_typing_contract.py `
  tests\test_portable_typing.py `
  tests\test_battle_presentation_session.py `
  tests\test_starred_tuple_contract.py `
  tests\test_character_profiles.py `
  tests\test_terminal_battle_ui.py `
  tests\test_strict_zip_contract.py `
  tests\test_save_contract.py `
  tests\test_session_persistence_boundary.py `
  tests\test_save_repository.py `
  tests\test_overworld_session.py `
  tests\test_runtime_overworld.py `
  tests\test_m10b_map_inspection.py `
  tests\test_itertools_contract.py `
  tests\test_next_default_contract.py `
  tests\test_overworld_presenter.py `
  tests\test_battle_presenter.py `
  tests\test_item_first_inventory.py `
  tests\test_inventory_action_resolver.py `
  tests\test_random_contract.py `
  tests\test_combat_resolver.py `
  tests\test_runtime_battle.py `
  tests\test_battle_player_state.py `
  tests\test_heal_action.py `
  tests\test_battle_ui_hardening.py `
  tests\test_micropython_route_probe_contract.py `
  tests\test_runtime_qualification.py `
  tests\test_m11_surface_routes.py `
  tests\test_m10c_route_integration.py `
  tests\test_overworld_state.py

Pop-Location
```

Report the actual total.

Do not predict it.

Run:

```powershell
.\.venv\Scripts\python.exe -m compileall `
  root\src `
  root\tests `
  root\tools `
  root\portability

.\.venv\Scripts\python.exe `
  root\tools\generate_dataclass_manifest.py --check

git diff --check
```

---

# Three Runtime Qualifications

Run the expanded probe in all three modes.

## 1. Native CPython

Require:

```text
all original stages PASS
all route nodes PASS
SURFACE_ROUTE_COMPLETE PASS
ROUTE_FINAL_STATE PASS
RAW_PROBE_STAGES_COMPLETE
```

## 2. Forced-overlay CPython

Require the same result.

This is important because the expanded route exercises much more of the overlay-backed runtime than MPY17 did.

## 3. Pinned MicroPython v1.29.0

Require the same functional route outcome:

```text
8 encounters
3 Rests
Goblin Lord
Dungeon Entrance
Level 9
EXP 68
GP 24
Gold 75
14 fresh enemies
no active Battle
no persistence materialization
```

and finally:

```text
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

After MPY18, that marker now means the **expanded full-route probe**, not merely the MPY17 first-encounter probe.

Document that semantic expansion explicitly.

---

# Expected Diff

Expected tooling:

```text
MODIFY
root/tools/micropython_probe.py
```

Expected tests:

```text
CREATE
root/tests/test_micropython_route_probe_contract.py
```

Expected documentation:

```text
MODIFY
docs/portability/micropython-probe.md
```

Expected production changes:

```text
NONE
```

Final scope:

```text
production source files changed:       0
gameplay code changed:                 0
combat rules changed:                  0
route/content changed:                 0
session implementation changed:        0
persistence/schema changed:            0
compatibility overlays changed:        0
bootstrap changed:                     0
MicroPython source/config changed:     0
new runtime compatibility primitive:   0

raw qualification horizon:
  1 session encounter
  ->
  full 12-node surface route

encounters qualified:                  8
rests qualified:                       3
enemy instances qualified:            14
boss qualified:                        Goblin Lord
terminal node qualified:               Dungeon Entrance
historical docs/mpy changes:           0
```

---

# Documentation

Update:

```text
docs/portability/micropython-probe.md
```

Record sealed MPY17:

```text
4ac69098c173d7fecbd590eb329c3222af00876b
MPY17 - Repair Portable Runtime Random Boundary
```

and its completion evidence:

```text
SESSION_ENCOUNTER_ENTRY     PASS
SESSION_ENCOUNTER_COMPLETE  PASS
RAW_PROBE_STAGES_COMPLETE
```

Then document MPY18:

```text
exact 12-node route oracle
8 encounter IDs
3 Rest IDs
8 encounter compositions
14 fresh EnemyState instances
deterministic route qualification harness
why deterministic combat is used
why MPY17 already covers default runtime RNG
semantic battle-input driver
prefix-state assertions
reward/progression assertions
Dungeon Entrance final state
no persistence materialization
native CPython result
forced-overlay CPython result
pinned MicroPython result
per-node memory observations
lowest FREE
highest ALLOC
final FREE/ALLOC
final dataclass census
full test total
cumulative test total
scope counts
```

Explicitly distinguish:

```text
MPY17
→ real default session Battle/RNG/CombatResolver first-encounter qualification

MPY18
→ deterministic full-route orchestration/state/progression qualification
```

Do not claim MPY18 proves statistically representative combat balance under MicroPython.

That is not the purpose of this gate.

---

# Stop Conditions

Stop and request a revised MPY18 plan if:

```text
the live authored route differs from the controlling 12-node contract

the CPython runtime qualification oracle no longer ends at
Level 9 / EXP 68 / GP 24 / Gold 75

full-route qualification requires a production source change

full-route qualification requires a new compatibility overlay

the bootstrap must be changed

persistence must be imported or instantiated

route completion requires bypassing OverworldSession

combat completion requires mutating enemy/player state outside Battle/session APIs

the deterministic probe produces behavior inconsistent with the existing
CPython runtime qualification test
```

If pinned MicroPython fails on a new language/runtime incompatibility during the expanded route:

```text
do not repair it inside MPY18
```

Record:

```text
last completed route node
failing route node
exception type/message
original traceback
FREE
ALLOC
dataclass census
```

and stop before release.

Unlike MPY14-MPY17, MPY18's actual goal is **full-route completion**, so a newly exposed incompatibility means MPY18 is not yet complete.

Derive a new evidence-backed compatibility gate from that failure.

---

# Success Condition

MPY18 succeeds only when all three environments independently reach:

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

with the authoritative final state:

```text
8 defeated encounters
3 resolved Rests
14 fresh enemies
Level 9
EXP 68
GP 24
Gold 75
route_complete = True
dungeon_entrance_reached = True
active_battle = None
```

and:

```text
MPY|RESULT|RAW_PROBE_STAGES_COMPLETE
```

---

# Future Gates

If MPY18 passes without exposing another compatibility wall:

```text
MPY19  Constrained-target memory and runtime pressure.

MPY20  Cross-runtime regression qualification and campaign closure.
```

MPY19 should use the per-node memory evidence generated here as its baseline rather than inventing thresholds before observing the full route.

---

# Release

Commit exactly:

```text
MPY18 - Qualify Full Surface Route
```

Push:

```text
mpy
```

Then verify:

```text
local HEAD == origin/mpy
tracked worktree clean
exact-SHA CI successful
historical docs/mpy files untouched and uncommitted
```

Final report must include:

```text
commit SHA/message
full-suite total
cumulative-suite total
native CPython expanded probe result
forced-overlay expanded probe result
pinned MicroPython expanded probe result
all 12 route-node markers
8 encounter IDs
3 Rest IDs
8 encounter compositions
Battle count
enemy count and identity result
final player progression
final route/world state
persistence materialization result
lowest FREE
highest ALLOC
final FREE/ALLOC
final dataclass census
CI run/conclusion
local/origin synchronization
tracked worktree state
historical docs/mpy preservation
```

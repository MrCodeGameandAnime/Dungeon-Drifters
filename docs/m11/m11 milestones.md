# M11 - Session Integrity and Regression

M11 is a regression and acceptance milestone, not another feature-building
milestone. It proves that the M9 and M10 systems operate as one connected
object graph.

## Baseline and Authority

```text
Branch: v0.2.11
Baseline: d74f19da38c0fddbe26a721cd519cd260e4f44eb
master: d74f19da38c0fddbe26a721cd519cd260e4f44eb
Branch divergence: 0 commits ahead, 0 commits behind
```

The M11 roadmap authority is the M11 section of `docs/v0.3 milestones.md`.
M9 and M10 behavior remains governed by their accepted contracts. M11 must
not silently redefine those contracts.

The persistent ownership chain is:

```text
CharacterProfile
-> Character
-> PlayerState
-> GameState
-> OverworldSession
```

## Gate Strategy

The four-Drifter full-route proof uses layered integration:

```text
real profiles, PlayerState, GameState, OverworldSession, route manifest,
EnemyState construction, rewards, Rest, snapshots, and presentation
-> deterministic Battle boundary for route completion
-> separate real Battle and CombatResolver proofs for mechanics and cleanup
```

This proves the complete session without turning M11 into a balance or enemy
AI milestone. Real-Battle tests use injected deterministic RNG and semantic
inputs; they do not use global-random monkeypatching as the primary seam.

Production changes are allowed only when an acceptance test exposes a narrow
defect. Do not add speculative infrastructure or duplicate persistent owners.

## M11-1 - Session Ownership and Snapshot Integrity

Commit:

```text
M11-1 - Prove Session Ownership and Snapshot Integrity
```

For Branoc, Azhvielle, Zhaivra, and Joruun, prove:

```text
select profile
-> create Character
-> create PlayerState
-> create GameState
-> enter OverworldSession
-> enter one encounter
-> return to the overworld
```

The selected canonical profile, Character, PlayerState, Health, Mana, Super,
Inventory, CharacterRunState, and every equipped object must remain the same
live objects through the Battle boundary. No second persistent state owner may
appear.

Create independent sessions and prove mutation of one session cannot alter the
other session's:

- progression, EXP, Growth Points, or level objects
- permanent stats or resources
- Super, gold, inventory, equipment, or run state
- prepared payloads
- StoryState, WorldState, or OverworldState

For every Drifter, create meaningful persistent state and assert exact schema-7
inspection snapshot values for:

- profile identity and archetype
- permanent stats
- level and EXP
- Growth Points
- current and maximum HP and Mana
- Super
- gold
- persistent inventory
- signature weapon and equipment slots
- CharacterRunState quantities and prepared Infusion
- StoryState and WorldState
- current route position and phase
- defeated encounters and resolved Rest IDs
- metadata

Snapshots must be defensive, deterministic, plain JSON values. They must not
contain Battle, CombatState, CombatResolver, presenters, terminal UI, open
menus, RNG objects, runtime enemies, object references, or temporary statuses.

The equipment proof remains within the M10 contract:

```text
signature weapon belongs to the correct PlayerState
-> effective bonuses are present
-> permanent base stats remain unchanged
-> Weapon inspection is truthful and non-mutating
-> unequipping removes effective bonuses
-> another session remains unchanged
```

No accessory system, weapon progression, replacement, refinement, or new item
behavior is added.

## M11-2 - Cross-Encounter State Integrity

Commit:

```text
M11-2 - Prove Cross Encounter State Integrity
```

Using real Battle and CombatState objects, prove persistent state survives the
correct boundaries:

- current HP and Mana
- Super
- EXP, level, and Growth Points
- gold
- permanent stats
- equipment and inventory
- CharacterRunState and prepared Infusion according to its owner contract
- route, defeated encounter, Rest, Story, and World state

Prove encounter-local state is cleaned or discarded correctly:

- Defend and Brace protection
- Gravemantle Break target links
- Arcane Overcharge and Instability
- Frost, Frozen, Burn, Poison, Stun, Conductive, and Turbulence
- Heal cooldowns and turn counters
- defeated enemy runtime objects and enemy-owned statuses
- current combat logs and final action availability

Defeated combatants receive immediate cleanup while unrelated living-combatant
state remains unchanged. At the session boundary, the old Battle and
CombatState become unreachable and the next Battle receives a fresh
CombatState. M11 must not require surviving-player entries to be erased from a
discarded object that no longer belongs to the session.

Prove duplicate-enemy identity, target-specific statuses, defeated-enemy
skipping, stable labels, exact Break linkage, and different-target Overcharge.

Prove defeat and Retry for:

- one ordinary encounter
- Goblin Pair
- Goblin Lord

Each defeat must restore the same PlayerState graph in place, grant no reward,
record no completion, remain at the current node, expose Retry, and create
fresh enemy runtime objects. A later victory must award exactly once.

Every terminal Battle must be inactive, show the final states, and expose no
actionable controls.

## M11-3 - Four-Drifter Full Surface Sessions

Commit:

```text
M11-3 - Prove Four Drifter Surface Sessions
```

Run the complete authored surface route for all four Drifters with real
session, route, enemy construction, reward, Rest, and presentation systems.
Use deterministic Battle completion for the full matrix and real Battle tests
for representative mechanics.

The fixed Rest matrix is:

```text
Branoc:    Rest, Rest, Rest
Azhvielle: Skip, Skip, Skip
Zhaivra:   Rest, Skip, Rest
Joruun:    Skip, Rest, Skip
```

Every route must prove:

- all eight encounters and exactly 14 independent runtime enemy instances
- authored composition and ordering
- rewards paid once and never for defeat, incomplete victory, or duplication
- all three Rest IDs resolved in authored order
- Goblin Lord completion exactly once
- Dungeon Entrance reached with no continuation
- the original PlayerState identity and persistent values preserved
- inventory, Character, Skills, Weapon, Equipment, and Map views remain valid
- final state is serializable

The expected endpoint without stat spending is:

```text
Level: 9
EXP: 68
Growth Points: 24
Gold: 75
Defeated encounters: 8
Resolved Rest nodes: 3
Current node: Dungeon Entrance
Route complete: true
```

Representative real-Battle coverage includes all four Drifter mechanic
families, Heal, Defend, Super gating, insufficient Mana, misses, invalid
inputs, dead-enemy suppression, simultaneous death, target attribution,
turn-scoped logs, and inactive final views. Terminal rendering is checked for
ordinary, multi-enemy, and boss encounters without raw IDs or stale output.

## M11-4 - Save, Exit, Load, and Continue

Commit:

```text
M11-4 - Prove Save Exit Load Continue
```

Use the actual SaveRepository and isolated temporary paths. Test saves at:

- before the surface route begins
- an unresolved combat node
- an unresolved Rest boundary
- after completed encounters
- near Goblin Lord
- Dungeon Entrance after route completion

For all four Drifters, prove loaded reconstruction restores the canonical
profile and exact level, EXP, Growth Points, gold, HP, Mana, Super, permanent
stats, signature weapon, inventory, run state, prepared payload, Story, World,
route position, contextual phase, defeated encounters, and resolved Rests.

Prove startup Load bypasses character selection, returns to Main, creates a
fresh isolated GameState, reconstructs no Battle or runtime enemy, and permits
continuation into the next encounter. Previous rewards must not be paid again;
the loaded session must be able to save again.

The central acceptance path must also be proven as one split campaign, not as
separate startup and continuation tests:

```text
Session A:
start a new surface route
complete several encounters
resolve at least one Rest
save through Options
quit

Session B:
restart startup
choose Load
confirm the first Overworld screen is Main
continue every remaining encounter
defeat Goblin Lord
reach Dungeon Entrance
save again
```

The resumed campaign must finish at Level 9, 68 EXP, 24 Growth Points, and
75 gold, with exactly eight defeated encounters, three resolved Rest nodes,
Dungeon Entrance current, and route completion true.

Retain cumulative proofs for:

- missing save -> normal new-game flow
- invalid save -> concise error, untouched file, no partial mutation
- unsupported future schema -> rejection
- schema 7 -> in-memory migration without automatic rewrite

Do not add save slots, autosave, cloud saves, configurable paths, Battle
serialization, schema 9, or a general persistence framework.

## Verification and Stop Protocol

At every gate:

1. Run focused M11 tests.
2. Run the complete pytest suite.
3. Run `python -m compileall src tests`.
4. Run `git diff --check`.
5. Review the exact diff for weakened tests, duplicate state, and M12 leakage.
6. Commit with the exact gate name.
7. Push `v0.2.11`.
8. Verify local and remote SHA equality.
9. Wait for green CI whose `headSha` exactly matches.
10. Report the SHA, test totals, CI run, and clean-tree result.
11. Stop for gate review before beginning the next gate.

## Final Acceptance

Run the complete focused M11 suite, the full pytest suite, compileall, and
diff-check. Review the cumulative M11 commit chain and confirm:

1. One authoritative GameState owns each active session.
2. One authoritative PlayerState owns each selected Drifter.
3. Persistent mutations survive the correct boundaries.
4. Temporary mutations die at the correct boundaries.
5. Enemy and status state remains identity-isolated.
6. Every Drifter completes the surface route.
7. Goblin Lord completion occurs exactly once.
8. Save, exit, load, and continuation preserve the session.
9. Independent sessions share no mutable state.
10. Presentation remains valid before, during, and after combat.

M11 is complete and sealed. It stops at Dungeon Entrance after the Goblin Lord
victory. M12 is documentation and release closure only; entering the dungeon,
companion recruitment, and party state belong to post-v0.3 work.

# M11 - Session Integrity and Regression

M11 proves the complete M9 and M10 session object graph. It does not add new
content systems.

## Authority

The M11 roadmap authority is the M11 section of `docs/v0.3 milestones.md`.
M9 and M10 behavior remains governed by their accepted contracts.

## Gates

### M11-1 - Session Ownership and Snapshot Integrity

Prove the canonical chain for all four Drifters:

```text
CharacterProfile -> Character -> PlayerState -> GameState -> OverworldSession
```

The same persistent owner graph must survive character selection, one Battle
handoff, and return to the overworld. Independent sessions must not share
mutable state.

Schema-7 inspection snapshots must contain all persistent player, story, world,
overworld, and metadata state as defensive plain values. They must not contain
Battle, CombatState, resolver, UI, presenter, RNG, enemy runtime, menu, object
reference, or temporary status state.

Signature-weapon ownership, effective bonuses, permanent-stat separation,
inspection, and isolation remain within the existing M10 equipment contract.

### M11-2 - Cross-Encounter State Integrity

Prove persistent values survive encounter boundaries while temporary combat
state is cleaned or discarded correctly. Prove target isolation, defeated
combatant cleanup, defeat rollback, Retry, and fresh enemy construction.

### M11-3 - Four-Drifter Surface Sessions

Run the complete authored surface route for every Drifter. Stop at Dungeon
Entrance. Prove rewards, Rest, route completion, identity preservation,
presentation, logs, universal actions, and inactive final Battle views.

### M11-4 - Save Exit Load Continue

Prove actual schema-8 save and load boundaries, startup loading, fresh canonical
reconstruction, continuation, reward non-duplication, invalid and missing save
behavior, future-schema rejection, and schema-7 in-memory migration.

M12 remains blocked until all M11 gates and cumulative acceptance are green.

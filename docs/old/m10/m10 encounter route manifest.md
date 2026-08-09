````markdown
# M10 Encounter Route Manifest

## Status

Approved M10 route contract.

This document defines the authored surface-route node order, stable IDs, encounter compositions, rewards, boss designation, route completion behavior, and next destinations.

It does not define runtime class names, persistence fields, menu ownership, multi-enemy turn resolution, rest recovery values, or save-file structure.

---

# Route Summary

The M10 surface route contains:

- 8 combat encounters
- 3 rest nodes
- 1 dungeon-entrance endpoint

The route is linear.

The player cannot bypass a combat encounter and advance to a later route node.

M10 ends when the player reaches the dungeon entrance after defeating the Goblin Lord encounter.

---

# Stable Node Order

| Order | Node ID                           | Node Type        |
|-------|-----------------------------------|------------------|
|     1 | `surface_goblin_solo`             | Combat           |
|     2 | `surface_goblin_pair`             | Combat           |
|     3 | `surface_warrior_solo`            | Combat           |
|     4 | `surface_rest_after_warrior_solo` | Rest             |
|     5 | `surface_warrior_pair`            | Combat           |
|     6 | `surface_shaman_solo`             | Combat           |
|     7 | `surface_shaman_pair`             | Combat           |
|     8 | `surface_rest_after_shaman_pair`  | Rest             |
|     9 | `surface_elite_patrol`            | Combat           |
|    10 | `surface_rest_before_goblin_lord` | Rest             |
|    11 | `surface_goblin_lord`             | Boss Combat      |
|    12 | `surface_dungeon_entrance`        | Dungeon Entrance |


These IDs are stable authored identifiers.

Display labels may differ from these IDs.

---

# Node Manifest

## 1. Goblin Solo

```text
Node ID: surface_goblin_solo
Encounter ID: surface_goblin_solo
Node Type: Combat
Boss: No
````

Composition, in authored order:

```text
1. goblin
```

Rewards:

```text
EXP: 40
Gold: 3
```

Completion:

```text
Victory clears the encounter.
Defeat does not clear the encounter.
```

Next destination:

```text
surface_goblin_pair
```

---

## 2. Goblin Pair

```text
Node ID: surface_goblin_pair
Encounter ID: surface_goblin_pair
Node Type: Combat
Boss: No
```

Composition, in authored order:

```text
1. goblin
2. goblin
```

Rewards:

```text
EXP: 80
Gold: 6
```

Completion:

```text
Victory requires defeating both Goblins.
Defeat does not clear the encounter.
```

Next destination:

```text
surface_warrior_solo
```

---

## 3. Goblin Warrior Solo

```text
Node ID: surface_warrior_solo
Encounter ID: surface_warrior_solo
Node Type: Combat
Boss: No
```

Composition, in authored order:

```text
1. goblin_warrior
```

Rewards:

```text
EXP: 60
Gold: 5
```

Completion:

```text
Victory clears the encounter.
Defeat does not clear the encounter.
```

Next destination:

```text
surface_rest_after_warrior_solo
```

---

## 4. Rest After Warrior Solo

```text
Node ID: surface_rest_after_warrior_solo
Node Type: Rest
Boss: No
```

Placement:

```text
After surface_warrior_solo
Before surface_warrior_pair
```

Completion:

```text
The node is resolved according to the M10 Rest Contract.
```

Next destination:

```text
surface_warrior_pair
```

---

## 5. Goblin Warrior Pair

```text
Node ID: surface_warrior_pair
Encounter ID: surface_warrior_pair
Node Type: Combat
Boss: No
```

Composition, in authored order:

```text
1. goblin_warrior
2. goblin_warrior
```

Rewards:

```text
EXP: 120
Gold: 10
```

Completion:

```text
Victory requires defeating both Goblin Warriors.
Defeat does not clear the encounter.
```

Next destination:

```text
surface_shaman_solo
```

---

## 6. Goblin Shaman Solo

```text
Node ID: surface_shaman_solo
Encounter ID: surface_shaman_solo
Node Type: Combat
Boss: No
```

Composition, in authored order:

```text
1. goblin_shaman
```

Rewards:

```text
EXP: 90
Gold: 7
```

Completion:

```text
Victory clears the encounter.
Defeat does not clear the encounter.
```

Next destination:

```text
surface_shaman_pair
```

---

## 7. Goblin Shaman Pair

```text
Node ID: surface_shaman_pair
Encounter ID: surface_shaman_pair
Node Type: Combat
Boss: No
```

Composition, in authored order:

```text
1. goblin_shaman
2. goblin_shaman
```

Rewards:

```text
EXP: 180
Gold: 14
```

Completion:

```text
Victory requires defeating both Goblin Shamans.
Defeat does not clear the encounter.
```

Next destination:

```text
surface_rest_after_shaman_pair
```

---

## 8. Rest After Shaman Pair

```text
Node ID: surface_rest_after_shaman_pair
Node Type: Rest
Boss: No
```

Placement:

```text
After surface_shaman_pair
Before surface_elite_patrol
```

Completion:

```text
The node is resolved according to the M10 Rest Contract.
```

Next destination:

```text
surface_elite_patrol
```

---

## 9. Goblin Elite Patrol

```text
Node ID: surface_elite_patrol
Encounter ID: surface_elite_patrol
Node Type: Combat
Boss: No
```

Composition, in authored order:

```text
1. goblin_elite
2. goblin
```

Rewards:

```text
EXP: 190
Gold: 12
```

Completion:

```text
Victory requires defeating both enemies.
Defeat does not clear the encounter.
```

Next destination:

```text
surface_rest_before_goblin_lord
```

---

## 10. Rest Before Goblin Lord

```text
Node ID: surface_rest_before_goblin_lord
Node Type: Rest
Boss: No
```

Placement:

```text
After surface_elite_patrol
Before surface_goblin_lord
```

Completion:

```text
The node is resolved according to the M10 Rest Contract.
```

Next destination:

```text
surface_goblin_lord
```

---

## 11. Goblin Lord

```text
Node ID: surface_goblin_lord
Encounter ID: surface_goblin_lord
Node Type: Boss Combat
Boss: Yes
```

Composition, in authored order:

```text
1. goblin_lord
2. goblin
3. goblin_warrior
```

Rewards:

```text
EXP: 300
Gold: 18
```

Completion:

```text
Victory requires defeating all three enemies.
Defeat does not clear the encounter.
Clearing this encounter unlocks the dungeon entrance.
```

Next destination:

```text
surface_dungeon_entrance
```

This is the only Goblin Lord encounter in M10.

There is no rematch, reinforcement phase, transformation, or second boss encounter.

---

## 12. Dungeon Entrance

```text
Node ID: surface_dungeon_entrance
Node Type: Dungeon Entrance
Boss: No
```

Composition:

```text
None
```

Rewards:

```text
None
```

Completion:

```text
Reaching this node completes the M10 surface route.
```

Next destination:

```text
None inside M10.
```

M10 stops at the dungeon entrance.

Entering or exploring the dungeon belongs to a later milestone.

---

# Route Advancement Rules

Combat nodes advance only after victory.

A combat node remains uncleared after defeat.

Multi-enemy combat nodes are not cleared when only one enemy is defeated.

A multi-enemy combat node is cleared only when every enemy in its authored composition is defeated.

Rest nodes do not contain enemies and do not award EXP or gold.

The exact recovery, cost, use, and skip rules for rest nodes are defined by the separate M10 Rest Contract.

The dungeon entrance is an endpoint, not a combat encounter.

---

# Reward Totals

Across the complete M10 surface route:

```text
Total EXP: 1,060
Total Gold: 75
```

Rewards are granted once per combat encounter when that encounter is first cleared.

Rest nodes and the dungeon entrance grant no combat rewards.

---

# Authored Route Chain

```text
surface_goblin_solo
→ surface_goblin_pair
→ surface_warrior_solo
→ surface_rest_after_warrior_solo
→ surface_warrior_pair
→ surface_shaman_solo
→ surface_shaman_pair
→ surface_rest_after_shaman_pair
→ surface_elite_patrol
→ surface_rest_before_goblin_lord
→ surface_goblin_lord
→ surface_dungeon_entrance
```

No alternate branch, optional combat route, boss rematch, or party-expansion node exists inside M10.

```

One correction to my earlier reward total math: the route awards **1,060 EXP and 75 gold** in total. The node placements now match the map exactly.
```

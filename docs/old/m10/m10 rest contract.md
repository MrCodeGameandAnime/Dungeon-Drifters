# M10 Rest Contract

## Purpose

Rest is a simple deterministic recovery action available only at authored Rest
nodes on the overworld map. Rest nodes are part of the route, not a general
combat or menu command.

The M10 route currently contains three authored Rest nodes. Future maps may
contain additional Rest nodes, including routes for later dungeons.

## Availability

Rest is available only when the current `OverworldState` route node is an
authored Rest node.

Rest is not available during Battle or from the general overworld menu at a
non-Rest node.

Each Rest node is single-use in M10. A Rest node cannot be revisited after the
player rests there or skips it.

## Rest Node Menu

At an unused Rest node, the node-specific menu offers:

```text
Rest
Save
Quit
Menu
```

`Menu` returns to the normal Main Overworld Menu. Opening that menu does not
consume the Rest node or change persistent state.

`Save` follows the M10 Save and Load Contract. Saving does not consume the Rest
node.

`Quit` exits without automatically saving and does not consume the Rest node.

The player may skip the node through the normal route action:

```text
Continue Without Rest
```

Skipping consumes the single-use Rest node without restoring resources and
advances to the next authored route node. Skipping currently has little
mechanical value, but remains available so the route cannot trap the player at
a recovery node.

## Recovery

When `Rest` is accepted:

- current HP becomes maximum HP
- current Mana becomes maximum Mana
- Super remains unchanged
- EXP remains unchanged
- level and Growth Points remain unchanged
- gold remains unchanged
- equipment remains unchanged
- persistent inventory remains unchanged
- prepared Infusion state remains unchanged
- story and world progress remain unchanged

Rest does not create, remove, or advance encounter-local CombatState. Active
combat statuses do not exist at a completed overworld node and are never
restored by resting.

Rest has no gold, time, item, or resource cost in M10.

## Route Transition

After either accepted `Rest` or `Continue Without Rest`:

1. Mark the current Rest node resolved.
2. Advance to its authored next route node.
3. Return to the Main Overworld Menu.

Rest does not award EXP or gold and does not repeat an encounter reward.

## State Ownership

`OverworldState` owns whether each authored Rest node has been resolved and
the current route node. `PlayerState` owns HP, Mana, Super, and persistent
character resources. No menu or presenter owns a second copy of those values.

## Save and Load

Rest-node resolution state is persistent route state and is included in the
M10 save boundary. Open menus, highlighted controls, and confirmation prompts
are not saved.

Loading returns to the safe Main Overworld Menu and never restores an open Rest
node submenu.

## Required Tests

- Rest appears only at authored map Rest nodes.
- Rest is unavailable during Battle and at non-Rest nodes.
- Rest restores HP and Mana to their maxima.
- Rest does not change Super.
- Rest does not change EXP, level, Growth Points, gold, equipment, inventory,
  or prepared Infusion state.
- Rest has no cost.
- Save and Quit do not consume the Rest node.
- Menu returns to the normal Main Overworld Menu without consuming the node.
- Continue Without Rest consumes the node without recovery.
- A resolved Rest node cannot be used again.
- Rest advances to the exact authored next route node.
- Rest does not award or duplicate encounter rewards.
- Rest-node resolution persists through save/load.
- Rest does not mutate active CombatState.

## Completion Gate

At each authored Rest node, the player can choose recovery, skip recovery, save,
quit, or return to the normal overworld menu. Recovery fully restores HP and
Mana, leaves Super unchanged, consumes the node exactly once, and advances the
route without changing unrelated persistent state.

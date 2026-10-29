# Hub and First Dungeon Loop Plan

**Status: Complete for the first Hub and Floor I loop.** The safe tutorial outing and the dangerous, repeatable Floor I run are implemented; see [hub-implementation.md](hub-implementation.md) and [floor-one-implementation.md](floor-one-implementation.md). Floor II content and starting runs from Floor II remain future work.

## Goal

Build the first playable dungeon loop so the player learns the hub, recruits a companion, fights as a two-Drifter party, and experiences a successful extraction before later runs introduce loss risk.

## Agreed First-Run Experience

1. The player chooses a starting Drifter and completes the existing main surface route, which awards 75 gold total.
2. The player enters Floor 1 and arrives at the hub inside the dungeon. This is not the overworld.
3. The starting Drifter meets a companion. The player spends 65 gold to bring the chosen Drifter into the party.
4. The player readies the pair and enters one encounter against three Goblins.
5. Both Drifters participate in the same battle alongside all three Goblins.
6. After the fight, the player chooses to fall back to the hub rather than being carried automatically into another encounter.
7. Returning successfully secures the gold, items, and XP earned during this first outing. The player regroups at the hub with those rewards retained.

This first outing teaches extraction through play: go out, fight, choose to return, and keep what was earned. The hub return then gives supplies and the shop a meaningful context for the next outing.

## Hub and Recruitment

For this slice, the hub is the preparation and regroup point within the dungeon. It supports the specific flow above rather than attempting to deliver every eventual hub feature.

The first recruitment adds one player-chosen companion to the player-selected starting Drifter. The main route awards 75 gold total. Recruiting the companion costs a fixed 65 gold; this is a fixed content value, not a percentage calculated dynamically.

The initial party size is two Drifters. Full-roster management, off-screen expeditions, and the complete long-term recruitment system are not part of this slice.

## Two-Drifter Combat and Turn Order

Combat uses the existing Dexterity stat for turn order; there is no separate Agility stat. All active Drifters and enemies are ordered together by current Dexterity, highest first. Each combatant takes an individual turn in that order.

Example:

| Combatant | Dexterity | Order |
| --- | ---: | ---: |
| Drifter A | 6 | 1 |
| Goblin A | 5 | 2 |
| Drifter B | 4 | 3 |
| Goblin B | 3 | 4 |

Thus the round is `Drifter A -> Goblin A -> Drifter B -> Goblin B`. The first encounter contains three Goblins, so its order includes all five combatants. Equal-Dexterity combatants are ordered by a 50/50 random tie-break. Until enemy targeting AI is developed, each Goblin chooses uniformly at random among the living Drifters.

When Dexterity changes mid-round, immediately recalculate the relative order of combatants who have not acted yet. A completed turn is not repeated. An attack that lowers Dexterity can therefore move its target later in the current round, depending on the other unacted combatants' Dexterity.

## Extraction and Risk

The first outing is the safe introduction: a successful return to the hub secures the outing's rewards.

Before a dangerous Floor I outing begins, the game displays: "Death means returning to the Hub. All unsecured XP, gold, and items are lost. No retry, rewind, or continue." Defeat returns the party to the Hub with HP and Mana fully restored, discards unsecured rewards, and preserves rewards already secured at the Hub. The player can prepare and start another outing from there.

The safe tutorial outing secures rewards when the party returns to the Hub. If the party loses the first tutorial fight, it returns to Drifter selection so the player can try again; this tutorial reset is the exception to the dangerous-run death return to the Hub.

On successful return, XP is awarded as normal and split 50/50 between the two Drifters. Gold and items are retained in a shared general inventory, available for use, procurement, crafting, and assignment as the player chooses.

## Floor I Follow-On Rules

The dangerous Floor I extension is specified in [floor-one.md](floor-one.md) and implemented in [floor-one-implementation.md](floor-one-implementation.md). Its rest, extraction, death, boss-clear, and replay rules are part of the completed Floor I scope. The following boundary remains:

- A Floor 1 boss clear is recorded. Using it to unlock the future Floor II route remains future work; Floor II content and the option to start a run from Floor II are not implemented yet.
- Floor I replay XP uses the implemented 50%, 40%, 30%, then 20% rates. Replay gold is not reduced, and rest extraction retains all run items while paying half of adjusted XP and gold.
- Floor I has two Rest nodes, each supporting recovery, inspection, saving, continuing, and extraction.

## Scope Boundaries

The original tutorial scope here covers the first Hub visit, first companion recruitment, two-Drifter party combat, one three-Goblin encounter, and the successful return that secures rewards. The dangerous Floor I extension is documented separately. Floor II content, full-roster management, four-character expedition assignments, and the complete long-term Hub economy remain outside this completed scope.

Core gameplay state and rules remain owned by the game, not by a browser presentation layer. Preserve the existing save architecture; add only the versioned save data and migration needed to retain the recruited party and secured progression. Do not redesign persistence or change unrelated platform architecture.

## Completion

The first Hub tutorial loop and the dangerous Floor I run described by this document and its linked Floor I design are implemented. Their implementation plans record the completed work and verification. Floor II progression, roster expansion, expeditions, and the broader Hub economy remain future work and are not blockers for this scope.

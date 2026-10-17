# Hub and First Dungeon Loop Plan

**Status:** Design draft for review. No gameplay implementation is included here.

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

Before a later outing begins, show a warning that death forfeits that outing's unbanked gold, items, and XP. Death returns the player to the hub with the party's HP and Mana fully restored; it does not offer a retry, rewind, or continuation of the failed outing. Rewards already secured at the hub remain available. The player can prepare and start another outing from there.

The first slice should make the successful return, fully restored HP and Mana, and retained rewards clear. If the party loses the first safe tutorial fight, return to Drifter selection and let the player start the tutorial again; this tutorial reset is the exception to the later-outing death return to hub. Exact warning copy remains to be written.

On successful return, XP is awarded as normal and split 50/50 between the two Drifters. Gold and items are retained in a shared general inventory, available for use, procurement, crafting, and assignment as the player chooses.

## Follow-On Progression Rules

These are agreed direction for later dungeon progression, but are not required to complete the first three-Goblin extraction slice:

- Progress to the next floor only by clearing the current floor's boss.
- After clearing Floor 1's boss, the player may start a later run from Floor 1 or Floor 2.
- On repeat runs of a previously cleared floor, XP is reduced per run: 50%, 40%, 30%, then 20% for subsequent runs. This reduction applies to XP; no equivalent reduction to gold or items has been decided.
- Rests can appear along the route, as they do above ground.

## Scope Boundaries

This plan covers the first hub visit, first companion recruitment, two-Drifter party combat, one three-Goblin encounter, and the successful return that secures rewards. It does not design the complete shop or supply economy, all hub services, a floor boss, Floor 2 content, four-character expedition assignments, or the full long-term extraction economy.

Core gameplay state and rules remain owned by the game, not by a browser presentation layer. Preserve the existing save architecture; add only the versioned save data and migration needed to retain the recruited party and secured progression. Do not redesign persistence or change unrelated platform architecture.

## Proposed Delivery Order

1. Define the hub arrival, recruitment, ready-up, and return choices using the existing game/session boundaries.
2. Represent the two-Drifter active party and resolve an encounter with three Goblins.
3. Implement shared Dexterity-based turn ordering, immediately reordering unacted combatants after Dexterity changes and using a 50/50 random tie-break for equal Dexterity.
4. Add the successful fallback transition and secure the first outing's rewards at the hub.
5. Add the pre-outing risk warning and death-to-hub loss behavior for subsequent outings.
6. Add focused tests for the tutorial loop, turn order, reward retention, and subsequent-run failure behavior before qualifying the broader suite.

This is a feature sequence, not yet a file-by-file implementation plan. Implementation planning should follow once the open combat and onboarding decisions are resolved and this design is approved.

## Remaining Decisions Before Implementation

- What exact copy explains the later-run extraction risk?

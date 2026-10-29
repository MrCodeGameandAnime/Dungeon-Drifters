# Floor One Dangerous Run

**Status:** Approved design. The first safe Hub outing is implemented; this document defines the next playable outing on Floor 1. See [floor-one-implementation.md](floor-one-implementation.md) for the implementation plan.

## Goal

Extend the existing Hub loop into a dangerous, repeatable Floor 1 expedition. The run should feel threatening from its first battle. Recruiting a second Drifter adds tactical options, but does not turn the dungeon into an easy victory lap.

## Route

Floor 1 contains ten battles total. Battle 10 is the floor boss. There are two Rest nodes:

```text
Battles 1-5
-> Midway Rest
-> Battles 6-9
-> Pre-Boss Rest
-> Battle 10: Floor Boss
```

Battles 1-9 use the existing Goblin enemy in groups of one to four. The exact group-size sequence is placeholder content for this implementation and can be retuned after playtesting. Battle 10 temporarily reuses the existing Goblin Lord encounter; no new enemy archetypes or difficulty-scaling rules are introduced here.

The rests follow the existing above-ground Rest behavior. At either Rest, players may recover, inspect their Drifters and inventory, save, continue without extracting, or extract. The second Rest is immediately before the boss.

## Outing Rules

Starting a dangerous run from the Hub displays the agreed warning: death forfeits the current run's unsecured XP, gold, and items. It offers no retry, rewind, or continue prompt.

At either Rest, extraction returns the party to the Hub with full HP and Mana. It banks all items found during the run and half of the run's accumulated XP and gold. Existing secured Hub resources and the recruited party remain intact.

Defeat during a dangerous run discards all unsecured XP, gold, and items, then returns the party to the Hub fully restored. It preserves previously secured resources, party membership, and unlocked floor progress. The defeat outcome replaces the current save state so a save made at a Rest cannot be loaded through the normal game flow to retry that run.

Clearing the Floor 1 boss completes the expedition, banks all remaining run rewards, returns the party to the Hub fully restored, and records Floor 1 as cleared. This is the progression gate for later floors. Floor 2's route and encounters are not part of this work.

The agreed XP reduction for replaying a cleared floor remains: runs started after the first Floor 1 clear receive 50%, 40%, 30%, then 20% XP. Each subsequent run uses the next rate, down to a 20% floor. Apply that rate to earned XP; a partial extraction at a Rest then pays half of the adjusted XP and half of the run's gold, while retaining all found items. Fractional gold payouts round up to the next whole coin, following the earlier agreed round-up convention for gold calculations. No equivalent gold reduction applies to replay runs.

## State And Compatibility

Extend the existing authored route, route/session state, and party outing state. Persist the current Floor 1 node, party state, unsecured run rewards, and Floor 1 clear/replay information through the existing game save. Use a forward game-state migration as needed. Death must persist the Hub outcome over the last Rest save.

Keep Python authoritative and preserve parity between terminal and browser play. Do not change the save envelope version, profile API, database schema, or persistence-provider architecture. No parallel floor engine or second save representation is introduced.

## Scope Boundaries

This work covers the dangerous Floor 1 run, its two Rest choices, partial extraction, death return, boss completion, saved run resumption at a Rest, and Floor 1 replay XP reduction. Outings use the existing two-Drifter party; selecting a different companion or swapping party members at the Hub is a separate follow-up.

It does not add Floor 2 content, shops or supply purchasing, new enemy types, new combat mechanics, enemy AI, difficulty-scaling formulas, or item/equipment systems. Exact encounter group counts are temporary balance content and may change after playtesting.

## Acceptance Criteria

- The authored route contains exactly ten battles and two Rests, with the Rests after battles 5 and 9 and the existing Goblin Lord encounter at battle 10.
- The first nine battles use only the existing Goblin enemy, with encounter groups between one and four.
- A Rest supports recovery, inspection, saving, continuing, and partial extraction using the established Hub/session interfaces.
- Extraction at either Rest banks all run items and half of the run XP and gold, then returns the party to the fully restored Hub.
- Defeat loses all unsecured rewards, preserves secured resources and party membership, returns the party to the fully restored Hub, and supersedes the Rest save so the run cannot be resumed through normal load.
- Loading a save made at a Rest resumes at that Rest with the saved party and run state intact.
- Defeating the boss banks all remaining rewards, records Floor 1 as cleared, and makes the agreed replay XP reduction available without implementing Floor 2.
- Existing surface route behavior and the first safe Hub outing remain unchanged.
- Browser and terminal sessions use the same authoritative rules and transitions.

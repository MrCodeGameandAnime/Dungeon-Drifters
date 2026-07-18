Yes. I would lock Dungeon Drifters to an **absolute character level cap of 250** and build the XP curve around that.

The reason is literal:

```text
6 stats × 100 maximum = 600 total stat points
Level 1 Drifters begin with 60 total stat points
600 − 60 = 540 Growth Points needed to max every stat
```

The repository enforces that every Level 1 archetype starts with exactly 60 total permanent stats, and each permanent stat is capped at 100.

At three Growth Points per level:

```text
Level 250 provides 249 level-ups
249 × 3 = 747 total Growth Points

747 total
− 540 for all six stats
= 207 Growth Points for the complete growth tree
```

That gives us an exact completionist structure:

```text
Level 250
= every stat at 100
+ every authored growth-tree node purchased
```

The tree for each Drifter should therefore have an exact total purchase cost of **207 Growth Points**. The existing economy already establishes one point for a permanent stat, two for a passive rank, and three for a new move. Augments can use the same one-to-three-point hierarchy according to strength.

# Dungeon Drifters XP formula

Replace the current linear `100 × level` threshold with this Elden Ring-inspired curve:

```text
ramp = max(0, current_level − 10)

XP required for next level =
floor(
    20 × (ramp + 5) × (current_level + 30)²
    ÷ 961
)
```

The `961` normalizes Level 1 exactly because:

```text
31² = 961
```

So Level 1 → 2 costs exactly **100 XP**.

This gives us:

* a very gentle opening
* noticeable acceleration after Level 10
* strong endgame scaling
* an extremely expensive completionist back half
* integer-only deterministic math

The current code already supports carryover and gaining multiple levels from one award, but it presently has no maximum-level enforcement.

## Exact curve milestones

| Current level | XP for next level | Total XP spent to reach level |
|--------------:|------------------:|------------------------------:|
|             1 |               100 |                             0 |
|            10 |               166 |                         1,150 |
|            25 |             1,259 |                        10,035 |
|            50 |             5,993 |                        89,252 |
|            75 |            16,061 |                       346,774 |
|           100 |            33,413 |                       939,335 |
|           125 |            60,000 |                     2,072,458 |
|           150 |            97,773 |                     4,000,425 |
|           175 |           148,683 |                     7,026,312 |
|           200 |           214,682 |                    11,501,965 |
|           225 |           297,721 |                    17,828,010 |
|     249 → 250 |           395,280 |                    26,058,564 |

The absolute total from Level 1 to Level 250 is:

```text
26,453,844 XP
```

Like Elden Ring, the back half carries most of the weight:

```text
Level 1 → 100:
939,335 XP
3.6% of the absolute total

Level 150 → 250:
22,453,419 XP
84.9% of the absolute total

Level 200 → 250:
14,951,879 XP
56.5% of the absolute total
```

So reaching a healthy endgame build is realistic, while maxing absolutely everything remains a major completionist undertaking.

# Intended progression bands

```text
Levels 1–10
Opening campaign and first dungeon entry

Levels 11–50
Foundation and early build identity

Levels 51–100
Mature main-game build

Levels 101–150
Endgame specialization

Levels 151–200
Postgame and New Game+

Levels 201–250
Extreme mastery and completionist progression
```

The expected practical build range can remain far below the absolute cap. Level 250 exists so the player can eventually master everything, not because the main campaign should require it.

# Growth Points by level

| Level | Total Growth Points earned |
|------:|---------------------------:|
|    10 |                         27 |
|    25 |                         72 |
|    50 |                        147 |
|   100 |                        297 |
|   150 |                        447 |
|   200 |                        597 |
|   250 |                        747 |

Each level should continue granting the authored:

```text
+4 maximum HP
+1 maximum Mana
3 Growth Points
```

When maximum HP or Mana rises, current HP or Mana should rise by the same delta rather than fully refill. That preserves the amount already missing.

# M10 surface-route XP

For M10, surface-route EXP should become secured immediately after complete encounter victory. The future unsecured-dungeon/extraction loop begins after the dungeon entrance rather than being forced into the surface campaign.

Recommended archetype values:

```text
Goblin:          40 XP
Goblin Warrior:  60 XP
Goblin Shaman:   90 XP
Goblin Elite:   150 XP
Goblin Lord:    200 XP
```

The encounter reward is calculated from its composition but awarded only once after the entire encounter is defeated:

| Encounter                      | Reward | Resulting level state |
|--------------------------------|-------:|-----------------------|
| 1 Goblin                       |     40 | Level 1, 40 / 100     |
| 2 Goblins                      |     80 | Level 2, 20 / 106     |
| 1 Goblin Warrior               |     60 | Level 2, 80 / 106     |
| 2 Goblin Warriors              |    120 | Level 3, 94 / 113     |
| 1 Goblin Shaman                |     90 | Level 4, 71 / 120     |
| 2 Goblin Shamans               |    180 | Level 6, 4 / 134      |
| Goblin Elite + Goblin          |    190 | Level 7, 60 / 142     |
| Goblin Lord + Goblin + Warrior |    300 | Level 9, 68 / 158     |

Total surface-route reward:

```text
1,060 XP
```

The Drifter reaches the dungeon entrance at:

```text
Level 9
68 / 158 XP
24 Growth Points available
```

That feels substantial without overleveling the character before the first dungeon.

# Cap behavior

At Level 250:

```text
next threshold = none
XP cannot increase the level further
excess XP is discarded
Growth Points stop being awarded
level cannot exceed 250
```

So the full lock I recommend is:

```text
Absolute level cap: 250
Growth Points per level: 3
Total lifetime Growth Points: 747
Stat-maxing cost: 540
Full growth-tree budget: 207
Total XP to cap: 26,453,844
M10 dungeon-entry target: Level 9
```

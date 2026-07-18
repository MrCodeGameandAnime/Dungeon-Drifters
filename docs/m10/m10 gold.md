## Recommended M10 gold contract

Use small fixed values by enemy archetype:

```text
Goblin:          3 gold
Goblin Warrior:  5 gold
Goblin Shaman:   7 gold
Goblin Elite:    9 gold
Goblin Lord:    10 gold
```

Encounter rewards are the sum of the enemies in the authored composition:

| Encounter                      | EXP | Gold | Running gold |
|--------------------------------|----:|-----:|-------------:|
| 1 Goblin                       |  40 |    3 |            3 |
| 2 Goblins                      |  80 |    6 |            9 |
| 1 Goblin Warrior               |  60 |    5 |           14 |
| 2 Goblin Warriors              | 120 |   10 |           24 |
| 1 Goblin Shaman                |  90 |    7 |           31 |
| 2 Goblin Shamans               | 180 |   14 |           45 |
| Goblin Elite + Goblin          | 190 |   12 |           57 |
| Goblin Lord + Goblin + Warrior | 300 |   18 |           75 |

```text
Total surface-route gold: 75
```

At the dungeon entrance, the expected progression state becomes:

```text
Level 9
68 / 158 EXP
24 unspent Growth Points
75 gold
```

That is enough to prove gold persistence and support a few modest early purchases later, but it does not make the player wealthy.

## Reward rules

```text
Starting gold: 0

Gold is awarded only after complete encounter victory.

Partial enemy defeats award no gold.

Defeat awards no gold.

A completed encounter cannot award gold again.

Gold is awarded once per encounter, not immediately per defeated enemy.

Gold does not receive:
- level multipliers
- Intuition scaling
- secured-EXP scaling
- duplicate-enemy bonuses
- random variance
- performance bonuses
```

The values can be calculated from enemy composition internally, but the **encounter reward remains atomic**:

```text
defeat every required enemy
→ receive the full encounter EXP
→ receive the full encounter gold
→ mark encounter completed
```

## Economy intent

For now, gold should use a **low-denomination economy** where one gold actually means something. A rough future scale—not yet a locked shop contract—would be:

```text
small consumable or service: 10–25 gold
basic useful purchase:       40–75 gold
meaningful equipment:       100+ gold
major or rare purchase:     several hundred gold
```

So completing the entire surface route might eventually buy:

* a few basic supplies,
* one modest utility purchase,
* or contribute toward equipment,

but not all three.

## Copy-ready contract for X

```text
# M10 Gold Reward Contract

Starting gold: 0

Gold rewards are authored independently from the nonlinear EXP curve.

Enemy gold values:

- Goblin: 3
- Goblin Warrior: 5
- Goblin Shaman: 7
- Goblin Elite: 9
- Goblin Lord: 10

Encounter rewards:

1. 1 Goblin: 3 gold
2. 2 Goblins: 6 gold
3. 1 Goblin Warrior: 5 gold
4. 2 Goblin Warriors: 10 gold
5. 1 Goblin Shaman: 7 gold
6. 2 Goblin Shamans: 14 gold
7. Goblin Elite + Goblin: 12 gold
8. Goblin Lord + Goblin + Goblin Warrior: 18 gold

Total M10 surface-route gold: 75

Gold is granted once after complete encounter victory.

Partial enemy defeats grant no gold.

Defeat grants no gold.

Completed encounters cannot grant gold twice.

Gold has no level multiplier, random variance, Intuition bonus, secured-EXP
bonus, or performance multiplier during M10.

Gold persists through overworld transitions and save/load.

M10 does not require a shop or gold-spending system.
```

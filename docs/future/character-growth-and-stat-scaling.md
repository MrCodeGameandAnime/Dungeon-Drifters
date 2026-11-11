# Character Growth And Stat Scaling

This is the canonical design authority for individual Drifter growth,
progression, and stat scaling. Character Growth consumes secured experience only;
the rules for securing or losing run experience are owned by
[Dungeon Progression, Difficulty, and Economy](dungeon-progression-difficulty-and-economy.md).

## Core Progression Loop

Once experience is secured, it contributes to levels and Growth Points.
Previously secured levels, spent or unspent Growth Points, and permanent
progression remain safe during later dungeon runs.

## Level Rewards

Each secured level after Level 1 grants:

- a modest automatic maximum-HP increase
- a modest automatic maximum-mana increase
- 3 Growth Points

The purpose of automatic HP and mana growth is to preserve baseline viability.

Players should not be forced to spend every few levels repairing their health or
mana merely to survive later content.

Constitution and Spirit should represent specialization rather than mandatory
maintenance.

## Growth Point Economy

| Purchase | Cost |
| --- | --- |
| +1 permanent stat | 1 Growth Point |
| New single-purchase passive skill | 2 Growth Points |
| New active skill | 3 Growth Points |

M3 uses these flat prices regardless of tier or skill type. Capstones, mana
techniques, and the additional Super do not cost extra. The following spending
patterns use these costs:

```text
Three stat increases

or

One passive plus one stat increase

or

One new move
```

Growth Points may be saved across levels.

Move and passive purchases may also require prerequisites such as:

- minimum level
- previous tree nodes
- minimum stats
- story progress
- character events
- weapon-refinement level
- discovered techniques
- artifacts
- boss defeats

Growth Point cost determines affordability.

Prerequisites determine eligibility.

## Starting Stat Budget

~~Dungeon Drifters uses six permanent stats.~~

~~Every Level 1 Drifter should have exactly:~~

```text
~~60 total permanent stat points~~
```

~~The total budget is equal.~~

~~Character identity comes from distribution.~~

## Six Permanent Stats

## Constitution

Primary function:

- maximum HP

Constitution determines durability above the automatic level-based baseline.

## Spirit

Primary function:

- maximum mana

Spirit determines sustained access to mana-consuming moves and utility.

## Intelligence

Primary functions:

- magical damage
- elemental damage
- alchemical payload power
- primary supernatural scaling

## Strength

Primary functions:

- blade and heavy-weapon physical damage
- physical damage negation

## Dexterity

Primary functions:

- bow physical damage
- physical staff and polearm strikes
- accuracy
- dodge

Dexterity governs physically striking with a staff.

It does not govern magic channeled through the staff.

## Intuition

Intuition is the Arcane-like utility and specialized-scaling stat.

Intended functions include:

- secondary magical scaling
- elemental control
- alchemical and compound potency
- critical bonuses
- searching and discovery
- experience bonuses
- super-meter generation
- defensive spell potency
- specialized character mechanics

Intelligence remains the primary raw-magic stat.

Intuition supports control, unusual effects, secondary scaling, and utility.

## Drifter Scaling Identities

A Drifter's primary scaling stat is the highest stat in their authored Level 1
permanent stat block. Their secondary scaling stat is the second-highest. M3
skills should primarily scale from, enhance, or synergize with these two stats.
Other stats may support specific mechanics when justified by the Drifter's
existing kit.

| Drifter | Primary | Secondary | Authored Level 1 values |
| --- | --- | --- | --- |
| Branoc | Strength | Constitution | STR 15 / CON 14 |
| Azhvielle | Intelligence | Spirit | INT 15 / SPI 13 |
| Zhaivra | Dexterity | Intuition | DEX 15 / INTU 14 |
| Joruun | Intelligence | Dexterity | INT 13 / DEX 12 |

## Primary Character Builds

## Azhvielle

- Primary stat: Intelligence
- Secondary stat: Spirit

Natural identity:

- raw magical power
- mana depth and spell sustain
- elemental and unusual-effect potency

Useful tertiary investments:

- Intuition
- Constitution
- Dexterity

## Zhaivra

- Primary stat: Dexterity
- Secondary stat: Intuition

Natural identity:

- precision archery
- accuracy
- criticals
- compound timing and reactions

Useful tertiary investments:

- Intelligence for stronger compound payloads
- Constitution
- Spirit where relevant

## Branoc

- Primary stat: Strength
- Secondary stat: Constitution

Natural identity:

- heavy physical damage
- physical negation
- high HP
- frontline durability

Useful tertiary investments:

- Intuition for defensive magic
- Spirit for repeated defensive techniques
- Dexterity for accuracy or handling utility

## Joruun

- Primary stat: Intelligence
- Secondary stat: Dexterity

Natural identity:

- elemental magic
- agile physical staff combat
- physical-magical hybrid play

Useful tertiary investments:

- Intuition
- Spirit
- Constitution

## Split Attack Scaling

A move may contain separate physical, magical, elemental, or alchemical
components.

Each component scales independently.

## Azhvielle Scaling

Physical staff strike:

- Dexterity

Magic cast through the staff:

- Intelligence
- Intuition

## Joruun Scaling

Physical Sky-Needle strike:

- Dexterity

Elemental technique:

- Intelligence
- Intuition

## Zhaivra Scaling

Arrow impact:

- Dexterity

Fire, poison, or compound payload:

- Intelligence
- Intuition

## Branoc Scaling

Sunder-Spire physical damage:

- Strength

Physical damage negation:

- Strength

Defensive spell potency:

- Intuition

Maximum HP:

- Constitution

## Stat Caps

~~Every permanent stat may reach:~~

```text
~~100~~
```

The game should allow players to live out extreme late-game and New Game+ build
fantasies.

Balance should come from:

- time investment
- Growth Point opportunity cost
- move and passive costs
- diminishing returns
- encounter design

The game should not prohibit eventual mastery.

## Universal Stat Bands

| Stat range | Intended meaning |
| --- | --- |
| 1-20 | Foundation |
| 21-40 | Highest-efficiency growth |
| 41-60 | Dedicated specialization |
| 61-80 | Diminishing returns |
| 81-100 | Prestige and power-fantasy investment |
| 100 | Hard cap |

General interpretation:

```text
40 = strong
60 = specialized
80 = exceptional
100 = fantasy fulfilled
```

The main game may be balanced around primary stats commonly reaching
approximately 40-60.

Values from 80-100 support extreme investment, postgame development, and New
Game+.

## Constitution Prototype

Reference assumptions:

```text
Level 1
Constitution 10
100 maximum HP
```

Automatic level gain:

```text
+4 maximum HP per secured level
```

Provisional Constitution curve:

| Constitution range | HP gained per point |
| --- | --- |
| 1-10 | 3 |
| 11-20 | 4 |
| 21-40 | 7 |
| 41-60 | 5 |
| 61-80 | 3 |
| 81-100 | 2 |

Provisional Constitution milestones before level growth, equipment, passives,
accessories, and permanent discoveries:

| Constitution | Maximum HP |
| --- | --- |
| 10 | 100 |
| 20 | 140 |
| 40 | 280 |
| 60 | 380 |
| 80 | 440 |
| 100 | 480 |

Provisional formula shape:

```text
Maximum HP =
Constitution-derived HP
+ automatic HP from secured levels
+ equipment bonuses
+ passive bonuses
+ accessory bonuses
+ permanent discovery bonuses
```

The intent is:

- low Constitution remains playable because of automatic growth
- moderate investment produces balanced durability
- 40-60 produces a dedicated tank
- 61-100 continues increasing HP with reduced efficiency

## Spirit Prototype

Reference assumptions:

```text
Level 1
Spirit 10
50 maximum mana
```

Automatic level gain:

```text
+1 maximum mana per secured level
```

Provisional Spirit curve:

| Spirit range | Mana gained per point |
| --- | --- |
| 1-10 | 1 |
| 11-20 | 2 |
| 21-40 | 4 |
| 41-60 | 3 |
| 61-80 | 2 |
| 81-100 | 1 |

Provisional Spirit milestones before level growth and other bonuses:

| Spirit | Maximum mana |
| --- | --- |
| 10 | 50 |
| 20 | 70 |
| 40 | 150 |
| 60 | 210 |
| 80 | 250 |
| 100 | 270 |

Provisional formula shape:

```text
Maximum Mana =
Spirit-derived mana
+ automatic mana from secured levels
+ equipment bonuses
+ passive bonuses
+ accessory bonuses
+ permanent discovery bonuses
```

Spirit increases casting capacity, not direct spell damage.

## Intelligence Prototype

Intelligence governs primary magical, elemental, and alchemical output.

Provisional cumulative output curve relative to Intelligence 10:

| Intelligence | Cumulative applicable output bonus |
| --- | --- |
| 10 | 0% |
| 20 | +25% |
| 40 | +65% |
| 60 | +95% |
| 80 | +110% |
| 100 | +120% |

At Intelligence 100, an applicable component has approximately:

```text
2.20x base output
```

before Intuition, weapon properties, passives, accessories, and enemy defenses.

## Strength Prototype

Strength governs heavy and blade physical damage.

Use the same provisional primary-output curve:

| Strength | Cumulative applicable physical bonus |
| --- | --- |
| 10 | 0% |
| 20 | +25% |
| 40 | +65% |
| 60 | +95% |
| 80 | +110% |
| 100 | +120% |

Strength also provides physical damage negation.

Provisional negation milestones:

| Strength | Physical negation from Strength |
| --- | --- |
| 10 | 0% |
| 20 | 5% |
| 40 | 15% |
| 60 | 24% |
| 80 | 30% |
| 100 | 34% |

Strength-based negation may combine with:

- guarding
- weapon configuration
- passives
- accessories
- temporary effects

Use a separate final physical-negation cap.

Current provisional direction:

```text
Approximately 75% maximum ordinary physical negation
```

Exceptional temporary effects may be handled separately.

## Dexterity Prototype

Dexterity governs applicable bow and staff physical damage.

Use the same provisional primary-output curve:

| Dexterity | Cumulative applicable physical bonus |
| --- | --- |
| 10 | 0% |
| 20 | +25% |
| 40 | +65% |
| 60 | +95% |
| 80 | +110% |
| 100 | +120% |

Dexterity also affects accuracy and dodge.

Provisional milestones:

| Dexterity | Accuracy bonus | Dodge bonus |
| --- | --- | --- |
| 10 | 0% | 0% |
| 20 | +4% | +2% |
| 40 | +10% | +6% |
| 60 | +15% | +10% |
| 80 | +18% | +13% |
| 100 | +20% | +15% |

Provisional final combat caps:

```text
Maximum ordinary final hit chance: 95%
Maximum ordinary dodge chance: 50%
```

Moves and temporary effects may explicitly override ordinary rules where
authored.

## Intuition Prototype

Intuition spreads its value across several systems rather than dominating one
raw-damage category.

Provisional milestones:

| Intuition | Special potency | Crit chance | Super gain | Discovery | Secured XP |
| --- | --- | --- | --- | --- | --- |
| 10 | 0% | 0% | 0% | 0% | 0% |
| 20 | +10% | +2% | +10% | +10% | +1% |
| 40 | +25% | +6% | +25% | +25% | +4% |
| 60 | +35% | +10% | +40% | +40% | +7% |
| 80 | +42% | +13% | +50% | +55% | +10% |
| 100 | +50% | +15% | +60% | +70% | +12% |

Special potency may apply to:

- secondary magical scaling
- elemental control
- alchemical payloads
- poison and fire compounds
- defensive spells
- buffs
- healing effects
- status effects
- character-specific mechanics

Provisional magical-component shape:

```text
Final magical component =
base magical power
x Intelligence scaling
x Intuition special-potency scaling
```

This is a conceptual formula shape, not a finalized implementation formula.

Intuition safeguards:

- critical chance should have a final global cap
- provisional ordinary critical cap: approximately 35%
- XP bonuses apply only to successfully secured experience
- determine later whether XP bonuses are personal or party-wide
- discovery should improve probabilities or reward quality, not guarantee rare
  loot
- super generation should accelerate but not become effectively unlimited

## Automatic HP And Mana Growth

Automatic resource growth is required for accessibility and build freedom.

Without it, players who buy moves or passives are punished by frozen
survivability and resource capacity while dungeon difficulty continues rising.

That creates an unwanted binary:

- invest heavily in Constitution and Spirit
- become an increasingly fragile glass cannon

The intended system instead provides:

```text
Automatic level growth
-> viable baseline

Constitution and Spirit
-> deliberate specialization
```

Players should choose to become tanks, glass cannons, battlemages, sustained
casters, or balanced hybrids.

The system should not force them into tank or glass-cannon extremes.

## Additional Permanent Resource Growth

Altars, rare items, and discoveries may provide additional permanent progression
such as:

- maximum HP
- maximum mana
- potion capacity
- potion potency
- consumable capacity
- limited party-wide blessings

These bonuses supplement automatic level growth.

They should not replace it.

Missing an optional altar should not leave a character unable to survive
required later content.

## Moves, Passives, And Stats

The existing starting move kits and initial Super timing remain governed by the
current move-progression design. M3 does not reopen or restrict those decisions.

M3 adds 24 GP-purchased skills per Drifter: 18 passive skills and six active
skills. The active skills are four mana techniques, one non-mana normal move,
and one additional Super. The non-mana move still costs Growth Points to
unlock. The additional Super unlocks at Level 50 and stays in the Super system;
it does not occupy a normal-move slot.

Each Drifter has four equipped normal-move slots. A newly purchased normal or
mana skill is permanently unlocked into that Drifter's available move pool and
may then be equipped in one of those four slots. Existing saves retain their
current kits and move access; M3 does not reset or retroactively restrict them.

M3 uses these level gates and skill counts:

| Tier | Level | Passive skills | Active skills |
| --- | ---: | ---: | --- |
| I | 1 | 5 | 1 non-mana normal move |
| II | 25 | 4 | Mana Technique 1 |
| III | 50 | 4 | Mana Technique 2 and additional Super |
| IV | 75 | 4 | Mana Technique 3 |
| V | 100 | 1 capstone | Mana Technique 4 |

Skills within an unlocked tier may generally be purchased in any order. A
skill-specific prerequisite or mutually exclusive branch requires an authored
reason; tier membership alone does not impose a chain.

Moves primarily expand tactical vocabulary.

Passives primarily reinforce identity, utility, and synergy.

Stats primarily increase foundational numerical capability.

All three compete for Growth Points.

## Separate Progression Systems

Character progression:

```text
Experience
-> levels
-> automatic HP and mana
-> Growth Points
-> stats, passives and moves
```

Signature-weapon progression:

```text
Dungeon loot, components and materials
-> weapon refinement
-> component configuration
-> scaling and move interaction
```

Hub economy:

```text
Gold
-> consumables
-> alchemical supplies
-> common components
-> accessories
-> services
```

These systems may interact through prerequisites but should not replace one
another.

## Respec Direction

A controlled respec system is recommended because Growth Points create meaningful
and potentially expensive choices.

Possible respec rules include:

- performed by a hub NPC or trader service
- paid for with secured gold
- requires a rare consumable
- becomes more expensive with repeated use
- refunds spent Growth Points
- does not alter signature-weapon refinement
- does not refund weapon components or materials

The existence, price, and limitations of respecs remain unresolved.

Respecs should permit experimentation without making every progression decision
meaningless.

## Power-Fantasy Intent

A player who reaches extreme levels, develops a complete skill tree, refines a
signature weapon, and raises stats toward 100 should become extremely powerful.

Returning to an early dungeon with:

- 100 in primary stats
- completed passives
- every move
- a highly refined signature weapon
- legendary accessories

should feel overwhelming.

That is earned progression, not a design failure.

The balancing rule is:

> Endgame power should be earned, not prevented.

## Current Authored Direction

Record these as the current intended foundation:

- ~~six permanent stats~~
- ~~60 total permanent stat points at Level 1~~
- ~~hard cap of 100 in every stat~~
- 3 Growth Points per secured level
- +1 permanent stat costs 1 Growth Point
- M3 single-purchase passive skill costs 2 GP; active skills cost 3 GP, without premiums
- Growth Points may be saved
- automatic HP gain occurs every secured level
- automatic mana gain occurs every secured level
- Constitution specializes maximum HP
- Spirit specializes maximum mana
- Intelligence is primary magical scaling
- Strength governs heavy/blade physical damage and physical negation
- Dexterity governs bow/staff physical damage, accuracy, and dodge
- Intuition is the Arcane-like utility and secondary-specialization stat
- soft caps preserve normal balance
- stats remain valuable through 100
- secured progression is not lost on ordinary dungeon death

## Provisional Rather Than Final Numbers

The numerical curves above are the current prototype direction.

They should be preserved for future implementation and testing, but clearly
identified as provisional until validated through:

- move costs
- enemy damage
- dungeon pacing
- weapon scaling
- accessory bonuses
- passive bonuses
- potion recovery
- mana costs
- super generation
- actual playtesting

Do not silently replace these figures during implementation.

Any proposed numerical change should be surfaced for design review.

## Explicitly Unresolved

The questions below remain broader design questions; they do not authorize M3
to change the existing level progression, 3-GP award, permanent stat spending,
six-stat model, HP/Mana growth, Level 250 cap, or signature-weapon progression.

Do not freeze these yet:

- final starting distributions for each Drifter
- experience thresholds
- leveling curve
- final HP auto-gain value
- final mana auto-gain value
- final Constitution curve
- final Spirit curve
- exact damage formulas
- exact scaling coefficients
- exact soft-cap boundaries
- exact negation cap
- exact accuracy cap
- exact dodge cap
- exact critical cap
- exact Intuition XP behavior
- personal versus party-wide XP bonuses
- exact discovery formula
- exact super-generation formula
- exact mechanical effects and numerical values for the authored M3 passive and active skills
- Rank structure for any future passive expansion beyond the initial M3 tree
- skill-specific prerequisites or mutually exclusive branches, where justified
- story prerequisites
- weapon-refinement prerequisites
- whether every passive can eventually be purchased
- respec availability
- respec cost
- respec limitations
- altar and permanent-item limits
- maximum Growth Point availability
- whether any levels grant something other than 3 Growth Points
- final terminology for Growth Points

Existing starting move kits and initial Super timing are settled by the current
move-progression design and are not unresolved M3 decisions.

## Milestone Boundary

Preserve the existing implementation exactly while separating
definitions from runtime state.

Future implementation:

- passive trees
- move unlocking
- new scaling curves
- split-damage formulas
- soft caps
- Intuition systems
- respecs
- permanent resource altars
- new experience-loss behavior

These systems should be implemented only after the foundational architecture can
clearly represent:

- permanent stats
- secured and unsecured experience
- character levels
- unspent Growth Points
- purchased nodes
- unlocked moves
- passive ranks
- prerequisites
- snapshot and save-state representation

# Complete

- ~~the six-stat replacement~~
- ~~60-point budget enforcement~~
- ~~stat caps~~
- ~~automatic HP or mana growth~~
- ~~Growth Points~~
- ~~stat spending~~

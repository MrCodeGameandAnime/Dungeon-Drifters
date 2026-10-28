# Signature Weapon Progression

This document records the current authored design direction for a permanent
signature-weapon system. Open decisions remain listed below.

For implementation, [signature-weapon-implementation.md](signature-weapon-implementation.md)
is the more specific contract where it deliberately resolves an ambiguity in
this broader design. Decisions not resolved there remain open as indicated
below.

## Core Philosophy

Each Drifter permanently retains their signature weapon.

The player does not routinely replace it with randomly dropped swords, bows,
staffs, or other loot weapons. These weapons are central to the characters'
identities:

- ~~Branoc carries Sunder-Spire.~~
- ~~Zhaivra carries Sathren.~~
- ~~Joruun carries Sky-Needle.~~
- ~~Azhvielle carries Needle of Plain Iron.~~

The governing principle is:

> Drifters do not replace their weapons. They evolve them.

Weapons found in the dungeon may still be valuable, but they are generally:

- inspected
- dismantled
- studied
- salvaged for materials
- converted into components
- used to unlock refinement knowledge
- incorporated into a signature weapon

The goal is to preserve character identity while retaining meaningful loot,
crafting, experimentation, and visual weapon progression.

## System Relationship

The intended mechanical chain is:

```text
Character stats
-> signature weapon
-> weapon refinement and installed components
-> move components
-> final combat result
```

Stats define the character's potential.

The signature weapon determines how those stats become weapon output.

Installed components and refinement paths modify that translation.

Moves determine which physical, magical, elemental, alchemical, defensive, or
utility parts of the weapon are used.

## Separate Progression Axes

Weapon progression should not be a single flat ladder.

The current direction separates weapon growth into distinct layers:

```text
Overall refinement (separate; final cap unresolved)
-> four modifiable weapon slots
-> continuous improvement and quality milestones for each slot
-> physical / mystical branch identity produced by the final configuration
```

These layers should remain distinct.

Overall refinement, if retained, represents development of the signature
weapon as a whole. It is separate from the 0-100 improvement progress tracked
by each slot and from the shared 0-100 Crafting level.

Slot improvement represents repeated material investment into one physical part
of that weapon. Each slot tracks its own progress from 0 to 100.

Slot quality represents the shared craftsmanship milestones reached only when
all four slots, the required materials, and shared Crafting level meet the
matching threshold.

Physical and mystical branches describe what the completed configuration has
become. They should emerge from the four-slot build rather than requiring a
second set of independent modification zones.

## 1. Overall Refinement Level

Every signature weapon has an overall refinement level displayed as:

```text
+0
+1
+2
...
+10
...
+20
```

The final cap is unresolved.

The refinement level represents improvement to the weapon as a whole and may
eventually affect:

- base output
- scaling efficiency
- magical channeling
- structural stability
- slot-development ceilings
- access to advanced branches
- access to stronger component and material tiers

The refinement level does not add additional modification slots. Every signature
weapon uses the fixed four-slot model described below.

The weapon retains its overall refinement level when individual slot
configurations are changed, subject to future balance decisions.

Example:

```text
Sky-Needle +0
Sky-Needle +8
Sky-Needle +20
```

## 2. Four-Slot Signature Weapon Model

Every signature weapon has exactly four modifiable pieces.

The purpose of the fixed count is to preserve meaningful customization without
turning every signature weapon into a large collection of independently managed
subparts.

The structure is:

```text
three structural / body pieces
+ one signature / special piece
= four total modifiable slots
```

The material family identifies the slot's dominant modification material; it
does not imply that the entire physical part is made from that material. The
following player-facing slot map is the implementation contract.

### Sunder-Spire

1. Blade / Guard assembly
2. Grip wrap / binding
3. Hilt core / handle
4. Crest / Core

The first three slots govern the physical body and handling of Sunder-Spire.
Metal is the dominant modification family for the blade and guard hardware;
Fiber for grip wrapping and binding; Timber for the hilt/handle structure. The
fourth slot carries the weapon's defensive, Deep-Iron, crest, or other
character-specific development.

Possible effects include:

- Strength scaling
- physical damage
- physical negation
- guard strength
- stagger
- accuracy
- defensive technique potency
- character-resource generation

### Sathren

1. Grip / fittings / mechanism
2. String
3. Limbs
4. Reservoir / Catalyst

The first three slots govern the physical bow. Metal is the dominant
modification family for grip hardware, fittings, and mechanism; Fiber for the
string; Timber for the limbs. The fourth slot carries Sathren's
compound-delivery, reservoir, catalyst, and other alchemical development.

Possible effects include:

- Dexterity scaling
- physical arrow damage
- accuracy
- critical behavior
- reservoir capacity
- compound delivery
- fire or poison potency
- Intelligence and Intuition payload scaling
- setup speed

### Sky-Needle

1. Head / Striking Cap
2. Binding / Grip
3. Shaft
4. Focus / Collar

The first three slots govern Sky-Needle's physical staff construction. Metal is
the dominant modification family for the striking head; Fiber for binding and
grip; Timber for the shaft. The fourth slot carries its elemental focus,
conduction, attunement, and other character-specific development.

Possible effects include:

- Dexterity-based staff damage
- Intelligence-based elemental damage
- Intuition-based elemental control
- mana efficiency
- current behavior
- lightning conduction
- water control
- wind control
- accuracy
- stagger

Example special materials or components may still include ideas such as:

Stormglass

Possible benefits:

- stronger lightning output
- improved Intelligence scaling

Possible costs:

- weaker water efficiency

Flood-Bone

Possible benefits:

- stronger water techniques
- improved Intuition scaling

Possible costs:

- reduced physical impact

Deep-Iron

Possible benefits:

- stronger physical staff strikes
- increased stagger

Possible costs:

- reduced accuracy
- reduced dodge interaction

### Azhvielle's Signature Weapon: Needle of Plain Iron

1. Focus head / fittings
2. Binding
3. Haft
4. Seal / Catalyst

The first three slots govern the physical construction and channeling body.
Metal is the dominant modification family for focus-head fittings; Fiber for
magical bindings; Timber for the haft. The fourth slot carries instability,
causal structure, magical specialization, and other character-specific
development.

Possible effects include:

- Dexterity-based physical staff damage
- Intelligence-based magical power
- Intuition-based magical control
- mana efficiency
- elemental specialization
- instability
- critical magic
- spell behavior

The weapon's name is Needle of Plain Iron. Its exact physical construction
beyond this slot model may be refined as content is authored.

## 3. Material Dismantling And Recovery

Dropped weapons and other eligible items may be dismantled into materials,
components, or refinement knowledge.

Each dismantleable source item should author at least:

- what materials or component families it can produce
- the maximum recoverable quantity
- the material tier or quality involved
- whether it can produce a rare special component, technique, or knowledge unlock

Example:

```text
Goblin drops Iron Sword
-> Iron Sword may contain up to 3 Iron
-> dismantle
-> recover 1, 2, or 3 Iron depending on the dismantling result
```

The maximum quantity belongs to the dropped item definition. At least one
matching material is always recovered; the actual yield may be lower than the
authored maximum.

Shared Crafting level shifts the random recovery result toward the authored
maximum, but never guarantees maximum recovery, even at level 100. The exact
random formula remains a tuning decision. Dismantling does not award Crafting
progress.

Most ordinary dropped weapons should primarily yield reusable materials rather
than becoming finished replacement weapons or requiring a bespoke signature-
weapon component for every drop.

Dismantling is the main material source. Enemies and bosses may also directly
drop rare materials, including cores.

Rare drops may additionally provide:

- special components
- rare materials
- blueprints
- branch knowledge
- attunement knowledge
- refinement techniques
- unique improvement items

This keeps ordinary loot scalable while allowing exceptional discoveries to
change a build.

## 4. Slot Improvement Progress

Each of the four slots tracks improvement progress from 0 to 100. The quality
gates are 25, 50, 75, and 100. An ordinary improvement recipe always succeeds
and rolls 1-5 points for its selected slot. Shared Crafting level shifts the
odds toward higher results, while every result from 1 to 5 remains possible.
The exact odds by Crafting level are data-driven tuning values.

Slot progress cannot overshoot its next quality gate. If a roll would cross the
gate, progress settles exactly at that gate and no overflow is retained. The
slot remains capped there until all four slots and shared Crafting meet that
gate and unlock its next tier. For example, a slot at 23 that rolls 4 settles
at 25, not 27. Once the tier is unlocked, the next improvement starts from 25.

Improvement directly raises the statistics governed by that slot. Improvement
and quality bonuses are calculated from the weapon's original base statistics,
not from already-modified values, so the two bonuses are additive rather than
compounding. Each slot-progress point adds 0.25% of the governed original base
stat, so 100 progress contributes +25%. Combine that with the applicable
cumulative quality bonus, then round the final projected stat once to the
nearest integer, with exact halves rounded up. For a nonnegative base stat `B`,
slot progress `P`, and cumulative quality bonus `Q` expressed as a fraction:

```text
projected_stat = round_half_up(B * (1 + 0.0025 * P + Q))
```

The four material families are fixed by slot number:

| Slot | Material family |
|---|---|
| 1 | Metal |
| 2 | Fiber |
| 3 | Timber |
| 4 | Cores |

Each material family has grades aligned to the ordinary weapon tiers. Grade I
improves a slot from 0 through 25. Once every slot and shared Crafting meet 25,
Tier II unlocks and Grade II is required for further progress toward 50. Grade
III is used after Tier III unlocks at 50, and Grade IV after Tier IV unlocks at
75. Material grade is determined by the slot's current progress band before the
roll; reaching a gate uses the grade for the band being completed. A slot at a
locked gate cannot be improved. Grade II materials first appear on Floor II,
Grade III on Floor III, and Grade IV on Floor IV, preventing a player from
farming an earlier floor for later-tier improvement materials. Floor I must
provide legitimate Grade-I sources for all four families, in quantities
sufficient to demonstrate at least one valid improvement for each slot family;
abundance need not be equal. Tier V uses Grade IV materials rather than
introducing Grade V.

The Floor I source approach is set: dismantlable Goblin loot supplies Grade-I
Metal, Fiber, and Timber, while every Goblin Lord defeat, including Floor I
replays, guarantees enough Grade-I Cores for one valid slot-four improvement.
Exact source item IDs, yields, and recipe quantities remain part of the balance
table.

Material quantities and recipe costs are authored per recipe; they do not follow
a forced 1/2/3/4 quantity formula. Each actual crafting or improvement recipe
also defines its own Crafting progress award. Numeric costs and awards remain
data-driven tuning values.

Improvement progress does not reset when a tier gate is unlocked. After Tier IV
unlocks at 75, progress from 75 to 100 continues to improve the Tier IV weapon.

## 5. Quality Milestones And Tier V

Tier I is the starting quality. Tier II-IV unlock at the first three gates; 100
is the Tier V capstone-attempt gate:

| Weapon tier | Required progress in every slot | Shared Crafting level |
|---|---:|---:|
| Tier I | Starting tier | Starting tier |
| Tier II | 25/100 | 25/100 |
| Tier III | 50/100 | 50/100 |
| Tier IV | 75/100 | 75/100 |
| Tier V attempt | 100/100 | 100/100 |

Each slot has to reach each gate; no single slot can carry the weapon into the
next tier. A slot's progress is capped at its next gate until all four slots and
the roster-wide Crafting level meet it. The shared tier advances only after all
five values meet the matching checkpoint. The material grade changes after the
gate is unlocked: Grade I can reach 25, Grade II is used to progress beyond 25,
Grade III beyond 50, and Grade IV beyond 75. At 100, the weapon becomes eligible
for a non-guaranteed Tier V attempt; reaching 100 alone does not grant Tier V.

Quality adds a separate bonus to the base statistics governed by each slot. The
first-pass schedule is a shared, linear +5% per ordinary breakthrough: Tier II
adds +5%, Tier III is +10% cumulative, and Tier IV is +15% cumulative. These
bonuses apply to base stats and add to continuous slot improvement; they do not
compound from current modified stats. The schedule is data-driven and can be
retuned without changing the progression rules.

Tier V is an optional god-tier capstone attempt. It requires all four slots at
100/100 and shared Crafting at 100/100. It uses a significantly larger,
authored quantity of Grade IV materials, has a fixed but non-guaranteed success
chance, and does not introduce a new material grade. A failed attempt consumes
its materials but preserves all existing progress and awards no Crafting
progress. Success adds a separate +25% of base stats governed by the slots.
This stacks additively with the Tier IV +15% quality bonus, for +40% cumulative
quality bonus after Tier V success. Tier V cost, chance, and bonus are
data-driven tuning values.

All quality bonuses are based on original weapon stats. Progress resumes from
each gate after the shared tier unlocks; Tier IV progress from 75 to 100 is
useful before attempting Tier V.

## 6. Crafting Progression

Crafting is a shared roster-wide skill with a 0-100 level. It is not owned by an
individual Drifter. Its level affects dismantling yield odds, the distribution
of 1-5 improvement rolls, and eligibility for the matching ordinary quality
milestones. The roster begins at Crafting Level 1 with zero progress toward
Level 2; the cumulative progress thresholds for later levels remain a tuning
decision. The balance target is for the roster to reach Crafting Level 25 after
about three Hub-returning Floor I runs, not a single clear. This should happen
before replay XP reaches its 20% minimum. Grade II materials remain exclusive to
Floor II, so reaching Crafting 25 on Floor I does not bypass the material gate
for Tier II weapon progression.

The Hub merchant handles crafting, weapon-improvement recipes, and dismantling.
`Character > Weapon` is for inspecting and configuring a signature weapon.
These progression interactions are Hub-only.

Crafting progress is awarded only for successfully completed, actual crafting
or weapon-improvement recipes. Each recipe authors its own progress award; there
is no global award formula. Awards increase from lower- to higher-tier recipes
to reflect their greater requirements. Dismantling awards none, and failed
Tier V attempts award none.

Alchemy is a separate progression system and does not award Crafting progress.
Alchemy can produce potions, arrows, and other items that may be ingredients in
recipes for higher-tier weapon progression. Alchemy's own progression and
recipe outcomes are defined by its separate design.

## 7. Physical Configuration Tree

Physical materials, slot configurations, quality levels, and special components
may push the completed weapon toward forms such as:

- Light
- Refined
- Heavy
- Great

These names represent configurations of the permanent signature weapon rather
than completely different weapons.

They should emerge from the state of the four slots rather than requiring extra
physical-branch equipment slots.

They should be interpreted according to the signature weapon.

### Light

Possible characteristics:

- lower weight
- faster attacks
- improved accuracy
- stronger Dexterity interaction
- better dodge or mobility interaction
- reduced impact, stagger, or raw power

### Refined

Possible characteristics:

- precise construction
- balanced performance
- reliable scaling
- improved control
- fewer severe strengths or weaknesses

### Heavy

Possible characteristics:

- increased physical output
- greater stagger or guard pressure
- stronger Strength interaction
- reduced speed, accuracy, or mobility

### Great

Possible characteristics:

- extreme physical specialization
- exceptional force, reach, draw weight, or impact
- greater resource or stamina demands
- major mechanical tradeoffs
- possible move alterations

A Great Sathren remains Sathren. It might become a reinforced, high-draw
configuration with devastating projectile impact rather than becoming a different
category of weapon.

Physical identity is derived from authored physical contribution points on the
current slot components/configuration. Improvement or quality adds identity
points only when explicitly authored. The physical identity with the highest
valid total is selected when it meets its minimum threshold.

## 8. Mystical Development Tree

Magical, elemental, alchemical, or supernatural materials, qualities, special
components, and attunements may push the completed weapon toward forms such as:

- Enchanted
- Mystic
- Attuned
- Legendary

These should also emerge from the four-slot configuration rather than requiring a
second collection of mystical modification zones.

Mystical identity is calculated independently from authored mystical contribution
points on the current slot components/configuration. Improvement or quality adds
identity points only when explicitly authored. The mystical identity with the
highest valid total is selected when it meets its minimum threshold. A weapon can
have one physical and one mystical identity at the same time. If two identities
on the same axis tie above threshold, that axis has no identity until one leads.
Identity is derived from the current configuration and recalculates automatically
when a component changes.

### Enchanted

The weapon develops a reliable supernatural property.

### Mystic

The weapon gains stronger interaction with magical or unusual scaling, especially
Intelligence and Intuition.

### Attuned

The weapon becomes strongly aligned with a specific:

- element
- current
- compound
- magical principle
- defensive discipline
- character mechanic

### Legendary

The weapon reaches a capstone identity created through refinement, rare
components, quality development, and player decisions.

Legendary status should be earned through development of the signature weapon. It
should not merely mean that the player found a replacement weapon labeled
"Legendary."

## Component-Based Construction

The system should take inspiration from modular weapon assembly, but the fixed
four-slot model is now the governing boundary.

Components, materials, and slot configurations should:

- visibly change the weapon where practical
- alter mechanical properties
- affect scaling
- create tradeoffs
- influence branch development
- contribute to generated weapon titles
- potentially alter how certain moves behave

Components should not all be direct upgrades.

Replacing an installed component consumes the old component; it does not return
to inventory. This also applies to rare cores installed in slot four.

Component effects on moves are data-driven. Initial modifiers may adjust an
existing move's power, resource cost, accuracy, or damage type. They do not
change its target or scaling. Rare cores may unlock a new data-authored
technique; once learned, that technique remains learned if the core is later
replaced. Direct modifiers from a component apply only while that component is
installed.

Example:

Heavier striking configuration

Benefits:

- increased physical output
- increased stagger
- stronger Strength scaling

Costs:

- reduced accuracy
- reduced attack speed
- reduced dodge or mobility

Another configuration might provide the opposite profile.

## Relationship To The Six-Stat System

Weapon components translate character investment into combat effects.

## Branoc

Sunder-Spire physical attacks:

- primarily Strength

Physical damage negation:

- Strength

Defensive techniques:

- potentially Intuition

## Zhaivra

Ordinary Sathren arrow impact:

- Dexterity

Fire, poison, or compound payload:

- Intelligence
- Intuition

A coated arrow may therefore contain separate physical and alchemical or
elemental damage components.

## Joruun

Physical Sky-Needle strikes:

- Dexterity

Elemental techniques:

- Intelligence
- Intuition

Hybrid moves may contain both components.

## Azhvielle

Physical staff strikes:

- Dexterity

Magic channeled through the staff:

- Intelligence
- Intuition

## Weapon Naming

The displayed weapon name should communicate the player-created configuration.

Provisional structure:

```text
[Prefix] [Signature Weapon] [Suffix] +[Refinement Level]
```

Example:

```text
Calamitous Sky-Needle of Torrential Rain +20
```

This could communicate:

- "Calamitous": dominant configuration, capstone form, or high-output prefix
- "Sky-Needle": permanent signature weapon identity
- "of Torrential Rain": dominant water affinity, component set, or attunement
- "+20": overall weapon refinement level

Additional examples:

```text
Refined Sathren of Venomous Glass +9
Attuned Sathren of the Burning Vein +16
Great Sunder-Spire of the Unbroken Gate +18
Mystic Needle of Plain Iron +13
```

These examples establish naming intent only. They do not freeze actual
obtainable affixes.

The final title may be generated from:

- physical branch
- mystical branch
- dominant component set
- elemental or compound alignment
- capstone achievement
- refinement level

## Build Diversity

Two players using the same Drifter and the same signature weapon should be able
to create meaningfully different final configurations.

For example, one Sky-Needle +20 might emphasize:

- fast Dexterity-based physical strikes
- accuracy
- dodge
- low mana dependence

Another Sky-Needle +20 might emphasize:

- storm damage
- Intelligence scaling
- Intuition scaling
- elemental attunement
- high mana consumption

Both remain authentic versions of Sky-Needle.

The strongest configurations should involve real tradeoffs. A weapon should not
become universally superior in every category simply because it reached a high
refinement level.

## Loot Philosophy

Dungeon loot may include:

- raw refinement materials
- dismantleable enemy weapons
- broken weapons
- catalysts
- magical focuses
- alchemical mechanisms
- rare metals
- creature materials
- runes
- seals
- blueprints
- forging knowledge
- refinement techniques
- special components
- improvement items

A common found weapon should usually produce reusable materials rather than become
an equipable replacement for a Drifter's signature weapon.

Example:

```text
Found weapon
-> inspect
-> dismantle
-> recover authored material quantity
-> spend materials on one of four signature-weapon slots
-> build improvement percentage
-> meet quality threshold
-> improve the permanent signature weapon
```

A rarer discovery may extend that flow:

```text
Rare found weapon / relic / mechanism
-> dismantle or study
-> recover rare material or special component
-> unlock branch, attunement, blueprint, or refinement knowledge
-> apply it through the four-slot signature-weapon system
```

Rare discoveries should remain exciting without forcing the Drifter to abandon
the weapon central to their identity.

The loot catalog will therefore need substantial authored breadth. Enemy weapons
and objects are not merely vendor trash; they are source items that feed
materials, crafting progression, quality growth, and rare build-defining unlocks.

## Explicitly Unresolved

These details are not final balance. Use the Gate 0 first-pass defaults below
for the initial playable loop; unresolved systems outside that loop remain
deferred rather than blocking implementation.

- final refinement cap
- which named physical and mystical identities are available, and their topology
- exact branch contribution values and minimum thresholds
- later-grade material recipes, quantities, and floor drop tables
- Alchemy progression and recipe rules (separate system)
- player-facing quality labels
- respec rules
- special-component rarity
- component stat and move effects beyond the playable baseline
- exact visual implementation
- exact affix-generation rules
- inventory limits
- final obtainable prefixes and suffixes

## Data-Driven Tuning Values

These values are intentionally authored per recipe, component, or shared
configuration so they can be balanced without changing the progression rules:

- material quantities and costs for each crafting/improvement recipe
- Crafting progress awarded by each successful recipe
- dismantling yield ranges and Crafting-weighted odds
- the Crafting-level distribution for 1-5 improvement rolls
- branch contribution points and minimum thresholds
- ordinary quality bonus schedule (currently +5% per breakthrough)
- Tier V Grade IV material cost, success chance, and +25% base-stat bonus
- per-component move-modifier values

### Gate 0 First-Pass Defaults

These are implementation defaults for the first playable loop, not a balance
lock. They are centralized in `app.content.weapon_progression_spec` and can be
retuned after playtesting.

| Material grade | Improvement cost | Crafting XP award |
|---|---:|---:|
| I | 1 | 20 |
| II | 2 | 30 |
| III | 3 | 40 |
| IV | 4 | 50 |

Crafting starts at Level 1 with 0 XP. Each level after the first costs 10
cumulative XP, so Level 25 begins at 240 XP. Improvement roll weights are
`1/2/3/4/5 points`:

| Crafting level | Roll weights (%) |
|---:|---|
| 1 | 40 / 25 / 18 / 12 / 5 |
| 25 | 32 / 24 / 19 / 15 / 10 |
| 50 | 24 / 22 / 20 / 18 / 16 |
| 75 | 16 / 19 / 21 / 22 / 22 |
| 100 | 10 / 15 / 20 / 25 / 30 |

Goblin Scrap dismantling yields one matching Grade-I Metal, Fiber, or Timber,
with a chance for a second based on Crafting level. Goblin Lord Cores dismantle
into one Grade-I Core. The double-yield chance is 20%, 35%, 50%, 65%, and 80%
at Crafting levels 1, 25, 50, 75, and 100 respectively. These values are
first-pass defaults; Floor I boss Core drops remain guaranteed.

The following are no longer unresolved:

- every signature weapon has exactly four modifiable slots
- the four-slot structure is three structural/body slots plus one signature/special slot
- ordinary dismantleable drops author a maximum material yield and may recover less than that maximum
- dismantling guarantees at least one matching material and never guarantees the authored maximum
- material families map by slot as metal, fiber, timber, and cores
- weapon-specific slot names are fixed by the four-slot table above; material family describes the dominant modification material, not the entire part's composition
- ordinary grades align to weapon tiers and first appear on their corresponding floors
- Floor I provides Grade-I sources for all four families, sufficient to demonstrate one valid improvement per family
- Floor I dismantlable Goblin loot supplies Grade-I Metal, Fiber, and Timber; every Goblin Lord defeat, including Floor I replays, guarantees Grade-I Cores for one slot-four improvement
- per-slot improvement progress and shared Crafting level each use a 0-100 scale
- each slot-progress point adds 0.25% of its governed original base stats; 100 progress adds +25%
- combine improvement and cumulative quality bonuses from original base stats, then round once, nearest integer with halves up
- ordinary improvement recipes always succeed and add 1-5 percentage points
- Tier II/III/IV/V gates are 25/50/75/100 for every slot and shared Crafting
- slot improvements cannot overshoot the next gate; progress clamps at the gate until the shared requirements unlock the next tier
- progress carries through ordinary tier breakthroughs without overflow from the triggering roll
- slot improvement and tier-quality bonuses are separate and both use original base stats
- Tier V success adds +25 percentage points to Tier IV's +15%, for +40% cumulative quality bonus
- Tier II/III/IV quality bonuses are currently +5%/+10%/+15% cumulative
- Tier V requires all slots and shared Crafting at 100, uses Grade IV materials, and is non-guaranteed
- failed Tier V attempts consume materials but preserve progress and award no Crafting progress
- Crafting is shared roster-wide and gains progress only from successful recipes with explicit awards
- the roster starts at Crafting Level 1 with zero progress toward Level 2; crafting, weapon improvement, and dismantling use a Hub merchant
- Alchemy is separate and does not award Crafting progress
- physical and mystical identities can coexist and are derived from the four-slot configuration
- ties on one identity axis produce no identity for that axis until one leads
- identity recalculates automatically after component changes
- replacing a component consumes the old one, including slot-four cores
- component move effects use data-driven modifiers; unlocked techniques remain learned
- every weapon-progression action explicitly targets a Drifter by stable ID rather than relying on lead/party order

# Complete

- ~~permanent stats~~
- ~~structured moves~~
- ~~equipment ownership~~

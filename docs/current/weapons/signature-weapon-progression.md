# Signature Weapon Progression

This document records the current authored design direction for a permanent
signature-weapon system. Open decisions remain listed below.

## Core Philosophy

Each Drifter permanently retains their signature weapon.

The player does not routinely replace it with randomly dropped swords, bows,
staffs, or other loot weapons. These weapons are central to the characters'
identities:

- ~~Branoc carries Sunder-Spire.~~
- ~~Zhaivra carries Sathren.~~
- ~~Joruun carries Sky-Needle.~~
- ~~Azhvielle carries her signature staff or magical focus; its final name remains
  unresolved.~~

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

The current direction separates weapon growth into four interacting layers:

```text
Overall refinement (+X)
-> four modifiable weapon slots
-> improvement percentage and quality within each slot
-> physical / mystical branch identity produced by the final configuration
```

These layers should remain distinct.

Overall refinement represents development of the signature weapon as a whole.

Slot improvement represents repeated material investment into one physical part
of that weapon.

Slot quality represents a larger craftsmanship threshold reached only when the
required improvement, materials, and crafting capability are present.

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

The current structure is:

```text
three structural / body pieces
+ one signature / special piece
= four total modifiable slots
```

The four slots are a shared system boundary, but their names and mechanical
meaning are authored for each signature weapon.

The exact player-facing labels may still change as the weapons are finalized.
The current working slot map is:

### Sunder-Spire

1. Blade
2. Guard
3. Hilt / Grip
4. Crest / Core

The first three slots govern the physical body and handling of Sunder-Spire. The
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

1. Limbs
2. String
3. Grip
4. Reservoir / Catalyst

The first three slots govern the physical bow. The fourth slot carries Sathren's
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
2. Shaft
3. Binding / Grip
4. Focus / Collar

The first three slots govern Sky-Needle's physical staff construction. The fourth
slot carries its elemental focus, conduction, attunement, and other
character-specific development.

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

### Azhvielle's Signature Staff Or Focus

1. Focus / Head
2. Haft
3. Binding
4. Seal / Catalyst

The first three slots govern the physical construction and channeling body. The
fourth slot carries instability, causal structure, magical specialization, and
other character-specific development.

Possible effects include:

- Dexterity-based physical staff damage
- Intelligence-based magical power
- Intuition-based magical control
- mana efficiency
- elemental specialization
- instability
- critical magic
- spell behavior

Its final weapon name and exact construction remain unresolved.

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

The maximum quantity belongs to the dropped item definition. The quantity actually
recovered may be lower.

Crafting level is intended to influence recovery quality and efficiency. A more
skilled crafter should generally be better at extracting the useful material from
an item rather than destroying or wasting part of it.

The exact random formula, minimum guaranteed recovery, and whether sufficiently
high Crafting can guarantee maximum recovery remain unresolved.

Most ordinary dropped weapons should primarily yield reusable materials rather
than becoming finished replacement weapons or requiring a bespoke signature-
weapon component for every drop.

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

## 4. Slot Improvement Percentage

Recovered materials are spent on one of the four weapon slots.

Each slot tracks its own improvement progress.

Conceptual example:

```text
2 Iron
-> attempt to improve Sunder-Spire Blade
-> nominal improvement: +2%
```

The nominal improvement is the value the material recipe can provide under the
required crafting conditions.

Crafting level may reduce or preserve that value.

Example:

```text
Nominal improvement: +2%
Crafting level below the full-efficiency requirement
-> realized improvement: +1%
```

The exact numbers above establish system behavior only. Final material costs,
improvement percentages, skill requirements, rounding, and efficiency curves
remain unresolved.

Improvement percentage is gradual progress. It is not the same thing as overall
weapon refinement and it is not the same thing as slot quality.

## 5. Slot Quality Breakthroughs

Each of the four slots also has a quality level.

Quality does not increase merely because the player spends one more common
material.

A quality breakthrough should require a combination of conditions such as:

- the slot reaching a required improvement percentage
- materials of the required tier or better
- the required Crafting level
- or an authorized improvement item that can satisfy or substitute for a missing
  crafting requirement

Conceptual flow:

```text
slot improvement reaches threshold
+ required material tier is present
+ Crafting requirement is met
    or an appropriate improvement item is used
-> slot quality increases
```

If the quality requirement is not met, additional ordinary improvement should not
silently bypass it.

When a slot's quality increases, all statistics governed by that slot receive the
quality increase's percentage improvement.

Conceptual example:

```text
Blade quality increases
-> Blade quality grants +X%
-> physical damage, stagger, Strength scaling, or other Blade-governed values
   each receive the authored quality increase where applicable
```

The exact quality names, number of quality tiers, threshold percentages,
material-tier requirements, and stat multipliers remain unresolved.

It is also unresolved whether improvement progress resets, partially carries, or
fully carries after a quality breakthrough.

## 6. Crafting Skill Relationship

Crafting level should matter at multiple points rather than acting as one flat
bonus.

Current intended relationships include:

```text
Crafting level
-> dismantling recovery efficiency
-> material yield quality
-> realized slot-improvement efficiency
-> eligibility for higher-quality breakthroughs
-> effectiveness or quality of crafted improvement items
```

A lower Crafting level may therefore recover fewer materials, realize less of a
material's nominal improvement value, or be unable to perform a higher-quality
breakthrough without assistance.

A higher Crafting level should improve efficiency and access without creating
materials from nothing or bypassing authored material requirements.

Crafting and Alchemy should follow the same broad skill principle where useful:
skill affects how effectively a recipe's inputs become a finished result.

For Alchemy, that may include the potency, duration, efficiency, or quality of
created alchemical items.

The exact Crafting and Alchemy level curves, caps, experience rules, failure
chances, and recipe requirements belong to their formal progression designs and
remain unresolved here.

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

The exact branch requirements, thresholds, and ordering remain unresolved.

## 8. Mystical Development Tree

Magical, elemental, alchemical, or supernatural materials, qualities, special
components, and attunements may push the completed weapon toward forms such as:

- Enchanted
- Mystic
- Attuned
- Legendary

These should also emerge from the four-slot configuration rather than requiring a
second collection of mystical modification zones.

They may represent progressive tiers, branching identities, or a combination of
both. The exact topology remains unresolved.

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
Mystic [Azhvielle Weapon Name] of Severed Causality +13
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

Do not freeze these yet:

- final refinement cap
- final player-facing names for each weapon's four slots
- exact branch topology
- exact branch thresholds and contribution formulas
- whether Light, Refined, Heavy, and Great are exclusive branches or tiered states
- whether Enchanted, Mystic, Attuned, and Legendary are branches or tiers
- exact upgrade costs
- exact dismantling recovery formulas and randomness
- minimum guaranteed dismantling yields
- Crafting level curve and cap
- Alchemy level curve and cap
- exact material tiers
- exact slot-improvement percentages
- exact quality names and number of quality tiers
- quality-threshold percentages
- whether improvement progress resets or carries after a quality breakthrough
- exact quality stat multipliers
- component-removal costs
- respec rules
- special-component rarity
- exact stat coefficients
- exact visual implementation
- exact affix-generation rules
- exact move modifications
- crafting interface
- inventory limits
- failure chances
- ~~final name of Azhvielle's weapon~~
- final obtainable prefixes and suffixes

The following are no longer unresolved:

- every signature weapon has exactly four modifiable slots
- the four-slot structure is three structural/body slots plus one signature/special slot
- ordinary dismantleable drops author a maximum material yield and may recover less than that maximum
- Crafting level influences recovery and improvement efficiency
- slot improvement percentage and slot quality are separate progression layers
- quality breakthroughs require authored thresholds rather than occurring automatically
- quality improvement increases the statistics governed by the improved slot
- physical and mystical branch identity should emerge from the four-slot configuration rather than add more modification zones

# Complete

- ~~permanent stats~~
- ~~structured moves~~
- ~~equipment ownership~~

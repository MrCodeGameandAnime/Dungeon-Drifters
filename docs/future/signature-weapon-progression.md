# Signature Weapon Progression

This note records future authored design direction for a permanent
signature-weapon system. It is not authorized for implementation during
Milestone 3.

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

A signature weapon may develop across several independent or interacting axes.

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
- component capacity
- access to advanced branches
- access to stronger component tiers

The weapon retains its overall refinement level when components are exchanged,
subject to future balance decisions.

Example:

```text
Sky-Needle +0
Sky-Needle +8
Sky-Needle +20
```

## 2. Physical Configuration Tree

Physical components may push a weapon toward forms such as:

- Light
- Refined
- Heavy
- Great

These names represent weapon configurations rather than completely different
weapons.

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

The exact branch requirements and ordering remain unresolved.

## 3. Mystical Development Tree

Magical, elemental, alchemical, or supernatural components may push the weapon
toward forms such as:

- Enchanted
- Mystic
- Attuned
- Legendary

These may represent progressive tiers, branching identities, or a combination of
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
components, and player decisions.

Legendary status should be earned through development of the signature weapon. It
should not merely mean that the player found a replacement weapon labeled
"Legendary."

## Component-Based Construction

The system should take inspiration from modular weapon assembly.

Components should:

- visibly change the weapon
- alter mechanical properties
- affect scaling
- create tradeoffs
- influence branch development
- contribute to generated weapon titles
- potentially alter how certain moves behave

Components should not all be direct upgrades.

Example:

Heavier striking component

Benefits:

- increased physical output
- increased stagger
- stronger Strength scaling

Costs:

- reduced accuracy
- reduced attack speed
- reduced dodge or mobility

Another component might provide the opposite profile.

## Weapon-Specific Component Zones

Each signature weapon should have component zones appropriate to its construction
and lore.

## Sunder-Spire

Possible component zones:

- blade sections
- fuller
- crossguard
- grip
- pommel
- Deep-Iron reinforcement
- crest or defensive focus

Possible mechanical effects:

- Strength scaling
- physical damage
- physical negation
- guard strength
- stagger
- accuracy
- defensive technique potency
- character-resource generation

## Sathren

Possible component zones:

- bow limbs
- string
- grip
- reservoir assembly
- pressure valves
- delivery channels
- arrow interface
- compound catalyst

Possible mechanical effects:

- Dexterity scaling
- physical arrow damage
- accuracy
- critical behavior
- reservoir capacity
- compound delivery
- fire or poison potency
- Intelligence and Intuition payload scaling
- setup speed

## Sky-Needle

Possible component zones:

- shaft sections
- striking cap
- grounding base
- copper collars
- conductive rings
- elemental focus
- bindings
- seals

Possible mechanical effects:

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

Example components:

Stormglass Collar

Benefits:

- stronger lightning output
- improved Intelligence scaling

Costs:

- weaker water efficiency

Flood-Bone Rings

Benefits:

- stronger water techniques
- improved Intuition scaling

Costs:

- reduced physical impact

Deep-Iron Foot

Benefits:

- stronger physical staff strikes
- increased stagger

Costs:

- reduced accuracy
- reduced dodge interaction

## Azhvielle's Signature Staff Or Focus

Possible component zones:

- haft
- striking head
- magical focus
- bindings
- elemental catalyst
- instability seal
- runic or causal structure

Possible mechanical effects:

- Dexterity-based physical staff damage
- Intelligence-based magical power
- Intuition-based magical control
- mana efficiency
- elemental specialization
- instability
- critical magic
- spell behavior

Its final weapon name and exact construction remain unresolved.

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
- weapon components
- broken enemy weapons
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

A found weapon may produce:

```text
Found weapon
-> inspect
-> dismantle
-> recover material or component
-> unlock refinement knowledge
-> apply to signature weapon
```

Rare discoveries should remain exciting without forcing the Drifter to abandon
the weapon central to their identity.

## Explicitly Unresolved

Do not freeze these yet:

- final refinement cap
- exact component-slot counts
- exact branch topology
- whether Light, Refined, Heavy, and Great are exclusive branches or tiered states
- whether Enchanted, Mystic, Attuned, and Legendary are branches or tiers
- upgrade costs
- component-removal costs
- respec rules
- component rarity
- exact stat coefficients
- exact visual implementation
- exact affix-generation rules
- exact move modifications
- crafting interface
- inventory limits
- dismantling yields
- failure chances
- ~~final name of Azhvielle's weapon~~
- final obtainable prefixes and suffixes

## Milestone Boundary

This is future design authority only.

Milestone 3 must continue extracting current definitions and runtime state
without implementing this system or altering existing combat behavior.

The weapon system should be designed formally only after the foundational work
for:

- ~~permanent stats~~
- resource formulas
- ~~structured moves~~
- damage components
- combat resolution
- ~~equipment ownership~~

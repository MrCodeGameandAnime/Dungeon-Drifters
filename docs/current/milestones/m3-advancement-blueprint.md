# M3 Universal 24-Skill Advancement Blueprint

Use one shared advancement blueprint for all four Drifters rather than
independently inventing 96 unrelated skills.

The blueprint defines the mechanical purpose of each slot. Each Drifter
receives a character-specific implementation using their canonical primary and
secondary stats, existing class identity, moves, mechanics, and weapon identity
where appropriate.

This document defines conceptual roles, not final numerical effects. Gate 2
owns damage composition, formulas, mitigation, and rounding.

Canonical scaling identities, derived from authored Level 1 permanent stats:

| Drifter | Primary | Secondary |
| --- | --- | --- |
| Branoc | Strength | Constitution |
| Azhvielle | Intelligence | Spirit |
| Zhaivra | Dexterity | Intuition |
| Joruun | Intelligence | Dexterity |

Do not force the secondary stat to deal damage. Use the function that stat
already has for that character:

```text
CON  -> HP / durability / defensive conversion
SPI  -> Mana / sustained casting / resource economy
INTU -> special potency / crit / Super / specialized effects
DEX  -> physical output / accuracy / dodge / agile mechanics
```

Tertiary stats may support an existing authored mechanic when justified, but
the tree should primarily reinforce the Drifter's primary/secondary identity.

## Fixed Advancement Structure

```text
Tier I     Level 1      5 passives + 1 free move
Tier II    Level 25     4 passives + 1 mana technique
Tier III   Level 50     4 passives + 1 mana technique + 1 new Super
Tier IV    Level 75     4 passives + 1 mana technique
Tier V     Level 100    1 capstone passive + 1 mana technique
```

All new skills are purchased with Growth Points. Costs are flat:

```text
Permanent stat     1 GP
Passive            2 GP
Active skill       3 GP
```

There is no premium pricing for capstones, mana techniques, or the additional
Super. "Free move" means non-mana, not free to unlock.

## Tier I: Foundation

Tier I establishes how the character's core stats and mechanics should feel.

### P1. Primary Output

Improve the character's most fundamental offensive use of their primary stat.

```text
STR -> heavy/blade physical pressure
INT -> magical/elemental output
DEX -> bow/staff physical output
```

Do not create a new subsystem; reinforce an existing offensive identity.

### P2. Secondary Identity

Strengthen the canonical secondary stat in its natural role. This need not
increase raw damage.

```text
CON  -> durability
SPI  -> mana capacity or sustained casting
INTU -> specialized potency/crit/Super interaction
DEX  -> physical technique/accuracy/dodge
```

### P3. Resource Foundation

Improve one resource or sustainability concern already relevant to the Drifter:
HP, Mana, Super, resource cost/preservation, or resource-linked effects. Keep
the effect simple and readable.

### P4. Class Mechanic Foundation

Enhance a mechanic already belonging to the Drifter's combat identity. Prefer
existing DD mechanics over new systems:

```text
Branoc     heavy pressure / Brace / frontline durability
Azhvielle  spellcasting / Arcane interactions / frost-gravity magic
Zhaivra    precision / archery / Infused Barb / compound effects
Joruun     staff combat / elemental interactions / storm setup
```

### P5. Utility Foundation

Give the character a broadly useful, identity-consistent combat quality-of-life
bonus. Possible areas include accuracy, dodge, crit, physical negation, special
potency, Super generation, mana efficiency, and defensive utility. Avoid
duplicating generic damage bonuses.

### A1. Free Technique

One new non-mana normal move.

- Costs 3 GP to unlock.
- Uses one of the four normal-move slots when equipped.
- Primarily expresses the Drifter's primary stat.
- Gives the player a new tactical option rather than merely replacing the
  basic attack with a larger number.
- Does not require an entirely new combat subsystem.

## Tier II: Specialization

Tier II begins turning the character's starting archetype into a deliberate
build.

### P6. Primary Specialization

A stronger or more conditional primary-stat passive than P1. Reward intentional
investment in the primary stat rather than duplicating P1.

### P7. Secondary Specialization

Deepen the secondary-stat identity established by P2:

```text
CON  -> stronger defensive conversion
SPI  -> better sustained Mana use
INTU -> stronger specialized effects or tempo
DEX  -> stronger accuracy/dodge/physical-technique interaction
```

### P8. Resource Efficiency

Improve efficiency with an existing resource: reduce mana pressure, improve
Super generation, conserve resources under an authored condition, or better use
large HP/Mana pools. Do not introduce unconditional infinite sustain.

### P9. Technique Synergy

Enhance interaction with the character's existing move or mechanic family. It
should encourage a play pattern rather than simply increase every number:

```text
Brace -> follow-up interaction
frost/gravity -> spell interaction
Infused Barb -> payload interaction
storm setup -> elemental interaction
```

### A2. Primary Mana Technique

One new mana-consuming technique built mainly around the primary stat. It is the
straightforward Tier II power option and costs 3 GP to unlock.

## Tier III: Hybridization

Tier III is the midpoint power spike. It introduces stronger interaction
between the two defining stats and grants the second Super.

### P10. Primary + Secondary Synergy

Reward investment in both canonical stats. Both stats need not contribute
directly to damage:

```text
STR + CON -> offense tied to durability
INT + SPI -> spell power supported by Mana investment
DEX + INTU -> precision enhanced by specialized potency
INT + DEX -> elemental magic interacting with physical technique
```

Exact numerical composition belongs to the Gate 2 arithmetic contract.

### P11. Tempo

Improve an existing tempo mechanic such as crit, Super generation, accuracy,
dodge, setup/trigger cadence, or conditional follow-up. Choose the variant that
fits the character.

### P12. Sustain / Defense

Provide a meaningful defensive or sustain option consistent with the
character's identity, without making every Drifter a tank:

```text
Branoc     direct durability
Azhvielle  caster survival/resource defense
Zhaivra    avoidance/precision survival
Joruun     hybrid/agile defense
```

### P13. Class Mechanic Upgrade

Upgrade the mechanic introduced or reinforced by P4/P9. This is the first major
class-mechanic passive and should noticeably alter use of the existing mechanic.
Do not add a second unrelated mechanic to fill the slot.

### A3. Hybrid Mana Technique

One mana technique expressing interaction between primary and secondary
identity. "Hybrid" means identity interaction, not necessarily two damage
packets. It costs 3 GP to unlock.

### A4. Additional Super

Unlock the Drifter's second Super at Level 50. It costs 3 GP, uses the existing
Super system, and does not occupy one of the four normal-move slots. It should
serve a meaningfully different tactical purpose from the existing Super and
strongly express the established identity; do not make it merely the existing
Super with more damage.

## Tier IV: Mastery

Tier IV rewards committed builds and strengthens the character's highest-level
class interactions.

### P14. Primary Mastery

A high-level passive representing mastery of the primary stat's role. It should
be stronger or more mechanically interesting than P1/P6 without invalidating
them.

### P15. Secondary Mastery

The equivalent mastery passive for the secondary stat. Respect its actual
function rather than turning every secondary stat into raw offense.

### P16. Conditional Power

A strong effect requiring a meaningful combat condition. Conditions may involve
resource state, successful setup, crit, enemy state, defensive state, move
family, Super state, or a successful sequence. The condition should be
observable and controllable enough to build around.

### P17. Advanced Class Mechanic

The strongest ordinary passive enhancement to the Drifter's existing
class-mechanic family, preparing the identity completed by the Tier V capstone.

### A5. Utility / Control Mana Technique

One advanced mana technique emphasizing more than straightforward raw damage.
Possible purposes include control, defense, setup, status interaction,
positioning abstraction, resource manipulation, class-mechanic setup, or
multi-step interaction. Stay within mechanics DD supports or can reasonably
extend during M3. It costs 3 GP to unlock.

## Tier V: Capstone

Tier V represents mastery rather than another broad batch of options.

### P18. Capstone Passive

The single Level 100 passive, costing the normal 2 GP. It should be the strongest
and most character-defining passive in the tree, strongly express primary and
secondary identity, interact meaningfully with an established class mechanic or
core combat loop, and feel transformative without creating an unrelated
subsystem. Do not make it a large universal percentage increase.

The capstone should answer: "What does the fully realized version of this
Drifter do?"

### A6. Final Mana Technique

The strongest non-Super active added by M3. It costs the normal 3 GP, consumes
Mana, unlocks at Level 100, strongly expresses the complete primary/secondary
identity, and sits below a Super in conceptual importance while still feeling
like an endgame technique. It may use advanced interactions established earlier
in the tree.

## Shared Authoring Rules

Use the same 24 slots for every Drifter, but do not make the four trees
mechanically identical. The slot purpose is shared; the implementation is
character-specific:

```text
universal slot
    -> canonical primary/secondary stats
    -> existing character mechanic
    -> existing move/weapon identity
    -> character-specific skill
```

For example, P2 should use Constitution/durability for Branoc,
Spirit/Mana/sustained casting for Azhvielle, Intuition/specialized potency,
crit, or Super interaction for Zhaivra, and Dexterity/physical staff,
accuracy, dodge, or agile interaction for Joruun.

Prefer existing DD concepts: damage/output, HP, Mana, Super, physical negation,
accuracy, dodge, critical chance, special potency, resource costs, existing
statuses, character mechanics, weapon/component interactions, and existing
setup/trigger relationships. Do not create a bespoke subsystem for every
passive.

Avoid passive redundancy. Do not fill a tree with effects distinguished only by
larger generic percentages; progression should move from foundation to
specialization, synergy, mastery, and capstone.

Every purchase belongs to the exact Drifter. Bench members retain their
progression. Existing signature-weapon techniques and investment remain separate
from GP-purchased advancement.

Do not revoke existing moves from legacy saves. M3 adds the new progression
structure on top of existing character state under the approved compatibility
policy.

## Numerical Balance Boundary

This blueprint defines what each skill slot does conceptually. It does not
authorize final damage coefficients, stat-composition formulas, mixed
mitigation, or rounding rules. Those remain governed by M3 Gate 2. Skills may be
authored conceptually before those formulas are finalized, but final numerical
implementations must use the approved Gate 2 arithmetic.

## Authoring Target

Do not invent 96 unrelated skills. Define the 24 universal roles once, then fill
P1-P18 and A1-A6 for each Drifter using canonical stats and existing identity.
This keeps authoring, implementation, testing, balancing, and future expansion
tractable while preserving character differences.

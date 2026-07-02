# Enemy Archetypes, Scaling, and Capability Progression

## Core Separation

Enemy design separates four concepts:

```text
Archetype = what the enemy is
Rank = how mechanically complex its authored kit may be
Tier = how numerically strong this encounter instance is
Encounter stage = where the enemy appears in the game
```

Encounter stage is placement data, not an intrinsic enemy property. A Goblin in
a later dungeon remains an ordinary Goblin unless the encounter asks for a
different archetype such as Goblin Captain, Goblin Shaman, or Goblin King.

Tier can make a reused archetype numerically stronger. It does not expand the
move roster, grant healing, grant Super, or change the enemy's identity.

## Canonical Enemy Definition

An enemy archetype definition owns authored identity and capability data:

```text
archetype_id
display name
rank
role
behavior
capabilities
base stats
base HP
base Mana
structured moves
```

`EnemyState` owns one encounter instance's mutable resources and preserves the
requested tier. Runtime health, mana, Super, stats, and combat moves must not be
shared between enemy instances.

Package ownership follows the same boundary:

```text
app.combat = reusable combat rules and contracts
app.enemies = enemy definitions, runtime enemy state, registration, scaling
              policies, factory, and authored enemy content
```

## Rank Budgets

Ranks are descriptive capability budgets, not runtime roster enforcement.

| Rank | Design default |
| --- | --- |
| COMMON | Usually 2 moves, one simple combat identity, no healing or Super by default |
| SPECIALIST | Usually 3 moves and one authored specialized capability such as magic, healing, ranged pressure, poison, control, or elemental setup |
| ELITE | Usually 4 moves, broader resource use, and one signature mechanic or stronger conditional behavior |
| BOSS | Full authored kit, possible Super capability, phases, or encounter-specific rules |

Rank does not automatically grant capabilities. Capabilities do not
automatically create moves. Moves do not automatically infer capabilities. The
archetype explicitly declares each piece.

## Capabilities

Capabilities describe systems the archetype is authorized to use.

Current capability examples:

```text
BASIC_ATTACKS
MAGIC
HEALING
SUPER
DEFEND
```

Healing is authored capability data, not universal enemy behavior. Super is also
authored capability data. Ordinary enemies do not gain either system merely
because they appear later.

The legacy Battle loop still contains a temporary universal low-HP enemy
healing branch. That branch is not the enemy model. Milestone 8 must remove it
when Battle begins using structured enemy moves and authored enemy capabilities.

## Tier

Tier determines numerical strength for one encounter instance.

```text
Goblin +0 = current base ordinary Goblin
Goblin +1, +2, +3 = deferred future scaling policies
```

Generic tier validation is shared:

```text
integer
not bool
zero or greater
```

After a tier is known to be legal, the archetype scaling policy decides whether
that archetype currently supports it. The current Goblin scaling policy supports
only tier 0.

## Current Ordinary Goblin

The ordinary Goblin contract is:

```text
Archetype ID: goblin
Display name: Goblin
Rank: COMMON
Role: MELEE_SKIRMISHER
Behavior: AGGRESSIVE
Tier: 0
Capabilities: BASIC_ATTACKS
HP: 60
Mana: 0/0
```

Current canonical roster:

```text
1. slash
2. jumping slash
```

Every current ordinary Goblin move is supported by the Milestone 7 resolver.
Milestone 8 should not need to silently filter malformed or unsupported ordinary
Goblin moves before action selection.

`suplex` is deferred future Goblin-family design for a higher-complexity
archetype such as Goblin Brute, Goblin Grappler, or Goblin Captain. Stagger is
not active in the ordinary Goblin roster.

## Deferred Systems

These remain extension points and are not implemented by the current enemy
contract pass:

```text
actual tier +1 through +3 multipliers
advanced enemy AI
healing AI
Defend behavior
resistances
weaknesses
reward tables
EXP rewards
gold rewards
loot
visual assets
formations
additional enemy archetypes
boss phases
```

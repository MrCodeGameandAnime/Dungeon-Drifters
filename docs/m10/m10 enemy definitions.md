# M10 Enemy Definition Lock

The ordinary Goblin remains unchanged:

```text
Archetype ID: goblin
HP: 60
Mana: 0

Constitution: 2
Spirit: 1
Intelligence: 1
Strength: 3
Dexterity: 1
Intuition: 1

Rank: Common
Role: Melee Skirmisher
Behavior: Aggressive
Capabilities: Basic Attacks
Tier: 0

Moves:
Slash
Jumping Slash
```

All M10 surface-route enemies use tier 0. Their definitions are permanent
enemy content and are registered through their individual enemy packages.

## Goblin Warrior

```text
Archetype ID: goblin_warrior
HP: 85
Mana: 0

Constitution: 4
Spirit: 1
Intelligence: 1
Strength: 5
Dexterity: 2
Intuition: 2

Rank: Common
Role: Brute
Behavior: Aggressive
Capabilities: Basic Attacks
Tier: 0
```

Moves:

| Move | Cost | Power | Scaling | Accuracy | Damage | Mechanic |
|---|---:|---:|---|---:|---|---|
| Cleaver Strike | 0 | 10 | Strength | 92 | Physical | `basic_attack` |
| Shieldbreaker Chop | 0 | 15 | Strength | 78 | Physical | `heavy_attack` |

## Goblin Shaman

```text
Archetype ID: goblin_shaman
HP: 65
Mana: 25

Constitution: 2
Spirit: 5
Intelligence: 6
Strength: 1
Dexterity: 3
Intuition: 4

Rank: Specialist
Role: Caster
Behavior: Aggressive
Capabilities: Basic Attacks, Magic
Tier: 0
```

Moves:

| Move | Resource | Cost | Power | Scaling | Accuracy | Damage | Mechanic |
|---|---|---:|---:|---|---:|---|---|
| Crooked Staff | None | 0 | 7 | Dexterity | 90 | Physical | `basic_attack` |
| Cinder Hex | Mana | 5 | 11 | Intelligence | 90 | Magical | `basic_attack` |
| Blight Spark | Mana | 10 | 16 | Intelligence, Spirit | 80 | Magical | `heavy_attack` |

## Goblin Elite

```text
Archetype ID: goblin_elite
HP: 130
Mana: 0

Constitution: 7
Spirit: 3
Intelligence: 2
Strength: 8
Dexterity: 5
Intuition: 4

Rank: Elite
Role: Brute
Behavior: Aggressive
Capabilities: Basic Attacks
Tier: 0
```

Moves:

| Move | Cost | Power | Scaling | Accuracy | Damage | Mechanic |
|---|---:|---:|---|---:|---|---|
| Veteran Slash | 0 | 13 | Strength, Dexterity | 92 | Physical | `basic_attack` |
| Butcher’s Advance | 0 | 18 | Strength | 84 | Physical | `heavy_attack` |
| Executioner’s Drop | 0 | 24 | Strength | 72 | Physical | `heavy_attack` |

## Goblin Lord

```text
Archetype ID: goblin_lord
HP: 220
Mana: 30

Constitution: 10
Spirit: 7
Intelligence: 7
Strength: 11
Dexterity: 6
Intuition: 9

Rank: Boss
Role: Boss
Behavior: Aggressive
Capabilities: Basic Attacks, Magic
Tier: 0
```

Moves:

| Move | Resource | Cost | Power | Scaling | Accuracy | Damage | Mechanic |
|---|---|---:|---:|---|---:|---|---|
| King’s Cleaver | None | 0 | 18 | Strength | 92 | Physical | `basic_attack` |
| Iron Decree | None | 0 | 25 | Strength, Intuition | 80 | Physical | `heavy_attack` |
| Black Banner Flame | Mana | 8 | 17 | Intelligence, Spirit | 88 | Magical | `basic_attack` |
| Tyrant’s Ruin | Mana | 14 | 26 | Strength, Intelligence | 75 | Hybrid | `heavy_attack` |

## Shared Enemy Action Policy

Every M10 enemy uses the same narrow policy:

1. Gather authored moves that are legal and currently affordable.
2. Select uniformly from that collection.
3. Resolve the selected move against the player.

Mana moves are excluded when the enemy cannot afford them. Each enemy retains
at least one zero-cost damaging move. Enemy Super, Defend, healing, summoning,
phases, statuses, tactical coordination, and advanced AI are not part of M10.

Selecting a move does not spend Mana. Accepted move resolution spends the
authored resource cost through `CombatResolver`.

## Final Boss Composition

The only Goblin Lord encounter is the final surface encounter:

```text
1 Goblin Lord
1 Goblin
1 Goblin Warrior
```

Authored composition order:

```text
Goblin Lord
Goblin
Goblin Warrior
```

There is no earlier Lord encounter, rematch, reinforcement phase,
transformation, or generic boss-phase system in M10.

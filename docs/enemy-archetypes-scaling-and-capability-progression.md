# Enemy Archetypes, Scaling, and Capability Progression

## Core Design Principle

Dungeon Drifters uses **base enemy archetypes with location-based scaling**.

Each enemy archetype owns its baseline identity:

- ~~base stats~~
- ~~move set~~
- resistances
- behavior
- rewards
- visual asset
- combat role

Enemy strength is not tied directly to the player’s level or build. Instead, the dungeon, region, or encounter tier applies a modifier to the archetype when creating its runtime state.

```text
Enemy archetype
    +
Dungeon or encounter tier
    =
Encounter-specific EnemyState
```

This allows the same enemy archetype to appear in multiple parts of the game at different levels of numerical strength without creating duplicate enemy classes.

---

## Archetype and Tier Separation

A canonical enemy definition might look like:

```text
Goblin

Base HP: 40
Base Strength: 5
Moves:
- Slash
- Jumping Slash
```

An encounter can then request:

```text
Goblin +0
Goblin +1
Goblin +2
Goblin +3
```

The tier modifies the Goblin’s baseline values:

```text
~~Goblin +0 = base values~~
Goblin +1 = base values × tier 1 modifier
Goblin +2 = base values × tier 2 modifier
Goblin +3 = base values × tier 3 modifier
```

The exact modifier can affect:

- HP
- mana
- physical and magical output
- defenses
- resistances
- EXP
- gold
- item rewards

The Goblin archetype still controls its ~~identity~~, ~~moves~~, and behavior. The tier controls its numerical strength.

A stronger ordinary Goblin does not require separate classes such as:

```text
WeakGoblin
MediumGoblin
StrongGoblin
LateGameGoblin
```

Instead, the runtime can eventually be created through a tier-aware interface such as:

```python
EnemyState(
    definition=Goblin(),
    tier=2,
)
```

or:

```python
spawn_enemy("goblin", tier=2)
```

Internally, the data remains explicit:

```text
~~archetype: goblin~~
tier: 2
```

The displayed name may be:

```text
Goblin +2
```

---

## Three Independent Enemy Dimensions

Enemy design is divided into three separate dimensions.

### 1. Archetype

The archetype determines:

- ~~identity~~
- ~~move names and effects~~
- physical and magical distribution
- resistances
- behavior
- role
- visual asset

### 2. Stage or Rank

The stage or rank determines the expected size of the kit and which combat systems may be available.

### 3. Tier

The tier determines numerical strength relative to the base archetype.

```text
Archetype = what the enemy is
Stage or rank = how mechanically complex it is
Tier = how numerically strong it is
```

A late-game Goblin can therefore remain mechanically simple while receiving higher stats. A Goblin Captain or Goblin Shaman is a separate archetype because it has a different role, kit, or behavior.

```text
Goblin +3          stronger ordinary Goblin
Goblin Captain +1  elite physical archetype
Goblin Shaman +1   healing or support archetype
Goblin King        boss archetype
```

---

## Enemy Capability Progression

Enemy stage establishes the default capability budget.

| Stage | Default move structure | Available systems |
| --- | --- | --- |
| Early | Physical moves | Defend, HP, mana |
| Mid | Physical moves plus 1 magic move | Defend, HP, heal, mana |
| End | Physical moves plus 2 magic moves | Defend, HP, heal, mana |
| Boss | Physical moves plus 2 magic moves | Defend, HP, heal, Super, mana |

These are defaults, not rigid physical-to-magic ratios.

An archetype may distribute its move budget differently:

```text
Front-line knight:
- 3 physical
- 1 magic

Cultist:
- 1 physical
- 3 magic

Elemental:
- 0 physical
- 4 magic

Spellblade:
- 2 physical
- 2 magic

Mid-game mage:
- 1 physical
- 2 magic
```

The stage controls the size of the capability budget. The archetype decides how that budget is spent.

---

## Healing Rules

Healing is an **authored capability**, not universal enemy behavior.

Mid-game and later stages may support healing, but that does not mean every enemy at those stages automatically heals.

Enemies that may reasonably heal include:

- shamans
- clerics
- alchemists
- regenerating creatures
- support units
- elite captains
- bosses

Enemies that do not have a healing identity should not receive generic recovery behavior.

A sewer rat, ordinary skeleton, brute, or basic Goblin should not repeatedly heal simply because it appears in a later dungeon.

Healing should exist as either:

- a structured healing move
- an explicit AI capability
- a defined regeneration trait

It should not be hard-coded as a universal low-HP action inside Battle.

---

## Mana Rules

~~All enemies may retain a mana field through the shared combat contract.~~

An enemy with no magical abilities can use:

```text
Mana: 0/0
```

or leave mana unused.

This preserves a consistent runtime shape without implying that every enemy has access to magic.

---

## Encounter Composition

Once archetypes and runtime tiers are separated, encounters become data-driven compositions.

```text
Dungeon 1:
- Goblin +0
- Slime +0

Dungeon 4:
- Goblin +2
- Slime +1
- Goblin Captain +0

Late Dungeon:
- Skeleton Archer +3
- Ash Cultist +2
- Orc +3
```

Dungeon construction becomes a matter of choosing:

- archetypes
- tiers
- quantities
- formations
- encounter roles

This reduces the need to program every encounter as a unique case.

---

## Numerical Scaling Does Not Require Kit Expansion

A later version of an ordinary enemy does not automatically receive more moves, healing, or boss mechanics.

```text
Early Goblin:
- 2 moves
- low stats

Later Goblin:
- same 2 moves
- stronger tier-scaled stats

Goblin Captain:
- separate archetype
- broader physical kit

Goblin Shaman:
- separate archetype
- healing or support behavior

Goblin King:
- boss archetype
- full kit and Super
```

This avoids two undesirable systems:

1. enemies automatically matching the player’s level everywhere
2. ordinary enemies receiving oversized kits only because they appear later

Enemy complexity is based on rank and identity. Enemy strength is based on encounter tier.

---

## Systemic Asset Reuse

The same archetype can be reused across multiple regions and difficulty bands.

One Goblin archetype can provide:

- ~~one base definition~~
- ~~one move kit~~
- one visual asset
- multiple tiers
- multiple regions
- multiple reward bands
- multiple encounter combinations

A `Goblin +3` can be substantially more dangerous than a `Goblin +0` without requiring an entirely new enemy asset.

New assets and new archetypes should be reserved for enemies that materially change combat:

```text
Goblin +2          reused archetype
Goblin Captain     new role and kit
Goblin Shaman      support and healing role
Goblin King        boss asset and boss behavior
```

This allows Dungeon Drifters to produce more encounter variety from a controlled set of authored assets while reserving development effort for enemies that genuinely change player decision-making.

---

## Design Outcome

The final enemy model separates identity, complexity, and strength:

```text
Base archetype
    defines ~~identity~~ and behavior

Stage or rank
    defines available combat capabilities

Tier
    defines numerical strength

~~EnemyState
    combines them for one encounter~~
```

This makes it easy to place any enemy at an appropriate strength level, reuse existing assets intelligently, preserve clear enemy identities, and expand dungeon content without duplicating classes or hard-coding every encounter.

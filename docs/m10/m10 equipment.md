# M10 Equipment Contract

M10 uses the existing signature weapons as the complete equipment content for
the surface route. This is an integration and inspection milestone, not the
implementation of the future signature-weapon progression system.

## Supported Equipment

M10 supports the existing `weapon` equipment slot and the four authored
signature weapons:

| Drifter   | Weapon               | Weapon type            | Current stat bonuses                  |
|-----------|----------------------|------------------------|---------------------------------------|
| Branoc    | Sunder-Spire         | Great Flamberge        | Strength +3, Constitution +1          |
| Azhvielle | Needle of Plain Iron | Ritual Needle          | Intelligence +3, Spirit +1            |
| Zhaivra   | Sathren              | Alchemical Recurve Bow | Dexterity +3, Intuition +1            |
| Joruun    | Sky-Needle           | Conductive Shakujō     | Spirit +2, Dexterity +1, Intuition +1 |

Existing intended-wielder restrictions and authored weapon data remain
authoritative. Signature weapons are not routinely replaced during M10.

## Effective Values

An equipped weapon contributes its current stat bonuses through the existing
`PlayerState.effective_stat()` path:

```text
effective stat = permanent character stat + equipped weapon bonus
```

Equipping or unequipping a weapon must not mutate permanent base attributes.
CombatResolver continues to consume effective values through the existing
combatant contract.

Weapon bonuses do not dynamically change maximum HP or maximum Mana during
M10. Maximum-resource progression remains controlled by level and permanent
character progression.

## Weapon Tab

The M10 Weapon tab is read-only inspection. It may display:

- weapon name
- weapon type
- intended wielder
- currently equipped stat bonuses

Example:

```text
Sunder-Spire
Great Flamberge
Strength +3 | Constitution +1
```

Building the Weapon tab must not equip, unequip, replace, refine, dismantle,
or otherwise mutate equipment or player state. Presenter and view construction
remain non-consuming.

## Explicit Non-Goals

M10 does not implement:

- refinement levels
- component slots or installed components
- physical or mystical weapon branches
- generated prefixes or suffixes
- weapon replacement or randomized weapons
- weapon loot generation
- dismantling or salvage
- crafting or refinement materials
- weapon durability
- weapon-specific move rewrites
- dynamic maximum HP or Mana from equipment

Those remain governed by
`docs/signature-weapon-progression.md` as future design direction and are
outside the M10 equipment milestone.

## M10 Gate

The equipment gate passes when a session can:

```text
create a player
-> record effective combat values
-> inspect the equipped signature weapon
-> verify its current stat bonuses
-> confirm combat uses effective values
-> confirm permanent base values remain unchanged
```

The Weapon tab must not create a new equipment system or broaden the existing
signature-weapon content.

# Armor

## Status

Future equipment and loot-system direction.

This system is intentionally deferred until the current Dungeon Drifters Part One systems are complete enough to support it cleanly.

Do not interrupt active milestone work to add armor prematurely.

---

# Core Principle

Dungeon Drifters armor should not be a disposable gear treadmill.

A piece found early in the game must be capable of remaining a legitimate endgame choice if the player prefers its identity, stat profile, or effect.

```text
Find armor
-> equip it
-> upgrade it
-> keep it
-> swap it when desired
-> potentially use the same piece through the entire game
```

This is not transmog.

The player is not preserving the appearance of an obsolete item while secretly using the stats of another item.

The original item itself remains equipped, continues to improve, and can reach maximum progression.

A beginner helm can therefore be the helm a player uses for the entire game.

---

# Equipment Structure

The primary armor slots are:

```text
Helm
Chest
Gloves
Boots
```

Armor is separate from:

```text
Signature Weapons
Accessories
Consumables
Crafting Components
```

Signature weapons remain Drifter-specific progression systems and are not replaced by random weapon drops.

Armor and accessories are ordinary equippable loot and may be swapped between owned pieces.

---

# Loot Sources

Enemies, elites, bosses, chests, expeditions, and other reward sources may provide:

```text
Armor
Components
Accessories
```

Every drop should have value even when the player does not want to equip or use it directly.

A player may generally choose to:

```text
KEEP
-> retain the item or component

EQUIP
-> wear armor or accessories
-> swap between owned pieces

DISMANTLE
-> break unwanted loot into useful crafting resources or materials

SELL
-> convert unwanted loot into gold
```

Components are not worn as equipment.

They remain crafting, refinement, upgrade, or progression inputs according to the system that consumes them.

---

# Loot Value Principle

Drops should create choices, not obsolescence.

A useful drop can have several forms of value:

```text
Combat value
-> Do I want to equip this?

Build value
-> Does this piece support a different strategy?

Crafting value
-> Is this more useful dismantled?

Economic value
-> Would I rather sell it?
```

An item that is not an equipment upgrade should still be capable of being useful.

---

# Armor Ownership

Armor is persistent Drifter equipment.

A Drifter may equip one owned piece in each supported armor slot.

Conceptually:

```text
Drifter
├── Helm
├── Chest
├── Gloves
└── Boots
```

Armor ownership and equipped state must be persistent.

The player must be able to:

- inspect owned armor
- equip armor on an exact selected Drifter
- replace an equipped piece
- swap between owned pieces
- unequip where allowed by the final equipment rules
- save and reload exact ownership and equipped state

No equipment action should silently target a different Drifter.

---

# Permanent Upgrade Viability

Every valid armor piece should be capable of reaching the maximum supported armor progression.

The game must not make early armor mechanically disposable merely because it dropped earlier.

The intended progression is:

```text
early armor
-> continued investment
-> continued improvement
-> maximum armor progression
```

rather than:

```text
early armor
-> statistically obsolete
-> forced replacement
```

A later drop may still be preferable because of its identity, stat distribution, effect, or build interaction.

It should not automatically be superior merely because it came from a later floor.

---

# No Transmog Dependency

Dungeon Drifters should not require transmog to preserve favorite armor.

If a player wants to keep using an early helm, they should be able to keep using that actual helm.

```text
Preferred early helm
-> upgrade it
-> continue wearing it
-> reach maximum progression
```

The visual identity and mechanical identity remain attached to the same item.

A future cosmetic system may exist independently, but armor viability must not depend on cosmetic replacement.

---

# Armor Power Philosophy

Armor power should primarily come from investment and authored identity rather than the floor on which the item dropped.

Conceptually:

```text
Armor Power
=
Upgrade Progression
+
Authored Stat Profile
+
Piece Identity
+
Optional Special Effect
```

It should not primarily be:

```text
Armor Power
=
Drop Location
```

This allows early and late armor to remain meaningfully different without making early armor automatically worthless.

---

# Armor Identity

Different armor pieces should create different build choices.

Potential identity dimensions may include:

- defensive stat distribution
- HP support
- mana support
- offensive stat support
- Dexterity or initiative support
- resource interactions
- resistance
- status interactions
- build-specific bonuses
- conditional effects
- party interactions
- risk/reward effects

The exact stat and effect model should be designed when the armor system is implemented.

Do not prematurely lock specific numerical balance values.

---

# Rarity Philosophy

Rarity must not mean that lower-rarity armor is permanently incapable of endgame viability.

A higher-rarity item may provide:

- a more specialized identity
- unusual stat distributions
- uncommon effects
- more complex build interactions
- lower drop frequency
- harder acquisition requirements
- different upgrade economics

It should not simply mean:

```text
Common = bad
Legendary = strictly better
```

Every supported armor tier or rarity should remain compatible with the rule that a favored piece can reach maximum progression.

Rarity should create different choices, not invalidate earlier choices.

---

# Accessories

Accessories are separate from armor.

They are equippable, persistent, and swappable.

Their primary purpose should be build specialization rather than duplicating armor.

Conceptually:

```text
Armor
-> durable equipment foundation
-> stat profile
-> defensive and secondary build shaping

Accessories
-> specialized effects
-> build modifiers
-> situational interactions
```

Potential accessory slots may include:

```text
Ring
Amulet
```

Additional accessory slots should only be added if they serve a clear gameplay purpose.

Accessories may be:

- equipped
- swapped
- stored
- sold
- dismantled where supported
- persisted across save/load

The exact upgrade rules for accessories should be designed separately rather than assumed to match armor.

---

# Signature Weapon Separation

Signature weapons remain fundamentally different from armor and accessories.

```text
Signature Weapon
-> belongs to a specific Drifter
-> is not replaced by random weapon drops
-> progresses through its own component and refinement system

Armor
-> found as loot
-> owned
-> equipped
-> swapped
-> upgraded
-> can remain viable for the entire game

Accessories
-> found as loot
-> owned
-> equipped
-> swapped
-> focused on specialization
```

Random loot must not undermine the identity of signature weapons.

---

# Dismantling

Armor, accessories, and appropriate component loot may be dismantled when the relevant economy supports it.

Dismantling should convert unwanted drops into useful progression resources.

The exact outputs should be authored by item family or loot rules rather than improvised by platform clients.

Potential outputs may include:

- crafting materials
- armor upgrade materials
- component materials
- rarity-dependent resources
- specialized crafting inputs

Dismantling must be authoritative engine behavior.

Clients only request the action and display the result.

---

# Selling

Armor, accessories, and appropriate component loot may also be sold.

Selling gives the player an economic alternative to dismantling.

This creates a meaningful decision:

```text
unwanted drop
-> dismantle for progression resources

or

unwanted drop
-> sell for gold
```

The economy should avoid making one option universally correct.

Gold values, dismantle values, upgrade costs, and material scarcity should be tuned together after the complete loot and economy loop exists.

---

# Swapping and Build Experimentation

Owned armor and accessories should remain available for future use unless sold, dismantled, consumed, or otherwise deliberately removed.

The player should be encouraged to retain multiple useful pieces and swap them for different situations.

For example:

```text
Boss setup
-> defensive chest
-> resistance-focused accessory

General exploration
-> balanced armor
-> resource-oriented accessory

Special encounter
-> status-resistant helm
-> specialized ring
```

This allows equipment progression to support buildcraft without forcing the player to permanently abandon previous investments.

---

# Enemy and Reward Integration

Armor, accessories, and components should become part of the broader Dungeon Drifters reward economy.

Potential reward sources include:

- ordinary enemies
- elite enemies
- bosses
- treasure rooms
- chests
- expedition rewards
- merchants
- special events
- challenge rewards

Different enemies and locations may have different loot tendencies.

Later systems may use enemy archetypes, biome identity, depth, difficulty, or authored reward tables to influence what can drop.

The exact loot-generation rules should be designed alongside dungeon progression and economy rather than hardcoded into the armor system.

---

# Equipment Progression Goals

The armor system should satisfy all of the following:

- early armor can remain viable through the entire game
- every valid armor piece can reach maximum supported progression
- players are never forced to replace armor solely because it dropped earlier
- swapping armor remains useful
- armor identity matters
- rarity does not equal automatic superiority
- unwanted loot remains valuable
- dismantling supports progression
- selling supports the economy
- armor does not replace signature weapon progression
- accessories remain a separate build-specialization layer
- exact Drifter ownership is preserved
- equipment state survives save/load
- clients do not own equipment rules

---

# Persistence Requirements

The final implementation must persist at minimum:

- armor ownership
- armor identity
- upgrade state
- equipped armor per Drifter
- accessory ownership
- equipped accessories per Drifter
- any authored item-specific persistent progression
- dismantling and selling outcomes through normal inventory state

Save reconstruction must preserve the exact equipment state.

Loading a save must never:

- duplicate armor
- lose equipped items
- equip an item on the wrong Drifter
- reset upgrades
- recreate dismantled or sold items
- silently replace missing content definitions

Schema changes must use the normal Dungeon Drifters persistence migration rules.

---

# Presentation Requirements

Terminal, browser, Android, PC, and future clients should consume the same authoritative equipment state.

Clients may provide different presentation, but should expose equivalent gameplay information.

Useful views may eventually include:

```text
Armor Loadout
Owned Armor
Accessory Loadout
Owned Accessories
Item Inspection
Upgrade Preview
Dismantle Preview
Sell Preview
```

The engine decides:

- whether an item can be equipped
- which Drifter owns or equips it
- upgrade legality
- upgrade results
- dismantle legality and outputs
- sale legality and value
- resulting inventory state

The client displays those decisions.

---

# Implementation Boundary

This document defines future direction.

It does not authorize immediate implementation.

Armor should be added only when the surrounding systems are mature enough to support:

- stable equipment ownership
- inventory storage
- loot generation
- dungeon reward integration
- economy balance
- upgrade resources
- save migration
- exact Drifter equipment targeting
- presentation support
- browser and future Android parity

Do not reopen current sealed systems merely to add armor early.

---

# First Implementation Scope

When armor development begins, the first implementation should remain intentionally narrow.

A reasonable first proof would be:

```text
one armor slot
-> two armor pieces
-> exact Drifter equip
-> swap between owned pieces
-> one upgrade path
-> sell
-> dismantle
-> save
-> reload
-> exact reconstruction
```

Once that vertical slice is proven, expand to:

```text
Helm
Chest
Gloves
Boots
Accessories
Broader loot integration
Full upgrade economy
```

This keeps the system testable and avoids introducing the entire equipment economy in one uncontrolled change.

---

# Deferred Decisions

The following should remain deliberately open until implementation planning:

- exact armor stat formula
- exact maximum upgrade level
- exact upgrade costs
- armor rarity names
- rarity probabilities
- armor drop rates
- dismantle yields
- sale values
- accessory upgrade rules
- number of accessory slots beyond the initial design
- class or archetype restrictions, if any
- universal versus restricted armor eligibility
- armor set bonuses
- special-effect frequency
- biome-specific armor rules
- boss-exclusive armor
- PvP equipment normalization
- cosmetic systems

These decisions should be informed by the completed progression, economy, dungeon, and character-growth systems.

---

# Acceptance Rules

The armor system is successful only if:

```text
Favorite armor can remain favorite armor.

Investment can preserve an early piece through endgame.

Later drops create alternatives rather than mandatory replacements.

Unwanted loot still has crafting or economic value.

Armor and accessories remain swappable.

Signature weapons remain unique and non-replaceable.

The engine owns every equipment rule.

Save/load preserves exact ownership, upgrades, and equipped state.
```

The central rule is:

```text
Drops should create choices, not obsolescence.
```

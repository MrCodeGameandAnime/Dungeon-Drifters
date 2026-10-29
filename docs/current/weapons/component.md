# Weapon Components

This document defines the finalized names for the material families used to
make signature-weapon components. The playable Floor I baseline now has generic
material IDs, sources, recipes, weapon-specific component names, and gameplay
effects authored in game content. Exact balance remains tunable; higher-grade
sources, recipes, and components will be authored alongside later floors.

## Materials And Components

Materials are recipe inputs. A component is the weapon-specific part installed
in one of a Drifter's four signature-weapon slots. The material family describes
the slot's dominant modification material, not the complete physical makeup of
the part.

Slot families are fixed across all signature weapons:

| Slot | Material family |
|---:|---|
| 1 | Metal |
| 2 | Fiber |
| 3 | Timber |
| 4 | Cores |

The installed part's name is specific to its weapon and slot. The four family
names are shared so recipes and material progression can use one consistent
system.

## Finalized Material Names

| Tier | Metal | Fiber | Timber | Cores | First floor |
|---|---|---|---|---|---:|
| I - Early / common | Scrap metal <br> Basic fittings and striking surfaces | Cord <br> Simple bindings and grips | Softwood <br> Basic hafts, shafts, and limbs | Faded Core<br>Entry-level signature focus | 1 |
| II - Mid / uncommon | Iron <br> Sturdier weapon structures | Cotton <br> Reinforced wraps and strings | Hardwood <br> Stronger hafts, shafts, and limbs | Elemental core <br> Elemental component options | 2 |
| III - Late / rare | Steel <br> High-strength fittings | Silk <br> High-tension bindings and strings | Ironwood <br> Resilient weapon bodies | Overcharged core <br> Advanced signature effects | 3 |
| IV - End / mythic | Etheral Alloy <br> Mythic weapon structures | Carbon <br> Lightweight, durable bindings | Elderwood <br> Rare, durable weapon bodies | Singularity Core <br> Top-grade signature focus | 4 |

The material names shown here are final. This table does not establish exact
drop sources, abundance, recipe costs, weapon-specific component names, or
gameplay effects. Tier II-IV sources and recipes will be authored alongside
their floor content.

## Progression Rules

- Material grades I-IV align with weapon tiers and first appear on Floors I-IV,
  respectively. Earlier floors do not provide later-grade materials.
- Slot 1 uses Metal, slot 2 Fiber, slot 3 Timber, and slot 4 Cores.
- Tier V attempts use Grade IV materials; there is no Grade V material family.
- Recipe costs and Crafting awards are authored per recipe. They do not have to
  follow a fixed quantity pattern.
- Only successful crafting or improvement recipes award their authored
  Crafting progress. Dismantling does not award Crafting progress.
- Crafting a component at the Hub Merchant consumes its authored materials and
  directly installs it on the explicitly selected Drifter. The installed recipe
  is no longer offered for that Drifter. Component parts do not enter shared
  inventory, and alternate-part storage is deferred.
- Crafting and slot improvement are separate actions. Crafting does not change
  the slot's 0-100 improvement progress.
- Component identity and combat effects are authored separately from the
  material names in weapon content.

## Current Floor I Sources

The playable baseline uses generic Grade-I material IDs:

| Family | Working material ID | Current source |
|---|---|---|
| Metal | `grade_i_metal` | Dismantle Goblin Scrap |
| Fiber | `grade_i_fiber` | Dismantle Goblin Scrap |
| Timber | `grade_i_timber` | Dismantle Goblin Scrap |
| Cores | `grade_i_cores` | Goblin Lord reward; guaranteed on each defeat |

The player-facing names and source fiction can change later without changing
the fixed family mapping or the grade gates.

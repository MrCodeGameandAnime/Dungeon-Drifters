# Party And Expedition Core Loop

> **M6 contract correction (2026-11-10):** For M6, expeditions take 20 minutes of real elapsed time after confirmed launch, target only previously completed floors, grant the expedition pair a collective 20% of the secured dungeon XP base pool, and use only Training, Material, Equipment, and Recovery rewards actually eligible from that floor. M6 does not require a Floor IV route. Scouting, Story, Elite, pair-specific outcomes, and future full-party events while an assignment is outstanding remain M8 work. Interaction with the already-authored M4 Floor II helper and Floor III boss is recorded in the M6 Gate 0 review holds. The M6 milestone plan records the current reward-source audit and review holds. Broader possibilities in this document are not authorization to add them to M6.

This is the canonical design authority for the four-Drifter roster, active and
expedition assignments, expedition categories, experience distribution, and
reuniting the party. Dungeon risk, extraction, and economy are defined in
[Dungeon Progression, Difficulty, and Economy](dungeon-progression-difficulty-and-economy.md).
Individual character advancement is defined in
[Character Growth and Stat Scaling](character-growth-and-stat-scaling.md).

## Core Premise

The player controls a permanent roster of four Drifters.

For most dungeon runs, the roster is divided into two groups:

* **Dungeon Party:** Two Drifters actively enter the dungeon.
* **Expedition Party:** The other two Drifters complete a separate off-screen assignment.

The player develops all four characters over time, chooses pairings based on dungeon conditions, and reunites the full team for major boss battles.

The system should encourage favorite characters without allowing the player to permanently ignore the rest of the roster.

---

# 1. Return to the Hub

Every major gameplay cycle begins at the central hub.

At the hub, the player can:

* inspect all four Drifters
* equip weapons, armor, relics, and consumables
* review character levels and abilities
* examine available dungeons
* examine available expeditions
* review known enemy traits and environmental hazards
* speak with characters
* advance story events
* prepare the next deployment

The hub is where the player manages the entire group.

---

# 2. Select a Dungeon

The player chooses from available dungeons.

Each dungeon displays known or rumored information:

* recommended level
* expected enemy types
* environmental conditions
* likely damage resistances
* likely weaknesses
* possible materials
* story relevance
* required Drifters, if any
* expedition duration
* boss progress

Information may be incomplete when the dungeon is first discovered.

The player can learn more through:

* previous attempts
* NPC dialogue
* expedition reports
* discovered documents
* character knowledge
* purchased intelligence
* scouting abilities

---

# 3. Determine Party Restrictions

The selected dungeon establishes how much freedom the player has when choosing the active pair.

## Free-Choice Dungeon

The player chooses any two Drifters.

Example:

* Branoc and Zhaivra enter.
* Joruun and Azhvielle go on expedition.

These dungeons emphasize party composition, experimentation, and mechanical advantages.

## Character Story Dungeon

One Drifter is mandatory because the dungeon is tied to that character’s story.

Example:

* Branoc is required.
* The player chooses Branoc’s partner.
* The remaining two Drifters form the expedition party.

This preserves player choice while ensuring the relevant character participates in their own story.

## Locked-Pair Story Dungeon

Two specific Drifters are required.

This is used when:

* both characters share the story
* their conflict must develop
* their abilities are central to the dungeon
* the mission requires a specific relationship

Locked pairs should be uncommon so they feel narratively important.

## Full-Party Event

All four Drifters enter together.

This is reserved primarily for:

* dungeon bosses
* major story battles
* final encounters
* rare survival sequences
* events where the party reunites against a shared threat

---

# 4. Choose the Dungeon Party

The player selects two available Drifters for the active dungeon run.

The decision should be influenced by several factors.

## Personal Preference

The player may naturally favor a particular pair.

The game allows this, but repeated use creates tradeoffs.

## Dungeon Matchup

Certain characters perform better in specific conditions.

Examples:

* Branoc excels in attrition-heavy dungeons and against direct physical threats.
* Zhaivra excels when enemy weaknesses, materials, or environmental reactions can be exploited.
* Joruun excels when wind, water, lightning, movement, or environmental manipulation matter.
* Azhvielle excels against magical threats, curses, spirits, or enemies vulnerable to dangerous high-output abilities.

## Party Synergy

Every two-character combination should eventually have:

* useful mechanical interactions
* unique dialogue
* different tactical strengths
* identifiable weaknesses
* possible combination abilities

With four Drifters, there are six possible two-character pairings.

Each pairing should feel valid, even when it is not optimal for a particular dungeon.

## Character Development

The player may bring a less-used Drifter to:

* close a level gap
* unlock abilities
* improve equipment mastery
* advance a relationship
* complete a personal objective
* prepare them for an upcoming required dungeon

---

# 5. Assign the Expedition Party

The two Drifters not entering the dungeon are assigned to an expedition.

Expeditions occur alongside the active dungeon run.

For M6, an assignment lasts 20 minutes of real elapsed time from confirmed
launch. Gameplay inputs, route nodes, and repeated commands do not advance its
timer. The clock is persisted in UTC and evaluated by shared game logic; clients
only display the resulting state. Assignment rewards settle when the outing
ends, not when a player repeats an event or reloads. The
[Dungeon Progression, Difficulty, and Economy](dungeon-progression-difficulty-and-economy.md)
document owns the M6 energy values and clock policy.

## Common Expedition Objectives

Expedition categories describe the primary reward focus. Objectives describe
the specific work assigned to the pair.

Long-term expedition objectives may include:

* material gathering
* weapon or armor recovery
* scouting undiscovered dungeon areas
* hunting specific enemies
* gathering provisions
* investigating rumors
* locating merchants
* recovering lost documents
* searching for rare crafting components
* assisting settlements
* mapping dangerous regions

## Expedition Categories

M6 exposes only the four categories below. The wider list is future design
space and does not authorize additional M6 categories or rewards.

### Training Expedition

Primary reward: a collective expedition XP pool equal to the M6 target of 20%
of the secured dungeon XP base pool, shared between the two expedition
Drifters, then individually modified by each recipient's existing M3 Intuition
bonus. The exact M6 split and integer convention are recorded in the milestone
plan and remain subject to balance validation.

### Material Expedition

Primary reward: a fixed, deterministic material outcome actually obtainable
from the selected completed floor. Do not invent a material or award a grade
that the floor's authored content cannot produce.

### Equipment Expedition

M6 may award only authored M5 armor/equipment instances actually available
through the selected completed floor. The M6 Gate 0 audit currently finds no
live armor reward source on Floors I-III; those category/floor combinations
remain unavailable unless an eligible source is separately authored and
approved. No replacement signature weapons, stackable signature parts, or
procedural jewelry are permitted.

### Recovery Expedition

M6 may award only M2 carryable supplies actually available through the selected
completed floor. The current Floor I-III route content has no carryable supply
drops, so Recovery outcomes cannot be fabricated to fill the category.

### M8 Scouting Expedition

Primary reward: dungeon information, such as enemy types, weaknesses, hazards,
hidden paths, boss mechanics, or treasure locations.

### M8 Story Expedition

Primary rewards: narrative progress, character events, hidden lore, and new
locations. Story completion should not require payment.

### M8 Elite Expedition

Primary reward: rare or endgame resources. These assignments consume more energy
and may require specific character combinations or roster strength.

## Expedition Character Strengths

Pair-specific outcomes are deferred to M8. They are not part of the initial
M6 reward calculation.

Each Drifter may influence later expedition results differently.

Examples:

* Branoc improves survival and reduces injury risk.
* Zhaivra increases material quality and identification accuracy.
* Joruun increases unusual discoveries but may introduce unpredictable outcomes.
* Azhvielle improves magical artifact discovery while increasing danger.

The pairing itself may also affect results.

## Expedition Rewards

Later expedition content may return with:

* experience
* crafting materials
* equipment
* consumables
* currency
* maps
* rumors
* dungeon modifiers
* hidden routes
* character events
* future expedition opportunities

---

# 6. Experience Distribution

The active dungeon party receives full combat experience.

The M6 expedition pair receives the approved initial target of 20% of the
secured dungeon XP base pool collectively, not 20% per Drifter. Split the pool
deterministically, then apply each Drifter's own M3 Intuition bonus to that
Drifter's share. M6 must validate this supplementary award against existing
level thresholds; it does not change full- or partial-extraction math.

The Floor III boss XP contract remains the M4 rule: the four participating
Drifters share the authored boss award, then receive their own Intuition
bonuses. Pre-boss XP remains attributed to the active pair that earned it.
This expedition section does not redefine that rule.

This creates three valid approaches.

## Balanced Rotation

The player regularly changes party members.

Result:

* all four stay close in level
* more pairings are explored
* required story characters remain prepared
* equipment must be distributed thoughtfully

## Main Pair Focus

The player repeatedly uses the same two Drifters.

Result:

* the preferred pair becomes stronger
* the expedition pair remains somewhat behind
* future story requirements may force adaptation
* additional catch-up runs may become necessary

## Deliberate Grinding

The player keeps preferred mains while using optional dungeons to train the weaker characters.

Result:

* greater time investment
* more materials and equipment
* freedom to maintain a preferred playstyle
* reduced pressure from level differences

The system should pressure rotation without completely forbidding specialization.

---

# 7. Run the Dungeon

The selected pair enters the dungeon.

The active gameplay loop includes:

1. Explore a room or floor.
2. Encounter enemies, hazards, events, or choices.
3. Spend health, mana, consumables, and other resources.
4. Discover information or treasure.
5. Decide whether to continue, retreat, or change route.
6. Continue the independent 20-minute assignment timer; combat input does not
   accelerate it.
7. Repeat until the outing ends.

The dungeon should test both individual character strength and the selected pairing.

Some dungeons strongly favor certain Drifters.

Others require specific characters through the story.

The game should distinguish between:

* **Hard requirement:** A character must enter because of the narrative or dungeon structure.
* **Strong advantage:** A character is especially effective but not mandatory.
* **Alternative solution:** An unusual party can still succeed through equipment, preparation, or player skill.

---

# 8. Resolve the Expedition

At outing termination, reunite the roster and evaluate the assignment once. A
completed assignment freezes an outcome/report; an assignment under 20 minutes
is incomplete and grants no category reward or expedition XP. A completed
assignment retains its eligible category rewards even if the active pair dies;
its Training XP still uses only dungeon XP secured under existing rules.

The resulting Hub report remains claimable until claimed. Claim grants its
frozen reward to the recorded expedition pair exactly once. Save/load and
retries cannot reroll or duplicate the outcome.

The M6 report includes only its eligible Training, Material, Equipment, or
Recovery outcome. Later reports may include:

* experience earned
* materials recovered
* equipment found
* injuries or complications
* discovered information
* new locations
* relationship events
* special outcomes caused by the selected pairing

The expedition should feel like meaningful roster activity, not passive compensation for unused characters.

The player should occasionally receive something from the expedition that changes the next decision.

Example:

> Joruun and Azhvielle discovered a flooded passage beneath the next dungeon. Lightning attacks will be unusually dangerous there, but the route bypasses the armored gatekeepers.

---

# 9. Reunite at the Hub

All four Drifters return to the hub.

The player then:

* distributes rewards
* heals or treats injuries
* upgrades equipment
* crafts items
* unlocks abilities
* reads expedition reports
* advances character conversations
* receives new dungeon information
* decides who needs active experience
* prepares the next split

This completes one standard gameplay cycle.

## Standard Cycle

**Choose dungeon
→ identify restrictions
→ select active pair
→ assign expedition pair
→ complete dungeon
→ resolve expedition
→ reunite at hub
→ redistribute resources
→ repeat**

---

# 10. Boss Progression

Each major dungeon region builds toward a boss.

Progress may require:

* clearing several dungeon runs
* discovering the boss location
* gathering keys or ritual components
* completing character objectives
* weakening the boss
* unlocking the arena
* learning boss mechanics
* finishing related expeditions

The normal two-and-two structure prepares the roster for the eventual full-party battle.

---

# 11. Full-Party Boss Battle

When the boss arena becomes available, all four Drifters enter together.

No one remains on expedition.

The boss battle is the convergence point for:

* character levels
* collected equipment
* learned abilities
* discovered weaknesses
* expedition rewards
* party relationships
* previous dungeon choices

Boss combat should feel mechanically different from standard two-character combat.

Possible differences include:

* four active Drifters
* multiple enemies or boss components
* battlefield phases
* party-wide attacks
* coordinated defensive mechanics
* character-specific responsibilities
* combination abilities
* environmental interactions
* character switching or turn-order manipulation
* major story dialogue during combat

The player’s preferred pair may still form the center of their strategy, but victory should reward maintaining and developing the entire roster.

---

# 12. Post-Boss Resolution

After defeating the boss:

* all four receive full boss experience
* the region’s story advances
* personal character arcs may change
* new equipment tiers become available
* new expeditions unlock
* the next dungeon region opens
* relationships may develop based on prior pairings
* the roster returns to the normal two-and-two structure

The next region should introduce new reasons to reconsider established mains.

---

# 13. Long-Term Character Pressure

The system keeps all four Drifters relevant through several overlapping pressures.

## Mechanical Pressure

Different enemies, hazards, and environments favor different characters.

## Narrative Pressure

Story dungeons require particular Drifters.

## Level Pressure

Expedition characters earn less experience than active characters.

## Equipment Pressure

The player may not have enough top-tier equipment for everyone at once.

## Relationship Pressure

Pairings unlock dialogue, trust, conflict, and possibly combination abilities.

## Boss Pressure

All four must eventually fight together.

No single rule forces constant rotation. The combined systems naturally encourage it.

---

# 14. Example Gameplay Sequence

## Run One

Available dungeon:

**The Drowned Reliquary**

Known conditions:

* flooded chambers
* armored undead
* conductive surfaces
* magical seals

The player chooses:

* Dungeon Party: Branoc and Joruun
* Expedition Party: Zhaivra and Azhvielle

Reasoning:

* Branoc can withstand the armored undead.
* Joruun can manipulate the flooded environment.
* Zhaivra and Azhvielle are assigned to search for alchemical materials.

Results:

* Branoc and Joruun receive full experience.
* Zhaivra and Azhvielle receive reduced experience.
* The expedition finds a reagent that weakens magical barriers.
* The dungeon pair discovers the boss arena but cannot enter.

## Run Two

A story chamber requires Azhvielle.

The player chooses:

* Dungeon Party: Azhvielle and Zhaivra
* Expedition Party: Branoc and Joruun

Reasoning:

* Azhvielle is mandatory.
* Zhaivra can use the recovered reagent.
* Branoc and Joruun remain productive through expedition work.

Results:

* The magical barrier is destroyed.
* Azhvielle’s personal story advances.
* Branoc and Joruun discover a hidden approach to the boss arena.
* All four are now close enough in level to proceed.

## Boss Run

All four enter the arena.

The battle uses everything established previously:

* Branoc holds the boss’s attention.
* Zhaivra exploits the recovered material.
* Joruun manipulates the flooded arena.
* Azhvielle breaks the magical seals.
* The full party defeats the boss.

The region concludes, and the roster returns to the hub.

---

# 15. Core Design Identity

Dungeon Drifters becomes a game about managing four adventurers who repeatedly separate and reunite.

Normal dungeons ask:

> Which two Drifters should handle this threat?

Expeditions ask:

> What should the other two accomplish while the active party is away?

Story dungeons ask:

> Which companion should accompany the character whose past is being confronted?

Boss battles ask:

> Did the player prepare the entire group well enough to fight together?

The player may have mains, but the game is ultimately built around the complete roster.

# M10 Multi-Enemy Battle Contract

## Status

Approved implementation plan for one Drifter fighting one to four independent
enemies during the M10 surface route.

## Purpose

M10 expands the current one-player-versus-one-enemy Battle into an ordered
one-player-versus-many encounter while preserving the established ownership
boundaries:

```text
Battle
  orchestrates opportunities, targeting, lifecycle completion, and winner checks

CombatResolver
  resolves one actor, one move, and one exact target

CombatState
  owns encounter-local state and per-actor accepted-action lifecycle

BattlePresenter
  translates exact combat state into immutable views

TerminalBattleUI
  renders views and returns semantic input
```

The first architecture gate is one Drifter against two Goblins. The same
contract supports every M10 composition, including the final three-enemy
Goblin Lord encounter.

## Non-Goals

M10C does not add:

- party combat or ally targeting
- multi-target or area attacks
- enemy healing, Defend, Super, or item use
- speed-based initiative
- tactical coordination or threat selection
- reinforcements, summons, or encounter phases
- a generic formation system
- a broad Battle or CombatResolver rewrite

## Battle Participants

The canonical Battle boundary receives one exact `PlayerState` and an ordered
collection containing one to four exact `EnemyState` objects. The collection
is supplied in authored encounter-composition order. Empty collections and
collections larger than the supported M10 maximum are rejected explicitly.

Battle does not load route data, create enemy archetypes, own encounter rewards,
or own persistent encounter completion.

The same `EnemyState` object cannot appear twice in one Battle. Duplicate
archetypes require separate runtime objects with independent HP, Mana, and
identity-based temporary state.

M10 presentation supports one, two, three, or four enemies. The enemies are not a
party and have no shared HP, Mana, status, or action state.

## Runtime Target Identity

Battle assigns each enemy one immutable encounter-local target ID from authored
position:

```text
enemy_1
enemy_2
enemy_3
enemy_4
```

Target IDs:

- remain stable for the lifetime of the Battle
- do not change when another enemy is defeated
- are not display names or object memory addresses
- are not saved outside active Battle state
- are the only values accepted by semantic target-selection input

Resolution still receives the exact selected `EnemyState` object. CombatState
continues to use object identity for mechanical ownership.

## Display Labels

Enemies remain in authored order for presentation and action sequencing.

When a display name occurs once, retain the authored name. When it occurs more
than once, number every occurrence in authored order:

```text
Goblin 1
Goblin 2
```

```text
Goblin Shaman 1
Goblin Shaman 2
```

Numbering is presentation metadata. Resolver and status logic never branch on
numbered labels. Defeated enemies retain their original position and label.

## Compatibility Boundary

The canonical runtime surface is `Battle.enemies`, an immutable ordered tuple.

Single-enemy construction remains accepted temporarily and normalizes to a
one-element tuple so existing M9 tests and callers can migrate incrementally.

Any compatibility `foe` accessor is valid only when exactly one enemy exists.
It must fail explicitly for a multi-enemy Battle rather than returning the first
enemy.

The canonical immutable presentation surface is `BattleView.enemies`. A
temporary `BattleView.enemy` compatibility accessor follows the same
single-enemy-only rule.

Battle accepts the enemy collection directly. M10C does not introduce an
encounter-runtime owner inside Battle.

## Initiative

Initiative remains a single side-level roll at encounter start using the
existing injectable RNG seam. The result is either player-side first or
enemy-side first.

The initiative log reports the winning side. Enemy-side initiative must not be
rendered as though only the first authored enemy won initiative.

Dexterity, archetype, roster position, and enemy count do not modify initiative
in M10.

Player-side initiative produces:

```text
player opportunity
enemy phase in authored order
player opportunity
enemy phase in authored order
```

Enemy-side initiative produces:

```text
enemy phase in authored order
player opportunity
enemy phase in authored order
player opportunity
```

An enemy phase gives one opportunity to every currently living enemy in
authored order. It is not one shared accepted action.

## Enemy Action Sequence

For each authored enemy position during an enemy phase:

1. Skip the position when that enemy is already defeated.
2. Check the exact enemy for Frozen or Stun opportunity suppression.
3. If suppressed, record typed outcomes and continue without resolver or
   lifecycle execution.
4. Select uniformly from that enemy's currently legal affordable moves.
5. Resolve against the player or itself according to authored `TargetType`.
6. Complete that exact enemy's accepted-action lifecycle once.
7. Record lifecycle outcomes.
8. Evaluate victory or defeat immediately.
9. Continue only while the encounter remains active.

An enemy move selected from the legal affordable set is expected to be accepted.
An unexpected resolver rejection is an invariant failure. Battle does not
reroll, retry, advance lifecycle, or silently convert it into a skipped turn.

The existing enemy move-selection policy remains unchanged. M10C adds no
archetype-specific AI.

## Player Action and Target Sequence

The player retains the existing Actions, move, inventory, and Back workflows.
Self-targeted actions resolve without enemy target selection.

For an enemy-targeted move:

- exactly one living enemy is auto-targeted
- two or more living enemies require explicit Target Selection after the move
  is chosen

The sequence is:

```text
Actions
-> choose Attack or Super
-> choose authored move
-> choose target when multiple living enemies exist
-> resolve against the exact selected enemy
```

This preserves move-first navigation and avoids asking for an enemy target
before a self-targeted utility move such as Brace.

## Semantic Target Input

Add a typed interaction phase equivalent to:

```python
InteractionPhase.TARGETS
```

Add immutable semantic input equivalent to:

```python
ChooseTarget(target_id: str)
```

Add an immutable target option view containing at least:

- target ID
- selection number
- unique display label
- current and maximum HP
- temporary-state labels
- enabled state
- typed disabled reason when applicable

Target input uses only the offered target ID. Terminal numbers and labels are
adapter concerns.

An invalid, stale, defeated, absent, or disabled target:

- emits a typed target-unavailable rejection
- spends no Mana or Super
- consumes no prepared payload
- consumes no RNG
- changes no CombatState
- advances no lifecycle or phase
- leaves Target Selection open

## Target Navigation

Back from Target Selection returns to the move-selection phase that offered the
move and clears the selected move. It changes no resource, temporary state, or
turn-scoped log.

Back from move selection retains its existing return to Actions. Navigation,
invalid input, stale input, and target inspection never begin a displayed turn.

## Target-Sensitive Move Presentation

Some presentation depends on the exact target, especially Joruun's Conductive
and Turbulence setup.

Before target selection, the move list must not infer target-specific facts from
the first enemy, strongest enemy, or an aggregate of enemy states.

During Target Selection, each option may expose the selected move's exact
resolution label and target-sensitive tags. The same authored Lightning Palm may
preview Lightning Storm for one target while remaining Lightning Palm for
another.

The stable move-selection identity remains the authored move name. Presentation
does not mutate the authored Move.

When one living enemy is auto-targeted, existing target-sensitive presentation
uses that exact enemy.

## Accepted-Action Lifecycle

Every accepted action completes lifecycle exactly once for its exact actor.

For an accepted player action, Battle supplies the ordered enemy collection as
opposing combatants and preserves the exact selected target as presentation
context. For an accepted enemy action, the player is the sole opponent.

Existing lifecycle rules remain:

- `CombatState.turn_count` increments once per accepted actor action
- player Heal cooldown decreases only after accepted player actions
- status damage advances only for the actor that completed the action
- Burn resolves before Poison, which resolves before Frostbite
- defeated-target cleanup occurs before the next opportunity
- winner evaluation occurs immediately after lifecycle outcomes

One player action followed by four accepted enemy actions increments turn count
five times.

## Defend and Brace

Defend and Brace protection apply to the next accepted opposing action, not an
entire enemy phase.

```text
player Defends or Braces
-> first enemy opportunity is suppressed
-> protection remains active
-> next enemy performs an accepted action
-> protection applies and clears
-> later enemies act without that protection
```

A Frozen or Stun skip is not accepted and does not clear Defend or Brace.
Brace's Heavy follow-up remains armed until its existing accepted Heavy-attempt
consumption rule is satisfied.

## Opportunity Suppression

Frozen remains higher precedence than Stun for every combatant. Only one
suppression is consumed per opportunity; the second remains pending.

Suppressed opportunities perform no resolver call, lifecycle, turn-count
advance, status tick, Heal cooldown change, resource mutation, Defend clearing,
or Brace clearing.

A suppressed player opportunity proceeds to the full living-enemy phase. A
suppressed enemy opportunity proceeds to the next living enemy in authored
order.

## Winner Resolution

Winner evaluation occurs after every direct action and its lifecycle outcomes,
before another actor receives an opportunity.

```python
player_alive = player.is_alive()
all_enemies_defeated = all(not enemy.is_alive() for enemy in enemies)
player_won = all_enemies_defeated and player_alive
```

Consequences:

- defeating one enemy does not end a multi-enemy encounter
- defeated enemies never act again
- all enemies must be defeated for victory
- player death ends the encounter immediately
- later enemies do not act after player death
- simultaneous player and final-enemy death is defeat
- status damage can end combat before the next opportunity

Battle continues returning `"player"` or `"enemy"`.

## Defeated Enemy State

A defeated enemy:

- remains visible with HP 0 and a Defeated label
- remains in authored position
- is absent from target options
- receives no action opportunity
- cannot receive later damage, status, or resource mutation
- retains no temporary status state

No automatic retargeting occurs after selection. A target that is invalid at
resolution is rejected rather than redirected.

## Exact Status Ownership

All existing identity-based mechanics remain exact:

- Burn, Poison, Frostbite, Frozen, and Stun attach to one exact target
- Frost charges remain keyed by exact source-target identity
- Conductive and Turbulence remain keyed by exact source-target identity
- Gravemantle Break remains linked to one exact enemy
- Arcane Instability remains linked to its exact actor
- Brace and Defend remain linked to their exact owners

No status is copied, aggregated, or transferred when another enemy is selected
or defeated.

When Overcharge is consumed against a different enemy, the spell receives the
captured Overcharge bonus but not the old target's captured Break. The old setup
is still cleared exactly once.

Frost presentation queries the exact player-enemy pair for each panel.
Independent Frost charges are never summed or selected by maximum count.

## Defeat and Encounter Cleanup

After an accepted action, cleanup applies to the exact defeated combatant before
another opportunity begins.

Target defeat clears target-owned and target-linked temporary state. Source
defeat clears source-linked Frost, Frozen, Frostbite, Conductive, Turbulence, and
other approved source-owned state without clearing another living source's
independent state.

Encounter completion discards the entire CombatState. Enemy runtime objects and
temporary statuses never persist into the overworld or next encounter.

## Presentation Contract

`BattleView` exposes an immutable ordered enemy collection. Each enemy view
contains its target ID, unique display label, resources, and exact temporary
labels.

The terminal renders all one to four enemy panels in authored order, without
overlap, with independent HP, Mana, and state labels, in framed and narrow
layouts. Defeated enemies remain visible.

The final inactive view shows all final combatant states and victory or defeat
without actionable controls.

## Semantic Log Contract

Log entries use unique numbered labels for duplicate enemies so damage, misses,
resource spending, outcomes, suppression, and status ticks remain attributable.

The current turn-scoped sequence is:

```text
accepted player result and lifecycle outcomes
-> enemy 1 result and lifecycle outcomes
-> enemy 2 result and lifecycle outcomes
-> enemy 3 result and lifecycle outcomes
-> enemy 4 result and lifecycle outcomes
-> victory or defeat when applicable
```

The next accepted player action clears the previous displayed turn. Target
selection, Back, invalid input, rejected actions, and suppression do not clear
the sequence.

The bounded presentation session must retain one maximum-complexity M10 player
turn with four enemy responses. If deterministic tests prove the existing cap
insufficient, increase it only enough for that complete turn; do not retain
encounter-wide history.

## Contract Impact

Expected narrow additions:

- `Battle.enemies`
- encounter-local target IDs
- `BattleView.enemies`
- immutable target option views
- `InteractionPhase.TARGETS`
- `ChooseTarget`
- typed target-unavailable rejection
- temporary selected-move state while target selection is open

Expected compatibility seams:

- single-enemy constructor normalization
- single-enemy-only `Battle.foe`
- single-enemy-only `BattleView.enemy`

No `Move`, `MoveResult`, `CombatOutcome`, CombatResolver action contract, or
authored enemy definition change is required.

## Ordered Implementation

### M10C-1 - Participant and View Contracts

- normalize one to four enemy participants
- assign stable target IDs and duplicate labels
- add immutable enemy and target views
- add semantic target input and phase
- preserve single-enemy compatibility

### M10C-2 - Targeted Player Resolution

- preserve move-first navigation
- auto-target one living enemy
- offer exact target selection for multiple living enemies
- reject stale or defeated targets without mutation
- compute target-sensitive presentation from the exact target

### M10C-3 - Ordered Enemy Phases

- side-level initiative
- authored-order living enemy opportunities
- one lifecycle and winner check per accepted action
- suppression per exact enemy
- immediate stop after player death or full enemy defeat

### M10C-4 - Presentation and Logging

- render one to four independent enemy panels
- retain defeated enemies visibly
- attribute logs with unique labels
- preserve turn-scoped history through all responses
- preserve inactive final views

### M10C-5 - Identity and Route Hardening

- two-Goblin architecture gate
- Warrior and Shaman pairs
- Elite plus Goblin
- Goblin Lord, Goblin, and Warrior finale
- exact status isolation and cleanup
- single-enemy regression

## Required Tests

### Participants and Targeting

- Empty collections, collections above four enemies, and duplicate runtime
  objects are rejected.
- Separate equal-archetype enemies remain independent.
- Target IDs and duplicate labels are stable and deterministic.
- Single-enemy compatibility cannot select the first enemy of a group.
- Self-targeted moves require no enemy target.
- One living enemy is auto-targeted.
- Multiple living enemies require semantic target selection.
- Either duplicate enemy can be selected exactly.
- Back returns to the correct move phase.
- Invalid, stale, and defeated target IDs preserve resources, payloads, RNG,
  CombatState, lifecycle, and visible log.
- Target-dependent Lightning Palm presentation uses the exact target.

### Initiative and Enemy Phases

- Both initiative results produce the approved side order.
- Every living enemy acts at most once per enemy phase in authored order.
- Defeated enemies are skipped.
- Enemy Mana remains independent.
- Unexpected enemy resolver rejection fails without lifecycle.

### Lifecycle and Winner Checks

- Every accepted action completes lifecycle exactly once.
- Turn count advances once per accepted actor action.
- Player statuses and Heal cooldown advance only after player actions.
- Enemy statuses advance only after that exact enemy acts.
- Winner evaluation follows every action lifecycle.
- Killing the player stops later enemies.
- Defeating one enemy does not end combat.
- Defeating the final enemy ends combat immediately.
- Simultaneous player and final-enemy death is defeat.

### Suppression and Protection

- Frozen and Stun affect only the exact enemy.
- Frozen precedes Stun across consecutive opportunities.
- Suppression performs no resolver, lifecycle, tick, or protection clearing.
- A suppressed player is followed by the normal enemy phase.
- Defend and Brace protect against the next accepted enemy action only.
- Brace Heavy follow-up survives unrelated enemy actions.

### Status Isolation

- Burn, Poison, and Frostbite remain target-specific and ordered per actor.
- Frost charges remain exact per source-target pair.
- Conductive and Turbulence on one enemy do not affect another.
- Gravemantle Break never affects another enemy.
- Different-target discharge clears setup without captured Break.
- Defeat cleanup preserves unrelated living state.
- No CombatState leaks into the next encounter.

### Presentation and Regression

- One, two, three, and four enemy panels render at supported widths.
- Defeated enemies remain visible and untargetable.
- Duplicate labels keep logs attributable.
- A complete player turn plus four enemy responses remains visible.
- Rejected targeting does not clear the turn-scoped log.
- Final inactive views offer no controls.
- Existing single-Goblin behavior and winner values remain compatible.
- Branoc, Azhvielle, Zhaivra, and Joruun mechanics remain compatible.

## Completion Gate

M10C is complete when one selected Drifter can fight every authored M10 enemy
composition, choose any living enemy exactly, survive deterministic ordered
enemy phases, preserve all identity-linked mechanics, see every combatant's
independent state, and win only after every required enemy is defeated.

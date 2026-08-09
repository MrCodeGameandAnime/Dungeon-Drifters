# Deferred Combat Mechanic — Momentum

## Status

**Deferred until after v0.3**

Momentum is a planned shared combat mechanic, but it is not part of the current v0.3 implementation scope.

It should remain documented as a future system rather than being treated as an active resource, baseline character mechanic, or dependency of the current combat resolver.

---

## Core Identity

Momentum represents a combatant maintaining control, pressure, and rhythm during an encounter.

It is not a spendable resource like Mana or Super.

Instead, Momentum temporarily improves critical-hit frequency while the combatant continues performing successfully.

```text
Successful offense
        ↓
Momentum increases
        ↓
Critical chance improves
        ↓
Critical hits can occur more frequently
```

Momentum rewards sustained execution rather than simple resource accumulation.

---

## Character Availability

Momentum is intended to be shared by every playable Drifter.

It is not exclusive to Branoc or any particular archetype.

Different characters may eventually interact with Momentum in different ways, but the underlying system should remain shared.

---

## Encounter State

Momentum is temporary combat state.

It should:

* begin at zero when an encounter starts
* exist only during the current encounter
* reset when the encounter ends
* not persist in `PlayerState`
* not appear as a permanent character resource
* not be represented by `Move.resource_type`

The likely future ownership boundary is:

```text
CombatState
└── MomentumState
```

---

## Momentum Gain

A successful damaging move grants a set amount of Momentum.

Momentum gain is associated with the resolved move or action result, not with every individual strike contained within the move.

```text
Successful damaging move
→ Momentum increases

Missed move
→ no Momentum gained
→ existing Momentum remains unchanged
```

Multi-hit moves have not yet been fully designed.

The current rule is only that a move does not automatically generate additional Momentum merely because its animation or resolution contains multiple strikes.

Individual moves may eventually define their own Momentum behavior.

---

## Momentum Preservation

Defending preserves Momentum.

A combatant should be able to maintain offensive rhythm by responding intelligently to incoming pressure rather than being forced to attack every turn.

```text
Defend successfully
→ Momentum remains active
```

Avoiding or sufficiently reducing incoming damage should also preserve Momentum.

The exact distinction between blocking, dodging, partial mitigation, and complete avoidance remains unresolved.

---

## Momentum Loss

Taking meaningful damage lowers Momentum.

```text
Take meaningful damage
→ Momentum decreases
```

Taking damage does not automatically reset Momentum to zero.

The exact amount lost and how damage severity affects the loss remain undecided.

---

## Critical-Hit Effect

Momentum raises critical-hit frequency.

It does not guarantee a critical strike.

Higher Momentum should create periods where critical hits can occur more often, allowing the player to feel that sustained control is producing increasingly dangerous offense.

The exact relationship between Momentum and critical chance remains undecided.

Possible future implementations include:

* continuous critical-chance growth
* threshold-based critical bonuses
* Momentum bands with increasing benefits
* character-specific conversion rates

No exact formula is currently approved.

---

## Intuition Interaction

Intuition should influence Momentum in a limited way.

It should not drastically increase raw Momentum generation.

Possible future interactions include:

* slightly improving the critical benefit gained from existing Momentum
* slightly reducing Momentum loss
* improving Momentum preservation under pressure
* reaching higher critical-efficiency thresholds sooner

The final Intuition interaction remains unresolved.

---

## Enemy Access

Regular enemies are not currently expected to use Momentum.

Possible future users include:

* bosses
* major named enemies
* elite rivals
* important story encounters

Enemy access remains undecided and should be assigned explicitly rather than granted automatically.

---

## Relationship to Other Resources

### Mana

Mana is a persistent spendable resource used for special actions.

```text
Mana
→ stored as current and maximum values
→ spent to perform moves
→ persists beyond a single encounter
```

### Super

Super is a separate encounter meter.

It builds through:

* dealing damage
* receiving damage

It does not build through:

* healing
* using items

Super is spent to perform a super or signature move.

### Momentum

Momentum is not spent.

```text
Momentum
→ temporary encounter state
→ rewards sustained control
→ increases critical frequency
→ falls when meaningful damage is taken
```

The three systems serve different purposes:

```text
Mana
→ action economy

Super
→ combat participation and major payoff

Momentum
→ sustained execution and offensive control
```

---

## Current Locked Rules

* Momentum is shared by every playable character.
* Momentum begins at zero each encounter.
* Momentum resets when the encounter ends.
* Successful damaging moves grant Momentum.
* Momentum gain is associated with the move, not each individual strike.
* Missing grants no Momentum.
* Missing does not reduce or reset Momentum.
* Defending preserves Momentum.
* Avoiding or sufficiently reducing damage preserves Momentum.
* Taking meaningful damage lowers Momentum.
* Taking damage does not necessarily reset Momentum.
* Momentum raises critical-hit frequency.
* Momentum does not guarantee critical hits.
* Intuition has a limited interaction with Momentum.
* Momentum is not a `ResourceType`.
* Momentum is not part of v0.3.

---

## Unresolved Design Questions

The following must be settled before implementation:

* maximum Momentum
* gain per successful move
* loss from taking damage
* whether loss scales with damage severity
* what qualifies as sufficiently reduced damage
* whether blocking and dodging preserve Momentum differently
* exact critical-chance formula
* whether Momentum uses continuous values or thresholds
* whether Momentum naturally decays
* whether critical hits grant additional Momentum
* whether certain moves grant more or less Momentum
* whether certain moves require a Momentum threshold
* how multi-hit moves define custom Momentum behavior
* exact Intuition interaction
* boss and major-enemy access
* HUD and visual presentation

---

## v0.3 Boundary

Momentum should not be implemented during v0.3.

The current combat architecture may preserve a brief deferred-design note, but it must not:

* add active Momentum state
* add Momentum spending
* add Momentum formulas
* add Momentum to `ResourceType`
* alter current move costs
* alter critical calculations
* create resolver dependencies
* create character-specific Momentum assumptions

Momentum should be implemented only after the core combat resolver, Battle integration, character kits, and critical-hit behavior are stable enough to support it deliberately.

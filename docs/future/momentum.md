# Future Combat Mechanic: Momentum

## Status

**M7 design in progress; implementation deferred.** The November 17, 2026 design revision supersedes the earlier individual-combatant Momentum proposal. Remaining numerical, interaction, and interface rules must be resolved before implementation begins.

## Core Identity

Momentum represents contested battlefield control, pressure, rhythm, and dominance during one encounter. It is one shared encounter-wide state contested by the Drifter faction and the enemy faction, not an individual flow meter.

The working scale is 0-10, with 5 neutral:

```text
Enemy control                         Drifter control
0 ----------- 1 -------- ... -------- 5 -------- ... -------- 10
                                      neutral
```

The conceptual direction is that movement toward 0 represents increasing enemy control and movement toward 10 represents increasing Drifter control. Final display orientation and numeric presentation remain subject to approval.

Momentum is not a spendable resource like Mana or Super. Control should be difficult to establish against meaningful resistance, easier to lose under substantial pressure, and resistant to trivial chip damage. The system intentionally permits runaway offensive pressure and does not guarantee a comeback.

## Collective, Action-Based Control

The value reflects the encounter's collective performance. Any participant's meaningful action can contribute to the shared state according to the faction that acts and the approved event rules. One Drifter's actions can establish control; substantial pressure against teammates can undermine it.

Momentum is evaluated around combat actions, not only at round boundaries. Outnumbering naturally creates more action opportunities to influence control. Do not normalize by participant count or apply a passive numerical-superiority shift. The number of combatants alone does not move Momentum; resolved performance does.

Successful offensive actions should help establish control for the acting faction. Meaningful incoming damage should shift control toward the attacker. Insignificant chip damage should not automatically erase established control. Exact action eligibility, impact weights, loss thresholds, and amounts are not yet defined.

Action-based does not mean that every action contributes equally. The rules must prevent accidental repeated contribution from animation/log events, split damage components, multi-hit moves, or multiple targets unless the approved contract explicitly intends it.

## Defense And Recovery

Successful defense, avoidance, and sufficient mitigation should help preserve control. Defensive actions do not necessarily create positive Momentum; denying an opponent an opportunity to gain control can itself be valuable.

Healing presents a tactical opportunity cost: recover to survive, or take an action that contests control. Healing should not automatically count as offensive Momentum generation. Whether healing changes the shared bar in another way remains unresolved.

The distinctions among Defend, Brace, blocking, dodging, complete avoidance, partial mitigation, status effects, backlash, damage-over-time, and environmental hazards require explicit rules before implementation.

## Critical-Hit Interaction

Both factions can receive increasing, faction-wide critical-hit advantages as the shared value moves toward their side's control. At neutral, neither faction receives a Momentum-derived critical advantage. Existing critical modifiers from stats, equipment, or other approved systems continue independently.

```text
Enemy control -> enemy faction critical advantage increases
Neutral       -> no Momentum-derived critical advantage
Drifter control -> Drifter party critical advantage increases
```

This replaces the former assumption that regular enemies generally lack Momentum access. The enemy faction participates in the shared contest; it does not receive a separate independent bar. Runaway critical pressure is an intentional possible consequence when one side establishes dominance. There is no automatic rubber-banding.

The exact conversion, critical cap, rounding, whether critical hits feed back into Momentum, and whether a move uses the pre-action or post-action value are unresolved. No arithmetic should be inferred from this conceptual direction.

## Relationship To Character And Enemy Design

The shared mechanic is available to the encounter's factions, not assigned as separate pools to individual Drifters or enemies. Whether Intuition, a particular authored move, boss properties, status effects, or environmental conditions alter Momentum is unresolved. Do not assume that character identity or enemy rank changes the rules without an approved contract.

## Relationship To Other Resources

### Mana

Mana remains a persistent spendable resource used to perform special actions. Momentum does not change Mana costs or persistence.

### Super

Super remains governed by its existing lifetime, ownership, persistence, and spend rules. Momentum is independent and must not reset or mutate Super as a side effect.

### Momentum

Momentum is a temporary encounter value. It is not spent, is not a `ResourceType`, and is not permanent character progression.

## Architecture And Persistence Boundary

The intended ownership is one authoritative value in encounter combat state. Python resolves changes and critical effects. `Battle` coordinates action/lifecycle ordering. Presenters expose that state; terminal and browser clients display it without calculating gameplay outcomes.

Momentum should:

- begin at neutral when an encounter starts
- be shared across that encounter's participants and contested by both factions
- reset when the encounter ends
- remain out of permanent `PlayerState` progression and ordinary saved character state
- remain separate from Mana and Super
- not be represented as a move resource type

No save-schema migration is expected solely for this temporary state. Re-entering a route encounter creates a new neutral state, not a continuation. Revalidate exact class/API integration points against the repository when M7 begins; this document defines behavior, not a frozen implementation surface.

## Design Direction Established

1. Momentum is shared encounter-wide, not tracked per combatant.
2. Drifters and enemies contest the same state.
3. The working scale is 0-10 with 5 neutral; final visual orientation remains open.
4. The value represents collective battlefield control.
5. Both factions gain faction-wide critical advantages toward their respective control end.
6. Changes are action-based rather than round-based.
7. Numerical superiority creates more opportunities naturally; no headcount normalization is applied.
8. Control should be difficult to establish against meaningful opposition and easier to lose under substantial pressure.
9. Minor chip damage should not automatically erase established control.
10. Defensive performance should help preserve control, but defense need not generate it.
11. Runaway critical pressure is possible by design.
12. No automatic comeback or rubber-band mechanic is added.
13. Momentum is temporary, encounter-owned, non-spendable, and independent of Mana/Super.

## Unresolved Design Questions

These contracts must be settled before implementation:

- Whether gains primarily measure successful performance, battlefield control, or a defined combination.
- Exact gain amounts, allowed fractions/quantization, bounds, and eligible actions.
- What qualifies as meaningful incoming damage, severity-based loss, and gain/loss asymmetry.
- How misses, zero-damage/status actions, multi-hit moves, split components, multiple targets, damage-over-time, backlash, and hazards affect the bar.
- Whether defense, Brace, blocking, dodging, and mitigation only preserve control or can also shift it.
- Whether healing affects Momentum beyond consuming an action opportunity.
- The critical conversion at each control level, rounding, cap interaction, and any critical-to-Momentum feedback.
- Whether critical resolution uses the state before or after the current action's Momentum change.
- Whether Intuition, authored moves, bosses, or environmental properties can modify the shared mechanic.
- Final HUD orientation, threshold feedback, and terminal/browser presentation.

## Implementation Boundary

M7 remains in design review. Do not implement active Momentum state, formulas, critical changes, UI, save fields, or special enemy/move behavior from this document alone. The next step is to resolve the open contracts and update the M7 Gate 0 plan. The revised specification must remain a single shared contested system rather than layering the earlier individual model underneath it.

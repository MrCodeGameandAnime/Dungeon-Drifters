# Future Combat Mechanic: Momentum

## Status

**M7 design in progress; implementation deferred.** The November 17, 2026 design revisions supersede the earlier individual-combatant Momentum proposal. The shared scale and damage-shift contract are established for planning. The illustrative critical progression, its cap interaction, and arithmetic integration of the proposed dominance bonuses remain Gate 0 work before implementation.

## Core Identity

Momentum represents contested battlefield control, pressure, rhythm, and dominance during one encounter. It is one shared encounter-wide state contested by the Drifter faction and the enemy faction, not an individual flow meter.

Momentum is an integer from 0 through 10 and begins at 5 (neutral):

```text
Enemy control                         Drifter control
0 ----------- 1 -------- ... -------- 5 -------- ... -------- 10
                                      neutral
```

Positions 0-4 favor enemies; positions 6-10 favor Drifters. Relative control is Enemy +5 through Enemy +1, Neutral, and Drifter +1 through Drifter +5. The bar clamps at 0 and 10 and crosses neutral freely, without a barrier or conversion penalty. The semantic direction is settled; final HUD arrangement and styling remain a presentation task.

| Bar position | Relative control |
|---:|---|
| 0 | Enemy +5 |
| 1 | Enemy +4 |
| 2 | Enemy +3 |
| 3 | Enemy +2 |
| 4 | Enemy +1 |
| 5 | Neutral (0) |
| 6 | Drifter +1 |
| 7 | Drifter +2 |
| 8 | Drifter +3 |
| 9 | Drifter +4 |
| 10 | Drifter +5 |

Momentum is not a spendable resource like Mana or Super. The approved damage rules give every successful damaging attack a standard or enhanced shift, so repeated small hits may accumulate. The 10% remaining-HP threshold and 1/2-tick values are approved; there are no additional damage tiers. The system intentionally permits runaway offensive pressure and does not guarantee a comeback. There is no passive Momentum decay or artificial recovery.

## Collective, Action-Based Control

The value reflects the encounter's collective performance. Damaging actions shift the single shared state toward the faction that caused the damage under the same rules for Drifters and enemies. Other non-damaging actions have no assigned Momentum effect unless explicitly listed below or resolved at Gate 0.

Momentum is evaluated around combat actions, not only at round boundaries. Outnumbering naturally creates more action opportunities to influence control. Do not normalize by participant count or apply a passive numerical-superiority shift. The number of combatants alone does not move Momentum; resolved performance does.

The universal damage rules are:

| Damage outcome | Base contribution before target defense |
|---|---:|
| Actual HP damage below 10% of pre-damage remaining HP | 1 tick toward attacker |
| Actual HP damage at least 10% of pre-damage remaining HP | 2 ticks toward attacker |
| Miss or zero actual HP damage | 0 ticks |
| Healing | 0 ticks |
| Rejected action | 0 ticks |

Use actual HP removed, not theoretical damage or overkill. The inclusive threshold can be compared without floating-point division:

```text
actual_hp_damage * 10 >= hp_before_damage
```

The proposed 1-tick/2-tick distinction is settled. Defense reduces the contribution by one tick, with a floor of zero; it does not shift Momentum toward the defending faction:

| Damage outcome | Without defense | With defense |
|---|---:|---:|
| Standard | 1 tick | 0 ticks |
| Enhanced | 2 ticks | 1 tick |

For split physical/magical damage, combine actual HP damage from the resolved components, classify once against the target's pre-damage remaining HP, and apply one contribution for the attack. Do not shift once per component. Multi-hit, multi-target, and simultaneous outcomes remain unresolved. Critical hits do not receive an independent Momentum multiplier; their actual damage uses the universal classification.

Action-based does not mean that presentation events, components, or repeated logs create additional contributions. Resolve Momentum at authoritative combat boundaries, not from client rendering.

## Defense And Recovery

Defense is an approved reduction to the damage contribution: subtract one tick and floor at zero, without shifting toward the defender. The M7 entry audit must map this rule to the existing defensive states without changing their combat behavior. Healing explicitly contributes zero Momentum.

Other non-damaging actions, status actions outside the combined start-of-turn damage phase, recoil/backlash, and environmental hazards require explicit rules before implementation. Do not award repeated contributions from ticks or log events by accident.

## Critical-Hit Interaction

Both factions can receive increasing, faction-wide critical-hit advantages as the shared value moves toward their side's control. At neutral, neither faction receives a Momentum-derived critical advantage. Existing critical modifiers from stats, equipment, or other approved systems continue independently.

```text
Enemy control -> enemy faction critical advantage increases
Neutral       -> no Momentum-derived critical advantage
Drifter control -> Drifter party critical advantage increases
```

The previously proposed five-level critical conversion is listed with the damage and mitigation thresholds below. Critical bonuses are additive percentage points, not multipliers to existing critical chance. The +2 percentage-point-per-advantage-level progression remains illustrative and requires final approval, including its interaction with existing critical caps. Existing non-Momentum modifiers remain governed by the existing combat contract. This replaces the former assumption that regular enemies generally lack Momentum access. The enemy faction participates in the shared contest; it does not receive a separate independent bar. Runaway critical pressure is an intentional possible consequence when one side establishes dominance. There is no automatic rubber-banding.

Combat calculations read the applicable critical, outgoing-damage, and incoming-mitigation advantages from the current shared Momentum at the relevant resolution boundary. For a damage-causing action, apply its Momentum shift only after its damage resolves, so that action cannot benefit retroactively from the state it creates. Critical hits have no separate Momentum multiplier; they affect the contribution only through actual HP damage. Start-of-turn damage-over-time resolves before the affected combatant's action, so its Momentum shift can immediately change applicable bonuses for subsequent calculations if the combatant survives and can act.

## Proposed Damage And Mitigation Advantages

The current design direction adds outgoing damage and incoming damage mitigation at +3 and +5 faction advantage. The same thresholds and values apply symmetrically whether Drifters or enemies control Momentum. The threshold tiers are not cumulative: +3 and +4 provide 5% outgoing damage and 5% incoming mitigation; +5 provides 10% of each, not 15%.

| Faction advantage | Illustrative critical bonus | Current proposed outgoing damage | Current proposed incoming mitigation |
|---|---:|---:|---:|
| Neutral | +0 percentage points | 0% | 0% |
| +1 | +2 percentage points | 0% | 0% |
| +2 | +4 percentage points | 0% | 0% |
| +3 | +6 percentage points | +5% | +5% |
| +4 | +8 percentage points | +5% | +5% |
| +5 | +10 percentage points | +10% | +10% |

These are proposed planning thresholds; Gate 0 remains open for arithmetic and combat-pipeline integration. Integrate them into the existing authoritative combat damage calculation; do not create a separate Momentum damage pipeline. Resolve percentage rounding, ordering against existing outgoing modifiers and incoming defenses, and the interaction between percentage mitigation and the separate one-tick reduction to Momentum contribution. Do not conflate these two defensive effects.

The final actual HP damage after the approved damage/mitigation ordering and rounding remains the input to the standard/enhanced 10% classification. Therefore, the proposed outgoing damage bonus may change whether damage reaches the enhanced threshold, while incoming mitigation may lower damage and the resulting Momentum contribution. The illustrative 9 damage plus 10% example does not determine rounding: an intermediate value such as 9.9 only qualifies for enhanced contribution if authoritative final HP damage is 10. Likewise, an incoming 10 reduced by 10% reaches 9 only if the approved arithmetic resolves that way. Do not implement either example's rounding by assumption.

Bonuses are evaluated from the current authoritative Momentum at the relevant action boundary. An attack does not benefit retroactively from Momentum generated by its own damage; the new state applies to subsequent actions. Start-of-turn damage may change the state before the affected combatant acts. Crossing below a threshold immediately removes or reduces its associated bonus. At +1/+2, critical advantage may increase under the proposed critical progression, but there is no damage or mitigation bonus until +3.

The intended tactical stages are establishing advantage (+1/+2), dominance (+3/+4), and maximum dominance (+5). Preventing the opposing faction from reaching +3 is a primary defensive objective. Maximum control is intentionally powerful and may snowball; do not add a hidden comeback system to counter it.

## Combined Start-Of-Turn Damage-Over-Time

All applicable damage-over-time effects resolving at the beginning of the same combatant's turn are combined into one Momentum calculation for that phase. Their ordinary damage and duration behavior remains separate and unchanged.

1. Resolve applicable start-of-turn effects before the combatant's action.
2. Sum the actual HP damage those effects cause during this phase.
3. Compare the sum with the affected combatant's HP immediately before the phase.
4. Classify the combined damage under the universal 10% standard/enhanced rule.
5. Apply one contribution using the universal damage and defense rules.
6. Update shared Momentum before determining whether the combatant can act.
7. If the combatant survives and can act, use the updated Momentum for its applicable critical, outgoing-damage, and incoming-mitigation bonuses.

Do not accumulate damage across different turns or give each status effect its own shift. The faction responsible for the damage receives the contribution. If the effects in one phase have mixed faction sources, attribution remains unresolved if the current status system permits that case.

Burn and Poison remain independent status effects for their normal damage and duration. Do not add status-specific Momentum values, multipliers, or new status behavior.

Example: a combatant has 100 HP before the phase; Burn deals 5 actual damage and Poison deals 5 actual damage. The combined 10 damage meets the 10% threshold and produces one enhanced 2-tick contribution toward the responsible faction, or 1 tick if the target is under an applicable defense state. Without defense, movement from Enemy +1 (position 4) crosses neutral and ends at Drifter +1 (position 6); with defense, it moves one tick to neutral. All critical, damage, and mitigation advantages update from the resulting shared state. The enemy's later action, if it survives, uses the updated state; its own attack then changes Momentum only for subsequent calculations.

## Minimum Deterministic Test Cases

1. An undefended enhanced attack moves Enemy +1 (position 4) two ticks to Drifter +1 (position 6).
2. An enemy standard attack moves Drifter +1 (position 6) one tick to neutral (position 5).
3. Burn 5 plus Poison 5 against 100 HP before the start-of-turn phase meets the enhanced threshold.
4. Those two effects cause one combined Momentum contribution, not one per effect.
5. Damage from separate turns is not accumulated into a later DoT calculation.
6. Start-of-turn status damage changes the applicable Momentum bonuses available to the affected combatant's upcoming action.
7. An action uses pre-action Momentum for its own critical, outgoing-damage, and incoming-mitigation calculations; its damage shifts Momentum only for later actions.
8. Neutral grants neither faction a Momentum-derived critical, damage, or mitigation bonus.
9. Momentum crosses neutral without a penalty or stopping condition.
10. The shared value remains an integer bounded from 0 through 10.
11. The same damage and defense rules apply when Drifter/enemy faction ownership is reversed.
12. At +2 there is no proposed damage/mitigation bonus; at +3 and +4 the proposed values are 5%/5%; at +5 they are 10%/10%, not cumulative 15%.
13. The proposed bonuses apply symmetrically and change immediately when Momentum crosses +3 or +5 in either direction, including the +5 to +4 reduction.
14. After Gate 0 fixes rounding and operation order, final actual HP damage determines whether the universal 10% enhanced threshold is met.

## Relationship To Character And Enemy Design

The shared mechanic is available to the encounter's factions, not assigned as separate pools to individual Drifters or enemies. The combined start-of-turn damage rule applies to damage-over-time status effects. Whether Intuition, a particular authored move, boss properties, other status actions, or environmental conditions add or alter Momentum is unresolved. Do not assume that character identity or enemy rank changes the rules without an approved contract.

## Relationship To Other Resources

### Mana

Mana remains a persistent spendable resource used to perform special actions. Momentum does not change Mana costs or persistence.

### Super

Super remains governed by its existing lifetime, ownership, persistence, and spend rules. Momentum is independent and must not reset or mutate Super as a side effect.

### Momentum

Momentum is a temporary encounter value. It is not spent, is not a `ResourceType`, and is not permanent character progression.

## Architecture And Persistence Boundary

The intended ownership is one authoritative value in encounter combat state. Python resolves changes and critical, damage, and mitigation effects. `Battle` coordinates action/lifecycle ordering. Presenters expose that state; terminal and browser clients display it without calculating gameplay outcomes.

Momentum must:

- be an integer from 0 through 10, begin at neutral position 5, and clamp at either endpoint
- cross neutral freely and never use fractional contributions
- be shared across that encounter's participants and contested by both factions
- reset when the encounter ends
- remain out of permanent `PlayerState` progression and ordinary saved character state
- remain separate from Mana and Super
- not be represented as a move resource type

No save-schema migration is expected solely for this temporary state. Re-entering a route encounter creates a new neutral state, not a continuation. Revalidate exact class/API integration points against the repository when M7 begins, including the actual status-effect resolution lifecycle; do not assume status damage already resolves at the required pre-action boundary. This document defines behavior, not a frozen implementation surface.

## Approved Rules And Remaining Proposals

1. Momentum is shared encounter-wide, not tracked per combatant.
2. Drifters and enemies contest the same state and use the same authoritative rules.
3. Momentum is an integer 0-10, starts at 5, clamps at endpoints, and crosses neutral freely.
4. The value represents collective battlefield control.
5. Standard damage contributes 1 tick; enhanced damage contributes 2 ticks at the inclusive threshold of 10% of pre-damage remaining HP, using actual HP removed. No additional damage tiers or fractional Momentum are used.
6. A target under applicable defense reduces the contribution by one tick, floored at zero; this never shifts the bar toward the defender.
7. Split physical/magical damage is aggregated into one attack result and one contribution. Multi-hit, multi-target, and simultaneous outcome rules remain open.
8. Misses, zero actual HP damage, healing, and rejected actions contribute zero Momentum.
9. Start-of-turn damage-over-time for one combatant is combined into one contribution before its action; effects are not accumulated across turns.
10. An action uses the pre-action Momentum state for applicable bonuses; its own damage contribution affects subsequent actions. Start-of-turn status damage updates Momentum before the upcoming action's bonuses are calculated.
11. Numerical superiority creates more action opportunities naturally; no headcount normalization or passive headcount shift is applied.
12. Both factions receive faction-wide critical advantages toward their respective control end; the +2 percentage-points-per-tick table is illustrative and awaits final approval.
13. Both factions receive symmetric damage and mitigation advantages at the proposed +3/+5 thresholds; +3/+4 are 5% and +5 is 10%, not cumulative. Their arithmetic integration remains open.
14. Runaway control is possible by design; no automatic comeback, passive decay, or rubber-band mechanic is added.
15. Momentum is temporary, encounter-owned, non-spendable, and independent of Mana/Super.

## Unresolved Design Questions

These remaining contracts must be settled before implementation:

- Momentum rules for multi-hit, multi-target, and simultaneous target outcomes.
- Attribution when a combined start-of-turn damage phase contains effects from multiple factions, if supported by current authored status content.
- Which existing defensive states qualify for the approved one-tick reduction; preserve their existing mitigation/avoidance behavior.
- Whether non-damaging actions beyond healing, Intuition, authored moves, bosses, other status actions, or environmental properties add or alter Momentum.
- Final critical bonus progression; +2 percentage points per faction-advantage tick remains illustrative. Existing caps and non-Momentum modifiers must remain unchanged.
- Final arithmetic integration for the proposed +3/+5 damage and mitigation thresholds: percentage rounding; ordering with existing damage and defense modifiers; interaction with the separate one-tick Momentum defense reduction; final actual damage used for the 10% classification; and immediate tier loss when control drops below a threshold.
- Final terminal/browser presentation and feedback for integer bar position, relative faction control, and standard/enhanced shifts.
- M7 entry audit of current action, status, critical, defense, presenter, and runtime integration boundaries.

## Implementation Boundary

M7 remains in design review. Do not implement active Momentum state, formulas, critical changes, UI, save fields, or special enemy/move behavior from this document alone. The approved scale, damage shifts, defense reduction, combined start-of-turn damage rule, and dynamic action timing are fixed planning inputs. The +3/+5 damage and mitigation thresholds are the current proposed dominance direction, not a closed arithmetic contract. Gate 0 remains open for the listed edge cases, defense-state mapping, critical progression and cap interaction, percentage rounding and modifier order, any special modifiers, presentation, and repository seam audit. The revised specification must remain a single shared contested system rather than layering the earlier individual model underneath it.

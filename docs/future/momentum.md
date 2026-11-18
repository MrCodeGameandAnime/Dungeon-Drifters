# Future Combat Mechanic: Momentum

## Status

**M7 Gate 0 is closed; implementation status is tracked in the current milestone plan.** The November 17, 2026 revisions supersede the earlier individual-combatant Momentum proposal. The shared scale, damage-shift contract, critical progression, defense rule, attribution, DoT timing/suppression safeguard, damage arithmetic, and terminal/browser presentation are approved.

## Core Identity

Momentum represents contested battlefield control, pressure, rhythm, and dominance during one encounter. It is one shared encounter-wide state contested by the Drifter faction and the enemy faction, not an individual flow meter.

Momentum is an integer from 0 through 10 and begins at 5 (neutral):

```text
Enemy control                         Drifter control
0 ----------- 1 -------- ... -------- 5 -------- ... -------- 10
                                      neutral
```

Positions 0-4 favor enemies; positions 6-10 favor Drifters. Relative control is Enemy +5 through Enemy +1, Neutral, and Drifter +1 through Drifter +5. The bar clamps at 0 and 10 and crosses neutral freely, without a barrier or conversion penalty. The approved shared meter uses visible +3 landmarks at positions 2 and 8 and +5 endpoints at positions 0 and 10, plus plain-text active-bonus readouts in both clients; final visual styling remains an implementation detail.

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

The value reflects the encounter's collective performance. Damage shifts the single shared state only when attributable to a faction opposing the damaged combatant, under the same rules for Drifters and enemies. Same-faction damage, self-backlash, and unattributed environmental damage do not shift Momentum. Non-damaging actions do not affect Momentum; healing explicitly contributes zero.

Momentum is evaluated around combat actions, not only at round boundaries. Outnumbering naturally creates more action opportunities to influence control. Do not normalize by participant count or apply a passive numerical-superiority shift. The number of combatants alone does not move Momentum; resolved performance does.

The universal damage rules are:

| Damage outcome | Base contribution before active Defend/Brace contribution reduction |
|---|---:|
| Actual HP damage below 10% of pre-damage remaining HP | 1 tick toward opposing-faction source |
| Actual HP damage at least 10% of pre-damage remaining HP | 2 ticks toward opposing-faction source |
| Miss or zero actual HP damage | 0 ticks |
| Healing | 0 ticks |
| Rejected action | 0 ticks |

Use actual HP removed, not theoretical damage or overkill. The inclusive threshold can be compared without floating-point division:

```text
actual_hp_damage * 10 >= hp_before_damage
```

The 1-tick/2-tick distinction is settled. An applicable active Defend or Brace state reduces a resolved attack's contribution by one tick, with a floor of zero; it does not shift Momentum toward the defending faction. Apply the reduction at most once per attack, even if both states apply. Passive stat, equipment, and passive-skill mitigation do not qualify. Momentum's percentage mitigation also does not qualify for an additional reduction:

| Damage outcome | Before active-defense contribution reduction | With applicable active Defend/Brace |
|---|---:|---:|
| Standard | 1 tick | 0 ticks |
| Enhanced | 2 ticks | 1 tick |

For split physical/magical damage, combine actual HP damage from the resolved components, classify once against the target's pre-damage remaining HP, and apply one contribution for the attack. Do not shift once per component. The current combat model resolves one target and one hit per move action, with actions resolved sequentially; M7 does not add multi-hit, multi-target, or simultaneous attacks. Revisit these rules only if those mechanics are introduced later. Critical hits do not receive an independent Momentum multiplier; their actual damage uses the universal classification.

Action-based does not mean that presentation events, components, or repeated logs create additional contributions. Resolve Momentum at authoritative combat boundaries, not from client rendering.

## Defense And Recovery

Only an applicable active Defend or Brace state reduces an attack's Momentum contribution. Apply the reduction once at most for the resolved attack, including split-component attacks. This rule does not change damage mitigation itself. Healing explicitly contributes zero Momentum.

No special Momentum modifiers apply to Intuition, individual moves, bosses, or non-damaging effects. Healing contributes zero. Damage contributes only when attributable to an opposing faction. Self-backlash and unattributed environmental damage do not shift Momentum. Do not award repeated contributions from status ticks or presentation log entries.

## Critical-Hit Interaction

Both factions can receive increasing, faction-wide critical-hit advantages as the shared value moves toward their side's control. At neutral, neither faction receives a Momentum-derived critical advantage. Existing critical modifiers from stats, equipment, or other approved systems continue independently.

```text
Enemy control -> enemy faction critical advantage increases
Neutral       -> no Momentum-derived critical advantage
Drifter control -> Drifter party critical advantage increases
```

The five-level critical conversion is approved. Critical bonuses are additive percentage points, not multipliers to existing critical chance: +2 percentage points per faction advantage level, up to +10 at +5. Apply the bonus symmetrically to both factions and retain the existing 35% critical cap and all non-Momentum modifiers. This replaces the former assumption that regular enemies generally lack Momentum access. The enemy faction participates in the shared contest; it does not receive a separate independent bar. Runaway critical pressure is an intentional possible consequence when one side establishes dominance. There is no automatic rubber-banding.

Combat calculations read the applicable critical, outgoing-damage, and incoming-mitigation advantages from the current shared Momentum at the relevant resolution boundary. For a damage-causing action, apply its Momentum shift only after its damage resolves, so that action cannot benefit retroactively from the state it creates. Critical hits have no separate Momentum multiplier; they affect the contribution only through actual HP damage. Start-of-turn damage-over-time resolves before the affected combatant's action, so its Momentum shift can immediately change applicable bonuses for subsequent calculations if the combatant survives and can act.

## Approved Damage And Mitigation Advantages

The approved design adds outgoing damage and incoming damage mitigation at +3 and +5 faction advantage. The same thresholds and values apply symmetrically whether Drifters or enemies control Momentum. The threshold tiers are not cumulative: +3 and +4 provide 5% outgoing damage and 5% incoming mitigation; +5 provides 10% of each, not 15%.

| Faction advantage | Critical bonus | Outgoing damage | Incoming mitigation |
|---|---:|---:|---:|
| Neutral | +0 percentage points | 0% | 0% |
| +1 | +2 percentage points | 0% | 0% |
| +2 | +4 percentage points | 0% | 0% |
| +3 | +6 percentage points | +5% | +5% |
| +4 | +8 percentage points | +5% | +5% |
| +5 | +10 percentage points | +10% | +10% |

The +3/+5 values and arithmetic ordering are approved. Preserve existing integer-floor calculations and modifier order: apply the Momentum outgoing multiplier after existing attacker-side modifiers and before defenses; apply Momentum mitigation after existing defenses and before the critical multiplier. For split-component attacks, apply both at the corresponding existing per-component stages, sum actual damage, and apply the critical multiplier once. Integrate into the existing authoritative damage calculation; do not create a separate Momentum damage pipeline. The one-tick active-defense contribution reduction is a distinct rule and does not arise from passive or Momentum percentage mitigation.

Final actual HP removed after the approved modifier ordering, integer floors, defenses, Momentum mitigation, and critical multiplier determines the standard/enhanced contribution. Momentum percentages affect resolved move attacks through the existing attack pipeline. DoT tick amounts remain at their authored values and contribute using their actual HP damage; they are not routed through attack-only critical or percentage-modifier steps.

Bonuses are evaluated from the current authoritative Momentum at the relevant action boundary. An attack does not benefit retroactively from Momentum generated by its own damage; the new state applies to subsequent actions. Start-of-turn damage may change the state before the affected combatant acts. Crossing below a threshold immediately removes or reduces its associated bonus. At +1/+2, the approved critical advantage increases by 2 percentage points per level, but there is no damage or mitigation bonus until +3.

The intended tactical stages are establishing advantage (+1/+2), dominance (+3/+4), and maximum dominance (+5). Preventing the opposing faction from reaching +3 is a primary defensive objective. Maximum control is intentionally powerful and may snowball; do not add a hidden comeback system to counter it.

## Combined Start-Of-Turn Damage-Over-Time

All applicable damage-over-time effects resolving at the beginning of the same combatant's turn are combined into one Momentum calculation for that phase. Each retains its authored tick damage and duration. The start-of-turn timing is intentional: the phase runs before checking whether stun, frozen, or another action-opportunity suppression prevents the combatant from acting.

1. Resolve all applicable status ticks, preserving each status's ordinary damage and tick count. Advancing DoT durations must not decrement, expire, or otherwise consume the action-suppression effect due to be checked for this turn.
2. Sum actual HP damage only from statuses whose source belongs to the faction opposing the affected combatant. Ignore same-faction and unattributed status damage for Momentum, without suppressing their ordinary status damage itself.
3. Compare the eligible sum with the affected combatant's HP immediately before the entire phase.
4. Classify the eligible sum under the universal 10% standard/enhanced rule.
5. Apply one contribution toward the eligible source faction. No active Defend/Brace reduction applies because the existing DoT damage path does not use those defenses and the one-tick reduction is defined per resolved attack.
6. Update shared Momentum before the action-opportunity suppression check. The DoT phase and duration advancement must not consume, clear, replace, or expire suppression state before that check.
7. If the combatant survives, process stun/frozen suppression normally. If DoT defeats the combatant, no action occurs and ordinary defeated-combatant cleanup applies.
8. If the combatant survives and can act, its action uses the updated Momentum for applicable bonuses.

Do not accumulate damage across different turns or give each status effect its own shift. Mixed-source phases count only the eligible opposing-faction actual damage in their single contribution; same-faction and unattributed damage do not suppress that eligible contribution. If the eligible sum is zero, the phase causes no shift.

Burn, Poison, and Frostbite remain independent status effects with their authored tick values. Momentum does not add status-specific multipliers or change their damage values. The explicitly approved scheduling change means their tick phase advances even when action suppression subsequently skips the turn; suppression itself must still apply normally.

Example: a combatant has 100 HP before the phase. Opposing-faction Burn deals 5 actual damage and opposing-faction Poison deals 5; same-faction Burn deals another 4. The eligible total is 10, so one enhanced 2-tick contribution applies; the same-faction 4 damage still occurs but does not count toward Momentum. The new state applies before action suppression. If the combatant survives but is stunned, the stun still consumes the action opportunity; if the DoT phase defeats it, no action occurs.

## Minimum Deterministic Test Cases

1. An undefended enhanced attack moves Enemy +1 (position 4) two ticks to Drifter +1 (position 6).
2. An enemy standard attack moves Drifter +1 (position 6) one tick to neutral (position 5).
3. Burn 5 plus Poison 5 against 100 HP before the start-of-turn phase meets the enhanced threshold.
4. Those two effects cause one combined Momentum contribution, not one per effect.
5. Damage from separate turns is not accumulated into a later DoT calculation.
6. Start-of-turn status damage changes Momentum before suppression and before the affected combatant's upcoming action; DoT does not erase suppression.
7. An action uses pre-action Momentum for its own critical, outgoing-damage, and incoming-mitigation calculations; its damage shifts Momentum only for later actions.
8. Neutral grants neither faction a Momentum-derived critical, damage, or mitigation bonus.
9. Momentum crosses neutral without a penalty or stopping condition.
10. The shared value remains an integer bounded from 0 through 10.
11. The same damage and defense rules apply when Drifter/enemy faction ownership is reversed.
12. At +2 there is no damage/mitigation bonus; at +3 and +4 the approved values are 5%/5%; at +5 they are 10%/10%, not cumulative 15%.
13. The approved bonuses apply symmetrically and change immediately when Momentum crosses +3 or +5 in either direction, including the +5 to +4 reduction.
14. Final actual HP damage after approved integer-floor ordering determines whether the universal 10% enhanced threshold is met.

## Relationship To Character And Enemy Design

The shared mechanic is available to the encounter's factions, not assigned as separate pools to individual Drifters or enemies. The combined start-of-turn damage rule applies to damage-over-time status effects. Intuition, individual move identity, boss identity, and non-damaging effects do not add special Momentum modifiers. Healing contributes zero. Only opposing-faction-attributable damage contributes; self-backlash and unattributed environmental damage do not.

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

No save-schema migration is expected solely for this temporary state. Re-entering a route encounter creates a new neutral state, not a continuation. The repository audit found that DoT currently advances after accepted actions; M7 intentionally moves this phase before action suppression and must preserve the pending suppression. This document defines behavior, not a frozen implementation surface.

## Approved Rules

1. Momentum is shared encounter-wide, not tracked per combatant.
2. Drifters and enemies contest the same state and use the same authoritative rules.
3. Momentum is an integer 0-10, starts at 5, clamps at endpoints, and crosses neutral freely.
4. The value represents collective battlefield control.
5. Standard damage contributes 1 tick; enhanced damage contributes 2 ticks at the inclusive threshold of 10% of pre-damage remaining HP, using actual HP removed. No additional damage tiers or fractional Momentum are used.
6. An applicable active Defend or Brace state reduces a resolved attack's contribution by one tick, floored at zero and at most once per attack. Passive and Momentum percentage mitigation do not qualify.
7. Split physical/magical damage is aggregated into one attack result and one contribution. Current moves use one hit and one target; future multi-hit, multi-target, and simultaneous mechanics require a reviewed rule before introduction.
8. Misses, zero actual HP damage, healing, and rejected actions contribute zero Momentum.
9. Start-of-turn damage-over-time for one combatant is combined into one contribution before action suppression; eligible opposing-faction damage only is counted, duration advancement must preserve pending suppression, and effects are not accumulated across turns.
10. An action uses the pre-action Momentum state for applicable bonuses; its own damage contribution affects subsequent actions. Start-of-turn status damage updates Momentum before the upcoming action's bonuses are calculated.
11. Numerical superiority creates more action opportunities naturally; no headcount normalization or passive headcount shift is applied.
12. Both factions receive faction-wide critical advantages of +2 percentage points per control level up to +10 at +5; retain the existing 35% critical cap.
13. Both factions receive symmetric damage and mitigation advantages at +3/+4 (5%) and +5 (10%), not cumulatively. Preserve integer floors; outgoing is after attacker modifiers/before defenses, mitigation is after defenses/before critical.
14. Runaway control is possible by design; no automatic comeback, passive decay, or rubber-band mechanic is added.
15. Momentum is temporary, encounter-owned, non-spendable, and independent of Mana/Super.

## Gate 0 Closure

Gameplay rules, arithmetic, source-seam audit, deterministic event matrix, and shared-meter presentation are approved and recorded in [the M7 milestone plan](../current/milestones/m7-momentum.md). Gate 0 is closed for planning. Its closure records the implementation contract but does not implement gameplay.

- The meter includes visible +3 and +5 threshold cues on both faction sides, with text labels so state is not conveyed by color alone.
- The browser and terminal display the same Python-authoritative position and active bonuses; neither client calculates combat outcomes.
- The final deterministic event matrix covers attribution, defense reduction, mixed-source DoT, suppression preservation, damage ordering, threshold changes, and faction symmetry.
- At Gate 0 closure, M7 implementation remained a separate next step; no gameplay code was changed in that planning closure. Current implementation and qualification progress is tracked in the [M7 milestone plan](../current/milestones/m7-momentum.md).

## Implementation Boundary

M7's Gate 0 contract is closed for planning. The scale, damage shifts, defense reduction, DoT attribution/suppression behavior, critical progression, +3/+5 arithmetic, and presentation are approved inputs. Gate 0 closure itself did not implement gameplay; implementation progress and remaining qualification are tracked in the [M7 milestone plan](../current/milestones/m7-momentum.md). The shared specification remains one contested encounter value, not the superseded per-combatant model.

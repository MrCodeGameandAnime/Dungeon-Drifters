# M7 Momentum Implementation Plan

> Planning only. The November 17, 2026 design revision supersedes the earlier per-combatant Momentum model. Gate 0 remains open; no gameplay implementation is authorized.

**Status:** Design revision incorporated; remaining numerical, interaction, and interface contracts require resolution before implementation.

**Goal:** Add a temporary, encounter-wide measure of contested battlefield control. Control can improve the controlling faction's critical-hit frequency and, at proposed dominance thresholds, outgoing damage and incoming mitigation. Momentum is not a spendable resource or permanent progression system.

**Authority:** [Momentum design](../../future/momentum.md) is the current design authority. Revalidate the repository's combat, damage, critical, presentation, and runtime seams at M7 entry against the then-current [roadmap](development-roadmap.md), [M3](m3-character-advancement.md), and [M4](m4-enemy-progression.md) contracts.

## Supersession And Scope

The revised design replaces the prior proposal for independent Momentum values on each combatant. There is one shared bar for the encounter, contested by the Drifter side and the enemy side. All participants contribute to and are affected by that shared state according to their faction.

Momentum is an integer from 0 through 10, starts at 5 (neutral), and clamps at either endpoint. Positions 0-4 favor enemies; positions 6-10 favor Drifters. The equivalent relative-control values are Enemy +5 through Enemy +1, Neutral, and Drifter +1 through Drifter +5. Movement crosses neutral freely, without a barrier or conversion penalty. This is collective battlefield control, not an individual flow meter and not a round-based score. Final visual styling remains a presentation task.

Action opportunities are intentionally not normalized by party size. Outnumbering creates more opportunities to influence the shared state; actual action outcomes, not a passive headcount adjustment, determine its movement. No passive decay, rubber-banding, or guaranteed comeback mechanic is in scope.

Momentum remains encounter-scoped, authoritative in Python, non-spendable, independent of Mana and Super, excluded from permanent player progression and ordinary saves, and reset when an encounter ends. No save-schema change is expected for this temporary state.

## Approved Combat Contract

Drifters and enemies use the same universal damage-based Momentum rules. Classify actual HP damage against the target's remaining HP immediately before the relevant damage resolution. Do not use theoretical damage or overkill. The 10% cutoff is inclusive and is evaluated without requiring floating-point division:

```text
actual_hp_damage * 10 >= hp_before_damage
```

| Damage outcome | Base shift before target defense |
| --- | ---: |
| Actual damage below 10% of pre-damage remaining HP | 1 tick toward attacker |
| Actual damage at least 10% of pre-damage remaining HP | 2 ticks toward attacker |
| Miss or zero actual HP damage | 0 ticks |
| Healing | 0 ticks |
| Rejected action | 0 ticks |

There are no further damage tiers. A critical hit does not receive a separate Momentum multiplier; its actual HP damage is classified by these same rules.

Defense reduces the contribution by one tick, with a floor of zero. It does not move Momentum toward the defending faction:

| Damage outcome | Without defense | With defense |
| --- | ---: | ---: |
| Standard | 1 tick | 0 ticks |
| Enhanced | 2 ticks | 1 tick |

For a split physical/magical attack, sum the actual HP damage from the resolved components, classify once against the target's pre-attack remaining HP, and apply one contribution for the attack. Do not create one shift per component. Multi-hit, multi-target, and simultaneous outcomes remain unresolved.

At the beginning of a combatant's turn, combine all applicable start-of-turn damage-over-time effects for that combatant into one Momentum calculation. Resolve their ordinary damage and duration behavior, sum actual HP removed during that phase, compare it with the combatant's HP immediately before the phase, then apply one universal shift before determining whether the combatant can act. Damage from earlier turns is not accumulated. The responsible faction receives the shift; attribution for mixed-source effects remains to be resolved if the existing status system supports them.

Combat calculations read the applicable critical, outgoing-damage, and incoming-mitigation advantages from the current shared Momentum at the relevant resolution boundary. For a damage-causing action, apply its Momentum shift only after its damage resolves, so that action cannot benefit retroactively from the state it creates. Start-of-turn status damage resolves first, so its resulting Momentum can affect subsequent combat calculations if the combatant survives and can act.

The previously proposed critical progression is listed alongside the damage and mitigation thresholds below. Critical bonuses are additive percentage points, not multipliers to existing critical chance. The +2 percentage-point-per-advantage-level progression remains illustrative; final approval and interaction with existing critical caps remain open. Existing non-Momentum critical modifiers remain governed by their current contracts.

## Proposed Dominance Bonuses

The current design direction adds outgoing damage and incoming damage mitigation at +3 and +5 faction advantage. These percentage bonuses are symmetric: the Drifter faction and enemy faction use the same table. Thresholds do not stack with one another; +5 means 10%, not 15%, and +4 retains the +3 tier.

| Faction advantage | Illustrative critical bonus | Current proposed outgoing damage | Current proposed incoming mitigation |
| --- | ---: | ---: | ---: |
| Neutral | +0 percentage points | 0% | 0% |
| +1 | +2 percentage points | 0% | 0% |
| +2 | +4 percentage points | 0% | 0% |
| +3 | +6 percentage points | +5% | +5% |
| +4 | +8 percentage points | +5% | +5% |
| +5 | +10 percentage points | +10% | +10% |

The +3/+5 thresholds and values are planning direction; the arithmetic contract is not closed. Integrate them into the existing authoritative combat damage calculation; do not create a separate Momentum damage pipeline. Gate 0 must establish percentage rounding and composition with existing damage modifiers, where percentage mitigation enters the existing defensive pipeline, and how it relates to the separate one-tick reduction to Momentum contribution. Do not treat that one-tick reduction as percentage mitigation or assume one automatically implies the other.

Momentum bonuses are read from the authoritative state at the relevant action boundary. An attack does not gain a bonus retroactively from Momentum created by its own damage; later actions use the updated state. Start-of-turn damage can change the state before the affected combatant acts. Once Gate 0 establishes the order and rounding, classify the attack using actual HP removed after the applicable outgoing modifiers and incoming mitigation. The proposed damage and mitigation bonuses can therefore affect whether an attack is standard or enhanced. Exact ordering and rounding remain Gate 0 items.

The intended tactical stages are establishing advantage at +1/+2, dominance at +3/+4, and maximum dominance at +5. Preventing the opposing faction from reaching +3 is a primary defensive objective; maximum control is intentionally powerful and may snowball. Do not add automatic recovery, decay, headcount normalization, or rubber-banding.

No headcount normalization, passive numerical-superiority shift, automatic comeback bonus, or rubber-banding is in scope. Momentum remains one encounter-scoped shared integer, authoritative in Python, non-spendable, and outside permanent progression and ordinary saves.

## Architecture And Implementation Boundary

The shared value belongs to the encounter's authoritative combat state. Combat action and damage resolution determines changes; `Battle` coordinates the lifecycle; presenters expose the authoritative value and feedback. Terminal and browser clients must not calculate Momentum, critical, damage, or mitigation bonuses independently.

There must not be per-Drifter or per-enemy Momentum pools. All faction-wide advantage effects derive from the single encounter value. The design does not require a new move, enemy, `ResourceType`, persistent `PlayerState` field, or saved Momentum value merely to demonstrate the system.

At milestone entry, inspect the actual post-M3/M4 combat result, critical-resolution boundaries, and status-effect turn lifecycle before selecting integration points. Do not assume existing status effects already resolve at the required pre-action boundary. Do not prescribe stale class or method names as settled APIs. Preserve existing combat behavior except for explicitly approved Momentum effects.

## Gate 0 - Resolve The Gameplay Contract

- Approved: integer range 0-10, neutral/start at 5, faction direction, endpoint bounds, and free crossing through neutral; no fractional Momentum.
- Approved: standard 1-tick and enhanced 2-tick attack contributions, inclusive 10% actual-damage threshold, and no additional damage tiers.
- Approved: miss/zero actual HP damage, healing, and rejected actions cause no shift; defense reduces the normal contribution by one tick without shifting toward the defender.
- Approved: split-damage components are combined into one attack contribution; critical hits contribute only through their actual damage classification.
- Approved: start-of-turn damage-over-time for one combatant is combined into one contribution before that combatant's action; an action uses the pre-action Momentum state, and its own damage shift affects later actions.
- Proposed dominance direction: +3/+4 grant +5% outgoing damage and +5% incoming mitigation; +5 grants +10% of each, noncumulatively. The same thresholds apply symmetrically to both factions.
- [ ] Resolve multi-hit, multi-target, and simultaneous target outcomes, plus attribution when combined start-of-turn effects have mixed faction sources (if supported by current status content).
- [ ] Confirm which existing defensive states qualify for the approved one-tick defense reduction; preserve existing Defend/Brace/mitigation behavior otherwise.
- [ ] Approve or revise the illustrative +2 percentage-point-per-advantage-level critical progression; confirm its interaction with existing critical caps/modifiers without changing those contracts. The bonus is an additive percentage-point amount, not a multiplier.
- [ ] Resolve percentage damage and mitigation rounding; order Momentum damage bonuses with existing outgoing modifiers and order Momentum mitigation with existing defensive mechanics.
- [ ] Resolve how percentage mitigation interacts with the separate one-tick reduction to Momentum contribution; do not collapse these distinct effects.
- [ ] Confirm that final authoritative HP damage after the approved modifier/mitigation ordering and rounding is used for the 10% standard/enhanced classification.
- [ ] Verify the deterministic event matrix covers +2, +3, +4, and +5, immediate loss or reduction when crossing thresholds, and symmetric behavior for both factions.
- [ ] Decide whether any non-damaging actions beyond healing, Intuition, authored moves, bosses, or other authored properties modify Momentum. No special modifier is assumed by default.
- [ ] Approve terminal/browser presentation and shift feedback for the settled integer and relative-control model.
- [ ] Audit current combat, critical, mitigation, and client seams against the repository at M7 entry.

**Gate 0 proof:** A normative event-and-effect matrix with deterministic examples for both factions, approved arithmetic and ordering, and no unresolved rule required to begin coding. The universal damage/DoT rules are recorded above. The illustrative critical progression and proposed +3/+5 dominance thresholds are recorded; critical-cap interaction and percentage rounding/modifier ordering remain open.

## Gate 1 - Shared Encounter State And Lifecycle

- [ ] Add one bounded encounter-wide value initialized at neutral and accessible consistently to all participants and projections.
- [ ] Test neutral initialization, integer legal bounds, endpoint clamping, invalid updates, immutable presentation, and a single shared value under two- and four-Drifter encounters and multi-enemy encounters.
- [ ] Test faction direction, free crossing through neutral, and faction reversal without creating actor-specific values or implicit per-enemy meters.
- [ ] Prove the value is reset on victory, defeat, escape, construction failure, teardown, and subsequent encounter creation.
- [ ] Keep Momentum absent from player progression and persisted save payloads; do not reset or alter Mana/Super as a side effect.

**Gate 1 proof:** One authoritative shared value with validated bounds and complete encounter lifecycle isolation.

## Gate 2 - Action, Damage, And Critical Resolution

- [ ] Integrate the approved event matrix at authoritative action/damage boundaries, not from UI logs or per-component callbacks unless the approved rule explicitly requires that granularity.
- [ ] Test standard/enhanced damage at the 10% boundary, defended shift reduction, misses, zero actual damage, rejected inputs, healing, split-component aggregation, and every approved exceptional damage source.
- [ ] Verify Enemy +1 (position 4) plus an undefended enhanced 2-tick shift becomes Drifter +1 (position 6); verify Drifter +1 plus an enemy standard 1-tick shift returns to neutral, and reverse faction roles.
- [ ] Test start-of-turn Burn 5 + Poison 5 against 100 pre-phase HP as one enhanced contribution; verify effects from separate turns are not accumulated and the resulting Momentum bonuses are used for the next action.
- [ ] Test that an action uses pre-action Momentum for its critical and applicable damage bonuses, then applies its damage shift for subsequent actions; criticals receive no separate Momentum multiplier.
- [ ] Test the proposed advantage table at +2, +3, +4, and +5: no damage/mitigation bonus at +2, 5%/5% at +3 and +4, and 10%/10% at +5 rather than cumulative 15%.
- [ ] Test that both factions receive equivalent bonuses, that a generated Momentum shift only affects later actions, and that crossing below +3 or from +5 to +4 immediately removes or reduces the applicable tier.
- [ ] Test damage/mitigation rounding and composition with existing modifiers once those Gate 0 rules are approved; verify final actual HP damage controls the standard/enhanced threshold.
- [ ] Verify action counts are naturally respected without round-based normalization or additional headcount shifts.
- [ ] Test that the critical rule maps shared control to the appropriate faction's attacks and respects the approved cap and update ordering once the progression is finalized.
- [ ] Verify neutral grants neither faction a Momentum-derived critical bonus.
- [ ] Include deterministic tests at neutral and each finalized critical threshold, including any feedback from a critical hit to Momentum.

**Gate 2 proof:** Seeded resolution and state changes match the Gate 0 matrix for both sides, with no duplicate contribution from split representation, multi-hit effects, targets, or logs.

## Gate 3 - Feedback, Clients, And Save Exclusion

- [ ] Presenter, terminal, and browser contract tests show the same authoritative shared value and correct faction advantage.
- [ ] Built-browser coverage exercises a meaningful shift in both directions, neutral behavior, and encounter reset without client-authored game state.
- [ ] Check desktop and mobile layouts and terminal readability; feedback must not obscure targets, HP/Mana/Super, or actions.
- [ ] Verify save/reload boundaries contain no Momentum state and starting a new encounter always starts neutral.

**Gate 3 proof:** Semantic parity across clients and no accidental persistence or duplicated client rules.

## Gate 4 - Runtime And Cumulative Qualification

- [ ] Extend the pinned runtime probe with bounded shared-state updates, both faction directions, critical projection, and reset behavior.
- [ ] Run the applicable cumulative Python, web, content, build, browser, hosted service, migration, and exact-SHA CI checks.
- [ ] Record exact runtime and hosted evidence; do not describe deferred checks as passed.

**Closure:** The approved shared contested mechanic is implemented and qualified with deterministic action/critical behavior, faction-wide projection, encounter reset, client parity, and no save or unrelated combat regressions.

## Open Product Decisions

| ID | Decision still required before implementation |
| --- | --- |
| M7-D1 | Momentum effects for multi-hit, multi-target, and simultaneous target outcomes. |
| M7-D2 | Faction attribution when a combined start-of-turn damage phase includes effects from multiple factions, if supported by authored status content; map the approved defense reduction to existing defensive states. |
| M7-D3 | Final critical bonus progression; the +2 percentage-points-per-advantage-level table remains illustrative. Percentage-point semantics are fixed; resolve interaction with existing critical caps and preserve non-Momentum modifier contracts. |
| M7-D4 | Any Momentum effects for non-damaging actions beyond healing, or for Intuition, authored moves, bosses, or other authored properties. No special modifier is assumed by default. |
| M7-D5 | Final terminal/browser presentation and feedback for integer position, relative control, and standard/enhanced shifts. |
| M7-D6 | Final arithmetic integration for proposed +3/+5 dominance bonuses: percentage rounding, outgoing-modifier and incoming-defense order, interaction with the one-tick Momentum defense reduction, and use of final actual damage for the 10% classification. |

The integer scale, 1/2-tick damage shifts, 10% threshold, defense reduction, combined start-of-turn damage rule, and dynamic pre-action timing are approved planning contracts. The +3/+5 damage and mitigation thresholds are the current proposed dominance direction; the critical conversion and exact arithmetic integration remain open. Gate 0 is not closed. Do not reintroduce the superseded per-combatant model or infer missing values from historical examples.

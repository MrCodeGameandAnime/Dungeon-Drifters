# M7 Momentum Implementation Plan

> Planning only. The November 17, 2026 design revision supersedes the earlier per-combatant Momentum model. Gate 0 is closed for planning: gameplay contracts, source-seam audit, and presentation are approved. No gameplay implementation was performed as part of Gate 0 closure.

**Status:** Gate 0 complete; M7 implementation contract is ready for its separately authorized implementation step.

**Goal:** Add a temporary, encounter-wide measure of contested battlefield control. Control can improve the controlling faction's critical-hit frequency and, at approved dominance thresholds, outgoing damage and incoming mitigation. Momentum is not a spendable resource or permanent progression system.

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

| Damage outcome | Base shift before active Defend/Brace contribution reduction |
| --- | ---: |
| Actual damage below 10% of pre-damage remaining HP | 1 tick toward opposing-faction source |
| Actual damage at least 10% of pre-damage remaining HP | 2 ticks toward opposing-faction source |
| Miss or zero actual HP damage | 0 ticks |
| Healing | 0 ticks |
| Rejected action | 0 ticks |

There are no further damage tiers. A critical hit does not receive a separate Momentum multiplier; its actual HP damage is classified by these same rules.

An applicable active Defend or Brace state reduces the contribution by one tick, with a floor of zero. Apply this reduction at most once per resolved attack, even when both states or multiple split components qualify. It does not move Momentum toward the defending faction. Passive stat, equipment, and passive-skill mitigation do not qualify, and Momentum's own percentage mitigation does not grant an additional reduction:

| Damage outcome | Before active-defense contribution reduction | With applicable active Defend/Brace |
| --- | ---: | ---: |
| Standard | 1 tick | 0 ticks |
| Enhanced | 2 ticks | 1 tick |

For a split physical/magical attack, sum the actual HP damage from the resolved components, classify once against the target's pre-attack remaining HP, and apply one contribution for the attack. Do not create one shift per component. The current combat model resolves one target and one hit per move action, and actions resolve sequentially; M7 does not add multi-hit, multi-target, or simultaneous attacks. Revisit their Momentum rules only if those mechanics are introduced later.

At the beginning of a combatant's turn, resolve its applicable damage-over-time effects before checking whether stun, frozen, or another action-opportunity suppression prevents it from acting. Status ticks retain their authored damage and tick counts. Sum only actual HP damage from effects sourced by the opposing faction; ignore same-faction and unattributed damage for Momentum while preserving their ordinary status damage. Compare that eligible sum with the combatant's HP immediately before the entire DoT phase, then apply one contribution. Multiple opposing-faction sources still produce only one contribution. Do not accumulate damage across turns. Defend/Brace do not reduce this DoT contribution because the existing status tick path does not apply those defenses and the one-tick reduction is defined per resolved attack.

The DoT phase and its duration advancement must not consume, clear, replace, or expire action-suppression state before its normal action-opportunity check. If the combatant survives, the normal suppression check still occurs and consumes the applicable stun/frozen opportunity as usual. If DoT defeats the combatant, no action occurs; ordinary defeated-combatant cleanup may then clear its statuses.

Combat calculations read the applicable critical, outgoing-damage, and incoming-mitigation advantages from the current shared Momentum at the relevant resolution boundary. For a damage-causing action, apply its Momentum shift only after its damage resolves, so that action cannot benefit retroactively from the state it creates. Start-of-turn status damage resolves first, so its resulting Momentum can affect subsequent combat calculations if the combatant survives and can act. Only damage attributable to an opposing faction contributes: self-backlash and unattributed environmental damage do not shift Momentum.

Critical bonuses are additive percentage points, not multipliers to existing critical chance. Each faction advantage level adds 2 percentage points, reaching +10 percentage points at +5. Add this to the existing critical chance calculation and retain the existing 35% cap and all non-Momentum critical modifiers.

## Approved Dominance Bonuses

The approved design adds outgoing damage and incoming damage mitigation at +3 and +5 faction advantage. These percentage bonuses are symmetric: the Drifter faction and enemy faction use the same table. Thresholds do not stack with one another; +5 means 10%, not 15%, and +4 retains the +3 tier.

| Faction advantage | Critical bonus | Outgoing damage | Incoming mitigation |
| --- | ---: | ---: | ---: |
| Neutral | +0 percentage points | 0% | 0% |
| +1 | +2 percentage points | 0% | 0% |
| +2 | +4 percentage points | 0% | 0% |
| +3 | +6 percentage points | +5% | +5% |
| +4 | +8 percentage points | +5% | +5% |
| +5 | +10 percentage points | +10% | +10% |

Preserve existing integer-floor arithmetic and modifier ordering. Apply the Momentum outgoing multiplier after existing attacker-side modifiers and before target defenses. Apply Momentum mitigation after existing defenses and before the critical multiplier. For split-component attacks, apply each multiplier at the corresponding existing per-component stage, sum actual component damage, and apply the single critical multiplier once. Do not create a separate Momentum damage pipeline. The one-tick active-defense contribution reduction remains a separate rule and is not triggered by passive or Momentum percentage mitigation.

Momentum bonuses are read from the authoritative state at the relevant action boundary. An attack does not gain a bonus retroactively from Momentum created by its own damage; later actions use the updated state. Start-of-turn damage can change the state before the affected combatant acts. Classify an attack using final actual HP removed after the applicable outgoing modifiers, defenses, Momentum mitigation, and critical multiplier. The damage and mitigation bonuses can therefore affect whether an attack is standard or enhanced. Status ticks retain their authored damage values; their actual eligible HP damage affects Momentum contribution only.

The intended tactical stages are establishing advantage at +1/+2, dominance at +3/+4, and maximum dominance at +5. Preventing the opposing faction from reaching +3 is a primary defensive objective; maximum control is intentionally powerful and may snowball. Do not add automatic recovery, decay, headcount normalization, or rubber-banding.

No headcount normalization, passive numerical-superiority shift, automatic comeback bonus, or rubber-banding is in scope. Momentum remains one encounter-scoped shared integer, authoritative in Python, non-spendable, and outside permanent progression and ordinary saves.

## Presentation Proposal

Show one shared Momentum strip throughout battle, not separate meters for individual Drifters or enemies. The strip represents all eleven positions, with Enemy +5 at 0, Neutral at 5, and Drifter +5 at 10. Always pair the marker with a plain-text position and relative-control label, such as `Momentum 8/10 - Drifters +3`.

Mark the +3 advantage thresholds at positions 2 (Enemy +3) and 8 (Drifter +3), where the 5% damage and mitigation tier begins. Mark the +5 endpoints at positions 0 and 10, where the 10% tier applies. Use visible notches or equivalent distinct markers plus a short text legend; do not rely on color alone. The current marker and bonus text must make clear which side's threshold is active.

When a faction controls Momentum, show its currently active advantages in the same view, using explicit units: for example, `Drifters: critical chance +6 percentage points; outgoing damage +5%; incoming mitigation +5%`. At neutral, show that neither side has a Momentum bonus. The displayed values come from the Python-owned view; browser JavaScript only renders them.

The browser proposal is an accessible 0-10 meter with a value-text label identifying the controlling faction, the +3/+5 threshold landmarks, and active bonuses. The terminal proposal is a compact text/bar line in the existing battle status area, readable in both framed and linear layouts, with the threshold cues also understandable in narrow linear output. Refresh the same authoritative view after each attack and after the DoT phase, before the next action. The bar and bonus line provide shift feedback; do not add a duplicate log entry for each tick. The semantic treatment and threshold cues are approved; exact styling and layout remain subject to implementation qualification.

## Architecture And Implementation Boundary

The shared value belongs to the encounter's authoritative combat state. Combat action and damage resolution determines changes; `Battle` coordinates the lifecycle; presenters expose the authoritative value and feedback. Terminal and browser clients must not calculate Momentum, critical, damage, or mitigation bonuses independently.

There must not be per-Drifter or per-enemy Momentum pools. All faction-wide advantage effects derive from the single encounter value. The design does not require a new move, enemy, `ResourceType`, persistent `PlayerState` field, or saved Momentum value merely to demonstrate the system.

### Final Repository Seam Audit

- `root/src/app/combat/resolver.py` resolves a move against one target with one hit roll; split components are resolved through the existing damage path, summed into one applied move result, and receive one critical multiplier. Actual HP removed is available after applying damage. The existing critical chance cap is 35% (`MAX_ORDINARY_CRIT_CHANCE`).
- `root/src/app/combat/battle.py` checks action-opportunity suppression before an actor acts. `root/src/app/combat/combat_state.py` currently advances DoT through `complete_accepted_action()`, after an accepted action. `root/src/app/combat/status_state.py` stores source and target on DoT statuses and keeps stun/frozen suppression in separate state collections. M7 must move the DoT phase to the start-of-turn boundary without allowing duration advancement to consume or expire the pending suppression; defeated-combatant cleanup remains responsible for clearing statuses after lethal DoT.
- `root/src/app/presentation/battle_models.py` defines immutable `BattleView` and reconstructs it in `with_expedition_status()`; no Momentum projection exists yet. `root/src/app/presentation/battle_presenter.py` builds the view, `root/src/app/ui/terminal_battle_ui.py` owns framed and linear rendering, `root/web/python/dd_bridge.py` recursively projects dataclasses, and `root/web/play/js/pyd4.js` renders the browser view. M7 must expose one Python-authoritative projection, preserve it through view-copy paths, and render it in both clients without client-side combat calculations.

This audit confirms a bounded integration path and identifies the intentional DoT scheduling change. It does not freeze future API names or authorize implementation.

## Gate 0 - Contract And Final Verification

- Approved: integer range 0-10, neutral/start at 5, faction direction, endpoint bounds, and free crossing through neutral; no fractional Momentum.
- Approved: standard 1-tick and enhanced 2-tick attack contributions, inclusive 10% actual-damage threshold, and no additional damage tiers.
- Approved: miss/zero actual HP damage, healing, and rejected actions cause no shift; applicable active Defend or Brace reduces a resolved attack's contribution by one tick, at most once, without shifting toward the defender. Passive and Momentum percentage mitigation do not qualify.
- Approved: split-damage components are combined into one attack contribution; critical hits contribute only through their actual damage classification.
- Approved: start-of-turn DoT is combined into one contribution before the action-opportunity suppression check; eligible opposing-faction damage alone is counted, and DoT plus duration advancement cannot consume, clear, or expire pending suppression before its normal check. If DoT defeats the combatant, no action occurs.
- Approved: +2 critical percentage points per faction advantage level, up to +10 at +5, subject to the existing 35% cap.
- Approved: +3/+4 grant +5% outgoing damage and +5% incoming mitigation; +5 grants +10% of each, noncumulatively and symmetrically. Apply with the existing integer-floor ordering: outgoing after attacker modifiers/before defenses; mitigation after defenses/before critical.
- Approved: only damage attributable to an opposing faction contributes. Same-faction, self-backlash, and unattributed environmental damage do not shift Momentum; mixed-source DoT counts only eligible opposing-faction actual damage in its single contribution.
- Resolved for current combat model: one target and one hit per move action, sequentially resolved. Future multi-hit, multi-target, or simultaneous mechanics require their own reviewed rule before introduction.
- [x] Approve the shared terminal/browser meter with relative-control labels, active bonuses, and visible +3/+5 threshold cues.
- [x] Complete the M7 entry audit of current action, status, critical, defense, and client seams.
- [x] Record the deterministic event matrix below, including both factions, defense reduction, mixed-source DoT, and threshold updates.
- Approved: no special Momentum modifiers for Intuition, individual moves, bosses, or non-damaging effects; healing contributes zero. Other damage follows the universal rules when attributable to an opposing faction.

### Deterministic Event Matrix

| Event | Example and authoritative result |
| --- | --- |
| Drifter standard attack | At position 4 (Enemy +1), remove 9 of 100 pre-hit HP: one tick toward Drifters, ending at 5. If applicable active Defend/Brace reduces the contribution, it becomes zero and stays at 4. |
| Enemy enhanced attack | At position 6 (Drifter +1), remove 10 of 100 pre-hit HP: two ticks toward enemies, ending at 4. If applicable active Defend/Brace reduces the contribution once, it becomes one tick and ends at 5. |
| Split attack | Sum actual HP removed across its components and classify once against pre-attack HP. A 4+6 result against 100 HP is one enhanced attack and contributes two ticks, not one contribution per component. |
| Mixed-source DoT | Against 100 pre-phase HP, opposing-faction sources remove 5+5 HP while same-faction and unattributed sources remove 4+1 HP. All damage resolves normally; only the eligible opposing-faction 10 counts, producing one enhanced two-tick contribution. DoT does not receive the active-attack one-tick reduction. |
| Suppressed turn | Resolve DoT and its duration advancement before the suppression check without consuming, clearing, or expiring the pending stun/frozen opportunity. If the combatant survives, the ordinary check still suppresses the action; if DoT defeats them, no action occurs. |
| No eligible damage event | Miss, zero actual HP damage, healing, rejected action, same-faction damage, self-backlash, or unattributed environmental damage causes no Momentum change. |
| Dynamic thresholds | At +2/+3/+4/+5, the controlling faction receives +4/+6/+8/+10 critical percentage points and 0%/5%/5%/10% damage and mitigation. The enemy faction uses the identical table. Read bonuses from pre-action Momentum; apply an attack's shift only after its damage resolves. Crossing +5 to +4 reduces the damage/mitigation tier to 5%; crossing +3 to +2 removes it. |

**Gate 0 status: CLOSED FOR PLANNING.** The event matrix, approved arithmetic and attribution rules, repository seam audit, and user-approved terminal/browser presentation are recorded. M7's implementation remains a separate next step; no gameplay code was changed in this closure.

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
- [ ] Test start-of-turn Burn 5 + Poison 5 against 100 pre-phase HP as one enhanced contribution; test mixed sources count only opposing-faction actual damage and same-faction/unattributed damage is ignored for Momentum.
- [ ] Verify DoT and its duration advancement occur before stun/frozen suppression without consuming, clearing, or expiring that suppression; verify suppression still skips the action if the combatant survives, and lethal DoT prevents the action.
- [ ] Test that an action uses pre-action Momentum for its critical and applicable damage bonuses, then applies its damage shift for subsequent actions; criticals receive no separate Momentum multiplier.
- [ ] Test the approved advantage table at +2, +3, +4, and +5: no damage/mitigation bonus at +2, 5%/5% at +3 and +4, and 10%/10% at +5 rather than cumulative 15%.
- [ ] Test that both factions receive equivalent bonuses, that a generated Momentum shift only affects later actions, and that crossing below +3 or from +5 to +4 immediately removes or reduces the applicable tier.
- [ ] Test approved integer-floor composition and ordering with existing modifiers; verify final actual HP damage controls the standard/enhanced threshold.
- [ ] Verify action counts are naturally respected without round-based normalization or additional headcount shifts.
- [ ] Test that the critical rule maps shared control to the appropriate faction's attacks and respects the approved 35% cap and pre-action update ordering.
- [ ] Verify neutral grants neither faction a Momentum-derived critical bonus.
- [ ] Include deterministic tests at neutral and each finalized critical threshold, including any feedback from a critical hit to Momentum.

**Gate 2 proof:** Seeded resolution and state changes match the Gate 0 matrix for both sides, with no duplicate contribution from split-component representation or presentation logs. Multi-hit, multi-target, and simultaneous attacks remain outside M7 unless separately reviewed and approved.

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

## Gate 0 Decision Record

| ID | Decision and status |
| --- | --- |
| M7-D1 | Resolved for current combat model: one target and one hit per move action; no simultaneous resolution. Re-review if those mechanics are later introduced. |
| M7-D2 | Resolved: opposing-faction attribution; mixed-source DoT counts eligible opposing damage only. Applicable active Defend/Brace reduces attack contribution once; no reduction from passive or Momentum mitigation. Start-of-turn DoT precedes suppression without consuming it. |
| M7-D3 | Resolved: +2 critical percentage points per faction advantage level, capped by the existing 35% critical cap. |
| M7-D4 | Resolved: no special Momentum modifiers for Intuition, individual moves, bosses, or non-damaging effects; healing is zero. Unattributed and same-faction damage do not shift Momentum. |
| M7-D5 | Resolved: one shared terminal/browser meter with relative-control and active-bonus text, visible +3/+5 threshold cues, and Python-authoritative values. |
| M7-D6 | Resolved: preserve integer-floor damage ordering; outgoing Momentum bonus after attacker modifiers/before defenses; Momentum mitigation after defenses/before critical; classify using final actual HP removed. |

The integer scale, 1/2-tick damage shifts, 10% threshold, defense reduction, start-of-turn DoT ordering/attribution and suppression preservation, critical progression, +3/+5 arithmetic, and presentation are approved planning contracts. Gate 0 is closed for planning. Do not reintroduce the superseded per-combatant model or infer missing values from historical examples.

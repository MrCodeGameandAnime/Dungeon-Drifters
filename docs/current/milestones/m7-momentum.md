# M7 Momentum Implementation Plan

> Planning only. The November 17, 2026 design revision supersedes the earlier per-combatant Momentum model. Gate 0 remains open; no gameplay implementation is authorized.

**Status:** Design revision incorporated; remaining numerical, interaction, and interface contracts require resolution before implementation.

**Goal:** Add a temporary, encounter-wide measure of contested battlefield control. Control can improve the controlling faction's critical-hit frequency, but Momentum is not a spendable resource or permanent progression system.

**Authority:** [Momentum design](../../future/momentum.md) is the current design authority. Revalidate the repository's combat, damage, critical, presentation, and runtime seams at M7 entry against the then-current [roadmap](development-roadmap.md), [M3](m3-character-advancement.md), and [M4](m4-enemy-progression.md) contracts.

## Supersession And Scope

The revised design replaces the prior proposal for independent Momentum values on each combatant. There is one shared bar for the encounter, contested by the Drifter side and the enemy side. All participants contribute to and are affected by that shared state according to their faction.

The working scale is 0-10, with 5 neutral. Conceptually, the low end means enemy control and the high end means Drifter control. Exact display orientation remains open. This is collective battlefield control, not an individual flow meter and not a round-based score.

Action opportunities are intentionally not normalized by party size. Outnumbering creates more opportunities to influence the shared state; actual action outcomes, not a passive headcount adjustment, determine its movement. No rubber-banding or guaranteed comeback mechanic is in scope.

Momentum remains encounter-scoped, authoritative in Python, non-spendable, independent of Mana and Super, excluded from permanent player progression and ordinary saves, and reset when an encounter ends. No save-schema change is expected for this temporary state.

## Design Direction Established

- Successful offensive actions should contribute toward the acting faction establishing control; exact eligibility and amount are open.
- Meaningful incoming damage should shift control toward the attacking faction. Insignificant chip damage should not automatically erase established control.
- Momentum should be harder to establish against meaningful resistance than to lose under substantial pressure. Exact asymmetry and thresholds are open.
- Defensive performance, avoidance, and sufficient mitigation should help preserve control. Defense need not generate positive Momentum.
- Healing consumes an action opportunity and is a tactical tradeoff; whether healing itself affects the bar remains open.
- Both factions receive increasing, faction-wide critical advantages as control moves toward their end. Neutral control gives no Momentum-derived critical advantage; existing non-Momentum critical modifiers remain in effect.
- Runaway critical pressure is intentional. Do not add automatic comeback bonuses or rubber-banding.
- Critical caps, conversion, update ordering, and whether critical hits feed back into Momentum remain open.
- Multi-hit, split-damage, multi-target, status, damage-over-time, backlash, and environmental effects must not be multiplied accidentally by representation or log events. Their exact contribution rules remain open.

## Architecture And Implementation Boundary

The shared value belongs to the encounter's authoritative combat state. Combat action and damage resolution determines changes; `Battle` coordinates the lifecycle; presenters expose the authoritative value and feedback. Terminal and browser clients must not calculate Momentum, critical bonuses, completion, or decay independently.

There must not be per-Drifter or per-enemy Momentum pools. Faction-wide critical effects derive from the single encounter value. The design does not require a new move, enemy, `ResourceType`, persistent `PlayerState` field, or saved Momentum value merely to demonstrate the system.

At milestone entry, inspect the actual post-M3/M4 combat result and critical-resolution boundaries before selecting integration points. Do not prescribe stale class or method names as settled APIs. Preserve existing combat behavior except for explicitly approved Momentum effects.

## Gate 0 - Resolve The Gameplay Contract

- [ ] Confirm the numeric scale and representation, including the working 0-10 range, neutral midpoint, bounds, and displayed orientation.
- [ ] Choose whether contribution is performance-based, control-based, or a defined combination. Specify action eligibility and exact gain/quantization.
- [ ] Specify damage-loss eligibility, meaningful-damage threshold, severity scaling, gain/loss asymmetry, and whether one action can cause more than one shift.
- [ ] Resolve misses, zero-damage/status actions, multi-hit and split damage, multiple targets, DoT, backlash, hazards, and simultaneous effects.
- [ ] Specify how defend, block, dodge, Brace, mitigation, and healing preserve or change control.
- [ ] Define faction-wide critical conversion, rounding, caps, exact timing relative to an action's own Momentum change, and critical-hit feedback into the bar.
- [ ] Decide whether Intuition, authored moves, bosses, or other authored combat properties modify the shared system. No such modifier is assumed by default.
- [ ] Approve the visual/terminal presentation and the feedback shown for meaningful shifts and thresholds.
- [ ] Audit current combat, critical, mitigation, and client seams against the repository at M7 entry.

**Gate 0 proof:** A normative event-and-effect matrix with deterministic examples for both factions, no placeholder arithmetic, explicit rounding/order, and no unresolved rule required to begin coding.

## Gate 1 - Shared Encounter State And Lifecycle

- [ ] Add one bounded encounter-wide value initialized at neutral and accessible consistently to all participants and projections.
- [ ] Test neutral initialization, legal bounds, invalid updates, immutable presentation, and a single shared value under two- and four-Drifter encounters and multi-enemy encounters.
- [ ] Test faction direction without creating actor-specific values or implicit per-enemy meters.
- [ ] Prove the value is reset on victory, defeat, escape, construction failure, teardown, and subsequent encounter creation.
- [ ] Keep Momentum absent from player progression and persisted save payloads; do not reset or alter Mana/Super as a side effect.

**Gate 1 proof:** One authoritative shared value with validated bounds and complete encounter lifecycle isolation.

## Gate 2 - Action, Damage, And Critical Resolution

- [ ] Integrate the approved event matrix at authoritative action/damage boundaries, not from UI logs or per-component callbacks unless the approved rule explicitly requires that granularity.
- [ ] Test accepted actions, misses, rejected inputs, defense/avoidance, mitigation, meaningful damage, healing, and every approved exceptional damage source.
- [ ] Verify action counts are naturally respected without round-based normalization or additional headcount shifts.
- [ ] Test that a single critical rule maps shared control to the appropriate faction's attacks and respects the approved cap and update ordering.
- [ ] Include deterministic tests at neutral and each approved critical threshold, including any feedback from a critical hit to Momentum.

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
| M7-D1 | Final numerical scale/representation and whether contribution is performance-based, control-based, or combined; exact eligible action gains and quantization. |
| M7-D2 | Meaningful-damage definition, loss amount/severity, gain-versus-loss asymmetry, and handling of misses, mitigation, multi-hit/split/multi-target damage, DoT, backlash, and hazards. |
| M7-D3 | Critical conversion, rounding, cap, update ordering, and whether critical hits themselves move Momentum. |
| M7-D4 | Effects of defense, avoidance, Brace, healing, Intuition, authored move properties, and other character-specific mechanics. |
| M7-D5 | Any special boss/elite or environmental interactions beyond ordinary faction participation, plus final HUD/terminal orientation and shift feedback. |

These are open design contracts, not implementation defaults. Do not reintroduce the superseded per-combatant model or infer missing values from historical examples.

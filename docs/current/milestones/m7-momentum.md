# M7 Momentum Implementation Plan

> Implementation method: use `superpowers:executing-plans` for native gate-by-gate execution. Do not activate Momentum until its unresolved numerical contract is approved.

**Status:** Draft for review, 2026-10-29. Fixed encounter-state rules are specified; numerical/behavioral choices remain explicit entry decisions.

**Goal:** Add a shared, temporary reward for sustained combat control that raises critical frequency without becoming another spendable resource or permanent progression system.

**Architecture:** Momentum belongs to each participating combatant's encounter state within `CombatState`/Battle. Update it through authoritative action/damage results and lifecycle hooks; presenters display the result. Preserve existing Mana, Super, costs, critical/scaling rules except for the approved Momentum contribution.

**Tech stack:** Existing Python combat resolver/state/results/Battle, semantic presentation/client layers, deterministic RNG tests and pinned runtime qualification.

## Authority, Dependencies, And Exclusions

- [Momentum design](../../future/momentum.md), locked rules, unresolved questions, and encounter ownership.
- [Character growth](../../future/character-growth-and-stat-scaling.md), limited Intuition interaction and global critical limits.
- [Roadmap](../development-roadmap.md), M7/shared constraints; [M3](m3-character-advancement.md) damage/critical/effect contracts; [M4](m4-enemy-progression.md) mitigation and approved enemy behavior.

This can run before M6 if combat contracts are stable and the user selects that order. It does not depend on expedition energy or add passive/move trees. The source's v0.3 exclusion is historical deferral, not an approved formula or a reason to enable Momentum merely because the version changed.

Non-goals: Mana/Super redesign, new `ResourceType`, spending Momentum, permanent PlayerState fields, saved Momentum, automatic enemy access, natural decay, custom move thresholds or per-character exceptions unless separately selected. Current Super lifetime is preserved: although the design comparison calls it an encounter meter, the implementation owns it on `PlayerState` and persists it. Momentum's reset contract must not reset Super as a side effect.

## Current Relevant Implementation

At `8099b895`, `root/src/app/combat/combat_state.py` owns encounter Defend, Brace, heal cooldown, Arcane and status state; no active Momentum exists. `CombatResolver` returns `MoveResult`/typed outcomes, handles primary and secondary damage, criticals and Super gain. `Battle` routes accepted actions/lifecycle ticks and owns encounter completion. Multi-member actor ownership already matters; M3's independently resolved damage components may add further result detail before this milestone begins.

Current baseline ordinary critical cap is 35%, with Intuition critical and Super helpers in `player/scaling.py`. Re-read actual post-M3/M4 constants and the distinction between action damage, backlash and status ticks. Do not apply a new formula copied from this baseline after those contracts have deliberately changed.

## Canonical Behavior And Ownership

- Every playable Drifter starts each encounter at zero Momentum, has independent state, and returns to zero on every encounter exit.
- An accepted successful damaging action grants Momentum once for that action, not once per strike, target, damage packet, secondary status event, or log line.
- A miss grants none and does not remove existing Momentum. A rejected input changes nothing.
- Defending preserves it. Avoiding or sufficiently mitigating incoming damage preserves it under the approved definitions; meaningful incoming damage reduces it without necessarily resetting to zero.
- Momentum raises critical frequency but never guarantees a critical hit. Apply its approved conversion once within the accepted global critical cap and RNG resolution order.
- Intuition has a limited approved interaction, not a large raw-generation multiplier. Source examples do not select the formula.
- Enemy users, if any, require explicit authored access. Rank, tier, damage type or being a boss does not grant it implicitly.

Choose the update ordering at Gate 0, especially whether gain from the current action can affect that action's own crit (the plan does not assume it can), whether successful zero-damage/status-only outcomes qualify, and how recoil/DoT/multi-target damage affects loss. Define one loss calculation per qualifying incoming event so a split hit cannot accidentally erase more Momentum solely because M3 split its representation.

No permanent save field or schema bump is expected for Momentum itself. If additional persistent content configuration is proposed, justify it separately; combat snapshots already excluded from ordinary disk saves must remain excluded. Creating a new Battle after load/escape/win/loss cannot resurrect old Momentum from a player profile or stale presenter.

## Integration And Content

Expected existing edit areas: `root/src/app/combat/combat_state.py`, `resolver.py`, `result.py`, `battle.py`, `root/src/app/presentation/battle_models.py`/`battle_presenter.py`, terminal Battle UI and browser rendering. A small focused Momentum rules module may be justified after choosing formulas; exact names and ownership structures are revalidated at entry, not prescribed as already-existing APIs.

If enemies are selected, extend their authored capability/policy contract from M4 rather than checking display names. No new enemy or player move is required simply to exercise a shared mechanic. Configurable approved numeric values belong to one validated rules definition, not duplicated in Python/JavaScript or every Drifter kit.

Clients display each current actor's Momentum and meaningful gain/loss/preservation/crit feedback without covering existing HP/mana/Super or obscuring targets. They render Python-projected amounts and outcomes; no browser timer, decay, or inferred critical bonus. Preserve mobile phase navigation and desktop action access.

## Failure And Invariant Cases

Unknown/unregistered combatants, invalid rules, negative/boolean/nonfinite values, unsupported enemy access, stale action submission and invalid targets must not create corrupt state. An unaccepted action never grants/losses Momentum or advances a turn. A renderer exception/rebuild cannot update combat state. Probe/teardown must release participant references so this temporary system does not retain prior encounters.

Exercise normal victory, defeat, smoke escape, talisman return where permitted, encounter-construction failure and teardown. Momentum ends with that encounter under every path. Re-entering the same content is a new zero-state encounter, not a continuation of an old instance.

## Review Focus

- Rejected inputs and misses must not accidentally remove Momentum; Gate 2 checks both distinct results.
- Multi-hit/component/target actions must not multiply gain; Gate 2 checks one action-level update.
- Chip/mitigated damage and DoT/backlash must follow the selected loss boundary; Gate 2 checks exact event classes.
- Two/four members must not share Momentum or inherit enemy access; Gates 1/2 check actor isolation and explicit authoring.
- Exit/load/new encounters must clear Momentum without resetting saved Super; Gates 1/3 check every lifecycle and save exclusion.

## Gates And Tests

### Gate 0 - Approve The Numerical And Event Contract

- [ ] Resolve M7-D1 through D5 and audit the post-M3/M4 damage/result hooks.
- [ ] Record concrete examples for gain, preservation, meaningful damage, split/multi-hit actions, Intuition and the final critical cap, with exact integer rounding and update order.
- [ ] Decide enemy access and any optional decay/custom move behavior explicitly; unselected extensions stay absent.

Proof: one rules/event matrix with no placeholder formula reaches coding. Values can be editable provisional tuning after approval; fixed encounter ownership does not change.

### Gate 1 - Encounter State And Lifecycle

- [ ] Red/green focused combat-state tests for zero initialization, independent two/four-member state, validated clamping/bounds, immutable read projection and reference release on teardown.
- [ ] Implement minimal encounter-owned state and rules validation. Do not add PlayerState, save, Mana or `ResourceType` fields.
- [ ] Test new encounter after win/loss/escape/load starts at zero; current Super/Mana persistence is unchanged.

Proof: temporary state is isolated and leak-free; static/transitive import tests keep heavy persistence/network dependencies outside gameplay.

### Gate 2 - Action And Damage Resolution

- [ ] Extend existing resolver/Battle tests with successful action gain, miss preservation, Defend/avoidance preservation, approved partial mitigation, meaningful damage loss and rejection with zero mutation.
- [ ] Pin one gain per multi-hit/component/multi-target action and approved loss classification for DoT/backlash/phase/hazard effects. Verify update ordering with deterministic critical rolls at exact cap boundaries.
- [ ] Integrate approved Intuition contribution and enemy access. Test absence of authoring does not grant regular enemies Momentum; invalid access cannot bypass capability checks.

Proof: seeded results match the matrix; gain/loss occurs from real semantic actions, not a HUD calculation or per-log callback.

### Gate 3 - Feedback, Clients, And Save Exclusion

- [ ] Presenter/terminal/bridge tests verify exact actor amounts and outcome feedback with two and four members. Check phone portrait/landscape and desktop for readable unchanged control reachability.
- [ ] Built Playwright journey gains Momentum, misses/defends/takes approved damage, finishes or escapes, then begins another encounter at zero. Save/reload at a legal checkpoint proves no permanent Momentum state.
- [ ] Explicitly test schema/source snapshots remain free of Momentum and existing full move kits/purchases, component effects and Super costs are unchanged.

Proof: both clients observe the same rules without implementing them and no saved resource is introduced accidentally.

### Gate 4 - Runtime And Cumulative Qualification

- [ ] Extend the real probe with bounded gain/loss/reset semantics and party-member isolation; preserve historical markers and record changed memory pressure honestly.
- [ ] Run shared cumulative qualification, unchanged persistence/service regressions and exact-SHA hosted checks; obtain review before activating the mechanic in the accepted milestone.

Closure: shared temporary Momentum has approved formulas, real action integration, deterministic cap/lifecycle proof, client parity, and no permanent-save or other-resource regressions. Optional enemy/custom-move systems count only if actually approved and proven.

## Unresolved Product Decisions

| ID | Decision and blocking gate |
| --- | --- |
| M7-D1 | Maximum, gain and numerical representation; Gate 0 |
| M7-D2 | Meaningful damage, severity-based loss, sufficient mitigation, DoT/backlash/multi-target handling; Gate 0 |
| M7-D3 | Critical conversion/rounding/cap and pre/post-action update ordering; Gate 0 |
| M7-D4 | Limited Intuition interaction and whether natural decay/custom move thresholds exist; Gate 0 |
| M7-D5 | Explicit boss/elite access and HUD feedback policy; before Gates 2/3 |

These choices are not answered by illustrative formulas in the future document; do not silently freeze them here.

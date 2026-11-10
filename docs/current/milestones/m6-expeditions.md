# M6 Expeditions And The Two-Plus-Two Loop

> Gate 0 is closed and the M6 plan is implementation-ready. This documentation update does not authorize gameplay implementation.

**Planning baseline:** `c64332d0fe9aeac5811f6eb27f0edea836ff7451` (`dungeon`)
**Status:** M4B closed; M6 Gate 0 closed, 2026-11-10. Implementation requires separate authorization.
**Goal:** Add supplementary, floor-grounded expeditions for the existing four-Drifter roster without gating ordinary dungeon play or changing sealed combat, extraction, recruitment, or progression rules.

## Authority

- [Party and Expedition Core Loop](../../future/party-and-expedition-core-loop.md) owns roster deployment and expedition design.
- [Dungeon Progression, Difficulty, and Economy](../../future/dungeon-progression-difficulty-and-economy.md) owns dungeon risk and the expedition energy economy.
- [Development Roadmap](development-roadmap.md) sets milestone dependencies.
- [M1 roster](m1-permanent-roster.md), [M2 supplies and exits](m2-preparation-trading-escape.md), [M3 advancement](m3-character-advancement.md), [M4 enemy progression](m4-enemy-progression.md), and [M5 equipment](m5-armor-accessories.md) remain implementation authorities for their sealed behavior.

M6 becomes available only after the existing M4 Floor III clear/full-roster gate and four permanent recruits. This unlock condition is unchanged. Destination eligibility is separate: an expedition can target only a floor whose authoritative completion state is already true. No Floor IV route or proof route is part of M6.

## Approved M6 Contract

### Energy

| Rule | M6 contract |
| --- | --- |
| Capacity and initial balance | 100 maximum; first initialization, including a supported existing save, starts at 100 |
| Launch cost | 10 energy for each of the initially available assignment categories |
| Regeneration | 1 energy per 9 elapsed minutes (10 per 90 minutes) |
| Offline time | Counts, capped at 100 energy |
| Clock anchor | Persist UTC; a backward clock reading grants no energy and must not move the accepted anchor backward |
| Payment | Deduct atomically when the player confirms launch |
| Cancel/refund | Cancel before confirmation costs nothing; no refund after confirmation |
| Refills | No paid refills or separate earned-refill mechanic in M6 |
| Scope | Energy gates expedition launch only; it never gates dungeon entry, combat, extraction, or progression |

Approved overflow rule: regeneration stops at 100. Time spent at capacity creates no hidden credit; if energy is spent while at capacity, rebase the regeneration anchor to that spend time so there is no immediate refill. Normal one-per-nine-minute regeneration resumes from that point. Test full capacity, subsequent spending, and resumed regeneration.

The game currently has UTC-aware timestamp handling in persistence, but no gameplay clock/timer owner. M6 must use an authoritative shared-domain clock and persisted time evidence; clients may display status but may not determine elapsed time or settlement.

This is device-clock-based offline play, not trusted server time: persisted UTC prevents ordinary reload resets and backward-clock energy gains, but does not make a local save tamper-proof against deliberate clock changes. Stronger clock authority would require a separately approved service contract and is not part of M6.

### Eligibility, Assignment, And Timer

The expedition system unlock remains after Floor III completion and the permanent four-Drifter roster. The target list is derived from existing floor-clear state:

| Destination | Eligible when |
| --- | --- |
| Floor I | `floor_one_cleared` is true |
| Floor II | `floor_two_cleared` is true |
| Floor III | `floor_three_cleared` is true |
| A future floor | Its existing authoritative completion state is true |

Do not substitute route unlock, current cursor, boss-reward-pending, or a new M6 proof route for the authoritative clear flag.

At outing setup, the player chooses the active pair; the other two permanent Drifters are the expedition pair. Exactly one assignment may be launched per outing. Assignment membership is disjoint from the active pair, and assigned Drifters are unavailable for ordinary dungeon participation while the assignment is active. The active pair continues normal gameplay. The assignment is optional; an empty balance or no assignment must never block an outing.

The 20-minute real-elapsed-time clock begins only after confirmed launch. The assignment completes once elapsed time reaches 20 minutes. Repeated commands, waiting, rests, reloads, retries, or repeated event submissions cannot create another completion or reset the start time. There is no encounter-count progress and no artificial wait requirement in ordinary dungeon play.

### Passive Assignment Experience

Before launch, the player selects the expedition pair (the complement of the active dungeon pair), an eligible completed-floor destination, and one available assignment category, then confirms. Confirmation is the last required expedition interaction until the Hub report is claimed. While it runs, show only the assignment's basic information and remaining time/completed status. Do not simulate battles, encounters, exploration, maps, or combat animations; require equipment setup or inventory management; expose expedition AI, turns, or player-controlled actions; or generate intermediate events. The destination and category select the deterministic floor-eligible reward contract; they do not start a simulated expedition. The active dungeon pair continues normal gameplay independently.

If the outing ends before 20 minutes, the assignment is incomplete: its energy remains spent, it awards no category reward or expedition XP, and both Drifters return to the permanent roster. A completed assignment remains completed across reload and is evaluated at outing termination.

### Expedition XP

The initial balancing target is 20% of the outing's secured dungeon XP pool for the expedition pair collectively. It is supplemental XP, not a transfer from the active pair and not a per-Drifter 20% award.

Order:

```text
existing replay / extraction / talisman / boss / death rules
-> determine the secured base dungeon XP pool
-> calculate the expedition pool at 20%
-> split that pool between the two expedition Drifters
-> apply each recipient's M3 Intuition bonus to their own base share
-> floor each individual Intuition bonus using the existing M3 curve
```

Use `secured_xp_bonus_bps_from_intuition()` and the same per-recipient bonus order as M3. Do not apply one Drifter's Intuition to the other or reapply the bonus on reload/retry. A completed assignment with zero secured dungeon XP grants zero expedition XP. An incomplete assignment grants none.

Approved integer rule: `expedition_pool = floor(secured_base_pool * 20 / 100)`. Split with `divmod(pool, 2)`; if one point remains, give it to the first expedition participant in permanent roster order. Thus 100 -> pool 20 -> 10/10; 125 -> pool 25 -> 13/12; 200 -> pool 40 -> 20/20. These are base shares before each recipient's M3 Intuition bonus. The 20% figure remains a balance target to validate against M3 level thresholds and real run XP; the rounding and remainder convention are final.

## Decision Register

| Decision | Recorded M6 direction |
| --- | --- |
| M6-D1: Energy | Revised values and limits in this plan are approved. |
| M6-D2: Eligibility/progress | Completed-floor targets and the confirmed-launch 20-minute timer are approved; no Floor IV proof route. |
| M6-D3: Expedition XP | Collective 20% target and individual M3 Intuition ordering are approved; the 20% is balance-tested before closure. |
| M6-D4: Settlement | Outing-end settlement, death/early-termination treatment, pending Hub reports, and exactly-once claim are approved. |
| M6-D5: Initial content | Four categories and floor eligibility restrictions are approved. Training and Material are the initial available categories; Equipment and Recovery stay unavailable on floors without an eligible authored source. Material rewards are exactly one grade-appropriate metal on Floors I-III. |
| M6-D6: Outstanding-assignment full-party events | Deferred to M8; the explicit M6 Floor III outing restriction below preserves the existing four-member boss contract. |

### Settlement And Claims

At outing termination, reunite the full permanent roster and evaluate the assignment exactly once. Freeze an immutable report/outcome before it can be claimed. A completed assignment retains eligible category rewards even if the active pair dies; the active pair's dungeon XP still follows the existing secured-XP rules. An incomplete assignment has no category reward or expedition XP. Energy is never refunded.

Reports remain claimable at the Hub until claimed. Claiming grants the frozen reward to the recorded expedition participants and marks that report claimed as one atomic operation. Save/load, retries, and repeated claims cannot duplicate XP, items, equipment, or claim state. A failed required write cannot leave rewards granted without the claim or a claim recorded without its rewards.

Existing extraction, death, replay, talisman, boss settlement, secured equipment, and carried-supply semantics are unchanged. M6-D6, future full-party events while an expedition remains outstanding, is deferred to M8. The existing Floor III boss is handled by the approved M6-specific assignment restriction below.

### Initial Categories And Floor-Grounded Rewards

M6 retains only these categories:

1. **Training:** Expedition XP as defined above.
2. **Material:** A fixed, deterministic reward drawn only from the selected completed floor's eligible authored materials/reward sources.
3. **Equipment:** Only eligible M5 armor/equipment instances actually available through that floor's authored content.
4. **Recovery:** Only M2 carryable supplies actually available through that floor's authored content.

No expedition-exclusive items, complications/injuries, procedural jewelry, stackable signature parts, or rewards beyond the selected floor's eligibility. Do not roll an outcome again on reload. A future floor's content cannot be inferred from its numeric floor rarity policy alone.

| Destination | Authored ordinary reward evidence at Gate 0 | Available Material assignment reward | Equipment assignment | Recovery assignment |
| --- | --- | --- | --- | --- |
| Floor I | Route enemies drop `goblin_scrap`; the Goblin Lord also drops `goblin_lord_core`. Existing dismantle definitions turn these into Grade-I materials. | Exactly 1 Grade-I metal per completed Material assignment; the material is legitimately obtainable by dismantling Floor-I Goblin Scrap. | Unavailable: no eligible live floor source. Display the unavailable reason; do not offer a no-op. |
| Floor II | Tier-I route enemies retain Goblin Scrap drops and have authored Grade-II drops: metal/timber/fiber at 2,000 bps per eligible enemy and cores at 1,000 bps. The boss also has authored scrap/core drops. | Exactly 1 Grade-II metal per completed Material assignment; Grade-II metal is an authored eligible route drop. | Unavailable: no eligible live floor source. Display the unavailable reason; do not offer a no-op. |
| Floor III | Tier-II route enemies retain Goblin Scrap drops and have authored Grade-III drops: metal/timber/fiber at 2,000 bps per eligible enemy and cores at 1,000 bps. The boss also has authored scrap/core drops. | Exactly 1 Grade-III metal per completed Material assignment; Grade-III metal is an authored eligible route drop. | Unavailable: no eligible live floor source. Display the unavailable reason; do not offer a no-op. |
| Future floor | Re-audit that floor's route and actual reward definitions when it is authored and cleared. | One fixed material reward only after its source and amount are reviewed; never infer a grade or item from floor number alone. | Unavailable unless that floor has a legitimate eligible M5 equipment source. | Unavailable unless that floor has a legitimate eligible M2 carryable source. |

The one-unit Material outputs are approved initial M6 values and must use existing item/material ownership rules. Equipment and Recovery are not offered for Floors I-III until M8 supplies a legitimate eligible source; missing categories do not block M6 completion. No placeholder rewards, new drop rolls, rarity upgrades, or expedition-exclusive items are allowed. Scouting, Story, Elite, and pair-specific outcome content remain deferred to M8.

## Gate 0 Repository Audit

Audit performed against `dungeon` baseline `c64332d0fe9aeac5811f6eb27f0edea836ff7451`.

| Boundary | Actual seam and finding |
| --- | --- |
| Floor completion | `PartyState` already owns `floor_one_cleared`, `floor_two_cleared`, and `floor_three_cleared`; boss completion sets each flag, snapshots persist it, and save validation enforces prerequisite order. These are the M6 eligibility authorities. |
| Roster/deployment | `GameState.recruited_members` is permanent roster order (player followed by companions); `PartyState.active_drifter_ids` identifies the active pair. The complement can be derived without storing duplicate Drifter state. The M4 Floor II helper is a fresh temporary `PlayerState`, not the recruited member, and does not mutate that member's saved progression. The approved M6 exception permits this proxy even if the represented D3/D4 is assigned; it grants no XP/progression and does not affect assignment state. The Floor III boss uses all four permanent Drifters, so M6 forbids an assignment from coexisting with a Floor III outing. |
| XP | `PartyState.secured_xp_awards()` applies each member's M3 Intuition curve after floor division. It currently drops split remainders, so M6 must preserve the 20% pool with its approved two-person remainder rule rather than blindly reuse that split. `root/src/app/player/scaling.py` owns the curve. |
| Dungeon rewards | `RunEventService` owns replay-safe Floor II/III reward events and drop tables; Floor I uses its existing direct reward path. Route tables are in `root/src/app/content/routes/floor_one/route.py`, `floor_two/route.py`, and `floor_three/route.py`; drops are authored in `root/src/app/content/enemies/`. |
| M2 supplies | `root/src/app/content/hub_economy.py` defines carryables and Alchemy, but the current Floor I-III enemy/route reward tables do not drop healing potions, smoke bombs, or return talismans. |
| M5 equipment | `ArmorGenerationService` supports floor rarity policies, but policies do not author reward availability. `RunEventService.resolve_armor_reward()` is Floor-II-specific and no ordinary route invokes it. M5 explicitly records that no live Floor II armor reward source exists. No Floor I/III live armor sources were found either. |
| Persistence | Runtime snapshot and disk save schema are both 23. `save_document.py` owns canonical validation/migration; profile persistence retains immutable revision history. M6 persistent energy/time/assignment/report state will require a reviewed save-contract/migration change, but no new schema number or shape is chosen in this planning pass. |
| Clock/runtime | Persistence already creates and validates timezone-aware UTC timestamps (`SaveCoordinator`/`envelope.py`); no gameplay elapsed-time service or persisted gameplay timer exists. The actual pinned MicroPython probe must verify the chosen UTC parsing/arithmetic path and heap impact. |
| Clients/tests | Semantic gameplay is owned in shared Python session/presenter boundaries; terminal/browser clients project legal actions. Relevant existing suites include party state, Floor I/II/III sessions and run events, save-document/migration, presenter, browser smoke, profile service and pinned runtime probes. |

### Gate 0 Decisions Closed

All six product decisions below are approved and final for M6 planning. M6-D1 through M6-D5 remain unchanged; this record closes the five previously open review items and the energy-overflow assumption without authorizing implementation.

1. **Equipment and Recovery:** these categories remain unavailable for any floor without an eligible, authored reward source. Show why each is unavailable; do not offer a no-op assignment, invent a source, or add placeholder rewards. Training and Material are the initially available categories. Enabling Equipment or Recovery later requires legitimate floor content, owned by M8, and does not block M6 closure.
2. **Floor II helper proxy:** preserve M4's helper selection and eligibility rules. The independently constructed temporary D3/D4 proxy may represent a Drifter assigned to an expedition for this authored Floor II boss only. It cannot read or mutate the permanent Drifter's saved investment, grant XP or progression, change expedition membership, or interrupt the assignment. Preserve the existing Floor II D3+D4 replay restriction. This is not permission to deploy expedition participants in ordinary encounters.
3. **Floor III coexistence:** an assignment cannot launch alongside an active Floor III outing, and an active assignment cannot coexist with a Floor III outing through a launch-order path. Reject either conflicting transition before mutation. Ordinary Floor III play and the four-permanent-Drifter boss remain unchanged. Floor III remains a legal expedition destination during a compatible Floor I or Floor II outing. Energy never blocks ordinary Floor III play. M6-D6 full-party events remain deferred to M8.
4. **XP rounding:** calculate `expedition_pool = floor(secured_base_xp * 20 / 100)`, split the integer pool across the pair, award an odd remainder to the first expedition participant in permanent roster order, then apply each recipient's own existing M3 Intuition bonus and rounding. The examples above are base shares before Intuition.
5. **Material quantities:** each completed Material assignment grants exactly one grade-appropriate metal: Grade I for Floor I, Grade II for Floor II, and Grade III for Floor III. Use only the corresponding floor's existing legitimate source and normal ownership path; add no extra rolls, quantity, rarity changes, or expedition-exclusive items.
6. **Energy overflow:** capacity remains 100 and overflow is discarded. Time at capacity creates no hidden regeneration credit; spending energy while full rebases the UTC regeneration anchor to the spend time, so it does not immediately refill. Normal one-energy-per-nine-minutes regeneration resumes from that point. Preserve offline regeneration, rollback protection, and the 100 cap.

### Gate 0 Technical Handoff

The repository audit found no demonstrated blocker to implementing the approved contract. It did confirm that M6 needs new shared-domain energy/timer/assignment ownership, persisted UTC evidence, save migration and strict current-schema validation, report/claim idempotency, and matching terminal/browser projections. No API, schema number, or storage shape is selected here; those belong to the implementation gates after their detailed contract review. The local-device UTC limitation is documented above and is accepted by the approved offline-clock model; this is not server-authoritative tamper protection.

The audit exercised the relevant existing regression boundaries without changing source: 215 focused tests passed across roster/floor state, Floor II helper and run behavior, Floor III, save/migration, route/drop content, and local profile persistence. This is baseline evidence, not M6 implementation or runtime qualification. The pinned MicroPython v1.29.0 executable was not available in this workspace, so its runtime/heap qualification remains outstanding; it is not a demonstrated blocker to implementing the approved contracts. The pinned probe and cumulative hosted qualification remain required for M6 closure.

**Gate 0 outcome:** product decisions and technical seams are recorded; no further product approval is required for these holds. The plan is implementation-ready, but gameplay implementation requires separate authorization.

## Revised Milestones And Acceptance

### Gate 0 - Product And Repository Contract

- [x] Record the approved energy/overflow model, completed-floor eligibility, passive 20-minute assignment, 20% collective XP target and integer split, outing-end settlement, and four-category scope.
- [x] Audit floor flags, party and XP owners, reward sources, save schema, clock/runtime seam, and current qualification boundaries.
- [x] Close Equipment/Recovery availability, Floor II helper proxy, Floor III outing coexistence, XP rounding, Material quantities, and energy overflow according to the approved contracts above.

**Acceptance:** all Gate 0 product holds are closed; implementation seams and migration/runtime obligations are identified without inventing APIs or schemas. No Floor IV route or encounter-count proof is required.

### Gate 1 - Eligibility, Energy, And Durable Launch

- [ ] Add focused tests for every completed-floor flag, incomplete floors, future unknown floors, four permanent recruits, all six active pairs, disjoint complement, and the existing Floor II D3/D4 replay restriction.
- [ ] Test 100 initial/capacity, 10 launch debit for available categories, atomic rejection/failure, pre-confirm cancellation, no refund, nine-minute regeneration units, offline cap, repeated refresh, full-cap overflow with time discarded, anchor rebasing when spending at full capacity, resumed regeneration from that point, and backwards UTC time.
- [ ] Review and implement the required current/legacy save migration and malformed-state validation only after the state contract is approved. Preserve historical snapshots, immutable remote revisions, and forward incompatibility rejection.
- [ ] Prove energy never changes legal dungeon-entry/combat/extraction offers.

**Acceptance:** exactly one confirmed launch charges once and persists its roster, floor, assignment type, and time evidence; invalid or failed launch leaves no partial mutation.

### Gate 2 - Twenty-Minute Assignment Lifecycle

- [ ] With an injected deterministic test clock, prove pre-boundary incomplete and exact/after-20-minute completion, including save/reload, retry, clock rollback, and repeated command delivery.
- [ ] Prove assignment completion is time-derived and exactly once; waiting/resting/encounter repetition cannot manufacture progress or completion.
- [ ] Cover incomplete early outing termination with spent energy, no reward, and returned Drifters; no artificial wait is inserted into ordinary routes.
- [ ] Preserve M4's Floor II helper selection/eligibility and replay restrictions while allowing the separately constructed proxy to represent an expedition-assigned D3/D4; prove no persistent-state mutation, XP/progression grant, or assignment change. Reject assignment launch during a Floor III outing and reject starting/entering a Floor III outing while an assignment is active. Keep ordinary Floor III play and Floor III destinations from compatible Floor I/II outings available.

**Acceptance:** persisted elapsed time cannot reset, advance from client input, or complete twice; ordinary gameplay remains playable without an assignment.

### Gate 3 - Rewards, XP, Settlement, And Claims

- [ ] Initially offer only Training and Material. Show Equipment/Recovery as unavailable with an explanation for floors lacking eligible authored sources; do not offer no-op assignments. Implement the exact one-metal-per-floor rows and validate each against that floor's existing source and normal ownership path.
- [ ] Test the 20% secured base pool for zero, replay, extraction, talisman, death, boss, and ordinary termination. Test percentage rounding, odd split remainder, participant order, individual M3 Intuition bonuses, and no reload/retry duplication.
- [ ] Test completed assignment report retention after active-pair death, incomplete assignment zero rewards, zero secured XP, settlement once, Hub claim once, failure injection, reload, and duplicate claim.
- [ ] Ensure gear/supplies grant through the existing M5/M2 ownership and acquisition boundaries; no synthetic signatures or procedurally generated jewelry.

**Acceptance:** termination freezes a single outcome; one atomic Hub claim grants the recorded reward to the recorded expedition pair exactly once.

### Gate 4 - Terminal/Browser Player Journey

- [ ] Prove selection, disabled/unavailable reasons, confirmation/cancel, status-only assignment display with remaining/completed timer, ordinary dungeon play with no energy, reunion, report and claim in terminal and browser. Prove there is no expedition simulation, map, battle, intermediate event, or post-launch player action.
- [ ] Use test-controlled time; browser UI never authors elapsed time, reward outcomes, or progress.
- [ ] Qualify all six active pairs on routes compatible with unchanged M4 boss requirements; test target eligibility separately for Floors I-III. Prove the Floor II helper-proxy exception and both directions of the Floor III assignment/outings exclusion without blocking ordinary Floor III play or Floor III as a destination from a compatible outing.
- [ ] Prove launch-save-reload, outing termination-save-reload, report-claim-save-reload, and failed-write recovery.

**Acceptance:** terminal and browser expose the same legal semantic actions and cannot diverge on energy, timing, reward source, or claim state.

### Gate 5 - Runtime And Cumulative Qualification

- [ ] Extend and run the exact pinned MicroPython probe for UTC anchor handling, regen, launch, timer boundary, settlement, claim, snapshot/reconstruction, and no-energy dungeon play.
- [ ] Run root pytest, web tests, authored-content validation, compile/build, browser smoke, PostgreSQL profile-service tests, migration-from-zero, Alembic model parity, and exact-SHA hosted CI.
- [ ] Re-run any save-schema history, immutable remote revision, and concurrency checks affected by M6; preserve the M4/M5/M3 regression journeys.
- [ ] Record exact source SHA, hosted run, local pinned executable identity/results, balance observations, and explicit M8 handoff.

**Acceptance:** all relevant local and hosted qualification is green on the exact reviewed SHA; no test count or documentation claim substitutes for an unrun runtime boundary.

## Qualification Matrix

| Layer | Required M6 evidence |
| --- | --- |
| Unit/domain | Energy arithmetic/cap/clock rollback; target-floor eligibility; pair complement; 20% XP integer distribution and M3 bonus; timer boundary; incomplete/complete transitions |
| Contract/persistence | Current and historical save validation/migration; canonical snapshots; assignment/report claim idempotency; failed-write atomicity; immutable remote revisions |
| Flow | Active pair outing plus assignment; extraction/talisman/death/boss settlement; exactly-once Hub claim; no-energy dungeon run |
| Browser/terminal | Same offered semantic actions; selection/cancel/confirm; timer projection; save/reload; claim; no client-authored clock/reward |
| Service/qualification | PostgreSQL profile/migration/concurrency suite where save contract touches service; migration from zero; Alembic parity; exact-SHA hosted workflow |
| Runtime | Pinned MicroPython v1.29.0 parity and repeat stability with time parsing/arithmetic and new persisted state; never infer from CPython alone |

## Explicit Deferrals

- Floor IV proof routes, three-encounter completion rules, and all encounter-count expedition progress.
- Scouting, Story, Elite, complications/injuries, pair-specific outcomes, and their consumers (M8).
- Full-party events with an outstanding expedition (M6-D6, M8). This deferral does not override the explicit M6 Floor III outing restriction.
- Paid refills, earned refill items, capacity upgrades, monetization, and commercial services (M9 or later).
- Equipment and Recovery reward sources for M6 (M8); no placeholder source, and no reward may exceed selected-floor eligibility. Future-floor Material rewards also require a later floor-specific review.
- `docs/future/longterm.md`, `exe/`, and unrelated cleanup.

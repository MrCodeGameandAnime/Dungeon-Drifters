# M6 Expeditions And The Two-Plus-Two Loop

> Planning only. This revision records the approved M6 product corrections and the Gate 0 repository audit. It does not authorize gameplay implementation.

**Baseline:** `158b38e344d77ef5c78b07c91b5cad211b035466` (`dungeon`)
**Status:** M4B closed; M6 planning correction under review, 2026-11-10.
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
| Launch cost | 10 energy for each of the four initial assignment categories |
| Regeneration | 1 energy per 9 elapsed minutes (10 per 90 minutes) |
| Offline time | Counts, capped at 100 energy |
| Clock anchor | Persist UTC; a backward clock reading grants no energy and must not move the accepted anchor backward |
| Payment | Deduct atomically when the player confirms launch |
| Cancel/refund | Cancel before confirmation costs nothing; no refund after confirmation |
| Refills | No paid refills or separate earned-refill mechanic in M6 |
| Scope | Energy gates expedition launch only; it never gates dungeon entry, combat, extraction, or progression |

Operational interpretation for review: energy overflow while already at capacity is discarded rather than banked for later, so time spent full cannot create an instant refill after spending. This preserves the stated cap and requires an explicit boundary test.

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

Integer rule proposed for review: `expedition_pool = floor(secured_base_pool * 20 / 100)`. Split with `divmod(pool, 2)`; if one point remains, give it to the first expedition participant in permanent roster order. Thus 100 -> pool 20 -> 10/10; 125 -> pool 25 -> 13/12; 200 -> pool 40 -> 20/20. This convention preserves the full rounded expedition pool rather than dropping a split remainder. The 20% figure remains a balancing target until evaluated against M3 level thresholds and real run XP.

## Decision Register

| Decision | Recorded M6 direction |
| --- | --- |
| M6-D1: Energy | Revised values and limits in this plan are approved. |
| M6-D2: Eligibility/progress | Completed-floor targets and the confirmed-launch 20-minute timer are approved; no Floor IV proof route. |
| M6-D3: Expedition XP | Collective 20% target and individual M3 Intuition ordering are approved; the 20% is balance-tested before closure. |
| M6-D4: Settlement | Outing-end settlement, death/early-termination treatment, pending Hub reports, and exactly-once claim are approved. |
| M6-D5: Initial content | Four categories and floor eligibility restrictions are approved; source availability and fixed initial Material outputs are recorded in the review holds. |
| M6-D6: Outstanding-assignment full-party events | Deferred to M8; M6 cannot silently violate the existing Floor III four-member boss contract. |

### Settlement And Claims

At outing termination, reunite the full permanent roster and evaluate the assignment exactly once. Freeze an immutable report/outcome before it can be claimed. A completed assignment retains eligible category rewards even if the active pair dies; the active pair's dungeon XP still follows the existing secured-XP rules. An incomplete assignment has no category reward or expedition XP. Energy is never refunded.

Reports remain claimable at the Hub until claimed. Claiming grants the frozen reward to the recorded expedition participants and marks that report claimed as one atomic operation. Save/load, retries, and repeated claims cannot duplicate XP, items, equipment, or claim state. A failed required write cannot leave rewards granted without the claim or a claim recorded without its rewards.

Existing extraction, death, replay, talisman, boss settlement, secured equipment, and carried-supply semantics are unchanged. M6-D6, full-party events while an expedition remains outstanding, is deferred to M8; see the Gate 0 review hold below because the existing Floor III boss requires all four permanent Drifters.

### Initial Categories And Floor-Grounded Rewards

M6 retains only these categories:

1. **Training:** Expedition XP as defined above.
2. **Material:** A fixed, deterministic reward drawn only from the selected completed floor's eligible authored materials/reward sources.
3. **Equipment:** Only eligible M5 armor/equipment instances actually available through that floor's authored content.
4. **Recovery:** Only M2 carryable supplies actually available through that floor's authored content.

No expedition-exclusive items, complications/injuries, procedural jewelry, stackable signature parts, or rewards beyond the selected floor's eligibility. Do not roll an outcome again on reload. A future floor's content cannot be inferred from its numeric floor rarity policy alone.

| Destination | Authored ordinary reward evidence at Gate 0 | Eligible material candidates | Equipment | Recovery supplies |
| --- | --- | --- | --- | --- |
| Floor I | Route enemies drop `goblin_scrap`; the Goblin Lord also drops `goblin_lord_core`. Existing dismantle definitions turn these into Grade-I materials. | Grade-I metal/fiber/timber from Goblin Scrap; Grade-I cores from Goblin Lord Core. Conservative fixed-output proposal: 1 Grade-I metal per completed Material assignment. | None currently authored as a live floor reward source. | None of the M2 carryable items currently drops from this floor's route content. |
| Floor II | Tier-I route enemies retain the Goblin Scrap drops and have authored Grade-II drops: metal/timber/fiber at 2,000 bps per eligible enemy and cores at 1,000 bps. The boss also has the authored scrap/core drops. | Grade-II metal/fiber/timber/cores, plus dismantle outputs from actual scrap/core rewards. Conservative fixed-output proposal: 1 Grade-II metal per completed Material assignment. | No ordinary Floor II armor source is wired. M5 explicitly leaves live armor placement deferred. | No M2 carryable item currently drops from the Floor II route. |
| Floor III | Tier-II route enemies retain Goblin Scrap drops and have authored Grade-III drops: metal/timber/fiber at 2,000 bps per eligible enemy and cores at 1,000 bps. The boss also has the authored scrap/core drops. | Grade-III metal/fiber/timber/cores, plus dismantle outputs from actual scrap/core rewards. Conservative fixed-output proposal: 1 Grade-III metal per completed Material assignment. | No live Floor III armor source is authored; the M5 rarity policy is not itself a floor reward source. | No M2 carryable item currently drops from the Floor III route. |
| Future floor | Re-audit that floor's route and actual reward definitions when it is authored and cleared. | Only the floor's authored, obtainable materials; never infer a grade or item from floor number alone. | Only if a live authored source and M5 grant path exist. | Only if an M2 carryable is authored as obtainable through that floor. |

The one-unit Material amounts are conservative planning proposals, not a reason to invent missing sources. At this baseline Equipment and Recovery have no eligible live floor outcomes on Floors I-III. The plan must not offer a no-op or fabricate rewards. Review must decide whether these category/floor combinations remain unavailable until real sources are authored, or whether a separate content change is authorized. Scouting, Story, Elite, and pair-specific outcome content remain deferred to M8.

## Gate 0 Repository Audit

Audit performed against clean `dungeon` baseline `158b38e344d77ef5c78b07c91b5cad211b035466`.

| Boundary | Actual seam and finding |
| --- | --- |
| Floor completion | `PartyState` already owns `floor_one_cleared`, `floor_two_cleared`, and `floor_three_cleared`; boss completion sets each flag, snapshots persist it, and save validation enforces prerequisite order. These are the M6 eligibility authorities. |
| Roster/deployment | `GameState.recruited_members` is permanent roster order (player followed by companions); `PartyState.active_drifter_ids` identifies the active pair. The complement can be derived without storing duplicate Drifter state. The M4 Floor II helper is a fresh temporary `PlayerState`, not the recruited member, and does not mutate that member's saved progression. However, it represents a D3/D4 identity that may be assigned to an expedition; whether that special helper is an explicit exception to M6 unavailability remains for review. The Floor III boss uses all four permanent Drifters. |
| XP | `PartyState.secured_xp_awards()` applies each member's M3 Intuition curve after floor division. It currently drops split remainders, so M6 must preserve the 20% pool with its explicit two-person remainder rule rather than blindly reuse that split. `root/src/app/player/scaling.py` owns the curve. |
| Dungeon rewards | `RunEventService` owns replay-safe Floor II/III reward events and drop tables; Floor I uses its existing direct reward path. Route tables are in `root/src/app/content/routes/floor_one/route.py`, `floor_two/route.py`, and `floor_three/route.py`; drops are authored in `root/src/app/content/enemies/`. |
| M2 supplies | `root/src/app/content/hub_economy.py` defines carryables and Alchemy, but the current Floor I-III enemy/route reward tables do not drop healing potions, smoke bombs, or return talismans. |
| M5 equipment | `ArmorGenerationService` supports floor rarity policies, but policies do not author reward availability. `RunEventService.resolve_armor_reward()` is Floor-II-specific and no ordinary route invokes it. M5 explicitly records that no live Floor II armor reward source exists. No Floor I/III live armor sources were found either. |
| Persistence | Runtime snapshot and disk save schema are both 23. `save_document.py` owns canonical validation/migration; profile persistence retains immutable revision history. M6 persistent energy/time/assignment/report state will require a reviewed save-contract/migration change, but no new schema number or shape is chosen in this planning pass. |
| Clock/runtime | Persistence already creates and validates timezone-aware UTC timestamps (`SaveCoordinator`/`envelope.py`); no gameplay elapsed-time service or persisted gameplay timer exists. The actual pinned MicroPython probe must verify the chosen UTC parsing/arithmetic path and heap impact. |
| Clients/tests | Semantic gameplay is owned in shared Python session/presenter boundaries; terminal/browser clients project legal actions. Relevant existing suites include party state, Floor I/II/III sessions and run events, save-document/migration, presenter, browser smoke, profile service and pinned runtime probes. |

### Gate 0 Review Holds

1. **Equipment and Recovery availability:** the four approved categories include Equipment and Recovery, but actual Floor I-III reward content currently provides neither M5 gear nor M2 carryable supplies. The no-invention rule prevents filling those cells. Review whether those combinations stay unavailable pending authored sources, or whether a distinct floor-content update is allowed. No new item or source is authored by this planning correction.
2. **Floor II temporary-helper overlap:** on a Floor II outing, the two non-active Drifters are the expedition pair, while the M4 boss requires a temporary helper represented by D3 or D4. That helper is a fresh no-XP state and cannot mutate the assigned Drifter's saved progression, but it still represents the same identity. Decide whether this authored boss-only proxy is permitted while that identity is assigned, or whether assignment launch must be unavailable for an active Floor II outing. Do not weaken the M4 boss requirement, use the assigned Drifter's persistent state, or change assignment membership mid-run.
3. **Floor III full-party boundary:** an outstanding expedition pair cannot be unavailable and simultaneously participate as the four permanent Drifters in a Floor III boss. Proposed M6 guard: ordinary Floor III outings remain fully playable, but an assignment cannot be launched alongside an outing whose active route is Floor III. A Floor III expedition destination may still be selected while the active route is compatible. Keep M6-D6 (future full-party events with an outstanding assignment) deferred to M8. Review this guard before implementation; do not weaken M4 boss requirements.
4. **XP integer convention:** review the stated floor-20%-then-roster-order remainder rule. It matches the provided 125 -> 25 -> 13/12 example and preserves the full rounded pool.
5. **Material amounts:** review the proposed one-unit fixed Grade-I/II/III metal outcomes against the demonstrated route drop economy. They are deterministic and source-grounded, but remain tunable before implementation.

Until these holds are reviewed, this is a complete source audit and revised planning draft, not implementation-ready Gate 0 approval.

## Revised Milestones And Acceptance

### Gate 0 - Product And Repository Contract

- [x] Record the approved 100-energy/20-minute model, completed-floor eligibility, 20% collective XP target, outing-end settlement, and four-category restriction.
- [x] Audit floor flags, party and XP owners, reward sources, save schema, clock/runtime seam, and current qualification boundaries.
- [ ] Review the five holds above, including the Floor II temporary-helper overlap and proposed Floor III assignment-launch guard. No implementation begins before this review.
- [ ] Confirm actual fixed reward rows/amounts without inventing an unavailable source.

**Acceptance:** no unresolved product/source boundary is delegated to client code or handled by a silent fallback. No Floor IV route or encounter-count proof is required.

### Gate 1 - Eligibility, Energy, And Durable Launch

- [ ] Add focused tests for every completed-floor flag, incomplete floors, future unknown floors, four permanent recruits, all six active pairs, disjoint complement, and the existing Floor II D3/D4 replay restriction.
- [ ] Test 100 initial/capacity, 10 launch debit, atomic rejection/failure, pre-confirm cancellation, no refund, nine-minute regeneration units, offline cap, repeated refresh, full-cap overflow, and backwards UTC time.
- [ ] Review and implement the required current/legacy save migration and malformed-state validation only after the state contract is approved. Preserve historical snapshots, immutable remote revisions, and forward incompatibility rejection.
- [ ] Prove energy never changes legal dungeon-entry/combat/extraction offers.

**Acceptance:** exactly one confirmed launch charges once and persists its roster, floor, assignment type, and time evidence; invalid or failed launch leaves no partial mutation.

### Gate 2 - Twenty-Minute Assignment Lifecycle

- [ ] With an injected deterministic test clock, prove pre-boundary incomplete and exact/after-20-minute completion, including save/reload, retry, clock rollback, and repeated command delivery.
- [ ] Prove assignment completion is time-derived and exactly once; waiting/resting/encounter repetition cannot manufacture progress or completion.
- [ ] Cover incomplete early outing termination with spent energy, no reward, and returned Drifters; no artificial wait is inserted into ordinary routes.
- [ ] Enforce the reviewed M4 boss-boundary rules. Keep ordinary Floor III outings playable; if the proposed Floor III launch guard is approved, reject assignment launch alongside that active route while still allowing Floor III as a destination from a compatible outing. For Floor II, either test the approved boss-only helper-proxy exception for zero saved-state mutation/XP, or enforce the reviewed pre-launch assignment restriction. Never change assignment membership mid-run or weaken M4 boss participation.

**Acceptance:** persisted elapsed time cannot reset, advance from client input, or complete twice; ordinary gameplay remains playable without an assignment.

### Gate 3 - Rewards, XP, Settlement, And Claims

- [ ] Implement only reviewed fixed category/source rows. Validate every item ID against the selected floor's eligible authored content; reject or hide unavailable category/floor pairs.
- [ ] Test the 20% secured base pool for zero, replay, extraction, talisman, death, boss, and ordinary termination. Test percentage rounding, odd split remainder, participant order, individual M3 Intuition bonuses, and no reload/retry duplication.
- [ ] Test completed assignment report retention after active-pair death, incomplete assignment zero rewards, zero secured XP, settlement once, Hub claim once, failure injection, reload, and duplicate claim.
- [ ] Ensure gear/supplies grant through the existing M5/M2 ownership and acquisition boundaries; no synthetic signatures or procedurally generated jewelry.

**Acceptance:** termination freezes a single outcome; one atomic Hub claim grants the recorded reward to the recorded expedition pair exactly once.

### Gate 4 - Terminal/Browser Player Journey

- [ ] Prove selection, disabled/unavailable reasons, confirmation/cancel, visible energy and remaining/completed timer, ordinary dungeon play with no energy, reunion, report and claim in terminal and browser.
- [ ] Use test-controlled time; browser UI never authors elapsed time, reward outcomes, or progress.
- [ ] Qualify all six active pairs on routes compatible with unchanged M4 boss requirements; test target eligibility separately for Floors I-III. Prove the reviewed Floor II helper/assignment behavior, and prove the reviewed Floor III boss/assignment guard without blocking ordinary Floor III play or Floor III as a destination from a compatible outing.
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
- Full-party events with an outstanding expedition (M6-D6, M8), pending the M6 boundary review above.
- Paid refills, earned refill items, capacity upgrades, monetization, and commercial services (M9 or later).
- New floor loot/equipment/supply sources unless separately approved; no reward may exceed selected-floor eligibility.
- `docs/future/longterm.md`, `exe/`, and unrelated cleanup.

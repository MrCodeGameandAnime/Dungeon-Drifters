# M6 Expeditions And The Floor IV Two-Plus-Two Loop Implementation Plan

> Implementation method: use `superpowers:executing-plans` for native gate-by-gate execution. This plan does not authorize paid services or early roster unlocks.

**Status:** Draft for review, 2026-10-29. Contracts are semantic; exact modules/APIs and schemas must be revalidated after M5/M4B.

**Goal:** Make the reunited four-Drifter roster split into a dungeon pair and an event-progressed expedition pair on Floor IV, with launch energy, reduced XP and once-only reunion rewards.

**Architecture:** Persistent assignment/source/claim state belongs to the existing game, active IDs belong to roster/deployment state, and authored assignments define event requirements/rewards. Energy regeneration uses the approved host-clock policy; expedition completion uses accepted gameplay events, never a wall-clock countdown.

**Tech stack:** Existing Python runtime/content/RNG/save contracts, roster/trade/equipment services, semantic clients, pytest/Playwright, real PostgreSQL and pinned MicroPython qualification.

## Authority And Required Entry Evidence

- [Party design](../../future/party-and-expedition-core-loop.md), assignment, seven categories, reduced XP, reports, reunion and full-party events.
- [Economy](../../future/dungeon-progression-difficulty-and-economy.md), energy regeneration/costs, unlimited dungeon play and monetization boundaries.
- [Roadmap](../development-roadmap.md), M6 and fixed pacing; [M1](m1-permanent-roster.md), [M2](m2-preparation-trading-escape.md), [M3](m3-character-advancement.md), [M4B](m4-enemy-progression.md), [M5](m5-armor-accessories.md).

Entry requires accepted M4B evidence: D1 starts, D2 recruited on Floor I, D3 on Floor II, D4 on Floor III, and the first four-Drifter boss completed at the end of Floor III. Floor IV is the first expedition-enabled floor. Merely having four `PlayerState`s in a fixture or unlocking a menu does not satisfy this entry gate.

Non-goals: real-time expedition completion, restricting dungeon entry by energy, granting combat XP to the entire roster, new accounts/cloud architecture, paid refills, replacement signature weapons, or the full region/story content pass owned by M8.

## Current Baseline And Required Additions

At the inspected baseline, there is no expedition assignment model, energy ledger, event progress, report/claim lifecycle, or Floor IV route. The permanent roster/recruitment/four-party proof must arrive from earlier plans; do not assume current tutorial companions already satisfy it. Existing Story/World state, party shared resources, immutable content, exact-target progression, reward banking, equipment instance acquisition, saves and semantic presentation are the reuse points.

Re-audit actual post-M5 source before creating a module. Expected owners are `root/src/app/game/` for assignment orchestration, existing content/catalog for authored assignments, roster/party state for membership/shared rewards, and the established progression/equipment services for grants. Exact future class/function names are deliberately not frozen here.

## Fixed Contract And State Ownership

| Contract | Required behavior |
| --- | --- |
| Deployment | Two distinct available recruited IDs enter the dungeon; the remaining two may launch a legal assignment; no member is in both groups |
| Energy | Validated launch cost, bounded capacity and approved regeneration; atomic debit with launch; no energy required for ordinary dungeon play |
| Assignment | Stable assignment instance/content ID, participant IDs, necessary launch inputs, progress state, consumed-event/sequence evidence, outcome and claim state |
| Progress | Only selected accepted gameplay events count; redisplaying a node, repeated result submission, loading a save or waiting offline does not complete an assignment |
| Rewards | Authoritative once-only report/claim; reduced expedition XP to its pair only; actual materials/equipment/supplies through their existing grant owners |
| Return | Resolve under approved normal/death/early-extraction rules, reunite and allow rotation without losing identity/investment |

Do not store duplicate authoritative Drifter objects inside an assignment and overwrite the roster with them later. Persist only the launch inputs required to make modifiers/outcomes stable. Event evidence must distinguish legitimate replayed encounters in a new outing from duplicate delivery of the same outing's event; globally unique content node IDs alone are not enough.

Energy regeneration is a separate clock from assignment progress. Approve capacity, cost, regeneration rate/unit, persisted remainder/timestamp, offline cap, clock rollback/forward behavior, and host clock capability. Repeated refresh/reload cannot double-credit the same elapsed interval. Local offline saves are not made tamper-proof by a timestamp. Future paid grants require service authority and belong to M9's separately approved commercial work.

An empty energy balance leaves dungeon selection/entry playable; the other pair may remain idle. Insufficient energy rejects launch without charging or changing members. Do not force an assignment simply to permit a normal run. Full-party reunion encounters must not simultaneously keep those members assigned to an expedition; M8 uses the approved settlement/availability rule.

The source's 70-85% expedition XP is provisional and does not say whether active encounter XP is a pool or a per-member grant. Gate 0 must fix the basis, split, rounding, modifiers and treatment after death/early extraction. Reuse M3's secured-XP owner; do not apply Intuition twice or quietly give the active pair expedition XP. Explicitly author selected pair/character outcome modifiers, not every illustrative survival/injury example.

## Category And Content Delivery

1. Training and Material are the first real assignments, not empty category labels.
2. Equipment and Recovery follow using M5 instance/provenance and M2 supply consumers.
3. Scouting and Story require information/story consumers completed in M8; M6 defines validated outputs and controlled integration proofs, then M8 authors their actual release assignments and consumers.
4. Elite requires an approved risk/eligibility/reward definition and content from M8. Do not label it operational without that content.

M6 closure is the working assignment engine and first four categories with a minimal playable Floor IV loop; it must explicitly leave Scouting/Story/Elite release content to named M8 gates. M9 cannot count all seven delivered until those downstream consumers exist or their scope has an approved disposition.

The minimal Floor IV content proof uses ordinary gameplay to produce the selected events and return, not an artificial client progress button. Approve its finite route/exit rules and material access; Floor IV is the first legitimate Grade-IV source. M8 expands the region and remaining floor content. Source references to expedition "weapons" must resolve to approved signature-compatible material/recipe rewards or separately approved loot, never random replacements or stackable signature parts.

## Persistence, Failure, And Presentation

Migrate existing saves to no assignment and a deliberately approved initial energy balance, without retroactive elapsed-time grants or early unlocks. Store progression in the existing game save; account entitlements/credentials do not enter assignment state. Validate disjoint participant sets, recruited IDs, unlock conditions, content IDs, event/claim bounds, energy limits and compatible run phase before reconstruction.

Launch, event advancement and claim transitions must prepare/validate before mutation. Test failed required save writes at launch/return/claim, reconstruct fresh coordinators, and prove no double spend/grant/claim or lost already accepted report. Reward settlement must not bypass existing run no-rewind semantics. Keep immutable old cloud revisions/digests and explicit conflict resolution; no timestamp-winner merge of two expedition branches.

Terminal/browser show energy separately from assignment progress, selected participants, launch requirements/costs, earned report results, pending versus claimed status, blocked reasons and no-energy dungeon entry. The browser does not run a completion timer or choose rewards. Reports reflect actual saved outcomes, including any approved complications.

## Review Focus

- No energy must still permit ordinary dungeon entry; Gates 1/4 prove this through legal offers and live play.
- Offline elapsed time must not finish an expedition, nor refresh double-credit energy; Gate 2 tests both clocks separately.
- Duplicate event delivery must differ from a legitimate encounter replay in a new outing; Gate 2 tests event identity and persistence.
- Active/assigned sets must remain exclusive and exactly recruited; Gate 1 rejects overlaps and forged unlocks.
- Reopening a report after interrupted save/load must not grant rewards twice; Gate 3 injects failures and reconstructs the claim owner.

## Gates And Tests

### Gate 0 - Verify Floor III And Freeze Assignment Policies

- [ ] Verify live entry evidence for staged recruitment and the first four-Drifter boss. Revalidate owners/APIs from M1-M5; approve M6-D1 through D5 and the bounded Floor IV proof manifest.
- [ ] Specify finite assignment lifecycle transitions, event IDs/basis, cancellation, failure/early-return settlement, XP examples, energy clock examples and content grants.
- [ ] Approve simple editable initial values; do not treat commercial acceleration as necessary for gameplay.

Proof: no ambiguous outcome or unresolved clock behavior is delegated to client code.

### Gate 1 - Two-Plus-Two Selection And Atomic Launch

- [ ] Add red/green domain tests for exclusivity, unavailable/unrecruited/duplicate IDs, wrong floor/story gate, affordability and stale input. Test empty-energy dungeon entry and no assignment before Floor IV.
- [ ] Implement the persistent lifecycle and atomic launch debit; save/reload exact participant identity without cloning progression into assignment storage.
- [ ] Validate malformed assignment/participant/energy payloads at the trust boundary, including a full-party boss flag that lacks required recruitment/story evidence.

Proof: two legal groups, one launch charge, no early unlock, original roster investment intact.

### Gate 2 - Regeneration And Gameplay-Event Progress

- [ ] Use controlled clock/event fixtures for zero/partial/multiple regeneration intervals, capacity, repeated reads, offline bounds, backward/forward time, and reconstruction.
- [ ] Implement only the approved event consumers; test repeated notifications, encounter replay in another outing, Rest reinspection, save/load, ordinary waiting and event ordering.
- [ ] Persist necessary draw/outcome inputs once so reports cannot reroll on reload or after an inventory inspection.

Proof: clock time can regenerate energy but cannot finish the expedition; real accepted gameplay can progress it without a wall-clock wait.

### Gate 3 - Categories, XP, And Exactly-Once Reunion

- [ ] Author Training/Material first, then Equipment/Recovery through existing acquisition/XP/supply services. Validate eligible grade/floor/reward IDs and reduced XP/split rounding.
- [ ] Test normal return, early extraction, death, cancellation and incomplete assignment under approved policy. Failure after outcome preparation/commit must not grant twice or restore debited energy unexpectedly.
- [ ] Produce real report/claim state with participant-specific XP and shared resources; test fresh-load repeated claim and immutable remote history advancement. Document the Scouting/Story/Elite handoff to M8 explicitly.

Proof: completed assignment -> report -> claim -> reload -> already claimed, with exact quantities, instances, XP and roster state.

### Gate 4 - Floor IV Live Loop And Client Parity

- [ ] Terminal and built-browser journey: accepted Floor III clear -> Floor IV unlock -> select pair -> launch other pair -> play authored events -> return -> claim -> rotate -> repeat.
- [ ] Qualify all six active-pair combinations using the genuinely recruited four-member roster, including exact per-member skills/equipment/weapon/payload ownership and inactive-pair outcomes. Do not infer this from a two-member fixture.
- [ ] Show no-energy entry and report navigation on phone portrait/landscape and desktop. Confirm clients submit the same semantic launch/claim/event-producing gameplay actions, never client-authored progress.

Proof: the two-plus-two loop is a real playable run, not a simulated bridge result.

### Gate 5 - Runtime And Cumulative Closure

- [ ] Extend the real probe with split/launch/event/settlement/snapshot/teardown and no-energy play; run shared cumulative qualification and exact-SHA hosted checks.
- [ ] Record lifecycle/clock policy and the downstream content ledger; obtain review before declaring M6 closed.

Closure: first four categories function, reduced XP and all-six-pair live play are proven, clock/event separation and claim durability hold, and ordinary gameplay never depends on energy or payment. M8 owns the named remaining category consumers/content, not unspecified extra engine work.

## Unresolved Product Decisions

| ID | Decision and blocking gate |
| --- | --- |
| M6-D1 | Capacity/cost/regeneration, offline clock policy, initial energy and earned refills; Gate 0 |
| M6-D2 | Qualifying gameplay events, counts, length, launch/cancellation and reward snapshot rules; Gate 0 |
| M6-D3 | XP basis/reduction/split/rounding and M3 modifier ordering; before Gate 3 |
| M6-D4 | Death/early-extraction/incomplete assignment settlement and claim timing; Gate 0 |
| M6-D5 | First pair modifiers/complications, Floor IV proof content and signature-compatible equipment rewards; before Gates 3/4 |
| M6-D6 | Late full-party event settlement/availability for an outstanding expedition; M8 entry |

Paid energy/capacity/reward products remain M9 decisions with service-owned authority; they are not M6 dependencies.

# M1 Permanent Roster And Hub Party Selection Implementation Plan

> Implementation method: use `superpowers:executing-plans` for native gate-by-gate execution. This document does not authorize implementation, delegation, commits, or publishing.

**Status:** Planning draft, 2026-10-29. Current-code plan based on `hub` at `8099b895`; revalidate at entry, including local documentation moves.

**Goal:** Separate permanent recruited Drifters from the deployed party without changing recruitment pacing or losing any existing character investment.

**Architecture:** Extend `GameState`, `PartyState`, and the existing session/presenter/save contracts. Retain one canonical `PlayerState` per recruited Drifter and identify participants by stable authored Drifter IDs, never by a temporary lead/companion slot.

**Tech stack:** Existing Python runtime, authored content catalog, semantic terminal inputs, Pyodide bridge, validated profile saves, pytest, Playwright, pinned MicroPython.

## Authority And Boundaries

- [Roadmap](development-roadmap.md), especially M0/M1, staged recruitment, and the shared implementation/qualification contract.
- [Party design](../../future/party-and-expedition-core-loop.md), roster, selection, restrictions, and reunion sections.
- [Economy](../../future/dungeon-progression-difficulty-and-economy.md), secured ownership and death; existing Hub/Floor I evidence in [probe record](../../probe.md).
- [Weapon contract](../weapons/signature-weapon-implementation.md), exact-target progression and craft-and-install.

Fixed pacing: D1 starts; D2 joins on Floor I for the existing 65 gold; D3 joins on Floor II; D4 joins on Floor III; Floor III ends with the first four-Drifter boss; expeditions begin on Floor IV. D1-D4 denote recruitment order, not fixed character names. Any canonical Drifter can be D1, and no event may recruit an already-owned identity.

Non-goals: granting all four now, authoring Floors II-IV, expeditions/energy, armor, new skill trees, new reward multipliers, or changing the current tutorial/boss formats. Supporting a four-member roster structurally is not proof that live four-person boss combat is qualified.

## Verified Baseline And Gap

`GameState.player_state` owns the starting Drifter. `PartyState.companions` embeds recruited `PlayerState`s, but `recruit_companion()` rejects a second companion, `start_floor_one_run()` requires exactly one companion, and `_validate_party_members()` assumes the tutorial pair. `GameState.clone()` copies the original player and companions separately.

`OverworldSession` currently assembles local participant tuples, and several presenter/service lookups form `(game.player_state,) + party.companions`. Character, Skills, Weapon, Equipment, and merchant views already carry exact target IDs. Those IDs must address the roster, while battles and rewards must address the deployed participants. `Battle(..., party=...)` accepts an ordered sequence of unique canonical `PlayerState`s, but current content/session qualification is the pair.

Runtime schema 11/disk 12 store the original player plus embedded companions, not a separately persisted active-ID selection. There is no general recruitment-event contract or Hub pair selector. These are the missing capabilities; existing XP, weapons, and saves are not replacements to build again.

## State And Interfaces

The following are proposed M1 interfaces, not claims that they already exist. Gate 0 confirms naming against the entry tree:

| Proposed boundary | Contract |
| --- | --- |
| `GameState.recruited_members` | Read-only tuple of canonical recruited `PlayerState`s, including the original starting Drifter once |
| `GameState.member_for_drifter_id(drifter_id)` | Returns that canonical member; rejects unknown/unrecruited IDs, with no lead fallback |
| `PartyState.active_drifter_ids` | Ordered deployed IDs; M1 supports a single starting Drifter and the approved ordinary active pair, distinct from the permanent roster; M4B extends the authored full-party encounter mode |
| `GameState.active_party_members` | Resolves active IDs through the roster; does not clone them into another authoritative party |
| `PartyState.select_active_pair(drifter_ids, *, recruited_ids)` | Validates two distinct recruited IDs and Hub eligibility before assigning; no mutation on rejection |

Recommended implementation representation: preserve the original player at the existing root boundary and generalize companions to the remaining recruited members, adding explicit active IDs. This is a minimal storage recommendation, not a decision that the original Drifter must always fight or remain the narrative speaker. Gate 0 must approve another representation if needed; do not persist both a roster copy and companion copies.

Recruitment needs an authored event identity, required floor/story condition, eligible candidate IDs, cost, and one-time completion evidence. The client submits an offered event/Drifter ID, not an arbitrary floor/cost/unlock flag. Reuse `StoryState` completed-event support where sufficient. Decide when later recruits become secured before connecting a dungeon event. M1 supplies the validated extension point and controlled fixtures, not production Floor II/III recruitment scenes.

Ordinary-run participants are fixed at deployment and remain the reward recipients through encounter completion, Rest saves, extraction, and death. Bench members receive no combat XP merely because they are recruited; expedition XP belongs to M6. Retain the tutorial's 50/50 split and existing Floor I payout arithmetic. M4B may introduce an explicit authored full-party encounter boundary for the Floor III boss; that is not permission for arbitrary mid-run swaps. Its participation/reward contract must preserve earlier pair-earned rewards rather than redivide them across a newly enlarged party. Full-party boss XP interpretation is a later entry decision, not M1 arithmetic.

## File And Client Work

Modify `root/src/app/game/game_state.py`, `party_state.py`, `overworld_session.py`, and `weapon_progression.py`; extend `root/src/app/ui/overworld_ui.py`, `terminal_overworld_ui.py`, and `root/src/app/presentation/overworld_models.py`/`overworld_presenter.py`. Inspect `root/src/app/player/inventory_action.py` for actor-owned item targeting. Prefer one shared roster lookup over repeating position-dependent tuples.

Add only the small authored recruitment definition module needed by Gate 0's representation; its filename and catalog integration are a design choice to record before coding. Extend existing content validation/scaffolding only if the event becomes a new content family. Do not create another world/session engine.

Extend `root/web/python/dd_bridge.py` and `root/web/play/js/pyd4.js` to project and submit semantic pair/target choices. The browser may hold temporary checkbox/selection presentation, never recruitment eligibility or authoritative membership. Terminal exposes the same confirm/back choices. Existing mobile single-view menus and desktop presentation remain usable; no visual redesign is required.

## Persistence And Failure Contract

Update `root/src/app/snapshot.py`, `persistence/save_document.py`, affected envelope/migration dispatch, and profile-service validation tests for deliberate forward versions determined at entry. An existing pair migrates to precisely those two recruited IDs with the original active order; a pre-Hub save stays single-member. Do not grant future recruits, recreate their inventories, reset slot progress/Tier V, or mutate historical schema-12 payloads in place.

Validate canonical IDs, uniqueness, active membership/order/size, event eligibility, participant consistency, and legal phase/cursor combinations at the payload boundary before reconstruction. Clone/load must preserve independent member objects between games and shared canonical identity within one game. Unknown content is an explicit load error, not an excuse to substitute Branoc.

Forged IDs, duplicate selection, insufficient recruitment funds, stale offers, non-Hub swaps, repeated recruitment events, and mismatched run participants cause zero partial mutation. A failed battle construction restores all participating battle checkpoints and party phase, not only the former lead. Keep local/cloud save isolation and Rest no-rewind safeguards.

## Review Focus

- A migrated pair must not gain D3/D4 or lose investment; Gate 3 checks old snapshots and current remote advancement.
- A benched member must remain targetable at the Hub without earning active battle XP; Gate 2 checks targets and participant-only rewards.
- Reordering active IDs must not change original identity or clone roster members; Gates 1/3 check canonical references and reconstruction.
- Stale recruitment/pair choices must not charge twice or swap a live outing; Gates 1/2 check zero mutation.
- Failed battle construction must restore every participant, not only the former lead; Gate 2 checks checkpoint/phase rollback.

## Gates And Tests

Every gate uses red/green focused tests; names below are proposed additions unless identified as existing. Existing test modules are the preferred homes rather than a new test for every prose bullet.

### Gate 0 - Freeze M1 Decisions And Migration Shape

- [ ] Approve M1-D1 through D4 below; inventory all position-based roster lookups with `rg` and record the exact changed call sites.
- [ ] Specify old-to-new snapshot examples for a new game, pre-entrance save, recruited tutorial pair, completed Hub, and active Rest checkpoint. Map every added field to a runtime owner and validator.
- [ ] Review the shape before implementation; no unapproved narrative restriction or recruitment content is introduced.

Proof: a finite field/API/action matrix, migration fixtures, and decisions recorded in this plan. Unresolved downstream story costs are assigned to M4, not guessed.

### Gate 1 - Canonical Roster And Deployment Identity

- [ ] Add failing cases in `root/tests/test_game_state.py` and `test_party_state.py` for `test_recruited_members_are_unique_and_active_ids_resolve_canonical_objects`, `test_selection_rejects_duplicate_unknown_or_unrecruited_ids_without_mutation`, and `test_original_identity_does_not_change_when_active_order_changes`.
- [ ] Implement the approved roster lookup/active-ID representation and controlled recruitment eligibility; preserve the existing 65-gold event exactly once.
- [ ] Verify single-member opening, pair after D2, legal three-member pair choices after a controlled Floor II event, and no production path to premature D3/D4.

Proof: `python -m pytest tests/test_game_state.py tests/test_party_state.py tests/test_hub_flow.py` from `root/`; invalid snapshots and selection leave before/after state equal.

### Gate 2 - Session, Participant Rewards, And Exact Targets

- [ ] Extend `root/tests/test_hub_flow.py`, `test_party_battle.py`, `test_hub_extraction.py`, and `test_floor_one_run.py`. Exercise a controlled three-member roster with a non-default active pair, actor-owned moves/resources, participant-only rewards, and unchanged bench state.
- [ ] Route battle creation, rewards, return restoration, character/skill/weapon/equipment inspection, and merchant actions through the correct roster versus participant boundary.
- [ ] Add `test_pair_cannot_change_during_outing_or_rest`, `test_bench_weapon_action_targets_requested_member`, and construction-failure rollback for every participant. Keep existing `test_floor_one_recover_keeps_the_party_at_rest_until_explicit_continue` and extraction-after-recovery coverage.

Proof: all affected flow modules pass; pure synthetic roster tests do not claim live Floor III/four-party qualification.

### Gate 3 - Trusted Save And Remote Advancement

- [ ] Add schema migration/round-trip cases to `root/tests/test_save_state.py`, `test_game_snapshot.py`, `test_save_coordinator.py`, and profile integration tests. Cover two/three/four recruited IDs, active order, exact per-Drifter progression, no auto-recruitment, and source immutability.
- [ ] Implement validators/reconstruction/clone and version dispatch. Reject duplicate nested identities, dangling active references, invalid event/floor evidence, and mid-battle disk saves without a supported snapshot.
- [ ] Prove a historical schema-12 remote revision retains its digest/content and advances to a valid new revision; malformed current payloads are rejected by client and real service.

Proof: focused local persistence tests plus PostgreSQL service/integration tests and migration checks under the shared contract. A synthetic migration alone is insufficient.

### Gate 4 - Terminal And Built-Browser Flow

- [ ] Add semantic Hub pair-selection inputs and matching presenter offers. Test in `root/tests/test_party_terminal_ui.py`/`test_terminal_overworld_ui.py` and `root/web_tests/test_browser_bridge_contract.py`.
- [ ] Extend `root/web_tests/browser_smoke.mjs`: select a legal controlled recruited pair, inspect each member, alter one member's permitted progression, save, reload a new browser runtime, and verify exact roster, active IDs, target state, resources, and original identity.
- [ ] Verify D1 -> D2 onboarding by ordinary gameplay separately from controlled later-roster setup; invalid/unoffered submissions remain rejected. Check phone portrait/landscape and desktop for reachable selection and navigation.

Proof: same Python-authoritative choices/results in terminal and browser, no client-only recruitment or party rules.

### Gate 5 - Qualification And Handoff

- [ ] Extend the real probe with roster initialization, selection, snapshot round-trip, teardown, and no early recruit; run the shared cumulative qualification on the final tree.
- [ ] Record exact results/SHA, review the cumulative diff, and obtain acceptance for M1 only.

Closure: roster and active-party identity are distinct, all currently recruited members can be targeted exactly, old pairs migrate unchanged, and no future Drifter is granted. All-six-pair live qualification and the first four-Drifter boss remain M4B/M6 responsibilities after canonical recruitment.

## Unresolved Product Decisions

| ID | Decision and blocking gate | Do not assume |
| --- | --- | --- |
| M1-D1 | Original starting Drifter's narrative role and whether that identity imposes an active-party restriction; Gate 0 | A root save field means mandatory active leader, or changing slot 1 changes protagonist |
| M1-D2 | Later recruitment event representation and when recruitment becomes secured; Gate 0 defines the contract, M4 authors scenes/costs | D3/D4 cost 65 or appear immediately in the Hub |
| M1-D3 | Restoration/access rules for benched recruits at the Hub and during an outing; Gate 0 | A bench slot creates free mid-run healing or inventory transfer |
| M1-D4 | Pair-order semantics and any non-expedition Hub restrictions; Gate 0 | Arbitrary mid-run substitution or four-person ordinary encounters |

Later entry checks revalidate the concrete API names above; the recruitment floors and regression-protected first pair are fixed, not provisional.

# M1 Permanent Roster And Hub Party Selection Implementation Plan

> Implementation method: use `superpowers:executing-plans` for native gate-by-gate execution. This document does not authorize implementation, delegation, commits, or publishing.

**Status:** M1 implementation commit `8eb1a63cd08cf5f5a424749f3ae25479a048bccf` was corrected in `eee874a848ce86b094dc14d633c81a1c49928aa6`. Hosted run `41202800638` passed Python, web, PostgreSQL, content, and build checks, but browser smoke exposed a test synchronization race after returning from party selection. The smoke now waits for the Hub badge before opening Character; the web suite and clean full browser smoke pass locally. A hosted rerun on a new corrective commit remains required; M1 is not sealed.

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

The following are approved M1 interfaces, not claims that they already exist. Exact names may be adjusted during implementation without changing these ownership contracts:

| Proposed boundary | Contract |
| --- | --- |
| `GameState.recruited_members` | Read-only tuple of canonical recruited `PlayerState`s, including the original starting Drifter once |
| `GameState.member_for_drifter_id(drifter_id)` | Returns that canonical member; rejects unknown/unrecruited IDs, with no lead fallback |
| `PartyState.active_drifter_ids` | Persisted ordered selection, distinct from the permanent roster; one member before D2 joins and exactly two for an ordinary outing; M4B adds the explicit authored full-party encounter mode |
| `GameState.active_party_members` | Resolves active IDs through the roster; does not clone them into another authoritative party |
| `PartyState.select_active_pair(drifter_ids, *, recruited_ids)` | Validates two distinct recruited IDs and Hub eligibility before assigning; no mutation on rejection |

Approved representation: preserve the original player at the existing root boundary, generalize companions to the remaining recruited members, and persist explicit active IDs. The root player is the stable campaign/story anchor, not a mandatory active participant. Do not persist both a roster copy and companion copies.

Recruitment needs an authored event identity, required floor/story condition, eligible candidate IDs, cost, and one-time completion evidence. The client submits an offered event/Drifter ID, not an arbitrary floor/cost/unlock flag. Reuse `StoryState` completed-event support where sufficient. Decide when later recruits become secured before connecting a dungeon event. M1 supplies the validated extension point and controlled fixtures, not production Floor II/III recruitment scenes.

Ordinary-run participants are fixed at deployment and remain the reward recipients through encounter completion, Rest saves, extraction, and death. Bench members receive no combat XP merely because they are recruited; expedition XP belongs to M6. Retain the tutorial's 50/50 split and existing Floor I payout arithmetic. M4B may introduce an explicit authored full-party encounter boundary for the Floor III boss; that is not permission for arbitrary mid-run swaps. Its participation/reward contract must preserve earlier pair-earned rewards rather than redivide them across a newly enlarged party. Full-party boss XP interpretation is a later entry decision, not M1 arithmetic.

## File And Client Work

Modify `root/src/app/game/game_state.py`, `party_state.py`, `overworld_session.py`, and `weapon_progression.py`; extend `root/src/app/ui/overworld_ui.py`, `terminal_overworld_ui.py`, and `root/src/app/presentation/overworld_models.py`/`overworld_presenter.py`. Inspect `root/src/app/player/inventory_action.py` for actor-owned item targeting. Prefer one shared roster lookup over repeating position-dependent tuples.

Gate 1 adds the smallest immutable recruitment-event spec needed by the existing authored-content architecture and exposes its records through the current read-only content catalog. The spec owns event ID, floor/story eligibility, candidate Drifter IDs, and authored cost; the existing Floor I D2 onboarding is the only production recruitment event represented by M1. Follow the existing generated-catalog path where applicable, and extend its validation only for recruitment-specific invariants. Do not add a new narrative scene, second event engine, broad content framework, or production D3/D4 records.

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

## Gate 0 Decision Record

The user approved all six defaults on 2026-10-30:

| ID | Approved decision |
| --- | --- |
| M1-D1 | D1 remains the campaign/story anchor but may be benched. Active order never changes Drifter identity, and no active-party rule requires D1. |
| M1-D2 | Accepting a valid authored recruitment event adds that Drifter permanently and charges its authored cost exactly once. Death does not remove the recruit. Reuse `StoryState.completed_events` as the one-time event record; later recruitment scenes and prices remain owned by their floor/content milestones. |
| M1-D3 | At the Hub, all recruited Drifters are inspectable and available to existing exact-target Character, Skills, Weapon, Equipment, and merchant actions. During an outing, only the deployed pair is accessible; no bench actions, transfers, or swaps. Every return to the Hub restores all recruited Drifters to full HP/Mana. |
| M1-D4 | At the Hub, select any two distinct recruited Drifters. Selection order is battle/presentation order only. The pair is locked from deployment until return to the Hub, including Rest; ordinary outings remain two-person. |
| M1-D5 | Store D1 once as `GameState.player_state`, D2-D4 as canonical `PartyState.companions`, and the ordered active IDs on `PartyState`. No duplicate roster representation. |
| M1-D6 | Advance runtime schema 11 to 12 and disk schema 12 to 13. Keep profile-envelope version 1 and API `/v1`; update the profile-service payload validator for disk schema 13. No database-table migration is planned. |

The fixed campaign pacing remains unchanged: any Drifter may be D1; D2 joins on Floor I for 65 gold, D3 on Floor II, D4 on Floor III; Floor III has the first four-Drifter boss, and expeditions start on Floor IV. M1 adds no production D3/D4 scenes or costs. A recruit accepted during an outing joins the permanent roster immediately but cannot replace an outing participant until the party returns to the Hub.

### State, Action, And Validation Matrix

| Concern | Owner and rule | Validation/failure behavior |
| --- | --- | --- |
| Permanent roster | `GameState.player_state` is D1; `PartyState.companions` stores up to three additional canonical `PlayerState` objects. Each recruited Drifter exists once per game. | Canonical content IDs are unique; an unknown or unrecruited ID is rejected, never substituted with D1. |
| Deployed party | `PartyState.active_drifter_ids` is an ordered list of one or two recruited IDs. After D2 joins, ordinary outings use exactly two. Deployment captures the pair for the entire outing. | IDs must be unique and belong to the roster. A party change outside the Hub is rejected without mutation. |
| Recruitment | A semantic request names the currently offered authored event and candidate. The event owns eligibility/cost; successful addition and payment are one atomic mutation. `StoryState.completed_events` prevents replay. | Forged/stale event, duplicate recruit, or insufficient funds leaves roster, event evidence, and currency unchanged. Recruitment is permanent once accepted. |
| Hub targeting | Character, Skills, Weapon, Equipment, and merchant actions resolve the submitted Drifter ID against the full recruited roster. | Exact target required; no lead/first-member fallback. Bench actions are unavailable during an outing. |
| Battle and rewards | Battle construction, item-use actor, run checkpoints, XP, and encounter rewards resolve through the captured active IDs, not roster position. Bench members gain no combat XP. | Duplicate, missing, or changed participants fail before mutation; failed construction restores every captured participant and phase. |
| Return/recovery | Extraction or death returns to the Hub and restores every recruited Drifter to full HP/Mana. | No mid-run bench restoration or party substitution. Existing reward-loss/banking rules remain unchanged. |
| Persistence | Game snapshot runtime schema 12; disk schema 13; envelope v1 and API `/v1`. Profile service accepts the new current disk payload while historical remote revisions remain immutable. | Validate roster uniqueness, active subset/order/size, event evidence, and phase consistency before reconstruction. Invalid payloads fail closed. |

### Migration Examples

| Source state | Schema-13 roster | Active IDs | Preserved behavior |
| --- | --- | --- | --- |
| New game or legacy solo/pre-Hub save | D1 only | `[D1]` | No companion or future Drifter is granted. |
| Existing tutorial pair save | D1 plus its existing D2 | Existing pair order, normally `[D1, D2]` | All player progression, equipment, weapon investment, shared inventory, and recruitment evidence remain intact. |
| Completed Hub save | Exact legacy recruited members | Exact prior selection; legacy pair derives `[D1, D2]` | Hub state and shared resources remain unchanged. |
| Active Floor I Rest save | D1 and D2 | Exact active pair `[D1, D2]` | Rest cursor/phase, HP/Mana, pending rewards, and no-rewind behavior are preserved. No bench swap occurs on load. |
| Historical remote schema-12 revision | Migrated copy of the same D1/D2 state | `[D1, D2]` unless a valid prior selection is represented | Original payload and digest remain immutable; a new schema-13 write advances from the accepted remote revision. |

### Current-Tree Roster Lookup Inventory

Entry inventory at `4f857b6dce4c91b6ba09e93a5654cd32ead0dbcb` found these implementation boundaries. Line numbers are from that baseline and are navigation aids, not fixed patch locations.

| File/boundary | Current position-based assumption | M1 treatment |
| --- | --- | --- |
| `root/src/app/game/game_state.py` (`clone`, `snapshot`) | Clones/snapshots root player and companions as separate fixed fields. | Keep the one-root-plus-companions storage, extend companions and clone graph, persist active IDs. |
| `root/src/app/game/party_state.py` (`recruit_companion`, Floor I start/reward validation, snapshot reconstruction) | Rejects a second companion; assumes pair order and computes party size from root plus companion count. | Generalize roster membership; use captured active IDs for ordinary run eligibility and participant/reward ownership. |
| `root/src/app/game/overworld_session.py` (participant tuple at 246, 788, 868, 916, 1258; targeting at 642-643; battle setup/checkpoints at 1055-1118 and 1236; Rest recovery at 1363-1365) | Rebuilds participants as `(player_state,) + companions`, forces the root player into Battle, and checkpoints/restores only that root in some paths. | Resolve the deployed pair once and use it consistently for Battle, rewards, checkpoints, recovery, and exact targets. Keep root identity separate from active order. |
| `root/src/app/presentation/overworld_presenter.py` (`_companion_choices` 287-310; target lists 391-410, 444-478, 508-540) | Recruitment choices exclude the root lead; character, weapon, and merchant target lists contain only root plus companions. | Candidate offers come from authored event eligibility; Hub target lists use every recruited member. Pair-selection offers only recruited identities. |
| `root/src/app/game/weapon_progression.py` (target lookup at 208) | Resolves a Drifter through root plus companions. | Resolve against the canonical roster with no lead fallback. |
| `root/src/app/persistence/save_document.py` (current/legacy party validation around 601-780; Floor I payload validation around 1285-1292) | Limits old and current party snapshots to one companion and infers participant count from that shape. | Preserve historical-schema limits; update only schema-13 validation/migration to the approved roster and active-ID contracts. |
| `root/web/python/dd_bridge.py`, `root/web/play/js/pyd4.js` | Existing character/weapon/merchant commands already carry Drifter IDs, but no active-pair action exists. | Add semantic pair-selection submission/projection; Python remains authoritative for membership, eligibility, and validation. |
| `root/web/qualification/python/boot.py` (334, 386) | The sealed Surface/Hub probe explicitly names the tutorial lead and companion. | Preserve that pair as historical regression evidence; add roster qualification without weakening the existing two-Drifter path. |

A broad search for direct `player_state`/`companions` assumptions matched 26 Python test/support modules. This is an impact list, not a deletion/edit quota; Gate 1-4 touch the focused state, flow, persistence, presenter, terminal, browser, and profile-service owners below. Existing T0 qualification and historical Surface coverage remain protected.

## Gates And Tests

Every gate uses red/green focused tests; names below are proposed additions unless identified as existing. Existing test modules are the preferred homes rather than a new test for every prose bullet.

### Gate 0 - Freeze M1 Decisions And Migration Shape

- [x] Approve M1-D1 through D6 and record the selected representation above.
- [x] Inventory current position-based roster lookups and record the production boundaries and qualification references above.
- [x] Specify old-to-new snapshot examples for a new game, legacy solo/pre-Hub save, recruited tutorial pair, completed Hub, active Rest checkpoint, and historical remote schema-12 revision. Map new fields to owners and validators.
- [x] Review the shape before implementation; no unapproved narrative restriction, future recruitment price, or recruitment scene is introduced.

Gate 0 is complete. The field/action matrix and migration fixtures are specified above; implementation and generated migration tests begin at Gate 1. Unresolved downstream story costs remain assigned to their owning floor/content milestones.

### Gate 1 - Canonical Roster And Deployment Identity

- [x] Add focused cases in `root/tests/test_game_state.py` and `test_party_state.py` for canonical roster lookup, rejected duplicate/unrecruited selection without mutation, and unchanged root identity after active-order changes.
- [x] Implement the approved roster lookup/active-ID representation and authored recruitment eligibility; preserve the existing 65-gold event exactly once.
- [x] Verify the solo opening, pair after D2, legal pair choices with a controlled three-member test roster, and no production path to premature D3/D4.

Proof: root suite passed; invalid snapshots and selections leave before/after state equal. Controlled D3 data is test-only; no Floor II event or future recruit was authored.

### Gate 2 - Session, Participant Rewards, And Exact Targets

- [x] Extend the Hub/Floor I flows for a controlled three-member roster with a non-default active pair, actor-owned moves/resources, participant-only rewards, and unchanged bench state.
- [x] Route battle creation, rewards, return restoration, character/skill/weapon/equipment inspection, and merchant actions through the correct roster-versus-participant boundary.
- [x] Verify party lock through Rest, exact bench targeting rejection, and construction-failure rollback for all participants; retain recovery-at-Rest and extraction-after-recovery coverage.

Proof: all affected flow modules pass; pure synthetic roster tests do not claim live Floor III/four-party qualification.

### Gate 3 - Trusted Save And Remote Advancement

- [x] Add schema migration/round-trip cases covering one through four recruited IDs, active order, per-Drifter progression, no auto-recruitment, and source immutability.
- [x] Implement schema-13 validators/reconstruction/clone and version dispatch; reject malformed roster references, event evidence, and unsupported mid-battle disk saves.
- [x] Prove schema-12 remote history remains immutable while advancing to schema 13; reject malformed current payloads at client and real-service boundaries.

Proof: focused local persistence tests plus PostgreSQL service/integration tests and migration checks under the shared contract. A synthetic migration alone is insufficient.

### Gate 4 - Terminal And Built-Browser Flow

- [x] Add semantic Hub pair-selection inputs and presenter offers; terminal and browser bridge contract tests pass.
- [x] Execute the real-browser pair-selection and save/reload flow on the corrective working tree. A clean built-site smoke passes the two ordered choices, exact recruited target, stat investment, and weapon progression across save/reload. Hosted run `41160651816` exposed the missing two-member `Choose Party` option; run `41202800638` verified that fix and pair save/reload, then failed because the smoke clicked Character before the Hub rerender completed. The smoke now waits for the Hub badge after Back; hosted rerun remains required under Gate 5.
- [x] Verify semantic D1 -> D2 recruitment, invalid/unoffered submissions, and desktop/mobile selection/navigation contracts through the existing route, bridge, and viewport qualification tests.

Proof: same Python-authoritative choices/results in terminal and browser, no client-only recruitment or party rules.

### Gate 5 - Qualification And Handoff

- [x] Extend the real probe with roster initialization, selection, snapshot round-trip, teardown, and no early recruit; run the shared cumulative qualification with the pinned MicroPython executable.
- [ ] Review and accept the corrective diff, rerun cumulative hosted qualification on its commit, and record the resulting SHA and exact evidence.

Local qualification record (2026-10-30; uncommitted working tree):

- Root pytest: 1,856 passed. Web pytest: 62 passed. Profile service against disposable PostgreSQL 17: 33 passed.
- Authored-content validation passed: 5 enemies, 4 weapons, 4 Drifters, 10 encounters, 2 routes, and 1 recruitment event. Python compileall and `git diff --check` passed.
- PostgreSQL migration from zero passed; `alembic check` reported no new upgrade operations.
- The exact pinned Windows MicroPython v1.29.0 executable was used (488,960 bytes; SHA-256 `6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA`). Native/overlay CPython, default MicroPython, 624K MicroPython, and semantic parity passed; 624K was stable 3/3 and 608K produced the expected memory-limit result 3/3.
- The initial hosted M1 run `41160651816` on `8eb1a63cd08cf5f5a424749f3ae25479a048bccf` reached the Hub and failed because `Choose Party` was missing for a two-member completed roster. The regression reproduced that failure; the presenter now offers the action for exactly two members, and the focused presenter module passes 40 tests.
- After the presenter and browser-smoke corrections (2026-10-31), a clean local browser build passed the full `browser_smoke.mjs` route, including active-pair selection, recruited-Drifter stat save/reload, and weapon component/progression save/reload. This is local evidence only; the hosted cumulative rerun and its resulting SHA remain open.
- Hosted run `41202800638` on `eee874a848ce86b094dc14d633c81a1c49928aa6` passed its Python (1,857), web (62), PostgreSQL (33), content, compile, and browser-build checks, but browser smoke failed after Back from PARTY SELECTION because it attempted Character before the Hub rerender. Added a condition-based wait for the `HUB` badge and a web contract assertion that protects the sequence. Current web pytest passes 62; a fresh 147-file browser build and full local smoke pass. The synchronization correction is uncommitted and has no hosted result yet.

Closure: roster and active-party identity are distinct, all currently recruited members can be targeted exactly, old pairs migrate unchanged, and no future Drifter is granted. All-six-pair live qualification and the first four-Drifter boss remain M4B/M6 responsibilities after canonical recruitment.

## Deferred Decisions Owned By Later Milestones

| Owner | Deferred question | Boundary |
| --- | --- | --- |
| M4/content | Authored D3/D4 recruitment scenes, floor events, and costs. | Do not copy D2's 65-gold price or grant D3/D4 before their floors. |
| M4B | Exact four-Drifter boss participation and XP interpretation while preserving rewards earned by the prior pair. | Do not redivide earlier pair rewards or make ordinary encounters four-person. |

Later entry checks revalidate concrete API names against the implementation tree. The approved roster, active-pair, migration, and recovery semantics above are fixed for M1.

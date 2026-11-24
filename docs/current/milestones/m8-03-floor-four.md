# M8.3: Drowned Reliquary, Floor IV

**Status:** Gate A approved; Gate B implementation is complete in the current worktree. Local root, web, content, compile, browser and pinned-runtime checks are recorded below. Exact-SHA hosted CI and independent Gate C review remain pending; M8.3 is not yet closed or sealed.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Implementation base:** M8.2 `21565f3d37a6d845cdb70a0598d11b7e432b3269`, accepted and sealed with exact-SHA CI [45252053112](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/45252053112).

## Goal

Deliver the first playable M8 route using the approved two-Drifter ordinary and paired-boss loop, existing combat resolver, M7 Momentum, and authoritative Floor-IV clear evidence.

## Approval Boundary

**Already-approved inputs:** preserve M1's two-person ordinary outings and legal pair selection, M4's recruitment/XP ownership rules, M7's shared Momentum contract, and M6's completed-floor eligibility.

**Approved and implemented:** Floor-IV IDs, compositions, reward/source relationships, D6 portrait associations, and package numerical tuning. The owner authorized implementation values within those boundaries; M8.4-owned discovery, armor, and Healing Potion integrations remain disabled.

## Scope

- Add the parent manifest's approved 12-node `floor_four` route: nine ordinary battles, midpoint Rest, pre-boss Rest, and paired Floor-IV boss. `Tidebound Curator` is the approved boss identity.
- Author this destination as a member of Region 1 through M8.1's explicit membership contract; do not infer region from `floor_four` numbering.
- Use the approved encounter IDs `m8_floor_four_encounter_01` through `_09` and `m8_tidebound_curator_boss` with their accepted D1 compositions.
- Author the approved ordinary-enemy and Curator identities/compositions. Reuse supported combat mechanics; no new phases, formations, hazards, or renderer are authorized. M8.9 owns integration of the D6-approved static assets with their now-approved D1 associations; asset production/delivery remains a separate responsibility.
- Author the four named Grade-IV material source IDs in the parent manifest and the Floor-IV first-clear Grade-IV Crystal reward. Actual probabilities, quantities and recipe values require the approved balance pass; source provenance must remain floor-eligible.
- Record Floor-IV clear only through M8.1's canonical clear boundary; preserve pair XP splitting and ordinary two-member deployment.

## Implementation Record

### Route And Encounter Content

The authored route preserves the approved 12-node order and encounter compositions:

| Order | Node | Kind / encounter | Authored composition |
| ---: | --- | --- | --- |
| 1 | `floor_four_battle_01` | `m8_floor_four_encounter_01` | Reliquary Sentinel + Drowned Stalker |
| 2 | `floor_four_battle_02` | `m8_floor_four_encounter_02` | Brine Oracle + Drowned Stalker |
| 3 | `floor_four_battle_03` | `m8_floor_four_encounter_03` | Reliquary Sentinel x2 |
| 4 | `floor_four_battle_04` | `m8_floor_four_encounter_04` | Brine Oracle + Reliquary Sentinel |
| 5 | `floor_four_battle_05` | `m8_floor_four_encounter_05` | Ashbound Hound + Drowned Stalker |
| 6 | `floor_four_rest_midpoint` | Rest | Midpoint checkpoint |
| 7 | `floor_four_battle_06` | `m8_floor_four_encounter_06` | Reliquary Sentinel + Brine Oracle |
| 8 | `floor_four_battle_07` | `m8_floor_four_encounter_07` | Drowned Stalker x2 + Brine Oracle |
| 9 | `floor_four_battle_08` | `m8_floor_four_encounter_08` | Reliquary Sentinel + Ashbound Hound + Brine Oracle |
| 10 | `floor_four_battle_09` | `m8_floor_four_encounter_09` | Brine Oracle x2 + Drowned Stalker |
| 11 | `floor_four_rest_pre_boss` | Rest | Pre-boss checkpoint |
| 12 | `floor_four_battle_10` | `m8_tidebound_curator_boss` | Tidebound Curator + Reliquary Sentinel |

Tier-3 profile HP values are Sentinel 115, Oracle 80, Stalker 90, Hound 100, and Curator 300. Existing resolver and M7 Momentum apply. The ordinary enemy moves and authored tier-3 stats are in their respective enemy definitions; no new combat mechanics, phases, hazards, or formations were introduced. Legal two-Drifter active pairs remain unchanged.

### Reward And Progression Values

| Source ID | Authoritative source | Outcome |
| --- | --- | --- |
| `m8_floor_four_metal_drop_01` | Reliquary Sentinel, ordinary victory | 1 Grade-IV Metal at 3,000 bps |
| `m8_floor_four_fiber_drop_01` | Drowned Stalker, ordinary victory | 1 Grade-IV Fiber at 3,000 bps |
| `m8_floor_four_timber_drop_01` | Ashbound Hound, ordinary victory | 1 Grade-IV Timber at 3,000 bps |
| `m8_floor_four_core_drop_01` | Tidebound Curator boss victory | 1 Grade-IV Core at 10,000 bps |
| `m8_floor_four_first_clear_crystal` | First genuine Floor-IV clear only | Exactly 1 Grade-IV Magic Crystal |

Material drops are persisted with source/floor/node provenance and remain repeatable on legitimate Floor-IV replays. The reserved Grade-IV Merchant Crystal offer remains unavailable. Drowned Reliquary becomes Confirmed only through durable destination entry; Ashen Vault becomes Rumored only after genuine boss clear. Ordinary encounter XP remains unsecured run reward and follows existing Floor-IV pair split/Intuition rules at settlement. The paired boss uses the existing M4 boss-settlement pattern and ordinary pair XP ownership.

### Persistence And Compatibility

Schema 27 adds Floor-IV run identity, replay count, and outing XP multiplier to existing `PartyState` ownership. Schema-26 payloads migrate additively with inactive Floor-IV defaults and no inferred clear/unlock. Schema-26 remote-history payloads are dispatched through immutable historical validation; they are not migrated in place. Current-schema validation accepts only Floor-IV events belonging to the active Floor-IV run/route and rejects Floor-IV evidence in historical schemas. Existing I-III save defaults and progression remain covered. No new discovery claims or armor/recovery rewards are activated by this package.

### Pinned Runtime And Heap Evidence

Pinned Windows MicroPython v1.29.0 passed semantic parity and the 1408 KiB stable (3/3) / 1216 KiB expected-memory-limit (3/3) matrix. The binary SHA-256 is `6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA`. Values below are `lowest free heap / peak allocated`, in bytes, from three comparable runs:

| Probe state | Run 1 | Run 2 | Run 3 | Classification |
| --- | ---: | ---: | ---: | --- |
| M8.2 baseline, 1408 KiB | 306592 / 1102176 | 310256 / 1098512 | 310288 / 1098480 | Stable pass, 3/3 |
| M8.2 baseline, 1216 KiB | 117968 / 1098672 | 118128 / 1098512 | 118240 / 1098400 | Expected memory limit, 3/3 |
| M8.3 implementation, 1408 KiB | 279968 / 1128800 | 280544 / 1128224 | 280544 / 1128224 | Stable pass, 3/3 |
| M8.3 implementation, 1216 KiB | 88480 / 1128160 | 88336 / 1128304 | 88304 / 1128336 | Expected memory limit, 3/3 |

The original M8.2 qualification did not record per-run telemetry; its separate follow-up measurement is shown for comparison. M8.3 required no heap-profile increase.

## Exclusions And Handoff

No permanent discoveries, live armor/recovery rewards, expedition category/report work, Floor-V route, extra recruitment, or four-member boss. M8.4 owns discovery, armor and recovery reward integration. Until M8.4, Rest nodes must not imply those sources are available. M8.5 owns expedition access to the completed destination.

**Persistence impact:** Floor-IV clear storage and migration belong to M8.1. This package authors the genuine victory that sets that evidence; it must not add a second completion record.

## Ownership

Route and encounter catalog owners are `root/src/app/content/route_spec.py`, `root/src/app/content/routes/`, `enemy_spec.py`, `catalog.py`, and generated catalog tooling. Session, route cursor, reward, and clear ownership remain in `root/src/app/game/overworld_session.py`, `overworld_state.py`, `party_state.py`, and existing run-event owners. Revalidate exact call sites before implementation; do not add new APIs to this plan by assumption.

## Tests, Package Gates, And Qualification History

Test route reachability/node order, every encounter definition, tier-3 validation, Floor-IV unlock from M8.1, two-member deployment, pair XP and Intuition, M7 symmetry, material grade provenance, first-clear idempotency, Rest checkpoint reload, boss settlement retry, failed writes and unchanged I-III behavior.

- **Gate A, plan approval:** Approved by the owner in the M8.3 authorization. D1 identities, compositions, source mappings, and D6 associations remain unchanged.
- **Gate B, implementation and focused tests:** Implemented. Focused Floor-IV session tests: 11 passed; route/content and persistence boundary tests passed in the root suite.
- **Gate C, exact-SHA qualification:** Local results recorded; hosted exact-SHA CI is pending push. Independent review and owner closure remain open.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Pending commit | Pending exact-SHA CI | Local: 2,547 root passed / 12 local Python 3.12 `annotationlib` environment failures; 94 web passed; 36 service passed / 17 skipped without local Docker; content validation, compile, 199-file browser build, full Playwright smoke, and pinned MicroPython matrix passed | Pending independent Gate C review | Gate B implemented; not sealed |

The hosted workflow uses Python 3.14 and PostgreSQL 17; it must pass on the exact implementation SHA before Gate C review. The 12 local root failures are compatibility-overlay subprocess tests that require Python 3.14's `annotationlib`; their failures do not overlap Floor-IV tests. Local PostgreSQL, migration-from-zero, and Alembic parity could not run because the Docker engine is unavailable. Record exact implementation SHA and hosted run after push. Close only after hosted qualification, independent review, and owner acceptance.


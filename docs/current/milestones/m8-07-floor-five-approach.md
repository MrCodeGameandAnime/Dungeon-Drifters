# M8.7: Ashen Vault, Floor V Approach

**Status:** CLOSED AND SEALED at implementation SHA `0fcd64347e7b2af5673e5ba9785b5bba5676edf8`; owner acceptance and exact-SHA hosted qualification are complete. M8.8 may proceed.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate route and expedition owners at package entry.

## Goal

Deliver the paired seven-node approach that reveals the reunion arena through a real victory and returns to the Hub without inserting or swapping party members.

## Approval Boundary

**Already-approved inputs:** preserve the two-plus-two roster loop, M1 pair selection, M2 outing settlement, M6 passive expedition behavior, M7 Momentum, and M8-D5's expedition coexistence/settlement boundary. The separate four-member boss has no active assignment; a completed, settled but unclaimed report does not block it; no assignment is canceled or refunded automatically.

**Already approved:** Floor-V encounter, route/node, reward/source IDs and placements; D3 fact/reveal mappings; and D5 assignment boundaries. **Package review remains:** implementation, persistence, integration and test details within those contracts.

M8-D6 approves `m8_art_ashen_vault` as a static Region 1 destination illustration, associated with the now-approved Ashen Vault destination identity. M8.9 owns live integration; this does not change the route or gameplay contract.

## Scope

- Add the six parent-manifest Floor-V ordinary encounters and `floor_five_approach`: six battles plus `floor_five_rest_midpoint`.
- Author the Ashen Vault/Floor-V destination as a member of Region 1 through M8.1's explicit membership contract; do not infer region from `floor_five` numbering.
- Keep ordinary encounters two-Drifter and allow any legal active pair.
- Place `spirit_relic_floor5_01` at the midpoint Rest using the reward/search contract delivered by M8.4; do not duplicate its effect or claim logic.
- Record `m8_ashen_arena_revealed` only after the route's genuine final victory is durably committed. Failed/abandoned battle or failed save cannot reveal it.
- Preserve M7 Momentum, Grade-IV provenance, normal extraction/death settlement, and the two-plus-two roster loop.

## Exclusions And Handoff

No reunion boss, Floor-V clear, first-clear boss reward, new discovery service, or item key. M8.1 owns the arena eligibility evidence; M8.4 owns the Spirit Relic reward; M8.5 owns the approved assignment coexistence/report lifecycle behavior used here. M8.8 consumes the arena reveal.

## Ownership And Persistence

Use existing route/content/session/run-event/save owners, revalidated at package entry. The route is a paired outing and uses normal durable outcome/return semantics. Do not add a parallel campaign engine or client-side arena unlock.

**Persistence impact:** M8.1 owns durable arena-reveal state. This package records it through that owner after genuine victory; no separate route-completion schema is proposed.

M8.7 owns the live Spirit Relic test for the approved source ID and placement. Use the approved 1,000-bps base chance with existing Intuition adjustment through the normal search path. Claim exactly +3 GP for one eligible active Drifter and reload without a second award. Preserve existing per-run retry semantics; separately exercise a failed search and no reward.

## Tests, Package Gates, And Qualification History

Test all six encounters and route order, all legal pairs, midway Rest/search/save/reload, source idempotency, assignment coexistence as approved by D5, final victory vs defeat/extraction/save failure, no premature arena option, reload/retry, and terminal/browser parity.

- **Gate A, plan approval:** Authorized by the M8.7 implementation authorization; D1 content/source entries, D3 mappings, and M8-D5 remain fixed.
- **Gate B, implementation and focused tests:** Implemented; route, reveal, discovery placement, failure/retry, expedition coexistence, migration, and browser journeys have focused coverage.
- **Gate C, exact-SHA qualification and closure:** CLOSED; hosted CI run `45832492446` passed and the owner accepted M8.7 as sealed.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| `0fcd64347e7b2af5673e5ba9785b5bba5676edf8` | [Exact-SHA hosted CI 45832492446](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/45832492446): 2,693 root, 96 web, and 56 profile-service tests passed; browser smoke, PostgreSQL integration, migration-from-zero, and Alembic parity passed. | Pinned MicroPython v1.29.0; native/overlay/runtime parity passed; 1408 KiB stable 3/3; 1216 KiB expected memory limit 3/3. | Accepted by owner after adversarial corrections | CLOSED AND SEALED |

Review corrections: pre-schema-30 remote fixtures omit `floor_five_approach_run_id`, a schema-29 remote revision with a settled M8.5 report migrates to schema 30 without changing historical payload/digest, midpoint extraction now exercises direct Extract with save-failure rollback/retry and compatible expedition settlement, and terminal recovery exposes only the retry action.

The local correction-candidate report above predates the final hosted seal and is retained as historical context; the exact-SHA hosted run and accepted pinned MicroPython results in the qualification table are authoritative for closure.

M8.7 is closed. M8.8 consumes its durable `m8_ashen_arena_revealed` evidence and remains responsible for the separate reunion encounter and settlement.


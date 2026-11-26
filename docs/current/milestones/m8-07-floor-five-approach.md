# M8.7: Ashen Vault, Floor V Approach

**Status:** Implementation and local qualification in progress under the approved M8.7 authorization. The route, discovery placement, settlement, schema migration, tests, and real-browser journey are implemented. Exact-SHA hosted qualification and independent review remain open; do not start M8.8 until M8.7 is accepted.
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
- **Gate C, exact-SHA qualification and closure:** Open; local cumulative checks are recorded below. Hosted CI and independent adversarial review are pending.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Candidate implementation (commit pending) | Exact-SHA hosted CI pending | Exact pinned Windows MicroPython v1.29.0, 488,960 bytes, SHA-256 `6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA`: CPython 3.12.14 native and forced overlay, MicroPython default, and semantic parity passed; 1408 KiB stable 3/3; 1216 KiB expected memory limit 3/3; `MYP20|RESULT|CLOSURE_COMPLETE`. | Pending | Open |

Local cumulative checks on the pre-commit candidate: **2,679 root tests passed; 12 compatibility tests failed** because the local CPython 3.12.14 runtime lacks `annotationlib` (the hosted workflow uses Python 3.14); **96 web tests passed**. Authored-content validation passed (10 enemies, 4 weapons, 4 Drifters, 27 encounters, 6 routes, 3 recruitment events), Python compilation passed, the browser build packaged 209 runtime files, and the full Playwright smoke exited 0 with `M8.7_BROWSER|APPROACH_RELIC_AND_ARENA_REVEAL|PASS`. `git diff --check` passed. Local PostgreSQL, migration-from-zero, and Alembic checks could not run because the Docker engine was unavailable; exact-SHA hosted qualification is pending. The pinned MicroPython matrix is recorded above.

Require independent review and record CI/closure evidence.


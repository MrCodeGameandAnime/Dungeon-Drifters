# M8.4: Permanent Discoveries, Armor, And Recovery Rewards

**Status:** Proposed work package. M8-D1 reward/source identities and placements, M8-D3 fact/reveal mappings and discovery contracts, and M8-D4's no-portable-story-item direction are approved. Package-level integration, permitted drop tuning, and qualification remain open; no implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate M3/M4/M5 source owners at package entry.

## Goal

Connect real Floor-IV reward sources to existing permanent-discovery claims, M5 armor ownership, and M2 recovery-item ownership, preserving atomic settlement and reload behavior.

## Approval Boundary

**Already-approved inputs:** use M3's one-time source-ID and active-party-only target contract; the three discovery reward types/values (+5 max HP, +5 max Mana, +3 GP), 10% base search chance with existing Intuition adjustment, and existing per-run search/retry semantics; M2's secured/carried/death-loss semantics; M5's armor identity/security/atomic transaction contracts; and M8-D4's exclusion of portable story-critical quest items.

**Already approved:** discovery IDs/placements, all other M8 reward/source identities and their effects/relationships, the four M8-D3 fact IDs/reveal mappings, discovery reward values, 10% base chance, and Intuition/retry contracts. **Package review remains:** live service integration and only the tunable ordinary-drop probabilities/quantities identified in the parent. Fixed discovery rewards and explicit first-clear effects are not balance variables.

## Scope

- Generalize the Floor-II-specific search/discovery and armor-reward paths only for the Floor-IV sources approved at Gate 0.
- Use the approved discovery reward contracts through M3's source-ID, active-party, and one-time claim boundary: `ancient_well_floor4_01` at `floor_four_rest_midpoint` grants Ancient Well +5 max HP; `forgotten_altar_floor4_01` at `floor_four_rest_pre_boss` grants +5 max Mana; `spirit_relic_floor5_01` at `floor_five_rest_midpoint` grants +3 GP.
- Use a 1,000-bps base search chance with the existing Intuition adjustment and preserve existing per-run search/retry behavior. Resolve outcomes at the authoritative event boundary and persist the outcome before presentation; do not adjust the existing Intuition curve.
- M8.4 owns the Spirit Relic's reward definition and claim-compatible source data; M8.7 owns placing it at `floor_five_rest_midpoint`. No Floor-V route is added here.
- Connect the manifest's Floor-IV armor and Healing Potion sources to an authoritative genuine-victory boundary. Keep armor unsecured until the existing safe securing boundary and use M2 carried/secured semantics for Recovery.
- Preserve source outcome immutability, selected Drifter targeting, cap cancel/consume rules, and transaction atomicity.

## Exclusions And Handoff

No retuning of existing discovery sources, new permanent reward type, party-wide effect, vendor acquisition path, expedition report or Floor-V route. Portable story-critical quest items are excluded; ordinary inventory retains its existing M2 loss/persistence rules. M8.3 provides the Floor-IV nodes; M8.5 consumes legitimate Equipment/Recovery sources; M8.7 owns any approved Spirit Relic placement.

## Ownership And Migration

Revalidate `root/src/app/game/run_events.py`, `permanent_discovery.py`, `equipment.py`, `overworld_session.py`, and `root/src/app/persistence/save_document.py`. Use M3's durable claim owner and M5's `EquipmentInstance`/reward evidence. Any schema extension starts from the actual accepted schema at implementation entry, preserves older save and immutable remote-history semantics, and cannot rewrite generation evidence when armor becomes secured.

M8.4 qualifies the approved Spirit Relic claim independently: exactly +3 GP to one eligible active Drifter, once across retry and reload. Record the live Floor V search as deferred to M8.7.

## Tests, Package Gates, And Qualification History

Prove actual battle-path armor acquisition, Rest securing, save/reload/next victory; exact item identity and quantity; recovery through death, extraction and safe return; discovery search persistence and no reroll; first/second active target; inactive target rejection; cap cancel/consume; duplicate claim; failed persistence with no reward/claim divergence; legacy migration; and both clients.

- **Gate A, plan approval:** Open; review the service integration, candidate-state/persistence boundaries, allowed ordinary-drop tuning, and focused test plan. M8-D1/D3 product mappings and fixed rewards are approved and must not be reopened.
- **Gate B, implementation and focused tests:** Not started; source/effect/transaction red/green coverage.
- **Gate C, exact-SHA qualification and closure:** Not run; root/web, content, compile/build, browser, PostgreSQL/migration/Alembic and pinned MicroPython.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Not implemented | Not run | Not run | Pending | Open |

Independent review and hosted results are required for closure.


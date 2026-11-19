# M8.4: Permanent Discoveries, Armor, And Recovery Rewards

**Status:** Proposed work package. M8-D1, M8-D3, and M8-D4 are pending; no implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate M3/M4/M5 source owners at package entry.

## Goal

Connect real Floor-IV reward sources to existing permanent-discovery claims, M5 armor ownership, and M2 recovery-item ownership, preserving atomic settlement and reload behavior.

## Approval Boundary

**Already-approved inputs:** use M3's one-time source-ID and active-party-only target contract, M2's secured/carried/death-loss semantics, and M5's armor identity/security/atomic transaction contracts.

**Still pending:** M8-D1, M8-D3 (including search rates/reveal sources), and M8-D4 (no portable key or an explicitly reviewed item policy). The proposed +5 HP, +5 Mana, and +3 GP values reuse existing M3 reward types; their M8 source placement remains pending approval.

## Scope

- Generalize the Floor-II-specific search/discovery and armor-reward paths only for the Floor-IV sources approved at Gate 0.
- Register `ancient_well_floor4_01` (+5 max HP), `forgotten_altar_floor4_01` (+5 max Mana), and `spirit_relic_floor5_01` (+3 GP) through the existing M3 source-ID/active-party/one-time claim contract. Proposed 1,000-bps base search rates remain subject to M8-D3 approval.
- M8.4 owns the Spirit Relic's reward definition and claim-compatible source data; M8.7 owns placing it at `floor_five_rest_midpoint`. No Floor-V route is added here.
- Connect the manifest's Floor-IV armor and Healing Potion sources to an authoritative genuine-victory boundary. Keep armor unsecured until the existing safe securing boundary and use M2 carried/secured semantics for Recovery.
- Preserve source outcome immutability, selected Drifter targeting, cap cancel/consume rules, and transaction atomicity.

## Exclusions And Handoff

No discovery probability retuning, new permanent reward type, party-wide effect, vendor acquisition path, expedition report or Floor-V route. M8.3 provides the live Floor-IV encounters/Rest nodes; M8.5 consumes the legitimate Equipment/Recovery sources; M8.7 places the already-authored Spirit Relic source.

## Ownership And Migration

Revalidate `root/src/app/game/run_events.py`, `permanent_discovery.py`, `equipment.py`, `overworld_session.py`, and `root/src/app/persistence/save_document.py`. Use M3's durable claim owner and M5's `EquipmentInstance`/reward evidence. Any schema extension starts from the actual accepted schema at implementation entry, preserves older save and immutable remote-history semantics, and cannot rewrite generation evidence when armor becomes secured.

M8.4 qualifies the proposed Spirit Relic claim independently: exactly +3 GP to one eligible active Drifter, once across retry and reload. Record the live Floor V search as deferred to M8.7.

## Tests, Package Gates, And Qualification History

Prove actual battle-path armor acquisition, Rest securing, save/reload/next victory; exact item identity and quantity; recovery through death, extraction and safe return; discovery search persistence and no reroll; first/second active target; inactive target rejection; cap cancel/consume; duplicate claim; failed persistence with no reward/claim divergence; legacy migration; and both clients.

- **Gate A, plan approval:** Open; resolve M8-D1/D3/D4 and authored source placement.
- **Gate B, implementation and focused tests:** Not started; source/effect/transaction red/green coverage.
- **Gate C, exact-SHA qualification and closure:** Not run; root/web, content, compile/build, browser, PostgreSQL/migration/Alembic and pinned MicroPython.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Not implemented | Not run | Not run | Pending | Open |

Independent review and hosted results are required for closure.


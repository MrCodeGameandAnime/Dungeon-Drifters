# M8.4: Permanent Discoveries, Armor, And Recovery Rewards

**Status:** CLOSED AND SEALED at `0a73019f9acdfcdbad4c3f2d910c212e38ddc154`. Exact-SHA hosted CI [45625705219](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/45625705219) passed Tests and Profile Service (PostgreSQL); the complete correction diff passed adversarial review with no outstanding findings.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Implementation baseline:** M8.3 sealed at `af156e8e1d3d9c331a5f4ce6a449530e18ebf099`, runtime/disk schema 27. M8.4 adds schema 28 for fixed-item reward evidence while preserving schema-27 payloads as immutable history.

## Goal

Connect real Floor-IV reward sources to existing permanent-discovery claims, M5 armor ownership, and M2 recovery-item ownership, preserving atomic settlement and reload behavior.

## Approval Boundary

**Approved inputs:** use M3's one-time source-ID and active-party-only target contract; the three discovery reward types/values (+5 max HP, +5 max Mana, +3 GP), 10% base search chance with existing Intuition adjustment, and existing per-run search/retry semantics; M2's secured/carried/death-loss semantics; M5's armor identity/security/atomic transaction contracts; and M8-D4's exclusion of portable story-critical quest items. Discovery IDs/placements, M8 reward/source identities and effects, M8-D3 fact mappings, fixed discovery rewards, and first-clear effects are approved and are not reopened here.

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

Use M3's durable claim owner and M5's `EquipmentInstance`/reward evidence. Schema 28 adds the fixed-item reward event and encounter source evidence; schema-27 saves remain strictly validated and immutable in remote history, and migration preserves their existing Floor-IV state. Do not rewrite armor generation evidence when security ownership changes.

M8.4 qualifies the approved Spirit Relic claim independently: exactly +3 GP to one eligible active Drifter, once across retry and reload. Record the live Floor V search as deferred to M8.7.

## Tests And Qualification

Qualification covers actual battle-path armor acquisition, Rest securing, save/reload/next victory; exact item identity and quantity; recovery through death, extraction and safe return; discovery search persistence and no reroll; first/second active target; inactive target rejection; cap cancel/consume; duplicate claim; failed persistence with no reward/claim divergence; legacy migration; and both clients.

The adversarial-review revision rejects M8.4 Floor-IV/V discovery claims, discovered-source records, and search evidence when validating pre-M8.4 schemas. Negative cases cover all three evidence forms through historical-profile and migration validation; legitimate schema-27 Floor-IV saves remain immutable inputs and migrate to schema 28.

The built-browser journey verifies Encounter 08's single authored `field_chest` armor instance and single Healing Potion reward, their unsecured outing ownership, armor security at the pre-boss Rest, reward evidence after reload, and nonduplicating final settlement. Separate real-runtime browser saves deterministically claim the Ancient Well (+5 max HP) and Forgotten Altar (+5 max Mana), target an active Drifter, preserve the other three Drifters, survive reload, and are not reoffered.

Local revision qualification: root suite 2,586 passed; web suite 95 passed; authored-content validation, compilation, browser build (200 runtime files), and full Playwright smoke passed. The pinned MicroPython v1.29.0 matrix passed native and forced-overlay CPython, default MicroPython, and semantic parity; 1408 KiB was stable (3/3) and 1216 KiB was confirmed memory-limited (3/3). Exact-SHA hosted Tests and PostgreSQL qualification is pending for this revision.


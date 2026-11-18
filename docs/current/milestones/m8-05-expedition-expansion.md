# M8.5: Expedition Expansion

**Status:** Proposed work package. M8-D1, M8-D3, and M8-D5 remain pending; no implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate current M6/M8 state owners at package entry.

## Goal

Extend M6's passive, timer-based, exactly-once report contract to approved completed M8 floors and eligible reward categories without adding simulated expedition gameplay.

## Scope

- Extend completed-floor eligibility to Floor IV and later Floor V only after its approved completion event. Preserve 100 energy, launch cost, 20-minute elapsed timer, offline/rollback protection and no-energy dungeon gameplay.
- Add the parent report IDs: Floor-IV Material, Equipment, Recovery, Scouting, Story and Elite; Floor-V Material. Categories without an eligible authored source stay unavailable with an explanation.
- Freeze report outcomes at launch. Equipment reports carry/reference the complete unique `EquipmentInstance`; stack rewards use legitimate floor source IDs; Scouting/Story effects are applied once at Hub claim.
- Use the approved floor-eligible material and source matrix; no expedition-exclusive item or invented content.
- Preserve pair assignment rules, Floor-III launch restriction, M4 temporary Floor-II helper exception only, and no assignment participant in a general battle.

## Exclusions And Handoff

No new energy economics, expedition combat, M6-D6 general full-party event redesign, Floor-V reunion deployment, or story scene authoring. M8.1 provides clear/fact owners; M8.3/8.8 provide completion and reward sources; M8.4 provides armor/recovery sources; M8.6 consumes the Story result. M8.7/M8.8 must obey the assignment restrictions approved under D5.

## Ownership And Persistence

Current owners to revalidate: `root/src/app/game/expeditions.py`, `expedition_state.py`, `party_state.py`, report claim/session/presenter flow, and `root/src/app/persistence/save_document.py`. Current reports support XP and stackable items; new frozen outcome types require validated ownership and a migration from the actual schema. Do not store duplicated client-side results or reroll on reload.

## Tests And Closure

Cover each category's availability by destination/source, frozen result, timer completion and incompletion, outing termination, launch/save failure, stale/duplicate launch, one-time claim, reload/retry, unique equipment identity, floor-grade provenance, scouting/story fact adoption, and no energy effect on ordinary play. Run root/web, content/build, browser journeys, PostgreSQL/migration/Alembic and pinned MicroPython exact-SHA qualification. Record independent review, CI URL and closure evidence.


# M8.9: Region And Enemy Visual Presentation

**Status:** D6's limited static-asset scope is approved. Package planning and implementation remain open; no implementation is authorized by this document update.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate asset pipeline, client surfaces and content IDs at package entry.

## Goal

Integrate the eight approved static visuals into existing destination, battle-semantic and inspection presentation. Asset production/delivery is separate from this package's live integration. Preserve the terminal experience and Python-authoritative combat behavior. This package does not create a combat renderer.

## Approved Scope

M8-D6 approves exactly these asset IDs and categories:

| Asset ID | Category | Intended content association |
| --- | --- | --- |
| `m8_art_drowned_reliquary` | Region 1 destination illustration | Drowned Reliquary; confirm its stable content ID in the detailed D1 manifest. |
| `m8_art_ashen_vault` | Region 1 destination illustration | Ashen Vault; confirm its stable content ID in the detailed D1 manifest. |
| `m8_portrait_reliquary_sentinel` | Ordinary-enemy portrait | Proposed `reliquary_sentinel`; confirm identity and ID under D1. |
| `m8_portrait_brine_oracle` | Ordinary-enemy portrait | Proposed `brine_oracle`; confirm identity and ID under D1. |
| `m8_portrait_drowned_stalker` | Ordinary-enemy portrait | Proposed `drowned_stalker`; confirm identity and ID under D1. |
| `m8_portrait_ashbound_hound` | Ordinary-enemy portrait | Proposed `ashbound_hound`; confirm identity and ID under D1. |
| `m8_portrait_tidebound_curator` | Boss portrait | Proposed `tidebound_curator`; confirm identity and ID under D1. |
| `m8_portrait_ashen_regent` | Boss portrait | Proposed `ashen_regent`; confirm identity and ID under D1. |

The eight asset IDs/categories are approved. The specific enemy/boss associations remain conditional on D1 finalizing the finite content manifest. Do not treat this asset approval as approval of proposed enemy identities, compositions, or combat values.

## Ownership And Integration

Keep asset production and delivery distinct from M8.9's live integration and qualification. Delivered assets require stable approved IDs, source/provenance, dimensions, accessible descriptions, responsive use, and an approved fallback. M8.9 associates the delivered assets with the finalized content catalog and integrates them into existing client surfaces; it does not silently create a new asset pipeline.

- Region illustrations appear in existing destination/region presentation.
- Enemy and boss portraits may appear in existing semantic battle and inspection views.
- Existing terminal presentation remains usable without image rendering.
- Existing Drifter sprites remain unchanged. No redesign, replacement, migration, or sprite-in-combat work is included.

## Exclusions

No new 2D combat renderer, animation engine, battlefield/staging system, formations, hazard mechanics, boss phases, damage/status/targeting/turn-resolution changes, M7 changes, or new sprite-in-combat/animation asset pipeline. Existing supported enemy capabilities may be used only when separately specified in approved content. Full future 2D RPG presentation remains deferred to an unnumbered future milestone and is not M8 work.

## Dependencies And Qualification

M8-D6 scope is approved. M8.9 still depends on asset production/delivery and final D1 content IDs/associations. It may proceed alongside other M8 implementation after those associations are confirmed, and must integrate before M8.10.

Qualification must verify all eight assets or approved readable fallbacks through their actual user-visible destination, battle-semantic, or inspection surfaces. Check catalog references, dimensions, crop/responsive behavior, accessible descriptions, and browser rendering; verify terminal functionality and client semantic parity. No graphical combat or animation qualification is required.

**Persistence impact:** none for static assets. If asset references alter serialized content identities, stop and review that scope separately.

## Package Gates And Qualification History

- **Gate A, plan approval:** Open; confirm final D1 content associations, production/delivery ownership, asset specifications, and the focused integration matrix. D6 itself is approved and must not be reopened.
- **Gate B, asset integration and focused checks:** Not started; verify catalog references, fallbacks, responsive/accessibility behavior, and actual client presentation.
- **Gate C, exact-SHA qualification and closure:** Not run; run relevant content/build/browser checks and hosted workflow. No MicroPython rerun for asset-only changes unless shared runtime code is touched.

| Implementation SHA | Hosted CI URL/results | Asset/build evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Not implemented | Not run | Not run | Pending | Open |

Record the delivered asset manifest, final D1 associations, reviewer disposition, CI URL and closure here and in the parent.

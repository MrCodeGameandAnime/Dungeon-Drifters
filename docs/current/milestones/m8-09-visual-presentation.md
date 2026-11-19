# M8.9: Region And Enemy Visual Presentation

**Status:** Proposed work package. M8-D1's finite content identity and M8-D6 are pending; regional architecture is approved, but no implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate asset pipeline and client sizes at package entry.

## Goal

Create and integrate the finite static art set for the proposed Region 1 destinations and enemies if approved, while retaining the existing semantic/text battle presentation.

## Approval Boundary

**Already-approved inputs:** Python remains authoritative for gameplay and clients remain projections/adapters; M7's shared combat model is unchanged.

**Still pending:** M8-D1's finite destination/enemy content identity and M8-D6 visual scope/fallback requirements. The eight listed assets are proposed IDs, not a commission or an approved asset style.

## Scope

- Region art for the two M8 destinations in Region 1: `m8_art_drowned_reliquary`, `m8_art_ashen_vault`. Region 2 receives no art/content package in M8; its future visual identity remains open.
- Portraits: `m8_portrait_reliquary_sentinel`, `m8_portrait_brine_oracle`, `m8_portrait_drowned_stalker`, `m8_portrait_ashbound_hound`, `m8_portrait_tidebound_curator`, `m8_portrait_ashen_regent`.
- Record asset path, dimensions, alt text, source/license provenance, crop behavior, and readable fallback. Associate each asset with its stable content ID.
- Verify desktop and narrow/mobile layouts, contrast/readability, and missing-asset behavior in browser and terminal-compatible presentation.

## Exclusions And Dependencies

No new combat renderer, animation engine, 3D scene, gameplay logic, external payment or unsupported asset pipeline. Begin only after M8-D1/D6 and the stable IDs are approved. This can run in parallel with M8.2–M8.8 after IDs stabilize; M8.9 qualifies final integration before M8.10.

**Persistence impact:** none for an asset-only implementation. If asset references alter serialized content identities, stop and review that scope separately.

M8.9 can record production evidence once manifest IDs and visual scope are approved. Close only after checking each asset or approved fallback through its actual region or encounter, including the reunion boss.

## Package Gates And Qualification History

Use existing asset/content checks and browser build. Test all eight ID references resolve, no blank primary media, alt text/fallbacks are present, intended crops render at desktop/mobile sizes, and non-visual clients remain functional.

- **Gate A, plan approval:** Open; resolve M8-D1/D6 and approve stable asset IDs/style/source requirements.
- **Gate B, asset integration and focused checks:** Not started; content-reference, fallback and responsive rendering checks.
- **Gate C, exact-SHA qualification and closure:** Not run; relevant root/web/build/content checks and hosted workflow. No MicroPython rerun for asset-only changes unless shared runtime code is touched.

| Implementation SHA | Hosted CI URL/results | Asset/build evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Not implemented | Not run | Not run | Pending | Open |

Record reviewer disposition, final asset manifest, CI URL and closure here and in the parent.


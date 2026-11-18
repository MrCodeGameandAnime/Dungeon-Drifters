# M8.9: Region And Enemy Visual Presentation

**Status:** Proposed work package. M8-D1 and M8-D6 are pending; no implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate asset pipeline and client sizes at package entry.

## Goal

Create and integrate the finite static art set for the approved regions and enemies while retaining the existing semantic/text battle presentation.

## Scope

- Region art: `m8_art_drowned_reliquary`, `m8_art_ashen_vault`.
- Portraits: `m8_portrait_reliquary_sentinel`, `m8_portrait_brine_oracle`, `m8_portrait_drowned_stalker`, `m8_portrait_ashbound_hound`, `m8_portrait_tidebound_curator`, `m8_portrait_ashen_regent`.
- Record asset path, dimensions, alt text, source/license provenance, crop behavior, and readable fallback. Associate each asset with its stable content ID.
- Verify desktop and narrow/mobile layouts, contrast/readability, and missing-asset behavior in browser and terminal-compatible presentation.

## Exclusions And Dependencies

No new combat renderer, animation engine, 3D scene, gameplay logic, external payment or unsupported asset pipeline. Begin only after M8-D1/D6 and the stable IDs are approved. This can run in parallel with M8.2–M8.8 after IDs stabilize; final integration is included in M8.10.

## Tests And Closure

Use existing asset/content checks and browser build. Test all eight ID references resolve, no blank primary media, alt text/fallbacks are present, intended crops render at desktop/mobile sizes, and non-visual clients remain functional. Run relevant root/web/build/content checks and exact-SHA hosted workflow; record reviewer disposition, asset manifest, CI URL and closure here and in the parent. No MicroPython rerun is needed for asset-only changes unless shared runtime code is touched.


# M8.9: Region And Enemy Visual Presentation

**Status:** CLOSED AND SEALED at implementation SHA `4b37cbdb9aa581c8c34e47e3a2aeece7c9af11d2`. Independent implementation review passed with no blocking production defects. Exact-SHA hosted CI and the pinned MicroPython matrix passed.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `9b88a5e1c50bea18bf6c25a2ec177796da759dc1` (audited 2026-11-27). Hosted CI [45944167218](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/45944167218) passed both Tests and Profile Service (PostgreSQL).

## Goal

Deliver the eight approved static visuals, then integrate them into existing destination and battle-semantic presentation. Asset delivery (Gate A prerequisite) and live integration (Gate B) are distinct stages within this package. Preserve the terminal experience and Python-authoritative combat behavior. This package does not create a combat renderer.

## Approved Scope

M8-D6 approves exactly these asset IDs and categories:

| Asset ID | Category | Intended content association |
| --- | --- | --- |
| `m8_art_drowned_reliquary` | Region 1 destination illustration | `drowned_reliquary`. |
| `m8_art_ashen_vault` | Region 1 destination illustration | `ashen_vault`. |
| `m8_portrait_reliquary_sentinel` | Ordinary-enemy portrait | Approved `reliquary_sentinel` identity. |
| `m8_portrait_brine_oracle` | Ordinary-enemy portrait | Approved `brine_oracle` identity. |
| `m8_portrait_drowned_stalker` | Ordinary-enemy portrait | Approved `drowned_stalker` identity. |
| `m8_portrait_ashbound_hound` | Ordinary-enemy portrait | Approved `ashbound_hound` identity. |
| `m8_portrait_tidebound_curator` | Boss portrait | Approved `tidebound_curator` identity. |
| `m8_portrait_ashen_regent` | Boss portrait | Approved `ashen_regent` identity. |

The eight asset IDs/categories and their D1 content associations are approved. Asset approval does not settle numerical combat values or asset-production specifications.

## Gate A Review And Authorization

The independent Gate A review disposition is **PASS - recommended for owner approval** at the audit baseline above. The owner approved Gate A on 2026-11-27. The required eight assets have since been delivered, and the authorized Gate B integration is implemented in this work package.

The audit revalidated the current browser build and presentation seams. Gate B adds renderer-neutral visual IDs to destination/enemy presentation views, maps those IDs from canonical Python content identities, and resolves them in the browser only. The explicit site builder packages each approved asset. No visual metadata is persisted; terminal views remain text-first and fully functional.

## Asset Delivery Manifest

All eight approved static assets are delivered. They were generated specifically for M8.9 and optimized from original PNG masters to WebP; no third-party visual sources or reference artwork were used. The fallback preserves semantic labels/details and interactions, removes only an unavailable image, and retains the existing text-first terminal experience.

| Stable asset ID | Associated content ID | Repository path | Format / dimensions | Source / provenance | Accessible description (`alt`) | Responsive crop / scaling | Readable fallback | Delivery status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `m8_art_drowned_reliquary` | `drowned_reliquary` | `root/res/m8/regions/drowned-reliquary.webp` | WebP, 1536x1024, 3:2 | OpenAI ImageGen, 2026-11-27; generated PNG master, optimized with FFmpeg to WebP quality 90; no external source. | Ruined pale-stone sanctuary partly flooded at low tide, with arches reflected in coastal water under a storm-gray sky. | Fluid 3:2 image, max width 22rem, centered `object-fit: cover`. | Destination label, knowledge, availability and controls remain visible; failed image is removed. | Delivered and integrated |
| `m8_art_ashen_vault` | `ashen_vault` | `root/res/m8/regions/ashen-vault.webp` | WebP, 1536x1024, 3:2 | OpenAI ImageGen, 2026-11-27; generated PNG master, optimized with FFmpeg to WebP quality 90; no external source. | Monumental stone doors set into an ash-coated cliff above a pale, windswept plain. | Fluid 3:2 image, max width 22rem, centered `object-fit: cover`. | Destination label, knowledge, availability and controls remain visible; failed image is removed. | Delivered and integrated |
| `m8_portrait_reliquary_sentinel` | `reliquary_sentinel` | `root/res/m8/portraits/reliquary-sentinel.webp` | WebP, 1024x1536, 2:3 | OpenAI ImageGen, 2026-11-27; generated PNG master, optimized with FFmpeg to WebP quality 90; no external source. | Broad salt-worn armored guardian with a heavy shield in a flooded stone hall. | Fixed 3.5rem x 5.25rem 2:3 crop, centered `object-fit: cover`. | Enemy name, HP, temporary labels and battle controls remain visible; failed image is removed. | Delivered and integrated |
| `m8_portrait_brine_oracle` | `brine_oracle` | `root/res/m8/portraits/brine-oracle.webp` | WebP, 1024x1536, 2:3 | OpenAI ImageGen, 2026-11-27; generated PNG master, optimized with FFmpeg to WebP quality 90; no external source. | Veiled figure in salt-crusted gray-green robes holding a small sphere of water before flooded arches. | Fixed 3.5rem x 5.25rem 2:3 crop, centered `object-fit: cover`. | Enemy name, HP, temporary labels and battle controls remain visible; failed image is removed. | Delivered and integrated |
| `m8_portrait_drowned_stalker` | `drowned_stalker` | `root/res/m8/portraits/drowned-stalker.webp` | WebP, 1024x1536, 2:3 | OpenAI ImageGen, 2026-11-27; generated PNG master, optimized with FFmpeg to WebP quality 90; no external source. | Lean hooded hunter in waterlogged wraps standing in a submerged stone corridor. | Fixed 3.5rem x 5.25rem 2:3 crop, centered `object-fit: cover`. | Enemy name, HP, temporary labels and battle controls remain visible; failed image is removed. | Delivered and integrated |
| `m8_portrait_ashbound_hound` | `ashbound_hound` | `root/res/m8/portraits/ashbound-hound.webp` | WebP, 1024x1536, 2:3 | OpenAI ImageGen, 2026-11-27; generated PNG master, optimized with FFmpeg to WebP quality 90; no external source. | Charcoal-gray hound dusted with ash, shown against dark stone. | Fixed 3.5rem x 5.25rem 2:3 crop, centered `object-fit: cover`. | Enemy name, HP, temporary labels and battle controls remain visible; failed image is removed. | Delivered and integrated |
| `m8_portrait_tidebound_curator` | `tidebound_curator` | `root/res/m8/portraits/tidebound-curator.webp` | WebP, 1024x1536, 2:3 | OpenAI ImageGen, 2026-11-27; generated PNG master, optimized with FFmpeg to WebP quality 90; no external source. | Ancient teal-armored keeper with a sea-worn bronze half-mask and closed book in flooded arches. | Fixed 3.5rem x 5.25rem 2:3 crop, centered `object-fit: cover`. | Boss name, HP, temporary labels and battle controls remain visible; failed image is removed. | Delivered and integrated |
| `m8_portrait_ashen_regent` | `ashen_regent` | `root/res/m8/portraits/ashen-regent.webp` | WebP, 1024x1536, 2:3 | OpenAI ImageGen, 2026-11-27; generated PNG master, optimized with FFmpeg to WebP quality 90; no external source. | Regal figure in dark ash-dusted armor and ridged helm against monumental stone. | Fixed 3.5rem x 5.25rem 2:3 crop, centered `object-fit: cover`. | Boss name, HP, temporary labels and battle controls remain visible; failed image is removed. | Delivered and integrated |

## Ownership And Integration

Keep asset provenance/delivery distinct from live integration. M8.9 completes both stages in the approved Gate A-to-B sequence. Delivered assets require stable approved IDs, source/provenance, dimensions, accessible descriptions, responsive use, and a readable fallback; no new asset pipeline is introduced.

- Region illustrations appear in existing destination/region presentation.
- Enemy and boss portraits may appear in existing semantic battle and inspection views.
- Existing terminal presentation remains usable without image rendering.
- Existing Drifter sprites remain unchanged. No redesign, replacement, migration, or sprite-in-combat work is included.

**Gate B implementation:** `visual_assets.py` maps canonical destination/enemy IDs to the stable approved IDs. Existing Python presentation views carry only the optional visual ID. The browser maps IDs to relative asset URLs and `alt` descriptions, renders destination art and semantic enemy portraits, and removes only a failed image while preserving the existing button/card. `build_browser_site.py` explicitly stages all eight files under `assets/m8/`. No persistence or schema changes were made. No current inspection view was added or redesigned.

## Exclusions

No new 2D combat renderer, animation engine, battlefield/staging system, formations, hazard mechanics, boss phases, damage/status/targeting/turn-resolution changes, M7 changes, or new sprite-in-combat/animation asset pipeline. Existing supported enemy capabilities may be used only when separately specified in approved content. Full future 2D RPG presentation remains deferred to an unnumbered future milestone and is not M8 work.

## Dependencies And Qualification

M8-D6 scope and D1 content associations are approved. Gate A and asset delivery are complete; Gate B is integrated. Gate C exact-SHA hosted, review and pinned-runtime evidence passed; M8.9 is CLOSED AND SEALED before M8.10.

Qualification must verify all eight assets or approved readable fallbacks through their actual user-visible destination and battle-semantic surfaces. Check catalog references, dimensions, crop/responsive behavior, accessible descriptions, browser packaging/rendering, terminal functionality and semantic parity. The local full Playwright smoke verifies each asset loads during the M8 campaign route, tests a controlled unavailable-image response and retained destination action, and checks 390px mobile crops for both a destination image and an enemy portrait. No graphical combat or animation qualification is required.

**Persistence impact:** none for static assets. If asset references alter serialized content identities, stop and review that scope separately.

## Package Gates And Qualification History

- **Gate A, plan approval:** Approved by owner on 2026-11-27 after independent PASS. D1 associations and D6 scope remain authoritative.
- **Asset delivery:** Complete; all eight manifest rows include paths, formats/dimensions, provenance, descriptions, responsive behavior and fallback behavior.
- **Gate B, asset integration and focused checks:** Implemented and reviewed. Python associations, browser rendering and explicit packaging are covered by focused tests and cumulative Playwright smoke.
- **Gate C, exact-SHA qualification and closure:** Exact-SHA hosted CI [46080129038](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/46080129038) passed both jobs on implementation SHA `4b37cbdb9aa581c8c34e47e3a2aeece7c9af11d2`: 2,732 root tests, 97 web tests, content validation, compilation, browser build (213 runtime files), cumulative Playwright smoke, M8.9 static visual marker, PostgreSQL integration, migration-from-zero and Alembic parity. The exact pinned MicroPython v1.29.0 Windows executable (488,960 bytes; SHA-256 `6345EFFEE0DE9B5F8B1F7291C12F464D719900E5B1B703708B4591D22D78FDEA`) passed native CPython, forced-overlay CPython, semantic parity, 1472 KiB stable 3/3 and 1216 KiB expected-limit 3/3. Historical results from the alternate 486,912-byte artifact remain supplemental only.

| Implementation SHA | Hosted CI URL/results | Asset/build evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| `4b37cbdb9aa581c8c34e47e3a2aeece7c9af11d2` | [46080129038](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/46080129038): both hosted jobs passed | 8/8 delivered; 213 Python runtime files; cumulative browser smoke passed; exact pinned matrix passed at both approved heap profiles | Independent review PASS; owner directed sealing after pinned qualification | CLOSED AND SEALED |

M8.9 closure is recorded here and in the parent. M8.10 owns the remaining cumulative campaign qualification.

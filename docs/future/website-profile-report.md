# Dungeon Drifters Website Profile

**Review date:** 2026-09-23  
**Repository:** Dungeon Drifters  
**Published site:** https://mrcodegameandanime.github.io/Dungeon-Drifters/  
**Published Play page:** https://mrcodegameandanime.github.io/Dungeon-Drifters/play/  
**Repository revision inspected:** db25f83 (mobile Character)  
**Working-tree note:** The profiling run also saw pre-existing uncommitted changes in root/web/pyd4/styles.css and root/web_tests/browser_smoke.mjs. This report did not modify those files.

## Executive Summary

The site has a strong visual identity, a clear information architecture, and a technically sound static deployment. The normal website is structurally friendly to search engines at the page level: every tested page has a title, description, language declaration, semantic landmarks, a usable heading structure, and complete image alternative text. The Play page is also quick to render as an HTML shell and reached a usable Python runtime reliably in the measured public run.

The main weakness is payload size rather than initial server-side latency. The normal home page transferred approximately 9.55 MB on a fresh desktop load, primarily because its hero artwork and four 1.2-1.55 MB Drifter sprites are large PNGs and the four card sprites are eager-loaded. The Play page transferred approximately 6.90 MB before Start and approximately 13.03 MB by the time Drifter selection was ready. Most of that cost is Pyodide and raster art, not HTML, CSS, or JavaScript.

SEO fundamentals are present but incomplete. The normal pages have descriptions, but the site has no observed canonical links, robots.txt, sitemap.xml, Open Graph metadata, Twitter metadata, or structured data. The Play page has no description, canonical, or robots metadata. These omissions do not prevent indexing, but they reduce control over search previews, duplicate URL handling, and social sharing.

The highest-return work is asset optimization and delivery strategy. The site does not need a visual redesign for performance reasons. It needs smaller responsive image variants, explicit image dimensions, more deliberate lazy loading, and a small metadata/semantic cleanup pass.

## Overall Assessment

| Area | Assessment | Main reason |
| --- | --- | --- |
| Speed | Good shell speed, heavy payload | Static HTML and CSS render quickly, but large images and Pyodide dominate transfer and startup |
| SEO | Good baseline, incomplete control layer | Titles, descriptions, landmarks, and image text alternatives are present; canonical, social, structured, and crawler files are absent |
| Appearance | Strong and coherent | Distinctive fantasy presentation, focused Play surface, responsive phase layouts, and no horizontal overflow observed |
| Size | Main optimization opportunity | Home and Play are image/runtime-heavy; text assets are already comparatively small |
| Reliability | Good in the measured smoke path | Public Play reached runtime-ready and Drifter selection with no console or page errors |

## Scope And Method

This was an engineering profile rather than a Lighthouse scorecard. Measurements were taken against both the published GitHub Pages site and the local generated Play site.

The review covered:

- The public home page and all published normal content pages.
- The public Play page before Start and through the Drifter selection screen.
- The local Play build at http://127.0.0.1:8770/.
- Fresh Chromium contexts with cache disabled by context creation and no artificial network throttling.
- Desktop viewport testing at 1440 by 900.
- Mobile-layout checks at 390 by 844 and short landscape-style viewports.
- DOM audits for titles, descriptions, headings, landmarks, image alternatives, image loading behavior, and overflow.
- Static file sizes, published response sizes, cache headers, and the generated Play artifact.

The timing values below are directional production measurements, not guarantees for every device or network. Pyodide startup is especially sensitive to device speed, browser cache state, and network conditions.

## 1. Speed Profile

### Normal Website Home Page

Public URL:
https://mrcodegameandanime.github.io/Dungeon-Drifters/

| Measurement | Result |
| --- | ---: |
| HTTP status | 200 |
| Wall-clock page load in fresh Chromium | 666 ms |
| First Contentful Paint | 464 ms |
| Successful responses observed | 11 |
| Response bytes observed | approximately 9,550,321 |
| Horizontal overflow | None observed |

The page shell is fast. The transfer is heavy because the initial page requests the hero image and all four Drifter sprites. The largest observed resources were:

| Resource | Bytes |
| --- | ---: |
| Dungeon Drifters Heros.png | 4,037,412 |
| Azhvielle sprite | 1,553,684 |
| Joruun sprite | 1,329,494 |
| Branoc sprite | 1,302,805 |
| Zhaivra sprite | 1,179,011 |
| Three screenshot assets combined | 140,795 |
| Site CSS response | approximately 4,266 compressed bytes |
| Site JavaScript response | approximately 579 compressed bytes |

The raw source sizes of the normal website CSS and JavaScript are only 18,870 and 1,903 bytes respectively. They are not the performance bottleneck.

### Public Play Page

Public URL:
https://mrcodegameandanime.github.io/Dungeon-Drifters/play/

Before pressing Start:

| Measurement | Result |
| --- | ---: |
| HTTP status | 200 |
| Wall-clock load in fresh Chromium | 426 ms |
| First Contentful Paint | 312 ms |
| Response bytes observed | approximately 6,896,852 |
| Largest resource | Pyodide WebAssembly, 3,438,516 bytes |
| Second-largest resource | Python standard library ZIP, 2,505,313 bytes |
| Logo PNG | 896,210 bytes |

Through the runtime-ready state:

| Measurement | Result |
| --- | ---: |
| Python runtime ready | 5.064 seconds from navigation in the public run |
| Drifter selection visible after Start | 5.346 seconds from navigation |
| Response bytes observed | approximately 13,031,075 |
| Console errors | None observed |
| Page errors | None observed |

The Play page's initial HTML shell is fast. Its usable startup is dominated by downloading and initializing Pyodide. This is expected for a browser-hosted Python runtime and is much less likely to improve through normal HTML or CSS optimization than through caching and asset strategy.

### Local Play Build

The local generated site was served from root/web/dist using a simple local HTTP server. Local text responses are not compressed, so their byte totals should not be compared directly with the public compressed totals.

Observed local measurements:

| Measurement | Result |
| --- | ---: |
| Start button and Python-ready state | approximately 4.4-4.9 seconds |
| Drifter selection after Start | approximately 5.2 seconds |
| Runtime-ready response bytes | approximately 7,717,860 |
| Response bytes through selection | approximately 13,640,380 |
| Horizontal overflow | None observed |

### Caching And Delivery

Representative public responses returned Cache-Control max-age=600. That is a reasonable short cache for HTML, but it is conservative for immutable versioned assets such as Pyodide, sprites, logos, and icons. Public responses also exposed ETags.

Recommended delivery direction:

1. Keep HTML on a short revalidation policy so deployments appear promptly.
2. Give immutable hashed or versioned binaries a much longer cache lifetime.
3. Keep the Pyodide lock and runtime version pinned as they are now.
4. Confirm GitHub Pages compression and cache behavior after any asset pipeline change.

## 2. SEO Friendliness

### What Is Already Good

The normal published pages were checked for:

- HTTP 200 responses.
- Page-specific titles.
- Page-specific meta descriptions.
- lang=en on the document element.
- One main landmark, a header, a nav, and a footer.
- Complete image alt text.
- No empty links.
- No horizontal overflow.

The normal home page has a clear H1 of Dungeon Drifters. The character pages also have clear page-specific H1 headings:

- Ser Branoc
- Azhvielle
- Zhaivra Kelyth
- Joruun Veyr

The normal home page's current description is:

Dungeon Drifters is a character-driven fantasy RPG set in Ketlyv.

That is concise and relevant for a homepage search snippet.

### Metadata And Discoverability Gaps

No public robots.txt or sitemap.xml was observed in the root, site, or Play output. The normal pages also do not currently expose:

- rel=canonical links.
- Open Graph title, description, URL, or image metadata.
- Twitter card metadata.
- JSON-LD structured data.

The Play page has a title, but it does not expose a meta description, canonical URL, or social preview metadata.

These are not blockers for a small game site, but they are straightforward improvements:

| Priority | Recommendation | Benefit |
| --- | --- | --- |
| High | Add sitemap.xml for the normal public pages | Gives crawlers an explicit page inventory |
| High | Add robots.txt with the sitemap location | Makes crawl policy and discovery explicit |
| Medium | Add canonical links to every normal page | Prevents ambiguity if alternate URLs are introduced |
| Medium | Add Open Graph and Twitter metadata | Improves link previews in Discord, social sites, and messaging apps |
| Medium | Add JSON-LD for the game and website where the content is stable | Gives search engines structured context |
| Low | Decide explicitly whether the Play page should be indexable | The page is an interactive runtime surface rather than a content landing page |

### Heading And Landmark Notes

The normal gameplay page currently has two H1 elements:

- The road is a system.
- The surface journey, in motion.

That is visually understandable, but a single page-level H1 would be cleaner for search and assistive technology. One heading can become the H1 and the other can become an H2 without changing the visual design.

The Play page contains multiple mutually exclusive state headings in the DOM, including Dungeon Drifters, We could not start the game, and Choose your Drifter. The hidden states are not a major issue if they are correctly removed from the accessibility tree, but the page should ensure only the active state contributes meaningful heading structure.

The Play page currently has two main landmarks for its start screen and app shell. That can be acceptable for mutually exclusive application states, but a single stable main landmark with state-specific content would be simpler for crawlers and accessibility tools.

The Play utility buttons contain decorative images with empty alt text. The buttons should still have explicit accessible names even though the visible controls are icon-only. This is a small semantic issue with an easy fix.

### Image SEO And Layout Stability

The normal pages have complete alt text, which is a strong baseline. However, the image audit found:

- No width and height attributes on the checked images.
- No srcset or sizes attributes.
- The four homepage Drifter sprites are eager-loaded.

Adding intrinsic dimensions would reduce layout shift. Responsive image sources would reduce transfer on mobile and high-density screens. Lazy loading the below-fold character cards would reduce the normal homepage's initial payload, provided the currently visible hero artwork stays prioritized.

## 3. Appearance And Responsive Behavior

### Strengths

The visual system is consistent across the normal website and Play surface:

- The parchment, map, fantasy artwork, and dark game surface establish a clear identity.
- The Play page has moved toward a focused phase-driven layout instead of a persistent dashboard.
- The browser surface preserves the game progression flow while adapting terminal information for HTML.
- Desktop and mobile checks showed no horizontal overflow.
- The Drifter selection screen is visually legible and communicates the four choices clearly.
- The Character screen has a compact mobile presentation with readable stats and reachable navigation buttons.
- The normal website's navigation, content bands, and visual hierarchy are coherent.

The normal home page measured approximately 3,933 CSS pixels tall at 1440 by 900 and approximately 6,546 CSS pixels tall at 390 by 844. That is expected for a content-rich homepage and is separate from an overflow bug.

### Risks And Opportunities

The site is visually rich, but the same raster art that gives it identity also creates much of the payload. The most meaningful visual-performance improvements should preserve the artwork rather than remove it:

- Export the same artwork as WebP or AVIF with PNG fallback where transparency or compatibility requires it.
- Add appropriately sized mobile and desktop variants.
- Keep the hero's focal point stable when the viewport changes.
- Reserve image space with dimensions or aspect-ratio boxes.
- Avoid loading detailed below-fold art before it is needed.

The Play page's appearance is strongest when it presents one active game phase at a time. Future additions should preserve that rule, especially for Character, Skills, Weapon, and Equipment surfaces.

## 4. Size Profile

### Published Play Artifact

The committed Play tree was approximately 7,924,213 bytes on disk. The local generated dist tree was approximately 7,925,951 bytes. The main files were:

| File or asset | Bytes |
| --- | ---: |
| game/dd_runtime.zip | 505,550 |
| assets/dungeon-drifters-logo.png | 896,210 |
| assets/theme.m4a | 556,555 |
| assets/azhvielle.png | 1,553,684 |
| assets/branoc.png | 1,302,805 |
| assets/joruun.png | 1,329,494 |
| assets/zhaivra.png | 1,179,011 |
| js/pyd4.js | 30,396 |
| styles.css | 21,227 |
| python/dd_bridge.py | 4,947 |
| index.html | 8,427 |

The four character sprites total approximately 5.36 MB. The logo and music add approximately 1.45 MB. The game archive is relatively small compared with the Pyodide runtime downloaded from the pinned CDN.

### Normal Home Page

The normal home page's observed public transfer was approximately 9.55 MB. The hero image alone was approximately 4.04 MB, and the four eagerly loaded Drifter sprites totaled approximately 5.36 MB. This makes the home page image delivery the clearest size target.

### Size Priorities

1. Character sprites and hero image.
2. Pyodide WebAssembly and standard library on first Play use.
3. Logo and music assets on the Play start screen.
4. Duplicate or unnecessarily eager assets.
5. Text and CSS, which are already small.

## 5. Recommended Work

### High Priority

**Create an image delivery pipeline.** Produce WebP or AVIF variants for the hero and Drifter sprites, preserve PNG fallback where needed, and emit width-specific variants. This should be the largest reduction in both normal-site transfer and Play selection transfer.

**Add responsive image markup.** Use srcset and sizes for normal-site artwork. Add explicit width and height or aspect-ratio styling to prevent layout movement while images decode.

**Defer below-fold home assets.** Keep the visible hero prioritized, but lazy-load lower page screenshots, atlas previews, and character assets that are not initially visible.

**Add crawler and sharing metadata.** Add robots.txt, sitemap.xml, canonical links, Open Graph metadata, and a consistent description strategy to the normal pages.

### Medium Priority

**Improve Play semantics.** Add explicit names to icon-only utility buttons and ensure inactive start/error/selection states are hidden from the accessibility tree and heading outline.

**Simplify heading structure.** Reduce the normal gameplay page to one H1 followed by H2 sections.

**Use long-lived caching for immutable files.** Keep HTML short-lived, but cache versioned binaries, sprites, audio, and pinned runtime assets for much longer.

**Set performance budgets.** A practical first budget could be:

- Normal homepage initial transfer below 4 MB on desktop.
- Normal homepage initial transfer below 2 MB on mobile.
- Play shell HTML/CSS/JavaScript below 100 KB before runtime assets.
- Play first usable runtime below 6 seconds on a mid-range mobile device under a warm cache.

These should be measured as budgets, not treated as absolute pass/fail promises until real device data is collected.

### Low Priority

**Add production monitoring.** Capture real-user timings for first contentful paint, runtime-ready, and Drifter selection. Pyodide startup will vary enough by device that real-user data will be more useful than desktop-only lab measurements.

**Document the Play runtime cost.** A short note in the project documentation would set expectations that the first Play visit downloads a Python runtime and will be materially heavier than a normal content page.

## 6. Verification Summary

The profiling run verified:

- Public normal homepage returned HTTP 200.
- Public Play page returned HTTP 200.
- All eight checked normal pages returned HTTP 200.
- Public Play reached Python runtime-ready in approximately 5.064 seconds.
- Public Play reached Drifter selection in approximately 5.346 seconds.
- The bounded public Play run emitted no console errors or page errors.
- Normal and Play browser checks showed no horizontal overflow.
- Normal pages had titles, descriptions, language declarations, semantic landmarks, and complete image alternative text.
- Public cache headers exposed ETags and a ten-minute max-age on representative resources.

Existing repository verification from the surrounding UI work also recorded 49 web tests passing and 1,467 Python tests passing. Those figures are included as context from the current branch history, not as a replacement for rerunning the full suite after future changes.

## 7. Limitations

This review did not:

- Run a third-party Lighthouse or WebPageTest audit.
- Measure real Android hardware network timing.
- Perform a full accessibility audit with a screen reader.
- Compare multiple geographic GitHub Pages edge locations.
- Measure compressed transfer totals for every resource under every browser cache state.
- Change or commit product code.

The response-byte measurements are based on the resources observed by Chromium. Local totals include uncompressed text and therefore are not directly comparable with public compressed totals.

## Bottom Line

Dungeon Drifters is already visually distinctive and structurally healthy. The normal site is fast to paint but expensive to download, while the Play page is fast to shell-render but necessarily heavy at first runtime startup because of Pyodide. The most important improvement is not a new UI architecture: it is shrinking and prioritizing the existing artwork, then adding the small SEO and semantic metadata layer that the site currently lacks.

The site is in good shape for continued feature work. A focused asset pipeline plus sitemap, canonical, social metadata, and a few Play accessibility fixes would materially improve speed, discoverability, and polish without changing the game's presentation.

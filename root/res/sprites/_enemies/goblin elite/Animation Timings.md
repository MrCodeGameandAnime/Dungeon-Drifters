# Goblin Elite Animation Timings

Frames are numbered from 1 in reading order. Cell positions and pivots are in source pixels from the top left. Place the base pivot at the world-space ground point. Render all base cells at a common source scale. The ready silhouette is nominally 536 source pixels tall, compared with 480 for the Warrior and 432 for the standard Goblin.

| Asset | Frames | Grid | Cell size | Ground or effect pivot | Per-frame duration (ms) | Playback duration |
| --- | ---: | --- | --- | --- | --- | --- |
| [Combat Idle](base/Combat%20Idle.png) | 6 | 3 × 2 | 704 × 704 | (352, 612) | 220, 200, 160, 240, 160, 220 | 1,200 ms per loop |
| [Veteran Slash](base/Veteran%20Slash.png) | 6 | 3 × 2 | 896 × 896 | (448, 708) | 100, 120, 80, 60, 100, 140 | 600 ms |
| [Veteran Slash VFX](vfx/Veteran%20Slash.png) | 4 | 2 × 2 | 896 × 896 | (448, 708) | 40, 60, 60, 40 | 200 ms |
| [Butcher’s Advance](base/Butcher%E2%80%99s%20Advance.png) | 8 | 4 × 2 | 896 × 896 | (448, 708) | 100, 160, 110, 100, 60, 130, 160, 180 | 1,000 ms |
| [Butcher’s Advance VFX](vfx/Butcher%E2%80%99s%20Advance.png) | 6 | 3 × 2 | 896 × 896 | (448, 708) | 40, 40, 60, 60, 60, 40 | 300 ms |
| [Executioner’s Drop](base/Executioner%E2%80%99s%20Drop.png) | 8 | 4 × 2 | 896 × 896 | (448, 708) | 120, 180, 220, 350, 70, 180, 200, 180 | 1,500 ms |
| [Executioner’s Drop VFX](vfx/Executioner%E2%80%99s%20Drop.png) | 6 | 3 × 2 | 896 × 896 | (448, 708) | 40, 50, 80, 80, 90, 60 | 400 ms |
| [Damage Reaction](base/Damage%20Reaction.png) | 4 | 2 × 2 | 768 × 768 | (384, 644) | 60, 100, 120, 140 | 420 ms |
| [Defeat](base/Defeat.png) | 6 | 3 × 2 | 896 × 896 | (448, 708) | 120, 180, 220, 260, 300, hold | 1,080 ms before final hold |
| [Combat Approach](base/Combat%20Approach.png) | 8 | 4 × 2 | 768 × 768 | (384, 644) | 120, 120, 140, 140, 140, 140, 120, 140 | 1,060 ms with one stride cycle |
| [Combat Return](base/Combat%20Return.png) | 8 | 4 × 2 | 768 × 768 | (384, 644) | 120, 140, 150, 150, 150, 150, 120, 160 | 1,140 ms with one stride cycle |
| [Victory](base/Victory.png) | 8 | 4 × 2 | 896 × 896 | (448, 708) | 200, 160, 120, 240, 160, 120, 180, 220 | 1,400 ms per loop |

The labels and U+2019 apostrophes in Butcher’s Advance and Executioner’s Drop match the existing enemy content. [Move definitions](../../../../src/app/content/enemies/goblin_elite/enemy.py)

## Base playback

- **Combat Idle** loops frames 1–6. The head, upper armor and cleaver move together with a subtle weight shift. Both feet remain planted. The opening ready pose is shared with the neutral attack, reaction and movement transitions.
- **Veteran Slash** plays once. The compact wind-up leads into one controlled release on frame 4 at +300 ms. Frame 6 returns to Combat Idle frame 1.
- **Butcher’s Advance** plays once. Frames 1–2 load for 260 ms. Frames 3–5 drive left over 270 ms, with the single visual release on frame 5 at +470 ms. Frames 6–7 brake over 290 ms starting at +530 ms. Frame 8 settles at +820 ms and can lead into Combat Idle or Combat Return.
- **Executioner’s Drop** plays once. The high fourth frame holds for 350 ms. Release begins on frame 5 at +870 ms, followed by a low recovery. Both feet remain grounded. Frame 8 returns to Combat Idle frame 1.
- **Damage Reaction** plays once with a grounded recoil and torso recovery. Frame 4 matches Combat Idle frame 1.
- **Defeat** plays once and holds frame 6 indefinitely. Frames 5 and 6 share the settled pose. The preview encodes a 2,400 ms final hold and ends on that pose.
- **Combat Approach** enters on frames 1–2 (240 ms), repeats 3–6 (560 ms per cycle), and settles on frames 7–8 (260 ms). Translate the pivot left. Frame 8 can lead into an attack or return to idle.
- **Combat Return** enters on frames 1–2 (260 ms), repeats 3–6 (600 ms per cycle), and settles on frames 7–8 (280 ms). Translate the pivot right, preserving the original left-facing pose. Frame 8 leads into Combat Idle.
- **Victory** loops frames 1–8 around a fixed ground pivot. The free fist meets the breastplate on frames 3 and 6. The cleaver remains raised through the roar, hold and return. The contacts are celebration beats.

## Physical trails

| Effect | Start offset | Peak | Base release window | Alignment |
| --- | ---: | --- | --- | --- |
| Veteran Slash | +260 ms | Frame 2, +300–360 ms | Base frame 4, +300–360 ms | Narrow shortcut from the high-left blade to the compact diagonal cut. |
| Butcher’s Advance | +430 ms | Frame 2, +470–510 ms | Base frame 5, +470–530 ms | Broader trail riding the same externally translated pivot as the driving torso and blade. |
| Executioner’s Drop | +830 ms | Frame 2, +870–920 ms | Base frame 5, +870–940 ms | Heavy descending arc from the overhead weapon position to the low blade. |

All three effect sheets share the corresponding base pivot at (448, 708), play once, and clear on their last frame. Composite at the base pivot using the same source scale. The peak starts exactly at the strike and ends inside its window. Dissipation can continue into follow-through. The suggested frame durations were retained.

## External movement and review

The client owns world travel. The base and effects contain only pose-local shifts. Follow Butcher’s Advance with its own external drive and braking where appropriate. Coordinate any generic approach with that drive so the rush is shown once. The world-distance example travels 176 source pixels, during the documented drive and brake windows. The standalone gait previews show two stride cycles and the combined gait previews show one. The three-attack comparison uses a fixed pivot to expose choreography and separates the attacks with a 350 ms ready pose.

The offsets and cues describe presentation. The engine remains authoritative for combat.

# Goblin Animation Timings

Frame numbers start at 1 and follow reading order from the top left. Cell sizes and pivots are in pixels. Each pivot is measured from its cell's top-left corner. Place that pivot at the Goblin's world-space ground position. Use the same scale factor for every sheet. The canonical idle occupies roughly 430 source pixels in height, and the releases, strides, and Victory hop have extra room within their cells.

| Asset | Frames | Grid | Cell size | Registration | Per-frame duration (ms) | Playback duration |
| --- | ---: | --- | --- | --- | --- | --- |
| [Combat Idle](base/Combat%20Idle.png) | 6 | 3 × 2 | 576 × 576 | (288, 507) | 180, 160, 120, 220, 160, 180 | 1,020 ms per loop |
| [Slash](base/Slash.png) | 6 | 3 × 2 | 704 × 704 | (352, 571) | 100, 150, 90, 60, 120, 150 | 670 ms |
| [Slash VFX](vfx/Slash.png) | 4 | 2 × 2 | 704 × 704 | (352, 571) | 40, 60, 60, 40 | 200 ms |
| [Jumping Slash](base/Jumping%20Slash.png) | 8 | 4 × 2 | 704 × 704 | (352, 571) | 100, 180, 100, 120, 60, 120, 150, 180 | 1,010 ms |
| [Jumping Slash VFX](vfx/Jumping%20Slash.png) | 6 | 3 × 2 | 704 × 704 | (352, 571) | 40, 40, 60, 60, 60, 40 | 300 ms |
| [Damage Reaction](base/Damage%20Reaction.png) | 4 | 2 × 2 | 640 × 640 | (320, 539) | 60, 100, 120, 120 | 400 ms |
| [Defeat](base/Defeat.png) | 6 | 3 × 2 | 704 × 704 | (352, 571) | 100, 150, 180, 200, 250, hold | 880 ms before final hold |
| [Combat Approach](base/Combat%20Approach.png) | 8 | 4 × 2 | 640 × 640 | (320, 539) | 100, 100, 110, 110, 110, 110, 100, 120 | 860 ms with one stride cycle |
| [Combat Return](base/Combat%20Return.png) | 8 | 4 × 2 | 640 × 640 | (320, 539) | 100, 100, 120, 120, 120, 120, 100, 140 | 920 ms with one stride cycle |
| [Victory](base/Victory.png) | 8 | 4 × 2 | 704 × 704 | (352, 571) | 180, 100, 100, 150, 100, 100, 150, 120 | 1,000 ms per loop |

## Base playback

- **Combat Idle** loops frames 1–6. Frame 1 is the canonical stance and the common pose for action transitions. Both feet stay fixed.
- **Slash** plays once. Frame 4 begins at 340 ms and is the visual strike and trail release cue. Frame 5 follows through. Frame 6 resolves to the canonical stance. Resume idle at frame 1.
- **Jumping Slash** plays once. Frame 3 starts takeoff at 280 ms. Frame 5 begins at 500 ms and is the airborne visual strike and trail release cue. Frame 6 descends. Frame 7 lands at 680 ms. Frame 8 resolves to the canonical stance. Resume idle at frame 1.
- **Damage Reaction** plays once. Recoil peaks in frame 2 and settles to the canonical stance on frame 4. Resume idle at frame 1.
- **Defeat** plays frames 1–5 once and holds frame 6 indefinitely. Frames 5 and 6 share the settled pose. The review GIF plays once and gives the final hold 2,400 ms of encoded duration. It then stays on its last frame.
- **Combat Approach** plays frames 1–2 (200 ms), repeats 3–6 as needed (440 ms per cycle), then plays 7–8 (220 ms). Move the world pivot left. Frame 8 can lead directly into either attack or into idle.
- **Combat Return** plays frames 1–2 (200 ms), repeats 3–6 as needed (480 ms per cycle), then plays 7–8 (240 ms). Frame 1 starts in left-facing combat stance and frame 2 turns away in place. Frames 3–6 walk forward toward screen right in rear three-quarter view. Translate the world pivot right during these frames only. Frame 7 brakes and turns back in place, and frame 8 matches Combat Idle frame 1.

- **Victory** loops frames 1–8. Frames 1–2 load the foot on screen right. Frame 3 hops onto the opposite foot, which lands in frame 4 and compresses in frame 5. Frame 6 hops back to the original foot, frame 7 lands, and frame 8 recovers into frame 1. Keep the world pivot fixed. The airborne poses already lift the lowest contact point 54 and 50 source pixels in frames 3 and 6 respectively. Apply no separate hop offset. The axe stays overhead throughout, with no strike cue or VFX.

## External movement and jump

The approach and return sheets contain in-place poses. The horizontal distances and traversal speeds in the previews are illustrative. Use the externally supplied movement path and scale the pivot and any travel together when rendering. Small shifts around the pivot within the artwork express weight transfer.

The jumping sheet places the body's lowest point at the local pose baseline for every frame, including the airborne poses. Apply vertical jump displacement once, to the shared base and effect pivot. For the review preview, the lift above the world ground line is 0, 0, 48, 115, 104, 46, 0 and 0 source pixels by frame. Leave frame 2 grounded through compression and frame 7 grounded on landing. A renderer can interpolate the arc if desired. Apply any horizontal leap movement to the same world pivot.

## Effect sync

| Effect | Offset from base start | Strongest effect frame | Coupling |
| --- | ---: | ---: | --- |
| Slash | +300 ms | 2, begins at 340 ms with base frame 4 | Align with Slash pivot. Play once, clear on effect frame 4. |
| Jumping Slash | +420 ms | 3, begins at 500 ms with base frame 5 | Align with the Jumping Slash pivot, including the same external jump elevation. Play once, clear on effect frame 6. |

Composite the trails over the base at their registered positions. Each trail has a transparent final frame. The times from the brief were retained. Strike cues, effect offsets, movement previews and holds describe presentation. The headless engine remains authoritative for combat and movement rules.

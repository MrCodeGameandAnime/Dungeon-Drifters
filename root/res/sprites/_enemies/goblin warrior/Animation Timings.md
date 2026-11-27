# Goblin Warrior Animation Timings

Frames are numbered from 1 in reading order. All pivots are in source pixels from the cell's top-left corner. Place the pivot on the Warrior's world-space ground point. Use the same scale factor across the set. The canonical ready artwork occupies nominally 480 source pixels in height. Larger cells reserve room for the long blade and the fallen pose.

| Asset | Frames | Grid | Cell size | Pivot | Frame durations (ms) | Playback duration |
| --- | ---: | --- | --- | --- | --- | --- |
| [Combat Idle](base/Combat%20Idle.png) | 6 | 3 × 2 | 640 × 640 | (320, 552) | 180, 180, 160, 220, 160, 180 | 1,080 ms per loop |
| [Cleaver Strike](base/Cleaver%20Strike.png) | 6 | 3 × 2 | 768 × 768 | (384, 616) | 100, 160, 100, 70, 130, 160 | 720 ms |
| [Cleaver Strike VFX](vfx/Cleaver%20Strike.png) | 4 | 2 × 2 | 768 × 768 | (384, 616) | 40, 60, 60, 40 | 200 ms |
| [Shieldbreaker Chop](base/Shieldbreaker%20Chop.png) | 8 | 4 × 2 | 768 × 768 | (384, 616) | 100, 140, 160, 220, 70, 150, 180, 180 | 1,200 ms |
| [Shieldbreaker Chop VFX](vfx/Shieldbreaker%20Chop.png) | 6 | 3 × 2 | 768 × 768 | (384, 616) | 40, 40, 60, 60, 60, 40 | 300 ms |
| [Damage Reaction](base/Damage%20Reaction.png) | 4 | 2 × 2 | 704 × 704 | (352, 584) | 60, 100, 120, 120 | 400 ms |
| [Defeat](base/Defeat.png) | 6 | 3 × 2 | 768 × 768 | (384, 616) | 100, 150, 180, 220, 250, hold | 900 ms before final hold |
| [Combat Approach](base/Combat%20Approach.png) | 8 | 4 × 2 | 704 × 704 | (352, 584) | 100, 100, 120, 120, 120, 120, 100, 120 | 900 ms with one stride cycle |
| [Combat Return](base/Combat%20Return.png) | 8 | 4 × 2 | 704 × 704 | (352, 584) | 100, 100, 120, 120, 120, 120, 100, 140 | 920 ms with one stride cycle |
| [Victory](base/Victory.png) | 8 | 4 × 2 | 768 × 768 | (384, 616) | 180, 100, 100, 160, 100, 100, 160, 100 | 1,000 ms per loop |

## Base playback

- **Combat Idle** repeats frames 1–6 continuously. Both feet stay fixed. Frame 1 is the neutral stance shared with the action entry and exit frames.
- **Cleaver Strike** plays once. Frame 4 begins at 360 ms and is the visual strike and release cue. Frame 5 follows through and frame 6 returns to neutral. Resume Combat Idle at frame 1.
- **Shieldbreaker Chop** plays once. The fully raised blade holds across frame 4. Frame 5 begins at 620 ms and is the visual strike and release cue. Frames 6 and 7 carry the weight through the low position before frame 8 returns to neutral. Resume Combat Idle at frame 1.
- **Damage Reaction** plays once. The recoil peaks at frame 2. Frame 4 returns to neutral and leads into Combat Idle frame 1.
- **Defeat** plays once and holds frame 6 indefinitely. Frames 5 and 6 share the final settled pose. The preview encodes 2,400 ms for frame 6 and finishes on it.
- **Combat Approach** uses frames 1–2 (200 ms) for entry, repeats 3–6 (480 ms per cycle), and uses 7–8 (220 ms) to stop. Translate the world pivot left. Frame 8 leads into an attack or Combat Idle frame 1.
- **Combat Return** uses frames 1–2 (200 ms) for entry, repeats 3–6 (480 ms per cycle), and uses 7–8 (240 ms) to stop. Frame 1 starts in left-facing combat stance and frame 2 turns away in place. Frames 3–6 walk forward toward screen right in rear three-quarter view. Translate the world pivot right during these frames only. Frame 7 brakes and turns back in place, and frame 8 matches Combat Idle frame 1.
- **Victory** repeats frames 1–8 continuously at a fixed pivot. The two rising beats land into the plate-weighted stance. Frame 8 returns toward the blade-raised opening pose. There is no attack cue.

## Effect timing and movement

| Effect | Starts after base begins | Strongest frame | Alignment |
| --- | ---: | --- | --- |
| Cleaver Strike | 320 ms | Effect frame 2 begins at 360 ms, on base frame 4 | Composite at the shared (384, 616) pivot. Frame 4 clears. |
| Shieldbreaker Chop | 540 ms | Effect frame 3 begins at 620 ms, on base frame 5 | Composite at the shared (384, 616) pivot. Frame 6 clears. |

The movement and attack sheets stay centered around their ground pivot. The renderer owns horizontal displacement and carries the effect along with the attack pivot. The standalone movement previews show two stride cycles, while the combined previews use one. All preview travel distances are illustrative. The timing proposals were retained. Timings and release cues describe presentation. The headless engine remains authoritative.

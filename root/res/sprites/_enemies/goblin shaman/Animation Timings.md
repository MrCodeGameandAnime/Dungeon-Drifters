# Goblin Shaman Animation Timings

Frame numbering starts at 1. Read sheets from left to right, then top to bottom. Coordinates are source pixels measured from the top-left corner of a cell. Place the base pivot at the Shaman's world ground point and use a common scale. His canonical ready artwork is nominally 480 source pixels tall. The larger cells make room for raised or swept staff poses.

| Asset | Frames | Grid | Cell size | Pivot | Frame durations (ms) | Duration |
| --- | ---: | --- | --- | --- | --- | --- |
| [Combat Idle](base/Combat%20Idle.png) | 6 | 3 × 2 | 640 × 640 | (320, 552) | 220, 200, 180, 300, 180, 220 | 1,300 ms per loop |
| [Crooked Staff](base/Crooked%20Staff.png) | 6 | 3 × 2 | 832 × 832 | (416, 648) | 100, 120, 80, 60, 100, 140 | 600 ms |
| [Crooked Staff trail](vfx/Crooked%20Staff.png) | 4 | 2 × 2 | 832 × 832 | (416, 648) | 40, 60, 60, 40 | 200 ms |
| [Cinder Hex](base/Cinder%20Hex.png) | 8 | 4 × 2 | 832 × 832 | (416, 648) | 100, 140, 160, 200, 180, 60, 140, 180 | 1,160 ms |
| [Cinder Hex projectile](vfx/Cinder%20Hex%20-%20Projectile.png) | 6 | 3 × 2 | 224 × 224 | (80, 112) | 80, 80, 80, 80, 80, 80 | 480 ms per loop |
| [Cinder Hex impact](vfx/Cinder%20Hex%20-%20Impact.png) | 6 | 3 × 2 | 288 × 288 | (144, 144) | 40, 60, 80, 90, 100, 50 | 420 ms |
| [Blight Spark](base/Blight%20Spark.png) | 8 | 4 × 2 | 832 × 832 | (416, 648) | 120, 180, 220, 280, 400, 70, 180, 220 | 1,670 ms |
| [Blight Spark charge](vfx/Blight%20Spark%20-%20Charge.png) | 8 | 4 × 2 | 832 × 832 | (416, 648) | 120, 180, 220, 280, 400, 70, 180, 220 | 1,670 ms |
| [Blight Spark discharge](vfx/Blight%20Spark%20-%20Discharge.png) | 6 | 3 × 2 | 512 × 512 | (390, 256) | 40, 60, 100, 100, 120, 60 | 480 ms |
| [Damage Reaction](base/Damage%20Reaction.png) | 4 | 2 × 2 | 704 × 704 | (352, 584) | 60, 110, 140, 130 | 440 ms |
| [Defeat](base/Defeat.png) | 6 | 3 × 2 | 832 × 832 | (416, 648) | 100, 180, 220, 220, 250, hold | 970 ms before final hold |
| [Combat Approach](base/Combat%20Approach.png) | 8 | 4 × 2 | 704 × 704 | (352, 584) | 120, 120, 150, 150, 150, 150, 120, 150 | 1,110 ms with one stride cycle |
| [Combat Return](base/Combat%20Return.png) | 8 | 4 × 2 | 704 × 704 | (352, 584) | 120, 140, 160, 160, 160, 160, 120, 160 | 1,180 ms with one stride cycle |
| [Victory](base/Victory.png) | 8 | 4 × 2 | 832 × 832 | (416, 648) | 200, 160, 180, 260, 120, 100, 160, 220 | 1,400 ms per loop |

## Playback and registration

- **Combat Idle** loops frames 1–6. Both feet remain planted. Frame 1 is the neutral pose shared by the attack and movement transitions.
- **Crooked Staff** plays once. Frame 4 starts at 300 ms and provides the visual strike cue. Align the trail to the base pivot at +260 ms. Its strongest frame 2 starts with base frame 4. The traced skull path passes from approximately (282, 192) in frame 3 to (175, 483) in frame 4. Trail frame 4 is clear. Resume Combat Idle frame 1 after base frame 6.
- **Cinder Hex** plays once. Frame 4 opens the free hand near (470, 372). Launch the independently clocked projectile at the release gesture in frame 6, +780 ms, by aligning projectile center (80, 112) to the casting-hand origin (266, 385). The left-facing leading point is (56, 112). Repeat projectile frames 1–6 as needed in flight. On renderer-reported arrival, place impact contact (144, 144) at the chosen contact position and play frames 1–6 once. Impact frame 6 clears. Resume Combat Idle frame 1 after the base sheet completes even when the effect is still active.
- **Blight Spark** plays once. Base frame 5 is the 400 ms anticipation hold. Both charge and base start at the same time, use the same cell and pivot, and advance together. Charge frames 1 and 8 are clear. Base frame 6 starts at +1,200 ms and provides the single visual release. Place discharge origin (390, 256) onto the staff crystal at base coordinate (185, 246). The discharge's local leftward direction marker is (78, 256). Play the discharge once. Frame 6 clears. Resume Combat Idle frame 1 after base frame 8.
- **Damage Reaction** plays once. Briefly brace with the staff, then resume Combat Idle frame 1 after the neutral fourth frame.
- **Defeat** plays once. Hold frame 6 indefinitely at the ground pivot. Frames 5 and 6 share the settled body and staff pose. The review GIF encodes a 2,400 ms final hold and ends on that frame.
- **Combat Approach** enters on frames 1–2 (240 ms), repeats 3–6 (600 ms per cycle), and settles on 7–8 (270 ms). Move the world pivot left. The planted eighth frame can lead directly into Crooked Staff or Combat Idle.
- **Combat Return** enters on frames 1–2 (260 ms), repeats 3–6 (640 ms per cycle), and settles on 7–8 (280 ms). Move the world pivot right while preserving the left-facing pose. Continue into Combat Idle frame 1.
- **Victory** loops frames 1–8 with a fixed world pivot. The staff lifts through the cackle, stamps at frame 6, and returns toward frame 1 after the recovery. The motion is contained in the artwork.

## Blight Spark charge landmarks

| Base and charge frame | Staff crystal | Free hand |
| ---: | --- | --- |
| 2 | (264, 188) | (435, 426) |
| 3 | (292, 156) | (406, 365) |
| 4 | (309, 137) | (371, 221) |
| 5 | (310, 131) | (373, 217) |
| 6 | (185, 246) | (310, 316) |
| 7 | (228, 221) | (447, 417) |

## External presentation

Translate the movement and attack pivots externally where presentation calls for it. Cinder Hex and Blight Spark have stationary base poses. The preview moves the ember left by 240 source pixels over 520 ms after release and plays a single impact. This distance and placement are illustrative. The Blight discharge preview places its origin at the release point. Its movement and placement remain client-controlled.

The staff and belt crystals retain their intrinsic purple material color. The production idle retains slight reflected tint inside the hand silhouette after separating the master's transient flame. Active spell imagery is in the independent effects. All timing proposals were retained. Timings describe presentation and the headless engine remains authoritative.

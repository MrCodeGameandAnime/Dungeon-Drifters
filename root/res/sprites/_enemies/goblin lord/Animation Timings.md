# Goblin Lord Animation Timings

Frames are numbered from 1. Read left to right, then top to bottom. Pivots and landmarks use source pixels from the top-left corner of a cell. Place base pivots on the Lord's world-space ground point. Use a common source scale. The Lord's canonical ready silhouette is 600 source pixels tall, compared with 536 for the Elite and 432 for the standard Goblin.

| Asset | Frames | Grid | Cell size | Ground or effect pivot | Durations (ms) | Total |
| --- | ---: | --- | --- | --- | --- | --- |
| [Combat Idle](base/Combat%20Idle.png) | 6 | 3 × 2 | 768 × 768 | (384, 676) | 240, 220, 180, 280, 180, 240 | 1,340 ms per loop |
| [King’s Cleaver](base/King%E2%80%99s%20Cleaver.png) | 8 | 4 × 2 | 1024 × 1024 | (512, 804) | 100, 140, 180, 100, 70, 130, 160, 180 | 1,060 ms |
| [King’s Cleaver VFX](vfx/King%E2%80%99s%20Cleaver.png) | 6 | 3 × 2 | 1024 × 1024 | (512, 804) | 40, 40, 60, 60, 60, 40 | 300 ms |
| [Iron Decree](base/Iron%20Decree.png) | 8 | 4 × 2 | 1024 × 1024 | (512, 804) | 120, 180, 240, 380, 80, 200, 240, 200 | 1,640 ms |
| [Iron Decree VFX](vfx/Iron%20Decree.png) | 6 | 3 × 2 | 1024 × 1024 | (512, 804) | 40, 50, 80, 80, 90, 60 | 400 ms |
| [Black Banner Flame](base/Black%20Banner%20Flame.png) | 8 | 4 × 2 | 1024 × 1024 | (512, 804) | 120, 180, 220, 280, 300, 70, 180, 220 | 1,570 ms |
| [Black Banner Flame - Charge](vfx/Black%20Banner%20Flame%20-%20Charge.png) | 8 | 4 × 2 | 384 × 384 | (192, 202) | 120, 180, 220, 280, 300, 70, 180, 220 | 1,570 ms |
| [Black Banner Flame - Surge](vfx/Black%20Banner%20Flame%20-%20Surge.png) | 8 | 4 × 2 | 768 × 768 | (620, 400) | 40, 60, 80, 100, 100, 100, 100, 60 | 640 ms |
| [Tyrant’s Ruin](base/Tyrant%E2%80%99s%20Ruin.png) | 10 | 5 × 2 | 1024 × 1024 | (512, 804) | 120, 180, 220, 280, 360, 70, 120, 80, 220, 240 | 1,890 ms |
| [Tyrant’s Ruin - Cleaver](vfx/Tyrant%E2%80%99s%20Ruin%20-%20Cleaver.png) | 6 | 3 × 2 | 1024 × 1024 | (512, 804) | 40, 40, 60, 60, 60, 40 | 300 ms |
| [Tyrant’s Ruin - Charge](vfx/Tyrant%E2%80%99s%20Ruin%20-%20Charge.png) | 10 | 5 × 2 | 1024 × 1024 | (512, 804) | 120, 180, 220, 280, 360, 70, 120, 80, 220, 240 | 1,890 ms |
| [Tyrant’s Ruin - Discharge](vfx/Tyrant%E2%80%99s%20Ruin%20-%20Discharge.png) | 8 | 4 × 2 | 768 × 768 | (620, 400) | 40, 60, 100, 120, 120, 100, 80, 60 | 680 ms |
| [Damage Reaction](base/Damage%20Reaction.png) | 4 | 2 × 2 | 896 × 896 | (448, 740) | 70, 120, 150, 160 | 500 ms |
| [Defeat](base/Defeat.png) | 8 | 4 × 2 | 1024 × 1024 | (512, 804) | 120, 180, 220, 260, 300, 250, 200, hold | 1,530 ms before final hold |
| [Combat Approach](base/Combat%20Approach.png) | 8 | 4 × 2 | 896 × 896 | (448, 740) | 140, 140, 170, 170, 170, 170, 140, 180 | 1,280 ms with one stride cycle |
| [Combat Return](base/Combat%20Return.png) | 8 | 4 × 2 | 896 × 896 | (448, 740) | 140, 160, 180, 180, 180, 180, 140, 180 | 1,340 ms with one stride cycle |
| [Victory](base/Victory.png) | 10 | 5 × 2 | 1024 × 1024 | (512, 804) | 180, 160, 160, 180, 500, 200, 160, 160, 180, 300 | 2,180 ms per loop |

The move labels match the content, including U+2019 in King’s Cleaver and Tyrant’s Ruin. [Goblin Lord move definitions](../../../../src/app/content/enemies/goblin_lord/enemy.py)

## Base playback

- **Combat Idle** loops frames 1–6. The head, mask, upper body and cleavers move together through a heavy breath while the lower legs and feet remain anchored. Frame 1 is the shared neutral entry and exit pose.
- **King’s Cleaver** plays once. The screen-left hand carries the main sweep, with the other cleaver held low. Frame 5 starts at +520 ms. The blade follows through and returns to the idle pose on frame 8.
- **Iron Decree** plays once. Both blades hold overhead in frame 4 for 380 ms. Both descend together on frame 5 at +920 ms. Frame 8 returns to idle.
- **Black Banner Flame** plays once at a fixed character pivot. His blade signals the standard on frame 6 at +1,100 ms. The prop supplies the origin and the gesture marks the release. The base returns to idle after frame 8 while the independent surge can finish.
- **Tyrant’s Ruin** plays once. Frame 5 holds for 360 ms. The coordinated physical sweep starts on frame 6 at +1,160 ms, then the extended cleaver directs discharge on frame 8 at +1,350 ms. The character charge overlay is clear in frame 10 and the base returns to idle. These are presentation beats of one move.
- **Damage Reaction** plays once. Both cleavers remain held. Recoil peaks on frame 2 and the ready fourth frame leads back to Combat Idle.
- **Defeat** plays once and holds frame 8 indefinitely. Frames 7 and 8 share the settled silhouette with both released cleavers visible. The review GIF uses a 2,400 ms encoded final hold and ends at the settled frame.
- **Combat Approach** enters on frames 1–2 (280 ms), repeats frames 3–6 (680 ms per cycle), and settles on 7–8 (320 ms). Translate the world pivot left.
- **Combat Return** enters on frames 1–2 (300 ms), repeats frames 3–6 (720 ms per cycle), and settles on 7–8 (320 ms). Frame 1 starts in left-facing combat stance and frame 2 turns away in place. Frames 3–6 walk forward toward screen right in rear three-quarter view. Translate the world pivot right during these frames only. Frame 7 brakes and turns back in place, and frame 8 matches Combat Idle frame 1.
- **Victory** loops 1–10 at a fixed pivot. The screen-right cleaver plants on frame 2 and stays beside the Lord through frame 8. The screen-right hand raises, tips and lowers the flask across frames 4–6 while the opposite hand keeps its cleaver. The mouth opening is used with the canonical skull mask still in place. The planted cleaver is back in hand by frame 9 and remains held through the closing roar.

Re-enter Combat Idle at frame 1 after any action that returns to ready. The client owns world displacement. The walk sheets contain in-place artwork. Generic approach can be used where presentation needs it, independently of magical casts. All suggested frame durations were retained.

## Physical trails

| Effect | Starts after base | Peak within base strike | Blade trajectory in the shared 1,024-pixel cells |
| --- | ---: | --- | --- |
| King’s Cleaver | +440 ms | Effect frame 3 at +520–580 ms, inside base frame 5 at +520–590 ms | Main cleaver from the high-left wind-up near (385, 165) toward the leftward tip at (157, 468). |
| Iron Decree | +830 ms | Both trails peak together in effect frame 3 at +920–1,000 ms, matching base frame 5 | Screen-left cleaver from (496, 111) to (155, 766). Screen-right cleaver from (665, 115) to (280, 773). |
| Tyrant’s Ruin | +1,080 ms | Effect frame 3 at +1,160–1,220 ms, inside base frame 6 at +1,160–1,230 ms | Upper sweep (324, 195) to (166, 428). Lower sweep (712, 185) to (167, 585). |

Align each physical trail at the corresponding base pivot (512, 804). Play once. Final cells are clear. Dissipation extends into the follow-through where appropriate.

## Battle standard and Black Banner Flame

The canonical master has no standard and the game content describes it without an authored sprite. The separate charcoal banner uses bare tribal cloth, dark wood, an iron tip and bone trim. It is a 416 × 704 RGBA prop with no new emblem. Place ground pivot (176, 666) at the client-selected ground point. The flame origin is (187, 137), close to the skull fastening. The review places the prop ground pivot 305 source pixels to the Lord's screen-right and composites it behind him. [Battle Standard.png](props/Battle%20Standard.png)

Start the standard-relative charge with the base timeline. Align charge pivot (192, 202) with the prop flame origin. Charge frames 1 and 8 are clear. At +1,100 ms, align surge origin (620, 400) to the same prop landmark and play once. Its local leftward marker is (88, 400). The surge ends at +1,740 ms, including its clear eighth frame.

## Tyrant’s Ruin charge and discharge

Composite the charge on the shared base pivot. Its grid, cell dimensions and timing match the base exactly. Frames 1 and 10 are clear.

| Base and overlay frame | First charge landmark | Second charge landmark |
| ---: | --- | --- |
| 2 | (277, 459) | (686, 538) |
| 3 | (266, 280) | (780, 635) |
| 4 | (343, 264) | (668, 344) |
| 5 | (324, 229) | (722, 227) |
| 6 | (235, 429) | (234, 579) |
| 7 | (223, 603) | (688, 594) |
| 8 | (152, 438) | (775, 639) |
| 9 | (278, 451) | (671, 631) |

On base frame 8 at +1,350 ms, place the discharge origin (620, 400) on the directing cleaver tip at cell position (136, 438). Its local leftward marker is (88, 400). Play the discharge once independently. Its eighth frame clears and the timeline ends at +2,030 ms. Origin markers carry no fixed movement distance or placement rules.

## Review convention

Movement previews use illustrative travel. Standalone gait GIFs show two cycles and combined examples show one. The comparison holds a common world pivot and pauses on the ready stance for 360 ms between moves. The GIFs use a fixed palette per clip. Cues describe presentation and the headless engine remains authoritative.

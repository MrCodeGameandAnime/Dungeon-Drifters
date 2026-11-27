# Joruun Veyr, the Bloody Storm Monk — Animation Timings

Frames are numbered from 1 and read left to right, top to bottom. Pivots are measured in source pixels from the top-left of each cell. Align the named pivot to its presentation anchor. Use the same pivot and scale for a base pose and its registered overlay. Timings are recommendations for review. The 800 ms idle loop is the proposed timing for the existing approved artwork.

## Base poses

| ID | Asset | Frames | Grid | Cell (px) | Pivot (px) | Timing (ms) | Clear frames | Placement and playback |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| B01 | [Combat Idle](base/Combat%20Idle.png) | 6 | 3 × 2 | 576 × 576 | (318, 505) | 120, 130, 155, 110, 155, 130 | — | Idle and staff rhythm. Loop 1–6. |
| B02 | [Bring the Horse to Water](base/Bring%20the%20Horse%20to%20Water.png) | 8 | 4 × 2 | 768 × 640 | (414, 537) | 90, 100, 105, 120, 55, 70, 95, 100 | — | Physical sweep. Contact on 5. |
| B03 | [Lightning Palm](base/Lightning%20Palm.png) | 8 | 4 × 2 | 768 × 640 | (414, 537) | 80, 80, 90, 105, 50, 75, 90, 100 | — | Open-palm commitment on 5. Reused for all four Palm outcomes. |
| B04 | [Tempest Surge](base/Tempest%20Surge.png) | 8 | 4 × 2 | 896 × 640 | (478, 537) | 90, 110, 135, 145, 70, 110, 115, 100 | — | Green pressure release on 5. |
| B05 | [Hydro Whip](base/Hydro%20Whip.png) | 8 | 4 × 2 | 960 × 640 | (510, 537) | 85, 95, 100, 105, 45, 70, 95, 100 | — | Blue lash snap on 5. |
| B06 | [Coagulated Torrent](base/Coagulated%20Torrent.png) | 8 | 4 × 2 | 896 × 672 | (478, 553) | 100, 125, 170, 200, 560, 65, 140, 140 | — | Compression hold 5 and release 6. Release-palm origin approximately (670, 276). |
| B07 | [Defend](base/Defend.png) | 4 | 2 × 2 | 640 × 576 | (350, 505) | 85, 100, hold, 120 | — | Hold frame 3. Preview dwell 480 ms. |
| B08 | [Damage Reaction](base/Damage%20Reaction.png) | 4 | 2 × 2 | 640 × 576 | (350, 505) | 45, 75, 90, 100 | — | Brief recoil on 2, then idle. |
| B09 | [Defeat](base/Defeat.png) | 6 | 3 × 2 | 640 × 576 | (350, 505) | 100, 120, 150, 175, 210, indefinite hold | — | Grounded kneel on 5. Hold 6 indefinitely. |
| B10 | [Victory](base/Victory.png) | 6 | 3 × 2 | 640 × 576 | (350, 505) | 120, 140, 170, 540, 180, indefinite hold | — | Acknowledgment on 4. Hold 6 indefinitely. |
| B11 | [Combat Approach](base/Combat%20Approach.png) | 8 | 4 × 2 | 704 × 576 | (382, 505) | 100, 95, 115, 115, 115, 115, 100, 100 | — | Screen-right. Loop 3–6 for a 460 ms cycle. |
| B12 | [Combat Return](base/Combat%20Return.png) | 8 | 4 × 2 | 704 × 576 | (382, 505) | 100, 95, 115, 115, 115, 115, 100, 100 | — | Screen-left. Loop 3–6 for a 460 ms cycle. |

## Independent effects

| ID | Asset | Frames | Grid | Cell (px) | Pivot (px) | Timing (ms) | Clear frames | Placement and playback |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| V01 | [Bring the Horse to Water - Impact](vfx/Bring%20the%20Horse%20to%20Water%20-%20Impact.png) | 6 | 3 × 2 | 352 × 320 | (176, 160) | 35, 35, 55, 65, 70, 75 | 6 | Target contact point. Warm neutral strike accent. Clear 6. |
| V02 | [Lightning Palm - Base Impact](vfx/Lightning%20Palm%20-%20Base%20Impact.png) | 6 | 3 × 2 | 448 × 384 | (224, 192) | 35, 40, 55, 70, 90, 85 | 6 | Target contact point. Gold-only. Clear 6. |
| V03 | [Lightning Palm - Conductive Impact](vfx/Lightning%20Palm%20-%20Conductive%20Impact.png) | 6 | 3 × 2 | 448 × 384 | (224, 192) | 55, 55, 65, 90, 105, 85 | 6 | Target contact point. Yellow arcs ride the blue carriers. Clear 6. |
| V04 | [Lightning Palm - Turbulence Impact](vfx/Lightning%20Palm%20-%20Turbulence%20Impact.png) | 6 | 3 × 2 | 448 × 384 | (224, 192) | 55, 55, 70, 95, 105, 85 | 6 | Target contact point. Green eddies shape yellow arcs. Clear 6. |
| V05 | [Lightning Storm](vfx/Lightning%20Storm.png) | 8 | 4 × 2 | 512 × 512 | (256, 445) | 65, 75, 85, 100, 70, 100, 115, 90 | 8 | Target ground. Blue carrier, green helix, dominant gold discharge. Clear 8. |
| V06 | [Conductive Status](vfx/Conductive%20Status.png) | 6 | 3 × 2 | 448 × 384 | (224, 192) | 130, 130, 130, 130, 130, 130 | — | Target lower torso. Persistent blue loop. |
| V07 | [Conductive Consumption](vfx/Conductive%20Consumption.png) | 4 | 2 × 2 | 448 × 384 | (224, 192) | 55, 75, 85, 85 | 4 | Same lower-torso pivot as V06. Frame 1 shares V06 frame 1. Clear 4. |
| V08 | [Turbulence Status](vfx/Turbulence%20Status.png) | 6 | 3 × 2 | 448 × 384 | (224, 192) | 125, 125, 125, 125, 125, 125 | — | Target upper torso. Persistent green loop. Can coexist with V06. |
| V09 | [Turbulence Consumption](vfx/Turbulence%20Consumption.png) | 4 | 2 × 2 | 448 × 384 | (224, 192) | 55, 75, 85, 85 | 4 | Same upper-torso pivot as V08. Frame 1 shares V08 frame 1. Clear 4. |
| V10 | [Stun Status](vfx/Stun%20Status.png) | 6 | 3 × 2 | 320 × 224 | (160, 112) | 125, 125, 125, 125, 125, 125 | — | Place above target head. Persistent orbit, duration driven by state. |
| V11 | [Hydro Whip - Lash](vfx/Hydro%20Whip%20-%20Lash.png) | 8 | 4 × 2 | 960 × 640 | (510, 537) | 85, 95, 100, 105, 45, 70, 95, 100 | 1, 8 | Registered caster overlay, follows Sky-Needle. Clear 1 and 8. Sync B05. |
| V12 | [Hydro Whip - Impact](vfx/Hydro%20Whip%20-%20Impact.png) | 6 | 3 × 2 | 448 × 384 | (224, 192) | 40, 50, 65, 75, 95, 85 | 6 | Independent target torso. Place at lash contact. Clear 6. |
| V13 | [Tempest Surge - Wind Burst](vfx/Tempest%20Surge%20-%20Wind%20Burst.png) | 8 | 4 × 2 | 896 × 640 | (478, 537) | 90, 110, 135, 145, 70, 110, 115, 100 | 1, 8 | Registered caster overlay. Gathers at staff, releases through the open palm. Clear 1 and 8. Sync B04. |
| V14 | [Tempest Surge - Impact](vfx/Tempest%20Surge%20-%20Impact.png) | 6 | 3 × 2 | 448 × 384 | (224, 192) | 45, 65, 75, 85, 105, 90 | 6 | Independent target torso. Green pressure. Clear 6. |
| V15 | [Coagulated Torrent - Charge](vfx/Coagulated%20Torrent%20-%20Charge.png) | 8 | 4 × 2 | 896 × 672 | (478, 553) | 100, 125, 170, 200, 560, 65, 140, 140 | 1, 8 | Registered caster overlay. Hold 5 with base. Clear 1 and 8. Sync B06. |
| V16 | [Coagulated Torrent - Torrent](vfx/Coagulated%20Torrent%20-%20Torrent.png) | 8 | 4 × 2 | 608 × 256 | (524, 128) | 45, 50, 55, 65, 65, 75, 95, 85 | 8 | Leading tip pivot. Spawn at the release palm. Travel is independent of the sheet. Clear 8. |
| V17 | [Coagulated Torrent - Impact](vfx/Coagulated%20Torrent%20-%20Impact.png) | 8 | 4 × 2 | 512 × 512 | (256, 256) | 45, 55, 65, 80, 95, 115, 125, 90 | 8 | Target torso. Spawn on arrival. Clear 8. |
| V18 | [Movement Wind Accent](vfx/Movement%20Wind%20Accent.png) | 6 | 3 × 2 | 448 × 224 | (370, 188) | 85, 95, 110, 110, 110, 95 | 1, 6 | Optional ground-relative green wake extending left from the pivot. Reflect effect only for leftward travel. Clear 1 and 6. |
| V19 | [Defend Accent](vfx/Defend%20Accent.png) | 4 | 2 × 2 | 640 × 576 | (350, 505) | 85, 100, hold, 120 | 1, 4 | Optional guard overlay. Hold 3 with base. Clear 1 and 4. Sync B07. |
| V20 | [Victory Accent](vfx/Victory%20Accent.png) | 6 | 3 × 2 | 640 × 576 | (350, 505) | 120, 140, 170, 540, 180, clear on 6 | 1, 6 | Optional shoulder-level flourish. Clear 1 and 6. Sync B10. |
| V21 | [Super Residual Dissipation](vfx/Super%20Residual%20Dissipation.png) | 6 | 3 × 2 | 512 × 512 | (256, 256) | 90, 100, 105, 110, 120, 105 | 6 | Target torso. May replace V17 from its last visible pose. Clear 6. |

## Layer synchronization

- **Physical staff technique.** Start V01 on the B02 contact cue. The flash is warm gray and independent of the target sprite.
- **Water and wind.** Play V11 with B05 and V13 with B04. Start the independent impact at the target contact. On the corresponding status application or refresh, run V06 below the waist or V08 at the upper torso. Their footprints allow both states to read together.
- **Lightning Palm.** Use B03 for every version. Select one impact effect based on the outcome. V02 is gold alone, V03 adds blue water, V04 adds green wind, and V05 combines all three. On consumption, use the matching V07 or V09 fade at the status pivot. V05 keeps the blue carrier beneath the ascending green helix, with gold lightning tracing the combined path. The Stun example follows the conditional outcome from Conductive-only Palm. Display V10 only when the target gains that state.
- **Coagulated Torrent.** Play V15 against B06 and hold both at frame 5. At frame 6, place the leading pivot of V16 on the release palm and move it toward the intended contact point. Spawn V17 at contact. For the extended aftermath, replace V17 starting at frame 7 with V21 at the same center. Its first frame shares the last visible impact pose. The crimson threads and drops use separate artwork from Hydro Whip.
- **Movement and holds.** Play 1–2 for entry, 3–6 as an independent walk loop, and 7–8 for exit. Battlefield displacement belongs to the presentation layer. The optional air wake uses the ground anchor and may be reflected independently for leftward travel. In Defend, hold frame 3 as needed before recovery. Defeat and Victory have persistent frame-6 states.
- The review clips use a finite 480 ms guard dwell and 1,400 ms final defeat/victory holds. GIF timestamps are rounded to centiseconds and include a final 10 ms closing frame. Distances and status lifetimes in the clips demonstrate timing and composition. See the [Production Checklist](Production%20Checklist.md) for review status.

## Elemental palette

| Family | Deep | Mid | Bright | Highlight |
| --- | --- | --- | --- | --- |
| Water | `#123F73` | `#2E6FB2` | `#56A7E8` | `#BFE9FF` |
| Air | `#1D5A3A` | `#2E8A58` | `#5DCB7D` | `#C8F5D5` |
| Lightning | `#9B7600` | `#D8A900` | `#FFD83A` | `#FFF6B8` |
| Blood | `#24080D`, `#4E0B16` | `#811324` | `#B92539` | `#E3646C` |

These colors guided the artwork. The sprites retain intermediate tones for material detail and antialiasing.


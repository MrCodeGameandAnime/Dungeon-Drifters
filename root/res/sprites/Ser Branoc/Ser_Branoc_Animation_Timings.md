# Dungeon Drifters: Ser Branoc Animation Timings

## Scope

Initial graphical artwork package for Ser Branoc, the Unbroken Crest. Covers all 11 existing base animation sheets and six VFX sheets, including the five starting abilities. Unlockable abilities are deferred.

All frame numbers are **1-based**, in reading order (left to right, top to bottom). All durations are in milliseconds. These are proposed playback settings, not measured or final approved timings. Previously proposed values are preserved; values not established earlier are explicitly marked **new proposal**. Sprite Pop playback approval of an asset does not by itself qualify its per-frame timing.

## 1. Base character animations

### Combat Idle

- Asset: `base/Combat Idle.png`
- Layout: 3 columns × 2 rows; 6 frames
- Playback: continuous loop
- Timing: **new proposal** (no earlier per-frame durations were specified)

| Frame | Duration (ms) |
| --- | ---: |
| 1 | 150 |
| 2 | 150 |
| 3 | 150 |
| 4 | 150 |
| 5 | 150 |
| 6 | 150 |

**Cycle:** 900 ms. Loop frames 1–6.

### Standard Attack — Crestgrave Reaping

- Asset: `base/Standard Attack.png`
- Layout: 4 columns × 2 rows; 8 frames
- Playback: once, then idle
- Timing: **new proposal** (no earlier per-frame durations were specified)

| Frame | Pose | Duration (ms) |
| --- | --- | ---: |
| 1 | Ready | 100 |
| 2 | Anticipation | 100 |
| 3 | Two-handed preparation | 120 |
| 4 | Overhead windup | 140 |
| 5 | Strike / follow-through | 60 |
| 6 | Follow-through | 100 |
| 7 | Recovery | 100 |
| 8 | Return to idle | 120 |

**Total:** 840 ms. Frame 5 is a proposed visual impact marker.

### Defend / Brace

- Asset: `base/Defend Brace.png`
- Layout: 2 columns × 2 rows; 4 frames
- Playback: entry, variable hold, recovery
- Timing: previously proposed

| Frame | Pose | Duration (ms) |
| --- | --- | ---: |
| 1 | Anticipation | 100 |
| 2 | Brace preparation | 120 |
| 3 | Full defensive brace | Variable hold |
| 4 | Recovery | 150 |

**Total:** 370 ms + frame 3 hold. Ordinary Defend has no independent Brace activation effect. Brace uses the separate gold activation and persistent aura artwork; the persistent aura can outlast this character animation.

### Damage Reaction

- Asset: `base/Damage Reaction.png`
- Layout: 2 columns × 2 rows; 4 frames
- Playback: once, then idle or appropriate existing pose
- Timing: previously proposed

| Frame | Pose | Duration (ms) |
| --- | --- | ---: |
| 1 | Initial impact | 60 |
| 2 | Maximum recoil | 90 |
| 3 | Regaining balance | 100 |
| 4 | Recovery | 120 |

**Total:** 370 ms.

### Ironwake Dismemberment

- Asset: `base/Ironwake Dismemberment.png`
- Layout: 4 columns × 2 rows; 8 frames
- Playback: once, then recovery / return
- Timing: previously proposed

| Frame | Pose | Duration (ms) |
| --- | --- | ---: |
| 1 | Preparation | 100 |
| 2 | Weight transfer | 120 |
| 3 | Rising windup | 150 |
| 4 | Maximum windup | 250 |
| 5 | Explosive descent | 50 |
| 6 | Completed strike / impact | 130 |
| 7 | Heavy recovery | 180 |
| 8 | Return to combat idle | 120 |

**Total:** 1,100 ms. Frame 6 is the proposed visual impact marker. The enhanced version uses the same character sheet and timings, with synchronized gold VFX.

### Third Gate Obsequy

- Asset: `base/Third Gate Obsequy.png`
- Layout: 4 columns × 2 rows; 8 frames
- Playback: once, with a sustained channeling pose
- Timing: previously proposed

| Frame | Pose | Duration (ms) |
| --- | --- | ---: |
| 1 | Invocation preparation | 120 |
| 2 | Establishing the channel | 180 |
| 3 | Forbidden invocation | 250 |
| 4 | Maximum channeling | 800 |
| 5 | Release preparation | 150 |
| 6 | Cataclysmic release | 80 |
| 7 | Aftermath | 300 |
| 8 | Return to idle | 200 |

**Total:** 2,080 ms. Frame 4 is the proposed channeling hold; frame 6 is the proposed visual release marker. Rear Gate and Weapon FX follow the same frame timing.

### Cinderlung Vesper

- Asset: `base/Cinderlung Vesper.png`
- Layout: 4 columns × 2 rows; 8 frames
- Playback: once, with a sustained war-breath pose
- Timing: latest proposal after the combined GIF preview

| Frame | Pose | Duration (ms) |
| --- | --- | ---: |
| 1 | Idle | 80 |
| 2 | Preparation | 120 |
| 3 | Inhalation | 180 |
| 4 | Maximum buildup | 300 |
| 5 | Eruption | 80 |
| 6 | Sustained war-breath | 450 |
| 7 | Dissipation | 180 |
| 8 | Recovery | 100 |

**Total:** 1,490 ms. Frames 4 and 6 are the proposed anticipation and sustained release poses. The War Breath FX follows the same timings.

Earlier base-animation proposal (superseded by the latest suggestion): 100, 120, 200, 350, 80, 600, 200, 120 ms (1,770 ms total). Neither timing profile is recorded as playback-approved.

### Defeat

- Asset: `base/Defeat.png`
- Layout: 3 columns × 2 rows; 6 frames
- Playback: once, then hold defeated pose
- Timing: previously proposed

| Frame | Pose | Duration (ms) |
| --- | --- | ---: |
| 1 | Loss of strength | 120 |
| 2 | Faltering | 150 |
| 3 | Last support | 180 |
| 4 | Descent | 200 |
| 5 | Kneeling | 250 |
| 6 | Final defeat | Indefinite hold |

**Total:** 900 ms before final hold. Do not loop back to frame 1.

### Victory

- Asset: `base/Victory.png`
- Layout: 3 columns × 2 rows; 6 frames
- Playback: once, then hold victorious pose
- Timing: previously proposed

| Frame | Pose | Duration (ms) |
| --- | --- | ---: |
| 1 | Battle concluded | 150 |
| 2 | Composure | 180 |
| 3 | Ceremonial salute | 200 |
| 4 | Triumphant acknowledgment | 1,000 |
| 5 | Controlled descent | 250 |
| 6 | Victorious composure | Indefinite hold |

**Total:** 1,780 ms before final hold. Frame 4 is the primary victory salute.

### Combat Approach

- Asset: `base/Combat Approach.png`
- Layout: 4 columns × 2 rows; 8 frames
- Direction: screen-right
- Playback: entry, repeatable walking cycle, exit
- Timing: previously proposed

| Frame | Pose | Duration (ms) |
| --- | --- | ---: |
| 1 | Combat idle | 120 |
| 2 | Directional transition | 120 |
| 3 | First walking contact | 150 |
| 4 | First passing pose | 150 |
| 5 | Opposite walking contact | 150 |
| 6 | Opposite passing pose | 150 |
| 7 | Deceleration and turning | 120 |
| 8 | Combat ready | 120 |

**Entry:** frames 1–2, 240 ms. **Walk loop:** frames 3–6, 600 ms per cycle. **Exit:** frames 7–8, 240 ms. One full traversal with one walk cycle: 1,080 ms. Repeat only frames 3–6 as needed.

### Combat Return

- Asset: `base/Combat Return.png`
- Layout: 4 columns × 2 rows; 8 frames
- Direction: screen-left
- Playback: entry, repeatable walking cycle, exit
- Timing: previously proposed

| Frame | Pose | Duration (ms) |
| --- | --- | ---: |
| 1 | Combat stance | 120 |
| 2 | Return direction transition | 120 |
| 3 | First walking contact | 150 |
| 4 | First passing pose | 150 |
| 5 | Opposite walking contact | 150 |
| 6 | Opposite passing pose | 150 |
| 7 | Deceleration and turning | 120 |
| 8 | Combat ready | 120 |

**Entry:** frames 1–2, 240 ms. **Walk loop:** frames 3–6, 600 ms per cycle. **Exit:** frames 7–8, 240 ms. One full traversal with one walk cycle: 1,080 ms. Repeat only frames 3–6 as needed.

## 2. Independent VFX animations

### Brace Activation FX

- Asset: `vfx/Brace Activation.png`
- Layout: 2 columns × 2 rows; 4 frames
- Playback: once, then persistent aura
- Timing: **new per-frame proposal**, within the earlier 300–500 ms activation range

| Frame | Effect | Duration (ms) |
| --- | --- | ---: |
| 1 | Faint gathering energy | 100 |
| 2 | Energy builds | 120 |
| 3 | Maximum gold pulse | 150 |
| 4 | Settling glow | 130 |

**Total:** 500 ms. Peak aligns with the full Brace posture where practical; the activation pulse itself is not held indefinitely.

### Brace Persistent Aura

- Asset: `vfx/Brace Persistent Aura.png`
- Layout: 3 columns × 2 rows; 6 frames
- Playback: continuous independent loop while the offensive enhancement remains active
- Timing: **new proposal**

| Frame | Duration (ms) |
| --- | ---: |
| 1 | 150 |
| 2 | 150 |
| 3 | 150 |
| 4 | 150 |
| 5 | 150 |
| 6 | 150 |

**Cycle:** 900 ms. Remains visible during applicable idle, movement, and other actions until the enhancement is consumed or otherwise removed according to existing gameplay rules. Ordinary Defend does not create it.

### Enhanced Ironwake Dismemberment FX

- Asset: `vfx/Enhanced Ironwake Dismemberment.png`
- Layout: 4 columns × 2 rows; 8 frames
- Playback: synchronized with Ironwake Dismemberment, only when enhanced

| Frame | Effect | Duration (ms) |
| --- | --- | ---: |
| 1 | Stored energy intensifies | 100 |
| 2 | Energy gathers at weapon | 120 |
| 3 | Rising weapon energy | 150 |
| 4 | Maximum windup energy | 250 |
| 5 | Descending gold trail | 50 |
| 6 | Impact burst | 130 |
| 7 | Residual energy | 180 |
| 8 | Transparent / cleared | 120 |

**Total:** 1,100 ms. Uses the previously proposed Ironwake base timings. No effect on ordinary Ironwake. The persistent aura's removal follows actual enhancement consumption.

### Third Gate Obsequy — Rear Gate and Weapon FX

- Assets: `vfx/Third Gate Obsequy - Rear Gate.png`, `vfx/Third Gate Obsequy - Weapon.png`
- Layout: each 4 columns × 2 rows; 8 frame cells
- Playback: synchronized with Third Gate Obsequy character animation
- Layer order: Rear Gate behind character; Weapon FX in front of character

| Frame | Duration (ms) |
| --- | ---: |
| 1 | 120 |
| 2 | 180 |
| 3 | 250 |
| 4 | 800 |
| 5 | 150 |
| 6 | 80 |
| 7 | 300 |
| 8 | 200 |

**Total:** 2,080 ms per layer, playing concurrently, not consecutively. Final effect cells are transparent. Use the same hold timing on all three sheets.

### Cinderlung Vesper — War Breath FX

- Asset: `vfx/Cinderlung Vesper - War Breath.png`
- Layout: 4 columns × 2 rows; 8 frames
- Playback: synchronized with Cinderlung Vesper character animation

| Frame | Effect | Duration (ms) |
| --- | --- | ---: |
| 1 | Transparent | 80 |
| 2 | Transparent | 120 |
| 3 | Faint embers | 180 |
| 4 | Heat buildup | 300 |
| 5 | Initial eruption | 80 |
| 6 | Sustained war-breath | 450 |
| 7 | Dissipation | 180 |
| 8 | Transparent | 100 |

**Total:** 1,490 ms, concurrent with the base character sheet. Uses the latest proposed Cinderlung timing.

## 3. Quick reference

| Animation | Frames | Duration (ms) | Playback |
| --- | ---: | ---: | --- |
| Combat Idle | 6 | 900 | Loop; new timing |
| Crestgrave Reaping | 8 | 840 | Once; new timing |
| Defend / Brace | 4 | 370 + hold | Hold frame 3 |
| Damage Reaction | 4 | 370 | Once |
| Ironwake Dismemberment | 8 | 1,100 | Once |
| Third Gate Obsequy | 8 | 2,080 | Once; channel frame 4 |
| Cinderlung Vesper | 8 | 1,490 | Once; sustain frame 6 |
| Defeat | 6 | 900 + hold | Hold frame 6 indefinitely |
| Victory | 6 | 1,780 + hold | Hold frame 6 indefinitely |
| Combat Approach | 8 | 480 + 600 per cycle | Loop frames 3–6 only |
| Combat Return | 8 | 480 + 600 per cycle | Loop frames 3–6 only |
| Brace Activation FX | 4 | 500 | Once; new per-frame timing |
| Brace Persistent Aura | 6 | 900 | Loop; new timing |
| Enhanced Ironwake FX | 8 | 1,100 | Synchronized |
| Third Gate Rear Gate FX | 8 | 2,080 | Synchronized |
| Third Gate Weapon FX | 8 | 2,080 | Synchronized |
| Cinderlung War Breath FX | 8 | 1,490 | Synchronized |

**Inventory:** 11 base sheets (74 frame cells), 6 VFX sheets (42 frame cells), 17 sheets and 116 frame cells total. Canonical master artwork excluded from sheet count.

## Notes

- All timings remain adjustable after playback tests. Visual impact markers do not specify gameplay damage timing.
- Synchronized layers share the same timeline as their base sheet, including holds; their durations are not added to the base animation duration.
- The filenames follow the proposed `base/` and `vfx/` naming convention. Actual final on-disk names have not been independently checked.
- This is an artwork/playback reference only, not an implementation specification.
- Unlockable abilities are intentionally deferred.

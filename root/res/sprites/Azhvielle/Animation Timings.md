# Azhvielle, the Unconfessed — Animation Timings

Frames are numbered from 1 in left-to-right, top-to-bottom order. Pivots are measured from each cell’s top-left corner. For a registered layer, draw its top-left at the world or screen anchor minus its scaled pivot. Use the same scale for a base sheet and its paired cast overlay. The different cell sizes provide room for the Needle’s sweep and casting poses.

The reused Combat Idle has six frames. The provisional 200 ms per frame is from the production brief. The guard and persistent holds are marked separately from the finite durations used to render the review GIFs.

## Base poses

| ID | Asset | Frames | Grid | Cell (px) | Pivot (px) | Durations (ms) | Clear frames | Playback and placement |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| B01 | [Combat Idle](base/Combat%20Idle.png) | 6 | 3 × 2 | 576 × 576 | (310, 507) | 200, 200, 200, 200, 200, 200 | — | Loop 1–6. Provisional 1,200 ms cycle. Approved palm-toss art reused. |
| B02 | [Scepter Sweep](base/Scepter%20Sweep.png) | 8 | 4 × 2 | 768 × 640 | (406, 539) | 100, 120, 140, 160, 60, 100, 140, 120 | — | Once. Physical impact cue 5. Silver trail is optional. |
| B03 | [Gloamweight Sepulcher](base/Gloamweight%20Sepulcher.png) | 8 | 4 × 2 | 640 × 608 | (342, 523) | 100, 140, 180, 200, 300, 80, 180, 120 | — | Once. Compress on 5 and release on 6. |
| B04 | [Mournglass Bloom](base/Mournglass%20Bloom.png) | 8 | 4 × 2 | 640 × 608 | (342, 523) | 100, 140, 180, 200, 280, 70, 180, 120 | — | Once. Gather on 5 and release on 6. |
| B05 | [Gravemantle Rupture](base/Gravemantle%20Rupture.png) | 8 | 4 × 2 | 704 × 640 | (374, 539) | 100, 150, 180, 220, 350, 80, 200, 120 | — | Once. Downward command on 6. |
| B06 | [Causality Nullwake](base/Causality%20Nullwake.png) | 8 | 4 × 2 | 640 × 640 | (342, 539) | 120, 180, 250, 300, 800, 70, 350, 200 | — | Once. Anticipation hold 5 and release 6. |
| B07 | [Defend](base/Defend.png) | 4 | 2 × 2 | 576 × 576 | (310, 507) | 100, 120, variable hold, 150 | — | Variable hold on 3. 500 ms is the review duration only. |
| B08 | [Damage Reaction](base/Damage%20Reaction.png) | 4 | 2 × 2 | 576 × 576 | (310, 507) | 60, 90, 100, 120 | — | Once, then idle. Reused for Gravemantle self-damage. |
| B09 | [Defeat](base/Defeat.png) | 6 | 3 × 2 | 576 × 576 | (310, 507) | 120, 150, 180, 200, 250, indefinite hold | — | Play 1–5, hold 6 indefinitely. Review uses 1,500 ms. |
| B10 | [Victory](base/Victory.png) | 6 | 3 × 2 | 576 × 576 | (310, 507) | 150, 180, 200, 800, 250, indefinite hold | — | Acknowledgment hold 4. Hold 6 indefinitely. Review uses 1,500 ms. |
| B11 | [Combat Approach](base/Combat%20Approach.png) | 8 | 4 × 2 | 640 × 576 | (342, 507) | 120, 120, 150, 150, 150, 150, 120, 120 | — | Replay 3–6 independently. Screen-right in-place walk. |
| B12 | [Combat Return](base/Combat%20Return.png) | 8 | 4 × 2 | 640 × 576 | (342, 507) | 120, 120, 150, 150, 150, 150, 120, 120 | — | Replay 3–6 independently. Screen-left in-place walk, drawn from a rear three-quarter angle. |

## Independent VFX

| ID | Asset | Frames | Grid | Cell (px) | Pivot (px) | Durations (ms) | Clear frames | Playback and placement |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| V01 | [Scepter Sweep - Trail](vfx/Scepter%20Sweep%20-%20Trail.png) | 8 | 4 × 2 | 768 × 640 | (406, 539) | 100, 120, 140, 160, 60, 100, 140, 120 | 1, 2, 8 | Character overlay. Neutral silver arc. Clear 1, 2, 8. |
| V02 | [Gloamweight Sepulcher - Cast](vfx/Gloamweight%20Sepulcher%20-%20Cast.png) | 8 | 4 × 2 | 640 × 608 | (342, 523) | 100, 140, 180, 200, 300, 80, 180, 120 | 1, 8 | Character overlay. Follow the free palm. Clear 1 and 8. |
| V03 | [Gloamweight Sepulcher - Collapse](vfx/Gloamweight%20Sepulcher%20-%20Collapse.png) | 8 | 4 × 2 | 448 × 448 | (224, 224) | 80, 90, 100, 100, 70, 110, 120, 100 | 8 | Target torso center. Once from B03 release. Clear 8. |
| V04 | [Mournglass Bloom - Cast](vfx/Mournglass%20Bloom%20-%20Cast.png) | 8 | 4 × 2 | 640 × 608 | (342, 523) | 100, 140, 180, 200, 280, 70, 180, 120 | 1, 8 | Character overlay. Needle on 3, free hand on other active frames. Clear 1 and 8. |
| V05 | [Mournglass Bloom - Eruption](vfx/Mournglass%20Bloom%20-%20Eruption.png) | 8 | 4 × 2 | 448 × 448 | (224, 393) | 60, 80, 90, 100, 140, 100, 120, 100 | 8 | Target ground. Once from B04 release. Clear 8. |
| V06 | [Gravemantle Rupture - Cast](vfx/Gravemantle%20Rupture%20-%20Cast.png) | 8 | 4 × 2 | 704 × 640 | (374, 539) | 100, 150, 180, 220, 350, 80, 200, 120 | 1, 8 | Character overlay. Tracks the Needle head. Clear 1 and 8. |
| V07 | [Gravemantle Rupture - Ground](vfx/Gravemantle%20Rupture%20-%20Ground.png) | 8 | 4 × 2 | 512 × 448 | (256, 367) | 70, 80, 90, 100, 70, 130, 140, 100 | 8 | Ground contact at fissure hub. Once from B05 release. Clear 8. |
| V08 | [Causality Nullwake - Charge](vfx/Causality%20Nullwake%20-%20Charge.png) | 8 | 4 × 2 | 640 × 640 | (342, 539) | 120, 180, 250, 300, 800, 70, 350, 200 | 1, 8 | Character overlay. Needle on 3, free hand on other active frames. Clear 1 and 8. |
| V09 | [Causality Nullwake - Collapse](vfx/Causality%20Nullwake%20-%20Collapse.png) | 8 | 4 × 2 | 488 × 488 | (244, 244) | 100, 120, 160, 180, 60, 220, 180, 120 | 8 | Target torso center. Once from B06 release. Clear 8. |
| V10 | [Arcane Overcharge - Aura](vfx/Arcane%20Overcharge%20-%20Aura.png) | 6 | 3 × 2 | 576 × 576 | (310, 507) | 200, 200, 200, 200, 200, 200 | — | Character ground. Loop 1–6. Readable across poses. |
| V11 | [Arcane Overcharge - Discharge](vfx/Arcane%20Overcharge%20-%20Discharge.png) | 6 | 3 × 2 | 576 × 576 | (288, 288) | 80, 100, 100, 60, 120, 100 | 6 | Reposition the origin to the current casting point. Once. Clear 6. |
| V12 | [Gravemantle Break - Aura](vfx/Gravemantle%20Break%20-%20Aura.png) | 6 | 3 × 2 | 448 × 448 | (224, 224) | 180, 180, 180, 180, 180, 180 | — | Target waist center. Loop 1–6. |
| V13 | [Arcane Instability - Aura](vfx/Arcane%20Instability%20-%20Aura.png) | 6 | 3 × 2 | 576 × 576 | (310, 507) | 160, 90, 130, 220, 100, 180 | — | Character ground. Loop 1–6 independently of Overcharge. |
| V14 | [Gravemantle Backlash](vfx/Gravemantle%20Backlash.png) | 6 | 3 × 2 | 576 × 576 | (310, 507) | 80, 70, 80, 110, 140, 100 | 6 | Character ground. Self-impact sits near chest (304, 247). Clear 6. |
| V15 | [Frost Charge 1](vfx/Frost%20Charge%201.png) | 6 | 3 × 2 | 448 × 448 | (224, 393) | 200, 200, 200, 200, 200, 200 | — | Target ground. Loop 1–6. Sparse single cluster. |
| V16 | [Frost Charge 2](vfx/Frost%20Charge%202.png) | 6 | 3 × 2 | 448 × 448 | (224, 393) | 200, 200, 200, 200, 200, 200 | — | Target ground. Loop 1–6. Denser paired clusters. |
| V17 | [Frost Trigger - Freeze](vfx/Frost%20Trigger%20-%20Freeze.png) | 6 | 3 × 2 | 448 × 448 | (224, 393) | 70, 80, 90, 100, 140, 100 | — | Target ground. Once. Frame 6 shares Frozen Hold frame 1. |
| V18 | [Frozen - Hold](vfx/Frozen%20-%20Hold.png) | 6 | 3 × 2 | 448 × 448 | (224, 393) | 240, 240, 240, 240, 240, 240 | — | Target ground. Loop 1–6 or hold 1. Scale the shell about its pivot to recipient. |
| V19 | [Frozen - Shatter](vfx/Frozen%20-%20Shatter.png) | 6 | 3 × 2 | 448 × 448 | (224, 393) | 90, 90, 60, 90, 130, 100 | 6 | Target ground. Same scale as Hold. Clear 6. |
| V20 | [Frostbite - Aura](vfx/Frostbite%20-%20Aura.png) | 6 | 3 × 2 | 448 × 448 | (224, 393) | 200, 200, 200, 200, 200, 200 | — | Target ground. Loop 1–6 alongside Frozen and after Shatter. |
| V21 | [Frostbite - Tick](vfx/Frostbite%20-%20Tick.png) | 6 | 3 × 2 | 448 × 448 | (224, 224) | 60, 70, 60, 90, 110, 90 | 6 | Target torso. Independent pulse. Clear 6. |
| V22 | [Mournglass Backlash](vfx/Mournglass%20Backlash.png) | 6 | 3 × 2 | 576 × 576 | (310, 507) | 70, 80, 90, 100, 140, 100 | — | Character ground. Ends on Frozen Hold scaled to 135%, at cell offset (18, −24). |

## Layer synchronization

- Play V01, V02, V04, V06 and V08 in lockstep with their paired base sheet. The physical sweep cue is B02 frame 5. Ordinary spell release is frame 6. Spawn the associated target effect on the release cue and let it finish on its own timeline.
- V15 and V16 share the same ground pivot. On threshold, replace the charge layer with V17. Switch from its final frame to V18 frame 1. Apply V19 at the same scale and pivot on release. V20 and V21 run independently, including after shatter, while the target has Frostbite.
- V22 uses the idle pivot. To continue into generic Frozen Hold on Azhvielle, scale V18 by 1.35 about its native ground pivot and place its ground pivot 10 source pixels right of Azhvielle’s ground pivot. Equivalently place the resized V18 cell at (18, −24) relative to the 576 × 576 character cell’s top-left. Use the same transform for V19. The self-freeze preview keeps Azhvielle on one pose and uses only Frozen layers.
- Overcharge, Break and Instability have independent loop clocks. Apply Break at the target’s waist. Place Discharge’s center at the current spell’s casting point. Its short preview lead-in peaks around the release; the physical Scepter Sweep leaves the stored aura active. The Gravemantle self-impact example pairs V14 with Damage Reaction, then shows V13 alongside V10.
- Target effects contain only effect art. Preview positions and sizes demonstrate registration against the goblin silhouette. Gameplay state determines which effects are active and for how long.

Production and preview checks are recorded in the [Production Checklist](Production%20Checklist.md).


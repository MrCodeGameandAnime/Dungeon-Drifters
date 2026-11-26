# Zhaivra Kelyth Animation Timings

Playback proposals for the baseline art package. Durations are in milliseconds. Frames are numbered from 1 in left-to-right, top-to-bottom order. Pivots are in cell-local pixels from the top left. Align each base pivot to the same world-space ground point. Character overlays share their base sheet’s pivot. The listed anchors are registration points for integration and do not change the assets.

## Base character poses

| Asset | Grid | Cell size (px) | Durations | Playback and alignment |
| --- | --- | --- | --- | --- |
| [Combat Idle](base/Combat%20Idle.png) | 3 × 2 | 576 × 576 | 180, 180, 220, 260, 180, 180 | Loop. Shared actor anchor (355, 506). |
| [Mournpoint Verdict](base/Mournpoint%20Verdict.png) | 4 × 2 | 640 × 640 | 100, 120, 140, 200, 60, 100, 120, 120 | Release 5. Anchor (387, 550). Use Standard Arrow. |
| [Defend](base/Defend.png) | 2 × 2 | 576 × 576 | 100, 120, variable hold, 150 | Hold 3 at guard; release to frame 4. Anchor (355, 506). |
| [Damage Reaction](base/Damage%20Reaction.png) | 2 × 2 | 576 × 576 | 60, 90, 100, 120 | Once, then idle. Anchor (355, 506). |
| [Defeat](base/Defeat.png) | 3 × 2 | 576 × 576 | 120, 150, 180, 200, 250, indefinite hold | Hold 6. Anchor (355, 506). |
| [Victory](base/Victory.png) | 3 × 2 | 576 × 576 | 150, 180, 200, 800, 250, indefinite hold | Inspection hold 4; persistent stance 6. Anchor (355, 506). |
| [Combat Approach](base/Combat%20Approach.png) | 4 × 2 | 672 × 576 | 120, 120, 150, 150, 150, 150, 120, 120 | Loop 3–6 as needed to move right. Anchor (403, 506). |
| [Combat Return](base/Combat%20Return.png) | 4 × 2 | 672 × 576 | 120, 120, 150, 150, 150, 150, 120, 120 | Loop 3–6 as needed to move left. Anchor (403, 506). |
| [Hollowstring Trine](base/Hollowstring%20Trine.png) | 4 × 2 | 640 × 640 | 100, 120, 150, 180, 220, 60, 150, 120 | One release on 6. Anchor (387, 538). |
| [Nightskein Deluge](base/Nightskein%20Deluge.png) | 4 × 2 | 640 × 672 | 100, 140, 150, 180, 300, 70, 180, 120 | Elevated release 6. Anchor (387, 554). |
| [Infusion Preparation](base/Infusion%20Preparation.png) | 3 × 2 | 576 × 576 | 120, 180, 200, 300, 180, 120 | Shared by Fire and Poison. Anchor (355, 506). |
| [Infused Barb](base/Infused%20Barb.png) | 4 × 2 | 640 × 640 | 100, 140, 140, 180, 250, 60, 150, 120 | Release 6. Exact same base for both variants. Anchor (387, 538). |
| [Starless Meridian Obsequy](base/Starless%20Meridian%20Obsequy.png) | 4 × 2 | 640 × 640 | 120, 180, 250, 300, 650, 60, 350, 200 | Anticipation hold 5, release 6. Anchor (387, 538). |

## Independent effects

| Asset | Grid | Cell size (px) | Durations | Playback and alignment |
| --- | --- | --- | --- | --- |
| [Standard Arrow](vfx/Standard%20Arrow.png) | 2 × 2 | 320 × 96 | 80 each | Repeatable flight, center (160, 48). |
| [Hollowstring Trine - Arrow Split](vfx/Hollowstring%20Trine%20-%20Arrow%20Split.png) | 4 × 2 | 320 × 128 | 60 each | Start at base release. Center (160, 64); model one visual sequence. |
| [Nightskein Deluge - Shadow Volley](vfx/Nightskein%20Deluge%20-%20Shadow%20Volley.png) | 4 × 2 | 384 × 256 | 90 each | Start after elevated release; descending path is independent. Center (192, 128). |
| [Nightskein Deluge - Impact](vfx/Nightskein%20Deluge%20-%20Impact.png) | 3 × 2 | 544 × 320 | 70 each | Start on arrival. Contact pivot (300, 210). |
| [Fire Infusion - Preparation](vfx/Fire%20Infusion%20-%20Preparation.png) | 3 × 2 | 576 × 576 | 120, 180, 200, 300, 180, 120 | Overlay Infusion Preparation using its pivot. Frames 1 and 6 are clear. |
| [Poison Infusion - Preparation](vfx/Poison%20Infusion%20-%20Preparation.png) | 3 × 2 | 576 × 576 | 120, 180, 200, 300, 180, 120 | Overlay Infusion Preparation using its pivot. Frames 1 and 6 are clear. |
| [Fire Infusion - Ready Aura](vfx/Fire%20Infusion%20-%20Ready%20Aura.png) | 3 × 2 | 576 × 576 | 200 each | Loop over idle while Fire is prepared; use the idle pivot. |
| [Poison Infusion - Ready Aura](vfx/Poison%20Infusion%20-%20Ready%20Aura.png) | 3 × 2 | 576 × 576 | 200 each | Loop over idle while Poison is prepared; use the idle pivot. |
| [Infused Barb - Fire Projectile](vfx/Infused%20Barb%20-%20Fire%20Projectile.png) | 3 × 2 | 320 × 128 | 80 each | Repeatable flight until arrival. Tip pivot (254, 64). |
| [Infused Barb - Poison Projectile](vfx/Infused%20Barb%20-%20Poison%20Projectile.png) | 3 × 2 | 320 × 128 | 80 each | Repeatable flight until arrival. Tip pivot (254, 64). |
| [Infused Barb - Fire Impact](vfx/Infused%20Barb%20-%20Fire%20Impact.png) | 3 × 2 | 384 × 256 | 70 each | Once on arrival. Contact pivot (216, 128). |
| [Infused Barb - Poison Impact](vfx/Infused%20Barb%20-%20Poison%20Impact.png) | 3 × 2 | 384 × 256 | 70 each | Once on arrival. Contact pivot (216, 128). |
| [Starless Meridian Obsequy - Charge](vfx/Starless%20Meridian%20Obsequy%20-%20Charge.png) | 4 × 2 | 640 × 640 | 120, 180, 250, 300, 650, 60, 350, 200 | Overlay matching base. Frames 1 and 8 are clear. |
| [Starless Meridian Obsequy - Projectile](vfx/Starless%20Meridian%20Obsequy%20-%20Projectile.png) | 4 × 2 | 384 × 128 | 60 each | Independent flight. Leading pivot (310, 64). |
| [Starless Meridian Obsequy - Impact](vfx/Starless%20Meridian%20Obsequy%20-%20Impact.png) | 4 × 2 | 384 × 384 | 90 each | Once on arrival. Contact pivot (192, 192). |

## Synchronization

- Mournpoint uses the shared Standard Arrow after release frame 5.
- Hollowstring’s split begins on its single release in frame 6. The three visible arrows are one authored effect sequence.
- Nightskein uses its independent volley and impact after frame 6. Position the volley and impact in their own presentation space.
- Start the chosen Infusion Preparation overlay at the same time as the base preparation. The ready aura runs on its own clock while a payload is stored. Both Infused Barb variants use the same base shot and spawn their selected projectile on frame 6.
- Run the Starless charge on the base timeline. The release on frame 6 starts the independent projectile.
- Projectile movement and arrival are controlled externally. Preview positions are illustrative. Frame durations prescribe no travel distance, target count, damage events, or gameplay rules.
- No Sprite Pop or in-game timing has been approved. See [Production Checklist](Production%20Checklist.md) for verification status.


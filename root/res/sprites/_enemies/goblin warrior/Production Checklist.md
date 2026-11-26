# Goblin Warrior Production Checklist

| Asset | Cells | Static review | PNG audit |
| --- | ---: | --- | --- |
| [Combat Idle](base/Combat%20Idle.png) | 6 | Canonical artwork and planted-foot comparison | Pass |
| [Cleaver Strike](base/Cleaver%20Strike.png) | 6 | Wind-up, strike, follow-through and neutral transition | Pass |
| [Cleaver Strike VFX](vfx/Cleaver%20Strike.png) | 4 | Blade path and clear final cell | Pass |
| [Shieldbreaker Chop](base/Shieldbreaker%20Chop.png) | 8 | Overhead hold, descending strike and low recovery | Pass |
| [Shieldbreaker Chop VFX](vfx/Shieldbreaker%20Chop.png) | 6 | Descending path and clear final cell | Pass |
| [Damage Reaction](base/Damage%20Reaction.png) | 4 | Standing recoil and transition to neutral | Pass |
| [Defeat](base/Defeat.png) | 6 | Collapse with intact blade and stable final pose | Pass |
| [Combat Approach](base/Combat%20Approach.png) | 8 | Alternating support, planted brake and gait join | Pass |
| [Combat Return](base/Combat%20Return.png) | 8 | Backward footwork, alternating support and gait join | Pass |
| [Victory](base/Victory.png) | 8 | Blade-raised stance, planted surges and loop join | Pass |
| **Total** | **64** | **Eight base sheets and two independent effects** | |

## Verification scope

- **Master.** The original was renamed to [Goblin Warrior Sprite.png](Goblin%20Warrior%20Sprite.png). SHA-256 matches the recorded original at `f3d1be7115fdaa3e86ee3f7b96e07c93ecf0f76b744c38a3f4ebcc460fb9fb76`.
- **Static visual inspection.** Compared frames with the master and Combat Idle for the left-facing silhouette, broad proportions, fur and plate armor, tied-back hair, blade hand, jagged blade and ring pommel. Checked visible silhouettes and backgrounds, the pose progressions, the movement and victory joins, and the VFX separation. The standing recoil, opposite approach passing step, return source boundary and raised victory loop join were corrected during review.
- **Artwork fidelity.** Combat Idle uses localized movement of the canonical pixels. The other distinctive action poses are reference-based redraws assembled around a shared scale and pivot. Serrations, hardware, and cloth details have minor frame-to-frame variation. The broad silhouette, weapon silhouette and handedness remain recognizable. Gait footfall can drift at a renderer-controlled speed different from the review preview.
- **Automated PNG and transparency.** Confirmed exact grid dimensions, RGBA, all 64 cells, transparent padding, active alpha, clear final effect cells, and a byte-identical final defeat hold. Grounded base poses meet the registered baseline within one pixel. Idle feet and the shared neutral transitions were compared byte for byte. [Animation timings](Animation%20Timings.md) records pivots and synchronized release cues.
- **Animated preview generation and decoding.** The sibling project support folder contains `Goblin Warrior Animation Review/Previews/index.html` and a per-file decode report. All 16 GIFs decoded at the expected durations. The gallery groups eight base and eight combined or playback demonstrations. Both strongest effect frames were checked against their documented release cues.
- **Browser playback review.** Visually sampled Cleaver Strike with its trail, the Shieldbreaker lift, the forward and backward steps, the Victory loop, and the settled defeat hold. Inspected both release composites at their exact cue times separately.
- **Sprite Pop and in-game verification.** Pending.

![](<res/Dungeon Drifters Heros.png>)

Dungeon Drifters is a character-driven fantasy RPG set in Ketlyv.

Choose one of four distinct Drifters, master their unique combat style, grow
stronger through battle, evolve their signature weapon, and push deeper into
a dangerous world shaped by each character's identity and abilities.

The game is currently in active development. The playable build covers the
opening journey through the surface route, ending at the entrance to the
dungeon.

## The Drifters

### <img src="res/Ser%20Branoc%20Sprite.png" width="32" height="32"> Ser Branoc, the Unbroken Crest 

A relentless close-range fighter built around endurance, retaliation, and
overwhelming physical force.

Branoc plants himself in the fight, survives what should break him, and answers
with brutal counterpressure. His signature weapon, Sunder-Spire, and techniques
such as Brace and Ironwake Dismemberment reinforce his identity:

**plant → endure → answer**

### Azhvielle, the Unconfessed

A dangerous Black Mage whose combat style revolves around powerful magic,
Frost, Gravemantle, and calculated resource use.

Azhvielle can shape the pace of a fight through elemental pressure and
high-impact spell routes rather than meeting enemies head-on.

### Zhaivra Kelyth, the Uncontrolled Reagent

A Rogue Archer built around preparation, precision, and alchemical aggression.

Zhaivra can prepare specialized payloads, including Fire and Poison Infused
Barbs, turning inventory preparation and status pressure into part of her
combat identity.

### Joruun Veyr, the Bloody Storm Monk

A fast, aggressive Monk whose techniques draw on Water, Air, and Lightning.

Joruun chains martial pressure with elemental techniques, Stun, and rapid
combat flow to overwhelm enemies before they can settle into the fight.

## Current Playable Build

The current build contains the complete opening sequence for all four Drifters:

- Play through eight authored surface encounters that escalate from lone Goblins to the Goblin Lord.
- Fight single and multi-enemy battles using attacks, Defend, healing, items, Supers, targeting, and each Drifter's unique mechanics.
- Earn EXP, gold, Growth Points, and rewards while developing permanent stats and combat progression.
- Inspect your Drifter's character sheet, skills, inventory, map, progression, and signature weapon.
- Use three single-use Rest points to restore HP and Mana while deciding when to press forward.
- Save, quit, load, and continue the same run with persistent progression between sessions.
- Defeat the Goblin Lord and reach the dungeon entrance, the current endpoint of the playable build.

## Play Instructions

From the `root/` project directory, run:

```powershell
..\.venv\Scripts\python.exe src\run_game.py
```

You can also run `root/src/run_game.py` directly from PyCharm.

## Screenshots

The current terminal presentation is shown below:

![Structured move menu with Brace and empowered Ironwake](res/screenshots/DD_001.jpeg)

*Structured move menu showing authored roles, resource costs, Brace rules, and the dynamic Ironwake payoff label.*

![Battle HUD with five ordinary actions and persistent Super meter](res/screenshots/DD_002.jpeg)

*Battle HUD showing the five ordinary actions, unavailable-state labels, bounded battle log, and persistent Super meter.*

![Brace payoff resolved through Ironwake Dismemberment](res/screenshots/DD_003.jpeg)

*Battle log after Brace and an empowered Ironwake Dismemberment action.*


## Architecture

Dungeon Drifters is built around a modular, testable architecture that separates
game state, combat rules, authored content, presentation, and persistence.

Key foundations include:

- Structured `GameState` and player/world state ownership.
- A deterministic content-authoring system for Drifters, enemies, weapons,
  encounters, and routes.
- Resolver-driven turn-based combat with structured moves and results.
- Separate domain, presentation, and terminal UI layers.
- Versioned persistent game state with save/load support.
- Development tooling for content scaffolding, validation, and balance testing.

See the project documentation and change log for detailed implementation history
and architecture.

## Testing

From the `root/` project directory:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
python -m compileall src tests tools
```

## Project Structure

```text
Dungeon-Drifters/
├── root/
│   ├── src/        # Game source
│   ├── tests/      # Test suite
│   └── tools/      # Development and validation tools
├── docs/           # Project documentation
├── res/            # Screenshots and other resources
└── .github/        # CI workflows
```

The runnable Python project lives under `root/`; documentation, resources, and
repository-level configuration remain at the repository root.

## Change Log

The complete version history is maintained in the [change log](docs/change/change%20log.md).

## Contact

For questions or support, please get in touch with the maintainer:

- Email: [mrcodegameandanime@gmail.com](mailto:mrcodegameandanime@gmail.com)
- GitHub: [MrCodeGameAndAnime](https://github.com/MrCodeGameAndAnime)

## Development

- Use the [content authoring guide](docs/content%20creation/content%20authoring.md)
  to add Drifters, enemies, weapons, encounters, or routes through the supported
  scaffolding and validation workflow.
- `tools/balance_probe.py` provides deterministic combat simulations and
  reproducible balance artifacts.

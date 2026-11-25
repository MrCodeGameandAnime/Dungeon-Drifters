![](<../root/res/Dungeon Drifters Heros.png>)
---
Dungeon Drifters is a character-driven fantasy RPG set in Ketlyv.

**Current version: v0.8**

Choose one of four distinct Drifters, master their unique combat style, grow
stronger through battle, evolve their signature weapon, and push deeper into
a dangerous world shaped by each character's identity and abilities.

The game is in active development. The current v0.8 build includes the surface
route, the Hub, the first three dungeon floors, and a specialized Hub economy.
The same Python gameplay runtime is playable in the browser and through the
terminal; later floors remain in development.

## The Drifters

# <img src="../root/res/sprites/Ser%20Branoc/Ser%20Branoc%20Sprite.png" width="48" height="48"> Ser Branoc, the Unbroken Crest

A relentless close-range fighter built around endurance, retaliation, and
overwhelming physical force.

Branoc plants himself in the fight, survives what should break him, and answers
with brutal counterpressure. His signature weapon, Sunder-Spire, and techniques
such as Brace and Ironwake Dismemberment reinforce his identity:

**plant → endure → answer**

# <img src="../root/res/sprites/Azhvielle/Azhvielle%20Sprite.png" width="48" height="48"> Azhvielle, the Unconfessed

A dangerous Black Mage whose combat style revolves around powerful magic,
Frost, Gravemantle, and calculated resource use.

Azhvielle can shape the pace of a fight through elemental pressure and
high-impact spell routes rather than meeting enemies head-on.

# <img src="../root/res/sprites/Zhaivra%20Kelyth/Zhaivra%20Kelyth%20Sprite.png" width="48" height="48"> Zhaivra Kelyth, the Uncontrolled Reagent

A Rogue Archer built around preparation, precision, and alchemical aggression.

Zhaivra can prepare specialized payloads, including Fire and Poison Infused
Barbs, turning inventory preparation and status pressure into part of her
combat identity.

# <img src="../root/res/sprites/Joruun%20Veyr/Joruun%20Veyr%20Sprite.png" width="48" height="48"> Joruun Veyr, the Bloody Storm Monk

A fast, aggressive Monk whose techniques draw on Water, Air, and Lightning.

Joruun chains martial pressure with elemental techniques, Stun, and rapid
combat flow to overwhelm enemies before they can settle into the fight.

## Current Playable Build

The current development build is playable in the browser and terminal and
covers the route through the Floor III boss:

- Play the eight-encounter surface route through the Goblin Lord.
- Recruit and manage the permanent Drifter roster in the Hub, then choose an
  active pair for ordinary encounters.
- Complete Floor I's ten encounters, two Rest points, and Goblin Lord; extract
  to the Hub to secure rewards and prepare another run.
- Continue through Floor II's ten encounters and two Rest points. At the
  pre-boss Rest, choose D3 or D4 as a temporary third combatant for the boss.
  The helper does not join the permanent roster or receive boss XP.
- After clearing Floor II, recruit D3 and D4 independently in the Hub for 65
  shared gold each. Permanent recruits start at Level 1.
- Complete Floor III's ten encounters and two Rest points. Ordinary encounters
  use the active pair; the final boss requires all four permanent Drifters.
  Pre-boss rewards stay with their earning pair, while boss XP is split across
  the four participants before each one's Intuition bonus.
- Store supplies in the Hub, prepare a six-unit carried pack, use consumables
  and alchemy, and choose between Rest, extraction, and emergency exits.
- Spend Growth Points on character advancement, manage each Drifter's move
  loadout, and respec at the Hub.
- Assign the reserve pair to passive, 20-minute expeditions targeting
  completed floors. Training and eligible floor-material assignments are
  available; energy gates expeditions only, never ordinary dungeon play.
- Use four specialized Hub vendors: the Merchant for general commerce, the
  Blacksmith for weapons and armor, the Enchanter for armor modifiers and
  learned affixes, and the Alchemist for consumables and recipes.
- Buy and sell through finite vendor stock, use eligible same-visit buyback,
  and replenish stock after qualifying outings. Trade uninstalled weapon
  components while keeping installed parts attached to each weapon.
- Craft and improve signature weapons, upgrade armor, and manage fixed
  Ring/Pendant equipment. Build separate Alchemy and Enchanting progression,
  master consumable recipes, craft Mana Potions, and apply permanently learned
  armor affixes with Magic Crystals.
- Inspect the party, inventory, map, and equipment; save, quit, load, and
  continue with persistent progression. v0.8 builds use local saves; cloud
  synchronization is not enabled.

Further dungeon floors, additional expedition reward sources, and M7-M9
systems remain future work.

## Play Instructions

From the `root/` project directory, run:

```powershell
..\.venv\Scripts\python.exe src\run_game.py
```

You can also run `root/src/run_game.py` directly from PyCharm.

## Screenshots

The current terminal presentation is shown below:

![Structured move menu with Brace and empowered Ironwake](../root/res/screenshots/DD_001.jpeg)

*Structured move menu showing authored roles, resource costs, Brace rules, and the dynamic Ironwake payoff label.*

![Battle HUD with five ordinary actions and persistent Super meter](../root/res/screenshots/DD_002.jpeg)

*Battle HUD showing the five ordinary actions, unavailable-state labels, bounded battle log, and persistent Super meter.*

![Brace payoff resolved through Ironwake Dismemberment](../root/res/screenshots/DD_003.jpeg)

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

### Save and Cloud Data

The versioned `GameState` payload stores gameplay progression, including the
permanent roster and active pair, character advancement, shared inventory and
carried supplies, signature weapons, equipment, route state, and pending outing
rewards. Supported legacy disk saves are validated and migrated before use; the
original saved envelope is not mutated. A separate local profile envelope
stores the stable profile ID, optional DD account association, local sequence,
accepted remote revision, sync state, and payload digest. The local profile
store is authoritative for immediate play: saves are committed locally first,
and a player can continue playing, saving, quitting, and loading without an
account or network connection. **Cloud synchronization is not enabled in v0.8
builds.** The repository contains profile-sync interfaces and a DD-owned
HTTPS/JSON API backed by PostgreSQL as integration foundations for future host
support; they do not provide account linking or cloud sync in the v0.8 game.

The synchronization foundation keeps remote revisions immutable and idempotent.
A stale revision preserves the local branch and remote head as separate conflict
evidence; resolving it is explicit, with recovery data retained before the
active profile changes. Sync ordering does not depend on timestamps or silently
merge progression. These are architectural contracts, not features enabled in
the distributed v0.8 builds.

Accounts, linked platform identities, sessions, and entitlements remain service
data outside progression. Entitlements are account-scoped and service-owned;
source, expiry, and revocation can be represented without granting authority to
the client save. Ordinary earned gold remains gameplay data in `GameState`,
with dungeon-hub funds represented in the party state. Any future
platform-restricted currency must use separate account/service data rather than
game-state fields. Firebase has not been selected; provider integrations must
sit behind the DD contracts and be qualified independently on each platform.

See the project documentation and change log for detailed implementation history
and architecture.

## Testing

From the `root/` project directory:

```powershell
..\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
..\.venv\Scripts\python.exe -m pytest
..\.venv\Scripts\python.exe -m compileall src tests tools
```

## Project Structure

```text
Dungeon-Drifters/
├── docs/           # Project documentation
├── root/
│   ├── src/        # Game source
│   ├── tests/      # Test suite
│   └── tools/      # Development and validation tools
│   └── res/        # Game resources and screenshots
└── .github/        # CI workflows
```

The runnable Python project lives under `root/`; documentation, resources, and
repository-level configuration remain at the repository root.

## Change Log

The complete version history is maintained in the [change log](CHANGE_LOG.md).

## Contact

For questions or support, please get in touch with the maintainer:

- Email: [support@404builds.com](support@404builds.com)
- GitHub: [MrCodeGameAndAnime](https://github.com/MrCodeGameAndAnime)

## Development

- Use the [content authoring guide](CONTENT_AUTHORING.md)
  to add Drifters, enemies, weapons, encounters, or routes through the supported
  scaffolding and validation workflow.
- `root/tools/balance_probe.py` provides deterministic combat simulations and
  reproducible balance artifacts.

"""Ser Branoc character profile."""

from app.player.character import Brawler
from app.world.character_profiles.profile import CharacterProfile


PROFILE = CharacterProfile(
    choice="1",
    display_name="Ser Branoc, the Unbroken Crest",
    character_factory=Brawler,
    ascii_art=r"""
        /\_/\                 .-^^^^^^^^^-.                 /\_/\
   ____/ / \ \____        .-'  RHOM-GHAL  '-.        ____/ / \ \____
  /___  /___\  ___\______/___________________\______/___  /___\  ___\
      | |   | |      _.-' /\    /\    /\    /\ '-._      | |   | |
   ___|_|___|_|___.-'    /  \__/  \__/  \__/  \    '-.___|_|___|_|___
  /  /\   /\   /\ \    / /\  /\  /\  /\  /\ \    / /\   /\   /\  \
 /__/  \_/  \_/  \_\  /_/  \/  \/  \/  \/  \_\  /_/  \_/  \_/  \__\
 |                  \ |      .---------------.      | /                  |
 |   THE UNBROKEN    \|    .'  /\   /\   /\   '.    |/    THIRD GATE    |
 |      CREST         |   /   /  \_/  \_/  \    \   |      SENTINEL     |
 |                    |  |   / /\   /\   /\  \   |  |                   |
 |      /\    /\      |  |  /_/  \_/  \_/  \__\  |  |      /\    /\     |
 |_____/  \__/  \_____|  |       __________       |  |_____/  \__/  \____|
 \                  /   |      /  ______  \      |   \                   /
  \_________________/    |     /__/|    |\__\     |    \_________________/
        \                |     |  || /\ ||  |     |                /
         '---------------|     |__||_||_||__|     |---------------'
                         '--------\_||_/--------'
              .============ HONOR  DUTY  ENDURE ============.
               '============================================'
""",
    origin_title="Exiled Sentinel of Rhom-Ghal",
    biography="""From the Iron-Spires of Rhom-Ghal comes a knight without a crest. Once Lord-Commander of the mountain 
vanguard, Branoc surrendered his name, rank, and homeland to spare the soldiers under his command. Now he wanders the 
outer kingdoms in scarred Deep-Iron plate, accepting no gold for his sword, only provisions and information. Behind the 
narrow grilles of his helm is no revenant or cursed immortal. Branoc is flesh and blood, sustained by the Rhom-Ghalian 
Lung, a punishing discipline that allows the mountain knights to fight through thin air, smoke, exhaustion, and pain. 
He carries Sunder-Spire, a massive Great-Flamberge forged from broken Deep-Iron. Its rippled edge tears through guards 
and chainmail, while Branoc’s weight and momentum turn every swing into a crushing advance.""",
    dungeon_motive="""He has entered the dungeon in search of a lost mark of the Third Gate, believing it may lead him 
    to the scattered remnants of his fallen order. He does not know what waits beneath the stone.""",
    combat_role="Heavy Vanguard",
    combat_summary="""Branoc is slow, durable, and difficult to interrupt. He controls space through sweeping attacks, 
    heavy stagger, and relentless forward pressure.""",
    strengths="Defense, endurance, guard breaking, crowd control",
    weaknesses="Speed, recovery time, limited mobility",
    weapon="Sunder-Spire",
    discipline="Rhom-Ghalian Lung",
    quote="“Endurance is merely suffering with direction.”",
)


"""Zhaivra Kelyth character profile."""

from app.player.character import RogueArcher
from app.world.character_profiles.profile import CharacterProfile


PROFILE = CharacterProfile(
    choice="3",
    short_name="Zhaivra Kelyth",
    display_name="Zhaivra Kelyth, the Uncontrolled Reagent",
    character_factory=RogueArcher,
    ascii_art=r"""
+-------------------------------------------------------------------------+
|                                  /\                                     |
|                  __             /  \                __                  |
|              __/  \___________/ /\ \___________/  \__                   |
|          __/      \         / /  \ \         /      \__                 |
|       _/    _/\_ \_______/ /____\ \_______/ _/\_    \_                  |
|     /_____/ /  \__________________________/  \ \_____\                  |
|                .---------------------------------------.                |
|              /                    /\                   \                |
|   __/\__    /                    /  \                   \      __/\__   |
|_/      \_  |                    / /\ \                     | _/      \_ |
|\_  /\  _/  |                   / /  \ \                    | \_  /\  _/ |
|  \/  \/    |                  /_/ /\ \_\                   |   \/  \/   |
|     ||     |                     /  \                      |     ||     |
|     ||     |     <\             / /\ \              />     |     ||     |
|   .[==].   |    <<\            / /  \ \            />>     |   .[==].   |
|   |:++:|   |   <<<\           <  /||\  >          />>>     |   |:++:|   |
|   |:++:|   |   << /            \/ || \/            \ >>    |   |:++:|   |
|    \__/    |     </               ||                 \>    |    \__/    |
|            |                      ||                       |            |
|            |                     /||\                      |            |
|            |                    /_||_\                     |            |
|             \                     ||                    /               |
|              \                    ||                   /                |
|                '------------------|+-------------------'                |
|                         \__________________|__________________/         |
|                .---------------------------------------.                |
|              /  THE FLAME THAT REFUSES ITS VESSEL     \                 |
|                '---------------------------------------'                |
+-------------------------------------------------------------------------+
""",
    origin_title="Wandering Ashvein of Nhal Voryss",
    biography="""From the ever-burning arteries of Nhal Voryss comes an archer whose perfect shot moved an entire city. 
    Zhaivra Kelyth 
once served the Ashvein Survey, a caste of alchemical rangers responsible for maintaining the volatile passages of
the Hollow Colossus, the immense petrified organism within which her people built their civilization. Precise, 
analytical, and relentlessly prepared, she learned to read air currents through drifting mineral dust and identify 
combustible gases by the way they distorted distant light. She carries Sathren, a recurved bow grown from the bone-fiber 
of the Hollow Colossus and fitted with six internal reservoirs. A rotating thumb-ring coats each arrow with a selected 
compound moments before release, allowing Zhaivra to transform the battlefield one calculated reaction at a time.""",
    dungeon_motive="""Zhaivra entered the dungeon after discovering traces of bone beneath a ruined surface monastery 
    that appeared identical 
to the Hollow Colossus. She believes something buried within may explain what her homeland truly is and whether the 
First Turning can ever be undone.""",
    combat_role="Alchemical Marksman",
    combat_summary="""Zhaivra is a deliberate ranged combatant who controls terrain through sequenced reactions, 
    environmental manipulation, 
and carefully rationed ammunition. She rarely chooses the most destructive shot when a more efficient one will 
achieve the same result.""",
    strengths="Precision, battlefield control, armor disruption, environmental analysis",
    weaknesses="Limited compounds, preparation requirements, changing weather, overreliance on calculation",
    weapon="Sathren",
    discipline="Ashvein Alchemy",
    quote="“An arrow can strike exactly where you intended and still become the worst mistake of your life.”",
    selection_summary="precise, prepared, resource-limited",
)

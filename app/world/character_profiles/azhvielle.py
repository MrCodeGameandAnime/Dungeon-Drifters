"""Azhvielle character profile."""

from app.player.character import BlackMage
from app.world.character_profiles.profile import CharacterProfile


PROFILE = CharacterProfile(
    choice="2",
    display_name="Azhvielle, the Unconfessed",
    character_factory=BlackMage,
    ascii_art=r"""
                                     o                                     
                                    (o)                                    
                                     |                                     
                                  .--^--.                                  
                               .-'  /|\  '-.                               
                             --<   / | \   >--                             
      |       |   .-------------------------------------.   |       |      
         \     /   .-'               |               '-.   \     /         
           \  / .-'      .-----------------------.      '-. \  /           
  <--------o----<=====>----/----<  .---.  >----\----<=====>----o-------->  
         |   |    /      /      .-'  |  '-.      \      \    |   |         
    <--------o----------<------<    (O)    >------>----------o-------->    
         |   |    \      \      '-.  |  .-'      /      /    |   |         
  <--------o----<=====>----\----<  '---'  >----/----<=====>----o-------->  
           /  \ '-.      '-----------------------'      .-' /  \           
         /     \   '-.               |               .-'   /     \         
      |       |   '-------------------------------------'   |       |      
      .--.             /\            |            /\             .--.      
    .'    |           /  \           |           /  \           |    '.    
   /      |          /    \          |          /    \          |      \   
  |       |         <      >         |         <      >         |       |  
   \      |          \    /          |          \    /          |      /   
   '.    /            \  /           |           \  /            \    .'   
      '--'      o-------\/-------o   +   o-------\/-------o      '--'      
           |       |         \       |       /         |       |           
           o-------o----------o------+------o----------o-------o           
           |       |          \      |      /          |       |           
              <|>     <|>          \    /          <|>     <|>             
              V       V             <O>             V       V              
                                     V                                     
""",
    origin_title="Disputed Witch of the Ninth Court",
    biography="""From the vanished cities of Vharosyne comes a witch whom history cannot properly identify. Azhvielle 
appears across contradictory records as Azhvielle of the Ninth Court or the Oakhaven Archivist among many more. 
Historians dispute whether these names describe one woman, several descendants, or a recurring legend. 

She served as a court witch, healer, archivist, tutor, and adviser to rulers whose kingdoms now survive only as 
footnotes. Countless centuries have left her cynical, practical, and thoroughly unimpressed by end divine kingdoms

Through ancient Vharosynian Causal Sorcery, Azhvielle commands fire, water, ice, air, earth, metal, lightning, smoke, 
and their combined forms. Every spell, however, may cause an unrelated anomaly elsewhere. A spark might trigger a 
distant landslide, while a volcanic eruption might merely give a stranger temporary musical talent. The scale of the 
spell offers no clue to the consequence.

Azhvielle therefore avoids magic whenever an ordinary solution exists, relying instead on experience, observation, and 
the Needle of Plain Iron.

The covenant bound within her soul also prevents her from invoking holy magic. Divine power recognizes something 
impossible inside her and attempts to tear it free.""",
    dungeon_motive="""She entered the dungeon after learning that a surviving Vharosynian record had been recovered 
below. She refuses to explain what it contains or why it bears her name.""",
    combat_role="Elemental Controller",
    combat_summary="Azhvielle offers immense elemental range and battlefield control, but every spell risks "
"consequences beyond her sight.",
    strengths="Elemental mastery, adaptability, battlefield control, ancient knowledge",
    weaknesses="Unpredictable consequences, holy magic, mortal durability, reluctance to cast",
    weapon="Needle of Plain Iron*",
    discipline="Vharosynian Causal Sorcery",
    quote="“Yes, I can solve this with magic. That does not make it sensible.”",
)


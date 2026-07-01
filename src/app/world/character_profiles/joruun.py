"""Joruun Veyr character profile."""

from app.player.character import Monk
from app.world.character_profiles.profile import CharacterProfile


PROFILE = CharacterProfile(
    choice="4",
    short_name="Joruun Veyr",
    display_name="Joruun Veyr, the Bloody Storm Monk",
    character_factory=Monk,
    ascii_art=r"""
                                     ^                                     
                        ############/|\############                        
                  #######          /_|_\          #######                  
               ####     +++++++++_/ _^_ \_+++++++++     ####               
            ####   ++++++       .-~~~~~~-.        ++++++   ####            
         ####  +++++         .-'    __    '-.          +++++  ####         
       ###  ++++           .'    .-'  '-.    '.            ++++  ###       
      ##  +++             /    .'  .--.  '.    \              +++  ##      
    ### [=]              /    /   (  @ )   \    \               [=] ###    
   ##  ++                 \    \   '--'   /    /                  ++  ##   
   #  ++                    '.   '.__/\.'   .'                     ++  #   
  #  ++             /<<<<<<<<<<\    /  \     />>>>>>>>>>\           ++  #  
 ## ++         /\  /<<<<<<<<<<<<\  /    \    />>>>>>>>>>>>/\         ++ ## 
 #  +         /  \/<<<<<<<<<<<<<<\/      \   />>>>>>>>>>>/  \         +  # 
 #  +        / /   \<<<<<<<<<<<< /        \  \ >>>>>>>>>>>>/\ \       +  # 
 #  +       / /     \<<<<<<<<<< |          |  \ >>>>>>>>>>/  \ \      +  # 
 #  +        \ \                |   .--.   |               / /        +  # 
 ## ++        \ \                \  \__/  /               / /        ++ ## 
  #  ++        \/  __/\____/\____/\____/\____/\____/\__   \/        ++  #  
   #  ++         __/  \__/  \__/  \__/  \__/  \__/  \  \__         ++  #   
   ##  ++    _/~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\_     ++  ##   
    ### +++   /__\/\__/\__/\__/\__/\__/\__/\__/\__/\__/\/__\    +++ ###    
      ##  +++        vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv        +++  ##      
       ###  ++++       || ||||| |||||| ||||| || |||        ++++  ###       
         ####  +++++        || |   |||   | ||          +++++  ####         
            ####   ++++++           ||            ++++++   ####            
               ####     ++++++++++.----.+++++++++++     ####               
                  #######          |/\/|          #######                  
                        ###########|/\#|###########                        
                                  '----'                                   
""",
    origin_title="Wandering Prophet of the Hollow Gale",
    biography="""From the storm-beaten Kharuun Shelf comes a monk of questionable holiness. Joruun Veyr wanders from 
village to village 
performing genuine miracles for donations, free drinks, and the attention of beautiful women. Beneath the flowing 
tan robes, dark spectacles, and rehearsed wisdom is a gifted Veyrathi martial artist with an equally impressive talent 
for gambling, deception, and getting thrown out of taverns. He carries Sky-Needle, an ash-wood shakujō fitted with
copper collars and loose conductive rings. Through the Law of the Single Current, Joruun can generate wind, water,
or lightning, but only one at a time. Existing rain, rivers, blood, and charged skies allow him to combine their effects 
through careful environmental control. Wind grants him speed and invisible pressure strikes. Water provides defense, 
reach, and crushing hydraulic force. Lightning delivers devastating bursts at severe physical cost.""",
    dungeon_motive="""He claims he entered the dungeon in pursuit of a sacred Veyrathi matter. His explanation changes 
depending on who asks, how much they are paying, and whether the nearest tavern is still open.""",
    combat_role="Elemental Skirmisher",
    combat_summary="""Joruun is mobile, deceptive, and highly adaptable. He switches between three distinct combat forms 
and becomes increasingly dangerous when the environment supplies additional elements.""",
    strengths="Mobility, adaptability, battlefield control, burst damage",
    weaknesses="Elemental transition windows, limited stamina, lightning recoil",
    weapon="Sky-Needle",
    discipline="Law of the Single Current",
    quote="“The heavens provide the rain, the earth provides the grain, and the brewery provides salvation. Amen.”",
    selection_summary="mobile, adaptable, physically costly",
)

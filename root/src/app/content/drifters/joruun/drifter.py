"""Monk authored Drifter content."""

from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType
from app.combat.storm import (
    HYDRO_WHIP_MECHANIC,
    LIGHTNING_PALM_MECHANIC,
    TEMPEST_SURGE_MECHANIC,
)
from app.content.drifter_spec import (
    ClassMechanicSpec,
    DrifterSpec,
    DrifterStatSpec,
)


_STATS = DrifterStatSpec(10, 10, 13, 7, 12, 8)


_COMBAT_MOVES = (
        Move(
            name='Bring the Horse to Water',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=12,
            scales_with=(ScalingAttribute.DEXTERITY,),
            accuracy=90,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic=None,
            # Deferred mechanic: staff control
            description='A grounded staff technique that redirects force through precise positioning.'),
        Move(
            name='Lightning Palm',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=7,
            power=24,
            scales_with=(
                ScalingAttribute.DEXTERITY,
                ScalingAttribute.INTELLIGENCE,
                ScalingAttribute.INTUITION,
            ),
            accuracy=70,
            target=TargetType.ENEMY,
            damage_type=DamageType.HYBRID,
            mechanic=LIGHTNING_PALM_MECHANIC,
            description='A risky palm strike that carries lightning through the point of impact.'),
        Move(
            name='Tempest Surge',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=6,
            power=20,
            scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.INTUITION),
            accuracy=82,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic=TEMPEST_SURGE_MECHANIC,
            description='A controlled burst of storm force shaped through Sky-Needle.'),
        Move(
            name='Hydro Whip',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=4,
            power=16,
            scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.INTUITION),
            accuracy=88,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic=HYDRO_WHIP_MECHANIC,
            description='A snapping water current used to lash and reposition an enemy.'),
        Move(
            name='Coagulated Torrent',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.SUPER,
            resource_cost=100,
            power=32,
            scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.INTUITION),
            accuracy=100,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic=None,
            description='A decisive torrent that compresses gathered force into a finishing surge.'),
)


DRIFTER = DrifterSpec(
    drifter_id="joruun",
    archetype_name='Monk',
    stats=_STATS,
    combat_moves=_COMBAT_MOVES,
    class_mechanic=ClassMechanicSpec(
        name='Ki Forms',
        description='Monk techniques combine positioning, balance, and Ki setup effects.',
    ),
    starting_weapon_id="sky_needle",
    starting_run_inventory=(),
    starting_prepared_payloads=(),
    choice="4",
    short_name="Joruun Veyr",
    display_name="Joruun Veyr, the Bloody Storm Monk",
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


__all__ = ["DRIFTER"]

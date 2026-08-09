"""Black Mage authored Drifter content."""

from app.combat.frost import FROST_ATTACK_MECHANIC
from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType
from app.content.drifter_spec import (
    ClassMechanicSpec,
    DrifterSpec,
    DrifterStatSpec,
)


_STATS = DrifterStatSpec(7, 13, 15, 5, 8, 12)


_COMBAT_MOVES = (
        Move(
            name='Scepter Sweep',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=7,
            scales_with=(ScalingAttribute.DEXTERITY,),
            accuracy=92,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic='basic_attack',
            is_spell=False,
            description='A direct scepter strike aimed at the target.'),
        Move(
            name='Gloamweight Sepulcher',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=8,
            power=15,
            scales_with=(ScalingAttribute.INTELLIGENCE,),
            accuracy=86,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic=None,
            is_spell=True,
            description='Dark gravity folds inward, crushing the target beneath impossible weight.'),
        Move(
            name='Mournglass Bloom',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=6,
            power=12,
            scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.SPIRIT),
            accuracy=90,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic=FROST_ATTACK_MECHANIC,
            is_spell=True,
            frost_backlash=True,
            description='Black frost erupts outward, encasing nearby enemies in splintering ice.'),
        Move(
            name='Gravemantle Rupture',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=12,
            power=17,
            scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.SPIRIT),
            accuracy=80,
            target=TargetType.ENEMY,
            damage_type=DamageType.HYBRID,
            mechanic='gravemantle_rupture',
            is_spell=True,
            # Deferred mechanic: balance and armor break
            description='The ground ruptures beneath the target, shattering balance and armor.'),
        Move(
            name='Causality Nullwake',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.SUPER,
            resource_cost=100,
            power=30,
            scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.INTUITION),
            accuracy=100,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic=None,
            is_spell=True,
            # Deferred mechanic: causality control
            description='Causality collapses around the target, erasing motion before it can occur.'),
)


DRIFTER = DrifterSpec(
    drifter_id="azhvielle",
    archetype_name='Black Mage',
    stats=_STATS,
    combat_moves=_COMBAT_MOVES,
    class_mechanic=ClassMechanicSpec(
        name='Arcane Focus',
        description='Spells spend mana and scale primarily from intelligence.',
    ),
    starting_weapon_id="needle_of_plain_iron",
    starting_run_inventory=(),
    starting_prepared_payloads=(),
    choice="2",
    short_name="Azhvielle",
    display_name="Azhvielle, the Unconfessed",
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
    weapon="Needle of Plain Iron",
    discipline="Vharosynian Causal Sorcery",
    quote="“Yes, I can solve this with magic. That does not make it sensible.”",
    selection_summary="versatile, dangerous, unpredictable",
)


__all__ = ["DRIFTER"]

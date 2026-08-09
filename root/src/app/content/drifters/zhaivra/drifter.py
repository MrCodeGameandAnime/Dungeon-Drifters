"""Rogue Archer authored Drifter content."""

from app.combat.infused_barb import INFUSED_BARB_MECHANIC
from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType
from app.content.drifter_spec import (
    ClassMechanicSpec,
    DrifterSpec,
    DrifterStatSpec,
)


_STATS = DrifterStatSpec(8, 7, 10, 6, 15, 14)


_COMBAT_MOVES = (
        Move(
            name='Mournpoint Verdict',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=10,
            scales_with=(ScalingAttribute.DEXTERITY,),
            accuracy=96,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic='basic_attack',
            # Deferred mechanic: weak-point critical bonus
            description='Zhaivra drives a single arrow through the target’s weakest point.'),
        Move(
            name='Hollowstring Trine',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=4,
            power=16,
            scales_with=(ScalingAttribute.DEXTERITY,),
            accuracy=86,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic=None,
            # Deferred mechanic: three-hit sequence
            description='Three arrows split from one release, striking in a merciless sequence.'),
        Move(
            name='Nightskein Deluge',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=6,
            power=15,
            scales_with=(ScalingAttribute.DEXTERITY, ScalingAttribute.INTUITION),
            accuracy=82,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic=None,
            # Deferred mechanic: multi-target shadow volley
            description='A woven storm of shadow-arrows descends across the battlefield.'),
        Move(
            name='Infused Barb',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=5,
            power=14,
            scales_with=(ScalingAttribute.INTUITION, ScalingAttribute.INTELLIGENCE),
            accuracy=88,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic=INFUSED_BARB_MECHANIC,
            description='A prepared alchemical arrow carries fire or poison into the target.'),
        Move(
            name='Starless Meridian Obsequy',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.SUPER,
            resource_cost=100,
            power=28,
            scales_with=(ScalingAttribute.DEXTERITY, ScalingAttribute.INTUITION),
            accuracy=100,
            target=TargetType.ENEMY,
            damage_type=DamageType.HYBRID,
            mechanic=None,
            # Deferred mechanic: piercing multiple targets
            description='Zhaivra looses an impossible shot that tears a silent path through everything before it.'),
)


DRIFTER = DrifterSpec(
    drifter_id="zhaivra",
    archetype_name='Rogue Archer',
    stats=_STATS,
    combat_moves=_COMBAT_MOVES,
    class_mechanic=ClassMechanicSpec(
        name='Precision',
        description='High dexterity supports accuracy, critical hits, and multi-hit attacks.',
    ),
    starting_weapon_id="sathren",
    starting_run_inventory=(
        ('ember_shard', 1),
        ('deep_coal', 1),
        ('night_berry', 1),
    ),
    starting_prepared_payloads=(
        ('infused_barb', None),
    ),
    choice="3",
    short_name="Zhaivra Kelyth",
    display_name="Zhaivra Kelyth, the Uncontrolled Reagent",
    ascii_art=r"""
+-------------------------------------------------------------------------+
|                                    /\                                   |
|                   __              /  \             __                   |
|                __/  \____________/ /\ \___________/  \__                |
|            __/       \          / /  \ \         /      \__             |
|         _/    _/\_     \_______/ /____\ \_______/ _/\_     \_           |
|       /_____/ /  \________________________________/  \ \_____\          |
|                .---------------------------------------.                |
|              /                    /\                     \              |
|   __/\__    /                    /  \                      \   __/\__   |
| _/      \_ |                    / /\ \                     | _/      \_ |
| \_  /\  _/ |                   / /  \ \                    | \_  /\  _/ |
|   \/  \/   |                  /_/ /\ \_\                   |   \/  \/   |
|     ||     |                     /  \                      |     ||     |
|     ||     |     <\             / /\ \              />     |     ||     |
|   .[==].   |    <<\            / /  \ \            />>     |   .[==].   |
|   |:++:|   |   <<<\           <  /||\  >          />>>     |   |:++:|   |
|   |:++:|   |   << /            \/ || \/            \ >>    |   |:++:|   |
|    \__/    |     </               ||                 \>    |    \__/    |
|            |                      ||                       |            |
|            |                     /||\                      |            |
|            |                    /_||_\                     |            |
|             \                     ||                      /             |
|              \                    ||                     /              |
|                '------------------|+-------------------'                |
|                 \__________________|__________________/                 |
|                .---------------------------------------.                |
|               / THE FLAME THAT REFUSES ITS VESSEL      \                |
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


__all__ = ["DRIFTER"]

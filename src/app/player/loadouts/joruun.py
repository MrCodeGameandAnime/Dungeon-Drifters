from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType
from app.combat.storm import (
    HYDRO_WHIP_MECHANIC,
    LIGHTNING_PALM_MECHANIC,
    TEMPEST_SURGE_MECHANIC,
)
from app.items.weapon import SkyNeedle


def create_starting_stats():
    return {
        "constitution": 10,
        "spirit": 10,
        "intelligence": 13,
        "strength": 7,
        "dexterity": 12,
        "intuition": 8,
    }


def create_legacy_moves():
    return {
        1: 'Bring the Horse to Water',
        2: 'Lightning Palm',
        3: 'Tempest Surge',
        4: 'Hydro Whip',
        5: 'Coagulated Torrent',
    }


def create_combat_moves():
    return [
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
    ]


def create_class_mechanic():
    return {
        'name': 'Ki Forms',
        'description': 'Monk techniques combine positioning, balance, and Ki setup effects.',
    }


def create_starting_weapon():
    return SkyNeedle()

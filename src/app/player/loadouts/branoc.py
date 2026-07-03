from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType
from app.items.weapon import SunderSpire


def create_legacy_moves():
    return {1: 'slash', 2: 'jumping slash', 3: 'suplex'}


def create_combat_moves():
    return [
        Move(
            name='slash',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=9,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=92,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic='basic_attack',
            description='A reliable close-range strike.'),
        Move(
            name='jumping slash',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=3,
            power=14,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=82,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic='heavy_attack',
            description='A risky leaping attack that hits harder than a basic strike.'),
        Move(
            name='suplex',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=5,
            power=18,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=75,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic=None,
            # Deferred mechanic: stagger
            description='A brutal throw that can stagger a weakened foe.'),
    ]


def create_class_mechanic():
    return {
        'name': 'Heavy Vanguard',
        'description': 'A durable frontline identity built around heavy physical pressure.',
    }


def create_starting_weapon():
    return SunderSpire()

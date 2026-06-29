from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType


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
            mechanic='combo_builder',
            description='A reliable close-range strike that builds momentum.'),
        Move(
            name='jumping slash',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.CHARACTER,
            resource_cost=3,
            power=14,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=82,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic='combo_spender',
            description='A risky leaping attack that hits harder after momentum is built.'),
        Move(
            name='suplex',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.CHARACTER,
            resource_cost=5,
            power=18,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=75,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic='stagger',
            description='A brutal throw that can stagger a weakened foe.'),
    ]


def create_class_mechanic():
    return {
        'name': 'Momentum',
        'resource': 'momentum',
        'description': 'Basic hits build momentum; heavy techniques spend it for burst damage.',
    }

from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType


def create_legacy_moves():
    return {1: 'fireball', 2: 'heal', 3: 'thunderbolt'}


def create_combat_moves():
    return [
        Move(
            name='fireball',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=8,
            power=14,
            scales_with=(ScalingAttribute.INTELLIGENCE,),
            accuracy=88,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic='burn',
            description='A direct fire spell with a chance to leave burning damage later.'),
        Move(
            name='heal',
            kind=MoveKind.HEALING,
            resource_type=ResourceType.MANA,
            resource_cost=10,
            power=12,
            scales_with=(ScalingAttribute.INTELLIGENCE,),
            accuracy=100,
            target=TargetType.SELF,
            damage_type=DamageType.HEALING,
            mechanic='arcane_recovery',
            description='Restores health instead of damaging the enemy.'),
        Move(
            name='thunderbolt',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=14,
            power=20,
            scales_with=(ScalingAttribute.INTELLIGENCE,),
            accuracy=78,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic='shock',
            description='A volatile lightning spell with high damage and lower accuracy.'),
    ]


def create_class_mechanic():
    return {
        'name': 'Arcane Focus',
        'resource': 'mana',
        'description': 'Spells spend mana and scale primarily from intelligence.',
    }  # ice shield

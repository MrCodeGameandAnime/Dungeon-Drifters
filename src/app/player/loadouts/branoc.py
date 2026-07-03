from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType
from app.items.weapon import SunderSpire


def create_legacy_moves():
    return {
        1: 'Crestgrave Reaping',
        2: 'Cinderlung Vesper',
        3: 'Ghalmour Compression',
        4: 'Ironwake Dismemberment',
        5: 'Third Gate Obsequy',
    }


def create_combat_moves():
    return [
        Move(
            name='Crestgrave Reaping',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=9,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=92,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic='basic_attack',
            # Deferred mechanic: guard and armor cleave
            description='Sunder-Spire tears through the target, cleaving guard and armor.'),
        Move(
            name='Cinderlung Vesper',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=3,
            power=8,
            scales_with=(ScalingAttribute.SPIRIT,),
            accuracy=88,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic=None,
            # Deferred mechanic: line or multi-target war-breath
            description='A black war-breath erupts forward, searing everything in its path.'),
        Move(
            name='Ghalmour Compression',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=5,
            power=12,
            scales_with=(ScalingAttribute.SPIRIT, ScalingAttribute.INTUITION),
            accuracy=78,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic=None,
            # Deferred mechanic: pressure compression
            description='Invisible pressure closes around the target, crushing flesh against bone.'),
        Move(
            name='Ironwake Dismemberment',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=3,
            power=14,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=82,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic='heavy_attack',
            # Deferred mechanic: battlefield-splitting impact
            description='Branoc drives Sunder-Spire downward with battlefield-splitting force.'),
        Move(
            name='Third Gate Obsequy',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.SUPER,
            resource_cost=100,
            power=24,
            scales_with=(ScalingAttribute.STRENGTH, ScalingAttribute.SPIRIT),
            accuracy=100,
            target=TargetType.ENEMY,
            damage_type=DamageType.HYBRID,
            mechanic=None,
            # Deferred mechanic: Third Gate manifestation
            description='A forbidden gate manifests behind Branoc, pouring ruin through Sunder-Spire.'),
    ]


def create_class_mechanic():
    return {
        'name': 'Heavy Vanguard',
        'description': 'A durable frontline identity built around heavy physical pressure.',
    }


def create_starting_weapon():
    return SunderSpire()

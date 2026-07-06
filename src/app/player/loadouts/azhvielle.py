from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType
from app.items.weapon import NeedleOfPlainIron


def create_starting_stats():
    return {
        "constitution": 7,
        "spirit": 13,
        "intelligence": 15,
        "strength": 5,
        "dexterity": 8,
        "intuition": 12,
    }


def create_legacy_moves():
    return {
        1: 'Scepter Sweep',
        2: 'Gloamweight Sepulcher',
        3: 'Mournglass Bloom',
        4: 'Gravemantle Rupture',
        5: 'Causality Nullwake',
    }


def create_combat_moves():
    return [
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
            mechanic=None,
            # Deferred mechanic: multi-target frost encasement
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
            mechanic=None,
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
            # Deferred mechanic: causality control
            description='Causality collapses around the target, erasing motion before it can occur.'),
    ]


def create_class_mechanic():
    return {
        'name': 'Arcane Focus',
        'description': 'Spells spend mana and scale primarily from intelligence.',
    }  # ice shield


def create_starting_weapon():
    return NeedleOfPlainIron()

from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType
from app.items.weapon import Sathren


def create_starting_stats():
    return {
        "constitution": 8,
        "spirit": 7,
        "intelligence": 10,
        "strength": 6,
        "dexterity": 15,
        "intuition": 14,
    }


def create_starting_run_inventory():
    return {
        "ember_shard": 1,
        "deep_coal": 1,
    }


def create_starting_prepared_payloads():
    return {
        "cinderwrit_payload": False,
    }


def create_legacy_moves():
    return {
        1: 'Mournpoint Verdict',
        2: 'Hollowstring Trine',
        3: 'Nightskein Deluge',
        4: 'Cinderwrit Barb',
        5: 'Starless Meridian Obsequy',
    }


def create_combat_moves():
    return [
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
            name='Cinderwrit Barb',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=5,
            power=14,
            scales_with=(ScalingAttribute.INTUITION, ScalingAttribute.INTELLIGENCE),
            accuracy=88,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic=None,
            # Deferred mechanic: dark-fire burn
            description='A rune-burned arrow embeds in the target, igniting dark fire within.'),
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
    ]


def create_class_mechanic():
    return {
        'name': 'Precision',
        'description': 'High dexterity supports accuracy, critical hits, and multi-hit attacks.',
    }


def create_starting_weapon():
    return Sathren()

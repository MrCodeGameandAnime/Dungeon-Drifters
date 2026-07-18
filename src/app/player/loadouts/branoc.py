from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType
from app.combat.move_presentation import MovePresentation, MoveRole
from app.items.weapon import SunderSpire


def create_starting_stats():
    return {
        "constitution": 14,
        "spirit": 6,
        "intelligence": 5,
        "strength": 15,
        "dexterity": 10,
        "intuition": 10,
    }


def create_legacy_moves():
    return {
        1: 'Crestgrave Reaping',
        2: 'Cinderlung Vesper',
        3: 'Brace',
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
            description='Sunder-Spire tears through the target, cleaving guard and armor.',
            presentation=MovePresentation(role=MoveRole.NORMAL)),
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
            description='A black war-breath erupts forward, searing everything in its path.',
            presentation=MovePresentation(
                role=MoveRole.NORMAL,
                affinity_label='Fire',
            )),
        Move(
            name='Brace',
            kind=MoveKind.UTILITY,
            resource_type=ResourceType.MANA,
            resource_cost=5,
            power=0,
            scales_with=(ScalingAttribute.NONE,),
            accuracy=100,
            target=TargetType.SELF,
            damage_type=DamageType.NONE,
            mechanic='brace',
            description='Branoc plants Sunder-Spire and braces behind the Deep-Iron crest.',
            presentation=MovePresentation(role=MoveRole.UTILITY)),
        Move(
            name='Ironwake Dismemberment',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=14,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=82,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic='heavy_attack',
            # Deferred mechanic: battlefield-splitting impact
            description='Branoc drives Sunder-Spire downward with battlefield-splitting force.',
            presentation=MovePresentation(
                role=MoveRole.HEAVY,
                static_summary='A crushing Sunder-Spire strike.',
            )),
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
            description='A forbidden gate manifests behind Branoc, pouring ruin through Sunder-Spire.',
            presentation=MovePresentation(role=MoveRole.SUPER)),
    ]


def create_class_mechanic():
    return {
        'name': 'Heavy Vanguard',
        'description': 'A durable frontline identity built around heavy physical pressure.',
    }


def create_starting_weapon():
    return SunderSpire()

from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType


def create_legacy_moves():
    return {1: 'deadshot', 2: 'triple shot', 3: 'rain of arrows', 4: 'flaming arrow'}


def create_combat_moves():
    return [
        Move(
            name='deadshot',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=12,
            scales_with=(ScalingAttribute.DEXTERITY,),
            accuracy=95,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic='crit_bonus',
            description='A precise shot with increased critical potential.'),
        Move(
            name='triple shot',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=6,
            scales_with=(ScalingAttribute.DEXTERITY,),
            accuracy=86,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic='multi_hit',
            description='Fires three lighter shots that can each contribute damage.'),
        Move(
            name='rain of arrows',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=10,
            scales_with=(ScalingAttribute.DEXTERITY,),
            accuracy=80,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic='volley',
            description='A broad volley designed for future multi-enemy encounters.'),
        Move(
            name='flaming arrow',
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=13,
            scales_with=(ScalingAttribute.DEXTERITY, ScalingAttribute.INTUITION),
            accuracy=84,
            target=TargetType.ENEMY,
            damage_type=DamageType.HYBRID,
            mechanic='burn',
            description='A dexterous shot with a fire effect hook for later status damage.'),
    ]


def create_class_mechanic():
    return {
        'name': 'Precision',
        'description': 'High dexterity supports accuracy, critical hits, and multi-hit attacks.',
    }

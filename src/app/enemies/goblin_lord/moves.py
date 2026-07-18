from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType


def create_goblin_lord_moves():
    return (
        Move(
            name="King’s Cleaver", kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE, resource_cost=0, power=18,
            scales_with=(ScalingAttribute.STRENGTH,), accuracy=92,
            target=TargetType.ENEMY, damage_type=DamageType.PHYSICAL,
            mechanic="basic_attack",
            description="The Goblin Lord swings its enormous cleaver with practiced authority.",
        ),
        Move(
            name="Iron Decree", kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE, resource_cost=0, power=25,
            scales_with=(ScalingAttribute.STRENGTH, ScalingAttribute.INTUITION),
            accuracy=80, target=TargetType.ENEMY, damage_type=DamageType.PHYSICAL,
            mechanic="heavy_attack",
            description="The Lord commits its full weight to a crushing blow meant to end resistance immediately.",
        ),
        Move(
            name="Black Banner Flame", kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA, resource_cost=8, power=17,
            scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.SPIRIT),
            accuracy=88, target=TargetType.ENEMY, damage_type=DamageType.MAGICAL,
            mechanic="basic_attack",
            description="Dark fire gathers around the Lord’s battle standard before surging toward the target.",
        ),
        Move(
            name="Tyrant’s Ruin", kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA, resource_cost=14, power=26,
            scales_with=(ScalingAttribute.STRENGTH, ScalingAttribute.INTELLIGENCE),
            accuracy=75, target=TargetType.ENEMY, damage_type=DamageType.HYBRID,
            mechanic="heavy_attack",
            description="The Goblin Lord combines raw physical force with unstable sorcery in one devastating assault.",
        ),
    )

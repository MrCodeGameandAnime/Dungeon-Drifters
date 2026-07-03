from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType


def create_goblin_moves():
    return (
        Move(
            name="slash",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=8,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=90,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="basic_attack",
            description="A simple close-range strike.",
        ),
        Move(
            name="jumping slash",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=12,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=80,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="heavy_attack",
            description="A committed leaping slash.",
        ),
    )

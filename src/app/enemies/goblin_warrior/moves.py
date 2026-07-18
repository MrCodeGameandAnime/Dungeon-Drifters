from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType


def create_goblin_warrior_moves():
    return (
        Move(
            name="Cleaver Strike", kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE, resource_cost=0, power=10,
            scales_with=(ScalingAttribute.STRENGTH,), accuracy=92,
            target=TargetType.ENEMY, damage_type=DamageType.PHYSICAL,
            mechanic="basic_attack",
            description="A disciplined cleaver strike delivered with greater force than an ordinary Goblin slash.",
        ),
        Move(
            name="Shieldbreaker Chop", kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE, resource_cost=0, power=15,
            scales_with=(ScalingAttribute.STRENGTH,), accuracy=78,
            target=TargetType.ENEMY, damage_type=DamageType.PHYSICAL,
            mechanic="heavy_attack",
            description="A committed overhead chop intended to break through a defended position.",
        ),
    )

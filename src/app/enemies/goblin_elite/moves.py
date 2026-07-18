from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType


def create_goblin_elite_moves():
    return (
        Move(
            name="Veteran Slash", kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE, resource_cost=0, power=13,
            scales_with=(ScalingAttribute.STRENGTH, ScalingAttribute.DEXTERITY),
            accuracy=92, target=TargetType.ENEMY, damage_type=DamageType.PHYSICAL,
            mechanic="basic_attack",
            description="A practiced slash delivered with the speed and control of an experienced killer.",
        ),
        Move(
            name="Butcher’s Advance", kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE, resource_cost=0, power=18,
            scales_with=(ScalingAttribute.STRENGTH,), accuracy=84,
            target=TargetType.ENEMY, damage_type=DamageType.PHYSICAL,
            mechanic="heavy_attack",
            description="The Elite surges forward and drives its weapon through the target’s guard.",
        ),
        Move(
            name="Executioner’s Drop", kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE, resource_cost=0, power=24,
            scales_with=(ScalingAttribute.STRENGTH,), accuracy=72,
            target=TargetType.ENEMY, damage_type=DamageType.PHYSICAL,
            mechanic="heavy_attack",
            description="A brutal descending strike that sacrifices accuracy for overwhelming force.",
        ),
    )

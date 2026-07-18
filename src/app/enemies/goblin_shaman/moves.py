from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType


def create_goblin_shaman_moves():
    return (
        Move(
            name="Crooked Staff", kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE, resource_cost=0, power=7,
            scales_with=(ScalingAttribute.DEXTERITY,), accuracy=90,
            target=TargetType.ENEMY, damage_type=DamageType.PHYSICAL,
            mechanic="basic_attack",
            description="A quick strike from the Shaman's crooked ritual staff.",
        ),
        Move(
            name="Cinder Hex", kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA, resource_cost=5, power=11,
            scales_with=(ScalingAttribute.INTELLIGENCE,), accuracy=90,
            target=TargetType.ENEMY, damage_type=DamageType.MAGICAL,
            mechanic="basic_attack",
            description="A concentrated ember of Goblin sorcery hurled at the target.",
        ),
        Move(
            name="Blight Spark", kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA, resource_cost=10, power=16,
            scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.SPIRIT),
            accuracy=80, target=TargetType.ENEMY, damage_type=DamageType.MAGICAL,
            mechanic="heavy_attack",
            description="The Shaman compresses unstable ritual energy into a violent magical discharge.",
        ),
    )

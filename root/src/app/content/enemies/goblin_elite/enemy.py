from app.combat.move import (
    DamageType,
    Move,
    MoveKind,
    ResourceType,
    ScalingAttribute,
    TargetType,
)
from app.content.enemy_spec import EnemySpec, StatBlockSpec
from app.enemies.definition import EnemyBehavior, EnemyCapability, EnemyRank, EnemyRole


ENEMY = EnemySpec(
    archetype_id="goblin_elite",
    name="Goblin Elite",
    stats=StatBlockSpec(
        constitution=7,
        spirit=3,
        intelligence=2,
        strength=8,
        dexterity=5,
        intuition=4,
    ),
    hp=130,
    mana=0,
    exp_reward=150,
    gold_reward=9,
    rank=EnemyRank.ELITE,
    role=EnemyRole.BRUTE,
    behavior=EnemyBehavior.AGGRESSIVE,
    capabilities=frozenset({EnemyCapability.BASIC_ATTACKS}),
    moves=(
        Move(
            name="Veteran Slash",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=13,
            scales_with=(ScalingAttribute.STRENGTH, ScalingAttribute.DEXTERITY),
            accuracy=92,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="basic_attack",
            description="A practiced slash delivered with the speed and control of an experienced killer.",
        ),
        Move(
            name="Butcher\u2019s Advance",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=18,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=84,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="heavy_attack",
            description="The Elite surges forward and drives its weapon through the target\u2019s guard.",
        ),
        Move(
            name="Executioner\u2019s Drop",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=24,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=72,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="heavy_attack",
            description="A brutal descending strike that sacrifices accuracy for overwhelming force.",
        ),
    ),
)


__all__ = ["ENEMY"]

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
    archetype_id="goblin_lord",
    name="Goblin Lord",
    stats=StatBlockSpec(
        constitution=10,
        spirit=7,
        intelligence=7,
        strength=11,
        dexterity=6,
        intuition=9,
    ),
    hp=220,
    mana=30,
    exp_reward=200,
    gold_reward=10,
    rank=EnemyRank.BOSS,
    role=EnemyRole.BOSS,
    behavior=EnemyBehavior.AGGRESSIVE,
    capabilities=frozenset(
        {EnemyCapability.BASIC_ATTACKS, EnemyCapability.MAGIC}
    ),
    moves=(
        Move(
            name="King\u2019s Cleaver",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=18,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=92,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="basic_attack",
            description="The Goblin Lord swings its enormous cleaver with practiced authority.",
        ),
        Move(
            name="Iron Decree",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=25,
            scales_with=(ScalingAttribute.STRENGTH, ScalingAttribute.INTUITION),
            accuracy=80,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="heavy_attack",
            description="The Lord commits its full weight to a crushing blow meant to end resistance immediately.",
        ),
        Move(
            name="Black Banner Flame",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=8,
            power=17,
            scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.SPIRIT),
            accuracy=88,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic="basic_attack",
            description="Dark fire gathers around the Lord\u2019s battle standard before surging toward the target.",
        ),
        Move(
            name="Tyrant\u2019s Ruin",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=14,
            power=26,
            scales_with=(ScalingAttribute.STRENGTH, ScalingAttribute.INTELLIGENCE),
            accuracy=75,
            target=TargetType.ENEMY,
            damage_type=DamageType.HYBRID,
            mechanic="heavy_attack",
            description="The Goblin Lord combines raw physical force with unstable sorcery in one devastating assault.",
        ),
    ),
)


__all__ = ["ENEMY"]

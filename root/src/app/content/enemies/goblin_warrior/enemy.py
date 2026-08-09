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
    archetype_id="goblin_warrior",
    name="Goblin Warrior",
    stats=StatBlockSpec(
        constitution=4,
        spirit=1,
        intelligence=1,
        strength=5,
        dexterity=2,
        intuition=2,
    ),
    hp=85,
    mana=0,
    exp_reward=60,
    gold_reward=5,
    rank=EnemyRank.COMMON,
    role=EnemyRole.BRUTE,
    behavior=EnemyBehavior.AGGRESSIVE,
    capabilities=frozenset({EnemyCapability.BASIC_ATTACKS}),
    moves=(
        Move(
            name="Cleaver Strike",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=10,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=92,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="basic_attack",
            description="A disciplined cleaver strike delivered with greater force than an ordinary Goblin slash.",
        ),
        Move(
            name="Shieldbreaker Chop",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=15,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=78,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="heavy_attack",
            description="A committed overhead chop intended to break through a defended position.",
        ),
    ),
)


__all__ = ["ENEMY"]

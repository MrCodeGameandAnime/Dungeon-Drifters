from app.combat.move import (
    DamageType,
    Move,
    MoveKind,
    ResourceType,
    ScalingAttribute,
    TargetType,
)
from app.content.enemy_spec import EnemySpec, EnemyTierSpec, ItemDropSpec, StatBlockSpec
from app.enemies.definition import EnemyBehavior, EnemyCapability, EnemyRank, EnemyRole


ENEMY = EnemySpec(
    archetype_id="goblin",
    name="Goblin",
    stats=StatBlockSpec(
        constitution=2,
        spirit=1,
        intelligence=1,
        strength=3,
        dexterity=1,
        intuition=1,
    ),
    hp=60,
    mana=0,
    exp_reward=40,
    gold_reward=3,
    rank=EnemyRank.COMMON,
    role=EnemyRole.MELEE_SKIRMISHER,
    behavior=EnemyBehavior.AGGRESSIVE,
    capabilities=frozenset({EnemyCapability.BASIC_ATTACKS}),
    supported_tiers=(0, 1),
    tier_profiles=(
        EnemyTierSpec(
            tier=1,
            stats=StatBlockSpec(
                constitution=3,
                spirit=1,
                intelligence=1,
                strength=4,
                dexterity=2,
                intuition=1,
            ),
            hp=75,
            mana=0,
            item_drops=(ItemDropSpec("grade_ii_metal", 1, 2000),),
        ),
    ),
    moves=(
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
    ),
    item_drops=(("goblin_scrap", 1),),
)


__all__ = ["ENEMY"]

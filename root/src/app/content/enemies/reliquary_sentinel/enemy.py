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
    archetype_id="reliquary_sentinel",
    name="Reliquary Sentinel",
    stats=StatBlockSpec(
        constitution=10,
        spirit=4,
        intelligence=3,
        strength=12,
        dexterity=6,
        intuition=4,
    ),
    hp=160,
    mana=0,
    exp_reward=130,
    gold_reward=12,
    rank=EnemyRank.ELITE,
    role=EnemyRole.BRUTE,
    behavior=EnemyBehavior.AGGRESSIVE,
    capabilities=frozenset({EnemyCapability.BASIC_ATTACKS, EnemyCapability.DEFEND}),
    moves=(
        Move(
            name="Tidal Mace",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=12,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=90,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="basic_attack",
            description="The Sentinel drives a heavy mace through the guard.",
        ),
        Move(
            name="Stoneward Slam",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=15,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=78,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="heavy_attack",
            description="The Sentinel commits its weight to a crushing blow.",
        ),
    ),
    supported_tiers=(0, 3),
    tier_profiles=(
        EnemyTierSpec(
            tier=3,
            stats=StatBlockSpec(
                constitution=16,
                spirit=6,
                intelligence=5,
                strength=15,
                dexterity=9,
                intuition=6,
            ),
            hp=115,
            mana=0,
            item_drops=(
                ItemDropSpec(
                    "grade_iv_metal",
                    1,
                    3000,
                    source_id="m8_floor_four_metal_drop_01",
                ),
            ),
        ),
    ),
    item_drops=(("grade_i_metal", 1),),
)


__all__ = ["ENEMY"]

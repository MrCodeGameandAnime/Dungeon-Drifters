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
    archetype_id="ashbound_hound",
    name="Ashbound Hound",
    stats=StatBlockSpec(
        constitution=8,
        spirit=4,
        intelligence=3,
        strength=10,
        dexterity=10,
        intuition=6,
    ),
    hp=140,
    mana=0,
    exp_reward=150,
    gold_reward=13,
    rank=EnemyRank.ELITE,
    role=EnemyRole.BRUTE,
    behavior=EnemyBehavior.AGGRESSIVE,
    capabilities=frozenset({EnemyCapability.BASIC_ATTACKS}),
    moves=(
        Move(
            name="Cinder Bite",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=11,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=90,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="basic_attack",
            description="The Hound lunges forward with a heavy bite.",
        ),
        Move(
            name="Ashfall Pounce",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=16,
            scales_with=(ScalingAttribute.STRENGTH, ScalingAttribute.DEXTERITY),
            accuracy=78,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="heavy_attack",
            description="The Hound crashes down in a forceful pounce.",
        ),
    ),
    supported_tiers=(0, 3),
    tier_profiles=(
        EnemyTierSpec(
            tier=3,
            stats=StatBlockSpec(
                constitution=12,
                spirit=5,
                intelligence=4,
                strength=14,
                dexterity=12,
                intuition=8,
            ),
            hp=100,
            mana=0,
            item_drops=(
                ItemDropSpec(
                    "grade_iv_timber",
                    1,
                    3000,
                    source_id="m8_floor_four_timber_drop_01",
                ),
            ),
        ),
    ),
    item_drops=(("grade_i_timber", 1),),
)


__all__ = ["ENEMY"]

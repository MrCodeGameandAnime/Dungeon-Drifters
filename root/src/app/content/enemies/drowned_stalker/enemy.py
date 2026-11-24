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
    archetype_id="drowned_stalker",
    name="Drowned Stalker",
    stats=StatBlockSpec(
        constitution=7,
        spirit=4,
        intelligence=3,
        strength=8,
        dexterity=13,
        intuition=10,
    ),
    hp=130,
    mana=0,
    exp_reward=140,
    gold_reward=13,
    rank=EnemyRank.ELITE,
    role=EnemyRole.MELEE_SKIRMISHER,
    behavior=EnemyBehavior.AGGRESSIVE,
    capabilities=frozenset({EnemyCapability.BASIC_ATTACKS}),
    moves=(
        Move(
            name="Undercut",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=10,
            scales_with=(ScalingAttribute.DEXTERITY,),
            accuracy=94,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="basic_attack",
            description="The Stalker darts in with a low, precise strike.",
        ),
        Move(
            name="Riptide Crossing",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=14,
            scales_with=(ScalingAttribute.DEXTERITY, ScalingAttribute.STRENGTH),
            accuracy=82,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="heavy_attack",
            description="The Stalker crosses the field in a committed slash.",
        ),
    ),
    supported_tiers=(0, 3),
    tier_profiles=(
        EnemyTierSpec(
            tier=3,
            stats=StatBlockSpec(
                constitution=10,
                spirit=5,
                intelligence=4,
                strength=10,
                dexterity=15,
                intuition=15,
            ),
            hp=90,
            mana=0,
            item_drops=(
                ItemDropSpec(
                    "grade_iv_fiber",
                    1,
                    3000,
                    source_id="m8_floor_four_fiber_drop_01",
                ),
            ),
        ),
    ),
    item_drops=(("grade_i_fiber", 1),),
)


__all__ = ["ENEMY"]

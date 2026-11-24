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
    archetype_id="tidebound_curator",
    name="Tidebound Curator",
    stats=StatBlockSpec(
        constitution=14,
        spirit=14,
        intelligence=14,
        strength=10,
        dexterity=8,
        intuition=12,
    ),
    hp=360,
    mana=100,
    exp_reward=320,
    gold_reward=24,
    rank=EnemyRank.BOSS,
    role=EnemyRole.BOSS,
    behavior=EnemyBehavior.AGGRESSIVE,
    capabilities=frozenset({EnemyCapability.BASIC_ATTACKS, EnemyCapability.MAGIC}),
    moves=(
        Move(
            name="Archive Cleave",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=17,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=88,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="basic_attack",
            description="The Curator sweeps a relic blade across its target.",
        ),
        Move(
            name="Undertow Index",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=10,
            power=18,
            scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.SPIRIT),
            accuracy=86,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic="basic_attack",
            description="A measured surge of brine sorcery crashes over one target.",
        ),
        Move(
            name="Final Catalogue",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=16,
            power=23,
            scales_with=(ScalingAttribute.INTELLIGENCE,),
            accuracy=76,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic="heavy_attack",
            description="The Curator unleashes a forceful spell from its sealed archive.",
        ),
    ),
    supported_tiers=(0, 3),
    tier_profiles=(
        EnemyTierSpec(
            tier=3,
            stats=StatBlockSpec(
                constitution=21,
                spirit=17,
                intelligence=18,
                strength=14,
                dexterity=12,
                intuition=16,
            ),
            hp=300,
            mana=140,
            item_drops=(
                ItemDropSpec(
                    "grade_iv_cores",
                    1,
                    10000,
                    source_id="m8_floor_four_core_drop_01",
                ),
            ),
        ),
    ),
    item_drops=(("goblin_lord_core", 1),),
)


__all__ = ["ENEMY"]

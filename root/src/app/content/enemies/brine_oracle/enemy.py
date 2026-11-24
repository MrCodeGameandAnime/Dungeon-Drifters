from app.combat.move import (
    DamageType,
    Move,
    MoveKind,
    ResourceType,
    ScalingAttribute,
    TargetType,
)
from app.content.enemy_spec import EnemySpec, EnemyTierSpec, StatBlockSpec
from app.enemies.definition import EnemyBehavior, EnemyCapability, EnemyRank, EnemyRole


ENEMY = EnemySpec(
    archetype_id="brine_oracle",
    name="Brine Oracle",
    stats=StatBlockSpec(
        constitution=5,
        spirit=10,
        intelligence=12,
        strength=3,
        dexterity=7,
        intuition=8,
    ),
    hp=120,
    mana=36,
    exp_reward=160,
    gold_reward=14,
    rank=EnemyRank.SPECIALIST,
    role=EnemyRole.CASTER,
    behavior=EnemyBehavior.AGGRESSIVE,
    capabilities=frozenset({EnemyCapability.BASIC_ATTACKS, EnemyCapability.MAGIC}),
    moves=(
        Move(
            name="Reedpoint",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=9,
            scales_with=(ScalingAttribute.DEXTERITY,),
            accuracy=92,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="basic_attack",
            description="The Oracle lashes with a sharpened reed staff.",
        ),
        Move(
            name="Saltglass Lance",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=8,
            power=10,
            scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.SPIRIT),
            accuracy=88,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic="basic_attack",
            description="A narrow lance of condensed brine strikes one target.",
        ),
        Move(
            name="Drowned Script",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=13,
            power=13,
            scales_with=(ScalingAttribute.INTELLIGENCE,),
            accuracy=78,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic="heavy_attack",
            description="The Oracle releases a forceful wave of written sorcery.",
        ),
    ),
    supported_tiers=(0, 3),
    tier_profiles=(
        EnemyTierSpec(
            tier=3,
            stats=StatBlockSpec(
                constitution=8,
                spirit=13,
                intelligence=14,
                strength=4,
                dexterity=10,
                intuition=12,
            ),
            hp=80,
            mana=50,
        ),
    ),
)


__all__ = ["ENEMY"]

from app.combat.move import (
    DamageType,
    Move,
    MoveKind,
    ResourceType,
    ScalingAttribute,
    TargetType,
)
from app.content.enemy_spec import (
    EnemySpec,
    EnemyTierSpec,
    ItemDropSpec,
    StatBlockSpec,
)
from app.enemies.definition import EnemyBehavior, EnemyCapability, EnemyRank, EnemyRole


ENEMY = EnemySpec(
    archetype_id="ashen_regent",
    name="Ashen Regent",
    stats=StatBlockSpec(
        constitution=14,
        spirit=14,
        intelligence=15,
        strength=12,
        dexterity=11,
        intuition=12,
    ),
    hp=320,
    mana=110,
    exp_reward=720,
    gold_reward=45,
    rank=EnemyRank.BOSS,
    role=EnemyRole.BOSS,
    behavior=EnemyBehavior.AGGRESSIVE,
    capabilities=frozenset({EnemyCapability.BASIC_ATTACKS, EnemyCapability.MAGIC}),
    moves=(
        Move(
            name="Cindersteel Sweep",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=18,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=88,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="basic_attack",
            description="The Regent's blackened blade sweeps through one target.",
        ),
        Move(
            name="Ashfall Verdict",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=14,
            power=21,
            scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.SPIRIT),
            accuracy=84,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic="basic_attack",
            description="A concentrated fall of ember-dark sorcery strikes one target.",
        ),
        Move(
            name="Regent's Last Decree",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=22,
            power=27,
            scales_with=(ScalingAttribute.INTELLIGENCE,),
            accuracy=76,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic="heavy_attack",
            description="The Regent releases a forceful, single-target burst of ashfire.",
        ),
    ),
    supported_tiers=(0, 3),
    tier_profiles=(
        EnemyTierSpec(
            tier=3,
            stats=StatBlockSpec(
                constitution=23,
                spirit=19,
                intelligence=20,
                strength=19,
                dexterity=14,
                intuition=17,
            ),
            hp=520,
            mana=160,
            item_drops=(
                ItemDropSpec(
                    "grade_iv_cores",
                    1,
                    10000,
                    source_id="m8_ashen_regent_grade_iv_core_01",
                ),
            ),
        ),
    ),
)


__all__ = ["ENEMY"]

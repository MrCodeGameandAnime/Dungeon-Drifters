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
    archetype_id="goblin_shaman",
    name="Goblin Shaman",
    stats=StatBlockSpec(
        constitution=2,
        spirit=5,
        intelligence=6,
        strength=1,
        dexterity=3,
        intuition=4,
    ),
    hp=65,
    mana=25,
    exp_reward=90,
    gold_reward=7,
    rank=EnemyRank.SPECIALIST,
    role=EnemyRole.CASTER,
    behavior=EnemyBehavior.AGGRESSIVE,
    capabilities=frozenset(
        {EnemyCapability.BASIC_ATTACKS, EnemyCapability.MAGIC}
    ),
    supported_tiers=(0, 1, 2),
    tier_profiles=(
        EnemyTierSpec(
            tier=1,
            stats=StatBlockSpec(
                constitution=3,
                spirit=6,
                intelligence=7,
                strength=1,
                dexterity=4,
                intuition=5,
            ),
            hp=75,
            mana=30,
            item_drops=(ItemDropSpec("grade_ii_cores", 1, 1000),),
        ),
        EnemyTierSpec(
            tier=2,
            stats=StatBlockSpec(
                constitution=4,
                spirit=7,
                intelligence=8,
                strength=1,
                dexterity=5,
                intuition=6,
            ),
            hp=90,
            mana=36,
            item_drops=(ItemDropSpec("grade_iii_cores", 1, 1000),),
        ),
    ),
    moves=(
        Move(
            name="Crooked Staff",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=7,
            scales_with=(ScalingAttribute.DEXTERITY,),
            accuracy=90,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="basic_attack",
            description="A quick strike from the Shaman's crooked ritual staff.",
        ),
        Move(
            name="Cinder Hex",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=5,
            power=11,
            scales_with=(ScalingAttribute.INTELLIGENCE,),
            accuracy=90,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic="basic_attack",
            description="A concentrated ember of Goblin sorcery hurled at the target.",
        ),
        Move(
            name="Blight Spark",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.MANA,
            resource_cost=10,
            power=16,
            scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.SPIRIT),
            accuracy=80,
            target=TargetType.ENEMY,
            damage_type=DamageType.MAGICAL,
            mechanic="heavy_attack",
            description="The Shaman compresses unstable ritual energy into a violent magical discharge.",
        ),
    ),
    item_drops=(("goblin_scrap", 1),),
)


__all__ = ["ENEMY"]

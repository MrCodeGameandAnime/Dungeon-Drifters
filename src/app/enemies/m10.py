"""Authored M10 Goblin-route enemy definitions."""

from app.combat.move import (
    DamageType,
    Move,
    MoveKind,
    ResourceType,
    ScalingAttribute,
    TargetType,
)
from app.enemies.definition import Enemy, EnemyBehavior, EnemyCapability, EnemyRank, EnemyRole


def _damage_move(name, *, resource_type, resource_cost, power, scales_with, accuracy,
                 damage_type, mechanic, description):
    return Move(
        name=name,
        kind=MoveKind.DAMAGE,
        resource_type=resource_type,
        resource_cost=resource_cost,
        power=power,
        scales_with=scales_with,
        accuracy=accuracy,
        target=TargetType.ENEMY,
        damage_type=damage_type,
        mechanic=mechanic,
        description=description,
    )


def _no_cost_move(name, power, scales_with, accuracy, damage_type, mechanic, description):
    return _damage_move(
        name,
        resource_type=ResourceType.NONE,
        resource_cost=0,
        power=power,
        scales_with=scales_with,
        accuracy=accuracy,
        damage_type=damage_type,
        mechanic=mechanic,
        description=description,
    )


def create_goblin_warrior_moves():
    return (
        _no_cost_move(
            "Cleaver Strike", 10, (ScalingAttribute.STRENGTH,), 92,
            DamageType.PHYSICAL, "basic_attack",
            "A disciplined cleaver strike delivered with greater force than an ordinary Goblin slash.",
        ),
        _no_cost_move(
            "Shieldbreaker Chop", 15, (ScalingAttribute.STRENGTH,), 78,
            DamageType.PHYSICAL, "heavy_attack",
            "A committed overhead chop intended to break through a defended position.",
        ),
    )


def create_goblin_shaman_moves():
    return (
        _no_cost_move(
            "Crooked Staff", 7, (ScalingAttribute.DEXTERITY,), 90,
            DamageType.PHYSICAL, "basic_attack",
            "A quick strike from the Shaman's crooked ritual staff.",
        ),
        _damage_move(
            "Cinder Hex", resource_type=ResourceType.MANA, resource_cost=5,
            power=11, scales_with=(ScalingAttribute.INTELLIGENCE,), accuracy=90,
            damage_type=DamageType.MAGICAL, mechanic="basic_attack",
            description="A concentrated ember of Goblin sorcery hurled at the target.",
        ),
        _damage_move(
            "Blight Spark", resource_type=ResourceType.MANA, resource_cost=10,
            power=16,
            scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.SPIRIT),
            accuracy=80, damage_type=DamageType.MAGICAL, mechanic="heavy_attack",
            description="The Shaman compresses unstable ritual energy into a violent magical discharge.",
        ),
    )


def create_goblin_elite_moves():
    return (
        _no_cost_move(
            "Veteran Slash", 13,
            (ScalingAttribute.STRENGTH, ScalingAttribute.DEXTERITY), 92,
            DamageType.PHYSICAL, "basic_attack",
            "A practiced slash delivered with the speed and control of an experienced killer.",
        ),
        _no_cost_move(
            "Butcher’s Advance", 18, (ScalingAttribute.STRENGTH,), 84,
            DamageType.PHYSICAL, "heavy_attack",
            "The Elite surges forward and drives its weapon through the target’s guard.",
        ),
        _no_cost_move(
            "Executioner’s Drop", 24, (ScalingAttribute.STRENGTH,), 72,
            DamageType.PHYSICAL, "heavy_attack",
            "A brutal descending strike that sacrifices accuracy for overwhelming force.",
        ),
    )


def create_goblin_lord_moves():
    return (
        _no_cost_move(
            "King’s Cleaver", 18, (ScalingAttribute.STRENGTH,), 92,
            DamageType.PHYSICAL, "basic_attack",
            "The Goblin Lord swings its enormous cleaver with practiced authority.",
        ),
        _no_cost_move(
            "Iron Decree", 25,
            (ScalingAttribute.STRENGTH, ScalingAttribute.INTUITION), 80,
            DamageType.PHYSICAL, "heavy_attack",
            "The Lord commits its full weight to a crushing blow meant to end resistance immediately.",
        ),
        _damage_move(
            "Black Banner Flame", resource_type=ResourceType.MANA, resource_cost=8,
            power=17,
            scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.SPIRIT),
            accuracy=88, damage_type=DamageType.MAGICAL, mechanic="basic_attack",
            description="Dark fire gathers around the Lord’s battle standard before surging toward the target.",
        ),
        _damage_move(
            "Tyrant’s Ruin", resource_type=ResourceType.MANA, resource_cost=14,
            power=26,
            scales_with=(ScalingAttribute.STRENGTH, ScalingAttribute.INTELLIGENCE),
            accuracy=75, damage_type=DamageType.HYBRID, mechanic="heavy_attack",
            description="The Goblin Lord combines raw physical force with unstable sorcery in one devastating assault.",
        ),
    )


class GoblinWarrior(Enemy):
    def __init__(self):
        super().__init__(
            strn=5, con=4, intl=1, dex=2, spirit=1, intuition=2,
            hp=85, mana=0, name="Goblin Warrior", archetype_id="goblin_warrior",
            rank=EnemyRank.COMMON, role=EnemyRole.BRUTE,
            behavior=EnemyBehavior.AGGRESSIVE,
            capabilities=(EnemyCapability.BASIC_ATTACKS,),
            combat_moves=create_goblin_warrior_moves(),
        )


class GoblinShaman(Enemy):
    def __init__(self):
        super().__init__(
            strn=1, con=2, intl=6, dex=3, spirit=5, intuition=4,
            hp=65, mana=25, name="Goblin Shaman", archetype_id="goblin_shaman",
            rank=EnemyRank.SPECIALIST, role=EnemyRole.CASTER,
            behavior=EnemyBehavior.AGGRESSIVE,
            capabilities=(EnemyCapability.BASIC_ATTACKS, EnemyCapability.MAGIC),
            combat_moves=create_goblin_shaman_moves(),
        )


class GoblinElite(Enemy):
    def __init__(self):
        super().__init__(
            strn=8, con=7, intl=2, dex=5, spirit=3, intuition=4,
            hp=130, mana=0, name="Goblin Elite", archetype_id="goblin_elite",
            rank=EnemyRank.ELITE, role=EnemyRole.BRUTE,
            behavior=EnemyBehavior.AGGRESSIVE,
            capabilities=(EnemyCapability.BASIC_ATTACKS,),
            combat_moves=create_goblin_elite_moves(),
        )


class GoblinLord(Enemy):
    def __init__(self):
        super().__init__(
            strn=11, con=10, intl=7, dex=6, spirit=7, intuition=9,
            hp=220, mana=30, name="Goblin Lord", archetype_id="goblin_lord",
            rank=EnemyRank.BOSS, role=EnemyRole.BOSS,
            behavior=EnemyBehavior.AGGRESSIVE,
            capabilities=(EnemyCapability.BASIC_ATTACKS, EnemyCapability.MAGIC),
            combat_moves=create_goblin_lord_moves(),
        )


__all__ = ["GoblinWarrior", "GoblinShaman", "GoblinElite", "GoblinLord"]

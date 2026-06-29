from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType


def create_legacy_enemy_moves():
    return (
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
        Move(
            name="suplex",
            kind=MoveKind.DAMAGE,
            resource_type=ResourceType.NONE,
            resource_cost=0,
            power=14,
            scales_with=(ScalingAttribute.STRENGTH,),
            accuracy=75,
            target=TargetType.ENEMY,
            damage_type=DamageType.PHYSICAL,
            mechanic="stagger",
            description="A forceful throw meant to disrupt the target.",
        ),
    )


class Enemy:
    def __init__(self, strn, con, intl, dex, hp, mana, name, combat_moves, spirit=1, intuition=1):
        self.strength = strn
        self.constitution = con
        self.intelligence = intl
        self.dexterity = dex
        self.spirit = spirit
        self.intuition = intuition
        self.hp = hp
        self.mana = mana
        self.name = name
        self.combat_moves = tuple(combat_moves)
        self.moves = {
            index: move.name
            for index, move in enumerate(self.combat_moves, start=1)
        }
        self.level = 1
        self.exp = 0


class Goblin(Enemy):
    def __init__(self):
        super().__init__(
            strn=3,
            con=2,
            intl=1,
            dex=1,
            hp=60,
            mana=10,
            name="Goblin",
            combat_moves=create_legacy_enemy_moves())


class Orc(Enemy):
    def __init__(self):
        super().__init__(
            strn=7,
            con=5,
            intl=1,
            dex=1,
            hp=60,
            mana=10,
            name="Orc",
            combat_moves=create_legacy_enemy_moves())


class SkeletonArcher(Enemy):
    def __init__(self):
        super().__init__(
            strn=7,
            con=5,
            intl=1,
            dex=1,
            hp=60,
            mana=10,
            name="Skeleton Archer",
            combat_moves=create_legacy_enemy_moves())


class Zombie(Enemy):
    def __init__(self):
        super().__init__(
            strn=7,
            con=5,
            intl=1,
            dex=1,
            hp=60,
            mana=10,
            name="Zombie",
            combat_moves=create_legacy_enemy_moves())


class SnakeLord(Enemy):
    def __init__(self):
        super().__init__(
            strn=7,
            con=5,
            intl=1,
            dex=1,
            hp=60,
            mana=10,
            name="Snake Lord",
            combat_moves=create_legacy_enemy_moves())

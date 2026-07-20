from enum import StrEnum


class EnemyRank(StrEnum):
    COMMON = "common"
    SPECIALIST = "specialist"
    ELITE = "elite"
    BOSS = "boss"


class EnemyRole(StrEnum):
    MELEE_SKIRMISHER = "melee_skirmisher"
    BRUTE = "brute"
    RANGED = "ranged"
    CASTER = "caster"
    SUPPORT = "support"
    CONTROLLER = "controller"
    BOSS = "boss"


class EnemyBehavior(StrEnum):
    AGGRESSIVE = "aggressive"


class EnemyCapability(StrEnum):
    BASIC_ATTACKS = "basic_attacks"
    MAGIC = "magic"
    HEALING = "healing"
    SUPER = "super"
    DEFEND = "defend"


class Enemy:
    def __init__(
            self,
            strn,
            con,
            intl,
            dex,
            hp,
            mana,
            exp_reward,
            gold_reward,
            name,
            combat_moves,
            archetype_id,
            rank,
            role,
            behavior,
            capabilities,
            spirit=1,
            intuition=1):
        self.strength = strn
        self.constitution = con
        self.intelligence = intl
        self.dexterity = dex
        self.spirit = spirit
        self.intuition = intuition
        self.hp = hp
        self.mana = mana
        self._exp_reward = _validate_nonnegative_integer("exp_reward", exp_reward)
        self._gold_reward = _validate_nonnegative_integer("gold_reward", gold_reward)
        self.archetype_id = _validate_nonempty_string("archetype_id", archetype_id)
        self.name = name
        self.rank = _validate_enum_member("rank", rank, EnemyRank)
        self.role = _validate_enum_member("role", role, EnemyRole)
        self.behavior = _validate_enum_member("behavior", behavior, EnemyBehavior)
        self.capabilities = _validate_capabilities(capabilities)
        self.combat_moves = tuple(combat_moves)

    @property
    def moves(self):
        return {
            index: move.name
            for index, move in enumerate(self.combat_moves, start=1)
        }

    @property
    def exp_reward(self):
        return self._exp_reward

    @property
    def gold_reward(self):
        return self._gold_reward


def _validate_nonempty_string(name, value):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must not be empty")

    return value


def _validate_nonnegative_integer(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a nonnegative integer")
    if value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")

    return value


def _validate_enum_member(name, value, enum_type):
    if not isinstance(value, enum_type):
        raise TypeError(f"{name} must be a {enum_type.__name__} member")

    return value


def _validate_capabilities(capabilities):
    if isinstance(capabilities, str):
        raise TypeError("capabilities must be an iterable of EnemyCapability members")

    try:
        normalized = frozenset(capabilities)
    except TypeError as error:
        raise TypeError("capabilities must be an iterable of EnemyCapability members") from error

    for capability in normalized:
        if not isinstance(capability, EnemyCapability):
            raise TypeError("capabilities must contain only EnemyCapability members")

    return normalized


__all__ = [
    "Enemy",
    "EnemyBehavior",
    "EnemyCapability",
    "EnemyRank",
    "EnemyRole",
]

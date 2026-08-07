"""Immutable authored enemy specifications."""

import keyword
import re
from dataclasses import dataclass

from app.combat.move import Move
from app.enemies.definition import (
    Enemy,
    EnemyBehavior,
    EnemyCapability,
    EnemyRank,
    EnemyRole,
)
from app.enemies.validation import validate_enemy_tier


_ARCHETYPE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def _validate_integer(name, value, *, minimum, maximum=None):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        if maximum is None:
            raise ValueError(f"{name} must be at least {minimum}")
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def _validate_nonempty_string(name, value):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


@dataclass(frozen=True)
class StatBlockSpec:
    constitution: int
    spirit: int
    intelligence: int
    strength: int
    dexterity: int
    intuition: int

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            object.__setattr__(
                self,
                name,
                _validate_integer(name, getattr(self, name), minimum=1, maximum=100),
            )


@dataclass(frozen=True)
class EnemySpec:
    archetype_id: str
    name: str
    stats: StatBlockSpec
    hp: int
    mana: int
    exp_reward: int
    gold_reward: int
    rank: EnemyRank
    role: EnemyRole
    behavior: EnemyBehavior
    capabilities: frozenset[EnemyCapability]
    moves: tuple[Move, ...]
    supported_tiers: tuple[int, ...] = (0,)

    def __post_init__(self):
        archetype_id = _validate_nonempty_string("archetype_id", self.archetype_id)
        if (
            _ARCHETYPE_ID_PATTERN.fullmatch(archetype_id) is None
            or keyword.iskeyword(archetype_id)
        ):
            raise ValueError(
                "archetype_id must be a lowercase snake-case Python module name"
            )
        object.__setattr__(self, "archetype_id", archetype_id)
        object.__setattr__(self, "name", _validate_nonempty_string("name", self.name))

        if not isinstance(self.stats, StatBlockSpec):
            raise TypeError("stats must be a StatBlockSpec")
        object.__setattr__(self, "hp", _validate_integer("hp", self.hp, minimum=1))
        for name in ("mana", "exp_reward", "gold_reward"):
            object.__setattr__(
                self,
                name,
                _validate_integer(name, getattr(self, name), minimum=0),
            )

        for name, enum_type in (
            ("rank", EnemyRank),
            ("role", EnemyRole),
            ("behavior", EnemyBehavior),
        ):
            if not isinstance(getattr(self, name), enum_type):
                raise TypeError(f"{name} must be a {enum_type.__name__} member")

        if not isinstance(self.capabilities, frozenset):
            raise TypeError("capabilities must be a frozenset")
        if any(
            not isinstance(capability, EnemyCapability)
            for capability in self.capabilities
        ):
            raise TypeError("capabilities must contain only EnemyCapability members")

        if not isinstance(self.moves, tuple):
            raise TypeError("moves must be a tuple")
        if not self.moves:
            raise ValueError("moves must not be empty")
        if any(not isinstance(move, Move) for move in self.moves):
            raise TypeError("moves must contain only Move values")
        move_names = tuple(move.name for move in self.moves)
        if len(set(move_names)) != len(move_names):
            raise ValueError("moves must use unique names")

        if not isinstance(self.supported_tiers, tuple):
            raise TypeError("supported_tiers must be a tuple")
        if any(
            isinstance(tier, bool) or not isinstance(tier, int)
            for tier in self.supported_tiers
        ):
            raise TypeError("supported_tiers must contain only integers")
        if self.supported_tiers != (0,):
            raise ValueError("FLAT-1 enemy specifications support only tier 0")

    def create_definition(self, tier=0):
        tier = validate_enemy_tier(tier)
        if tier not in self.supported_tiers:
            raise ValueError(f"{self.archetype_id} does not support tier {tier}")

        return Enemy(
            strn=self.stats.strength,
            con=self.stats.constitution,
            intl=self.stats.intelligence,
            dex=self.stats.dexterity,
            spirit=self.stats.spirit,
            intuition=self.stats.intuition,
            hp=self.hp,
            mana=self.mana,
            exp_reward=self.exp_reward,
            gold_reward=self.gold_reward,
            name=self.name,
            archetype_id=self.archetype_id,
            rank=self.rank,
            role=self.role,
            behavior=self.behavior,
            capabilities=tuple(self.capabilities),
            combat_moves=(move for move in self.moves),
        )


__all__ = ["EnemySpec", "StatBlockSpec"]

"""Immutable authored enemy specifications."""

import keyword
import re
from dataclasses import dataclass

from app.combat.move import DamageComponentIdentity, Move, validate_damage_identity_keys
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
class ItemDropSpec:
    item_id: str
    quantity: int
    chance_bps: int

    def __post_init__(self):
        item_id = _validate_nonempty_string("item_id", self.item_id)
        if _ARCHETYPE_ID_PATTERN.fullmatch(item_id) is None:
            raise ValueError("item_id must be lowercase snake case")
        object.__setattr__(self, "item_id", item_id)
        object.__setattr__(
            self,
            "quantity",
            _validate_integer("drop quantity", self.quantity, minimum=1),
        )
        object.__setattr__(
            self,
            "chance_bps",
            _validate_integer("drop chance", self.chance_bps, minimum=0, maximum=10000),
        )


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
class EnemyTierSpec:
    tier: int
    stats: StatBlockSpec
    hp: int
    mana: int
    item_drops: tuple[ItemDropSpec, ...] = ()

    def __post_init__(self):
        tier = validate_enemy_tier(self.tier)
        if tier == 0:
            raise ValueError("tier profiles must be above tier zero")
        object.__setattr__(self, "tier", tier)
        if not isinstance(self.stats, StatBlockSpec):
            raise TypeError("stats must be a StatBlockSpec")
        object.__setattr__(self, "hp", _validate_integer("hp", self.hp, minimum=1))
        object.__setattr__(
            self,
            "mana",
            _validate_integer("mana", self.mana, minimum=0),
        )
        if not isinstance(self.item_drops, tuple):
            raise TypeError("item_drops must be a tuple")
        if any(not isinstance(drop, ItemDropSpec) for drop in self.item_drops):
            raise TypeError("tier item_drops must contain ItemDropSpec values")


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
    item_drops: tuple[tuple[str, int], ...] = ()
    tier_profiles: tuple[EnemyTierSpec, ...] = ()
    damage_resistances: tuple[tuple[DamageComponentIdentity, str], ...] = ()
    damage_weaknesses: tuple[tuple[DamageComponentIdentity, str], ...] = ()

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
        for tier in self.supported_tiers:
            validate_enemy_tier(tier)
        if (
            not self.supported_tiers
            or self.supported_tiers[0] != 0
            or tuple(sorted(set(self.supported_tiers))) != self.supported_tiers
        ):
            raise ValueError("supported_tiers must be unique, ordered, and start at 0")

        if not isinstance(self.tier_profiles, tuple):
            raise TypeError("tier_profiles must be a tuple")
        if any(not isinstance(profile, EnemyTierSpec) for profile in self.tier_profiles):
            raise TypeError("tier_profiles must contain only EnemyTierSpec values")
        profile_tiers = tuple(profile.tier for profile in self.tier_profiles)
        if len(set(profile_tiers)) != len(profile_tiers):
            raise ValueError("tier_profiles must use unique tiers")
        if tuple(sorted(profile_tiers)) != profile_tiers:
            raise ValueError("tier_profiles must be ordered by tier")
        if self.supported_tiers != (0,) + profile_tiers:
            raise ValueError("tier_profiles must match supported_tiers")

        if not isinstance(self.item_drops, tuple):
            raise TypeError("item_drops must be a tuple")
        drop_ids = []
        for drop in self.item_drops:
            if not isinstance(drop, tuple) or len(drop) != 2:
                raise TypeError("each item drop must be an (item_id, quantity) tuple")
            item_id, quantity = drop
            if (
                not isinstance(item_id, str)
                or _ARCHETYPE_ID_PATTERN.fullmatch(item_id) is None
            ):
                raise ValueError("item drop IDs must be lowercase snake case")
            _validate_integer("item drop quantity", quantity, minimum=1)
            drop_ids.append(item_id)
        if len(set(drop_ids)) != len(drop_ids):
            raise ValueError("item drop IDs must be unique")

        resistances = validate_damage_identity_keys(
            "damage_resistances",
            self.damage_resistances,
        )
        weaknesses = validate_damage_identity_keys(
            "damage_weaknesses",
            self.damage_weaknesses,
        )
        if any(identity in weaknesses for identity in resistances):
            raise ValueError("an enemy cannot resist and be weak to the same identity")
        object.__setattr__(self, "damage_resistances", resistances)
        object.__setattr__(self, "damage_weaknesses", weaknesses)

    def create_definition(self, tier=0):
        tier = validate_enemy_tier(tier)
        if tier not in self.supported_tiers:
            raise ValueError(f"{self.archetype_id} does not support tier {tier}")

        profile = None
        if tier != 0:
            for candidate in self.tier_profiles:
                if candidate.tier == tier:
                    profile = candidate
                    break
        stats = self.stats if profile is None else profile.stats
        hp = self.hp if profile is None else profile.hp
        mana = self.mana if profile is None else profile.mana

        return Enemy(
            strn=stats.strength,
            con=stats.constitution,
            intl=stats.intelligence,
            dex=stats.dexterity,
            spirit=stats.spirit,
            intuition=stats.intuition,
            hp=hp,
            mana=mana,
            exp_reward=self.exp_reward,
            gold_reward=self.gold_reward,
            name=self.name,
            archetype_id=self.archetype_id,
            rank=self.rank,
            role=self.role,
            behavior=self.behavior,
            capabilities=tuple(self.capabilities),
            combat_moves=(move for move in self.moves),
            damage_resistances=self.damage_resistances,
            damage_weaknesses=self.damage_weaknesses,
        )

    def item_drop_table_for_tier(self, tier):
        tier = validate_enemy_tier(tier)
        if tier not in self.supported_tiers:
            raise ValueError(f"{self.archetype_id} does not support tier {tier}")
        for profile in self.tier_profiles:
            if profile.tier == tier:
                return profile.item_drops
        return ()


__all__ = ["EnemySpec", "EnemyTierSpec", "ItemDropSpec", "StatBlockSpec"]

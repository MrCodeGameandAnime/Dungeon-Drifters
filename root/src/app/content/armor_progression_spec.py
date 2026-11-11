"""Authored deterministic armor investment and rarity advancement costs."""

from dataclasses import dataclass

from app.content.armor_spec import ARMOR_RARITIES
from app.content.equipment_spec import (
    EQUIPMENT_TEMPLATES,
    MAX_ARMOR_UPGRADE_RANK,
)
from app.content.weapon_progression_spec import get_material_spec


@dataclass(frozen=True)
class ArmorUpgradeStepSpec:
    rank: int
    gold_cost: int
    material_quantity: int

    def __post_init__(self):
        for name in ("rank", "gold_cost", "material_quantity"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
        if self.rank < 1:
            raise ValueError("armor upgrade rank must be positive")
        if self.gold_cost < 0 or self.material_quantity < 1:
            raise ValueError("armor upgrade costs are invalid")


@dataclass(frozen=True)
class ArmorRarityAdvanceSpec:
    source_rarity: str
    target_rarity: str
    gold_cost: int
    material_id: str
    material_quantity: int

    def __post_init__(self):
        rarity_ids = tuple(spec.rarity_id for spec in ARMOR_RARITIES)
        if (
            self.source_rarity not in rarity_ids
            or self.target_rarity not in rarity_ids
            or rarity_ids.index(self.target_rarity)
            != rarity_ids.index(self.source_rarity) + 1
        ):
            raise ValueError("armor rarity advancement must move exactly one tier")
        if isinstance(self.gold_cost, bool) or not isinstance(self.gold_cost, int):
            raise TypeError("rarity advancement gold cost must be an integer")
        if self.gold_cost < 0:
            raise ValueError("rarity advancement gold cost must not be negative")
        if isinstance(self.material_quantity, bool) or not isinstance(
            self.material_quantity, int
        ):
            raise TypeError("rarity advancement material quantity must be an integer")
        if self.material_quantity < 1:
            raise ValueError("rarity advancement material quantity must be positive")
        material = get_material_spec(self.material_id)
        target_grade = rarity_ids.index(self.source_rarity) + 1
        if material.family != "cores" or material.grade != target_grade:
            raise ValueError("rarity advancement requires its target-grade core")


ARMOR_UPGRADE_STEPS = (
    ArmorUpgradeStepSpec(1, 10, 1),
    ArmorUpgradeStepSpec(2, 20, 2),
    ArmorUpgradeStepSpec(3, 40, 3),
    ArmorUpgradeStepSpec(4, 80, 4),
)

RARITY_ADVANCEMENT_SPECS = (
    ArmorRarityAdvanceSpec("common", "uncommon", 25, "grade_i_cores", 1),
    ArmorRarityAdvanceSpec("uncommon", "rare", 50, "grade_ii_cores", 1),
    ArmorRarityAdvanceSpec("rare", "epic", 100, "grade_iii_cores", 1),
    ArmorRarityAdvanceSpec("epic", "legendary", 200, "grade_iv_cores", 1),
)

_UPGRADE_BY_RANK = {spec.rank: spec for spec in ARMOR_UPGRADE_STEPS}
_RARITY_ADVANCEMENT_BY_SOURCE = {
    spec.source_rarity: spec for spec in RARITY_ADVANCEMENT_SPECS
}


def get_armor_upgrade_step(rank):
    try:
        return _UPGRADE_BY_RANK[rank]
    except (KeyError, TypeError) as error:
        raise ValueError(f"no armor upgrade step for rank {rank!r}") from error


def get_armor_upgrade_material(definition_id):
    for template in EQUIPMENT_TEMPLATES:
        if template.definition_id == definition_id and template.is_armor:
            return template.material_id
    raise ValueError(f"no armor upgrade material for {definition_id!r}")


def get_rarity_advancement(source_rarity):
    try:
        return _RARITY_ADVANCEMENT_BY_SOURCE[source_rarity]
    except (KeyError, TypeError) as error:
        raise ValueError(f"no rarity advancement from {source_rarity!r}") from error


def validate_armor_progression_content(*, upgrade_steps, rarity_advancements):
    upgrade_steps = tuple(upgrade_steps)
    rarity_advancements = tuple(rarity_advancements)
    if upgrade_steps != tuple(sorted(upgrade_steps, key=lambda item: item.rank)):
        raise ValueError("armor upgrade steps must be ordered by rank")
    if tuple(item.rank for item in upgrade_steps) != tuple(
        range(1, MAX_ARMOR_UPGRADE_RANK + 1)
    ):
        raise ValueError("armor upgrade track must cover its configured ranks")
    if tuple(
        (item.source_rarity, item.target_rarity) for item in rarity_advancements
    ) != (("common", "uncommon"), ("uncommon", "rare"), ("rare", "epic"), ("epic", "legendary")):
        raise ValueError("rarity advancement must define every adjacent rarity pair")
    return upgrade_steps, rarity_advancements


validate_armor_progression_content(
    upgrade_steps=ARMOR_UPGRADE_STEPS,
    rarity_advancements=RARITY_ADVANCEMENT_SPECS,
)


__all__ = [
    "ARMOR_UPGRADE_STEPS",
    "RARITY_ADVANCEMENT_SPECS",
    "ArmorRarityAdvanceSpec",
    "ArmorUpgradeStepSpec",
    "get_armor_upgrade_material",
    "get_armor_upgrade_step",
    "get_rarity_advancement",
    "validate_armor_progression_content",
]

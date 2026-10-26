"""Immutable authored data for signature-weapon progression slots."""

from dataclasses import dataclass


SLOT_MATERIAL_FAMILIES = ("metal", "fiber", "timber", "cores")
CRAFTING_LEVEL_THRESHOLDS = tuple(range(0, 1000, 10))
MAX_CRAFTING_EXPERIENCE = CRAFTING_LEVEL_THRESHOLDS[-1]
QUALITY_GATES = (25, 50, 75, 100)
_GRADE_NAMES = ("I", "II", "III", "IV")
_IMPROVEMENT_COSTS_AND_AWARDS = ((1, 20), (2, 30), (3, 40), (4, 50))
IMPROVEMENT_ROLL_WEIGHT_BANDS = (
    (1, (40, 25, 18, 12, 5)),
    (25, (32, 24, 19, 15, 10)),
    (50, (24, 22, 20, 18, 16)),
    (75, (16, 19, 21, 22, 22)),
    (100, (10, 15, 20, 25, 30)),
)
SALVAGE_DOUBLE_YIELD_CHANCE_BANDS = (
    (1, 20),
    (25, 35),
    (50, 50),
    (75, 65),
    (100, 80),
)


@dataclass(frozen=True)
class MaterialSpec:
    item_id: str
    display_name: str
    family: str
    grade: int

    def __post_init__(self):
        for field in ("item_id", "display_name"):
            value = getattr(self, field)
            if not isinstance(value, str):
                raise TypeError(f"{field} must be a string")
            if not value.strip():
                raise ValueError(f"{field} must not be empty")
        if self.family not in SLOT_MATERIAL_FAMILIES:
            raise ValueError("unknown material family")
        if isinstance(self.grade, bool) or not isinstance(self.grade, int):
            raise TypeError("material grade must be an integer")
        if self.grade not in (1, 2, 3, 4):
            raise ValueError("material grade must be between 1 and 4")


@dataclass(frozen=True)
class WeaponImprovementRecipeSpec:
    recipe_id: str
    material_id: str
    material_cost: int
    crafting_award: int

    def __post_init__(self):
        for field in ("recipe_id", "material_id"):
            value = getattr(self, field)
            if not isinstance(value, str):
                raise TypeError(f"{field} must be a string")
            if not value:
                raise ValueError(f"{field} must not be empty")
        for field in ("material_cost", "crafting_award"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field} must be an integer")
            if value < 1:
                raise ValueError(f"{field} must be positive")


@dataclass(frozen=True)
class DismantleSpec:
    item_id: str
    output_material_ids: tuple[str, ...]
    maximum_yield: int

    def __post_init__(self):
        if not isinstance(self.item_id, str) or not self.item_id:
            raise ValueError("item_id must be a non-empty string")
        if not isinstance(self.output_material_ids, tuple):
            raise TypeError("output_material_ids must be a tuple")
        if not self.output_material_ids or not all(
            isinstance(item_id, str) and item_id for item_id in self.output_material_ids
        ):
            raise ValueError("dismantle outputs must contain material IDs")
        if isinstance(self.maximum_yield, bool) or not isinstance(
            self.maximum_yield,
            int,
        ):
            raise TypeError("maximum_yield must be an integer")
        if self.maximum_yield < 1 or self.maximum_yield > 5:
            raise ValueError("maximum_yield must be between 1 and 5")


MATERIAL_SPECS = tuple(
    MaterialSpec(
        item_id=f"grade_{_GRADE_NAMES[grade - 1].lower()}_{family}",
        display_name=f"Grade {_GRADE_NAMES[grade - 1]} {family.title()}",
        family=family,
        grade=grade,
    )
    for grade in range(1, 5)
    for family in SLOT_MATERIAL_FAMILIES
)

IMPROVEMENT_RECIPE_SPECS = tuple(
    WeaponImprovementRecipeSpec(
        recipe_id=f"improve_grade_{grade}_{family}",
        material_id=f"grade_{_GRADE_NAMES[grade - 1].lower()}_{family}",
        material_cost=cost,
        crafting_award=award,
    )
    for grade, (cost, award) in enumerate(
        _IMPROVEMENT_COSTS_AND_AWARDS,
        start=1,
    )
    for family in SLOT_MATERIAL_FAMILIES
)

DISMANTLE_SPECS = (
    DismantleSpec(
        "goblin_scrap",
        (
            "grade_i_metal",
            "grade_i_fiber",
            "grade_i_timber",
        ),
        2,
    ),
    DismantleSpec("goblin_lord_core", ("grade_i_cores",), 1),
)

_MATERIALS_BY_ID = {spec.item_id: spec for spec in MATERIAL_SPECS}
_IMPROVEMENT_RECIPES_BY_MATERIAL = {
    spec.material_id: spec for spec in IMPROVEMENT_RECIPE_SPECS
}
_DISMANTLE_SPECS_BY_ID = {spec.item_id: spec for spec in DISMANTLE_SPECS}


def get_material_spec(item_id):
    try:
        return _MATERIALS_BY_ID[item_id]
    except (KeyError, TypeError) as error:
        raise ValueError(f"unknown progression material: {item_id}") from error


def get_improvement_recipe(material_id):
    try:
        return _IMPROVEMENT_RECIPES_BY_MATERIAL[material_id]
    except (KeyError, TypeError) as error:
        raise ValueError(f"unknown improvement material: {material_id}") from error


def get_dismantle_spec(item_id):
    try:
        return _DISMANTLE_SPECS_BY_ID[item_id]
    except (KeyError, TypeError) as error:
        raise ValueError(f"item cannot be dismantled: {item_id}") from error


def improvement_roll(crafting_level, rng):
    if isinstance(crafting_level, bool) or not isinstance(crafting_level, int):
        raise TypeError("crafting level must be an integer")
    if not 1 <= crafting_level <= 100:
        raise ValueError("crafting level must be between 1 and 100")
    weights = IMPROVEMENT_ROLL_WEIGHT_BANDS[0][1]
    for minimum_level, candidate_weights in IMPROVEMENT_ROLL_WEIGHT_BANDS:
        if crafting_level >= minimum_level:
            weights = candidate_weights
    roll = rng.randint(1, 100)
    cumulative = 0
    for points, weight in enumerate(weights, start=1):
        cumulative += weight
        if roll <= cumulative:
            return points
    raise ValueError("improvement weights must total 100")


def salvage_double_yield_chance(crafting_level):
    if isinstance(crafting_level, bool) or not isinstance(crafting_level, int):
        raise TypeError("crafting level must be an integer")
    if not 1 <= crafting_level <= 100:
        raise ValueError("crafting level must be between 1 and 100")
    chance = SALVAGE_DOUBLE_YIELD_CHANCE_BANDS[0][1]
    for minimum_level, candidate_chance in SALVAGE_DOUBLE_YIELD_CHANCE_BANDS:
        if crafting_level >= minimum_level:
            chance = candidate_chance
    return chance


def crafting_level_for_experience(experience):
    if isinstance(experience, bool) or not isinstance(experience, int):
        raise TypeError("crafting experience must be an integer")
    if experience < 0:
        raise ValueError("crafting experience must not be negative")
    level = 1
    for threshold in CRAFTING_LEVEL_THRESHOLDS[1:]:
        if experience < threshold:
            break
        level += 1
    return level


@dataclass(frozen=True)
class WeaponSlotSpec:
    slot_id: str
    label: str
    material_family: str
    starting_component_id: str

    def __post_init__(self):
        for field in (
            "slot_id",
            "label",
            "material_family",
            "starting_component_id",
        ):
            value = getattr(self, field)
            if not isinstance(value, str):
                raise TypeError(f"{field} must be a string")
            if not value:
                raise ValueError(f"{field} must not be empty")
        if self.material_family not in SLOT_MATERIAL_FAMILIES:
            raise ValueError("unknown slot material family")


@dataclass(frozen=True)
class WeaponProgressionSpec:
    slots: tuple[WeaponSlotSpec, ...]

    def __post_init__(self):
        if not isinstance(self.slots, tuple):
            raise TypeError("slots must be a tuple")
        if len(self.slots) != len(SLOT_MATERIAL_FAMILIES):
            raise ValueError("signature weapons must define exactly four slots")
        if not all(isinstance(slot, WeaponSlotSpec) for slot in self.slots):
            raise TypeError("slots must contain WeaponSlotSpec values")
        slot_ids = tuple(slot.slot_id for slot in self.slots)
        if len(set(slot_ids)) != len(slot_ids):
            raise ValueError("weapon slot IDs must be unique")
        for slot, expected_family in zip(self.slots, SLOT_MATERIAL_FAMILIES):
            if slot.material_family != expected_family:
                raise ValueError(
                    "slot material families must be metal, fiber, timber, cores"
                )


__all__ = (
    "CRAFTING_LEVEL_THRESHOLDS",
    "DISMANTLE_SPECS",
    "DismantleSpec",
    "IMPROVEMENT_RECIPE_SPECS",
    "IMPROVEMENT_ROLL_WEIGHT_BANDS",
    "MATERIAL_SPECS",
    "MaterialSpec",
    "MAX_CRAFTING_EXPERIENCE",
    "QUALITY_GATES",
    "SLOT_MATERIAL_FAMILIES",
    "SALVAGE_DOUBLE_YIELD_CHANCE_BANDS",
    "WeaponProgressionSpec",
    "WeaponImprovementRecipeSpec",
    "WeaponSlotSpec",
    "crafting_level_for_experience",
    "get_dismantle_spec",
    "get_improvement_recipe",
    "get_material_spec",
    "improvement_roll",
    "salvage_double_yield_chance",
)

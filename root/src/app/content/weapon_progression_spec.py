"""Immutable authored data for signature-weapon progression slots."""

from dataclasses import dataclass


SLOT_MATERIAL_FAMILIES = ("metal", "fiber", "timber", "cores")
CRAFTING_LEVEL_THRESHOLDS = tuple(range(0, 1000, 10))
MAX_CRAFTING_EXPERIENCE = CRAFTING_LEVEL_THRESHOLDS[-1]
QUALITY_GATES = (25, 50, 75, 100)
_GRADE_NAMES = ("I", "II", "III", "IV")
_MATERIAL_DISPLAY_NAMES = (
    ("Scrap metal", "Cord", "Softwood", "Faded Core"),
    ("Iron", "Cotton", "Hardwood", "Elemental core"),
    ("Steel", "Silk", "Ironwood", "Overcharged core"),
    ("Etheral Alloy", "Carbon", "Elderwood", "Singularity Core"),
)
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
PHYSICAL_IDENTITY_THRESHOLD = 2
MYSTICAL_IDENTITY_THRESHOLD = 2
PHYSICAL_IDENTITIES = ("Fast", "Refined", "Heavy", "Great")
MYSTICAL_IDENTITIES = ("Enchanted", "Mystic", "Attuned", "Legendary")


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


@dataclass(frozen=True)
class ComponentMoveModifierSpec:
    move_name: str
    power_delta: int = 0
    resource_cost_delta: int = 0
    accuracy_delta: int = 0
    damage_type: str | None = None

    def __post_init__(self):
        if not isinstance(self.move_name, str) or not self.move_name.strip():
            raise ValueError("move_name must be a nonempty string")
        for name in ("power_delta", "resource_cost_delta", "accuracy_delta"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
        if self.damage_type is not None and self.damage_type not in {
            "physical",
            "magical",
            "hybrid",
        }:
            raise ValueError("component damage_type is invalid")
        if not any(
            (self.power_delta, self.resource_cost_delta, self.accuracy_delta)
        ) and self.damage_type is None:
            raise ValueError("component move modifier must change a move")


@dataclass(frozen=True)
class WeaponComponentSpec:
    component_id: str
    display_name: str
    slot_id: str
    is_starting: bool = False
    recipe_material_id: str | None = None
    recipe_cost: int = 0
    crafting_award: int = 0
    physical_identity: str | None = None
    physical_points: int = 0
    mystical_identity: str | None = None
    mystical_points: int = 0
    move_modifiers: tuple[ComponentMoveModifierSpec, ...] = ()

    def __post_init__(self):
        for name in ("component_id", "display_name", "slot_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a nonempty string")
        if not isinstance(self.is_starting, bool):
            raise TypeError("is_starting must be a boolean")
        if self.recipe_material_id is not None and (
            not isinstance(self.recipe_material_id, str)
            or not self.recipe_material_id
        ):
            raise ValueError("recipe_material_id must be nonempty or None")
        for name in ("recipe_cost", "crafting_award", "physical_points", "mystical_points"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
            if value < 0:
                raise ValueError(f"{name} must not be negative")
        if self.is_starting:
            if (
                self.recipe_material_id is not None
                or self.recipe_cost
                or self.crafting_award
                or self.move_modifiers
                or self.physical_identity is not None
                or self.mystical_identity is not None
                or self.physical_points
                or self.mystical_points
            ):
                raise ValueError("starting components must preserve baseline behavior")
        elif (
            self.recipe_material_id is None
            or self.recipe_cost < 1
            or self.crafting_award < 1
        ):
            raise ValueError("craftable components require a material recipe and award")
        if self.physical_identity is None:
            if self.physical_points:
                raise ValueError("physical points require a physical identity")
        elif self.physical_identity not in PHYSICAL_IDENTITIES or self.physical_points < 1:
            raise ValueError("physical identity contribution is invalid")
        if self.mystical_identity is None:
            if self.mystical_points:
                raise ValueError("mystical points require a mystical identity")
        elif self.mystical_identity not in MYSTICAL_IDENTITIES or self.mystical_points < 1:
            raise ValueError("mystical identity contribution is invalid")
        if not isinstance(self.move_modifiers, tuple) or not all(
            isinstance(modifier, ComponentMoveModifierSpec)
            for modifier in self.move_modifiers
        ):
            raise TypeError("move_modifiers must contain ComponentMoveModifierSpec values")


MATERIAL_SPECS = tuple(
    MaterialSpec(
        item_id=f"grade_{_GRADE_NAMES[grade - 1].lower()}_{family}",
        display_name=_MATERIAL_DISPLAY_NAMES[grade - 1][family_index],
        family=family,
        grade=grade,
    )
    for grade in range(1, 5)
    for family_index, family in enumerate(SLOT_MATERIAL_FAMILIES)
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
    components: tuple[WeaponComponentSpec, ...]

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
        if not isinstance(self.components, tuple) or not all(
            isinstance(component, WeaponComponentSpec)
            for component in self.components
        ):
            raise TypeError("components must contain WeaponComponentSpec values")
        component_ids = tuple(component.component_id for component in self.components)
        if len(set(component_ids)) != len(component_ids):
            raise ValueError("weapon component IDs must be unique")
        for slot in self.slots:
            matching = tuple(
                component
                for component in self.components
                if component.slot_id == slot.slot_id
            )
            starters = tuple(component for component in matching if component.is_starting)
            if len(starters) != 1 or starters[0].component_id != slot.starting_component_id:
                raise ValueError("each slot must define its authored starting component")
            craftable = tuple(component for component in matching if not component.is_starting)
            if not craftable:
                raise ValueError("each slot must offer a craftable component")
        slot_ids = {slot.slot_id for slot in self.slots}
        if any(component.slot_id not in slot_ids for component in self.components):
            raise ValueError("component references an unknown weapon slot")
        for component in self.components:
            if component.is_starting:
                continue
            material = get_material_spec(component.recipe_material_id)
            slot = next(slot for slot in self.slots if slot.slot_id == component.slot_id)
            if material.grade != 1 or material.family != slot.material_family:
                raise ValueError("Floor I component recipes must use matching Grade-I materials")


def get_weapon_component_spec(progression, component_id):
    if not isinstance(progression, WeaponProgressionSpec):
        raise TypeError("progression must be a WeaponProgressionSpec")
    for component in progression.components:
        if component.component_id == component_id:
            return component
    raise ValueError(f"unknown signature weapon component: {component_id}")


def derive_weapon_identities(progression, installed_components):
    scores = ({}, {})
    for slot in progression.slots:
        component = get_weapon_component_spec(
            progression,
            installed_components[slot.slot_id],
        )
        if component.physical_identity is not None:
            scores[0][component.physical_identity] = (
                scores[0].get(component.physical_identity, 0)
                + component.physical_points
            )
        if component.mystical_identity is not None:
            scores[1][component.mystical_identity] = (
                scores[1].get(component.mystical_identity, 0)
                + component.mystical_points
            )
    return (
        _winning_identity(scores[0], PHYSICAL_IDENTITY_THRESHOLD),
        _winning_identity(scores[1], MYSTICAL_IDENTITY_THRESHOLD),
    )


def project_component_move_effects(progression, installed_components, moves):
    modifiers_by_move = {}
    for slot in progression.slots:
        component = get_weapon_component_spec(
            progression,
            installed_components[slot.slot_id],
        )
        for modifier in component.move_modifiers:
            current = modifiers_by_move.setdefault(
                modifier.move_name,
                [0, 0, 0, None],
            )
            current[0] += modifier.power_delta
            current[1] += modifier.resource_cost_delta
            current[2] += modifier.accuracy_delta
            if modifier.damage_type is not None:
                current[3] = modifier.damage_type

    if not modifiers_by_move:
        return moves
    projected = []
    for move in moves:
        values = modifiers_by_move.get(move.name)
        if values is None:
            projected.append(move)
            continue
        power_delta, cost_delta, accuracy_delta, damage_type = values
        projected.append(
            type(move)(
                name=move.name,
                kind=move.kind,
                resource_type=move.resource_type,
                resource_cost=max(0, move.resource_cost + cost_delta),
                power=max(0, move.power + power_delta),
                scales_with=move.scales_with,
                accuracy=max(0, min(100, move.accuracy + accuracy_delta)),
                target=move.target,
                damage_type=damage_type or move.damage_type,
                mechanic=move.mechanic,
                description=move.description,
                presentation=move.presentation,
                is_spell=move.is_spell,
                frost_backlash=move.frost_backlash,
            )
        )
    return tuple(projected)


def _winning_identity(scores, threshold):
    if not scores:
        return None
    highest = max(scores.values())
    winners = tuple(identity for identity, score in scores.items() if score == highest)
    if highest < threshold or len(winners) != 1:
        return None
    return winners[0]


__all__ = (
    "CRAFTING_LEVEL_THRESHOLDS",
    "ComponentMoveModifierSpec",
    "DISMANTLE_SPECS",
    "DismantleSpec",
    "IMPROVEMENT_RECIPE_SPECS",
    "IMPROVEMENT_ROLL_WEIGHT_BANDS",
    "MATERIAL_SPECS",
    "MaterialSpec",
    "MAX_CRAFTING_EXPERIENCE",
    "MYSTICAL_IDENTITIES",
    "MYSTICAL_IDENTITY_THRESHOLD",
    "PHYSICAL_IDENTITIES",
    "PHYSICAL_IDENTITY_THRESHOLD",
    "QUALITY_GATES",
    "SLOT_MATERIAL_FAMILIES",
    "SALVAGE_DOUBLE_YIELD_CHANCE_BANDS",
    "WeaponProgressionSpec",
    "WeaponImprovementRecipeSpec",
    "WeaponComponentSpec",
    "WeaponSlotSpec",
    "derive_weapon_identities",
    "crafting_level_for_experience",
    "get_dismantle_spec",
    "get_improvement_recipe",
    "get_material_spec",
    "improvement_roll",
    "get_weapon_component_spec",
    "project_component_move_effects",
    "salvage_double_yield_chance",
)

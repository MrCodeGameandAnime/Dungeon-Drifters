"""Authored armor rarities, modifiers, and floor generation policy."""

from dataclasses import dataclass

from app.combat.move import DamageDefenseClass
from app.combat.passive_effect import PassiveCombatEffect, PassiveEffectKind
from app.content.equipment_spec import (
    ACCESSORY_SLOTS,
    ARMOR_SLOTS,
    EQUIPMENT_TEMPLATES,
    EquipmentTemplateSpec,
)
from app.content.route_spec import validate_content_id


MODIFIER_GRADES = ("I", "II", "III", "IV", "V")


@dataclass(frozen=True)
class ArmorRaritySpec:
    rarity_id: str
    name: str
    modifier_capacity: int

    def __post_init__(self):
        try:
            validate_content_id("rarity ID", self.rarity_id)
        except (TypeError, ValueError) as error:
            raise ValueError("rarity ID is invalid") from error
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("rarity name must be non-empty")
        if isinstance(self.modifier_capacity, bool) or not isinstance(
            self.modifier_capacity, int
        ):
            raise TypeError("rarity modifier capacity must be an integer")
        if not 1 <= self.modifier_capacity <= len(MODIFIER_GRADES):
            raise ValueError("rarity modifier capacity must be between one and five")

    @property
    def modifier_grades(self):
        return MODIFIER_GRADES[: self.modifier_capacity]


@dataclass(frozen=True)
class ArmorModifierSpec:
    modifier_id: str
    name: str
    grade: str
    compatible_slots: tuple[str, ...]
    effects: tuple[PassiveCombatEffect, ...]
    extraction_gold_cost: int = 0
    extraction_material_costs: tuple[tuple[str, int], ...] = ()
    affix_gold_cost: int = 0
    affix_material_costs: tuple[tuple[str, int], ...] = ()

    def __post_init__(self):
        try:
            validate_content_id("modifier ID", self.modifier_id)
        except (TypeError, ValueError) as error:
            raise ValueError("modifier ID is invalid") from error
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("modifier name must be non-empty")
        if self.grade not in MODIFIER_GRADES:
            raise ValueError("modifier grade is invalid")
        if not isinstance(self.compatible_slots, tuple) or not self.compatible_slots:
            raise ValueError("modifier requires compatible armor slots")
        if any(slot not in ARMOR_SLOTS for slot in self.compatible_slots):
            raise ValueError("modifier compatibility requires a compatible armor slot")
        if len(set(self.compatible_slots)) != len(self.compatible_slots):
            raise ValueError("modifier compatible slots must be unique")
        if not isinstance(self.effects, tuple) or not self.effects:
            raise ValueError("modifier requires at least one combat effect")
        if any(not isinstance(effect, PassiveCombatEffect) for effect in self.effects):
            raise TypeError("modifier effects must use existing passive combat effects")
        _validate_modifier_costs(self)


@dataclass(frozen=True)
class FloorRarityPolicySpec:
    floor: int
    rarity_weights_bps: tuple[tuple[str, int], ...]
    modifier_chance_percent: int

    def __post_init__(self):
        if isinstance(self.floor, bool) or not isinstance(self.floor, int):
            raise TypeError("floor must be an integer")
        if not 1 <= self.floor <= 10:
            raise ValueError("floor must be between one and ten")
        if not isinstance(self.rarity_weights_bps, tuple) or not self.rarity_weights_bps:
            raise TypeError("rarity weights must be a non-empty tuple")
        seen = set()
        total = 0
        for entry in self.rarity_weights_bps:
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise TypeError("rarity weights must be (rarity_id, weight) pairs")
            rarity_id, weight = entry
            try:
                validate_content_id("rarity weight ID", rarity_id)
            except (TypeError, ValueError) as error:
                raise ValueError("rarity weight ID is invalid") from error
            if rarity_id in seen:
                raise ValueError("rarity weight IDs must be unique")
            if isinstance(weight, bool) or not isinstance(weight, int):
                raise TypeError("rarity weight must be an integer")
            if weight < 0:
                raise ValueError("rarity weight must not be negative")
            seen.add(rarity_id)
            total += weight
        if total != 10000:
            raise ValueError("rarity weights must sum to 10000")
        if isinstance(self.modifier_chance_percent, bool) or not isinstance(
            self.modifier_chance_percent, int
        ):
            raise TypeError("modifier chance must be an integer")
        if not 0 <= self.modifier_chance_percent <= 100:
            raise ValueError("modifier chance must be between zero and 100")


def _validate_modifier_costs(spec):
    for field in ("extraction_gold_cost", "affix_gold_cost"):
        value = getattr(spec, field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("modifier gold costs must be non-negative integers")
    from app.content.weapon_progression_spec import get_material_spec

    for field in ("extraction_material_costs", "affix_material_costs"):
        costs = getattr(spec, field)
        if not isinstance(costs, tuple):
            raise TypeError("modifier material costs must be tuples")
        seen = set()
        for entry in costs:
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise ValueError("modifier costs must be material/quantity pairs")
            material_id, quantity = entry
            if get_material_spec(material_id) is None:
                raise ValueError("modifier costs reference unknown materials")
            if material_id in seen:
                raise ValueError("modifier material costs must be unique")
            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
                raise ValueError("modifier material quantities must be positive")
            seen.add(material_id)


ARMOR_RARITIES = (
    ArmorRaritySpec("common", "Common", 1),
    ArmorRaritySpec("uncommon", "Uncommon", 2),
    ArmorRaritySpec("rare", "Rare", 3),
    ArmorRaritySpec("epic", "Epic", 4),
    ArmorRaritySpec("legendary", "Legendary", 5),
)

MODIFIER_DEFINITIONS = (
    ArmorModifierSpec(
        "bastion_grade_i",
        "Bastion",
        "I",
        ARMOR_SLOTS,
        (PassiveCombatEffect(PassiveEffectKind.MITIGATION, 1, DamageDefenseClass.PHYSICAL),),
        5, (("grade_i_cores", 1),), 3, (("grade_i_cores", 1),),
    ),
    ArmorModifierSpec(
        "vanguard_grade_i",
        "Vanguard",
        "I",
        ARMOR_SLOTS,
        (PassiveCombatEffect(PassiveEffectKind.DAMAGE_OUTPUT, 1, DamageDefenseClass.PHYSICAL),),
        5, (("grade_i_cores", 1),), 3, (("grade_i_cores", 1),),
    ),
    ArmorModifierSpec(
        "ward_grade_ii",
        "Ward",
        "II",
        ARMOR_SLOTS,
        (PassiveCombatEffect(PassiveEffectKind.MITIGATION, 1, DamageDefenseClass.MAGICAL),),
        10, (("grade_ii_cores", 1),), 6, (("grade_ii_cores", 1),),
    ),
    ArmorModifierSpec(
        "force_grade_iii",
        "Force",
        "III",
        ARMOR_SLOTS,
        (PassiveCombatEffect(PassiveEffectKind.DAMAGE_OUTPUT, 1, DamageDefenseClass.PHYSICAL),),
        15, (("grade_iii_cores", 1),), 9, (("grade_iii_cores", 1),),
    ),
    ArmorModifierSpec(
        "focus_grade_iv",
        "Focus",
        "IV",
        ARMOR_SLOTS,
        (PassiveCombatEffect(PassiveEffectKind.MANA_COST, 1),),
        20, (("grade_iv_cores", 1),), 12, (("grade_iv_cores", 1),),
    ),
    ArmorModifierSpec(
        "resolve_grade_v",
        "Resolve",
        "V",
        ARMOR_SLOTS,
        (PassiveCombatEffect(PassiveEffectKind.SUPER_GAIN, 1),),
        25, (("grade_iv_cores", 1),), 15, (("grade_iv_cores", 1),),
    ),
)

_FLOOR_WEIGHTS = (
    (("common", 10000),),
    (("common", 9600), ("uncommon", 400)),
    (("common", 9300), ("uncommon", 700)),
    (("common", 8800), ("uncommon", 1100), ("rare", 100)),
    (("common", 8200), ("uncommon", 1500), ("rare", 300)),
    (("common", 7600), ("uncommon", 1800), ("rare", 550), ("epic", 50)),
    (("common", 7000), ("uncommon", 2100), ("rare", 800), ("epic", 100)),
    (("common", 6500), ("uncommon", 2200), ("rare", 1100), ("epic", 190), ("legendary", 10)),
    (("common", 6000), ("uncommon", 2300), ("rare", 1300), ("epic", 350), ("legendary", 50)),
    (("common", 5500), ("uncommon", 2300), ("rare", 1400), ("epic", 700), ("legendary", 100)),
)
FLOOR_RARITY_POLICIES = tuple(
    FloorRarityPolicySpec(floor, weights, 35 + floor)
    for floor, weights in enumerate(_FLOOR_WEIGHTS, start=1)
)


def validate_armor_content(*, templates, rarities, modifiers, policies):
    templates = tuple(templates)
    rarities = tuple(rarities)
    modifiers = tuple(modifiers)
    policies = tuple(policies)
    if any(not isinstance(item, EquipmentTemplateSpec) for item in templates):
        raise TypeError("armor templates must use EquipmentTemplateSpec")
    armor_templates = tuple(item for item in templates if item.is_armor)
    if {item.slot_id for item in armor_templates} != set(ARMOR_SLOTS):
        raise ValueError("armor templates must cover every armor slot")
    accessory_templates = tuple(item for item in templates if item.is_static_accessory)
    if {item.slot_id for item in accessory_templates} != set(ACCESSORY_SLOTS):
        raise ValueError("fixed accessories must cover Ring and Pendant slots")
    _require_unique("armor template", (item.definition_id for item in templates))

    if any(not isinstance(item, ArmorRaritySpec) for item in rarities):
        raise TypeError("rarities must use ArmorRaritySpec")
    _require_unique("rarity", (item.rarity_id for item in rarities))
    if tuple(item.modifier_capacity for item in rarities) != (1, 2, 3, 4, 5):
        raise ValueError("rarity capacities must progress from one through five")
    rarity_ids = {item.rarity_id for item in rarities}

    if any(not isinstance(item, ArmorModifierSpec) for item in modifiers):
        raise TypeError("modifiers must use ArmorModifierSpec")
    _require_unique("modifier", (item.modifier_id for item in modifiers))
    if {item.grade for item in modifiers} != set(MODIFIER_GRADES):
        raise ValueError("armor modifier catalog must cover every grade")
    for grade in MODIFIER_GRADES:
        for slot in ARMOR_SLOTS:
            if not any(
                modifier.grade == grade and slot in modifier.compatible_slots
                for modifier in modifiers
            ):
                raise ValueError("every modifier grade needs a pool for each armor slot")
    if any(not isinstance(item, FloorRarityPolicySpec) for item in policies):
        raise TypeError("policies must use FloorRarityPolicySpec")
    _require_unique("floor policy", (str(item.floor) for item in policies))
    by_floor = {item.floor: item for item in policies}
    if set(by_floor) != set(range(1, 11)):
        raise ValueError("rarity policy must define floors one through ten")
    highest_capacity = 0
    legendary_first_floor = None
    for floor in range(1, 11):
        policy = by_floor[floor]
        weights = dict(policy.rarity_weights_bps)
        if any(rarity_id not in rarity_ids for rarity_id in weights):
            raise ValueError("floor rarity policy references an unknown rarity")
        available = max(
            (rarity.modifier_capacity for rarity in rarities if weights.get(rarity.rarity_id, 0)),
            default=0,
        )
        if available < highest_capacity:
            raise ValueError("floor rarity eligibility cannot move backward")
        highest_capacity = available
        if weights.get("legendary", 0) and legendary_first_floor is None:
            legendary_first_floor = floor
    if dict(by_floor[1].rarity_weights_bps).get("legendary", 0):
        raise ValueError("legendary must be unavailable on the opening floor")
    if legendary_first_floor is None or dict(by_floor[10].rarity_weights_bps).get("legendary", 0) <= 0:
        raise ValueError("legendary must be a possible final-floor reward")
    return templates, rarities, modifiers, policies


def get_armor_rarity(rarity_id):
    for rarity in ARMOR_RARITIES:
        if rarity.rarity_id == rarity_id:
            return rarity
    raise ValueError(f"unknown armor rarity: {rarity_id!r}")


def get_armor_modifier(modifier_id):
    for modifier in MODIFIER_DEFINITIONS:
        if modifier.modifier_id == modifier_id:
            return modifier
    raise ValueError(f"unknown armor modifier: {modifier_id!r}")


def get_floor_rarity_policy(floor):
    for policy in FLOOR_RARITY_POLICIES:
        if policy.floor == floor:
            return policy
    raise ValueError(f"no armor rarity policy for floor {floor!r}")


def _require_unique(name, values):
    values = tuple(values)
    if len(values) != len(set(values)):
        raise ValueError(f"{name} IDs must be unique")


validate_armor_content(
    templates=EQUIPMENT_TEMPLATES,
    rarities=ARMOR_RARITIES,
    modifiers=MODIFIER_DEFINITIONS,
    policies=FLOOR_RARITY_POLICIES,
)


__all__ = [
    "ARMOR_RARITIES",
    "FLOOR_RARITY_POLICIES",
    "MODIFIER_DEFINITIONS",
    "MODIFIER_GRADES",
    "ArmorModifierSpec",
    "ArmorRaritySpec",
    "FloorRarityPolicySpec",
    "get_armor_modifier",
    "get_armor_rarity",
    "get_floor_rarity_policy",
    "validate_armor_content",
]

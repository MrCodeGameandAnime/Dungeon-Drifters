"""Authored armor and fixed-accessory definitions."""

from dataclasses import dataclass

from app.content.route_spec import validate_content_id


EQUIPMENT_SLOTS = ("helm", "chest", "gloves", "boots", "ring", "pendant")
ARMOR_SLOTS = ("helm", "chest", "gloves", "boots")
ACCESSORY_SLOTS = ("ring", "pendant")
ARMOR_FAMILIES = ("light", "heavy", "arcane")
STAT_NAMES = (
    "constitution",
    "spirit",
    "intelligence",
    "strength",
    "dexterity",
    "intuition",
)
MAX_ARMOR_UPGRADE_RANK = 4


@dataclass(frozen=True)
class EquipmentTemplateSpec:
    definition_id: str
    name: str
    category: str
    slot_id: str
    stat_ranges: tuple[tuple[str, int, int], ...]
    family: str | None = None
    material_id: str | None = None
    upgrade_stat_bonuses: tuple[tuple[str, int], ...] = ()
    sale_value_gold: int | None = None
    dismantle_yields: tuple[tuple[str, int], ...] = ()

    def __post_init__(self):
        _validate_template(self)

    @property
    def is_static_accessory(self):
        return self.category == "accessory"

    @property
    def is_armor(self):
        return self.category == "armor"


def validate_equipment_templates(specs):
    if not isinstance(specs, (tuple, list)):
        raise TypeError("equipment templates must be a sequence")
    values = tuple(specs)
    if any(not isinstance(spec, EquipmentTemplateSpec) for spec in values):
        raise TypeError("equipment templates must contain EquipmentTemplateSpec values")
    ids = tuple(spec.definition_id for spec in values)
    if len(ids) != len(set(ids)):
        raise ValueError("equipment template IDs must be unique")
    return values


def _validate_template(spec):
    from app.content.weapon_progression_spec import get_material_spec

    try:
        validate_content_id("equipment definition ID", spec.definition_id)
    except (TypeError, ValueError) as error:
        raise ValueError("equipment definition ID is invalid") from error
    if not isinstance(spec.name, str) or not spec.name.strip():
        raise ValueError("equipment name must be a non-empty string")
    if spec.category not in {"armor", "accessory"}:
        raise ValueError("equipment category must be armor or accessory")
    if spec.slot_id not in EQUIPMENT_SLOTS:
        raise ValueError("equipment slot is invalid")
    if (spec.category == "armor") != (spec.slot_id in ARMOR_SLOTS):
        raise ValueError("equipment category does not match its slot")
    if spec.category == "armor":
        if spec.family not in ARMOR_FAMILIES:
            raise ValueError("armor template family is invalid")
        try:
            validate_content_id("armor material ID", spec.material_id)
        except (TypeError, ValueError) as error:
            raise ValueError("armor template material ID is invalid") from error
        try:
            get_material_spec(spec.material_id)
        except ValueError as error:
            raise ValueError("armor template references an unknown material") from error
    elif spec.family is not None or spec.material_id is not None:
        raise ValueError("static accessory cannot define an armor family or material")
    if not isinstance(spec.upgrade_stat_bonuses, tuple):
        raise TypeError("equipment upgrade stat bonuses must be a tuple")
    upgrade_stats = set()
    for entry in spec.upgrade_stat_bonuses:
        if not isinstance(entry, tuple) or len(entry) != 2:
            raise ValueError("equipment upgrade bonuses must contain stat/value pairs")
        name, value = entry
        if name not in STAT_NAMES or name in upgrade_stats:
            raise ValueError("equipment upgrade bonus has an invalid or duplicate stat")
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError("equipment upgrade stat bonus must be a positive integer")
        upgrade_stats.add(name)
    if spec.category == "accessory" and spec.upgrade_stat_bonuses:
        raise ValueError("static accessories cannot define armor upgrade bonuses")
    if spec.category == "armor" and not spec.upgrade_stat_bonuses:
        raise ValueError("armor template must define an upgrade stat bonus")
    if spec.sale_value_gold is not None and (
        isinstance(spec.sale_value_gold, bool)
        or not isinstance(spec.sale_value_gold, int)
        or spec.sale_value_gold < 0
    ):
        raise ValueError("equipment sale value must be a non-negative integer")
    if not isinstance(spec.dismantle_yields, tuple):
        raise TypeError("equipment dismantle yields must be a tuple")
    yielded_materials = set()
    for entry in spec.dismantle_yields:
        if not isinstance(entry, tuple) or len(entry) != 2:
            raise ValueError("dismantle yields must contain material/quantity pairs")
        material_id, quantity = entry
        try:
            validate_content_id("dismantle material ID", material_id)
        except (TypeError, ValueError) as error:
            raise ValueError("dismantle material ID is invalid") from error
        try:
            get_material_spec(material_id)
        except ValueError as error:
            raise ValueError("unknown dismantle material") from error
        if material_id in yielded_materials:
            raise ValueError("dismantle material IDs must be unique")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            raise ValueError("dismantle material quantity must be positive")
        yielded_materials.add(material_id)
    if spec.category == "accessory" and (
        spec.sale_value_gold is not None or spec.dismantle_yields
    ):
        raise ValueError("fixed accessories require explicit disposal authorization")
    if not isinstance(spec.stat_ranges, tuple):
        raise TypeError("equipment stat ranges must be a tuple")
    names = []
    for entry in spec.stat_ranges:
        if not isinstance(entry, tuple) or len(entry) != 3:
            raise ValueError("equipment stat ranges must contain stat/min/max tuples")
        name, minimum, maximum = entry
        if name not in STAT_NAMES or name in names:
            raise ValueError("equipment stat range has an invalid or duplicate stat")
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (minimum, maximum)):
            raise TypeError("equipment stat bounds must be integers")
        if minimum > maximum:
            raise ValueError("equipment stat range minimum exceeds maximum")
        names.append(name)


EQUIPMENT_TEMPLATES = validate_equipment_templates(
    (
        EquipmentTemplateSpec(
            "field_helm", "Field Helm", "armor", "helm",
            (("constitution", 1, 3),), "heavy", "grade_i_metal",
            (("constitution", 1),), 6, (("grade_i_metal", 1),),
        ),
        EquipmentTemplateSpec(
            "field_chest", "Field Chest", "armor", "chest",
            (("constitution", 1, 4), ("spirit", 0, 2)),
            "heavy", "grade_i_metal", (("constitution", 1),),
            10, (("grade_i_metal", 2),),
        ),
        EquipmentTemplateSpec(
            "field_gloves", "Field Gloves", "armor", "gloves",
            (("strength", 1, 3), ("dexterity", 0, 1)),
            "light", "grade_i_fiber", (("strength", 1),),
            6, (("grade_i_fiber", 1),),
        ),
        EquipmentTemplateSpec(
            "field_boots", "Field Boots", "armor", "boots",
            (("dexterity", 1, 3), ("intuition", 0, 1)),
            "light", "grade_i_fiber", (("dexterity", 1),),
            6, (("grade_i_fiber", 1),),
        ),
        EquipmentTemplateSpec(
            "iron_ring", "Iron Ring", "accessory", "ring", (("intuition", 1, 1),)
        ),
        EquipmentTemplateSpec(
            "wayfinder_pendant",
            "Wayfinder Pendant",
            "accessory",
            "pendant",
            (("spirit", 1, 1),),
        ),
    )
)
_TEMPLATES_BY_ID = {spec.definition_id: spec for spec in EQUIPMENT_TEMPLATES}


def get_equipment_template(definition_id):
    if not isinstance(definition_id, str) or not definition_id:
        raise ValueError("equipment definition ID must be a non-empty string")
    try:
        return _TEMPLATES_BY_ID[definition_id]
    except KeyError as error:
        raise ValueError(f"unknown equipment definition: {definition_id}") from error


__all__ = [
    "ACCESSORY_SLOTS",
    "ARMOR_FAMILIES",
    "ARMOR_SLOTS",
    "EQUIPMENT_SLOTS",
    "EQUIPMENT_TEMPLATES",
    "MAX_ARMOR_UPGRADE_RANK",
    "EquipmentTemplateSpec",
    "get_equipment_template",
    "validate_equipment_templates",
]

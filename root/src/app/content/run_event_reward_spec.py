"""Authored fixed rewards that resolve at a run-event boundary."""

from dataclasses import dataclass

from app.content.equipment_spec import get_equipment_template
from app.content.route_spec import validate_content_id


_SUPPORTED_RUN_FLOORS = {"floor_two": 2, "floor_four": 4}


@dataclass(frozen=True)
class ArmorRewardSourceSpec:
    source_id: str
    floor_id: str
    node_id: str
    floor: int
    template_id: str

    def __post_init__(self):
        validate_content_id("armor reward source ID", self.source_id)
        validate_content_id("armor reward floor ID", self.floor_id)
        validate_content_id("armor reward node ID", self.node_id)
        validate_content_id("armor reward template ID", self.template_id)
        if _SUPPORTED_RUN_FLOORS.get(self.floor_id) != self.floor:
            raise ValueError("armor reward floor does not match its floor ID")
        if not get_equipment_template(self.template_id).is_armor:
            raise ValueError("armor reward source must reference armor")


@dataclass(frozen=True)
class FixedItemRewardSourceSpec:
    source_id: str
    floor_id: str
    node_id: str
    item_id: str
    quantity: int

    def __post_init__(self):
        for name in ("source_id", "floor_id", "node_id", "item_id"):
            validate_content_id(f"fixed item reward {name}", getattr(self, name))
        if self.floor_id not in _SUPPORTED_RUN_FLOORS:
            raise ValueError("fixed item reward floor is unsupported")
        if isinstance(self.quantity, bool) or not isinstance(self.quantity, int):
            raise TypeError("fixed item reward quantity must be an integer")
        if self.quantity < 1:
            raise ValueError("fixed item reward quantity must be positive")


M8_FLOOR_FOUR_ARMOR_REWARD = ArmorRewardSourceSpec(
    source_id="m8_floor_four_armor_source",
    floor_id="floor_four",
    node_id="floor_four_battle_08",
    floor=4,
    template_id="field_chest",
)

M8_FLOOR_FOUR_RECOVERY_REWARD = FixedItemRewardSourceSpec(
    source_id="m8_floor_four_recovery_source",
    floor_id="floor_four",
    node_id="floor_four_battle_08",
    item_id="healing_potion",
    quantity=1,
)


__all__ = [
    "ArmorRewardSourceSpec",
    "FixedItemRewardSourceSpec",
    "M8_FLOOR_FOUR_ARMOR_REWARD",
    "M8_FLOOR_FOUR_RECOVERY_REWARD",
]

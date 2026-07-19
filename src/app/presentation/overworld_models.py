"""Immutable renderer-neutral models for overworld presentation."""

from dataclasses import dataclass
from enum import StrEnum


class OverworldScreen(StrEnum):
    MAIN = "main"
    CHARACTER = "character"
    SKILLS = "skills"
    WEAPON = "weapon"
    EQUIPMENT = "equipment"
    ITEMS = "items"
    ITEM_INSPECT = "item_inspect"
    MAP = "map"
    OPTIONS = "options"
    QUIT_CONFIRMATION = "quit_confirmation"


class OverworldAction(StrEnum):
    CHARACTER = "character"
    ITEMS = "items"
    MAP = "map"
    OPTIONS = "options"
    SKILLS = "skills"
    WEAPON = "weapon"
    EQUIPMENT = "equipment"
    CRAFT = "craft"
    INSPECT = "inspect"
    USE = "use"
    SAVE = "save"
    LOAD = "load"
    QUIT = "quit"
    BACK = "back"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    ENTER_ENCOUNTER = "enter_encounter"
    RETRY = "retry"


class OverworldAvailabilityReason(StrEnum):
    GROWTH_UNAVAILABLE = "growth_unavailable"
    CRAFT_UNAVAILABLE = "craft_unavailable"
    NO_ITEM_SELECTED = "no_item_selected"
    NO_OVERWORLD_USE = "no_overworld_use"
    ENCOUNTER_INSPECTION_UNAVAILABLE = "encounter_inspection_unavailable"
    SAVE_UNAVAILABLE = "save_unavailable"
    LOAD_UNAVAILABLE = "load_unavailable"


class MapNodeState(StrEnum):
    CURRENT = "current"
    COMPLETED = "completed"
    REMAINING = "remaining"


@dataclass(frozen=True)
class OverworldOptionView:
    action: OverworldAction
    label: str
    enabled: bool
    disabled_reason: OverworldAvailabilityReason | None = None

    def __post_init__(self):
        object.__setattr__(self, "action", OverworldAction(self.action))
        _validate_text("label", self.label)
        _validate_bool("enabled", self.enabled)
        if self.disabled_reason is not None:
            object.__setattr__(
                self,
                "disabled_reason",
                OverworldAvailabilityReason(self.disabled_reason),
            )
        if self.enabled == (self.disabled_reason is not None):
            raise ValueError("option availability and disabled reason disagree")


@dataclass(frozen=True)
class StatRowView:
    label: str
    value: int
    increase_visible: bool = False
    increase_enabled: bool = False
    disabled_reason: OverworldAvailabilityReason | None = None

    def __post_init__(self):
        _validate_text("label", self.label)
        _validate_nonnegative("value", self.value)
        _validate_bool("increase_visible", self.increase_visible)
        _validate_bool("increase_enabled", self.increase_enabled)
        if self.disabled_reason is not None:
            object.__setattr__(
                self,
                "disabled_reason",
                OverworldAvailabilityReason(self.disabled_reason),
            )
        if not self.increase_visible and (
            self.increase_enabled or self.disabled_reason is not None
        ):
            raise ValueError("hidden stat controls cannot have availability")
        if self.increase_visible and self.increase_enabled == (
            self.disabled_reason is not None
        ):
            raise ValueError("stat availability and disabled reason disagree")


@dataclass(frozen=True)
class CharacterOverviewView:
    display_name: str
    archetype_label: str
    stats: tuple[StatRowView, ...]
    level: int
    exp_current: int
    exp_threshold: int
    exp_fill_bps: int
    hp_current: int
    hp_maximum: int
    mana_current: int
    mana_maximum: int
    super_current: int
    super_maximum: int

    def __post_init__(self):
        _validate_text("display_name", self.display_name)
        _validate_text("archetype_label", self.archetype_label)
        _validate_instance_tuple("stats", self.stats, StatRowView)
        for name in (
            "level",
            "exp_current",
            "exp_threshold",
            "exp_fill_bps",
            "hp_current",
            "hp_maximum",
            "mana_current",
            "mana_maximum",
            "super_current",
            "super_maximum",
        ):
            _validate_nonnegative(name, getattr(self, name))
        if not 0 <= self.exp_fill_bps <= 10_000:
            raise ValueError("exp_fill_bps must be between 0 and 10000")


@dataclass(frozen=True)
class SkillMoveView:
    name: str
    description: str

    def __post_init__(self):
        _validate_text("name", self.name)
        _validate_text("description", self.description)


@dataclass(frozen=True)
class SkillsView:
    growth_points_available: int | None
    growth_message: str
    stats: tuple[StatRowView, ...]
    moves: tuple[SkillMoveView, ...]

    def __post_init__(self):
        if self.growth_points_available is not None:
            _validate_nonnegative(
                "growth_points_available",
                self.growth_points_available,
            )
        _validate_text("growth_message", self.growth_message)
        _validate_instance_tuple("stats", self.stats, StatRowView)
        _validate_instance_tuple("moves", self.moves, SkillMoveView)


@dataclass(frozen=True)
class StatBonusView:
    label: str
    amount: int

    def __post_init__(self):
        _validate_text("label", self.label)
        _validate_nonnegative("amount", self.amount)


@dataclass(frozen=True)
class WeaponView:
    name: str
    weapon_type: str
    intended_wielder: str
    bonuses: tuple[StatBonusView, ...]
    description: str

    def __post_init__(self):
        for name in ("name", "weapon_type", "intended_wielder", "description"):
            _validate_text(name, getattr(self, name))
        _validate_instance_tuple("bonuses", self.bonuses, StatBonusView)


@dataclass(frozen=True)
class AccessorySlotView:
    label: str
    item_name: str

    def __post_init__(self):
        _validate_text("label", self.label)
        _validate_text("item_name", self.item_name)


@dataclass(frozen=True)
class EquipmentView:
    necklace: AccessorySlotView
    ring: AccessorySlotView
    benefits: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.necklace, AccessorySlotView):
            raise TypeError("necklace must be an AccessorySlotView")
        if not isinstance(self.ring, AccessorySlotView):
            raise TypeError("ring must be an AccessorySlotView")
        _validate_text_tuple("benefits", self.benefits)


@dataclass(frozen=True)
class OverworldItemView:
    selection_key: str
    display_name: str
    quantity: int
    description: str
    overworld_use_enabled: bool = False

    def __post_init__(self):
        for name in ("selection_key", "display_name", "description"):
            _validate_text(name, getattr(self, name))
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        _validate_bool("overworld_use_enabled", self.overworld_use_enabled)


@dataclass(frozen=True)
class InventoryView:
    items: tuple[OverworldItemView, ...]
    selected_item_key: str | None = None
    inspected_item: OverworldItemView | None = None

    def __post_init__(self):
        _validate_instance_tuple("items", self.items, OverworldItemView)
        if self.selected_item_key is not None:
            _validate_text("selected_item_key", self.selected_item_key)
        if self.inspected_item is not None and not isinstance(
            self.inspected_item,
            OverworldItemView,
        ):
            raise TypeError("inspected_item must be an OverworldItemView")


@dataclass(frozen=True)
class MapNodeView:
    display_label: str
    kind_label: str
    state: MapNodeState

    def __post_init__(self):
        _validate_text("display_label", self.display_label)
        _validate_text("kind_label", self.kind_label)
        object.__setattr__(self, "state", MapNodeState(self.state))


@dataclass(frozen=True)
class MapView:
    nodes: tuple[MapNodeView, ...]

    def __post_init__(self):
        _validate_instance_tuple("nodes", self.nodes, MapNodeView)


@dataclass(frozen=True)
class OverworldView:
    screen: OverworldScreen
    location_label: str
    adventure_text: str
    options: tuple[OverworldOptionView, ...]
    contextual_route_option: OverworldOptionView | None = None
    notice: str | None = None
    character: CharacterOverviewView | None = None
    skills: SkillsView | None = None
    weapon: WeaponView | None = None
    equipment: EquipmentView | None = None
    inventory: InventoryView | None = None
    route_map: MapView | None = None

    def __post_init__(self):
        object.__setattr__(self, "screen", OverworldScreen(self.screen))
        _validate_text("location_label", self.location_label)
        _validate_text("adventure_text", self.adventure_text)
        _validate_instance_tuple("options", self.options, OverworldOptionView)
        if any(
            option.action in {
                OverworldAction.ENTER_ENCOUNTER,
                OverworldAction.RETRY,
            }
            for option in self.options
        ):
            raise ValueError(
                "contextual route actions must not be stored in options"
            )
        if self.contextual_route_option is not None:
            if not isinstance(self.contextual_route_option, OverworldOptionView):
                raise TypeError(
                    "contextual_route_option must be an OverworldOptionView"
                )
            if self.screen is not OverworldScreen.MAIN:
                raise ValueError(
                    "contextual_route_option is valid only on the Main screen"
                )
            if self.contextual_route_option.action not in {
                OverworldAction.ENTER_ENCOUNTER,
                OverworldAction.RETRY,
            }:
                raise ValueError("invalid contextual route action")
        if self.notice is not None:
            _validate_text("notice", self.notice)
        for name, expected_type in (
            ("character", CharacterOverviewView),
            ("skills", SkillsView),
            ("weapon", WeaponView),
            ("equipment", EquipmentView),
            ("inventory", InventoryView),
            ("route_map", MapView),
        ):
            value = getattr(self, name)
            if value is not None and not isinstance(value, expected_type):
                raise TypeError(f"{name} must be {expected_type.__name__}")


def _validate_text(name, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")


def _validate_bool(name, value):
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a boolean")


def _validate_nonnegative(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must not be negative")


def _validate_instance_tuple(name, values, expected_type):
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple")
    if not all(isinstance(value, expected_type) for value in values):
        raise TypeError(f"{name} must contain {expected_type.__name__} values")


def _validate_text_tuple(name, values):
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple")
    for value in values:
        _validate_text(name, value)

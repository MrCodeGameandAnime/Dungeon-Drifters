"""Immutable renderer-neutral models for overworld presentation."""

from dataclasses import dataclass
from enum import StrEnum


class OverworldScreen(StrEnum):
    MAIN = "main"
    HUB = "hub"
    FLOOR_ONE_WARNING = "floor_one_warning"
    COMPANION_SELECTION = "companion_selection"
    PARTY_READY = "party_ready"
    OUTING = "outing"
    EXTRACTION = "extraction"
    CHARACTER = "character"
    SKILLS = "skills"
    WEAPON = "weapon"
    EQUIPMENT = "equipment"
    MERCHANT = "merchant"
    ITEMS = "items"
    ITEM_INSPECT = "item_inspect"
    MAP = "map"
    MAP_INSPECT = "map_inspect"
    OPTIONS = "options"
    QUIT_CONFIRMATION = "quit_confirmation"
    LOAD_CONFIRMATION = "load_confirmation"
    REST = "rest"


class OverworldAction(StrEnum):
    CHARACTER = "character"
    ITEMS = "items"
    MAP = "map"
    OPTIONS = "options"
    SKILLS = "skills"
    WEAPON = "weapon"
    EQUIPMENT = "equipment"
    MERCHANT = "merchant"
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
    REST = "rest"
    SKIP_REST = "skip_rest"
    MENU = "menu"
    RECRUIT_COMPANION = "recruit_companion"
    READY = "ready"
    RETURN_TO_HUB = "return_to_hub"
    START_FLOOR_ONE = "start_floor_one"
    SET_OUT = "set_out"
    EXTRACT = "extract"


class OverworldAvailabilityReason(StrEnum):
    GROWTH_UNAVAILABLE = "growth_unavailable"
    NO_GROWTH_POINTS = "no_growth_points"
    STAT_AT_MAXIMUM = "stat_at_maximum"
    CRAFT_UNAVAILABLE = "craft_unavailable"
    NO_ITEM_SELECTED = "no_item_selected"
    NO_OVERWORLD_USE = "no_overworld_use"
    ENCOUNTER_INSPECTION_UNAVAILABLE = "encounter_inspection_unavailable"
    SAVE_UNAVAILABLE = "save_unavailable"
    LOAD_UNAVAILABLE = "load_unavailable"
    INSUFFICIENT_SHARED_GOLD = "insufficient_shared_gold"


@dataclass(frozen=True)
class CompanionChoiceView:
    drifter_id: str
    display_name: str
    archetype_label: str
    summary: str
    cost: int
    enabled: bool
    disabled_reason: OverworldAvailabilityReason | None = None

    def __post_init__(self):
        for name in ("drifter_id", "display_name", "archetype_label", "summary"):
            _validate_text(name, getattr(self, name))
        _validate_nonnegative("cost", self.cost)
        _validate_bool("enabled", self.enabled)
        if self.disabled_reason is not None:
            object.__setattr__(
                self,
                "disabled_reason",
                OverworldAvailabilityReason(self.disabled_reason),
            )
        if self.enabled == (self.disabled_reason is not None):
            raise ValueError("companion availability and disabled reason disagree")


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
    stat_name: str
    label: str
    value: int
    increase_visible: bool = False
    increase_enabled: bool = False
    disabled_reason: OverworldAvailabilityReason | None = None

    def __post_init__(self):
        _validate_text("stat_name", self.stat_name)
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
    exp_threshold: int | None
    exp_fill_bps: int
    hp_current: int
    hp_maximum: int
    mana_current: int
    mana_maximum: int
    super_current: int
    super_maximum: int
    targets: tuple = ()
    selected_target_id: str | None = None

    def __post_init__(self):
        _validate_text("display_name", self.display_name)
        _validate_text("archetype_label", self.archetype_label)
        _validate_instance_tuple("stats", self.stats, StatRowView)
        _validate_instance_tuple("targets", self.targets, MerchantTargetView)
        if self.targets:
            _validate_selected_target(self.targets, self.selected_target_id)
        for name in (
            "level",
            "exp_current",
            "exp_fill_bps",
            "hp_current",
            "hp_maximum",
            "mana_current",
            "mana_maximum",
            "super_current",
            "super_maximum",
        ):
            _validate_nonnegative(name, getattr(self, name))
        if self.exp_threshold is not None:
            _validate_nonnegative("exp_threshold", self.exp_threshold)
        if not 0 <= self.exp_fill_bps <= 10_000:
            raise ValueError("exp_fill_bps must be between 0 and 10000")


@dataclass(frozen=True)
class SkillMoveView:
    name: str
    description: str
    power: int | None = None
    accuracy: int | None = None
    resource_type: str | None = None
    resource_cost: int | None = None
    damage_type: str | None = None

    def __post_init__(self):
        _validate_text("name", self.name)
        _validate_text("description", self.description)
        for name in ("power", "accuracy", "resource_cost"):
            value = getattr(self, name)
            if value is not None:
                _validate_nonnegative(name, value)
        for name in ("resource_type", "damage_type"):
            value = getattr(self, name)
            if value is not None:
                _validate_text(name, value)


@dataclass(frozen=True)
class SkillsView:
    growth_points_available: int | None
    growth_message: str
    stats: tuple[StatRowView, ...]
    moves: tuple[SkillMoveView, ...]
    targets: tuple = ()
    selected_target_id: str | None = None

    def __post_init__(self):
        if self.growth_points_available is not None:
            _validate_nonnegative(
                "growth_points_available",
                self.growth_points_available,
            )
        _validate_text("growth_message", self.growth_message)
        _validate_instance_tuple("stats", self.stats, StatRowView)
        _validate_instance_tuple("moves", self.moves, SkillMoveView)
        _validate_instance_tuple("targets", self.targets, MerchantTargetView)
        if self.targets:
            _validate_selected_target(self.targets, self.selected_target_id)


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
    targets: tuple
    selected_target_id: str
    components: tuple
    physical_identity: str | None
    mystical_identity: str | None

    def __post_init__(self):
        for name in ("name", "weapon_type", "intended_wielder", "description"):
            _validate_text(name, getattr(self, name))
        _validate_instance_tuple("bonuses", self.bonuses, StatBonusView)
        _validate_instance_tuple("targets", self.targets, MerchantTargetView)
        _validate_text("selected_target_id", self.selected_target_id)
        _validate_instance_tuple("components", self.components, WeaponComponentSlotView)
        if len(self.components) != 4:
            raise ValueError("weapon view must contain four component slots")
        for name in ("physical_identity", "mystical_identity"):
            value = getattr(self, name)
            if value is not None:
                _validate_text(name, value)
        if not any(
            target.drifter_id == self.selected_target_id and target.selected
            for target in self.targets
        ):
            raise ValueError("weapon target must be present and selected")


@dataclass(frozen=True)
class WeaponComponentOptionView:
    component_id: str
    display_name: str
    quantity: int
    effect_summary: tuple[str, ...] = ()

    def __post_init__(self):
        _validate_text("component_id", self.component_id)
        _validate_text("display_name", self.display_name)
        _validate_nonnegative("quantity", self.quantity)
        _validate_text_tuple("effect_summary", self.effect_summary)
        if self.quantity <= 0:
            raise ValueError("available component quantity must be positive")


@dataclass(frozen=True)
class WeaponComponentSlotView:
    slot_id: str
    label: str
    installed_component_id: str
    installed_component_name: str
    available_components: tuple[WeaponComponentOptionView, ...]
    installed_effect_summary: tuple[str, ...] = ()

    def __post_init__(self):
        for name in (
            "slot_id",
            "label",
            "installed_component_id",
            "installed_component_name",
        ):
            _validate_text(name, getattr(self, name))
        _validate_instance_tuple(
            "available_components",
            self.available_components,
            WeaponComponentOptionView,
        )
        _validate_text_tuple("installed_effect_summary", self.installed_effect_summary)


@dataclass(frozen=True)
class MerchantTargetView:
    drifter_id: str
    display_name: str
    selected: bool

    def __post_init__(self):
        _validate_text("drifter_id", self.drifter_id)
        _validate_text("display_name", self.display_name)
        _validate_bool("selected", self.selected)


@dataclass(frozen=True)
class MerchantMaterialView:
    item_id: str
    display_name: str
    quantity: int

    def __post_init__(self):
        _validate_text("item_id", self.item_id)
        _validate_text("display_name", self.display_name)
        _validate_nonnegative("quantity", self.quantity)


@dataclass(frozen=True)
class MerchantSlotView:
    slot_id: str
    label: str
    material_family: str
    progress: int
    material_id: str
    material_name: str
    material_cost: int
    material_quantity: int
    can_improve: bool
    blocked_reason: str | None = None

    def __post_init__(self):
        for name in (
            "slot_id",
            "label",
            "material_family",
            "material_id",
            "material_name",
        ):
            _validate_text(name, getattr(self, name))
        for name in ("progress", "material_cost", "material_quantity"):
            _validate_nonnegative(name, getattr(self, name))
        if self.progress > 100:
            raise ValueError("progress must not exceed 100")
        _validate_bool("can_improve", self.can_improve)
        if self.blocked_reason is not None:
            _validate_text("blocked_reason", self.blocked_reason)
        if self.can_improve == (self.blocked_reason is not None):
            raise ValueError("improvement availability and reason disagree")


@dataclass(frozen=True)
class MerchantDismantleView:
    item_id: str
    display_name: str
    quantity: int
    output_material_names: tuple[str, ...]
    maximum_yield: int

    def __post_init__(self):
        _validate_text("item_id", self.item_id)
        _validate_text("display_name", self.display_name)
        _validate_nonnegative("quantity", self.quantity)
        if self.quantity <= 0:
            raise ValueError("dismantle quantity must be positive")
        _validate_text_tuple("output_material_names", self.output_material_names)
        _validate_nonnegative("maximum_yield", self.maximum_yield)
        if self.maximum_yield <= 0:
            raise ValueError("maximum_yield must be positive")


@dataclass(frozen=True)
class MerchantComponentRecipeView:
    component_id: str
    display_name: str
    slot_id: str
    slot_label: str
    material_name: str
    material_cost: int
    material_quantity: int
    crafting_award: int
    can_craft: bool

    def __post_init__(self):
        for name in (
            "component_id",
            "display_name",
            "slot_id",
            "slot_label",
            "material_name",
        ):
            _validate_text(name, getattr(self, name))
        for name in ("material_cost", "material_quantity", "crafting_award"):
            _validate_nonnegative(name, getattr(self, name))
        if not self.material_cost or not self.crafting_award:
            raise ValueError("component recipes require positive costs and awards")
        _validate_bool("can_craft", self.can_craft)
        if self.can_craft != (self.material_quantity >= self.material_cost):
            raise ValueError("component recipe availability disagrees with stock")


@dataclass(frozen=True)
class MerchantView:
    crafting_level: int
    crafting_experience: int
    targets: tuple[MerchantTargetView, ...]
    selected_target_id: str
    weapon_name: str
    slots: tuple[MerchantSlotView, ...]
    materials: tuple[MerchantMaterialView, ...]
    dismantle_items: tuple[MerchantDismantleView, ...]
    component_recipes: tuple[MerchantComponentRecipeView, ...]

    def __post_init__(self):
        _validate_nonnegative("crafting_level", self.crafting_level)
        _validate_nonnegative("crafting_experience", self.crafting_experience)
        _validate_text("selected_target_id", self.selected_target_id)
        _validate_text("weapon_name", self.weapon_name)
        _validate_instance_tuple("targets", self.targets, MerchantTargetView)
        _validate_instance_tuple("slots", self.slots, MerchantSlotView)
        _validate_instance_tuple("materials", self.materials, MerchantMaterialView)
        _validate_instance_tuple(
            "dismantle_items",
            self.dismantle_items,
            MerchantDismantleView,
        )
        _validate_instance_tuple(
            "component_recipes",
            self.component_recipes,
            MerchantComponentRecipeView,
        )
        if not any(
            target.drifter_id == self.selected_target_id and target.selected
            for target in self.targets
        ):
            raise ValueError("selected target must be present and selected")
        if any(
            target.selected != (target.drifter_id == self.selected_target_id)
            for target in self.targets
        ):
            raise ValueError("exactly the selected target must be marked selected")
        if len(self.slots) != 4:
            raise ValueError("merchant weapon view must contain four slots")


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
    targets: tuple = ()
    selected_target_id: str | None = None

    def __post_init__(self):
        if not isinstance(self.necklace, AccessorySlotView):
            raise TypeError("necklace must be an AccessorySlotView")
        if not isinstance(self.ring, AccessorySlotView):
            raise TypeError("ring must be an AccessorySlotView")
        _validate_text_tuple("benefits", self.benefits)
        _validate_instance_tuple("targets", self.targets, MerchantTargetView)
        if self.targets:
            _validate_selected_target(self.targets, self.selected_target_id)


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
class OutingItemRewardView:
    item_id: str
    quantity: int
    display_name: str | None = None

    def __post_init__(self):
        _validate_text("item_id", self.item_id)
        if self.display_name is not None:
            _validate_text("display_name", self.display_name)
        if isinstance(self.quantity, bool) or not isinstance(self.quantity, int):
            raise TypeError("quantity must be an integer")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")


@dataclass(frozen=True)
class OutingRewardsView:
    experience: int
    gold: int
    items: tuple[OutingItemRewardView, ...] = ()

    def __post_init__(self):
        _validate_nonnegative("experience", self.experience)
        _validate_nonnegative("gold", self.gold)
        _validate_instance_tuple("items", self.items, OutingItemRewardView)


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
class MapEncounterInspectionView:
    encounter_label: str
    composition: tuple[str, ...]
    boss: bool

    def __post_init__(self):
        _validate_text("encounter_label", self.encounter_label)
        _validate_text_tuple("composition", self.composition)
        if not self.composition:
            raise ValueError("composition must not be empty")
        _validate_bool("boss", self.boss)


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
    merchant: MerchantView | None = None
    equipment: EquipmentView | None = None
    inventory: InventoryView | None = None
    route_map: MapView | None = None
    encounter_inspection: MapEncounterInspectionView | None = None
    companion_choices: tuple[CompanionChoiceView, ...] = ()
    shared_gold: int | None = None
    recruitment_cost: int | None = None
    outing_rewards: OutingRewardsView | None = None

    def __post_init__(self):
        object.__setattr__(self, "screen", OverworldScreen(self.screen))
        _validate_text("location_label", self.location_label)
        _validate_text("adventure_text", self.adventure_text)
        _validate_instance_tuple("options", self.options, OverworldOptionView)
        _validate_instance_tuple(
            "companion_choices",
            self.companion_choices,
            CompanionChoiceView,
        )
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
            allowed_contextual_actions = {
                OverworldScreen.MAIN: {
                    OverworldAction.ENTER_ENCOUNTER,
                    OverworldAction.RETRY,
                    OverworldAction.REST,
                },
                OverworldScreen.REST: {OverworldAction.SKIP_REST},
            }.get(self.screen, set())
            if not allowed_contextual_actions:
                raise ValueError(
                    "contextual_route_option is valid only on the Main or Rest screen"
                )
            if self.contextual_route_option.action not in allowed_contextual_actions:
                raise ValueError("invalid contextual route action")
        if self.notice is not None:
            _validate_text("notice", self.notice)
        if self.shared_gold is not None:
            _validate_nonnegative("shared_gold", self.shared_gold)
        if self.recruitment_cost is not None:
            _validate_nonnegative("recruitment_cost", self.recruitment_cost)
        if self.outing_rewards is not None and not isinstance(
            self.outing_rewards,
            OutingRewardsView,
        ):
            raise TypeError("outing_rewards must be an OutingRewardsView")
        if (self.screen is OverworldScreen.EXTRACTION) != (
            self.outing_rewards is not None
        ):
            raise ValueError("pending outing rewards belong only to Extraction")
        if (self.screen is OverworldScreen.MERCHANT) != (self.merchant is not None):
            raise ValueError("merchant data belongs only to the Merchant screen")
        if self.screen is OverworldScreen.COMPANION_SELECTION:
            if len(self.companion_choices) != 3:
                raise ValueError("companion selection must offer three choices")
            if self.shared_gold is None or self.recruitment_cost is None:
                raise ValueError("companion selection must show shared gold and cost")
        elif self.companion_choices:
            raise ValueError("companion choices are only valid on their selection screen")
        for name, expected_type in (
            ("character", CharacterOverviewView),
            ("skills", SkillsView),
            ("weapon", WeaponView),
            ("merchant", MerchantView),
            ("equipment", EquipmentView),
            ("inventory", InventoryView),
            ("route_map", MapView),
            ("encounter_inspection", MapEncounterInspectionView),
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


def _validate_selected_target(targets, selected_target_id):
    _validate_text("selected_target_id", selected_target_id)
    if not any(target.drifter_id == selected_target_id for target in targets):
        raise ValueError("selected target must be present")
    if any(target.selected != (target.drifter_id == selected_target_id) for target in targets):
        raise ValueError("exactly the selected target must be marked selected")


def _validate_text_tuple(name, values):
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple")
    for value in values:
        _validate_text(name, value)

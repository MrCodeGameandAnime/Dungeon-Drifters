"""Immutable renderer-neutral models for battle presentation."""

from dataclasses import dataclass, field
from enum import StrEnum

from app.combat.result import CombatOutcome
from app.player.run_items import InventoryCommand


class ActionIntent(StrEnum):
    ATTACK = "attack"
    DEFEND = "defend"
    HEAL = "heal"
    ITEMS = "items"
    ESCAPE = "escape"
    SUPER = "super"


class InteractionPhase(StrEnum):
    ACTIONS = "actions"
    REGULAR_MOVES = "regular_moves"
    HEALING_MOVES = "healing_moves"
    SUPER_MOVES = "super_moves"
    INVENTORY = "inventory"
    INVENTORY_ITEM = "inventory_item"
    INVENTORY_INSPECT = "inventory_inspect"
    INVENTORY_COMBINATION = "inventory_combination"
    INVENTORY_CONFIRMATION = "inventory_confirmation"
    TARGETS = "targets"
    COMPLETE = "complete"


class InputRejectionReason(StrEnum):
    ACTION_UNAVAILABLE = "action_unavailable"
    MOVE_UNAVAILABLE = "move_unavailable"
    BACK_UNAVAILABLE = "back_unavailable"
    SUPER_UNAVAILABLE = "super_unavailable"
    INVENTORY_ITEM_UNAVAILABLE = "inventory_item_unavailable"
    INVENTORY_COMMAND_UNAVAILABLE = "inventory_command_unavailable"
    INVENTORY_COMPANION_UNAVAILABLE = "inventory_companion_unavailable"
    INVENTORY_CONFIRMATION_UNAVAILABLE = "inventory_confirmation_unavailable"
    TARGET_UNAVAILABLE = "target_unavailable"


class BattleEventType(StrEnum):
    ENCOUNTER_START = "encounter_start"
    INITIATIVE = "initiative"
    DAMAGE = "damage"
    MISS = "miss"
    HEALING = "healing"
    DEFEND = "defend"
    UTILITY = "utility"
    ACTION_REJECTED = "action_rejected"
    INPUT_REJECTED = "input_rejected"
    VICTORY = "victory"
    DEFEAT = "defeat"
    INVENTORY = "inventory"
    STATUS = "status"


class ActionAvailabilityReason(StrEnum):
    NO_REGULAR_MOVES = "no_regular_moves"
    NO_HEALING_MOVES = "no_healing_moves"
    FULL_HP = "full_hp"
    HEAL_COOLDOWN = "heal_cooldown"
    CANNOT_DEFEND = "cannot_defend"
    NOT_IMPLEMENTED = "not_implemented"
    SUPER_NOT_READY = "super_not_ready"


class MoveAvailabilityReason(StrEnum):
    INSUFFICIENT_RESOURCE = "insufficient_resource"
    REQUIRES_PREPARED_PAYLOAD = "requires_prepared_payload"


class InventoryAvailabilityReason(StrEnum):
    ALREADY_PREPARED = "already_prepared"
    ITEM_UNAVAILABLE = "item_unavailable"
    MISSING_COMPANION = "missing_companion"


@dataclass(frozen=True)
class CombatantView:
    display_name: str
    hp_current: int
    hp_maximum: int
    mana_current: int | None = None
    mana_maximum: int | None = None
    super_current: int | None = None
    super_maximum: int | None = None
    defending: bool = False
    temporary_labels: tuple[str, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "display_name", _validate_nonempty_string("display_name", self.display_name))
        _validate_resource_pair("hp", self.hp_current, self.hp_maximum, optional=False)
        _validate_resource_pair("mana", self.mana_current, self.mana_maximum, optional=True)
        _validate_resource_pair("super", self.super_current, self.super_maximum, optional=True)
        object.__setattr__(self, "defending", _validate_bool("defending", self.defending))
        object.__setattr__(
            self,
            "temporary_labels",
            _validate_string_tuple("temporary_labels", self.temporary_labels),
        )


@dataclass(frozen=True)
class EnemyCombatantView:
    target_id: str
    display_label: str
    hp_current: int
    hp_maximum: int
    mana_current: int | None = None
    mana_maximum: int | None = None
    super_current: int | None = None
    super_maximum: int | None = None
    defending: bool = False
    temporary_labels: tuple[str, ...] = ()
    defeated: bool = False

    def __post_init__(self):
        object.__setattr__(self, "target_id", _validate_nonempty_string("target_id", self.target_id))
        object.__setattr__(
            self,
            "display_label",
            _validate_nonempty_string("display_label", self.display_label),
        )
        _validate_resource_pair("hp", self.hp_current, self.hp_maximum, optional=False)
        _validate_resource_pair("mana", self.mana_current, self.mana_maximum, optional=True)
        _validate_resource_pair("super", self.super_current, self.super_maximum, optional=True)
        object.__setattr__(self, "defending", _validate_bool("defending", self.defending))
        object.__setattr__(
            self,
            "temporary_labels",
            _validate_string_tuple("temporary_labels", self.temporary_labels),
        )
        object.__setattr__(self, "defeated", _validate_bool("defeated", self.defeated))
        if self.defeated and self.hp_current != 0:
            raise ValueError("defeated enemies must have zero current HP")

    @property
    def display_name(self):
        return self.display_label


@dataclass(frozen=True)
class ActionOptionView:
    intent: ActionIntent
    number: int | None
    label: str
    enabled: bool
    disabled_reason: ActionAvailabilityReason | None = None

    def __post_init__(self):
        object.__setattr__(self, "intent", _validate_enum("intent", self.intent, ActionIntent))
        object.__setattr__(self, "number", _validate_optional_positive_integer("number", self.number))
        object.__setattr__(self, "label", _validate_nonempty_string("label", self.label))
        object.__setattr__(self, "enabled", _validate_bool("enabled", self.enabled))
        object.__setattr__(
            self,
            "disabled_reason",
            _validate_optional_enum(
                "disabled_reason",
                self.disabled_reason,
                ActionAvailabilityReason,
            ),
        )
        _validate_availability(self.enabled, self.disabled_reason)


@dataclass(frozen=True)
class MoveOptionView:
    selection_key: str
    number: int
    name: str
    tags: tuple[str, ...]
    rules_summary: str
    resource_label: str | None
    enabled: bool
    disabled_reason: MoveAvailabilityReason | None = None

    def __post_init__(self):
        object.__setattr__(
            self,
            "selection_key",
            _validate_nonempty_string("selection_key", self.selection_key),
        )
        object.__setattr__(self, "number", _validate_positive_integer("number", self.number))
        object.__setattr__(self, "name", _validate_nonempty_string("name", self.name))
        object.__setattr__(self, "tags", _validate_string_tuple("tags", self.tags))
        object.__setattr__(
            self,
            "rules_summary",
            _validate_nonempty_string("rules_summary", self.rules_summary),
        )
        object.__setattr__(
            self,
            "resource_label",
            _validate_optional_string("resource_label", self.resource_label),
        )
        object.__setattr__(self, "enabled", _validate_bool("enabled", self.enabled))
        object.__setattr__(
            self,
            "disabled_reason",
            _validate_optional_enum(
                "disabled_reason",
                self.disabled_reason,
                MoveAvailabilityReason,
            ),
        )
        _validate_availability(self.enabled, self.disabled_reason)


@dataclass(frozen=True)
class TargetOptionView:
    target_id: str
    number: int
    display_label: str
    hp_current: int
    hp_maximum: int
    temporary_labels: tuple[str, ...]
    move_preview: MoveOptionView
    enabled: bool
    disabled_reason: InputRejectionReason | None = None

    def __post_init__(self):
        object.__setattr__(self, "target_id", _validate_nonempty_string("target_id", self.target_id))
        object.__setattr__(self, "number", _validate_positive_integer("number", self.number))
        object.__setattr__(
            self,
            "display_label",
            _validate_nonempty_string("display_label", self.display_label),
        )
        _validate_resource_pair("hp", self.hp_current, self.hp_maximum, optional=False)
        object.__setattr__(
            self,
            "temporary_labels",
            _validate_string_tuple("temporary_labels", self.temporary_labels),
        )
        _validate_instance("move_preview", self.move_preview, MoveOptionView)
        object.__setattr__(self, "enabled", _validate_bool("enabled", self.enabled))
        object.__setattr__(
            self,
            "disabled_reason",
            _validate_optional_enum(
                "disabled_reason",
                self.disabled_reason,
                InputRejectionReason,
            ),
        )
        _validate_availability(self.enabled, self.disabled_reason)


@dataclass(frozen=True)
class InventoryItemOptionView:
    item_id: str
    number: int
    display_name: str
    quantity: int
    enabled: bool
    disabled_reason: InventoryAvailabilityReason | None = None

    def __post_init__(self):
        object.__setattr__(
            self,
            "item_id",
            _validate_nonempty_string("item_id", self.item_id),
        )
        object.__setattr__(self, "number", _validate_positive_integer("number", self.number))
        object.__setattr__(
            self,
            "display_name",
            _validate_nonempty_string("display_name", self.display_name),
        )
        object.__setattr__(self, "quantity", _validate_positive_integer("quantity", self.quantity))
        object.__setattr__(self, "enabled", _validate_bool("enabled", self.enabled))
        object.__setattr__(
            self,
            "disabled_reason",
            _validate_optional_enum(
                "disabled_reason",
                self.disabled_reason,
                InventoryAvailabilityReason,
            ),
        )
        _validate_availability(self.enabled, self.disabled_reason)


@dataclass(frozen=True)
class InventoryCommandOptionView:
    command: InventoryCommand
    number: int
    label: str
    enabled: bool
    disabled_reason: InventoryAvailabilityReason | None = None

    def __post_init__(self):
        object.__setattr__(self, "command", _validate_enum("command", self.command, InventoryCommand))
        object.__setattr__(self, "number", _validate_positive_integer("number", self.number))
        object.__setattr__(self, "label", _validate_nonempty_string("label", self.label))
        object.__setattr__(self, "enabled", _validate_bool("enabled", self.enabled))
        object.__setattr__(
            self,
            "disabled_reason",
            _validate_optional_enum(
                "disabled_reason",
                self.disabled_reason,
                InventoryAvailabilityReason,
            ),
        )
        _validate_availability(self.enabled, self.disabled_reason)


@dataclass(frozen=True)
class InventoryInspectionView:
    item_id: str
    display_name: str
    description: str

    def __post_init__(self):
        for field_name in ("item_id", "display_name", "description"):
            object.__setattr__(
                self,
                field_name,
                _validate_nonempty_string(field_name, getattr(self, field_name)),
            )


@dataclass(frozen=True)
class InventoryConfirmationView:
    source_item_id: str
    source_display_name: str
    companion_item_id: str
    companion_display_name: str
    action_id: str
    result_display_name: str

    def __post_init__(self):
        for field_name in (
            "source_item_id",
            "source_display_name",
            "companion_item_id",
            "companion_display_name",
            "action_id",
            "result_display_name",
        ):
            object.__setattr__(
                self,
                field_name,
                _validate_nonempty_string(field_name, getattr(self, field_name)),
            )


@dataclass(frozen=True)
class SuperMeterView:
    current: int
    maximum: int
    fill_bps: int
    ready: bool
    activation_key: str
    activation_offered: bool

    def __post_init__(self):
        _validate_resource_pair("super", self.current, self.maximum, optional=False)
        object.__setattr__(self, "fill_bps", _validate_basis_points("fill_bps", self.fill_bps))
        object.__setattr__(self, "ready", _validate_bool("ready", self.ready))
        object.__setattr__(
            self,
            "activation_key",
            _validate_nonempty_string("activation_key", self.activation_key),
        )
        object.__setattr__(
            self,
            "activation_offered",
            _validate_bool("activation_offered", self.activation_offered),
        )
        if self.activation_offered and not self.ready:
            raise ValueError("Super activation cannot be offered when the meter is not ready")


@dataclass(frozen=True)
class BattleLogEntry:
    event_type: BattleEventType
    actor_name: str | None = None
    target_name: str | None = None
    action_name: str | None = None
    accepted: bool | None = None
    hit: bool | None = None
    amount: int = 0
    critical: bool = False
    resource_spent: int = 0
    statuses_applied: tuple[str, ...] = ()
    reason: str | None = None
    rejection_reason: InputRejectionReason | None = None
    outcomes: tuple[CombatOutcome, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "event_type", _validate_enum("event_type", self.event_type, BattleEventType))
        for name in ("actor_name", "target_name", "action_name", "reason"):
            object.__setattr__(self, name, _validate_optional_string(name, getattr(self, name)))
        object.__setattr__(self, "accepted", _validate_optional_bool("accepted", self.accepted))
        object.__setattr__(self, "hit", _validate_optional_bool("hit", self.hit))
        object.__setattr__(self, "amount", _validate_nonnegative_integer("amount", self.amount))
        object.__setattr__(self, "critical", _validate_bool("critical", self.critical))
        object.__setattr__(
            self,
            "resource_spent",
            _validate_nonnegative_integer("resource_spent", self.resource_spent),
        )
        object.__setattr__(
            self,
            "statuses_applied",
            _validate_string_tuple("statuses_applied", self.statuses_applied),
        )
        object.__setattr__(
            self,
            "rejection_reason",
            _validate_optional_enum(
                "rejection_reason",
                self.rejection_reason,
                InputRejectionReason,
            ),
        )
        if not isinstance(self.outcomes, tuple):
            raise TypeError("outcomes must be a tuple")
        if not all(isinstance(outcome, CombatOutcome) for outcome in self.outcomes):
            raise TypeError("outcomes must contain CombatOutcome values")
        if self.event_type == BattleEventType.INPUT_REJECTED and self.rejection_reason is None:
            raise ValueError("input_rejected events require rejection_reason")
        if self.event_type != BattleEventType.INPUT_REJECTED and self.rejection_reason is not None:
            raise ValueError("rejection_reason is only valid for input_rejected events")


@dataclass(frozen=True)
class BattleVisualView:
    player_lines: tuple[str, ...] = ()
    enemy_lines: tuple[str, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "player_lines", _validate_string_tuple("player_lines", self.player_lines))
        object.__setattr__(self, "enemy_lines", _validate_string_tuple("enemy_lines", self.enemy_lines))


@dataclass(frozen=True)
class BattleView:
    interaction_phase: InteractionPhase
    player: CombatantView
    enemies: tuple[EnemyCombatantView, ...]
    super_meter: SuperMeterView
    action_options: tuple[ActionOptionView, ...] = ()
    move_options: tuple[MoveOptionView, ...] = ()
    target_options: tuple[TargetOptionView, ...] = ()
    inventory_items: tuple[InventoryItemOptionView, ...] = ()
    selected_inventory_item: InventoryItemOptionView | None = None
    inventory_commands: tuple[InventoryCommandOptionView, ...] = ()
    inventory_inspection: InventoryInspectionView | None = None
    inventory_companions: tuple[InventoryItemOptionView, ...] = ()
    inventory_confirmation: InventoryConfirmationView | None = None
    log_entries: tuple[BattleLogEntry, ...] = ()
    visual: BattleVisualView = field(default_factory=BattleVisualView)

    def __post_init__(self):
        object.__setattr__(
            self,
            "interaction_phase",
            _validate_enum("interaction_phase", self.interaction_phase, InteractionPhase),
        )
        _validate_instance("player", self.player, CombatantView)
        object.__setattr__(
            self,
            "enemies",
            _validate_instance_tuple("enemies", self.enemies, EnemyCombatantView),
        )
        if not self.enemies:
            raise ValueError("BattleView requires at least one enemy")
        if len(self.enemies) > 4:
            raise ValueError("BattleView supports at most four enemies")
        if len({enemy.target_id for enemy in self.enemies}) != len(self.enemies):
            raise ValueError("enemy target IDs must be unique")
        _validate_instance("super_meter", self.super_meter, SuperMeterView)
        object.__setattr__(
            self,
            "action_options",
            _validate_instance_tuple("action_options", self.action_options, ActionOptionView),
        )
        object.__setattr__(
            self,
            "move_options",
            _validate_instance_tuple("move_options", self.move_options, MoveOptionView),
        )
        object.__setattr__(
            self,
            "target_options",
            _validate_instance_tuple("target_options", self.target_options, TargetOptionView),
        )
        object.__setattr__(
            self,
            "inventory_items",
            _validate_instance_tuple(
                "inventory_items",
                self.inventory_items,
                InventoryItemOptionView,
            ),
        )
        object.__setattr__(
            self,
            "selected_inventory_item",
            _validate_optional_instance(
                "selected_inventory_item",
                self.selected_inventory_item,
                InventoryItemOptionView,
            ),
        )
        object.__setattr__(
            self,
            "inventory_commands",
            _validate_instance_tuple(
                "inventory_commands",
                self.inventory_commands,
                InventoryCommandOptionView,
            ),
        )
        object.__setattr__(
            self,
            "inventory_inspection",
            _validate_optional_instance(
                "inventory_inspection",
                self.inventory_inspection,
                InventoryInspectionView,
            ),
        )
        object.__setattr__(
            self,
            "inventory_companions",
            _validate_instance_tuple(
                "inventory_companions",
                self.inventory_companions,
                InventoryItemOptionView,
            ),
        )
        object.__setattr__(
            self,
            "inventory_confirmation",
            _validate_optional_instance(
                "inventory_confirmation",
                self.inventory_confirmation,
                InventoryConfirmationView,
            ),
        )
        object.__setattr__(
            self,
            "log_entries",
            _validate_instance_tuple("log_entries", self.log_entries, BattleLogEntry),
        )
        _validate_instance("visual", self.visual, BattleVisualView)

    @property
    def enemy(self):
        if len(self.enemies) != 1:
            raise ValueError("BattleView.enemy is available only for single-enemy battles")
        return self.enemies[0]


def _validate_enum(name, value, enum_type):
    try:
        return enum_type(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"invalid {name}: {value!r}") from error


def _validate_optional_enum(name, value, enum_type):
    if value is None:
        return None
    return _validate_enum(name, value, enum_type)


def _validate_bool(name, value):
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a boolean")
    return value


def _validate_optional_bool(name, value):
    if value is None:
        return None
    return _validate_bool(name, value)


def _validate_nonnegative_integer(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must not be negative")
    return value


def _validate_positive_integer(name, value):
    value = _validate_nonnegative_integer(name, value)
    if value == 0:
        raise ValueError(f"{name} must be positive")
    return value


def _validate_optional_positive_integer(name, value):
    if value is None:
        return None
    return _validate_positive_integer(name, value)


def _validate_basis_points(name, value):
    value = _validate_nonnegative_integer(name, value)
    if value > 10_000:
        raise ValueError(f"{name} must not exceed 10000")
    return value


def _validate_nonempty_string(name, value):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


def _validate_optional_string(name, value):
    if value is None:
        return None
    return _validate_nonempty_string(name, value)


def _validate_string_tuple(name, values):
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple")
    return tuple(_validate_nonempty_string(name, value) for value in values)


def _validate_resource_pair(name, current, maximum, *, optional):
    if optional and current is None and maximum is None:
        return
    if current is None or maximum is None:
        raise ValueError(f"{name} current and maximum must both be provided")
    current = _validate_nonnegative_integer(f"{name}_current", current)
    maximum = _validate_positive_integer(f"{name}_maximum", maximum)
    if current > maximum:
        raise ValueError(f"{name} current must not exceed maximum")


def _validate_availability(enabled, disabled_reason):
    if enabled and disabled_reason is not None:
        raise ValueError("enabled options must not have a disabled reason")
    if not enabled and disabled_reason is None:
        raise ValueError("disabled options require a disabled reason")


def _validate_instance(name, value, expected_type):
    if not isinstance(value, expected_type):
        raise TypeError(f"{name} must be {expected_type.__name__}")
    return value


def _validate_optional_instance(name, value, expected_type):
    if value is None:
        return None
    return _validate_instance(name, value, expected_type)


def _validate_instance_tuple(name, values, expected_type):
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple")
    return tuple(_validate_instance(name, value, expected_type) for value in values)

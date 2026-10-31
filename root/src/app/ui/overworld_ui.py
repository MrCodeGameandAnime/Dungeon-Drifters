"""Semantic overworld input values and UI protocol."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, TypeAlias, Union, runtime_checkable

from app.presentation.overworld_models import OverworldAction, OverworldView
from app.runtime_contracts import has_required_members


@dataclass(frozen=True)
class ChooseOverworldAction:
    action: OverworldAction

    def __post_init__(self):
        object.__setattr__(self, "action", OverworldAction(self.action))


@dataclass(frozen=True)
class ChooseOverworldItem:
    selection_key: str

    def __post_init__(self):
        if not isinstance(self.selection_key, str) or not self.selection_key.strip():
            raise ValueError("selection_key must be a nonempty string")


@dataclass(frozen=True)
class ChooseOverworldHealingTarget:
    drifter_id: str

    def __post_init__(self):
        if not isinstance(self.drifter_id, str) or not self.drifter_id.strip():
            raise ValueError("drifter_id must be a nonempty string")


@dataclass(frozen=True)
class ChoosePermanentStatIncrease:
    stat_name: str

    def __post_init__(self):
        if not isinstance(self.stat_name, str) or not self.stat_name.strip():
            raise ValueError("stat_name must be a nonempty string")


@dataclass(frozen=True)
class ChooseCompanion:
    drifter_id: str
    event_id: str

    def __post_init__(self):
        if not isinstance(self.drifter_id, str) or not self.drifter_id.strip():
            raise ValueError("drifter_id must be a nonempty string")
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError("event_id must be a nonempty string")


@dataclass(frozen=True)
class ChooseActivePair:
    drifter_ids: tuple[str, str]

    def __post_init__(self):
        if not isinstance(self.drifter_ids, tuple) or len(self.drifter_ids) != 2:
            raise ValueError("drifter_ids must contain exactly two IDs")
        for drifter_id in self.drifter_ids:
            if not isinstance(drifter_id, str) or not drifter_id.strip():
                raise ValueError("drifter IDs must be nonempty strings")


@dataclass(frozen=True)
class ChooseMerchantTarget:
    drifter_id: str

    def __post_init__(self):
        if not isinstance(self.drifter_id, str) or not self.drifter_id.strip():
            raise ValueError("drifter_id must be a nonempty string")


class HubSupplyOperation(StrEnum):
    BUY = "buy"
    SELL = "sell"
    LOAD = "load"
    UNLOAD = "unload"


@dataclass(frozen=True)
class ChooseHubSupplyAction:
    operation: HubSupplyOperation
    item_id: str

    def __post_init__(self):
        object.__setattr__(self, "operation", HubSupplyOperation(self.operation))
        if not isinstance(self.item_id, str) or not self.item_id.strip():
            raise ValueError("item_id must be a nonempty string")


@dataclass(frozen=True)
class ChooseAlchemyRecipe:
    recipe_id: str

    def __post_init__(self):
        if not isinstance(self.recipe_id, str) or not self.recipe_id.strip():
            raise ValueError("recipe_id must be a nonempty string")


@dataclass(frozen=True)
class ChooseCharacterTarget:
    drifter_id: str

    def __post_init__(self):
        if not isinstance(self.drifter_id, str) or not self.drifter_id.strip():
            raise ValueError("drifter_id must be a nonempty string")


@dataclass(frozen=True)
class ChooseMerchantImprove:
    target_drifter_id: str
    slot_id: str

    def __post_init__(self):
        for name in ("target_drifter_id", "slot_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a nonempty string")


@dataclass(frozen=True)
class ChooseMerchantDismantle:
    target_drifter_id: str
    item_id: str
    quantity: int = 1

    def __post_init__(self):
        for name in ("target_drifter_id", "item_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a nonempty string")
        if isinstance(self.quantity, bool) or not isinstance(self.quantity, int):
            raise TypeError("quantity must be an integer")
        if self.quantity < 1:
            raise ValueError("quantity must be positive")


@dataclass(frozen=True)
class ChooseMerchantCraftComponent:
    target_drifter_id: str
    component_id: str

    def __post_init__(self):
        for name in ("target_drifter_id", "component_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a nonempty string")


@dataclass(frozen=True)
class ChooseMerchantTierV:
    target_drifter_id: str

    def __post_init__(self):
        if not isinstance(self.target_drifter_id, str) or not self.target_drifter_id.strip():
            raise ValueError("target_drifter_id must be a nonempty string")


@dataclass(frozen=True)
class ChooseWeaponTarget:
    drifter_id: str

    def __post_init__(self):
        if not isinstance(self.drifter_id, str) or not self.drifter_id.strip():
            raise ValueError("drifter_id must be a nonempty string")


OverworldInput: TypeAlias = Union[
    ChooseOverworldAction,
    ChooseOverworldItem,
    ChooseOverworldHealingTarget,
    ChoosePermanentStatIncrease,
    ChooseCompanion,
    ChooseActivePair,
    ChooseCharacterTarget,
    ChooseMerchantTarget,
    ChooseHubSupplyAction,
    ChooseAlchemyRecipe,
    ChooseMerchantImprove,
    ChooseMerchantDismantle,
    ChooseMerchantCraftComponent,
    ChooseMerchantTierV,
    ChooseWeaponTarget,
]


@runtime_checkable
class OverworldUI(Protocol):
    def render(self, view: OverworldView) -> None:
        ...

    def read_input(self, view: OverworldView) -> OverworldInput:
        ...


_OVERWORLD_UI_CALLABLE_MEMBERS = ("render", "read_input")


def is_overworld_ui(value):
    return has_required_members(
        value,
        _OVERWORLD_UI_CALLABLE_MEMBERS,
        _OVERWORLD_UI_CALLABLE_MEMBERS,
    )

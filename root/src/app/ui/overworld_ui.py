"""Semantic overworld input values and UI protocol."""

from dataclasses import dataclass
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
class ChoosePermanentStatIncrease:
    stat_name: str

    def __post_init__(self):
        if not isinstance(self.stat_name, str) or not self.stat_name.strip():
            raise ValueError("stat_name must be a nonempty string")


@dataclass(frozen=True)
class ChooseCompanion:
    drifter_id: str

    def __post_init__(self):
        if not isinstance(self.drifter_id, str) or not self.drifter_id.strip():
            raise ValueError("drifter_id must be a nonempty string")


@dataclass(frozen=True)
class ChooseMerchantTarget:
    drifter_id: str

    def __post_init__(self):
        if not isinstance(self.drifter_id, str) or not self.drifter_id.strip():
            raise ValueError("drifter_id must be a nonempty string")


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
class ChooseWeaponTarget:
    drifter_id: str

    def __post_init__(self):
        if not isinstance(self.drifter_id, str) or not self.drifter_id.strip():
            raise ValueError("drifter_id must be a nonempty string")


@dataclass(frozen=True)
class ChooseWeaponComponent:
    target_drifter_id: str
    slot_id: str
    component_id: str

    def __post_init__(self):
        for name in ("target_drifter_id", "slot_id", "component_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a nonempty string")


OverworldInput: TypeAlias = Union[
    ChooseOverworldAction,
    ChooseOverworldItem,
    ChoosePermanentStatIncrease,
    ChooseCompanion,
    ChooseCharacterTarget,
    ChooseMerchantTarget,
    ChooseMerchantImprove,
    ChooseMerchantDismantle,
    ChooseMerchantCraftComponent,
    ChooseWeaponTarget,
    ChooseWeaponComponent,
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

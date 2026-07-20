"""Semantic overworld input values and UI protocol."""

from dataclasses import dataclass
from typing import Protocol, TypeAlias, runtime_checkable

from app.presentation.overworld_models import OverworldAction, OverworldView


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


OverworldInput: TypeAlias = (
    ChooseOverworldAction
    | ChooseOverworldItem
    | ChoosePermanentStatIncrease
)


@runtime_checkable
class OverworldUI(Protocol):
    def render(self, view: OverworldView) -> None:
        ...

    def read_input(self, view: OverworldView) -> OverworldInput:
        ...

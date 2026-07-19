"""Semantic battle input values and the battle UI port."""

from dataclasses import dataclass
from typing import Protocol, TypeAlias, runtime_checkable

from app.player.run_items import InventoryCommand
from app.presentation.battle_models import ActionIntent, BattleView


@dataclass(frozen=True)
class ChooseAction:
    intent: ActionIntent

    def __post_init__(self):
        try:
            intent = ActionIntent(self.intent)
        except (TypeError, ValueError) as error:
            raise ValueError(f"invalid action intent: {self.intent!r}") from error
        object.__setattr__(self, "intent", intent)


@dataclass(frozen=True)
class ChooseMove:
    move_key: str

    def __post_init__(self):
        if not isinstance(self.move_key, str):
            raise TypeError("move_key must be a string")
        if not self.move_key.strip():
            raise ValueError("move_key must not be empty")


@dataclass(frozen=True)
class ChooseTarget:
    target_id: str

    def __post_init__(self):
        _validate_nonempty_string("target_id", self.target_id)


@dataclass(frozen=True)
class ChooseInventoryItem:
    item_id: str

    def __post_init__(self):
        _validate_nonempty_string("item_id", self.item_id)


@dataclass(frozen=True)
class ChooseInventoryCommand:
    command: InventoryCommand

    def __post_init__(self):
        try:
            command = InventoryCommand(self.command)
        except (TypeError, ValueError) as error:
            raise ValueError(f"invalid inventory command: {self.command!r}") from error
        object.__setattr__(self, "command", command)


@dataclass(frozen=True)
class ChooseInventoryCompanion:
    item_id: str

    def __post_init__(self):
        _validate_nonempty_string("item_id", self.item_id)


@dataclass(frozen=True)
class ConfirmInventoryUse:
    confirmed: bool

    def __post_init__(self):
        if not isinstance(self.confirmed, bool):
            raise TypeError("confirmed must be a boolean")


@dataclass(frozen=True)
class GoBack:
    pass


BattleInput: TypeAlias = (
    ChooseAction
    | ChooseMove
    | ChooseTarget
    | ChooseInventoryItem
    | ChooseInventoryCommand
    | ChooseInventoryCompanion
    | ConfirmInventoryUse
    | GoBack
)


@runtime_checkable
class BattleUI(Protocol):
    def render(self, view: BattleView) -> None:
        ...

    def read_input(self, view: BattleView) -> BattleInput:
        ...


def _validate_nonempty_string(name, value):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")

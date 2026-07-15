"""Semantic battle input values and the battle UI port."""

from dataclasses import dataclass
from typing import Protocol, TypeAlias, runtime_checkable

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
class GoBack:
    pass


BattleInput: TypeAlias = ChooseAction | ChooseMove | GoBack


@runtime_checkable
class BattleUI(Protocol):
    def render(self, view: BattleView) -> None:
        ...

    def read_input(self, view: BattleView) -> BattleInput:
        ...

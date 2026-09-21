"""Thin browser translation boundary around the authoritative DD runtime."""

import json
from dataclasses import fields, is_dataclass
from enum import Enum

from app.combat.battle import Battle
from app.content.catalog import create_enemy_state
from app.game.new_game import create_new_game
from app.game.overworld_session import OverworldSession
from app.player.run_items import InventoryCommand
from app.ui.battle_ui import (
    ChooseAction,
    ChooseInventoryCommand,
    ChooseInventoryCompanion,
    ChooseInventoryItem,
    ChooseMove,
    ChooseTarget,
    ConfirmInventoryUse,
    GoBack,
)
from app.ui.overworld_ui import (
    ChooseOverworldAction,
    ChooseOverworldItem,
    ChoosePermanentStatIncrease,
)


def _project(value):
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: _project(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_project(item) for item in value]
    if isinstance(value, list):
        return [_project(item) for item in value]
    if isinstance(value, dict):
        return {_project(key): _project(item) for key, item in value.items()}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise TypeError("unsupported browser projection value")


def _required(command, key):
    if key not in command:
        raise ValueError("browser command requires " + key)
    return command[key]


def _command_to_input(command):
    if not isinstance(command, dict):
        raise TypeError("browser command must be an object")
    kind = command.get("kind")
    if kind == "overworld_action":
        return ChooseOverworldAction(_required(command, "action"))
    if kind == "overworld_item":
        return ChooseOverworldItem(_required(command, "selection_key"))
    if kind == "stat_increase":
        return ChoosePermanentStatIncrease(_required(command, "stat_name"))
    if kind == "action":
        return ChooseAction(_required(command, "intent"))
    if kind == "move":
        return ChooseMove(_required(command, "key"))
    if kind == "target":
        return ChooseTarget(_required(command, "target_id"))
    if kind == "inventory_item":
        return ChooseInventoryItem(_required(command, "item_id"))
    if kind == "inventory_command":
        return ChooseInventoryCommand(_required(command, "command"))
    if kind == "inventory_companion":
        return ChooseInventoryCompanion(_required(command, "item_id"))
    if kind == "inventory_confirm":
        return ConfirmInventoryUse(_required(command, "confirmed"))
    if kind == "back":
        return GoBack()
    raise ValueError("unknown browser command: " + str(kind))


class BrowserRuntime:
    def __init__(self):
        self._game = None
        self._session = None
        self._drifter_id = None

    def start_game(self, drifter_id="branoc"):
        self._game = create_new_game(drifter_id)
        self._session = OverworldSession(
            self._game,
            ui=None,
            battle_factory=Battle,
            enemy_factory=create_enemy_state,
            battle_ui_factory=None,
            save_repository=None,
        )
        self._drifter_id = drifter_id
        return self.current_view()

    def current_view(self):
        if self._session is None:
            raise RuntimeError("browser runtime has not started")
        return _project(self._session.current_view())

    def current_view_json(self):
        return json.dumps(self.current_view(), separators=(",", ":"))

    def submit(self, command):
        if self._session is None:
            raise RuntimeError("browser runtime has not started")
        return _project(self._session.submit(_command_to_input(command)))

    def submit_json(self, command_json):
        return self.submit(json.loads(command_json))

    def restart_game(self):
        return self.start_game(self._drifter_id or "branoc")


_runtime = BrowserRuntime()


def start_game(drifter_id="branoc"):
    return _runtime.start_game(drifter_id)


def current_view():
    return _runtime.current_view()


def submit(command):
    return _runtime.submit(command)


def restart_game():
    return _runtime.restart_game()

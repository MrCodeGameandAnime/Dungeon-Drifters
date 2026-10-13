import ast
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from app.content.catalog import create_drifter
from app.game.game_state import GameState
from app.persistence import bootstrap as persistence_bootstrap
from app.game.overworld_session import OverworldSession
from app.persistence.ports import SaveLoadStatus, SavePortError, is_save_port
from app.player.player_state import PlayerState
from app.presentation.overworld_models import (
    OverworldAction,
    OverworldAvailabilityReason,
    OverworldScreen,
)
from app.ui.overworld_ui import ChooseOverworldAction


ROOT = Path(__file__).resolve().parents[1]


def _session(save_port=None):
    return OverworldSession(
        GameState(PlayerState(create_drifter("branoc"))),
        battle_factory=lambda *args, **kwargs: None,
        enemy_factory=lambda *args, **kwargs: None,
        ui=None,
        battle_ui_factory=None,
        save_port=save_port,
    )


class TrackingSavePort:
    def __init__(self):
        self.inspect_calls = 0
        self.save_calls = 0
        self.load_calls = 0

    def save(self, game_state):
        self.save_calls += 1
        return SimpleNamespace(status=SaveLoadStatus.SAVED, error=None)

    def inspect(self):
        self.inspect_calls += 1
        return SimpleNamespace(status=SaveLoadStatus.MISSING)

    def load(self):
        self.load_calls += 1
        return SimpleNamespace(status=SaveLoadStatus.MISSING, error=None)


def test_default_save_port_is_lazy_until_options_load_availability(monkeypatch):
    instances = []

    class TrackingDefaultSavePort(TrackingSavePort):
        def __init__(self):
            super().__init__()
            instances.append(self)

    monkeypatch.setattr(
        persistence_bootstrap,
        "build_default_save_port",
        TrackingDefaultSavePort,
    )

    session = _session()
    assert instances == []
    assert session.current_view().screen is OverworldScreen.MAIN
    assert instances == []

    options_view = session.submit(
        ChooseOverworldAction(OverworldAction.OPTIONS)
    )

    assert options_view.screen is OverworldScreen.OPTIONS
    assert len(instances) == 1
    assert instances[0].inspect_calls == 1

    session.current_view()
    assert len(instances) == 1
    assert instances[0].inspect_calls == 2


def test_injected_save_port_bypasses_default_constructor(monkeypatch):
    def fail_default_construction():
        raise AssertionError("default save port must not be constructed")

    monkeypatch.setattr(
        persistence_bootstrap,
        "build_default_save_port",
        fail_default_construction,
    )
    save_port = TrackingSavePort()

    session = _session(save_port)
    assert session.current_view().screen is OverworldScreen.MAIN
    options_view = session.submit(
        ChooseOverworldAction(OverworldAction.OPTIONS)
    )

    assert options_view.screen is OverworldScreen.OPTIONS
    assert save_port.inspect_calls == 1


@pytest.mark.parametrize(
    "save_port",
    [
        object(),
        SimpleNamespace(save=lambda game_state: game_state, inspect=lambda: None),
        SimpleNamespace(save=lambda game_state: game_state, load=lambda: None),
        SimpleNamespace(inspect=lambda: None, load=lambda: None),
        SimpleNamespace(save=None, inspect=lambda: None, load=lambda: None),
    ],
)
def test_invalid_save_port_is_rejected_immediately(save_port):
    with pytest.raises(TypeError, match="save_port must satisfy SavePort"):
        _session(save_port)


def test_save_port_protocol_accepts_callable_persistence_methods():
    assert is_save_port(TrackingSavePort()) is True


def test_overworld_session_has_no_module_level_filesystem_store_import():
    path = ROOT / "src" / "app" / "game" / "overworld_session.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))

    module_level_imports = [
        node
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module in {
            "app.persistence.local_store",
        }
    ]

    assert module_level_imports == []


def test_overworld_session_import_does_not_load_heavy_persistence_modules():
    script = """
import builtins
import sys
original_import = builtins.__import__
persistence_imports = []
def track_import(name, globals=None, *args, **kwargs):
    caller = "" if globals is None else globals.get("__name__", "")
    if caller.startswith("app.persistence.") and name.split(".", 1)[0] in {"copy", "datetime"}:
        persistence_imports.append((caller, name))
    return original_import(name, globals, *args, **kwargs)
builtins.__import__ = track_import
import app.game.overworld_session
forbidden = {
    "app.persistence.ports",
    "app.persistence.envelope",
    "app.persistence.save_document",
    "app.persistence.migration",
    "app.persistence.bootstrap",
    "app.persistence.local_store",
    "app.persistence.coordinator",
    "app.persistence.account",
    "app.persistence.remote_client",
    "app.persistence.sync",
}
loaded = sorted(forbidden.intersection(sys.modules))
print("\\n".join(loaded + [f"{caller}:{name}" for caller, name in persistence_imports]))
"""
    environment = os.environ.copy()
    source = str(ROOT / "src")
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (source, environment.get("PYTHONPATH", "")) if part
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == ""


def test_save_port_inspection_failure_keeps_options_surface_available():
    class FailingInspectPort(TrackingSavePort):
        def inspect(self):
            raise SavePortError("storage unavailable")

    session = _session(FailingInspectPort())

    view = session.submit(ChooseOverworldAction(OverworldAction.OPTIONS))

    assert view.screen is OverworldScreen.OPTIONS
    load_option = next(
        option for option in view.options if option.action is OverworldAction.LOAD
    )
    assert load_option.enabled is False
    assert load_option.disabled_reason is OverworldAvailabilityReason.LOAD_UNAVAILABLE


def test_save_port_load_failure_returns_to_options_with_notice():
    class FailingLoadPort(TrackingSavePort):
        def inspect(self):
            return SimpleNamespace(status=SaveLoadStatus.VALID)

        def load(self):
            raise SavePortError("storage unavailable")

    session = _session(FailingLoadPort())
    options = session.submit(ChooseOverworldAction(OverworldAction.OPTIONS))
    assert options.screen is OverworldScreen.OPTIONS

    confirmation = session.submit(ChooseOverworldAction(OverworldAction.LOAD))
    assert confirmation.screen is OverworldScreen.LOAD_CONFIRMATION

    result = session.submit(ChooseOverworldAction(OverworldAction.CONFIRM))

    assert result.screen is OverworldScreen.OPTIONS
    assert result.notice is not None

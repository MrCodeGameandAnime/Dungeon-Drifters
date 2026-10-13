import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.content.catalog import create_drifter
from app.game.game_state import GameState
from app.persistence import bootstrap as persistence_bootstrap
from app.game.overworld_session import OverworldSession
from app.persistence.ports import SaveLoadStatus, is_save_port
from app.player.player_state import PlayerState
from app.presentation.overworld_models import OverworldAction, OverworldScreen
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

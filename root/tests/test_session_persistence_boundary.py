import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.content.catalog import create_drifter
from app.game.game_state import GameState
from app.game import save_repository as save_repository_module
from app.game.overworld_session import OverworldSession
from app.game.save_contract import SaveLoadStatus
from app.player.player_state import PlayerState
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.ui.overworld_ui import ChooseOverworldAction


ROOT = Path(__file__).resolve().parents[1]


def _session(save_repository=None):
    return OverworldSession(
        GameState(PlayerState(create_drifter("branoc"))),
        battle_factory=lambda *args, **kwargs: None,
        enemy_factory=lambda *args, **kwargs: None,
        ui=None,
        battle_ui_factory=None,
        save_repository=save_repository,
    )


class TrackingRepository:
    def __init__(self):
        self.inspect_calls = 0
        self.save_calls = 0
        self.load_calls = 0

    def save(self, game_state):
        self.save_calls += 1
        return game_state

    def inspect(self):
        self.inspect_calls += 1
        return SimpleNamespace(status=SaveLoadStatus.MISSING)

    def load(self):
        self.load_calls += 1
        return SimpleNamespace(status=SaveLoadStatus.MISSING, error=None)


def test_default_repository_is_lazy_until_options_load_availability(monkeypatch):
    instances = []

    class TrackingDefaultRepository(TrackingRepository):
        def __init__(self):
            super().__init__()
            instances.append(self)

    monkeypatch.setattr(
        save_repository_module,
        "SaveRepository",
        TrackingDefaultRepository,
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


def test_injected_repository_bypasses_default_constructor(monkeypatch):
    def fail_default_construction():
        raise AssertionError("default repository must not be constructed")

    monkeypatch.setattr(
        save_repository_module,
        "SaveRepository",
        fail_default_construction,
    )
    repository = TrackingRepository()

    session = _session(repository)
    assert session.current_view().screen is OverworldScreen.MAIN
    options_view = session.submit(
        ChooseOverworldAction(OverworldAction.OPTIONS)
    )

    assert options_view.screen is OverworldScreen.OPTIONS
    assert repository.inspect_calls == 1


@pytest.mark.parametrize(
    "repository",
    [
        object(),
        SimpleNamespace(save=lambda game_state: game_state, inspect=lambda: None),
        SimpleNamespace(save=lambda game_state: game_state, load=lambda: None),
        SimpleNamespace(inspect=lambda: None, load=lambda: None),
        SimpleNamespace(save=None, inspect=lambda: None, load=lambda: None),
    ],
)
def test_invalid_repository_is_rejected_immediately(repository):
    with pytest.raises(TypeError, match="save_repository must be a SaveRepository"):
        _session(repository)


def test_overworld_session_has_no_module_level_disk_repository_import():
    path = ROOT / "src" / "app" / "game" / "overworld_session.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))

    module_level_imports = [
        node
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "app.game.save_repository"
    ]

    assert module_level_imports == []
